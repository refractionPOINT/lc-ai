"""Deterministic grading for bounded case lifecycle maintenance."""

from __future__ import annotations

import re

from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from .base import assertion, evidence_refs, merge_evidence


def _rows(value: Any, key: str) -> list[Mapping[str, Any]] | None:
    if not isinstance(value, Mapping):
        return None
    rows = value.get(key)
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return None
    return [row for row in rows if isinstance(row, Mapping)]


def _case(snapshot: Any) -> Mapping[str, Any] | None:
    value = snapshot.get("case") if isinstance(snapshot, Mapping) else None
    return value if isinstance(value, Mapping) else None


def _note_key(event: Mapping[str, Any]) -> tuple[Any, Any, Any]:
    metadata = event.get("metadata")
    metadata = metadata if isinstance(metadata, Mapping) else {}
    return metadata.get("content"), metadata.get("note_type", "general"), metadata.get("is_public", False)


def _entity_key(entity: Mapping[str, Any]) -> tuple[Any, Any, Any, Any]:
    return entity.get("entity_type"), entity.get("entity_value"), entity.get("note"), entity.get("verdict")


def _stable_distractor(snapshot: Any) -> Any:
    """Exclude only server-controlled read metadata, retaining all user state."""
    if not isinstance(snapshot, Mapping):
        return None
    value = deepcopy(dict(snapshot))
    if "case" not in value:
        return {key: _stable_distractor(item) for key, item in value.items()}
    case = value.get("case")
    if isinstance(case, dict):
        for key in ("last_updated_at", "last_updated_by"):
            case.pop(key, None)
    return value


