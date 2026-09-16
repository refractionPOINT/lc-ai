"""Evaluator-side fixed-executable transport with a bounded CLI policy."""

from __future__ import annotations

import asyncio
import base64
import binascii
import hashlib
import json
import os
import stat
import time
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from aiohttp import web


class PolicyError(ValueError):
    """The requested CLI invocation is outside controlled-cli-v1."""


@dataclass(frozen=True)
class CommandSpec:
    value_options: frozenset[str] = frozenset()
    flag_options: frozenset[str] = frozenset()
    path_options: frozenset[str] = frozenset()
    fixed_values: tuple[tuple[str, frozenset[str]], ...] = ()

    def allowed_values(self, option: str) -> frozenset[str] | None:
        return dict(self.fixed_values).get(option)


@dataclass(frozen=True)
class ValidatedCommand:
    argv: tuple[str, ...]
    file_arguments: tuple[tuple[int, PurePosixPath], ...]
    command: tuple[str, str]


_GLOBAL_VALUE_OPTIONS = frozenset({"--oid", "--output", "--filter", "--fields", "--sort-by"})
_GLOBAL_FLAG_OPTIONS = frozenset({"--quiet", "-q", "--wide", "-W", "--no-warnings", "--reverse"})
_GLOBAL_FIXED_VALUES = {"--output": frozenset({"json", "yaml", "toon", "csv", "table", "jsonl"})}
_UNSAFE_GLOBAL_VALUE_OPTIONS = frozenset({"--profile", "--env"})
_UNSAFE_GLOBAL_FLAG_OPTIONS = frozenset({"--debug", "--debug-full", "--debug-curl"})
_HELP_OPTIONS = frozenset({"--help", "-h", "--ai-help"})

CONTROLLED_CLI_V1_NOTICE = """\
The controlled CLI transport supports only these LimaCharlie operations:
lookup list/get/set; hive list/get/set for the lookup hive only; search
run/validate/queries/limits; cloud-adapter list/get/set/list-types/schema/sensors;
dr list/get/set/enable
in the general namespace; output list/create for detect webhooks; and detection
list/get. Use stdin or an --input-file below /work for command input. The
transport snapshots input files without following symlinks. Search checkpoint,
resume, delete, import/export, generic api/auth, debug, credential-profile, and
environment-selection commands are unavailable. Use shell redirection in the
candidate container for files such as /work/export.jsonl. Safe global options
may appear anywhere in a command, and --ai-help is available at the root,
permitted group, and permitted leaf-command levels.

Authentication and organization scoping are already supplied by this transport;
skip production auth/whoami preflights. ai generate-query is unavailable. This
profile permits manual LCQL construction even when production skills prescribe
generation. For search syntax and examples, open `search run --ai-help` and
`search validate --ai-help`; group help is only an index. Modern CLI pipelines
retain sensor-selector and event-type positions; --start/--end replace only the
raw time prefix. Recheck leaf help after parser errors before retrying.
"""

_STAGE_SCRIPT = """\
import os
import sys

path = sys.argv[1]
flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
descriptor = os.open(path, flags, 0o600)
with os.fdopen(descriptor, "wb") as destination:
    while True:
        block = sys.stdin.buffer.read(65536)
        if not block:
            break
        destination.write(block)
"""

