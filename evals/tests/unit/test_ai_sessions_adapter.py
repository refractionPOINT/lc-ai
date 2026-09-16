from __future__ import annotations

import pytest

from lc_eval.adapters.ai_sessions import AISessionsAdapter, AISessionsConfig
from lc_eval.adapters.base import Usage


def adapter(tmp_path, **changes) -> AISessionsAdapter:
    values = {
        "trial_id": "trial-1",
        "model": "claude-pinned",
        "workdir": tmp_path,
        "executable": "python",
        "command_prefix": ("docker", "exec", "candidate"),
    }
    values.update(changes)
    return AISessionsAdapter(AISessionsConfig(**values))


def test_argv_pins_model_turns_trial_and_timeout_without_prompt(tmp_path) -> None:
    harness = adapter(tmp_path, max_turns=17, timeout_seconds=321.5)
    prepared = harness.prepare("literal task $(hostname)")

    assert prepared.argv == (
        "docker",
        "exec",
        "candidate",
        "python",
        "/opt/lc-eval/workspace_runner.py",
        "--trial-id",
        "trial-1",
        "--model",
        "claude-pinned",
        "--max-turns",
        "17",
        "--timeout",
        "321.5",
    )
    assert prepared.prompt == "literal task $(hostname)"
    assert prepared.prompt not in prepared.argv


@pytest.mark.parametrize("field,value", [("max_turns", 0), ("timeout_seconds", 0)])
def test_config_rejects_nonpositive_native_limits(tmp_path, field, value) -> None:
    with pytest.raises(ValueError, match="positive"):
        adapter(tmp_path, **{field: value})


def test_top_level_result_sets_completion_and_conservative_usage(tmp_path) -> None:
    harness = adapter(tmp_path)
    events = harness.normalize_native_event(
        {
            "type": "result",
            "payload": {
                "subtype": "success",
                "is_error": False,
                "result": "finished",
                "input_tokens": 101,
                "output_tokens": 23,
                # The Claude bridge deliberately does not forward cache classes.
                "total_cost_usd": 1.25,
            },
        }
    )

    assert [kind for kind, _ in events] == ["usage", "completion"]
    assert events[0][1]["semantics"] == "cumulative_final"
    assert events[1][1] == {"result": "finished", "is_error": False, "subtype": "success"}
    assert harness.final_usage() == Usage(
        input_tokens=101,
        output_tokens=23,
        cache_read_tokens=None,
        cache_write_tokens=None,
        cost_micro_usd=None,
        total_input_tokens=None,
    )


def test_missing_native_usage_stays_unknown(tmp_path) -> None:
    harness = adapter(tmp_path)
    harness.normalize_native_event(
        {"type": "result", "payload": {"subtype": "success", "result": "done"}}
    )
    assert harness.final_usage() == Usage()


def test_child_result_does_not_finalize_or_replace_usage(tmp_path) -> None:
    harness = adapter(tmp_path)
    child = harness.normalize_native_event(
        {
            "type": "result",
            "parent_tool_use_id": "parent-1",
            "subagent_type": "Task",
            "payload": {
                "result": "child output",
                "input_tokens": 999,
                "output_tokens": 888,
            },
        }
    )
    assert child == [("native", {"type": "result"})]
    assert harness.final_usage() == Usage()

    harness.normalize_native_event(
        {
            "type": "result",
            "payload": {"result": "top", "input_tokens": 7, "output_tokens": 3},
        }
    )
    assert harness.final_usage() == Usage(input_tokens=7, output_tokens=3)


def test_usage_delta_is_preserved_without_becoming_final_usage(tmp_path) -> None:
    harness = adapter(tmp_path)
    payload = {"input_tokens": 11, "output_tokens": 4}
    events = harness.normalize_native_event({"type": "usage_delta", "payload": payload})
    assert events == [("usage", {"usage": payload, "semantics": "native_delta_unaggregated"})]
    assert harness.final_usage() == Usage()


def test_native_messages_and_duplicate_tool_events_are_normalized(tmp_path) -> None:
    harness = adapter(tmp_path)
    messages = harness.normalize_native_event(
        {
            "type": "assistant",
            "payload": {
                "content": [
                    {"type": "text", "text": "working"},
                    {"type": "tool_use", "id": "tool-1", "name": "Bash"},
                ]
            },
        }
    )
    assert messages == [("message", {"role": "assistant", "text": "working"})]

    tool = {"id": "tool-1", "name": "Bash", "input": {"command": "pwd"}}
    assert harness.normalize_native_event({"type": "tool_use", "payload": tool}) == [
        ("tool_call", tool)
    ]
    assert harness.normalize_native_event({"type": "tool_use", "payload": tool}) == []
