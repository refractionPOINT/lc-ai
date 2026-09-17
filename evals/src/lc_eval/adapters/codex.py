"""Codex native JSONL adapter."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .base import (
    AdapterCapabilities,
    AdapterConfig,
    NativeSubprocessAdapter,
    Usage,
    command_argv,
    nonnegative_int,
    normalize_usage,
)


_ALLOWED_CONFIG_OVERRIDES = frozenset({"model_reasoning_effort"})


def _validate_config_override(value: str) -> None:
    key, separator, setting = value.partition("=")
    if not separator or not setting.strip():
        raise ValueError("Codex config overrides must use key=value syntax")
    if key.strip() not in _ALLOWED_CONFIG_OVERRIDES:
        raise ValueError(f"Codex config override is not allowed: {key.strip() or '<empty>'}")


def build_codex_argv(
    executable: str,
    *,
    model: str,
    command_prefix: Sequence[str] = (),
    config_overrides: Sequence[str] = (),
    externally_isolated: bool = True,
    context_mode: str = "legacy",
) -> tuple[str, ...]:
    if not model:
        raise ValueError("model is required")
    if not externally_isolated:
        raise ValueError("the controlled Codex profile requires external isolation")
    if context_mode not in {"legacy", "bare", "lc_ai"}:
        raise ValueError("invalid context_mode")
    for override in config_overrides:
        _validate_config_override(override)
    args = [
        "exec",
        "--json",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--dangerously-bypass-approvals-and-sandbox",
        "--model",
        model,
    ]
    for override in config_overrides:
        args.extend(("--config", override))
    args.append("-")
    return command_argv(command_prefix, executable, args)


@dataclass(frozen=True)
class CodexConfig(AdapterConfig):
    auth_mode: str = "subscription"
    config_overrides: tuple[str, ...] = ()
    externally_isolated: bool = True
    max_tool_calls: int = 80
    context_mode: str = "legacy"

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.auth_mode not in {"subscription", "api_key"}:
            raise ValueError("auth_mode must be 'subscription' or 'api_key'")
        if self.max_tool_calls <= 0:
            raise ValueError("max_tool_calls must be positive")
        for override in self.config_overrides:
            _validate_config_override(override)
        if self.context_mode not in {"legacy", "bare", "lc_ai"}:
            raise ValueError("invalid context_mode")


class CodexAdapter(NativeSubprocessAdapter):
    def __init__(self, config: CodexConfig) -> None:
        super().__init__(config)
        self.codex_config = config
        self._final_usage: Usage | None = None
        self._tool_calls_started = 0
        self._tool_calls_completed = 0

    @classmethod
    def capabilities(cls) -> AdapterCapabilities:
        return AdapterCapabilities(
            name="codex",
            native_stream=True,
            shell=True,
            files=True,
            fresh_session=True,
            limitations=(
                "requires externally enforced container isolation",
                "subscription spend is not dollar-metered by the adapter",
            ),
            required_auth_files=("auth.json",),
        )

    def build_argv(self) -> tuple[str, ...]:
        return build_codex_argv(
            self.config.executable,
            model=self.config.model,
            command_prefix=self.config.command_prefix,
            config_overrides=self.codex_config.config_overrides,
            externally_isolated=self.codex_config.externally_isolated,
            context_mode=self.codex_config.context_mode,
        )

    def normalize_native_event(self, event: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
        event_type = str(event.get("type", "unknown"))
        normalized: list[tuple[str, Mapping[str, Any]]] = []
        item = event.get("item")
        if event_type == "item.started" and isinstance(item, dict):
            if item.get("type") in {"command_execution", "mcp_tool_call", "web_search"}:
                self._tool_calls_started += 1
                normalized.append(
                    (
                        "tool_call",
                        {**item, "tool_call_number": self._tool_calls_started},
                    )
                )
            else:
                normalized.append(("item_started", dict(item)))
        elif event_type == "item.completed" and isinstance(item, dict):
            kind = item.get("type")
            if kind == "agent_message":
                text = item.get("text")
                if isinstance(text, str):
                    self._result_text = text
                normalized.append(("message", {"role": "assistant", "text": text or ""}))
            elif kind in {"command_execution", "mcp_tool_call", "web_search"}:
                self._tool_calls_completed += 1
                normalized.append(
                    (
                        "tool_result",
                        {**item, "tool_call_number": self._tool_calls_completed},
                    )
                )
                if self._tool_calls_completed >= self.codex_config.max_tool_calls:
                    normalized.append(
                        (
                            "limit_reached",
                            {
                                "limit": "tool_calls",
                                "maximum": self.codex_config.max_tool_calls,
                            },
                        )
                    )
            else:
                normalized.append(("item_completed", dict(item)))
        elif event_type in {"turn.completed", "thread.completed"}:
            usage = _codex_usage(event.get("usage"))
            if usage is not None:
                self._final_usage = usage
                normalized.append(("usage", {"usage": usage.as_dict(), "semantics": "cumulative_final"}))
            normalized.append(("completion", {"type": event_type}))
        elif event_type in {"turn.failed", "error"}:
            normalized.append(("error", dict(event)))
        elif event_type in {"thread.started", "turn.started"}:
            normalized.append(("lifecycle", {"type": event_type, "thread_id": event.get("thread_id")}))
        else:
            normalized.append(("native", {"type": event_type}))
        return normalized

    def final_usage(self) -> Usage:
        return self._final_usage or Usage()


def _codex_usage(value: Any) -> Usage | None:
    if not isinstance(value, dict):
        return None
    input_tokens = nonnegative_int(value.get("input_tokens"))
    output_tokens = nonnegative_int(value.get("output_tokens"))
    cached = nonnegative_int(value.get("cached_input_tokens"))
    cache_write = nonnegative_int(value.get("cache_write_input_tokens"))
    if cached is None:
        details = value.get("input_tokens_details")
        if isinstance(details, dict):
            cached = nonnegative_int(details.get("cached_tokens"))
    if all(item is None for item in (input_tokens, output_tokens, cached, cache_write)):
        return None
    return normalize_usage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_input_tokens=cached,
        cache_write_input_tokens=cache_write,
        input_tokens_are_total=True,
    )
