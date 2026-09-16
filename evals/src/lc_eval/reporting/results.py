"""Campaign result aggregation over plain trial-result dictionaries."""

from __future__ import annotations

import json
import math
import os
import tempfile
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


COMMAND_METRIC_NAMES = (
    "output_bytes",
    "cli_seconds",
    "cli_failed_commands",
    "rejected_commands",
)


def command_metrics(path: str | os.PathLike[str], *, max_events: int = 1_000_000) -> dict[str, Any]:
    """Aggregate numeric broker evidence without copying command text into reports."""

    unknown = {name: None for name in COMMAND_METRIC_NAMES}
    source = Path(path)
    if max_events <= 0 or not source.is_file():
        return unknown
    requests: set[str] = set()
    ends: dict[str, Mapping[str, Any]] = {}
    observed_command_ids: set[str] = set()
    rejected = 0
    try:
        with source.open(encoding="utf-8") as stream:
            for number, line in enumerate(stream, 1):
                if number > max_events:
                    return unknown
                event = json.loads(line)
                if not isinstance(event, Mapping):
                    return unknown
                kind = event.get("type")
                if kind == "command_rejected":
                    rejected += 1
                elif kind == "command_request":
                    command_id = event.get("id")
                    if not isinstance(command_id, str) or not command_id or command_id in requests:
                        return unknown
                    requests.add(command_id)
                elif kind == "command_end":
                    command_id = event.get("id")
                    if not isinstance(command_id, str) or not command_id or command_id in ends:
                        return unknown
                    ends[command_id] = event
                    observed_command_ids.add(command_id)
                elif kind in {"command_start", "stdout", "stderr"}:
                    command_id = event.get("id")
                    if not isinstance(command_id, str) or not command_id:
                        return unknown
                    observed_command_ids.add(command_id)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return unknown

    complete = requests == set(ends) and observed_command_ids <= requests
    end_events = [ends[command_id] for command_id in sorted(requests)] if complete else []
    byte_values = [event.get("bytes") for event in end_events]
    second_values = [event.get("seconds") for event in end_events]
    code_values = [event.get("code") for event in end_events]
    bytes_known = complete and all(
        isinstance(value, int) and not isinstance(value, bool) and value >= 0
        for value in byte_values
    )
    seconds_known = complete and all(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and value >= 0
        for value in second_values
    )
    codes_known = complete and all(
        isinstance(value, int) and not isinstance(value, bool) for value in code_values
    )
    return {
        "output_bytes": sum(byte_values) if bytes_known else None,
        "cli_seconds": sum(second_values) if seconds_known else None,
        "cli_failed_commands": (
            sum(code != 0 for code in code_values) if codes_known else None
        ),
        "rejected_commands": rejected,
    }


def _success(trial: Mapping[str, Any]) -> bool:
    return trial.get("grade", trial.get("task_grade")) == "pass"


def _finite_number(value: Any) -> float | int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(float(value)):
        return None
    return value


def _metric(trial: Mapping[str, Any], name: str) -> float | int | None:
    direct = _finite_number(trial.get(name))
    if direct is not None:
        return direct
    for section in ("usage", "timings", "metrics"):
        value = trial.get(section)
        if isinstance(value, Mapping):
            number = _finite_number(value.get(name))
            if number is not None:
                return number
    return None


def metric_summary(trials: Sequence[Mapping[str, Any]], name: str) -> dict[str, Any]:
    values = [_metric(trial, name) for trial in trials]
    known = [value for value in values if value is not None]
    missing = len(values) - len(known)
    return {
        "total": sum(known) if known and missing == 0 else None,
        "known_total": sum(known) if known else None,
        "mean": (sum(known) / len(known)) if known else None,
        "known_count": len(known),
        "missing_count": missing,
    }


def _scenario_id(trial: Mapping[str, Any]) -> str:
    value = trial.get("scenario_id")
    if isinstance(value, str):
        return value
    scenario = trial.get("scenario")
    if isinstance(scenario, Mapping) and isinstance(scenario.get("id"), str):
        return scenario["id"]
    manifest = trial.get("manifest")
    if isinstance(manifest, Mapping) and isinstance(manifest.get("scenario_id"), str):
        return manifest["scenario_id"]
    return "unknown"


