from copy import deepcopy

from lc_eval.verifiers.cases import verify_cases


DETECTION = {"detect_id": "det-1", "cat": "eval"}
DESIRED = {
    "status": "in_progress", "severity": "high",
    "entity": {"entity_type": "domain", "entity_value": "x.example.test", "note": "supplied", "verdict": "suspicious"},
    "note": {"content": "eval=x; action=triage", "note_type": "analysis", "is_public": False},
}


def _snapshot():
    return {
        "case": {"case_number": 7, "status": "in_progress", "severity": "high", "last_updated_at": "later"},
        "detections": [{"detect_id": "det-1"}],
        "entities": [DESIRED["entity"]],
        "events": [{"event_type": "case_note_added", "metadata": DESIRED["note"]}],
    }


def _fixture(snapshot=None):
    snap = snapshot or _snapshot()
    distractor = {"case": {"case_number": 8, "status": "new", "severity": "medium"}, "detections": [], "entities": [], "events": []}
    return {
        "variant": "clean", "detection": DETECTION, "desired": DESIRED,
        "baseline_target": None, "baseline_distractors": {"8": distractor},
        "target_matches": [{"case_number": 7, "detection_count": 1, "snapshot": snap}],
        "observed_distractors": {"8": deepcopy(distractor)},
    }


def test_cases_correct_state_passes():
    results = verify_cases({}, _fixture(), {"completion": "Maintained case 7 for detection det-1"}, {})
    assert {result["status"] for result in results} == {"pass"}


def test_cases_detects_duplicate_note_missing_entity_and_distractor_change():
    snap = _snapshot()
    snap["entities"] = []
    snap["events"].append(deepcopy(snap["events"][0]))
    fixture = _fixture(snap)
    fixture["observed_distractors"]["8"]["case"]["severity"] = "critical"
    results = verify_cases({}, fixture, {"completion": "case 7 det-1"}, {})
    statuses = {result["id"]: result["status"] for result in results}
    assert statuses["cases.target.entity_once"] == "fail"
    assert statuses["cases.target.note_once"] == "fail"
    assert statuses["cases.distractor.unchanged"] == "fail"


def test_cases_partial_preserves_seeded_records():
    baseline = _snapshot()
    baseline["entities"] = [{"entity_type": "user", "entity_value": "alice", "note": "keep", "verdict": "informational"}]
    baseline["events"] = [{"event_type": "case_note_added", "metadata": {"content": "keep", "note_type": "handoff", "is_public": False}}]
    observed = _snapshot()
    observed["entities"].extend(deepcopy(baseline["entities"]))
    observed["events"].extend(deepcopy(baseline["events"]))
    fixture = _fixture(observed)
    fixture.update({"variant": "partial", "baseline_target": baseline})
    results = verify_cases({}, fixture, {"completion": "case 7 det-1"}, {})
    assert {row["id"]: row["status"] for row in results}["cases.target.preexisting_preserved"] == "pass"


def test_cases_missing_observation_is_inconclusive():
    fixture = {"variant": "clean", "detection": DETECTION, "desired": DESIRED}
    results = verify_cases({}, fixture, {}, {})
    assert all(row["status"] == "unknown" for row in results)
