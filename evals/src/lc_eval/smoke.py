"""Bounded subscription harness smoke checks with no LimaCharlie organization."""

from __future__ import annotations

import contextlib
import json
import time
import uuid

from .config import atomic_json
from .controller import Controller
from .execution.broker import Broker, CONTROLLED_CLI_V1_NOTICE
from .execution.docker import DockerEnvironment
from .execution.workspace_runner import DENIED_TOOLS


def native_policy_checks(root):
    events = [json.loads(line) for line in (root / "agent.stdout").read_text().splitlines()]
    inventories = [event["payload"]["data"]["tools"] for event in events
                   if event.get("type") == "system"
                   and event.get("payload", {}).get("subtype") == "eval_tool_inventory"]
    calls = [event.get("payload", {}).get("name") for event in events if event.get("type") == "tool_use"]
    help_file = root / "work" / "search-help.txt"
    return {
        "sdk_tool_inventory_observed": bool(inventories),
        "delegation_and_scheduling_absent": bool(inventories) and all(
            not set(tools).intersection(DENIED_TOOLS) for tools in inventories),
        "no_forbidden_tool_calls": not set(calls).intersection(DENIED_TOOLS),
        "no_child_events": not any(event.get("parent_tool_use_id") for event in events),
        "leaf_help_has_pipeline_example": help_file.is_file()
        and "* | NEW_PROCESS |" in help_file.read_text(),
    }


async def smoke(config, campaign):
    controller = Controller(config)
    results = []
    with controller.journal.exclusive():
        if controller.journal.resources():
            raise RuntimeError("reconcile resources before smoke")
        for selected in config.agents:
            agent = selected.model_copy(update={"timeout_seconds": 90, "max_turns": 4})
            trial_id = campaign + "-" + uuid.uuid4().hex[:10]
            root = controller.journal.create_trial(
                trial_id, campaign, {"kind": "harness-smoke", "adapter": agent.adapter}
            )
            env = DockerEnvironment(config, trial_id, root, controller.journal)
            broker = None
            result = {
                "trial_id": trial_id,
                "scenario_id": "harness-smoke",
                "adapter": agent.adapter,
                "execution_status": "failed",
                "grade": "inconclusive",
                "cleanup_status": "pending",
                "usage": {},
                "manifest": {
                    "kind": "harness-smoke", "harness": agent.adapter,
                    "model": agent.model, "harness_version": agent.version,
                    "timeout_seconds": agent.timeout_seconds, "max_turns": agent.max_turns,
                    "ai_sessions": config.ai_sessions.model_dump(mode="json")
                    if agent.adapter == "ai_sessions" and config.ai_sessions else None,
                },
                "timings": {},
            }
            try:
                controller.journal.transition(trial_id, "provisioning")
                env.start(str(uuid.uuid4()), "smoke-no-platform-authority", agent_config=selected)
                broker = Broker(
                    env.worker,
                    env.socket_dir,
                    root / "commands.jsonl",
                    workspace=env.work,
                    # Native startup performs root-help/version discovery before
                    # the candidate's explicit version and leaf-help probes.
                    max_invocations=8 if agent.adapter == "ai_sessions" else 4,
                    max_seconds=30,
                )
                await broker.start()
                controller.journal.transition(trial_id, "ready")
                controller.journal.transition(trial_id, "running")
                start = time.monotonic()
                native_probe = (
                    " Also save `limacharlie search run --ai-help` output to /work/search-help.txt. "
                    "If an Agent or Task delegation tool is available, use it to read that help; "
                    "otherwise read it directly."
                    if agent.adapter == "ai_sessions" else ""
                )
                await controller.run_agent(
                    agent,
                    env,
                    "Write exactly lc-eval-smoke-ok to /work/smoke.txt, then run limacharlie --version. Report completion. Do not read authentication files.\n"
                    + native_probe + "\n"
                    + CONTROLLED_CLI_V1_NOTICE,
                    result,
                    root,
                )
                result["timings"]["active_seconds"] = time.monotonic() - start
                env.stop_candidate()
                value = (
                    (env.work / "smoke.txt").read_text().strip()
                    if (env.work / "smoke.txt").is_file()
                    else None
                )
                result["grade"] = (
                    "pass"
                    if value == "lc-eval-smoke-ok"
                    and result["execution_status"] == "completed"
                    and broker.count >= 1
                    else "fail"
                )
                if agent.adapter == "ai_sessions":
                    result["policy_checks"] = native_policy_checks(root)
                    if not all(result["policy_checks"].values()):
                        result["grade"] = "fail"
            except Exception as exc:
                result["error"] = f"{type(exc).__name__}: {exc}"
            finally:
                with contextlib.suppress(Exception):
                    env.stop_candidate()
                if broker:
                    with contextlib.suppress(Exception):
                        await broker.close()
                controller.journal.transition(trial_id, "cleaning")
                cleanup = controller.reconcile(trial_id)
                result["cleanup_status"] = "clean" if not cleanup["unresolved"] else "failed"
                atomic_json(root / "result.json", result)
                controller.journal.finish(trial_id, result)
                controller.journal.transition(trial_id, "finished")
            results.append(result)
            if result["cleanup_status"] != "clean":
                break
    return results
