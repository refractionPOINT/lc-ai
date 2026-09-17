"""Independent, no-organization native context discovery probe."""
from __future__ import annotations

import contextlib
import json
import time
import uuid
from pathlib import Path
from typing import Any

from .config import atomic_json
from .context_profiles import prepare_context_corpus
from .controller import Controller
from .execution.docker import DockerEnvironment
from .models import RunConfig, safe_id

PROBE_TIMEOUT_SECONDS = 90
PROBE_MAX_TURNS = 8
PREFERRED_PASSIVE_CANARY = "lc-fundamentals--platform-config"


def _canary(config: RunConfig, agent) -> tuple[dict[str, str], str]:
    """Resolve a canary and phrase from the pinned archive, never the worktree."""
    probe_agent = agent.model_copy(update={"context_mode": "lc_ai"})
    probe_config = config.model_copy(update={"agents": [probe_agent]}, deep=True)
    corpus = prepare_context_corpus(probe_config)
    if corpus is None:
        raise ValueError("context probe requires context.lc_ai")
    selected = PREFERRED_PASSIVE_CANARY if PREFERRED_PASSIVE_CANARY in corpus["skills"] else corpus["canary"]["skill"]
    source_skill = selected.split("--", 1)[1]
    plugin = corpus["skills"][selected]
    skill_path = Path(corpus["skill_root"]) / selected / "SKILL.md"
    source_path = Path(corpus["skill_root"]).parent / "archive" / f"marketplace/plugins/{plugin}/skills/{source_skill}/SKILL.md"
    canary = {
        "skill": selected,
        "source_skill": source_skill,
        "plugin": plugin,
        "skill_md_sha256": _sha256(skill_path),
        "source_skill_md_sha256": _sha256(source_path),
    }
    text = skill_path.read_text()
    phrase = _body_phrase(text)
    if agent.adapter == "ai_sessions":
        canary["normalized_skill"] = canary["skill"]
        canary["skill"] = canary["source_skill"]
        canary["skill_md_sha256"] = canary["source_skill_md_sha256"]
    return canary, phrase


def _body_phrase(text: str) -> str:
    in_frontmatter = False
    frontmatter_done = False
    candidates: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if line == "---" and not frontmatter_done:
            if not in_frontmatter:
                in_frontmatter = True
            else:
                in_frontmatter = False
                frontmatter_done = True
            continue
        if in_frontmatter or not line or line.startswith(("#", "```")):
            continue
        if len(line) >= 24:
            candidates.append(line)
    if not candidates:
        raise ValueError("canary SKILL.md has no stable prose phrase")
    return candidates[0]


def probe_prompt(mode: str, skill: str) -> str:
    if mode not in {"bare", "lc_ai"}:
        raise ValueError("context probe mode must be bare or lc_ai")
    expectation = (
        "Load that skill through the harness's native skill mechanism solely to inspect its documentation. "
        "Do not execute any workflow, command, configuration change, deployment, or external action from it. "
        "Then reproduce exactly the first complete prose line in its SKILL.md body."
        if mode == "lc_ai"
        else "Do not search the filesystem. State whether that skill appears in the native skill inventory."
    )
    return (
        "This is a context-discovery probe. Do not run limacharlie and do not read authentication files. "
        f"Inspect the native skill inventory for the skill named {skill!r}. {expectation} "
        "Briefly report the available skill names you can observe."
    )


def _sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze_probe(stdout: bytes | str, *, mode: str, canary: dict[str, str], phrase: str) -> dict[str, Any]:
    text = stdout.decode("utf-8", "replace") if isinstance(stdout, bytes) else stdout
    events = []
    for line in text.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            events.append(value)
    rendered = json.dumps(events, sort_keys=True, ensure_ascii=False)
    skill = canary["skill"]
    phrase_observed = phrase in rendered
    skill_referenced = skill in rendered
    native_skill_call = any(_native_skill_call(event, skill) for event in events)
    startup_inventory = any(
        skill in json.dumps(event, sort_keys=True)
        and event.get("type") in {"system", "thread.started"}
        for event in events
    )
    path_read = any(_skill_file_read(event, skill) for event in events)
    completed = any(event.get("type") in {"result", "turn.completed", "thread.completed"} for event in events)
    skill_use = native_skill_call or path_read
    passed = (
        completed and phrase_observed and skill_referenced and (skill_use or startup_inventory)
        if mode == "lc_ai"
        else completed and not phrase_observed and not native_skill_call and not startup_inventory
    )
    return {
        "passed": passed,
        "phrase_observed": phrase_observed,
        "skill_referenced": skill_referenced,
        "native_skill_call_observed": native_skill_call,
        "startup_inventory_observed": startup_inventory,
        "native_discovery_observed": native_skill_call or startup_inventory,
        "explicit_skill_file_read_observed": path_read,
        "skill_use_observed": skill_use,
        "completion_observed": completed,
        "event_count": len(events),
    }


