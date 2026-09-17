import csv
import io

from lc_eval.verifiers.cloudsec import PATH, verify_cloudsec


def _fixture():
    rows = {
        "fnd-a": {"finding_id": "fnd-a", "severity": "HIGH", "status": "open", "owner": "", "title": "a", "finding_class": "code_weakness", "rule_id": "A", "resolution": "", "ticket": ""},
        "fnd-b": {"finding_id": "fnd-b", "severity": "HIGH", "status": "open", "owner": "", "title": "b", "finding_class": "code_weakness", "rule_id": "B", "resolution": "", "ticket": ""},
    }
    return {"expected_export": rows, "baseline_findings": rows, "target_ids": ["fnd-a"], "target_owner": "owner@example.invalid", "policy_before": {"p": 1}, "readiness": {"main": 7, "distractors": 3}}


def _csv(rows):
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=["finding_id", "severity", "status", "owner", "title", "finding_class", "rule_id"], extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return {"files": {PATH: {"path": PATH, "kind": "file", "within_workspace": True, "content": stream.getvalue()}}}


def test_cloudsec_exact_export_and_triage_pass():
    fixture = _fixture()
    after = {key: dict(value) for key, value in fixture["baseline_findings"].items()}
    after["fnd-a"].update(owner=fixture["target_owner"], status="accepted", resolution="accepted")
    results = verify_cloudsec({}, fixture, _csv(fixture["expected_export"].values()), {"findings_after": after, "collection_complete": True, "policy_after": {"p": 1}})
    assert all(item["status"] == "pass" for item in results)


def test_cloudsec_partial_export_and_wrong_nontarget_fail():
    fixture = _fixture()
    after = {key: dict(value) for key, value in fixture["baseline_findings"].items()}
    after["fnd-a"].update(owner=fixture["target_owner"], status="accepted", resolution="accepted")
    after["fnd-b"]["owner"] = fixture["target_owner"]
    results = verify_cloudsec({}, fixture, _csv([fixture["expected_export"]["fnd-a"]]), {"findings_after": after, "collection_complete": True, "policy_after": {"p": 1}})
    statuses = {item["id"]: item["status"] for item in results}
    assert statuses["cloudsec.export.membership"] == "fail"
    assert statuses["cloudsec.nontargets.preserved"] == "fail"


def test_cloudsec_missing_observations_are_unknown():
    results = verify_cloudsec({}, _fixture(), _csv(_fixture()["expected_export"].values()), {})
    statuses = {item["id"]: item["status"] for item in results}
    assert statuses["cloudsec.targets.owner"] == "unknown"
    assert statuses["cloudsec.policy.preserved"] == "unknown"
