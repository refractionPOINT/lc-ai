"""Claude Code native stream adapter."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
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


def build_claude_code_argv(
    executable: str,
    *,
    model: str,
    auth_mode: str = "subscription",
    max_budget_usd: Decimal | str | None = None,
    max_turns: int = 20,
    allowed_tools: Sequence[str] = ("Bash", "Read", "Write", "Edit"),
    command_prefix: Sequence[str] = (),
    effort: str | None = None,
) -> tuple[str, ...]:
    if auth_mode not in {"subscription", "api_key"}:
        raise ValueError("auth_mode must be 'subscription' or 'api_key'")
    if max_turns <= 0:
        raise ValueError("max_turns must be positive")
    if not model or not allowed_tools:
        raise ValueError("model and at least one allowed tool are required")
    args = [
        "-p",
        "--output-format",
        "stream-json",
        "--verbose",
        "--safe-mode",
        "--no-session-persistence",
        "--disable-slash-commands",
        "--strict-mcp-config",
        "--mcp-config",
        '{"mcpServers":{}}',
        "--dangerously-skip-permissions",
        "--permission-prompts",
        "none",
        "--tools",
        ",".join(allowed_tools),
        "--allowedTools",
        ",".join(allowed_tools),
        "--model",
        model,
        "--max-turns",
        str(max_turns),
    ]
    if auth_mode == "api_key":
        args.insert(4, "--bare")
    if max_budget_usd is not None:
        if auth_mode != "api_key":
            raise ValueError("max_budget_usd is only supported for api_key auth")
        budget = Decimal(str(max_budget_usd))
        if budget <= 0:
            raise ValueError("max_budget_usd must be positive")
        args.extend(("--max-budget-usd", format(budget, "f")))
    if effort is not None:
        args.extend(("--effort", effort))
    return command_argv(command_prefix, executable, args)


@dataclass(frozen=True)
class ClaudeCodeConfig(AdapterConfig):
    auth_mode: str = "subscription"
    max_budget_usd: Decimal | None = None
    max_turns: int = 20
    allowed_tools: tuple[str, ...] = ("Bash", "Read", "Write", "Edit")
    effort: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.auth_mode not in {"subscription", "api_key"}:
            raise ValueError("auth_mode must be 'subscription' or 'api_key'")
        if self.max_turns <= 0:
            raise ValueError("max_turns must be positive")
        if self.max_budget_usd is not None and self.auth_mode != "api_key":
            raise ValueError("max_budget_usd is only supported for api_key auth")


class ClaudeCodeAdapter(NativeSubprocessAdapter):
    def __init__(self, config: ClaudeCodeConfig) -> None:
        super().__init__(config)
        self.claude_config = config
        self._message_usage: dict[str, dict[str, int]] = {}
        self._final_usage: Usage | None = None

    @classmethod
    def capabilities(cls) -> AdapterCapabilities:
        return AdapterCapabilities(
            name="claude-code",
            native_stream=True,
            shell=True,
            files=True,
            fresh_session=True,
            limitations=("subscription spend is not dollar-metered by the adapter",),
            required_auth_files=(".credentials.json",),
        )

    def build_argv(self) -> tuple[str, ...]:
        return build_claude_code_argv(
            self.config.executable,
            model=self.config.model,
            auth_mode=self.claude_config.auth_mode,
            max_budget_usd=self.claude_config.max_budget_usd,
            max_turns=self.claude_config.max_turns,
            allowed_tools=self.claude_config.allowed_tools,
            command_prefix=self.config.command_prefix,
            effort=self.claude_config.effort,
        )

    def normalize_native_event(self, event: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
        event_type = str(event.get("type", "unknown"))
        normalized: list[tuple[str, Mapping[str, Any]]] = []
        if event_type == "assistant":
            message = event.get("message")
            if isinstance(message, dict):
                message_id = str(message.get("id") or len(self._message_usage))
                usage = _usage_dict(message.get("usage"))
                if usage is not None:
                    self._message_usage[message_id] = usage
                    normalized.append(("usage", {"usage": usage, "semantics": "message_delta"}))
                content = message.get("content")
                if isinstance(content, list):
                    for block in content:
                        if not isinstance(block, dict):
                            continue
                        kind = block.get("type")
                        if kind == "tool_use":
                            normalized.append(("tool_call", dict(block)))
                        elif kind == "text":
                            normalized.append(("message", {"role": "assistant", "text": block.get("text", "")}))
        elif event_type == "user":
            message = event.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        normalized.append(("tool_result", dict(block)))
        elif event_type == "result":
            usage = _usage_dict(event.get("usage"))
            cost = event.get("total_cost_usd")
            cost_micro = None
            if isinstance(cost, (int, float, str)) and not isinstance(cost, bool):
                try:
                    cost_micro = int(Decimal(str(cost)) * 1_000_000)
                except Exception:
                    cost_micro = None
            if usage is not None:
                self._final_usage = _to_usage(usage, cost_micro)
                normalized.append(("usage", {"usage": usage, "semantics": "cumulative_final"}))
            elif cost_micro is not None:
                self._final_usage = Usage(cost_micro_usd=cost_micro)
            result = event.get("result")
            self._result_text = result if isinstance(result, str) else None
            normalized.append(
                (
                    "completion",
                    {
                        "is_error": bool(event.get("is_error", False)),
                        "subtype": event.get("subtype"),
                        "result": self._result_text,
                    },
                )
            )
        elif event_type == "system":
            normalized.append(("lifecycle", {"type": event_type, "subtype": event.get("subtype")}))
        else:
            normalized.append(("native", {"type": event_type}))
        return normalized

    def final_usage(self) -> Usage:
        if self._final_usage is not None:
            return self._final_usage
        if not self._message_usage:
            return Usage()
        totals: dict[str, int] = {}
        for usage in self._message_usage.values():
            for key, value in usage.items():
                totals[key] = totals.get(key, 0) + value
        return _to_usage(totals, None)


def _usage_dict(value: Any) -> dict[str, int] | None:
    if not isinstance(value, dict):
        return None
    aliases = {
        "input_tokens": "input_tokens",
        "output_tokens": "output_tokens",
        "cache_read_input_tokens": "cache_read_tokens",
        "cache_creation_input_tokens": "cache_write_tokens",
    }
    result = {}
    for source, target in aliases.items():
        number = nonnegative_int(value.get(source))
        if number is not None:
            result[target] = number
    return result or None


def _to_usage(values: Mapping[str, int], cost_micro: int | None) -> Usage:
    return normalize_usage(
        input_tokens=values.get("input_tokens"),
        output_tokens=values.get("output_tokens"),
        cached_input_tokens=values.get("cache_read_tokens"),
        cache_write_input_tokens=values.get("cache_write_tokens"),
        input_tokens_are_total=False,
        cost_micro_usd=cost_micro,
    )