_KEY = frozenset({"--key"})
_EMPTY = CommandSpec()
_COMMANDS: dict[tuple[str, str], CommandSpec] = {
    ("lookup", "list"): _EMPTY,
    ("lookup", "get"): CommandSpec(value_options=_KEY),
    ("lookup", "set"): CommandSpec(
        value_options=frozenset({"--key", "--input-file", "--tag", "--comment"}),
        flag_options=frozenset({"--enabled", "--disabled"}),
        path_options=frozenset({"--input-file"}),
    ),
    ("hive", "list"): CommandSpec(
        value_options=frozenset({"--hive-name"}),
        fixed_values=(("--hive-name", frozenset({"lookup"})),),
    ),
    ("hive", "get"): CommandSpec(
        value_options=frozenset({"--hive-name", "--key"}),
        fixed_values=(("--hive-name", frozenset({"lookup"})),),
    ),
    ("hive", "set"): CommandSpec(
        value_options=frozenset(
            {"--hive-name", "--key", "--input-file", "--tag-add", "--tag-rm", "--comment", "--expiry"}
        ),
        flag_options=frozenset({"--enabled", "--disabled"}),
        path_options=frozenset({"--input-file"}),
        fixed_values=(("--hive-name", frozenset({"lookup"})),),
    ),
    ("search", "run"): CommandSpec(
        value_options=frozenset({"--query", "--start", "--end", "--stream", "--limit"}),
        flag_options=frozenset({"--raw", "--expand"}),
        fixed_values=(("--stream", frozenset({"event", "detect", "audit"})),),
    ),
    ("search", "validate"): CommandSpec(value_options=frozenset({"--query"})),
    ("search", "queries"): CommandSpec(
        value_options=frozenset({"--state", "--limit"}),
        fixed_values=(("--state", frozenset({"all", "executing", "idle"})),),
    ),
    ("search", "limits"): _EMPTY,
    ("cloud-adapter", "list"): _EMPTY,
    ("cloud-adapter", "get"): CommandSpec(value_options=_KEY),
    ("cloud-adapter", "set"): CommandSpec(
        value_options=frozenset({"--key", "--input-file", "--tag", "--comment"}),
        flag_options=frozenset({"--enabled", "--disabled"}),
        path_options=frozenset({"--input-file"}),
    ),
    ("cloud-adapter", "list-types"): _EMPTY,
    ("cloud-adapter", "schema"): CommandSpec(
        value_options=frozenset({"--type"}),
        fixed_values=(("--type", frozenset({"webhook"})),),
    ),
    ("cloud-adapter", "sensors"): CommandSpec(value_options=_KEY),
    ("dr", "list"): CommandSpec(
        value_options=frozenset({"--namespace"}),
        fixed_values=(("--namespace", frozenset({"general"})),),
    ),
    ("dr", "get"): CommandSpec(
        value_options=frozenset({"--key", "--namespace"}),
        fixed_values=(("--namespace", frozenset({"general"})),),
    ),
    ("dr", "set"): CommandSpec(
        value_options=frozenset(
            {"--key", "--input-file", "--detect", "--respond", "--tag", "--namespace"}
        ),
        flag_options=frozenset({"--enabled", "--disabled"}),
        path_options=frozenset({"--input-file", "--detect", "--respond"}),
        fixed_values=(("--namespace", frozenset({"general"})),),
    ),
    ("dr", "enable"): CommandSpec(
        value_options=frozenset({"--key", "--namespace"}),
        fixed_values=(("--namespace", frozenset({"general"})),),
    ),
    ("output", "list"): _EMPTY,
    ("output", "create"): CommandSpec(
        value_options=frozenset({"--name", "--module", "--type", "--input-file"}),
        path_options=frozenset({"--input-file"}),
        fixed_values=(
            ("--module", frozenset({"webhook"})),
            ("--type", frozenset({"detect"})),
        ),
    ),
    ("detection", "list"): CommandSpec(
        value_options=frozenset({"--start", "--end", "--cat", "--limit"})
    ),
    ("detection", "get"): CommandSpec(value_options=frozenset({"--id"})),
}
_DIAGNOSTIC_TOKENS = frozenset(
    {
        "auth", "get-token", "api", "api-key", "org", "user", "secret",
        "delete", "import", "export", "checkpoint", "resume",
    }
    | {part for command in _COMMANDS for part in command}
)
_DIAGNOSTIC_OPTIONS = frozenset(
    {
        "--debug", "--debug-full", "--debug-curl", "--profile", "--env",
        "--checkpoint", "--resume", "--force", "--input-file", "--output-file",
    }
    | set(_GLOBAL_VALUE_OPTIONS)
    | set(_GLOBAL_FLAG_OPTIONS)
    | set(_HELP_OPTIONS)
    | {option for spec in _COMMANDS.values() for option in spec.value_options | spec.flag_options}
)


