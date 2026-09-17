import json
import contextlib
from types import SimpleNamespace

import pytest

import lc_eval.context_probe as context_probe_module
from lc_eval.context_probe import PREFERRED_PASSIVE_CANARY, _body_phrase, analyze_probe, probe_prompt


CANARY = {"skill": "probe-canary", "skill_md_sha256": "a" * 64}
PHRASE = "Context probe marker omega seven lives only in this skill file."


def test_body_phrase_ignores_frontmatter_and_headings():
    text = "---\nname: probe-canary\ndescription: metadata only\n---\n# Probe\n\n" + PHRASE + "\n"
    assert _body_phrase(text) == PHRASE


def test_prompt_names_skill_but_does_not_leak_expected_phrase():
    prompt = probe_prompt("lc_ai", CANARY["skill"])
    assert CANARY["skill"] in prompt
    assert PHRASE not in prompt
    assert "native skill mechanism" in prompt
    assert "Do not execute any workflow" in prompt


def test_preferred_probe_canary_is_passive_platform_documentation():
    assert PREFERRED_PASSIVE_CANARY == "lc-fundamentals--platform-config"


def test_positive_probe_requires_marker_and_native_discovery_evidence():
    event = {
        "type": "assistant",
        "message": {"content": [
            {"type": "tool_use", "name": "Skill", "input": {"skill": CANARY["skill"]}},
            {"type": "text", "text": PHRASE},
        ]},
    }
    transcript = json.dumps(event) + "\n" + json.dumps({"type": "result", "result": PHRASE})
    evidence = analyze_probe(transcript, mode="lc_ai", canary=CANARY, phrase=PHRASE)
    assert evidence["passed"]
    assert evidence["native_skill_call_observed"]


def test_positive_probe_rejects_phrase_without_discovery_evidence():
    event = {"type": "result", "result": PHRASE}
    evidence = analyze_probe(json.dumps(event), mode="lc_ai", canary=CANARY, phrase=PHRASE)
    assert not evidence["passed"]


def test_bare_probe_passes_only_when_canary_is_not_discovered():
    clean = analyze_probe(
        json.dumps({"type": "result", "result": "skill unavailable"}),
        mode="bare", canary=CANARY, phrase=PHRASE,
    )
    leaked = analyze_probe(
        json.dumps({"type": "tool_use", "name": "Skill", "input": {"skill": CANARY["skill"]}}),
        mode="bare", canary=CANARY, phrase=PHRASE,
    )
    assert clean["passed"]
    assert not leaked["passed"]


def test_bare_probe_requires_completion_and_rejects_startup_inventory_leak():
    assert not analyze_probe("", mode="bare", canary=CANARY, phrase=PHRASE)["passed"]
    transcript = "\n".join((
        json.dumps({"type": "system", "skills": [CANARY["skill"]]}),
        json.dumps({"type": "result", "result": "unavailable"}),
    ))
    evidence = analyze_probe(transcript, mode="bare", canary=CANARY, phrase=PHRASE)
    assert evidence["completion_observed"]
    assert evidence["startup_inventory_observed"]
    assert not evidence["passed"]


def test_explicit_codex_skill_file_read_is_use_but_not_native_discovery():
    transcript = "\n".join((
        json.dumps({"type": "item.completed", "item": {
            "type": "command_execution", "command": "cat /auth/skills/probe-canary/SKILL.md",
        }}),
        json.dumps({"type": "turn.completed", "result": PHRASE + " probe-canary"}),
    ))
    evidence = analyze_probe(transcript, mode="lc_ai", canary=CANARY, phrase=PHRASE)
    assert evidence["explicit_skill_file_read_observed"]
    assert evidence["skill_use_observed"]
    assert not evidence["native_discovery_observed"]


def test_ai_sessions_native_read_of_plugin_skill_is_use_but_not_discovery():
    transcript = "\n".join((
        json.dumps({
            "type": "tool_use",
            "payload": {
                "name": "Read",
                "input": {"file_path": "/opt/lc-fundamentals/skills/platform-config/SKILL.md"},
            },
        }),
        json.dumps({"type": "result", "payload": {"result": PHRASE + " platform-config"}}),
    ))
    evidence = analyze_probe(
        transcript,
        mode="lc_ai",
        canary={"skill": "platform-config", "skill_md_sha256": "a" * 64},
        phrase=PHRASE,
    )
    assert evidence["explicit_skill_file_read_observed"]
    assert evidence["skill_use_observed"]
    assert not evidence["native_discovery_observed"]
    assert evidence["passed"]


@pytest.mark.parametrize("mode", ["legacy", "unknown"])
def test_probe_prompt_rejects_nonexperimental_labels(mode):
    with pytest.raises(ValueError, match="bare or lc_ai"):
        probe_prompt(mode, CANARY["skill"])


@pytest.mark.asyncio
async def test_probe_does_not_prepare_context_when_pending_resources_block(monkeypatch):
    class Copyable(SimpleNamespace):
        def model_copy(self, *, update, deep=False):
            values = vars(self).copy()
            values.update(update)
            return Copyable(**values)

    class Journal:
        @contextlib.contextmanager
        def exclusive(self):
            yield

        def resources(self):
            return [{"pending": True}]

    agent = Copyable(adapter="codex", context_mode="legacy", timeout_seconds=600, max_turns=30)
    config = Copyable(agents=[agent])
    monkeypatch.setattr(
        context_probe_module, "Controller", lambda resolved: SimpleNamespace(journal=Journal())
    )
    prepared = False

    def forbidden_prepare(*args):
        nonlocal prepared
        prepared = True
        raise AssertionError("context preparation must occur after the resource guard")

    monkeypatch.setattr(context_probe_module, "_canary", forbidden_prepare)
    with pytest.raises(RuntimeError, match="reconcile resources"):
        await context_probe_module.probe(config, "probe-campaign", "codex", "lc_ai")
    assert prepared is False
