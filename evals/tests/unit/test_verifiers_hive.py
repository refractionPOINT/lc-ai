from lc_eval.verifiers.hive import verify_hive


def _record(name, owner, *, tag="preserve"):
    return {
        "name": name,
        "data": {"asset-a": {"owner": owner, "nested": {"ticket": "LC-7"}}},
        "usr_mtd": {"enabled": True, "tags": [tag], "comment": "keep"},
        "sys_mtd": {"etag": "volatile"},
    }


def test_hive_checks_exact_nested_state_and_ignores_system_metadata():
    baseline = [_record("target", "old"), _record("target-copy", "other")]
    expected = [_record("target", "platform-ops"), _record("target-copy", "other")]
    observed = [_record("target", "platform-ops"), _record("target-copy", "other")]
    observed[0]["sys_mtd"] = {"etag": "new"}
    results = verify_hive(
        {}, {"target_name": "target", "baseline_records": baseline, "expected_records": expected},
        {"completion": "Updated target owner to platform-ops."}, {"observed_records": observed},
    )
    assert {result["status"] for result in results} == {"pass"}


def test_hive_detects_nested_loss_and_distractor_mutation():
    baseline = [_record("target", "old"), _record("target-copy", "other")]
    expected = [_record("target", "platform-ops"), _record("target-copy", "other")]
    observed = [_record("target", "platform-ops"), _record("target-copy", "changed")]
    del observed[0]["data"]["asset-a"]["nested"]
    results = verify_hive(
        {}, {"target_name": "target", "baseline_records": baseline, "expected_records": expected},
        {"completion": "done"}, {"observed_records": observed},
    )
    statuses = {result["id"]: result["status"] for result in results}
    assert statuses["hive.target.data_exact"] == "fail"
    assert statuses["hive.target.user_metadata_exact"] == "pass"
    assert statuses["hive.distractors.unchanged"] == "fail"
    assert statuses["hive.deliverable.identifies_target"] == "fail"


def test_hive_missing_snapshot_is_unknown_not_pass():
    results = verify_hive({}, {"target_name": "target"}, {}, {})
    assert all(result["status"] == "unknown" for result in results)
