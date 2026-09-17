"""Verifier for fresh, signed production-routing probes."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from .base import assertion, evidence_refs, merge_evidence, summarize_ids


def _ids(value: Any) -> set[str] | None:
    if isinstance(value, Mapping):
        values: set[str] = set()
        for item in value.values():
            parsed = _ids(item)
            if parsed is not None:
                values.update(parsed)
        return values
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return {str(item) for item in value}
    return None


def _event_id(value: Any, depth: int = 0) -> str | None:
    if depth > 5 or not isinstance(value, Mapping):
        return None
    for key in ("eval_event_id", "probe_id"):
        if isinstance(value.get(key), str):
            return value[key]
    for key in ("event", "payload", "data", "detect", "routing"):
        found = _event_id(value.get(key), depth + 1)
        if found:
            return found
    return None


def _timestamp(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if not isinstance(value, str):
        return None
    try:
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except ValueError:
        return None


def _health(facts: Mapping[str, Any]) -> tuple[bool | None, dict[str, Any] | None]:
    value = facts.get("receiver_health", facts.get("health"))
    if isinstance(value, bool):
        return value, {"healthy": value}
    if not isinstance(value, Mapping):
        return None, None
    checks = [value[key] for key in ("management_reachable", "receiver_ready", "positive_control_received") if key in value]
    if isinstance(value.get("healthy"), bool):
        checks.append(value["healthy"])
        return all(item is True for item in checks), dict(value)
    if not isinstance(value.get("positive_control_received"), bool):
        return None, dict(value)
    return all(item is True for item in checks), dict(value)


def _window(facts: Mapping[str, Any]) -> tuple[bool | None, float | None, float | None, dict[str, Any] | None]:
    value = facts.get("observation_window", facts.get("window"))
    if not isinstance(value, Mapping):
        return None, None, None, None
    start = _timestamp(value.get("start", value.get("started_at")))
    end = _timestamp(value.get("end", value.get("ended_at")))
    completed = value.get("complete", value.get("observation_complete"))
    minimum = float(facts.get("minimum_negative_window_seconds", value.get("minimum_seconds", 180)))
    if start is None or end is None or not isinstance(completed, bool):
        return None, start, end, dict(value)
    return completed and end >= start and end - start >= minimum, start, end, {**dict(value), "duration_seconds": end - start, "minimum_seconds": minimum}


def _valid_receipts(facts: Mapping[str, Any], start: float | None, end: float | None) -> tuple[set[str] | None, dict[str, Any]]:
    receipts = facts.get("received_records", facts.get("receipts"))
    if not isinstance(receipts, Sequence) or isinstance(receipts, (str, bytes)):
        return None, {"reason": "receipt evidence missing"}
    valid: set[str] = set()
    invalid_signature = 0
    stale = 0
    unidentified = 0
    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            unidentified += 1
            continue
        event_id = _event_id(receipt)
        if event_id is None:
            unidentified += 1
            continue
        if receipt.get("signature_valid") is not True:
            invalid_signature += 1
            continue
        received = _timestamp(receipt.get("received_at", receipt.get("timestamp")))
        fresh_flag = receipt.get("fresh") is True
        if start is not None and end is not None:
            if received is None or not (start <= received <= end):
                stale += 1
                continue
        elif not fresh_flag:
            stale += 1
            continue
        valid.add(event_id)
    return valid, {
        "valid_signed_fresh_ids": summarize_ids(valid),
        "invalid_signature_records": invalid_signature,
        "stale_records": stale,
        "unidentified_records": unidentified,
    }


def verify_routing(
    manifest: Mapping[str, Any] | None,
    fixture_handle: Mapping[str, Any] | None,
    frozen_artifacts: Mapping[str, Any] | None,
    evidence: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    facts = merge_evidence(fixture_handle, evidence)
    refs = evidence_refs(evidence, "evidence:routing-probes")
    expected_match = _ids(facts.get("expected_match_ids", facts.get("matching_probe_ids")))
    expected_negative = _ids(facts.get("expected_negative_ids", facts.get("negative_probe_ids")))
    ingested = _ids(facts.get("observed_ingestion_ids", facts.get("ingested_ids")))
    healthy, health_details = _health(facts)
    window_valid, start, end, window_details = _window(facts)
    received, receipt_details = _valid_receipts(facts, start, end)
    assertions: list[dict[str, Any]] = []

    all_probes = None if expected_match is None or expected_negative is None else expected_match | expected_negative
    if all_probes is None or ingested is None:
        assertions.append(assertion(
            "routing.probes_ingested", "unknown", expected=summarize_ids(all_probes) if all_probes is not None else None,
            observed=summarize_ids(ingested) if ingested is not None else None, evidence=refs,
            explanation="The expected probe set or independent ingestion evidence is missing.",
        ))
    else:
        missing = all_probes - ingested
        assertions.append(assertion(
            "routing.probes_ingested", "pass" if not missing else "fail", expected=summarize_ids(all_probes),
            observed={"ingested": summarize_ids(ingested), "missing": summarize_ids(missing)}, evidence=refs,
            explanation="All routing probes were independently observed in ingestion." if not missing else "Some routing probes were not observed in ingestion.",
        ))

    health_status = "unknown" if healthy is None else "pass" if healthy else "unknown"
    assertions.append(assertion(
        "routing.receiver_health", health_status,
        expected={"management_reachable": True, "receiver_ready": True, "positive_control_received": True},
        observed=health_details, evidence=refs,
        explanation=(
            "Receiver readiness and positive-control delivery establish a healthy observation path."
            if healthy else "Receiver health is missing or unhealthy, so absent target receipts are not conclusive."
        ),
    ))
    assertions.append(assertion(
        "routing.observation_window", "unknown" if window_valid is None else "pass" if window_valid else "fail",
        expected={"complete": True, "minimum_seconds": float(facts.get("minimum_negative_window_seconds", 180))},
        observed=window_details, evidence=refs,
        explanation=(
            "The complete bounded observation window met its minimum duration."
            if window_valid else "The observation window is missing required timing evidence."
            if window_valid is None else "The observation window was incomplete, reversed, or too short."
        ),
    ))

    if expected_match is None or received is None:
        match_status = "unknown"
        match_missing = expected_match
        match_explanation = "Expected matching IDs or signed receipt evidence is missing."
    else:
        match_missing = expected_match - received
        if not match_missing:
            match_status = "pass"
            match_explanation = "Every fresh matching probe has a valid signed target receipt."
        elif healthy is True and window_valid is True:
            match_status = "fail"
            match_explanation = "Fresh matching probes are missing despite a healthy, complete observation window."
        else:
            match_status = "unknown"
            match_explanation = "Matching receipts are missing, but receiver health or the observation window is insufficient."
    assertions.append(assertion(
        "routing.matching_delivered", match_status,
        expected=summarize_ids(expected_match) if expected_match is not None else None,
        observed={**receipt_details, "missing": summarize_ids(match_missing or set())}, evidence=refs,
        explanation=match_explanation,
    ))

    if expected_negative is None or received is None:
        negative_status = "unknown"
        leaked: set[str] = set()
        negative_explanation = "Expected negative IDs or signed receipt evidence is missing."
    else:
        leaked = expected_negative & received
        if leaked:
            negative_status = "fail"
            negative_explanation = "One or more fresh negative probes reached the target receiver."
        elif healthy is True and window_valid is True:
            negative_status = "pass"
            negative_explanation = "No negative probe arrived during the healthy bounded observation window."
        else:
            negative_status = "unknown"
            negative_explanation = "No negative receipt was seen, but health or window evidence is insufficient."
    assertions.append(assertion(
        "routing.negatives_excluded", negative_status,
        expected={"received_negative_ids": {"count": 0, "ids": [], "truncated": False}},
        observed={"received_negative_ids": summarize_ids(leaked)}, evidence=refs,
        explanation=negative_explanation,
    ))

    before = facts.get("baseline_output_before", facts.get("baseline_config"))
    after = facts.get("baseline_output_after", facts.get("observed_baseline_config"))
    if before is None or after is None:
        baseline_status = "unknown"
    else:
        baseline_status = "pass" if before == after else "fail"
    assertions.append(assertion(
        "routing.baseline_output_unchanged", baseline_status, expected=before, observed=after, evidence=refs,
        explanation=(
            "The unrelated baseline output definition is unchanged."
            if baseline_status == "pass" else "The unrelated baseline output definition changed."
            if baseline_status == "fail" else "A before or after baseline-output snapshot is missing."
        ),
    ))
    return assertions


class RoutingVerifier:
    def verify(self, manifest: Mapping[str, Any], fixture_handle: Mapping[str, Any], frozen_artifacts: Mapping[str, Any], evidence: Mapping[str, Any]) -> list[dict[str, Any]]:
        return verify_routing(manifest, fixture_handle, frozen_artifacts, evidence)
