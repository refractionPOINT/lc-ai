"""Run the native ai-sessions Go runner against a loopback control plane.

This module runs *inside* the candidate container.  It does not implement a
model or tools: the real session-runner starts its packaged SDK bridge.  The
loopback server only supplies the small manager/proxy protocol that the Go
runner requires.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
import signal
import sys
from pathlib import Path
from typing import Any

from aiohttp import WSMsgType, web


PLUGINS = [
    "lc-essentials",
    "lc-advanced-skills",
    "lc-fundamentals",
    "lc-compliance",
]
ALLOWED_TOOLS = ["Bash", "Read", "Write", "Edit", "Glob", "Grep", "Skill"]
DENIED_TOOLS = ["Agent", "Task", "CronCreate", "CronDelete", "CronList"]
PROFILE_INSTRUCTIONS = """\
This session uses the controlled-cli-v1 evaluation profile. These profile-specific
instructions override conflicting production plugin workflows. LimaCharlie
authentication and organization scoping are already provided by the transport;
skip auth/whoami permission preflights. The ai generate-query command is not
available. For this profile, construct LCQL manually using the installed CLI's
leaf help: start with `limacharlie search run --ai-help` and consult
`limacharlie search validate --ai-help` for validation. The search group help is
only an index. Modern CLI queries retain the sensor-selector and event-type
pipeline positions; --start/--end replace only the raw time prefix. Older
interactive query examples are not modern CLI command examples. On validation
errors, recheck the documented grammar before changing quoting or operators.
Use the public task's restricted command list. Work directly with the available
tools; Agent/Task delegation and scheduled background work are disabled.
"""


class ProtocolError(RuntimeError):
    """The local runner control protocol was violated."""


def read_oauth_token(path: Path) -> str:
    """Read a Claude credential file without ever rendering its token."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProtocolError("Claude subscription credential file is unreadable") from exc
    candidates: list[Any] = [value.get("accessToken")]
    for key in ("oauthData", "claudeAiOauth", "claudeOauth"):
        nested = value.get(key)
        if isinstance(nested, dict):
            candidates.append(nested.get("accessToken"))
    tokens = [item for item in candidates if isinstance(item, str) and item]
    if len(set(tokens)) != 1:
        raise ProtocolError("Claude subscription credential file has no unique access token")
    return tokens[0]