class CommandPolicy:
    """Exact command/flag policy for the three initial scenarios."""

    def __init__(self, *, allowed_oids: tuple[str, ...] = ()) -> None:
        self.allowed_oids = frozenset(allowed_oids)

    @staticmethod
    def describe() -> str:
        return CONTROLLED_CLI_V1_NOTICE.strip()

    def validate(self, argv: object, cwd: object) -> ValidatedCommand:
        if not isinstance(argv, list) or not argv or len(argv) > 200:
            raise PolicyError("argv must be a nonempty array of at most 200 strings")
        if any(not isinstance(arg, str) or len(arg) > 100_000 or "\0" in arg for arg in argv):
            raise PolicyError("argv contains an invalid value")
        if not isinstance(cwd, str) or cwd != "/work":
            raise PolicyError("controlled-cli-v1 requires cwd /work")
        remaining = self._partition_global_options(argv)
        if len(remaining) == 1 and remaining[0][1] in _HELP_OPTIONS | {"--version"}:
            return ValidatedCommand(tuple(argv), (), ("meta", "help"))
        if not remaining:
            raise PolicyError("a permitted CLI command is required")

        cursor = 0
        _, group = remaining[cursor]
        cursor += 1
        if cursor == len(remaining) - 1 and remaining[cursor][1] in _HELP_OPTIONS:
            if any(command[0] == group for command in _COMMANDS):
                return ValidatedCommand(tuple(argv), (), (group, "help"))
        if cursor >= len(remaining) or remaining[cursor][1].startswith("-"):
            raise PolicyError("a permitted CLI subcommand is required")
        _, subcommand = remaining[cursor]
        cursor += 1
        spec = _COMMANDS.get((group, subcommand))
        if spec is None:
            raise PolicyError("command is outside controlled-cli-v1")

        file_arguments: list[tuple[int, PurePosixPath]] = []
        while cursor < len(remaining):
            argument_index, argument = remaining[cursor]
            if argument in _HELP_OPTIONS and cursor == len(remaining) - 1:
                cursor += 1
                continue
            option, inline_value = _split_option(argument)
            if option in spec.flag_options:
                if inline_value is not None:
                    raise PolicyError(f"flag {option} does not take a value")
                cursor += 1
                continue
            if option not in spec.value_options:
                raise PolicyError("option is not permitted for this command")
            if inline_value is None:
                if cursor + 1 >= len(remaining):
                    raise PolicyError(f"option {option} requires a value")
                value_index, value = remaining[cursor + 1]
                if value.startswith("--"):
                    raise PolicyError(f"option {option} requires a value")
                cursor += 2
            else:
                value_index = argument_index
                value = inline_value
                cursor += 1
            fixed = spec.allowed_values(option)
            if fixed is not None and value not in fixed:
                raise PolicyError(f"value for {option} is outside controlled-cli-v1")
            if option in spec.path_options:
                file_arguments.append((value_index, _workspace_path(value)))

        return ValidatedCommand(tuple(argv), tuple(file_arguments), (group, subcommand))

    def _partition_global_options(self, argv: list[str]) -> list[tuple[int, str]]:
        """Mirror LazyGroup's global-option hoisting while retaining indexes."""
        remaining: list[tuple[int, str]] = []
        index = 0
        while index < len(argv):
            argument = argv[index]
            if argument == "--":
                remaining.extend(enumerate(argv[index:], start=index))
                break
            if not argument.startswith("-"):
                remaining.append((index, argument))
                index += 1
                continue
            option, inline = _split_option(argv[index])
            if option in _UNSAFE_GLOBAL_FLAG_OPTIONS | _UNSAFE_GLOBAL_VALUE_OPTIONS:
                raise PolicyError(f"global option {option} is not permitted")
            if option in _GLOBAL_FLAG_OPTIONS:
                if inline is not None:
                    raise PolicyError(f"flag {option} does not take a value")
                index += 1
                continue
            if option not in _GLOBAL_VALUE_OPTIONS:
                remaining.append((index, argument))
                index += 1
                continue
            if inline is None:
                if index + 1 >= len(argv):
                    raise PolicyError(f"option {option} requires a value")
                value = argv[index + 1]
                index += 2
            else:
                value = inline
                index += 1
            if option == "--oid" and self.allowed_oids and value not in self.allowed_oids:
                raise PolicyError("organization ID is not assigned to this trial")
            fixed = _GLOBAL_FIXED_VALUES.get(option)
            comparable = value.lower() if option == "--output" else value
            if fixed is not None and comparable not in fixed:
                raise PolicyError(f"value for {option} is outside controlled-cli-v1")
        return remaining


