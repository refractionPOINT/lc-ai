from __future__ import annotations

import asyncio
import os
import sys
import time
from decimal import Decimal

import pytest

from lc_eval.adapters import (
    AdapterConfig,
    ClaudeCodeAdapter,
    ClaudeCodeConfig,
    CodexAdapter,
    CodexConfig,
    ScriptedAdapter,
    ScriptedStep,
    UnsupportedAdapterError,
    WorkspaceAdapter,
    build_claude_code_argv,
    build_codex_argv,
)
from lc_eval.adapters.base import NativeSubprocessAdapter, Usage, command_argv, normalize_usage


def test_native_argv_builders_keep_prompt_on_stdin_and_auth_modes_separate() -> None:
    claude = build_claude_code_argv(
        "claude",
        model="fixed-claude",
        auth_mode="subscription",
        max_turns=9,
        command_prefix=("docker", "exec", "candidate"),
    )
    assert claude[:4] == ("docker", "exec", "candidate", "claude")
    assert "--bare" not in claude
    assert "--max-budget-usd" not in claude
    assert claude[-2:] == ("--max-turns", "9")
    assert "--dangerously-skip-permissions" in claude
    assert claude[claude.index("--mcp-config") + 1] == '{"mcpServers":{}}'

    api_key = build_claude_code_argv(
        "claude", model="fixed-claude", auth_mode="api_key", max_budget_usd=Decimal("1.25")
    )
    assert "--bare" in api_key
    assert api_key[api_key.index("--max-budget-usd") + 1] == "1.25"

    codex = build_codex_argv("codex", model="fixed-codex")
    assert codex[-1] == "-"
    assert "--ephemeral" in codex
    assert "--dangerously-bypass-approvals-and-sandbox" in codex
    with pytest.raises(ValueError, match="external isolation"):
        build_codex_argv("codex", model="fixed-codex", externally_isolated=False)
    with pytest.raises(ValueError, match="not allowed"):
        build_codex_argv(
            "codex", model="fixed-codex", config_overrides=('model="different-model"',)
        )


def test_claude_cumulative_result_usage_does_not_double_count(tmp_path) -> None:
    adapter = ClaudeCodeAdapter(
        ClaudeCodeConfig(
            trial_id="t",
            model="m",
            workdir=tmp_path,
            executable="claude",
            auth_mode="api_key",
        )
    )
    first = {
        "type": "assistant",
        "message": {
            "id": "msg-1",
            "content": [{"type": "text", "text": "working"}],
            "usage": {"input_tokens": 10, "output_tokens": 4},
        },
    }
    duplicate = dict(first)
    final = {
        "type": "result",
        "result": "done",
        "usage": {
            "input_tokens": 10,
            "output_tokens": 6,
            "cache_read_input_tokens": 3,
            "cache_creation_input_tokens": 2,
        },
        "total_cost_usd": 0.012345,
    }
    adapter.normalize_native_event(first)
    adapter.normalize_native_event(duplicate)
    adapter.normalize_native_event(final)
    assert adapter.final_usage() == Usage(10, 6, 3, 2, 12_345, 15)


def test_claude_subscription_usage_does_not_claim_dollar_cost(tmp_path) -> None:
    adapter = ClaudeCodeAdapter(
        ClaudeCodeConfig(
            trial_id="t",
            model="m",
            workdir=tmp_path,
            executable="claude",
            auth_mode="subscription",
        )
    )
    adapter.normalize_native_event(
        {
            "type": "result",
            "result": "done",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 6,
                "cache_read_input_tokens": 3,
                "cache_creation_input_tokens": 2,
            },
            "total_cost_usd": 0.012345,
        }
    )
    assert adapter.final_usage() == Usage(10, 6, 3, 2, None, 15)


