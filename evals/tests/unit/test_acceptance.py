import json

from lc_eval.acceptance import validate_references, write_acceptance
from lc_eval.journal import Journal


def _reference(trial_id, adapter, grade, *, evidence_complete=True, execution_status="completed"):
    return {
        "trial_id": trial_id,
        "adapter": adapter,
        "scenario_id": "hive-preserve-update",
        "grade": grade,
        "execution_status": execution_status,
        "evidence_complete": evidence_complete,
        "cleanup_status": "clean",
        "assertions": [{"id": "hive.target.data_exact", "status": "fail"}],
    }


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


def test_reference_grade_without_completed_frozen_evidence_is_rejected(tmp_path):
    journal = Journal(tmp_path)
    for result in (
        _reference("good-incomplete", "reference", "pass", evidence_complete=False),
        _reference("bad-failed-process", "reference_bad", "fail", execution_status="failed"),
    ):
        journal.create_trial(result["trial_id"], "calibration", {})
        journal.finish(result["trial_id"], result)
    journal.close()

    validation = validate_references(tmp_path, "calibration")
    hive = validation["checks"][0]
    assert hive["good_trial_ids"] == []
    assert hive["bad_trial_ids"] == []


def test_acceptance_markdown_uses_reported_billing_mode(tmp_path):
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps(
            {
                "campaign": {"billing_mode": "hard_usd"},
                "acceptance": {"status": "unknown", "criteria": {}},
                "trials": [],
            }
        )
    )
    output = write_acceptance(report).read_text()
    assert "metered API usage" in output
    assert "existing subscriptions" not in output
