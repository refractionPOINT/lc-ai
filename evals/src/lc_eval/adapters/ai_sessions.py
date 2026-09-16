"""Local ai-sessions native Go coordinator and SDK bridge adapter."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .base import AdapterCapabilities, AdapterConfig, NativeSubprocessAdapter, Usage, command_argv, nonnegative_int


@dataclass(frozen=True)
class AISessionsConfig(AdapterConfig):
    max_turns: int = 30
    timeout_seconds: float = 600.0

    def __post_init__(self):
        super().__post_init__()
        if self.max_turns < 1:
            raise ValueError("max_turns must be positive")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


class AISessionsAdapter(NativeSubprocessAdapter):
    def __init__(self, config: AISessionsConfig):
        super().__init__(config)
        self.runner_config = config
        self._usage = Usage()
        self._tool_ids: set[str] = set()

    @classmethod
    def capabilities(cls):
        return AdapterCapabilities(
            name="ai_sessions", native_stream=True, shell=True, files=True,
            fresh_session=True, required_auth_files=(".credentials.json",),
            limitations=(
                "local native runner with evaluator control-plane transport; not hosted Workspace",
                "Anthropic subscription only; cache classes and total input are absent from native result events",
                "reduced cloud-tool image; native plugins and docs are explicitly pinned",
            ),
        )

    def build_argv(self):
        return command_argv(self.config.command_prefix, self.config.executable, (
            "/opt/lc-eval/workspace_runner.py", "--trial-id", self.config.trial_id,
            "--model", self.config.model, "--max-turns", str(self.runner_config.max_turns),
            "--timeout", str(self.runner_config.timeout_seconds),
        ))

    def normalize_native_event(self, event: Mapping[str, Any]):
        context = {key: event[key] for key in ("parent_tool_use_id", "subagent_type") if key in event}
        return [(kind, {**payload, **context}) for kind, payload in self._normalize(event)]

    def _normalize(self, event: Mapping[str, Any]):
        kind = event.get("type")
        payload = event.get("payload")
        payload = payload if isinstance(payload, dict) else {}
        # Nested agent completions cannot finish or replace the top-level run.
        if kind == "result" and not event.get("parent_tool_use_id"):
            text = payload.get("result")
            self._result_text = text if isinstance(text, str) else None
            self._usage = Usage(
                input_tokens=nonnegative_int(payload.get("input_tokens")),
                output_tokens=nonnegative_int(payload.get("output_tokens")),
            )
            return [("usage", {"usage": self._usage.as_dict(), "semantics": "cumulative_final"}),
                    ("completion", {"result": self._result_text, "is_error": bool(payload.get("is_error")),
                                    "subtype": payload.get("subtype")})]
        if kind == "assistant":
            return [("message", {"role": "assistant", "text": block.get("text", "")})
                    for block in payload.get("content", []) if isinstance(block, dict) and block.get("type") == "text"]
        if kind == "tool_use":
            ident = payload.get("id")
            if isinstance(ident, str) and ident in self._tool_ids:
                return []
            if isinstance(ident, str):
                self._tool_ids.add(ident)
            return [("tool_call", payload)]
        if kind == "tool_result":
            return [("tool_result", payload)]
        if kind == "user":
            return [("tool_result", block) for block in payload.get("content", [])
                    if isinstance(block, dict) and block.get("type") == "tool_result"]
        if kind == "usage_delta":
            # Retain raw observations without adding deltas to a cumulative final result.
            return [("usage", {"usage": payload, "semantics": "native_delta_unaggregated"})]
        if kind == "system":
            return [("native", {"type": kind, **payload})]
        return [("native", {"type": kind})]

    def final_usage(self):
        return self._usage
