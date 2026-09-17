import asyncio
from pathlib import Path
from types import SimpleNamespace
import json
import uuid

from lc_eval.fixtures import cases
from lc_eval.fixtures.local_cli import ControlError


class _CLI:
    def __init__(self):
        self.invocations = []

    def invoke(self, args, oid):
        self.invocations.append((args, oid))
        return {}


def test_case_fixture_seed_variants_are_distinct(monkeypatch, tmp_path: Path):
    created = []
    notes = []

    def create(_cli, _oid, detection, summary, severity):
        created.append((detection, summary, severity))
        return len(created)

    def api(_cli, _oid, method, path, *, body=None, params=None):
        del params
        if method == "POST" and path.endswith("/notes"):
            notes.append(body)
        return {}

    monkeypatch.setattr(cases, "_create", create)
    monkeypatch.setattr(cases, "_api", api)
    monkeypatch.setattr(cases, "_wait_ready", lambda *_args: {})
    monkeypatch.setattr(cases, "_wait_list_ready", lambda *_args: None)
    monkeypatch.setattr(cases, "snapshot_case", lambda _cli, _oid, number: {
        "case": {"case_number": number}, "events": [], "detections": [], "entities": []})

    cli = _CLI()
    config = SimpleNamespace(
        limits=SimpleNamespace(verification_seconds=30),
        lc=SimpleNamespace(readiness_seconds=600),
    )
    partial = cases.provision(config, cli, None, "trial", "oid", 1, tmp_path)
    distractor = cases.provision(config, cli, None, "trial", "oid", 2, tmp_path)

    assert partial["variant"] == "partial" and partial["target_case_number"] is not None
    assert distractor["variant"] == "distractor"
    assert len(partial["distractor_case_numbers"]) == 1
    assert len(distractor["distractor_case_numbers"]) == 3
    assert uuid.UUID(partial["detection"]["detect_id"])
    assert uuid.UUID(partial["detection"]["routing"]["sid"])
    assert [call[0] for call in cli.invocations].count(
        ["extension", "subscribe", "--name", "ext-cases"]) == 2
    assert any(note["content"] == "Pre-existing analyst note; preserve exactly." for note in notes)


def test_clean_case_variant_is_explicitly_unsupported_before_mutation(tmp_path):
    cli = _CLI()
    config = SimpleNamespace(limits=SimpleNamespace(verification_seconds=30))
    try:
        cases.provision(config, cli, None, "trial", "oid", 0, tmp_path)
    except cases.CaseCreateUnsupportedError as error:
        assert "pinned native CLI" in str(error)
    else:
        raise AssertionError("clean case variant was allowed despite broken native create")
    assert cli.invocations == []


def test_trusted_case_seed_encodes_detection_as_json_string():
    class CLI:
        def invoke(self, args, oid):
            assert oid == "oid"
            assert args[:6] == [
                "extension", "request", "--name", "ext-cases", "--action", "create_case"]
            payload = json.loads(args[7])
            assert isinstance(payload["detection"], str)
            assert json.loads(payload["detection"])["detect_id"] == "detect-id"
            return {"data": {"created": 1, "case_number": 42}}

    assert cases._create(CLI(), "oid", {"detect_id": "detect-id"}, "summary", "low") == 42


def test_cases_readiness_retries_transient_absence(monkeypatch):
    attempts = []

    def api(*_args, **_kwargs):
        attempts.append(1)
        if len(attempts) < 3:
            raise ControlError("not ready", status_code=404)
        return {"severity_mapping": {"critical_min": 8}}

    monkeypatch.setattr(cases, "_api", api)
    assert cases._wait_ready(object(), "oid", 1, retry_seconds=0)["severity_mapping"]
    assert len(attempts) == 3


def test_cases_readiness_does_not_retry_authorization_failure(monkeypatch):
    def denied(*_args, **_kwargs):
        raise ControlError("forbidden", status_code=403)

    monkeypatch.setattr(cases, "_api", denied)
    try:
        cases._wait_ready(object(), "oid", 1, retry_seconds=0)
    except ControlError as error:
        assert error.status_code == 403
    else:
        raise AssertionError("authorization failure was retried or accepted")


