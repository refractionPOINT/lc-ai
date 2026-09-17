from copy import deepcopy

from lc_eval.verifiers.reconcile import verify


def _record(owner, *, comment="managed", tags=None):
    return {
        "data": {"lookup_data": {"application": {"owner": owner, "tier": "critical"}}},
        "usr_mtd": {"enabled": True, "tags": tags or ["eval", "managed"], "comment": comment},
    }


def _fixture():
    lookup = _record("platform")
    rule = {
        "data": {"detect": {"event": "LC_EVAL_CONFIG", "op": "is", "path": "event/environment", "value": "production"},
                 "respond": [{"action": "report", "name": "eval-config-production"}]},
        "usr_mtd": {"enabled": True, "tags": ["eval", "managed"], "comment": "Managed production rule"},
    }
    archive = _record("platform", comment="Unrelated: retain exactly")
    expected = {"lookup": {"owners": lookup, "owners-archive": archive}, "dr-general": {"prod-rule": rule}}
    return {
        "desired": {"lookup": {"owners": lookup}, "dr-general": {"prod-rule": rule}},
        "expected": expected,
        "baseline": {"lookup": {"owners": _record("legacy"), "owners-archive": archive}, "dr-general": {}},
    }


def test_reconcile_verifier_accepts_exact_multi_hive_state():
    fixture = _fixture()
    results = verify({}, fixture, {}, {"state": deepcopy(fixture["expected"])})
    assert {row["status"] for row in results} == {"pass"}


def test_reconcile_ignores_only_canonical_backend_lookup_optimization():
    fixture = _fixture()
    observed = deepcopy(fixture["expected"])
    observed["lookup"]["owners"]["data"]["optimized_lookup_data"] = {
        "_LC_INDICATORS": None, "_LC_METADATA": None}
    observed["lookup"]["owners-archive"]["data"]["optimized_lookup_data"] = {
        "_LC_INDICATORS": None, "_LC_METADATA": None}
    results = verify({}, fixture, {}, {"state": observed})
    assert {row["status"] for row in results} == {"pass"}


def test_reconcile_rejects_noncanonical_optimization_data():
    fixture = _fixture()
    observed = deepcopy(fixture["expected"])
    observed["lookup"]["owners"]["data"]["optimized_lookup_data"] = {
        "_LC_INDICATORS": ["candidate supplied"], "_LC_METADATA": None}
    statuses = {row["id"]: row["status"] for row in verify({}, fixture, {}, {"state": observed})}
    assert statuses["config.desired_exact"] == "fail"


def test_reconcile_verifier_rejects_stale_target_distractor_change_and_extra_record():
    fixture = _fixture()
    observed = deepcopy(fixture["expected"])
    observed["lookup"]["owners"]["data"]["lookup_data"]["application"]["owner"] = "legacy"
    observed["lookup"]["owners-archive"]["usr_mtd"]["comment"] = "changed"
    observed["lookup"]["extra-copy"] = _record("platform")
    statuses = {row["id"]: row["status"] for row in verify({}, fixture, {}, {"state": observed})}
    assert statuses == {
        "config.desired_exact": "fail",
        "config.unrelated_preserved": "fail",
        "config.record_sets_exact": "fail",
    }


def test_reconcile_verifier_rejects_unrequested_target_metadata():
    fixture = _fixture()
    observed = deepcopy(fixture["expected"])
    observed["lookup"]["owners"]["usr_mtd"]["unexpected"] = "should-not-be-added"
    statuses = {row["id"]: row["status"] for row in verify({}, fixture, {}, {"state": observed})}
    assert statuses["config.desired_exact"] == "fail"


def test_reconcile_missing_snapshot_is_unknown():
    results = verify({}, _fixture(), {}, {})
    assert [(row["id"], row["status"]) for row in results] == [("config.observed", "unknown")]


def test_reconcile_tag_order_is_semantic_but_duplicate_tags_are_changes():
    fixture = _fixture()
    observed = deepcopy(fixture["expected"])
    observed["lookup"]["owners"]["usr_mtd"]["tags"].reverse()
    assert {row["status"] for row in verify({}, fixture, {}, {"state": observed})} == {"pass"}
    observed["lookup"]["owners"]["usr_mtd"]["tags"].append("eval")
    statuses = {row["id"]: row["status"] for row in verify({}, fixture, {}, {"state": observed})}
    assert statuses["config.desired_exact"] == "fail"