def test_missing_usage_remains_unknown(tmp_path) -> None:
    claude = ClaudeCodeAdapter(
        ClaudeCodeConfig(trial_id="t", model="m", workdir=tmp_path, executable="claude")
    )
    claude.normalize_native_event({"type": "result", "result": "done"})
    assert claude.final_usage() == Usage()
    codex = CodexAdapter(CodexConfig(trial_id="t", model="m", workdir=tmp_path, executable="codex"))
    codex.normalize_native_event({"type": "turn.completed"})
    assert codex.final_usage() == Usage()


def test_codex_usage_and_tool_events(tmp_path) -> None:
    adapter = CodexAdapter(
        CodexConfig(trial_id="t", model="m", workdir=tmp_path, executable="codex")
    )
    events = adapter.normalize_native_event(
        {"type": "item.started", "item": {"id": "i", "type": "command_execution", "command": "pwd"}}
    )
    assert events[0][0] == "tool_call"
    adapter.normalize_native_event(
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 100,
                "cached_input_tokens": 70,
                "cache_write_input_tokens": 0,
                "output_tokens": 8,
            },
        }
    )
    assert adapter.final_usage() == Usage(
        input_tokens=30,
        output_tokens=8,
        cache_read_tokens=70,
        cache_write_tokens=0,
        total_input_tokens=100,
    )


def test_normalize_usage_preserves_unknowns_and_emits_metric_aliases() -> None:
    unknown_cache = normalize_usage(
        input_tokens=100,
        output_tokens=8,
        cached_input_tokens=None,
        cache_write_input_tokens=None,
        input_tokens_are_total=True,
    )
    assert unknown_cache.input_tokens is None
    assert unknown_cache.total_input_tokens == 100
    assert unknown_cache.cache_read_tokens is None

    inconsistent_cache = normalize_usage(
        input_tokens=10,
        output_tokens=1,
        cached_input_tokens=11,
        cache_write_input_tokens=0,
        input_tokens_are_total=True,
    )
    assert inconsistent_cache.input_tokens is None
    assert inconsistent_cache.total_input_tokens == 10

    claude = normalize_usage(
        input_tokens=6,
        output_tokens=253,
        cached_input_tokens=22_639,
        cache_write_input_tokens=11_565,
        input_tokens_are_total=False,
    )
    assert claude.as_dict() == {
        "input_tokens": 6,
        "total_input_tokens": 34_210,
        "output_tokens": 253,
        "cache_read_tokens": 22_639,
        "cached_input_tokens": 22_639,
        "cache_write_tokens": 11_565,
        "cache_write_input_tokens": 11_565,
        "cost_micro_usd": None,
    }


def test_codex_emits_hard_tool_call_limit_event(tmp_path) -> None:
    adapter = CodexAdapter(
        CodexConfig(
            trial_id="t",
            model="m",
            workdir=tmp_path,
            executable="codex",
            max_tool_calls=1,
        )
    )
    normalized = adapter.normalize_native_event(
        {"type": "item.completed", "item": {"id": "i", "type": "command_execution"}}
    )
    assert [event_type for event_type, _ in normalized] == ["tool_result", "limit_reached"]


class _PythonAdapter(NativeSubprocessAdapter):
    @classmethod
    def capabilities(cls):  # pragma: no cover - irrelevant test helper
        raise NotImplementedError

    def __init__(self, config: AdapterConfig, script: str) -> None:
        super().__init__(config)
        self.script = script

    def build_argv(self) -> tuple[str, ...]:
        return command_argv((), self.config.executable, ("-c", self.script))

    def normalize_native_event(self, event):
        return [(str(event.get("type", "native")), event)]

    def final_usage(self):
        return Usage()


@pytest.mark.asyncio
async def test_subprocess_drains_both_streams_and_feeds_prompt_on_stdin(tmp_path) -> None:
    script = r'''
import json, sys
p = sys.stdin.read()
sys.stdout.write(json.dumps({"type": "prompt", "value": p}) + "\n")
sys.stdout.flush()
sys.stderr.write("diagnostic\n")
sys.stderr.flush()
'''
    adapter = _PythonAdapter(
        AdapterConfig(
            trial_id="t",
            model="m",
            workdir=tmp_path,
            executable=sys.executable,
            environment=os.environ.copy(),
        ),
        script,
    )
    prepared = adapter.prepare("literal `whoami` and $(hostname)")
    assert "literal `whoami`" not in prepared.argv
    await adapter.start()
    streamed = [event async for event in adapter.events()]
    result = await adapter.collect()
    assert result.exit_code == 0
    assert result.stderr == b"diagnostic\n"
    assert streamed[0].payload["value"] == "literal `whoami` and $(hostname)\n"