class LocalControlPlane:
    def __init__(
        self,
        *,
        trial_id: str,
        session_token: str,
        config_token: str,
        oauth_token: str,
        model: str,
        max_turns: int,
        prompt: str,
        context_mode: str = "legacy",
    ) -> None:
        self.trial_id = trial_id
        self.session_token = session_token
        self.config_token = config_token
        self.oauth_token = oauth_token
        self.model = model
        self.max_turns = max_turns
        self.prompt = prompt
        if context_mode not in {"legacy", "bare", "lc_ai"}:
            raise ProtocolError("invalid ai_sessions context mode")
        self.context_mode = context_mode
        self.archive_token = secrets.token_urlsafe(32)
        self.base_url = ""
        self.saw_result = False
        self.terminal_status: str | None = None
        self.ws_connected = asyncio.Event()

    def _authorized(self, request: web.Request) -> bool:
        return secrets.compare_digest(
            request.headers.get("X-Session-Token", ""), self.session_token
        )

    def _require_runner(self, request: web.Request) -> None:
        if request.match_info.get("session_id") != self.trial_id or not self._authorized(request):
            raise web.HTTPUnauthorized()

    async def exchange(self, request: web.Request) -> web.Response:
        if not self._authorized(request):
            raise web.HTTPUnauthorized()
        try:
            body = await request.json()
        except (json.JSONDecodeError, web.HTTPBadRequest) as exc:
            raise web.HTTPBadRequest() from exc
        if body != {"session_id": self.trial_id, "config_token": self.config_token}:
            raise web.HTTPUnauthorized()
        # Deliberately omit every persistence/workspace identity field.  The
        # credential exists only in this in-container response and runner env.
        return web.json_response(
            {
                "session_id": self.trial_id,
                "session_token": self.session_token,
                "provider": "anthropic",
                "cred_type": "oauth_token",
                "credential": self.oauth_token,
                "interaction_proxy_url": self.base_url,
                "permission_mode": "acceptEdits",
                "allowed_tools": ALLOWED_TOOLS,
                "denied_tools": DENIED_TOOLS,
                "system_prompt_suffix": PROFILE_INSTRUCTIONS,
                "max_turns": self.max_turns,
                "initial_prompt": self.prompt,
                "model": self.model,
                "one_shot": True,
                "plugins": [] if self.context_mode == "bare" else PLUGINS,
                "profile_memories": [],
                "resume_mode": False,
            }
        )

    async def heartbeat(self, request: web.Request) -> web.Response:
        self._require_runner(request)
        return web.Response(status=204)

    async def status(self, request: web.Request) -> web.Response:
        self._require_runner(request)
        try:
            body = await request.json()
        except (json.JSONDecodeError, web.HTTPBadRequest) as exc:
            raise web.HTTPBadRequest() from exc
        status = body.get("status") if isinstance(body, dict) else None
        if status not in {"running", "terminated", "failed"}:
            raise web.HTTPBadRequest(text="invalid status")
        if status in {"terminated", "failed"}:
            self.terminal_status = status
        return web.Response(status=204)

    async def workspace_upload_url(self, request: web.Request) -> web.Response:
        self._require_runner(request)
        return web.json_response(
            {
                "upload_url": (
                    f"{self.base_url}/internal/archive/{self.trial_id}"
                    f"?token={self.archive_token}"
                )
            }
        )

    async def archive_upload(self, request: web.Request) -> web.Response:
        if request.match_info.get("session_id") != self.trial_id or not secrets.compare_digest(
            request.query.get("token", ""), self.archive_token
        ):
            raise web.HTTPUnauthorized()
        while await request.content.readany():
            pass
        return web.Response(status=201)

    async def workspace_archived(self, request: web.Request) -> web.Response:
        self._require_runner(request)
        return web.Response(status=200)

    async def websocket(self, request: web.Request) -> web.WebSocketResponse:
        if request.match_info.get("session_id") != self.trial_id:
            raise web.HTTPNotFound()
        supplied = request.headers.get("X-Session-Token") or request.query.get("token", "")
        if not secrets.compare_digest(supplied, self.session_token):
            raise web.HTTPUnauthorized()
        ws = web.WebSocketResponse(max_msg_size=10 * 1024 * 1024)
        await ws.prepare(request)
        self.ws_connected.set()
        async for message in ws:
            if message.type == WSMsgType.TEXT:
                try:
                    event = json.loads(message.data)
                except json.JSONDecodeError as exc:
                    raise ProtocolError("runner emitted invalid JSON") from exc
                if not isinstance(event, dict) or not isinstance(event.get("type"), str):
                    raise ProtocolError("runner emitted an invalid event object")
                if event["type"] == "result" and "parent_tool_use_id" not in event:
                    self.saw_result = True
                sys.stdout.write(json.dumps(event, separators=(",", ":")) + "\n")
                sys.stdout.flush()
            elif message.type == WSMsgType.ERROR:
                raise ProtocolError("runner WebSocket failed")
        return ws

    def app(self) -> web.Application:
        app = web.Application(client_max_size=10 * 1024 * 1024)
        app.router.add_post("/internal/config/exchange", self.exchange)
        app.router.add_post("/internal/sessions/{session_id}/heartbeat", self.heartbeat)
        app.router.add_post("/internal/sessions/{session_id}/status", self.status)
        app.router.add_post(
            "/internal/sessions/{session_id}/workspace-upload-url", self.workspace_upload_url
        )
        app.router.add_put("/internal/archive/{session_id}", self.archive_upload)
        app.router.add_post(
            "/internal/sessions/{session_id}/workspace-archived", self.workspace_archived
        )
        app.router.add_get("/internal/runner/{session_id}/ws", self.websocket)
        return app


async def _forward_stderr(stream: asyncio.StreamReader) -> None:
    while chunk := await stream.read(65536):
        sys.stderr.buffer.write(chunk)
        sys.stderr.buffer.flush()