def _native_skill_call(event: dict[str, Any], skill: str) -> bool:
    candidates: list[Any] = [event]
    message = event.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, list):
            candidates.extend(content)
    payload = event.get("payload")
    if isinstance(payload, dict):
        candidates.append({"type": event.get("type"), **payload})
    for candidate in candidates:
        if not isinstance(candidate, dict) or candidate.get("type") != "tool_use":
            continue
        if str(candidate.get("name", "")).lower() != "skill":
            continue
        if skill in json.dumps(candidate, sort_keys=True):
            return True
    return False


def _skill_file_read(event: dict[str, Any], skill: str) -> bool:
    rendered = json.dumps(event, sort_keys=True)
    if skill not in rendered or "SKILL.md" not in rendered:
        return False
    if event.get("type") in {"item.started", "item.completed"} and "command_execution" in rendered:
        return True
    if event.get("type") != "tool_use":
        return False
    payload = event.get("payload")
    candidate = payload if isinstance(payload, dict) else event
    return str(candidate.get("name", "")).lower() == "read"


async def probe(config: RunConfig, campaign: str, adapter: str, context_mode: str) -> dict[str, Any]:
    """Run one bounded native context probe without LimaCharlie authority."""
    safe_id(campaign)
    if context_mode not in {"bare", "lc_ai"}:
        raise ValueError("context probe mode must be bare or lc_ai")
    matches = [agent for agent in config.agents if agent.adapter == adapter]
    if len(matches) != 1:
        raise ValueError("context probe requires exactly one configured matching adapter")
    agent = matches[0].model_copy(update={
        "context_mode": context_mode,
        "timeout_seconds": PROBE_TIMEOUT_SECONDS,
        "max_turns": PROBE_MAX_TURNS,
    })
    resolved = config.model_copy(update={"agents": [agent]}, deep=True)
    controller = Controller(resolved)
    trial_id = safe_id(campaign + "-context-" + uuid.uuid4().hex[:10])
    with controller.journal.exclusive():
        if controller.journal.resources():
            raise RuntimeError("reconcile resources before context probe")
        canary, phrase = _canary(resolved, agent)
        manifest = {
            "kind": "native-context-probe", "adapter": adapter, "context_mode": context_mode,
            "timeout_seconds": PROBE_TIMEOUT_SECONDS, "max_turns": PROBE_MAX_TURNS,
            "canary": canary,
        }
        result: dict[str, Any] = {
            "trial_id": trial_id, "adapter": adapter, "context_mode": context_mode,
            "execution_status": "failed", "grade": "inconclusive", "cleanup_status": "pending",
            "manifest": manifest, "usage": {}, "timings": {},
        }
        root = controller.journal.create_trial(trial_id, campaign, manifest)
        env = DockerEnvironment(resolved, trial_id, root, controller.journal)
        try:
            controller.journal.transition(trial_id, "provisioning")
            env.start(str(uuid.uuid4()), "context-probe-no-platform-authority", agent_config=agent)
            result["manifest"]["context"] = env.context_identity
            result["manifest"]["context_audit"] = env.context_audit
            atomic_json(root / "manifest.json", result["manifest"])
            controller.journal.transition(trial_id, "ready")
            controller.journal.transition(trial_id, "running")
            started = time.monotonic()
            await controller.run_agent(agent, env, probe_prompt(context_mode, canary["skill"]), result, root)
            result["timings"]["active_seconds"] = time.monotonic() - started
            stdout = (root / "agent.stdout").read_bytes() if (root / "agent.stdout").is_file() else b""
            result["probe_evidence"] = analyze_probe(
                stdout, mode=context_mode, canary=canary, phrase=phrase,
            )
            result["grade"] = (
                "pass" if result["execution_status"] == "completed" and result["probe_evidence"]["passed"]
                else "fail"
            )
        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            with contextlib.suppress(Exception):
                env.stop_candidate()
            controller.journal.transition(trial_id, "cleaning")
            cleanup = controller.reconcile(trial_id)
            result["cleanup_status"] = "clean" if not cleanup["unresolved"] else "failed"
            atomic_json(root / "result.json", result)
            controller.journal.finish(trial_id, result)
            controller.journal.transition(trial_id, "finished")
    return result
