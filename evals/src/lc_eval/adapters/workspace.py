"""Workspace adapter capability stub.

The remote workspace does not yet demonstrate the controlled image, CLI trace,
credential isolation, or artifact guarantees required by this evaluation.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping

from .base import (
    AdapterCapabilities,
    AdapterEvent,
    BaseAdapter,
    CollectedRun,
    PreparedRun,
    UnsupportedAdapterError,
)


_REASON = (
    "workspace is unsupported for controlled-cli-v1: runner image/CLI pinning, "
    "clean session memory, complete tool traces, isolated credentials, and "
    "bounded artifact retrieval have not been established"
)


class WorkspaceAdapter(BaseAdapter):
    @classmethod
    def capabilities(cls) -> AdapterCapabilities:
        return AdapterCapabilities(
            name="workspace",
            native_stream=False,
            shell=False,
            files=False,
            fresh_session=False,
            supported=False,
            limitations=(_REASON,),
        )

    def prepare(
        self,
        public_spec: str,
        execution_env: Mapping[str, str] | None = None,
    ) -> PreparedRun:
        raise UnsupportedAdapterError(_REASON)

    async def start(self) -> None:
        raise UnsupportedAdapterError(_REASON)

    async def _events(self) -> AsyncIterator[AdapterEvent]:
        raise UnsupportedAdapterError(_REASON)
        yield  # pragma: no cover

    def events(self) -> AsyncIterator[AdapterEvent]:
        return self._events()

    async def stop(self, deadline: float | None = None) -> None:
        return None

    async def collect(self) -> CollectedRun:
        raise UnsupportedAdapterError(_REASON)
