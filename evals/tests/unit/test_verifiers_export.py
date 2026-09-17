import json

from lc_eval.verifiers.export import verify_export


def _row(event_id, message=None):
    return {"eval_event_id": event_id, "environment": "production", "message": message or event_id}


def _content(*rows):
    return "\n".join(json.dumps(row) for row in rows) + "\n"


def test_export_accepts_exact_bounded_jsonl():
    expected = {"a": _row("a"), "b": _row("b")}
    results = verify_export({}, {"expected_rows": expected}, {"export": {"path": "/work/export.jsonl", "content": _content(*expected.values()), "kind": "file"}}, {"platform_mutations": []})
    assert all(result["status"] == "pass" for result in results)


def test_export_rejects_traversal_duplicate_and_wrong_value():
    expected = {"a": _row("a"), "b": _row("b")}
    rows = [_row("a"), _row("a"), _row("b", "fabricated")]
    results = verify_export({}, {"expected_rows": expected}, {"export": {"path": "/work/elsewhere/../export.jsonl", "content": _content(*rows)}}, {})
    statuses = {result["id"]: result["status"] for result in results}
    assert statuses["export.safe_file"] == "fail"
    assert statuses["export.unique_ids"] == "fail"
    assert statuses["export.values"] == "fail"
    assert statuses["export.count"] == "fail"


def test_export_rejects_extra_fields_and_enforces_bounds():
    row = {**_row("a"), "secret": "unexpected"}
    results = verify_export({}, {"expected_rows": {"a": _row("a")}, "max_export_bytes": 10}, {"export": {"path": "/work/export.jsonl", "content": _content(row)}}, {})
    assert {item["id"]: item["status"] for item in results}["export.valid_bounded_jsonl"] == "fail"