def test_case_collect_uses_detection_identity(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(cases, "_list_cases", lambda *_args: [{"case_number": 7}, {"case_number": 8}])

    def snapshot(_cli, _oid, number):
        detect_id = "target" if number == 7 else "other"
        return {"case": {"case_number": number}, "events": [], "entities": [],
                "detections": [{"detect_id": detect_id}]}

    monkeypatch.setattr(cases, "snapshot_case", snapshot)
    fixture = {"detection": {"detect_id": "target", "cat": "category"},
               "target_case_number": 7, "distractor_case_numbers": [8]}
    observed = cases.collect(None, object(), "oid", fixture, tmp_path)
    assert [row["case_number"] for row in observed["target_matches"]] == [7]
    assert observed["observed_distractors"]["8"]["case"]["case_number"] == 8


def test_case_collect_uses_trusted_target_when_list_index_omits_it(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(cases, "_list_cases", lambda *_args: [{"case_number": 8}])

    def snapshot(_cli, _oid, number):
        detect_id = "target" if number == 7 else "other"
        return {"case": {"case_number": number}, "events": [], "entities": [],
                "detections": [{"detect_id": detect_id, "sid": "sid", "hostname": "host",
                                "detection_cat": "category", "detection_source": "source",
                                "detection_priority": 0}]}

    monkeypatch.setattr(cases, "snapshot_case", snapshot)
    fixture = {"detection": {"detect_id": "target", "cat": "category"},
               "target_case_number": 7, "distractor_case_numbers": [8]}
    observed = cases.collect(None, object(), "oid", fixture, tmp_path)
    assert observed["target_matches"] == [{
        "case_number": 7, "detection_count": 1, "snapshot": snapshot(None, None, 7)}]


def test_case_list_reads_actual_cases_projection_without_search():
    class CLI:
        def get_urls(self, oid):
            assert oid == "oid"
            return {"cases": "cases.example"}

        def api(self, oid, method, path, **kwargs):
            assert (oid, method, path) == ("oid", "GET", "cases")
            assert kwargs["params"] == {"oids": "oid", "page_size": "200"}
            return {"cases": [{"case_number": 1, "detection_cats": ["category"]}],
                    "next_page_token": ""}

    assert cases._list_cases(CLI(), "oid") == [
        {"case_number": 1, "detection_cats": ["category"]}]


def test_cases_permissions_are_the_exact_backend_route_requirements():
    assert set(cases.PERMISSIONS) == {
        "org.get", "investigation.get", "investigation.set", "ext.request",
    }


def test_case_list_readiness_waits_out_subscription_cache_and_proves_detections(monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(cases.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(cases.time, "sleep", lambda seconds: clock.__setitem__(0, clock[0] + seconds))
    monkeypatch.setattr(cases, "_list_cases", lambda *_args: [
        {"case_number": 1}, {"case_number": 2}])
    monkeypatch.setattr(cases, "_component", lambda _cli, _oid, number, _name: [
        {"detect_id": "target" if number == 1 else "distractor"}])

    cases._wait_list_ready(
        object(), "oid", {1: "target", 2: "distractor"},
        tenant_ready_at=100.0, timeout_seconds=360.0, retry_seconds=5.0,
    )
    assert clock[0] >= 100.0 + cases.SUBSCRIBED_CACHE_TTL_SECONDS + cases.SUBSCRIBED_CACHE_MARGIN_SECONDS


def test_case_list_readiness_rejects_missing_seeded_case(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(cases.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(cases.time, "sleep", lambda seconds: clock.__setitem__(0, clock[0] + seconds))
    monkeypatch.setattr(cases, "_list_cases", lambda *_args: [{"case_number": 1}])
    try:
        cases._wait_list_ready(
            object(), "oid", {1: "target", 2: "distractor"},
            tenant_ready_at=0.0, timeout_seconds=320.0, retry_seconds=20.0,
        )
    except ControlError as error:
        assert "missing=[2]" in str(error)
    else:
        raise AssertionError("readiness accepted an incomplete list index")


def test_case_reference_discovers_detection_through_native_cli(monkeypatch):
    calls = []

    def fake_run(argv, *, timeout):
        calls.append(argv)
        command = argv[6:]
        if command == ["case", "list", "--limit", "200"]:
            return json.dumps({"cases": [{"case_number": 8}, {"case_number": 7}],
                               "next_page_token": ""})
        if command == ["case", "detection", "list", "--case", "8"]:
            return json.dumps({"detections": [{"detect_id": "other"}]})
        if command == ["case", "detection", "list", "--case", "7"]:
            return json.dumps({"detections": [{"detect_id": "target"}]})
        return "{}"

    monkeypatch.setattr("lc_eval.execution.docker.run", fake_run)
    fixture = {
        "target_case_number": 7,
        "public": {
            "detection_id": "target", "target_status": "in_progress",
            "target_severity": "high", "entity_type": "domain",
            "entity_value": "target.example", "entity_note": "note",
            "entity_verdict": "suspicious", "note_type": "analysis",
            "note_content": "content",
        },
    }
    completion = asyncio.run(cases.reference(
        fixture, SimpleNamespace(agent="candidate-container")))

    native = [argv[6:] for argv in calls]
    assert native[:3] == [
        ["case", "list", "--limit", "200"],
        ["case", "detection", "list", "--case", "8"],
        ["case", "detection", "list", "--case", "7"],
    ]
    assert ["case", "update", "--case-number", "7", "--status", "in_progress",
            "--severity", "high"] in native
    assert "case 7" in completion


def test_case_reference_does_not_fall_back_to_trusted_number(monkeypatch):
    monkeypatch.setattr(
        "lc_eval.execution.docker.run",
        lambda _argv, *, timeout: json.dumps({"cases": [], "next_page_token": ""}),
    )
    fixture = {"target_case_number": 7, "public": {"detection_id": "target"}}
    try:
        asyncio.run(cases.reference(fixture, SimpleNamespace(agent="candidate-container")))
    except ControlError as error:
        assert "exactly one case" in str(error)
    else:
        raise AssertionError("reference bypassed native discovery with trusted case number")
