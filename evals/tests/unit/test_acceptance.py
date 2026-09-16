from lc_eval.acceptance import validate_references
from lc_eval.journal import Journal


def test_reference_validation_does_not_accept_failed_process_without_named_assertion(tmp_path):
    j = Journal(tmp_path)
    tid = "bad-hive"
    j.create_trial(tid, "calibration", {})
    j.finish(
        tid,
        {
            "trial_id": tid,
            "adapter": "reference_bad",
            "scenario_id": "hive-preserve-update",
            "grade": "fail",
            "cleanup_status": "clean",
            "assertions": [],
        },
    )
    result = validate_references(tmp_path, "calibration")
    assert result["reference_validation_passed"] is False
    assert result["checks"][0]["bad_trial_ids"] == []


def test_missing_reference_evidence_stays_unproved(tmp_path):
    result = validate_references(tmp_path)
    assert result["reference_validation_passed"] is False
    assert len(result["checks"]) == 3
    assert all(not check["passed"] for check in result["checks"])
