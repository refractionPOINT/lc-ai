"""Harness adapter registry."""

from .base import (
    AdapterCapabilities,
    AdapterConfig,
    AdapterError,
    AdapterEvent,
    AdapterStateError,
    BaseAdapter,
    CollectedRun,
    PreparedRun,
    UnsupportedAdapterError,
    Usage,
    normalize_usage,
)
from .claude_code import ClaudeCodeAdapter, ClaudeCodeConfig, build_claude_code_argv
from .codex import CodexAdapter, CodexConfig, build_codex_argv
from .scripted import ScriptedAdapter, ScriptedStep
from .workspace import WorkspaceAdapter

ADAPTERS: dict[str, type[BaseAdapter]] = {
    "claude-code": ClaudeCodeAdapter,
    "codex": CodexAdapter,
    "scripted": ScriptedAdapter,
    "workspace": WorkspaceAdapter,
}


def adapter_class(name: str) -> type[BaseAdapter]:
    try:
        return ADAPTERS[name]
    except KeyError as exc:
        raise ValueError(f"unknown adapter: {name}") from exc


__all__ = [
    "ADAPTERS",
    "AdapterCapabilities",
    "AdapterConfig",
    "AdapterError",
    "AdapterEvent",
    "AdapterStateError",
    "BaseAdapter",
    "ClaudeCodeAdapter",
    "ClaudeCodeConfig",
    "CodexAdapter",
    "CodexConfig",
    "CollectedRun",
    "PreparedRun",
    "ScriptedAdapter",
    "ScriptedStep",
    "UnsupportedAdapterError",
    "Usage",
    "WorkspaceAdapter",
    "adapter_class",
    "build_claude_code_argv",
    "build_codex_argv",
    "normalize_usage",
]
