"""Live interruption drill: crash after runtime creation, then reconcile the ledger."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

from .config import atomic_json, load
from .controller import Controller
from .execution.docker import DockerEnvironment
from .fixtures import keys
from .models import safe_id

EXPECTED_CRASH_EXIT = 86
REQUIRED_RESOURCE_KINDS = {"org", "api_key", "docker_network", "docker_container"}


def _crash_marker(path: Path) -> tuple[dict, dict]:
    """Validate that the child reached a fully acquired candidate runtime."""

    try:
        marker = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}, {"valid": False, "reason": "post-start marker is missing or invalid"}
    resources = marker.get("resources")
    if not isinstance(resources, list):
        return marker, {"valid": False, "reason": "post-start marker omitted resources"}
    valid_resources = [
        resource
        for resource in resources
        if isinstance(resource, dict)
        and isinstance(resource.get("kind"), str)
        and isinstance(resource.get("name"), str)
        and isinstance(resource.get("resource_id"), str)
        and bool(resource["resource_id"])
        and resource.get("status") == "active"
    ]
    kinds = {resource["kind"] for resource in valid_resources}
    containers = [
        resource for resource in valid_resources if resource["kind"] == "docker_container"
    ]
    candidate = [resource for resource in containers if resource["name"].endswith("-agent")]
    worker = [resource for resource in containers if resource["name"].endswith("-worker")]
    networks = [resource for resource in valid_resources if resource["kind"] == "docker_network"]
    valid = (
        len(valid_resources) == len(resources)
        and REQUIRED_RESOURCE_KINDS <= kinds
        and len(candidate) == 1
        and len(worker) == 1
        and len(containers) >= 4
        and len(networks) >= 2
        and isinstance(marker.get("oid"), str)
        and bool(marker["oid"])
    )
    return marker, {
        "valid": valid,
        "resource_count": len(resources),
        "resource_kinds": sorted(kinds),
        "candidate_container": candidate[0]["name"] if len(candidate) == 1 else None,
        "worker_container": worker[0]["name"] if len(worker) == 1 else None,
        "container_count": len(containers),
        "network_count": len(networks),
        "reason": None if valid else "marker does not prove a fully acquired candidate runtime",
    }


def _child(config_path: Path, campaign: str, trial_id: str) -> None:
    config = load(config_path)
    controller = Controller(config)
    selected = next(
        (agent for agent in config.agents if agent.adapter in {"claude_code", "codex"}),
        None,
    )
    if selected is None:
        raise RuntimeError("fault drill requires a supported live harness configuration")
    manifest = {
        "kind": "interruption-recovery-drill",
        "crash_point": "after_candidate_start",
        "adapter": selected.adapter,
    }
    root = controller.journal.create_trial(trial_id, campaign, manifest)
    atomic_json(root / "manifest.json", manifest)
    controller.journal.transition(trial_id, "provisioning")
    org = controller.orgs.create(trial_id, config.lc.location)
    key = keys.create(
        controller.cli, controller.journal, trial_id, org["oid"], "hive-preserve-update"
    )
    environment = DockerEnvironment(config, trial_id, root, controller.journal)
    environment.start(org["oid"], key, agent_config=selected)
    resources = controller.journal.resources(trial_id)
    atomic_json(
        root / "crash-created.json",
        {
            "oid": org["oid"],
            "resources": [
                {
                    "kind": resource["kind"],
                    "name": resource["name"],
                    "resource_id": resource["resource_id"],
                    "status": resource["status"],
                }
                for resource in resources
            ],
        },
    )
    os._exit(EXPECTED_CRASH_EXIT)


def _update_proof(run_root: Path, passed: bool, trial_id: str) -> None:
    path = run_root / "proof.json"
    try:
        proof = json.loads(path.read_text()) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        proof = {}
    proof.update(
        interruption_recovery_passed=passed,
        interruption_recovery_trial_id=trial_id,
    )
    atomic_json(path, proof)


def run_crash_drill(config_path: Path, campaign: str) -> dict:
    """Run the child crash and recover only its journal-owned resources.

    The caller owns the run-directory controller lock. This function makes a
    real organization and is therefore intentionally never called by tests.
    """

    config_path = Path(config_path).expanduser().resolve()
    config = load(config_path)
    safe_id(campaign)
    trial_id = safe_id("fault-" + uuid.uuid4().hex[:16])
    controller = Controller(config)
    command = [
        sys.executable,
        "-m",
        "lc_eval.crash_drill",
        "--child",
        "--config",
        str(config_path),
        "--campaign",
        campaign,
        "--trial",
        trial_id,
    ]
    child_error = None
    try:
        child = subprocess.run(command, capture_output=True, timeout=config.lc.readiness_seconds + 60)
        child_returncode = child.returncode
    except subprocess.TimeoutExpired:
        child_returncode = None
        child_error = "crash child timed out"

    rows = [row for row in controller.journal.trials(campaign) if row["id"] == trial_id]
    if not rows:
        result = {
            "schema_version": 1,
            "trial_id": trial_id,
            "campaign_id": campaign,
            "scenario_id": "interruption-recovery-drill",
            "adapter": "fault_injection",
            "execution_status": "failed",
            "grade": "not-run",
            "cleanup_status": "failed",
            "assertions": [],
            "usage": {},
            "timings": {},
            "evidence_complete": False,
            "interruption_recovery_passed": False,
            "error": child_error or f"child exited {child_returncode} before journaling the trial",
        }
        _update_proof(config.run_data_dir, False, trial_id)
        return result

    root = config.run_data_dir / "trials" / trial_id
    finalization_errors = []
    try:
        controller.journal.transition(trial_id, "cleaning")
    except Exception as exc:
        finalization_errors.append({"stage": "transition_cleaning", "error": str(exc)})
    try:
        cleanup = controller.reconcile(trial_id)
    except Exception as exc:
        cleanup = {"unresolved": controller.journal.resources(trial_id), "errors": []}
        finalization_errors.append({"stage": "reconcile", "error": str(exc)})
    clean = not cleanup["unresolved"] and not cleanup["errors"] and not finalization_errors
    _, marker_evidence = _crash_marker(root / "crash-created.json")
    marker_valid = marker_evidence["valid"]
    expected_crash = child_returncode == EXPECTED_CRASH_EXIT
    passed = expected_crash and marker_valid and clean
    assertions = [
        {
            "id": "fault.runtime_started",
            "status": "pass" if marker_valid else "fail",
            "required": True,
            "expected": "journaled active candidate runtime",
            "observed": marker_evidence,
            "evidence": ["artifact:crash-created.json"],
            "explanation": (
                "The child journaled a fully acquired candidate runtime before interruption."
                if marker_valid
                else "The post-start marker does not prove a fully acquired candidate runtime."
            ),
        },
        {
            "id": "fault.expected_interruption",
            "status": "pass" if expected_crash else "fail",
            "required": True,
            "expected": EXPECTED_CRASH_EXIT,
            "observed": child_returncode,
            "evidence": ["process:crash-child"],
            "explanation": (
                "The child terminated at the deliberate crash point."
                if expected_crash
                else "The child did not terminate at the deliberate crash point."
            ),
        },
        {
            "id": "fault.exact_cleanup",
            "status": "pass" if clean else "fail",
            "required": True,
            "expected": {"unresolved": 0, "errors": 0},
            "observed": {
                "unresolved": len(cleanup["unresolved"]),
                "errors": len(cleanup["errors"]) + len(finalization_errors),
            },
            "evidence": ["journal:resources"],
            "explanation": (
                "Reconciliation removed every exact journal-owned resource."
                if clean
                else "Reconciliation left resources or cleanup errors."
            ),
        },
    ]
    result = {
        "schema_version": 1,
        "trial_id": trial_id,
        "campaign_id": campaign,
        "scenario_id": "interruption-recovery-drill",
        "adapter": "fault_injection",
        "execution_status": "interrupted" if child_returncode == EXPECTED_CRASH_EXIT else "failed",
        "grade": "not-run",
        "cleanup_status": "clean" if clean else "failed",
        "assertions": assertions,
        "usage": {},
        "timings": {},
        "manifest": rows[0]["manifest"],
        "evidence_complete": marker_valid,
        "cleanup_errors": [*cleanup["errors"], *finalization_errors],
        "interruption_recovery_passed": passed,
        "child_returncode": child_returncode,
        "crash_evidence": marker_evidence,
    }
    if child_error or not marker_valid:
        result["error"] = child_error or marker_evidence["reason"]
    atomic_json(root / "result.json", result)
    controller.journal.finish(trial_id, result)
    try:
        controller.journal.transition(trial_id, "finished")
    except Exception as exc:
        result["cleanup_status"] = "failed"
        result["interruption_recovery_passed"] = False
        result["cleanup_errors"].append({"stage": "transition_finished", "error": str(exc)})
        atomic_json(root / "result.json", result)
        controller.journal.finish(trial_id, result)
    _update_proof(config.run_data_dir, result["interruption_recovery_passed"], trial_id)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--trial", required=True)
    args = parser.parse_args()
    if not args.child:
        parser.error("this module entry point is only for the crash child")
    _child(args.config, args.campaign, args.trial)


if __name__ == "__main__":
    main()