class StreamingRedactor:
    """Redact exact byte strings without leaking matches split across chunks."""

    def __init__(self, secrets: tuple[bytes, ...], replacement: bytes = b"[REDACTED]") -> None:
        self.secrets = tuple(sorted({secret for secret in secrets if secret}, key=len, reverse=True))
        self.replacement = replacement
        self.pending = bytearray()

    def feed(self, data: bytes, *, final: bool = False) -> bytes:
        self.pending.extend(data)
        if not self.secrets:
            result = bytes(self.pending)
            self.pending.clear()
            return result
        output = bytearray()
        position = 0
        pending = bytes(self.pending)
        while position < len(pending):
            match = next((secret for secret in self.secrets if pending.startswith(secret, position)), None)
            if match is not None:
                output.extend(self.replacement)
                position += len(match)
                continue
            remainder = pending[position:]
            if not final and any(secret.startswith(remainder) for secret in self.secrets):
                break
            output.append(pending[position])
            position += 1
        self.pending = bytearray(pending[position:])
        if final and self.pending:
            output.extend(self.pending)
            self.pending.clear()
        return bytes(output)


class Broker:
    def __init__(
        self,
        worker: str,
        socket_dir: Path,
        evidence: Path,
        *,
        workspace: Path | None = None,
        max_seconds: int = 300,
        max_output: int = 16_000_000,
        max_input_file: int = 16_000_000,
        max_invocations: int = 80,
        redactions: tuple[str | bytes, ...] = (),
        allowed_oids: tuple[str, ...] = (),
    ) -> None:
        self.worker = worker
        self.socket_dir = socket_dir
        self.workspace = workspace or socket_dir.parent / "work"
        self.evidence = evidence
        self.max_seconds, self.max_output = max_seconds, max_output
        self.max_input_file = max_input_file
        self.max_invocations = max_invocations
        self.redactions = tuple(
            secret.encode() if isinstance(secret, str) else secret for secret in redactions if secret
        )
        self.policy = CommandPolicy(allowed_oids=allowed_oids)
        self.active = True
        self.count = 0
        self.processes: set[asyncio.subprocess.Process] = set()
        self.runner: web.AppRunner | None = None

    def redact(self, text: str) -> str:
        result = text
        for secret in self.redactions:
            result = result.replace(secret.decode(errors="ignore"), "[REDACTED]")
        return result

    def log(self, event: dict[str, Any]) -> None:
        self.evidence.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.evidence, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        with os.fdopen(fd, "a") as file:
            file.write(self.redact(json.dumps(event)) + "\n")

    async def execute(self, request: web.Request) -> web.StreamResponse:
        if not self.active or self.count >= self.max_invocations:
            raise web.HTTPForbidden(text="CLI transport is inactive or exhausted")
        try:
            data = await request.json()
        except (json.JSONDecodeError, UnicodeDecodeError, web.HTTPException) as exc:
            raise web.HTTPBadRequest(text="malformed JSON request") from exc
        if not isinstance(data, dict):
            raise web.HTTPBadRequest(text="request body must be an object")
        try:
            validated = self.policy.validate(data.get("argv"), data.get("cwd", "/work"))
        except PolicyError as exc:
            self.log(_invocation_event("command_rejected", data.get("argv"), data.get("cwd"), str(exc)))
            raise web.HTTPForbidden(text=str(exc)) from exc
        try:
            encoded_stdin = data.get("stdin", "")
            if not isinstance(encoded_stdin, str):
                raise TypeError
            stdin = base64.b64decode(encoded_stdin, validate=True)
        except (ValueError, TypeError, binascii.Error) as exc:
            self.log(_invocation_event("command_rejected", data.get("argv"), data.get("cwd"), "invalid stdin"))
            raise web.HTTPBadRequest(text="stdin must be valid base64") from exc
        if len(stdin) > 16_000_000:
            raise web.HTTPRequestEntityTooLarge(max_size=16_000_000, actual_size=len(stdin))

        self.count += 1
        command_id = uuid.uuid4().hex
        start = time.monotonic()
        deadline = start + self.max_seconds
        self.log({**_invocation_event("command_request", list(validated.argv), "/work"), "id": command_id})
        staged_paths: list[str] = []
        try:
            argv, staged_paths = await asyncio.wait_for(
                self._stage_files(validated, command_id, deadline),
                timeout=_remaining(deadline),
            )
            proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    "docker", "exec", "-i", "--workdir", "/work", self.worker,
                    "/usr/local/bin/python", "-I", "/usr/local/bin/limacharlie", *argv,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                ),
                timeout=_remaining(deadline),
            )
        except PolicyError as exc:
            await self._remove_staged(staged_paths)
            self.log({"type": "command_end", "id": command_id, "code": 125,
                      "error": "workspace input rejected", "seconds": time.monotonic() - start})
            raise web.HTTPForbidden(text=str(exc)) from exc
        except (OSError, RuntimeError) as exc:
            await self._remove_staged(staged_paths)
            self.active = False
            await self._kill_worker()
            self.log({"type": "command_end", "id": command_id, "code": 125,
                      "error": "worker spawn or input staging failed", "seconds": time.monotonic() - start})
            raise web.HTTPServiceUnavailable(text="CLI worker could not start the command") from exc

        self.log({**_invocation_event("command_start", list(validated.argv), "/work"),
                  "id": command_id, "command": list(validated.command), "at": time.time()})
        self.processes.add(proc)
        response = web.StreamResponse(headers={"Content-Type": "application/x-ndjson"})
        try:
            await response.prepare(request)
        except (ConnectionError, asyncio.CancelledError):
            await self._abort_process(proc)
            self.processes.discard(proc)
            await self._remove_staged(staged_paths)
            raise

        size = 0
        lock = asyncio.Lock()

        async def emit(event: dict[str, Any]) -> None:
            async with lock:
                await response.write(json.dumps(event).encode() + b"\n")

        async def feed() -> None:
            assert proc.stdin is not None
            try:
                proc.stdin.write(stdin)
                await proc.stdin.drain()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                proc.stdin.close()

        async def read(stream: asyncio.StreamReader, kind: str) -> None:
            nonlocal size
            redactor = StreamingRedactor(self.redactions)
            while block := await stream.read(32768):
                size += len(block)
                if size > self.max_output:
                    raise ValueError("command output limit")
                safe = redactor.feed(block)
                if safe:
                    self.log({"type": kind, "id": command_id, "text": safe.decode(errors="replace")})
                    await emit({"type": kind, "data": base64.b64encode(safe).decode()})
            tail = redactor.feed(b"", final=True)
            if tail:
                self.log({"type": kind, "id": command_id, "text": tail.decode(errors="replace")})
                await emit({"type": kind, "data": base64.b64encode(tail).decode()})

        assert proc.stdout is not None and proc.stderr is not None
        code = 125
        try:
            async with asyncio.timeout(_remaining(deadline)):
                await asyncio.gather(feed(), read(proc.stdout, "stdout"), read(proc.stderr, "stderr"))
                code = await proc.wait()
        except (TimeoutError, ValueError, ConnectionError, asyncio.CancelledError):
            self.active = False
            await self._kill_worker()
            if proc.returncode is None:
                proc.kill()
            await proc.wait()
        finally:
            self.processes.discard(proc)
            await self._remove_staged(staged_paths)
            self.log({"type": "command_end", "id": command_id, "code": code,
                      "bytes": size, "seconds": time.monotonic() - start})
        try:
            await emit({"type": "exit", "code": code})
        except ConnectionError:
            pass
        return response

    async def _stage_files(
        self,
        validated: ValidatedCommand,
        command_id: str,
        deadline: float | None = None,
    ) -> tuple[tuple[str, ...], list[str]]:
        deadline = deadline or (time.monotonic() + self.max_seconds)
        argv = list(validated.argv)
        staged: list[str] = []
        try:
            for number, (argument_index, path) in enumerate(validated.file_arguments):
                content = await asyncio.to_thread(read_workspace_file, self.workspace, path, self.max_input_file)
                remote = f"/tmp/lc-eval-input-{command_id}-{number}"
                # Track before the write so a partial file is removed after a
                # failed or timed-out staging subprocess.
                staged.append(remote)
                writer = await asyncio.create_subprocess_exec(
                    "docker", "exec", "-i", "--workdir", "/tmp", self.worker,
                    "/usr/local/bin/python", "-I", "-c", _STAGE_SCRIPT, remote,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.PIPE,
                )
                try:
                    _, error = await asyncio.wait_for(
                        writer.communicate(content), timeout=min(30, _remaining(deadline))
                    )
                except BaseException as exc:
                    if writer.returncode is None:
                        writer.kill()
                    await writer.wait()
                    if isinstance(exc, TimeoutError):
                        raise RuntimeError("timed out staging a workspace input file") from exc
                    raise
                if writer.returncode != 0:
                    raise RuntimeError(
                        "failed to stage a workspace input file: " + error.decode(errors="replace")
                    )
                argv[argument_index] = _replace_inline_path(argv[argument_index], remote)
        except BaseException:
            await self._remove_staged(staged)
            raise
        return tuple(argv), staged

    async def _remove_staged(self, paths: list[str]) -> None:
        if not paths:
            return
        try:
            cleaner = await asyncio.create_subprocess_exec(
                "docker", "exec", self.worker, "rm", "-f", "--", *paths,
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
            )
            await cleaner.wait()
        except OSError:
            self.active = False

    async def _kill_worker(self) -> None:
        try:
            killer = await asyncio.create_subprocess_exec(
                "docker", "kill", self.worker,
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
            )
            await killer.wait()
        except OSError:
            pass

    async def _abort_process(self, proc: asyncio.subprocess.Process) -> None:
        self.active = False
        await self._kill_worker()
        if proc.returncode is None:
            proc.kill()
        await proc.wait()

    async def start(self) -> None:
        self.socket_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        path = self.socket_dir / "broker.sock"
        path.unlink(missing_ok=True)
        app = web.Application(client_max_size=24_000_000)
        app.router.add_post("/execute", self.execute)
        self.runner = web.AppRunner(app)
        await self.runner.setup()
        await web.UnixSite(self.runner, str(path)).start()
        os.chmod(path, 0o666)

    async def close(self) -> None:
        self.active = False
        if self.runner:
            await self.runner.cleanup()


