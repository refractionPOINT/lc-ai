"""Harness adapter contracts and a safe asynchronous subprocess implementation."""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import signal
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class AdapterError(RuntimeError):
    """Base class for adapter failures."""


class AdapterStateError(AdapterError):
    """Raised when adapter lifecycle methods are called out of order."""


class UnsupportedAdapterError(AdapterError):
    """Raised when an adapter cannot satisfy the controlled execution profile."""


@dataclass(frozen=True)
class AdapterCapabilities:
    name: str
    native_stream: bool
    shell: bool
    files: bool
    fresh_session: bool
    external_isolation_required: bool = True
    supported: bool = True
    limitations: tuple[str, ...] = ()
    required_auth_files: tuple[str, ...] = ()


@dataclass(frozen=True)
class AdapterConfig:
    trial_id: str
    model: str
    workdir: Path
    executable: str
    command_prefix: tuple[str, ...] = ()
    environment: Mapping[str, str] = field(default_factory=dict)
    max_output_bytes: int = 16 * 1024 * 1024
    shutdown_grace_seconds: float = 15.0

    def __post_init__(self) -> None:
        if not self.trial_id or not self.model or not self.executable:
            raise ValueError("trial_id, model, and executable are required")
        if self.max_output_bytes <= 0 or self.shutdown_grace_seconds <= 0:
            raise ValueError("adapter limits must be positive")


@dataclass(frozen=True)
class PreparedRun:
    argv: tuple[str, ...]
    prompt: str
    cwd: Path
    env: Mapping[str, str]


@dataclass(frozen=True)
class AdapterEvent:
    sequence: int
    event_type: str
    payload: Mapping[str, Any]
    stream: str = "stdout"
    monotonic_time: float = field(default_factory=time.monotonic)


@dataclass(frozen=True)
class Usage:
    """Provider-neutral token usage.

    ``input_tokens`` is always the uncached input count.  Cache reads and cache
    writes are separate input classes.  ``total_input_tokens`` preserves an
    explicitly reported provider total, or is derived only when every input
    class is known.
    """

    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_read_tokens: int | None = None
    cache_write_tokens: int | None = None
    cost_micro_usd: int | None = None
    total_input_tokens: int | None = None

    def as_dict(self) -> dict[str, int | None]:
        return {
            "input_tokens": self.input_tokens,
            "total_input_tokens": self.total_input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cached_input_tokens": self.cache_read_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "cache_write_input_tokens": self.cache_write_tokens,
            "cost_micro_usd": self.cost_micro_usd,
        }


def normalize_usage(
    *,
    input_tokens: int | None,
    output_tokens: int | None,
    cached_input_tokens: int | None,
    cache_write_input_tokens: int | None,
    input_tokens_are_total: bool,
    cost_micro_usd: int | None = None,
) -> Usage:
    """Normalize native usage without converting missing cache counts to zero.

    Codex reports total input with cached input as a subset.  Claude reports
    uncached, cache-read, and cache-write input as disjoint counts.  This helper
    makes both forms produce the same :class:`Usage` convention.
    """

    if input_tokens_are_total:
        total = input_tokens
        uncached = (
            None
            if input_tokens is None or cached_input_tokens is None
            else max(0, input_tokens - cached_input_tokens)
        )
    else:
        uncached = input_tokens
        total = (
            input_tokens + cached_input_tokens + cache_write_input_tokens
            if input_tokens is not None
            and cached_input_tokens is not None
            and cache_write_input_tokens is not None
            else None
        )
    return Usage(
        input_tokens=uncached,
        output_tokens=output_tokens,
        cache_read_tokens=cached_input_tokens,
        cache_write_tokens=cache_write_input_tokens,
        cost_micro_usd=cost_micro_usd,
        total_input_tokens=total,
    )


@dataclass(frozen=True)
class CollectedRun:
    argv: tuple[str, ...]
    exit_code: int
    stdout: bytes
    stderr: bytes
    native_events: tuple[Mapping[str, Any], ...]
    events: tuple[AdapterEvent, ...]
    usage: Usage
    result_text: str | None
    stopped: bool
    output_truncated: bool