@pytest.mark.asyncio
async def test_subprocess_stop_terminates_process_group_and_drains(tmp_path) -> None:
    adapter = _PythonAdapter(
        AdapterConfig(
            trial_id="t",
            model="m",
            workdir=tmp_path,
            executable=sys.executable,
            environment=os.environ.copy(),
            shutdown_grace_seconds=0.2,
        ),
        "import sys,time; print('started', flush=True); print('err', file=sys.stderr, flush=True); time.sleep(60)",
    )
    adapter.prepare("task")
    await adapter.start()

    async def wait_for_both_streams():
        observed = set()
        async for event in adapter.events():
            if event.event_type == "stdout_text" and event.payload["text"] == "started":
                observed.add("stdout")
            if event.event_type == "stderr_text" and event.payload["text"] == "err":
                observed.add("stderr")
            if len(observed) == 2:
                return

    try:
        await asyncio.wait_for(wait_for_both_streams(), 10)
    finally:
        await adapter.stop()
    result = await adapter.collect()
    assert result.stopped
    assert result.exit_code != 0
    assert result.stdout == b"started\n"
    assert result.stderr == b"err\n"


@pytest.mark.asyncio
async def test_subprocess_limit_event_stops_without_external_consumer(tmp_path) -> None:
    script = r'''
import json, time
print(json.dumps({"type": "limit_reached"}), flush=True)
time.sleep(60)
'''
    adapter = _PythonAdapter(
        AdapterConfig(
            trial_id="t",
            model="m",
            workdir=tmp_path,
            executable=sys.executable,
            environment=os.environ.copy(),
            shutdown_grace_seconds=0.2,
        ),
        script,
    )
    adapter.prepare("task")
    await adapter.start()
    result = await asyncio.wait_for(adapter.collect(), 5)
    assert result.stopped
    assert result.exit_code != 0
    assert [event.event_type for event in result.events] == ["limit_reached"]


@pytest.mark.asyncio
async def test_expired_stop_deadline_kills_without_using_timestamp_as_timeout(tmp_path) -> None:
    script = r'''
import signal, time
signal.signal(signal.SIGTERM, signal.SIG_IGN)
print("ready", flush=True)
time.sleep(60)
'''
    adapter = _PythonAdapter(
        AdapterConfig(
            trial_id="t",
            model="m",
            workdir=tmp_path,
            executable=sys.executable,
            environment=os.environ.copy(),
            shutdown_grace_seconds=30,
        ),
        script,
    )
    adapter.prepare("task")
    await adapter.start()
    async for event in adapter.events():
        if event.payload.get("text") == "ready":
            break
    await asyncio.wait_for(adapter.stop(time.monotonic() - 1), 2)
    assert (await adapter.collect()).stopped


@pytest.mark.asyncio
async def test_scripted_and_workspace_capability_semantics(tmp_path) -> None:
    adapter = ScriptedAdapter(
        trial_id="t",
        steps=[ScriptedStep("message", {"text": "ok"})],
        workdir=tmp_path,
    )
    adapter.prepare("prompt")
    await adapter.start()
    assert [event.event_type async for event in adapter.events()] == ["message"]
    assert (await adapter.collect()).exit_code == 0
    assert not WorkspaceAdapter.capabilities().supported
    assert ClaudeCodeAdapter.capabilities().required_auth_files == (".credentials.json",)
    assert CodexAdapter.capabilities().required_auth_files == ("auth.json",)
    with pytest.raises(UnsupportedAdapterError, match="unsupported"):
        WorkspaceAdapter().prepare("prompt")