def _split_option(argument: str) -> tuple[str, str | None]:
    if not argument.startswith("-"):
        return "", None
    if "=" in argument:
        option, value = argument.split("=", 1)
        if not value:
            raise PolicyError(f"option {option} requires a value")
        return option, value
    return argument, None


def _workspace_path(value: str) -> PurePosixPath:
    if not value or "\0" in value:
        raise PolicyError("file path is invalid")
    candidate = PurePosixPath(value)
    if candidate.is_absolute():
        try:
            relative = candidate.relative_to("/work")
        except ValueError as exc:
            raise PolicyError("file arguments must be contained in /work") from exc
    else:
        relative = candidate
    if not relative.parts or relative == PurePosixPath(".") or ".." in relative.parts:
        raise PolicyError("file arguments must name a file below /work")
    return PurePosixPath("/work") / relative


def _replace_inline_path(argument: str, replacement: str) -> str:
    if "=" not in argument:
        return replacement
    option, _ = argument.split("=", 1)
    return f"{option}={replacement}"


def read_workspace_file(workspace: Path, path: PurePosixPath, max_bytes: int) -> bytes:
    """Read a regular /work file without following any symlink component."""
    relative = path.relative_to("/work")
    root_fd = os.open(workspace, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    opened = [root_fd]
    try:
        current = root_fd
        for component in relative.parts[:-1]:
            current = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
            opened.append(current)
        file_fd = os.open(
            relative.parts[-1],
            os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW,
            dir_fd=current,
        )
        opened.append(file_fd)
        info = os.fstat(file_fd)
        if not stat.S_ISREG(info.st_mode):
            raise PolicyError("file argument must be a regular file")
        if info.st_size > max_bytes:
            raise PolicyError("file argument exceeds the input limit")
        with os.fdopen(os.dup(file_fd), "rb") as file:
            content = file.read(max_bytes + 1)
        if len(content) > max_bytes:
            raise PolicyError("file argument exceeds the input limit")
        return content
    except OSError as exc:
        raise PolicyError("file argument is missing, inaccessible, or contains a symlink") from exc
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)


def _remaining(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("CLI request deadline expired")
    return remaining


def _invocation_event(event_type: str, argv: object, cwd: object, reason: str | None = None) -> dict[str, Any]:
    encoded = json.dumps(argv, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    shape: list[str] = []
    if isinstance(argv, list):
        for argument in argv:
            if not isinstance(argument, str):
                shape.append("[INVALID]")
                continue
            option = argument.split("=", 1)[0] if argument.startswith("-") else None
            if option is not None:
                shape.append(option if option in _DIAGNOSTIC_OPTIONS else "[OPTION]")
            elif argument in _DIAGNOSTIC_TOKENS:
                shape.append(argument)
            else:
                shape.append("[VALUE]")
    event: dict[str, Any] = {
        "type": event_type,
        "argv_sha256": hashlib.sha256(encoded).hexdigest(),
        "argv_shape": shape,
        "argc": len(argv) if isinstance(argv, list) else None,
        "cwd": "/work" if cwd == "/work" else "[INVALID]",
    }
    if reason is not None:
        event["reason"] = reason
    return event