def build_report(
    trials: Sequence[Mapping[str, Any]],
    *,
    campaign: Mapping[str, Any] | None = None,
    comparisons: Sequence[Mapping[str, Any]] = (),
    acceptance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a JSON-safe report without filling unknown measurements with zero."""

    copied = [dict(trial) for trial in trials]
    scored = [
        trial
        for trial in copied
        if trial.get("adapter") not in {"reference", "reference_bad", "scripted", "fault_injection"}
        and _scenario_id(trial) != "harness-smoke"
    ]
    successes = sum(_success(trial) for trial in scored)
    by_scenario: dict[str, dict[str, Any]] = {}
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for trial in scored:
        grouped[_scenario_id(trial)].append(trial)
    for scenario_id, values in sorted(grouped.items()):
        passed = sum(_success(value) for value in values)
        by_scenario[scenario_id] = {
            "attempts": len(values),
            "successes": passed,
            "success_rate": passed / len(values),
        }
    metrics = {
        name: metric_summary(scored, name)
        for name in (
            "input_tokens",
            "total_input_tokens",
            "output_tokens",
            "cached_input_tokens",
            "cache_read_tokens",
            "cache_write_tokens",
            "cost_usd",
            "cost_micro_usd",
            "cli_invocations",
            "cli_seconds",
            "cli_failed_commands",
            "rejected_commands",
            "backend_requests",
            "output_bytes",
            "active_seconds",
            "waiting_seconds",
            "verification_seconds",
        )
    }
    return {
        "schema_version": "1",
        "campaign": dict(campaign or {}),
        "summary": {
            "trials": len(scored),
            "recorded_trials": len(copied),
            "non_scored_trials": len(copied) - len(scored),
            "successes": successes,
            "success_rate": successes / len(scored) if scored else None,
            "by_scenario": by_scenario,
            "metrics": metrics,
        },
        "trials": copied,
        "comparisons": [dict(value) for value in comparisons],
        "acceptance": dict(acceptance) if acceptance is not None else None,
    }


def _criterion(status: str, explanation: str, observed: Any) -> dict[str, Any]:
    return {"status": status, "observed": observed, "explanation": explanation}


def acceptance_summary(
    trials: Sequence[Mapping[str, Any]],
    evidence: Mapping[str, Any] | None = None,
    *,
    expected_scenarios: Sequence[str] = (
        "hive-preserve-update",
        "search-complete-export",
        "webhook-production-routing",
    ),
    expected_harnesses: Sequence[str] = ("claude_code", "codex"),
) -> dict[str, Any]:
    """Evaluate the initial-loop acceptance criteria without hiding missing proof."""

    facts = dict(evidence or {})
    expected_scenario_set = set(expected_scenarios)
    genuine = [
        trial
        for trial in trials
        if _scenario_id(trial) in expected_scenario_set
        if trial.get("adapter", trial.get("harness"))
        not in {"scripted", "reference", "reference_bad", "fault_injection", None}
        and trial.get("invalid") is not True
    ]
    successful_scenarios = {_scenario_id(trial) for trial in genuine if _success(trial)}
    missing_success = sorted(set(expected_scenarios) - successful_scenarios)
    scenario_status = "pass" if not missing_success else "fail" if genuine else "unknown"

    terminal_values = {"finished", "complete", "completed", "failed", "timed_out", "unsupported"}
    matrix_missing: list[str] = []
    for scenario in expected_scenarios:
        for harness in expected_harnesses:
            found = any(
                _scenario_id(trial) == scenario
                and trial.get("adapter", trial.get("harness")) == harness
                and trial.get("execution_status", trial.get("status")) in terminal_values
                for trial in trials
            )
            if not found:
                matrix_missing.append(f"{scenario}:{harness}")

    unresolved = []
    for trial in trials:
        cleanup = trial.get("cleanup")
        cleanup_value = trial.get("cleanup_status", trial.get("cleanup_state"))
        if cleanup_value is None and isinstance(cleanup, Mapping):
            cleanup_value = cleanup.get("state")
        if cleanup_value not in {"clean", "cleaned", "complete", "verified"}:
            unresolved.append(trial.get("trial_id"))

    declared_modes = []
    billing_rows = []
    for trial in genuine:
        manifest = trial.get("manifest")
        usage = trial.get("usage")
        mode = trial.get("billing_mode")
        if mode is None and isinstance(usage, Mapping):
            mode = usage.get("billing_mode")
        if mode is None and isinstance(manifest, Mapping):
            mode = manifest.get("billing_mode")
        if isinstance(mode, str):
            declared_modes.append(mode)
        claimed_costs = {}
        if isinstance(usage, Mapping):
            for field in ("cost_usd", "cost_micro_usd"):
                if usage.get(field) is not None:
                    claimed_costs[field] = usage[field]
        billing_rows.append((trial.get("trial_id"), mode, claimed_costs))
    unique_modes = sorted(set(declared_modes))
    expected_billing_mode = facts.get("billing_mode")
    if expected_billing_mode is None and len(unique_modes) == 1:
        expected_billing_mode = unique_modes[0]
    billing_issues = []
    for trial_id, mode, claimed_costs in billing_rows:
        issue = mode != expected_billing_mode or expected_billing_mode not in {
            "subscription_limits",
            "hard_usd",
        }
        if expected_billing_mode == "subscription_limits" and claimed_costs:
            issue = True
        if expected_billing_mode == "hard_usd":
            valid_costs = [
                _finite_number(value)
                for value in claimed_costs.values()
            ]
            if not valid_costs or any(value is None or value < 0 for value in valid_costs):
                issue = True
        if issue:
            billing_issues.append(
                {
                    "trial_id": trial_id,
                    "billing_mode": mode,
                    "claimed_dollar_costs": claimed_costs,
                }
            )
    criteria = {
        "reference_validation": _criterion(
            "pass"
            if facts.get("reference_validation_passed") is True
            else "fail"
            if facts.get("reference_validation_passed") is False
            else "unknown",
            "Good references pass and named bad references fail their intended assertions.",
            facts.get("reference_validation_passed"),
        ),
        "harness_matrix_terminal": _criterion(
            "pass" if not matrix_missing else "fail" if genuine else "unknown",
            "Each configured harness has a terminal result for every initial scenario.",
            matrix_missing,
        ),
        "scenario_ai_success": _criterion(
            scenario_status,
            "Each scenario has at least one genuine AI success.",
            missing_success,
        ),
        "billing_accounting": _criterion(
            "pass" if genuine and not billing_issues else "fail" if billing_issues else "unknown",
            "Scored trials follow the declared billing mode; subscriptions make no dollar-cost claim.",
            {
                "billing_mode": expected_billing_mode,
                "checked_trials": len(genuine),
                "issues": billing_issues,
            },
        ),
        "cleanup": _criterion(
            "pass"
            if trials and not unresolved and facts.get("unresolved_resource_count") == 0
            else "fail"
            if unresolved
            or (
                isinstance(facts.get("unresolved_resource_count"), int)
                and facts["unresolved_resource_count"] > 0
            )
            else "unknown",
            "Every trial has verified cleanup and the resource ledger is empty.",
            {"trial_ids": unresolved, "unresolved_resource_count": facts.get("unresolved_resource_count")},
        ),
        "interruption_recovery": _criterion(
            "pass"
            if facts.get("interruption_recovery_passed") is True
            else "fail"
            if facts.get("interruption_recovery_passed") is False
            else "unknown",
            "The live interruption drill recovered and cleaned its owned resources.",
            facts.get("interruption_recovery_passed"),
        ),
        "paired_aa": _criterion(
            "pass"
            if facts.get("paired_aa_complete") is True
            else "fail"
            if facts.get("paired_aa_complete") is False
            else "unknown",
            "Both required Hive A/A repeats were reported as compatible pairs.",
            facts.get("paired_aa_complete"),
        ),
    }
    statuses = [value["status"] for value in criteria.values()]
    overall = (
        "pass"
        if all(status == "pass" for status in statuses)
        else "fail"
        if "fail" in statuses
        else "unknown"
    )
    return {"status": overall, "criteria": criteria}


def dumps_json(report: Mapping[str, Any], *, indent: int = 2) -> str:
    return json.dumps(report, indent=indent, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"


def write_json(report: Mapping[str, Any], path: str | os.PathLike[str]) -> Path:
    """Atomically write a report with user-only permissions."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = dumps_json(report)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
    return destination