def validate_completion(code: int, control: LocalControlPlane) -> None:
    if code != 0:
        raise ProtocolError(f"native session runner exited with status {code}")
    if not control.ws_connected.is_set() or not control.saw_result:
        raise ProtocolError("native session runner exited without a top-level result")
    if control.terminal_status != "terminated":
        raise ProtocolError("native session runner omitted successful terminal status")


async def run(args: argparse.Namespace, prompt: str) -> int:
    executable = Path(os.environ["SESSION_RUNNER"])
    if not executable.is_absolute() or not executable.is_file():
        raise ProtocolError("SESSION_RUNNER must name an absolute executable file")
    if not Path("/work").is_dir() or not Path("/workspace").is_dir():
        raise ProtocolError("/work and /workspace must exist")
    if Path("/workspace").resolve() != Path("/work").resolve():
        raise ProtocolError("/workspace must point to the trial /work directory")

    session_token, config_token = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    oauth_token = read_oauth_token(Path("/auth/.credentials.json"))
    control = LocalControlPlane(
        trial_id=args.trial_id,
        session_token=session_token,
        config_token=config_token,
        oauth_token=oauth_token,
        model=args.model,
        max_turns=args.max_turns,
        prompt=prompt,
        context_mode=args.context_mode,
    )
    server = web.AppRunner(control.app(), handle_signals=False)
    await server.setup()
    site = web.TCPSite(server, "127.0.0.1", 0)
    await site.start()
    sockets = getattr(site._server, "sockets", None)  # aiohttp exposes no public bound-port API
    if not sockets:
        await server.cleanup()
        raise ProtocolError("loopback control plane did not bind")
    control.base_url = f"http://127.0.0.1:{sockets[0].getsockname()[1]}"

    env = dict(os.environ)
    for key in (
        "ANTHROPIC_API_KEY",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "OPENAI_API_KEY",
        "GOOGLE_API_KEY",
        "OPENROUTER_API_KEY",
        "LC_API_KEY",
        "LC_JWT",
        "LC_UID",
        "LC_OID",
    ):
        env.pop(key, None)
    env.update(
        {
            "SESSION_ID": args.trial_id,
            "SESSION_TOKEN": session_token,
            "CONFIG_TOKEN": config_token,
            "SESSION_MANAGER_URL": control.base_url,
            "INTERACTION_PROXY_URL": control.base_url,
            "AI_PROVIDER": "anthropic",
            "NO_PROXY": "127.0.0.1,localhost",
            "no_proxy": "127.0.0.1,localhost",
        }
    )
    process = await asyncio.create_subprocess_exec(
        str(executable),
        env=env,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        start_new_session=True,
    )
    assert process.stdout is not None
    stdout_task = asyncio.create_task(_forward_stderr(process.stdout))
    assert process.stderr is not None
    stderr_task = asyncio.create_task(_forward_stderr(process.stderr))
    try:
        try:
            code = await asyncio.wait_for(process.wait(), timeout=args.timeout)
        except asyncio.TimeoutError:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                await asyncio.wait_for(process.wait(), timeout=args.shutdown_grace)
            except asyncio.TimeoutError:
                os.killpg(process.pid, signal.SIGKILL)
                await process.wait()
            raise ProtocolError("native session runner timed out")
        validate_completion(code, control)
        return 0
    finally:
        await asyncio.gather(stderr_task, stdout_task)
        await server.cleanup()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--model", required=True)
    result.add_argument("--max-turns", type=int, default=30)
    result.add_argument("--trial-id", required=True)
    result.add_argument("--timeout", type=float, default=600.0)
    result.add_argument("--shutdown-grace", type=float, default=15.0)
    result.add_argument("--context-mode", choices=("legacy", "bare", "lc_ai"), default="legacy")
    return result


def main() -> None:
    args = parser().parse_args()
    if args.max_turns < 1 or args.timeout <= 0 or args.shutdown_grace <= 0:
        parser().error("limits must be positive")
    prompt = sys.stdin.read()
    if not prompt.strip():
        parser().error("task prompt on stdin is empty")
    try:
        raise SystemExit(asyncio.run(run(args, prompt)))
    except (ProtocolError, KeyError) as exc:
        print(f"workspace runner: {exc}", file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
