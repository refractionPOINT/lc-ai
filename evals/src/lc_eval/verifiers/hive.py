"""Verifier for semantic Hive updates and preservation invariants."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from .base import assertion, evidence_refs, merge_evidence


def _records(value: Any) -> dict[str, dict[str, Any]] | None:
    if isinstance(value, Mapping):
        if "records" in value:
            return _records(value["records"])
        result: dict[str, dict[str, Any]] = {}
        for name, record in value.items():
            if not isinstance(record, Mapping):
                return None
            item = deepcopy(dict(record))
            item.setdefault("name", str(name))
            result[str(name)] = item
        return result
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        result = {}
        for record in value:
            if not isinstance(record, Mapping) or not isinstance(record.get("name"), str):
                return None
            result[record["name"]] = deepcopy(dict(record))
        return result
    return None


def _semantic(record: Mapping[str, Any]) -> dict[str, Any]:
    """Keep user state and exclude known volatile backend metadata."""

    return {
        "data": deepcopy(record.get("data")),
        "usr_mtd": deepcopy(record.get("usr_mtd", record.get("user_metadata"))),
    }


def _has_field(record: Mapping[str, Any], field: str) -> bool:
    if field == "usr_mtd":
        return "usr_mtd" in record or "user_metadata" in record
    return field in record


def _has_semantics(record: Mapping[str, Any]) -> bool:
    return _has_field(record, "data") and _has_field(record, "usr_mtd")


def verify_hive(
    manifest: Mapping[str, Any] | None,
    fixture_handle: Mapping[str, Any] | None,
    frozen_artifacts: Mapping[str, Any] | None,
    evidence: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    """Check exact target semantics, distractors, record membership, and response.

    Expected evidence accepts ``expected_records`` (preferred) or a fixture
    ``expected`` value. Observations accept ``observed_records`` or ``after``.
    The baseline is required to prove distractor preservation.
    """

    facts = merge_evidence(fixture_handle, evidence)
    baseline = _records(facts.get("baseline_records", facts.get("baseline")))
    expected = _records(facts.get("expected_records", facts.get("expected")))
    observed = _records(facts.get("observed_records", facts.get("after")))
    target = facts.get("target_name")
    if not isinstance(target, str) and expected and baseline:
        changed = [name for name in expected if _semantic(expected[name]) != _semantic(baseline.get(name, {}))]
        target = changed[0] if len(changed) == 1 else None

    snapshot_refs = evidence_refs(evidence, "evidence:hive-after")
    assertions: list[dict[str, Any]] = []
    for assertion_id, field, label in (
        ("hive.target.data_exact", "data", "data"),
        ("hive.target.user_metadata_exact", "usr_mtd", "user metadata"),
    ):
        if expected is None or observed is None or not isinstance(target, str):
            assertions.append(assertion(
                assertion_id, "unknown", expected=f"exact target {label}", observed=None,
                evidence=snapshot_refs,
                explanation="The frozen expected state, observed state, or target identity is missing.",
            ))
            continue
        expected_record = expected.get(target, {})
        observed_record = observed.get(target, {})
        wanted = _semantic(expected_record).get(field) if target in expected else None
        got = _semantic(observed_record).get(field) if target in observed else None
        ground_truth_present = target in expected and _has_field(expected_record, field)
        observation_present = target in observed and _has_field(observed_record, field)
        same = ground_truth_present and observation_present and wanted == got
        status = "unknown" if not ground_truth_present else "pass" if same else "fail"
        assertions.append(assertion(
            assertion_id,
            status,
            expected=wanted,
            observed=got,
            evidence=snapshot_refs,
            explanation=(
                f"The target {label} matches exactly."
                if status == "pass"
                else f"The frozen expected target {label} is missing."
                if status == "unknown"
                else f"The target record is missing or its {label} differs from the expected semantic state."
            ),
        ))

    if baseline is None or observed is None or not isinstance(target, str):
        assertions.append(assertion(
            "hive.distractors.unchanged",
            "unknown",
            expected="all non-target records unchanged",
            observed=None,
            evidence=snapshot_refs,
            explanation="A baseline, observed snapshot, or target identity is missing.",
        ))
    else:
        names = set(baseline) - {target}
        incomplete = sorted(
            name for name in names
            if not _has_semantics(baseline[name])
        )
        changed = sorted(
            name for name in names
            if name not in observed or not _has_semantics(observed[name])
            or _semantic(baseline[name]) != _semantic(observed[name])
        )
        distractor_status = "unknown" if incomplete else "pass" if not changed else "fail"
        assertions.append(assertion(
            "hive.distractors.unchanged",
            distractor_status,
            expected={"changed": []},
            observed={"changed": changed, "incomplete_baseline": incomplete},
            evidence=snapshot_refs,
            explanation=(
                "All distractor records are unchanged."
                if distractor_status == "pass" else "The distractor baseline lacks complete semantic state."
                if distractor_status == "unknown" else "One or more distractor records changed."
            ),
        ))

    membership_expected = set(expected or baseline or {}) if (expected is not None or baseline is not None) else None
    if membership_expected is None or observed is None:
        assertions.append(assertion(
            "hive.record_set.unchanged",
            "unknown",
            expected=None,
            observed=None,
            evidence=snapshot_refs,
            explanation="The expected or observed record set is missing.",
        ))
    else:
        membership_observed = set(observed)
        same = membership_expected == membership_observed
        assertions.append(assertion(
            "hive.record_set.unchanged",
            "pass" if same else "fail",
            expected=sorted(membership_expected),
            observed={
                "records": sorted(membership_observed),
                "missing": sorted(membership_expected - membership_observed),
                "extra": sorted(membership_observed - membership_expected),
            },
            evidence=snapshot_refs,
            explanation="The Hive record set is unchanged." if same else "Hive records were added or removed.",
        ))

    deliverable = None
    if isinstance(frozen_artifacts, Mapping):
        deliverable = frozen_artifacts.get("completion", frozen_artifacts.get("final_response"))
    if not isinstance(target, str) or deliverable is None:
        status = "unknown" if deliverable is None else "fail"
        found = False
    else:
        text = deliverable if isinstance(deliverable, str) else str(deliverable)
        found = target in text
        status = "pass" if found else "fail"
    assertions.append(assertion(
        "hive.deliverable.identifies_target",
        status,
        expected={"target_name": target},
        observed={"identifies_target": found} if deliverable is not None else None,
        evidence=evidence_refs(frozen_artifacts, "artifact:completion"),
        explanation=(
            "The completion response identifies the target record."
            if status == "pass"
            else "The completion response does not identify the target record."
            if status == "fail"
            else "No frozen completion response is available."
        ),
    ))
    return assertions


class HiveVerifier:
    """Controller-compatible wrapper around :func:`verify_hive`."""

    def verify(self, manifest: Mapping[str, Any], fixture_handle: Mapping[str, Any], frozen_artifacts: Mapping[str, Any], evidence: Mapping[str, Any]) -> list[dict[str, Any]]:
        return verify_hive(manifest, fixture_handle, frozen_artifacts, evidence)
