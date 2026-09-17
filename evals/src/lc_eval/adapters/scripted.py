"""Deterministic adapter for controller and grader tests."""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .base import (
    AdapterCapabilities,
    AdapterEvent,
    AdapterStateError,
    BaseAdapter,
    CollectedRun,
    PreparedRun,
    Usage,
)


@dataclass(frozen=True)
class ScriptedStep:
    event_type: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    delay_seconds: float = 0.0

    def __post_init__(self) -> None:
        if self.delay_seconds < 0:
            raise ValueError("delay_seconds cannot be negative")


class ScriptedAdapter(BaseAdapter):
    """Emits declared events only; it never claims to be a model harness."""

    def __init__(
        self,
        *,
        trial_id: str,
        steps: Sequence[ScriptedStep],
        exit_code: int = 0,
        usage: Usage | None = None,
        result_text: str | None = None,
        workdir: Path = Path("/work"),
    ) -> None:
        self.trial_id = trial_id
        self.steps = tuple(steps)
        self.exit_code = exit_code
        self.usage = usage or Usage()
        self.result_text = result_text
        self.workdir = workdir
        self._prepared: PreparedRun | None = None
        self._events: list[AdapterEvent] = []
        self._queue: asyncio.Queue[AdapterEvent | None] = asyncio.Queue()
        self._task: asyncio.Task[None] | None = None
        self._stopped = False

    @classmethod
    def capabilities(cls) -> AdapterCapabilities:
        return AdapterCapabilities(
            name="scripted",
            native_stream=False,
            shell=False,
            files=False,
            fresh_session=True,
            external_isolation_required=False,
            limitations=("test/reference runner; not an AI harness",),
        )

    def prepare(
        self,
        public_spec: str,
        execution_env: Mapping[str, str] | None = None,
    ) -> PreparedRun:
        if self._task is not None:
            raise AdapterStateError("scripted adapter has already started")
        self._prepared = PreparedRun(
            argv=("<scripted>",),
            prompt=public_spec,
            cwd=self.workdir,
            env=dict(execution_env or {}),
        )
        return self._prepared

    async def start(self) -> None:
        if self._prepared is None:
            raise AdapterStateError("prepare must be called before start")
        if self._task is not None:
            raise AdapterStateError("scripted adapter has already started")
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        try:
            for step in self.steps:
                if step.delay_seconds:
                    await asyncio.sleep(step.delay_seconds)
                event = AdapterEvent(
                    sequence=len(self._events) + 1,
                    event_type=step.event_type,
                    payload=dict(step.payload),
                    monotonic_time=time.monotonic(),
                )
                self._events.append(event)
                self._queue.put_nowait(event)
        except asyncio.CancelledError:
            self._stopped = True
        finally:
            self._queue.put_nowait(None)

    async def _iterate_events(self) -> AsyncIterator[AdapterEvent]:
        while True:
            event = await self._queue.get()
            if event is None:
                break
            yield event

    def events(self) -> AsyncIterator[AdapterEvent]:
        return self._iterate_events()

    async def stop(self, deadline: float | None = None) -> None:
        if self._task is None or self._task.done():
            return
        self._stopped = True
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass

    async def collect(self) -> CollectedRun:
        if self._task is None or self._prepared is None:
            raise AdapterStateError("scripted adapter has not started")
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        return CollectedRun(
            argv=self._prepared.argv,
            exit_code=-15 if self._stopped else self.exit_code,
            stdout=b"",
            stderr=b"",
            native_events=(),
            events=tuple(self._events),
            usage=self.usage,
            result_text=self.result_text,
            stopped=self._stopped,
            output_truncated=False,
        )