class BaseAdapter(ABC):
    @classmethod
    @abstractmethod
    def capabilities(cls) -> AdapterCapabilities:
        raise NotImplementedError

    @abstractmethod
    def prepare(
        self,
        public_spec: str,
        execution_env: Mapping[str, str] | None = None,
    ) -> PreparedRun:
        raise NotImplementedError

    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def events(self) -> AsyncIterator[AdapterEvent]:
        raise NotImplementedError

    @abstractmethod
    async def stop(self, deadline: float | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    async def collect(self) -> CollectedRun:
        raise NotImplementedError


class NativeSubprocessAdapter(BaseAdapter):
    """Common lifecycle for line-oriented native harness event streams.

    stdout and stderr are drained from process start, independently of whether a
    caller iterates :meth:`events`, so a noisy child cannot deadlock on a pipe.
    """

    def __init__(self, config: AdapterConfig) -> None:
        self.config = config
        self._prepared: PreparedRun | None = None
        self._process: asyncio.subprocess.Process | None = None
        self._stdout = bytearray()
        self._stderr = bytearray()
        self._native_events: list[Mapping[str, Any]] = []
        self._events: list[AdapterEvent] = []
        self._queue: asyncio.Queue[AdapterEvent | None] = asyncio.Queue()
        self._readers: list[asyncio.Task[None]] = []
        self._completion: asyncio.Task[None] | None = None
        self._done = asyncio.Event()
        self._stopped = False
        self._truncated = False
        self._result_text: str | None = None

    @abstractmethod
    def build_argv(self) -> tuple[str, ...]:
        raise NotImplementedError

    @abstractmethod
    def normalize_native_event(self, event: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
        raise NotImplementedError

    @abstractmethod
    def final_usage(self) -> Usage:
        raise NotImplementedError

    def prepare(
        self,
        public_spec: str,
        execution_env: Mapping[str, str] | None = None,
    ) -> PreparedRun:
        if self._process is not None:
            raise AdapterStateError("cannot prepare a running adapter")
        env = dict(self.config.environment)
        env.update(execution_env or {})
        self._prepared = PreparedRun(
            argv=self.build_argv(),
            prompt=public_spec,
            cwd=self.config.workdir,
            env=env,
        )
        return self._prepared

    async def start(self) -> None:
        if self._prepared is None:
            raise AdapterStateError("prepare must be called before start")
        if self._process is not None:
            raise AdapterStateError("adapter has already started")
        self._process = await asyncio.create_subprocess_exec(
            *self._prepared.argv,
            cwd=self._prepared.cwd,
            env=dict(self._prepared.env),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )
        assert self._process.stdin is not None
        self._process.stdin.write(self._prepared.prompt.encode("utf-8"))
        if not self._prepared.prompt.endswith("\n"):
            self._process.stdin.write(b"\n")
        await self._process.stdin.drain()
        self._process.stdin.close()
        with contextlib.suppress(BrokenPipeError, ConnectionResetError):
            await self._process.stdin.wait_closed()
        assert self._process.stdout is not None and self._process.stderr is not None
        self._readers = [
            asyncio.create_task(self._read_stream("stdout", self._process.stdout)),
            asyncio.create_task(self._read_stream("stderr", self._process.stderr)),
        ]
        self._completion = asyncio.create_task(self._finish())

    async def _read_stream(self, name: str, stream: asyncio.StreamReader) -> None:
        pending = bytearray()
        while True:
            chunk = await stream.read(64 * 1024)
            if not chunk:
                break
            self._append_output(name, chunk)
            pending.extend(chunk)
            while b"\n" in pending:
                line, _, remainder = pending.partition(b"\n")
                pending = bytearray(remainder)
                self._consume_line(name, bytes(line))
        if pending:
            self._consume_line(name, bytes(pending))

    def _append_output(self, name: str, chunk: bytes) -> None:
        target = self._stdout if name == "stdout" else self._stderr
        remaining = self.config.max_output_bytes - len(target)
        if remaining > 0:
            target.extend(chunk[:remaining])
        if len(chunk) > remaining:
            self._truncated = True

    def _consume_line(self, stream: str, line: bytes) -> None:
        text = line.decode("utf-8", errors="replace")
        parsed: Mapping[str, Any] | None = None
        if stream == "stdout":
            try:
                candidate = json.loads(text)
                if isinstance(candidate, dict):
                    parsed = candidate
            except json.JSONDecodeError:
                pass
        if parsed is None:
            self._emit(f"{stream}_text", {"text": text}, stream=stream)
            return
        native = {"stream": stream, "event": parsed, "raw": text}
        self._native_events.append(native)
        for event_type, payload in self.normalize_native_event(parsed):
            self._emit(event_type, payload, stream=stream)

    def _emit(self, event_type: str, payload: Mapping[str, Any], *, stream: str = "stdout") -> None:
        event = AdapterEvent(
            sequence=len(self._events) + 1,
            event_type=event_type,
            payload=dict(payload),
            stream=stream,
        )
        self._events.append(event)
        self._queue.put_nowait(event)

    async def _finish(self) -> None:
        assert self._process is not None
        await self._process.wait()
        await asyncio.gather(*self._readers)
        self._queue.put_nowait(None)
        self._done.set()

    async def _iterate_events(self) -> AsyncIterator[AdapterEvent]:
        while True:
            event = await self._queue.get()
            if event is None:
                break
            yield event

    def events(self) -> AsyncIterator[AdapterEvent]:
        return self._iterate_events()

    async def stop(self, deadline: float | None = None) -> None:
        process = self._process
        if process is None:
            return
        if process.returncode is not None:
            await self._done.wait()
            return
        self._stopped = True
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGTERM)
        timeout = self.config.shutdown_grace_seconds
        if deadline is not None:
            timeout = max(0.0, deadline - time.monotonic()) if deadline > time.monotonic() else max(0.0, deadline)
        try:
            await asyncio.wait_for(self._done.wait(), timeout=timeout)
        except TimeoutError:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            await self._done.wait()

    async def collect(self) -> CollectedRun:
        if self._process is None or self._prepared is None:
            raise AdapterStateError("adapter has not started")
        await self._done.wait()
        assert self._process.returncode is not None
        return CollectedRun(
            argv=self._prepared.argv,
            exit_code=self._process.returncode,
            stdout=bytes(self._stdout),
            stderr=bytes(self._stderr),
            native_events=tuple(self._native_events),
            events=tuple(self._events),
            usage=self.final_usage(),
            result_text=self._result_text,
            stopped=self._stopped,
            output_truncated=self._truncated,
        )


def command_argv(prefix: Sequence[str], executable: str, arguments: Sequence[str]) -> tuple[str, ...]:
    """Build an argv without shell interpolation."""
    if not executable or "\x00" in executable:
        raise ValueError("invalid executable")
    values = (*prefix, executable, *arguments)
    if any("\x00" in value for value in values):
        raise ValueError("argv values may not contain NUL")
    return tuple(values)


def nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    return None
