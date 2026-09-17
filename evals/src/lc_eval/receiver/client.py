"""Management client and owned local receiver/tunnel lifecycle helpers."""

from __future__ import annotations

import asyncio
import ipaddress
import json
import os
import re
from collections import deque
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from aiohttp import ClientSession, ClientTimeout, web

from .app import create_ingest_app, create_management_app
from .store import ReceiverStore, validate_trial_id


_QUICK_TUNNEL_URL = re.compile(
    r"https://[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.trycloudflare\.com\b",
    re.IGNORECASE,
)


class ManagementClientError(RuntimeError):
    def __init__(self, status: int, message: str):
        super().__init__(f"receiver management request failed ({status}): {message}")
        self.status = status


class ManagementClient:
    """Async client for the authenticated, loopback-only management API."""

    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        timeout_seconds: float = 10.0,
        session: httpx.AsyncClient | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self._token = token
        self._timeout_seconds = timeout_seconds
        self._session = session
        self._owns_session = session is None

    async def __aenter__(self) -> ManagementClient:
        await self._get_session()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def _get_session(self) -> httpx.AsyncClient:
        if self._session is None:
            self._session = httpx.AsyncClient(timeout=self._timeout_seconds)
        return self._session

    async def close(self) -> None:
        if self._owns_session and self._session is not None:
            await self._session.aclose()
            self._session = None

    async def _request(
        self, method: str, path: str, *, json_body: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        session = await self._get_session()
        response = await session.request(
            method,
            f"{self.base_url}{path}",
            headers={"Authorization": f"Bearer {self._token}"},
            json=json_body,
        )
        raw = response.content
        if response.status_code >= 400:
            try:
                detail = json.loads(raw).get("message", raw.decode("utf-8", "replace"))
            except (json.JSONDecodeError, AttributeError):
                detail = raw.decode("utf-8", "replace")
            raise ManagementClientError(response.status_code, str(detail))
        if not raw:
            return None
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ManagementClientError(response.status_code, "response was not an object")
        return value

    async def health(self) -> dict[str, Any]:
        return (await self._request("GET", "/healthz")) or {}

    async def create_trial(self, trial_id: str, secret: str) -> dict[str, Any]:
        validate_trial_id(trial_id)
        return (
            await self._request(
                "PUT", f"/v1/trials/{quote(trial_id, safe='')}", json_body={"secret": secret}
            )
        ) or {}

    create_bucket = create_trial

    async def get_trial(self, trial_id: str) -> dict[str, Any]:
        validate_trial_id(trial_id)
        return (
            await self._request("GET", f"/v1/trials/{quote(trial_id, safe='')}")
        ) or {}

    async def delete_trial(self, trial_id: str) -> None:
        validate_trial_id(trial_id)
        await self._request("DELETE", f"/v1/trials/{quote(trial_id, safe='')}")

    delete_bucket = delete_trial

    async def list_receipts(
        self,
        trial_id: str,
        *,
        after_receipt_id: int = 0,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        validate_trial_id(trial_id)
        value = await self._request(
            "GET",
            f"/v1/trials/{quote(trial_id, safe='')}/receipts"
            f"?after_receipt_id={after_receipt_id}&limit={limit}",
        )
        receipts = (value or {}).get("receipts")
        if not isinstance(receipts, list):
            raise ManagementClientError(200, "response omitted receipts list")
        return receipts


def _require_loopback(host: str, label: str) -> None:
    try:
        address = ipaddress.ip_address(host)
    except ValueError as error:
        raise ValueError(f"{label} must be an explicit loopback IP address") from error
    if not address.is_loopback:
        raise ValueError(f"{label} must be a loopback address")


class LocalReceiverServer:
    """Run separate public-ingest and private-management aiohttp listeners."""

    def __init__(
        self,
        store: ReceiverStore,
        management_token: str,
        *,
        ingest_host: str = "127.0.0.1",
        ingest_port: int = 0,
        management_host: str = "127.0.0.1",
        management_port: int = 0,
        max_payload_bytes: int = 2 * 1024 * 1024,
        max_events: int = 10_000,
    ):
        _require_loopback(ingest_host, "ingest_host")
        _require_loopback(management_host, "management_host")
        self.store = store
        self.management_token = management_token
        self.ingest_host = ingest_host
        self.ingest_port = ingest_port
        self.management_host = management_host
        self.management_port = management_port
        self.max_payload_bytes = max_payload_bytes
        self.max_events = max_events
        self._ingest_runner: web.AppRunner | None = None
        self._management_runner: web.AppRunner | None = None

    @property
    def ingest_url(self) -> str:
        if not self._ingest_runner or not self.ingest_port:
            raise RuntimeError("local receiver has not started")
        return f"http://{self.ingest_host}:{self.ingest_port}"

    @property
    def management_url(self) -> str:
        if not self._management_runner or not self.management_port:
            raise RuntimeError("local receiver has not started")
        return f"http://{self.management_host}:{self.management_port}"

    @property
    def management_client(self) -> ManagementClient:
        return ManagementClient(self.management_url, self.management_token)

    async def __aenter__(self) -> LocalReceiverServer:
        await self.start()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.stop()

    @staticmethod
    def _bound_port(site: web.TCPSite) -> int:
        server = site._server  # aiohttp does not expose the bound ephemeral port.
        if server is None or not server.sockets:
            raise RuntimeError("receiver listener did not bind a socket")
        return int(server.sockets[0].getsockname()[1])

    async def start(self) -> None:
        if self._ingest_runner or self._management_runner:
            raise RuntimeError("local receiver is already started")
        ingest_app = create_ingest_app(
            self.store,
            max_payload_bytes=self.max_payload_bytes,
            max_events=self.max_events,
        )
        management_app = create_management_app(self.store, self.management_token)
        self._ingest_runner = web.AppRunner(ingest_app, handle_signals=False)
        self._management_runner = web.AppRunner(management_app, handle_signals=False)
        try:
            await self._ingest_runner.setup()
            ingest_site = web.TCPSite(
                self._ingest_runner, self.ingest_host, self.ingest_port
            )
            await ingest_site.start()
            self.ingest_port = self._bound_port(ingest_site)

            await self._management_runner.setup()
            management_site = web.TCPSite(
                self._management_runner, self.management_host, self.management_port
            )
            await management_site.start()
            self.management_port = self._bound_port(management_site)
        except BaseException:
            await self.stop()
            raise

    async def stop(self) -> None:
        management_runner, self._management_runner = self._management_runner, None
        ingest_runner, self._ingest_runner = self._ingest_runner, None
        if management_runner is not None:
            await management_runner.cleanup()
        if ingest_runner is not None:
            await ingest_runner.cleanup()


class CloudflaredTunnel:
    """Own one pinned cloudflared quick-tunnel child process.

    The executable is always supplied by the caller. This class neither downloads
    cloudflared nor creates persistent Cloudflare resources.
    """

    def __init__(
        self,
        executable: str | Path,
        local_url: str,
        config_dir: str | Path,
        *,
        startup_timeout_seconds: float = 30.0,
        shutdown_grace_seconds: float = 10.0,
        readiness_probe: Callable[[str], Awaitable[None]] | None = None,
    ):
        self.executable = Path(executable).expanduser().resolve()
        self.local_url = local_url.rstrip("/")
        self.config_dir = Path(config_dir).expanduser().resolve()
        self.startup_timeout_seconds = startup_timeout_seconds
        self.shutdown_grace_seconds = shutdown_grace_seconds
        self._readiness_probe = readiness_probe or self._probe_public_health
        self.public_url: str | None = None
        self.process: asyncio.subprocess.Process | None = None
        self._pump_tasks: list[asyncio.Task[None]] = []
        self._recent_output: deque[str] = deque(maxlen=200)

    @property
    def pid(self) -> int | None:
        return self.process.pid if self.process else None

    @property
    def recent_output(self) -> tuple[str, ...]:
        return tuple(self._recent_output)

    @property
    def config_path(self) -> Path:
        return self.config_dir / "config.yml"

    def command_argv(self) -> list[str]:
        return [
            str(self.executable),
            "tunnel",
            "--config",
            str(self.config_path),
            "--no-autoupdate",
            "--url",
            self.local_url,
        ]

    async def __aenter__(self) -> CloudflaredTunnel:
        await self.start()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.stop()

    async def _pump(
        self, stream: asyncio.StreamReader, urls: asyncio.Queue[str]
    ) -> None:
        while line := await stream.readline():
            text = line.decode("utf-8", "replace").rstrip()
            self._recent_output.append(text)
            match = _QUICK_TUNNEL_URL.search(text)
            if match:
                urls.put_nowait(match.group(0).lower())

    async def _probe_public_health(self, public_url: str) -> None:
        deadline = asyncio.get_running_loop().time() + self.startup_timeout_seconds
        last_error: Exception | None = None
        timeout = ClientTimeout(total=min(5.0, self.startup_timeout_seconds))
        async with ClientSession(timeout=timeout) as session:
            while asyncio.get_running_loop().time() < deadline:
                try:
                    async with session.get(f"{public_url}/healthz") as response:
                        if response.status == 200:
                            value = await response.json()
                            if value.get("status") == "ok":
                                return
                except Exception as error:  # transient tunnel/DNS/TLS readiness
                    last_error = error
                await asyncio.sleep(0.25)
        raise TimeoutError(f"public receiver did not become ready: {last_error}")

    async def start(self) -> str:
        if self.process is not None:
            raise RuntimeError("cloudflared tunnel is already started")
        if not self.executable.is_file() or not os.access(self.executable, os.X_OK):
            raise ValueError("cloudflared executable must be an existing executable file")
        if self.startup_timeout_seconds <= 0 or self.shutdown_grace_seconds <= 0:
            raise ValueError("tunnel timeouts must be positive")
        if self.config_dir.exists():
            if not self.config_dir.is_dir() or any(self.config_dir.iterdir()):
                raise ValueError("tunnel config_dir must be absent or an empty directory")
            os.chmod(self.config_dir, 0o700)
        else:
            self.config_dir.mkdir(mode=0o700, parents=True)
        config_path = self.config_path
        config_path.write_text("{}\n", encoding="utf-8")
        os.chmod(config_path, 0o600)

        self.process = await asyncio.create_subprocess_exec(
            *self.command_argv(),
            cwd=self.config_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        assert self.process.stdout is not None
        assert self.process.stderr is not None
        urls: asyncio.Queue[str] = asyncio.Queue()
        self._pump_tasks = [
            asyncio.create_task(self._pump(self.process.stdout, urls)),
            asyncio.create_task(self._pump(self.process.stderr, urls)),
        ]
        url_task = asyncio.create_task(urls.get())
        exit_task = asyncio.create_task(self.process.wait())
        try:
            done, _ = await asyncio.wait(
                {url_task, exit_task},
                timeout=self.startup_timeout_seconds,
                return_when=asyncio.FIRST_COMPLETED,
            )
            if url_task in done:
                self.public_url = url_task.result()
            elif exit_task in done:
                raise RuntimeError(
                    f"cloudflared exited with status {exit_task.result()} before publishing a URL"
                )
            else:
                raise TimeoutError("cloudflared did not publish a quick-tunnel URL")
            await self._readiness_probe(self.public_url)
            return self.public_url
        except BaseException:
            await self.stop()
            raise
        finally:
            for task in (url_task, exit_task):
                if not task.done():
                    task.cancel()
            await asyncio.gather(url_task, exit_task, return_exceptions=True)

    async def stop(self) -> None:
        process, self.process = self.process, None
        self.public_url = None
        if process is not None and process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(
                    process.wait(), timeout=self.shutdown_grace_seconds
                )
            except TimeoutError:
                process.kill()
                await process.wait()
        for task in self._pump_tasks:
            if not task.done():
                task.cancel()
        if self._pump_tasks:
            await asyncio.gather(*self._pump_tasks, return_exceptions=True)
        self._pump_tasks.clear()


class ReceiverRuntime:
    """Context manager that starts both listeners and an optional quick tunnel."""

    def __init__(
        self,
        store: ReceiverStore,
        management_token: str,
        *,
        cloudflared_executable: str | Path | None = None,
        tunnel_config_dir: str | Path | None = None,
        **server_options: Any,
    ):
        self.server = LocalReceiverServer(store, management_token, **server_options)
        self.cloudflared_executable = cloudflared_executable
        self.tunnel_config_dir = tunnel_config_dir
        self.tunnel: CloudflaredTunnel | None = None

    @property
    def public_url(self) -> str:
        if self.tunnel is not None:
            if self.tunnel.public_url is None:
                raise RuntimeError("receiver tunnel has not started")
            return self.tunnel.public_url
        return self.server.ingest_url

    @property
    def management_client(self) -> ManagementClient:
        return self.server.management_client

    async def __aenter__(self) -> ReceiverRuntime:
        await self.start()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.stop()

    async def start(self) -> None:
        await self.server.start()
        try:
            if self.cloudflared_executable is not None:
                if self.tunnel_config_dir is None:
                    raise ValueError(
                        "tunnel_config_dir is required when cloudflared is enabled"
                    )
                self.tunnel = CloudflaredTunnel(
                    self.cloudflared_executable,
                    self.server.ingest_url,
                    self.tunnel_config_dir,
                )
                await self.tunnel.start()
        except BaseException:
            await self.stop()
            raise

    async def stop(self) -> None:
        tunnel, self.tunnel = self.tunnel, None
        if tunnel is not None:
            await tunnel.stop()
        await self.server.stop()
