import json

from lc_eval.verifiers.native_sensor import PATH, verify_native_sensor


def _facts():
    marker = "lc_eval_marker_abc"
    return {
        "marker": marker, "required_tag": "lc-eval:abc", "installation_key_description": "lc-eval-native-abc",
        "baseline_keys": {"old": {"desc": "distractor"}}, "baseline_sensors": [{"sid": "old-sid"}],
        "sensor_id": "new-sid", "sensor": {"sid": "new-sid", "alive": "2026-09-17 02:52:36", "version": "lc_sensor_5.3.9"},
        "online_sensors": [{"sid": "new-sid", "alive": "2026-09-17 02:52:36"}], "tags": ["lc-eval:abc"],
        "trusted_task_result": [{"routing": {"event_type": "OS_PROCESSES_REP"}, "event": {"PROCESSES": [{"COMMAND_LINE": f"python sleeper.py {marker}", "FILE_PATH": "/usr/bin/python", "PROCESS_ID": 42}]}}],
        "keys_after": {"old": {"desc": "distractor"}, "new": {"desc": "lc-eval-native-abc"}},
        "sensors_after": [{"sid": "old-sid"}, {"sid": "new-sid"}], "binary_sha256": "a" * 64,
        "deployment": {"network_mode": "bridge", "privileged": False, "read_only": True, "binds": None, "mounts": [], "cap_drop": ["ALL"]},
        "enrollment_state": "registered", "error_stage": None,
    }


def _frozen(value):
    return {"files": {PATH: {"path": PATH, "kind": "file", "content": json.dumps(value), "within_workspace": True}}}


def test_native_sensor_complete_real_evidence_passes():
    facts = _facts()
    results = verify_native_sensor({}, facts, _frozen(facts["trusted_task_result"]), {})
    assert all(item["status"] == "pass" for item in results)


def test_native_sensor_candidate_claim_without_trusted_marker_fails():
    facts = _facts()
    facts["trusted_task_result"] = [{"routing": {"event_type": "OS_PROCESSES_REP"}, "event": {"PROCESSES": []}}]
    statuses = {item["id"]: item["status"] for item in verify_native_sensor({}, facts, _frozen([{"marker": facts["marker"]}]), {})}
    assert statuses["native_sensor.task.marker_observed"] == "fail"


def test_native_sensor_missing_external_observations_are_unknown():
    facts = {"marker": "marker", "required_tag": "tag"}
    statuses = {item["id"]: item["status"] for item in verify_native_sensor({}, facts, {}, {})}
    assert statuses["native_sensor.registered"] == "unknown"
    assert statuses["native_sensor.task.real_response"] == "unknown"
    assert statuses["native_sensor.task.marker_observed"] == "unknown"


def test_native_sensor_rejects_substring_decoys_and_changed_baseline_key():
    facts = _facts()
    facts["tags"] = ["prefix-" + facts["required_tag"]]
    facts["keys_after"]["old"]["desc"] = "changed"
    candidate = facts["trusted_task_result"]
    candidate[0]["event"]["PROCESSES"][0]["COMMAND_LINE"] += "-suffix"
    statuses = {item["id"]: item["status"] for item in verify_native_sensor({}, facts, _frozen(candidate), {})}
    assert statuses["native_sensor.tagged"] == "fail"
    assert statuses["native_sensor.keys.preserved"] == "fail"
    assert statuses["native_sensor.task.marker_observed"] == "fail"


def test_native_sensor_missing_or_malformed_artifact_fails_with_trusted_evidence():
    facts = _facts()
    missing = {item["id"]: item["status"] for item in verify_native_sensor({}, facts, {}, {})}
    malformed = {item["id"]: item["status"] for item in verify_native_sensor({}, facts, {"files": {PATH: {"path": PATH, "content": "{"}}}, {})}
    assert missing["native_sensor.task.marker_observed"] == "fail"
    assert malformed["native_sensor.task.marker_observed"] == "fail"


def test_native_sensor_omitted_and_invalid_enrollment_are_candidate_failures():
    omitted = _facts()
    omitted.update(enrollment_state="missing", error_stage="missing_request")
    invalid = _facts()
    invalid.update(enrollment_state="invalid", error_stage="invalid_request")
    for facts in (omitted, invalid):
        statuses = {item["id"]: item["status"] for item in verify_native_sensor({}, facts, _frozen(facts["trusted_task_result"]), {})}
        assert statuses["native_sensor.enrollment.request"] == "fail"


def test_native_sensor_real_cli_timestamp_alive_uses_online_membership():
    facts = _facts()
    results = {item["id"]: item for item in verify_native_sensor({}, facts, _frozen(facts["trusted_task_result"]), {})}
    assert results["native_sensor.registered"]["status"] == "pass"
    assert results["native_sensor.registered"]["observed"]["alive_display"] == "2026-09-17 02:52:36"
    assert results["native_sensor.registered"]["observed"]["sensor_version"] == "lc_sensor_5.3.9"


def test_native_sensor_does_not_assume_missing_sensor_sid_matches_requested_sid():
    facts = _facts()
    facts["sensor"] = {"alive": "2026-09-17 02:52:36", "version": "lc_sensor_5.3.9"}
    status = {item["id"]: item["status"] for item in verify_native_sensor({}, facts, _frozen(facts["trusted_task_result"]), {})}
    assert status["native_sensor.registered"] == "fail"