def verify_cases(
    manifest: Mapping[str, Any] | None,
    fixture_handle: Mapping[str, Any] | None,
    frozen_artifacts: Mapping[str, Any] | None,
    evidence: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    del manifest
    facts = merge_evidence(fixture_handle, evidence)
    matches = facts.get("target_matches")
    desired = facts.get("desired")
    detection = facts.get("detection")
    refs = evidence_refs(evidence, "evidence:cases-after")
    valid_matches = matches if isinstance(matches, list) else None
    unique = valid_matches is not None and len(valid_matches) == 1
    results = [assertion(
        "cases.target.unique",
        "unknown" if valid_matches is None else "pass" if unique else "fail",
        expected={"matching_cases": 1},
        observed=None if valid_matches is None else {"matching_cases": len(valid_matches)},
        evidence=refs,
        explanation=("The supplied detection identifies exactly one case." if unique else
                     "Target case observations are missing." if valid_matches is None else
                     "The supplied detection is missing or linked to multiple cases."),
    )]
    snap = valid_matches[0].get("snapshot") if unique and isinstance(valid_matches[0], Mapping) else None
    case = _case(snap)

    if not isinstance(desired, Mapping) or case is None:
        field_status = "unknown"
        field_observed = None
        field_expected = None if not isinstance(desired, Mapping) else {
            "status": desired.get("status"), "severity": desired.get("severity")}
    else:
        field_expected = {"status": desired.get("status"), "severity": desired.get("severity")}
        field_observed = {"status": case.get("status"), "severity": case.get("severity")}
        field_status = "pass" if field_observed == field_expected else "fail"
    results.append(assertion(
        "cases.target.fields_exact", field_status, expected=field_expected, observed=field_observed,
        evidence=refs, explanation="The target status and severity match." if field_status == "pass" else
        "Target case fields could not be observed." if field_status == "unknown" else
        "The target status or severity differs from the supplied values.",
    ))

    detections = _rows(snap, "detections")
    detect_id = detection.get("detect_id") if isinstance(detection, Mapping) else None
    detect_count = None if detections is None or not isinstance(detect_id, str) else sum(
        row.get("detect_id") == detect_id for row in detections)
    results.append(assertion(
        "cases.target.detection_once", "unknown" if detect_count is None else "pass" if detect_count == 1 else "fail",
        expected={"detect_id": detect_id, "count": 1}, observed=None if detect_count is None else {"count": detect_count},
        evidence=refs, explanation="The supplied detection is attached exactly once." if detect_count == 1 else
        "Detection observations or expected identity are missing." if detect_count is None else
        "The supplied detection is not attached exactly once.",
    ))

    entities = _rows(snap, "entities")
    wanted_entity = desired.get("entity") if isinstance(desired, Mapping) else None
    wanted_entity_key = _entity_key(wanted_entity) if isinstance(wanted_entity, Mapping) else None
    entity_count = None if entities is None or wanted_entity_key is None else sum(
        _entity_key(row) == wanted_entity_key for row in entities)
    results.append(assertion(
        "cases.target.entity_once", "unknown" if entity_count is None else "pass" if entity_count == 1 else "fail",
        expected={"entity": wanted_entity, "count": 1}, observed=None if entity_count is None else {"count": entity_count},
        evidence=refs, explanation="The supplied entity is attached exactly once with its metadata." if entity_count == 1 else
        "Entity observations or expected values are missing." if entity_count is None else
        "The supplied entity is missing, duplicated, or has incorrect metadata.",
    ))

    events = _rows(snap, "events")
    notes = None if events is None else [event for event in events if event.get("event_type") == "case_note_added"]
    wanted_note = desired.get("note") if isinstance(desired, Mapping) else None
    wanted_note_key = (
        wanted_note.get("content"), wanted_note.get("note_type"), wanted_note.get("is_public")
    ) if isinstance(wanted_note, Mapping) else None
    note_count = None if notes is None or wanted_note_key is None else sum(_note_key(row) == wanted_note_key for row in notes)
    results.append(assertion(
        "cases.target.note_once", "unknown" if note_count is None else "pass" if note_count == 1 else "fail",
        expected={"note": wanted_note, "count": 1}, observed=None if note_count is None else {"count": note_count},
        evidence=refs, explanation="The structured private note exists exactly once." if note_count == 1 else
        "Note observations or expected values are missing." if note_count is None else
        "The structured note is missing, duplicated, public, or has the wrong type.",
    ))

    baseline = facts.get("baseline_target")
    if baseline is None and facts.get("variant") == "clean" and snap is not None:
        expected_dets = Counter([detect_id]) if isinstance(detect_id, str) else Counter()
        expected_entities = Counter([wanted_entity_key]) if wanted_entity_key is not None else Counter()
        expected_notes = Counter([wanted_note_key]) if wanted_note_key is not None else Counter()
        observed_dets = Counter(row.get("detect_id") for row in (detections or []))
        observed_entities = Counter(_entity_key(row) for row in (entities or []))
        observed_notes = Counter(
            _note_key(row) for row in (events or []) if row.get("event_type") == "case_note_added"
        )
        exact = (observed_dets == expected_dets and observed_entities == expected_entities
                 and observed_notes == expected_notes)
        preserved_status = "pass" if exact else "fail"
        preserved_observed = {"record_multisets_exact": exact}
    elif not isinstance(baseline, Mapping) or snap is None:
        preserved_status, preserved_observed = "unknown", None
    else:
        expected_dets = Counter(row.get("detect_id") for row in (_rows(baseline, "detections") or []))
        observed_dets = Counter(row.get("detect_id") for row in (detections or []))
        expected_entities = Counter(_entity_key(row) for row in (_rows(baseline, "entities") or []))
        expected_entities[wanted_entity_key] += 1
        observed_entities = Counter(_entity_key(row) for row in (entities or []))
        expected_notes = Counter(
            _note_key(row) for row in (_rows(baseline, "events") or [])
            if row.get("event_type") == "case_note_added"
        )
        expected_notes[wanted_note_key] += 1
        observed_notes = Counter(
            _note_key(row) for row in (events or []) if row.get("event_type") == "case_note_added"
        )
        exact = (observed_dets == expected_dets and observed_entities == expected_entities
                 and observed_notes == expected_notes)
        preserved_status = "pass" if exact else "fail"
        preserved_observed = {"record_multisets_exact": exact}
    results.append(assertion(
        "cases.target.preexisting_preserved", preserved_status,
        expected={"record_multisets_exact": True}, observed=preserved_observed,
        evidence=refs, explanation="The target contains exactly the seeded records and requested additions." if preserved_status == "pass" else
        "Pre-existing target state could not be observed." if preserved_status == "unknown" else
        "Target records were removed, changed, or duplicated.",
    ))

    baseline_other = facts.get("baseline_distractors")
    observed_other = facts.get("observed_distractors")
    if baseline_other is None or observed_other is None:
        distractor_status = "unknown"
    else:
        distractor_status = "pass" if _stable_distractor(baseline_other) == _stable_distractor(observed_other) else "fail"
    results.append(assertion(
        "cases.distractor.unchanged", distractor_status, expected="exact unrelated case state",
        observed=None if observed_other is None else "observed", evidence=refs,
        explanation="The unrelated case is unchanged." if distractor_status == "pass" else
        "The unrelated case baseline or observation is missing." if distractor_status == "unknown" else
        "The unrelated case changed.",
    ))

    completion = frozen_artifacts.get("completion", frozen_artifacts.get("final_response")) if isinstance(frozen_artifacts, Mapping) else None
    number = valid_matches[0].get("case_number") if unique else None
    text = completion if isinstance(completion, str) else ""
    # A small case number must not match a digit inside the detection UUID.
    readable = text.translate(str.maketrans('', '', '*`'))
    case_label = re.search(
        rf'(?i)\bcase(?:[ _-]*(?:number|id))?[\s:#"\'=|\[\]]*{number}\b',
        readable,
    ) if isinstance(number, int) else None
    found = bool(case_label) and isinstance(detect_id, str) and detect_id in text
    deliverable_status = "unknown" if completion is None else "pass" if found else "fail"
    results.append(assertion(
        "cases.deliverable.identifies_target", deliverable_status,
        expected={"case_number": number, "detection_id": detect_id}, observed=None if completion is None else {"identifies_both": found},
        evidence=evidence_refs(frozen_artifacts, "artifact:completion"),
        explanation="The completion identifies the case and detection." if deliverable_status == "pass" else
        "No frozen completion response is available." if deliverable_status == "unknown" else
        "The completion does not identify both the case and detection.",
    ))
    return results


verify = verify_cases


class CasesVerifier:
    def verify(self, manifest: Mapping[str, Any], fixture_handle: Mapping[str, Any], frozen_artifacts: Mapping[str, Any], evidence: Mapping[str, Any]) -> list[dict[str, Any]]:
        return verify_cases(manifest, fixture_handle, frozen_artifacts, evidence)
