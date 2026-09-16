"""Compatibility checks and paired-success efficiency comparisons."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

EFFICIENCY_METRICS = (
    "input_tokens", "output_tokens", "cost_usd", "cost_micro_usd", "active_seconds",
    "verification_seconds", "cli_invocations", "backend_requests", "output_bytes",
)


def _dig(value: Mapping[str, Any], *paths: str) -> Any:
    for path in paths:
        current: Any = value
        found = True
        for part in path.split("."):
            if not isinstance(current, Mapping) or part not in current:
                found = False
                break
            current = current[part]
        if found:
            return current
    return None


COMPATIBILITY_FIELDS: dict[str, tuple[str, ...]] = {
    "scenario_id": ("scenario_id", "scenario.id", "manifest.scenario_id"),
    "scenario_revision": ("scenario_revision", "scenario.revision", "manifest.scenario_revision"),
    "scenario_hash": ("scenario_hash", "manifest.scenario_hash"),
    "variant_seed": ("variant_seed", "seed", "manifest.variant_seed"),
    "docs_digest": ("docs_digest", "configuration.docs_digest", "manifest.docs_digest"),
    "fixture_recipe": ("fixture_recipe_digest", "fixture.recipe_digest", "manifest.fixture_recipe_digest"),
    "harness": ("adapter", "harness", "configuration.harness", "manifest.harness"),
    "model": ("model", "configuration.model", "manifest.model"),
    "effort": ("effort", "configuration.effort", "manifest.effort"),
    "tools": ("tools_digest", "configuration.tools_digest", "manifest.tools_digest"),
    "evaluator": (
        "evaluator_digest",
        "configuration.evaluator_digest",
        "manifest.evaluator_digest",
    ),
    "permission_profile": ("permission_profile", "configuration.permission_profile", "manifest.permission_profile"),
    "execution_profile": ("execution_profile", "configuration.execution_profile", "manifest.execution_profile"),
    "limits": ("limits", "configuration.limits", "manifest.limits"),
}

INFORMATIONAL_FIELDS: dict[str, tuple[str, ...]] = {
    "repetition": ("repetition", "manifest.repetition"),
    "cli_digest": ("cli_digest", "configuration.cli_digest", "manifest.cli_digest"),
}


def compatibility(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    mismatches = []
    missing = []
    values: dict[str, dict[str, Any]] = {}
    for field, paths in COMPATIBILITY_FIELDS.items():
        lhs, rhs = _dig(left, *paths), _dig(right, *paths)
        values[field] = {"left": lhs, "right": rhs}
        if lhs is None or rhs is None:
            missing.append(field)
        elif lhs != rhs:
            mismatches.append(field)
    for field, paths in INFORMATIONAL_FIELDS.items():
        values[field] = {"left": _dig(left, *paths), "right": _dig(right, *paths)}
    reasons = [f"mismatched controlled field: {field}" for field in mismatches]
    reasons.extend(f"missing controlled field: {field}" for field in missing)
    return {"compatible": not reasons, "reasons": reasons, "fields": values}


def _metric(trial: Mapping[str, Any], name: str) -> float | int | None:
    for source in (trial, trial.get("usage"), trial.get("timings"), trial.get("metrics")):
        if isinstance(source, Mapping):
            value = source.get(name)
            if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)):
                return value
    return None


def _success(trial: Mapping[str, Any]) -> bool:
    harness = trial.get("adapter", trial.get("harness"))
    return (
        harness not in {None, "scripted", "reference", "reference_bad", "fault_injection"}
        and trial.get("invalid") is not True
        and trial.get("grade", trial.get("task_grade")) == "pass"
        and trial.get("execution_status", trial.get("status")) == "completed"
        and trial.get("evidence_complete") is True
        and trial.get("cleanup_status", trial.get("cleanup_state")) == "clean"
    )


def compare_pair(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    check = compatibility(left, right)
    both_success = _success(left) and _success(right)
    efficiency_eligible = check["compatible"] and both_success
    efficiency: dict[str, Any] = {}
    for metric in EFFICIENCY_METRICS:
        lhs, rhs = _metric(left, metric), _metric(right, metric)
        efficiency[metric] = {
            "left": lhs,
            "right": rhs,
            "delta_right_minus_left": (
                rhs - lhs if efficiency_eligible and lhs is not None and rhs is not None else None
            ),
        }
    return {
        "left_trial_id": left.get("trial_id"),
        "right_trial_id": right.get("trial_id"),
        "compatibility": check,
        "left_success": _success(left),
        "right_success": _success(right),
        "paired_success": both_success,
        "efficiency": efficiency,
        "included_in_efficiency": efficiency_eligible,
    }


def _pair_key(trial: Mapping[str, Any]) -> tuple[Any, ...]:
    explicit = trial.get("pair_id")
    if explicit is not None:
        return ("pair_id", explicit)
    return tuple(
        _dig(trial, *COMPATIBILITY_FIELDS[field])
        for field in ("scenario_id", "scenario_revision", "scenario_hash", "variant_seed", "harness", "model")
    )


def _all_attempt_metrics(trials: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for metric in EFFICIENCY_METRICS:
        values = [_metric(trial, metric) for trial in trials]
        known = [value for value in values if value is not None]
        result[metric] = {
            "total": sum(known) if known and len(known) == len(values) else None,
            "known_total": sum(known) if known else None,
            "known_count": len(known),
            "missing_count": len(values) - len(known),
        }
    return result


def compare_results(left: Sequence[Mapping[str, Any]], right: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    right_by_key: dict[tuple[Any, ...], list[Mapping[str, Any]]] = {}
    for trial in right:
        right_by_key.setdefault(_pair_key(trial), []).append(trial)
    pairs = []
    unpaired_left = []
    for trial in left:
        choices = right_by_key.get(_pair_key(trial), [])
        if choices:
            pairs.append(compare_pair(trial, choices.pop(0)))
        else:
            unpaired_left.append(trial.get("trial_id"))
    unpaired_right = [trial.get("trial_id") for choices in right_by_key.values() for trial in choices]
    compatible_pairs = [pair for pair in pairs if pair["compatibility"]["compatible"]]
    successful_pairs = [pair for pair in compatible_pairs if pair["paired_success"]]
    return {
        "left": {
            "attempts": len(left), "successes": sum(_success(trial) for trial in left),
            "success_rate": sum(_success(trial) for trial in left) / len(left) if left else None,
            "all_attempt_metrics": _all_attempt_metrics(left),
        },
        "right": {
            "attempts": len(right), "successes": sum(_success(trial) for trial in right),
            "success_rate": sum(_success(trial) for trial in right) / len(right) if right else None,
            "all_attempt_metrics": _all_attempt_metrics(right),
        },
        "pairs": pairs,
        "pair_counts": {
            "total": len(pairs), "compatible": len(compatible_pairs),
            "paired_success": len(successful_pairs), "excluded_from_efficiency": len(pairs) - len(successful_pairs),
        },
        "unpaired": {"left": unpaired_left, "right": unpaired_right},
        "efficiency_basis": (
            "compatible genuine-harness pairs where both completed with complete evidence, "
            "passed, and cleaned"
        ),
    }
