"""Bounded verifier for the search export scenario."""

from __future__ import annotations

import json
import posixpath
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from .base import assertion, evidence_refs, merge_evidence, summarize_ids

DEFAULT_MAX_BYTES = 100 * 1024 * 1024
DEFAULT_MAX_ROWS = 25_000
REQUIRED_PATH = "/work/export.jsonl"
REQUIRED_FIELDS = ("eval_event_id", "environment", "message")


def _artifact(frozen: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    if not isinstance(frozen, Mapping):
        return None
    candidate = frozen.get("export")
    if isinstance(candidate, Mapping):
        return candidate
    artifacts = frozen.get("artifacts")
    if isinstance(artifacts, Mapping):
        candidate = artifacts.get(REQUIRED_PATH, artifacts.get("export.jsonl"))
        if isinstance(candidate, Mapping):
            return candidate
        if isinstance(candidate, str):
            return {"path": REQUIRED_PATH, "content": candidate}
    if isinstance(artifacts, Sequence) and not isinstance(artifacts, (str, bytes)):
        for candidate in artifacts:
            if isinstance(candidate, Mapping) and candidate.get("path") == REQUIRED_PATH:
                return candidate
    if "path" in frozen and ("content" in frozen or "rows" in frozen):
        return frozen
    return None


def _safe_export_path(artifact: Mapping[str, Any]) -> tuple[bool, str]:
    path = artifact.get("path")
    if not isinstance(path, str):
        return False, "missing path"
    normalized = posixpath.normpath(path)
    if path != REQUIRED_PATH or normalized != REQUIRED_PATH:
        return False, f"expected {REQUIRED_PATH}"
    if artifact.get("symlink") or artifact.get("kind") in {"symlink", "device", "fifo", "socket"}:
        return False, "artifact is not a regular frozen file"
    if artifact.get("within_workspace") is False:
        return False, "collector marked the path outside the workspace"
    return True, "safe regular workspace artifact"


def _expected_rows(facts: Mapping[str, Any]) -> dict[str, dict[str, Any]] | None:
    value = facts.get("expected_rows", facts.get("expected"))
    if isinstance(value, Mapping):
        result = {}
        for event_id, row in value.items():
            if not isinstance(row, Mapping):
                return None
            normalized = {field: row.get(field) for field in REQUIRED_FIELDS}
            normalized["eval_event_id"] = normalized["eval_event_id"] or str(event_id)
            result[str(event_id)] = normalized
        return result
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        result = {}
        for row in value:
            if not isinstance(row, Mapping) or not isinstance(row.get("eval_event_id"), str):
                return None
            result[row["eval_event_id"]] = {field: row.get(field) for field in REQUIRED_FIELDS}
        return result
    ids = facts.get("expected_ids")
    values = facts.get("expected_values")
    if isinstance(ids, Sequence) and not isinstance(ids, (str, bytes)):
        result = {}
        for event_id in ids:
            event_id = str(event_id)
            row = values.get(event_id, {}) if isinstance(values, Mapping) else {}
            result[event_id] = {
                "eval_event_id": event_id,
                "environment": row.get("environment", "production") if isinstance(row, Mapping) else "production",
                "message": row.get("message") if isinstance(row, Mapping) else None,
            }
        return result
    return None


def _parse_rows(artifact: Mapping[str, Any], max_bytes: int, max_rows: int) -> tuple[list[dict[str, Any]] | None, str | None, int]:
    if isinstance(artifact.get("rows"), Sequence) and not isinstance(artifact.get("rows"), (str, bytes)):
        raw_rows = artifact["rows"]
        if len(raw_rows) > max_rows:
            return None, f"row limit exceeded ({max_rows})", 0
        rows = []
        for index, row in enumerate(raw_rows, 1):
            if not isinstance(row, Mapping):
                return None, f"row {index} is not an object", 0
            rows.append(dict(row))
        encoded_size = len(json.dumps(rows, separators=(",", ":")).encode("utf-8"))
        if encoded_size > max_bytes:
            return None, f"byte limit exceeded ({max_bytes})", encoded_size
        return rows, None, encoded_size
    content = artifact.get("content")
    if isinstance(content, bytes):
        raw = content
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            return None, "file is not UTF-8", len(raw)
    elif isinstance(content, str):
        text = content
        raw = content.encode("utf-8")
    else:
        return None, "frozen file content is missing", 0
    if len(raw) > max_bytes:
        return None, f"byte limit exceeded ({max_bytes})", len(raw)
    lines = text.splitlines()
    if len(lines) > max_rows:
        return None, f"row limit exceeded ({max_rows})", len(raw)
    rows = []
    for index, line in enumerate(lines, 1):
        if not line.strip():
            return None, f"line {index} is empty", len(raw)
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            return None, f"line {index} is invalid JSON: {exc.msg}", len(raw)
        if not isinstance(row, dict):
            return None, f"line {index} is not a JSON object", len(raw)
        rows.append(row)
    return rows, None, len(raw)


def verify_export(
    manifest: Mapping[str, Any] | None,
    fixture_handle: Mapping[str, Any] | None,
    frozen_artifacts: Mapping[str, Any] | None,
    evidence: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    facts = merge_evidence(fixture_handle, evidence)
    expected = _expected_rows(facts)
    artifact = _artifact(frozen_artifacts)
    refs = evidence_refs(artifact, "artifact:/work/export.jsonl")
    assertions: list[dict[str, Any]] = []

    if artifact is None:
        assertions.append(assertion(
            "export.safe_file", "fail", expected=REQUIRED_PATH, observed=None,
            evidence=refs, explanation="The required frozen export artifact is missing.",
        ))
        parse_rows, parse_error, byte_count = None, "artifact missing", 0
    else:
        safe, path_detail = _safe_export_path(artifact)
        assertions.append(assertion(
            "export.safe_file", "pass" if safe else "fail", expected=REQUIRED_PATH,
            observed={"path": artifact.get("path"), "detail": path_detail}, evidence=refs,
            explanation="The export is a regular file at the required workspace path." if safe else "The export path or file type is unsafe.",
        ))
        max_bytes = int(facts.get("max_export_bytes", DEFAULT_MAX_BYTES))
        max_rows = int(facts.get("max_export_rows", DEFAULT_MAX_ROWS))
        parse_rows, parse_error, byte_count = _parse_rows(artifact, max_bytes, max_rows)

    assertions.append(assertion(
        "export.valid_bounded_jsonl", "pass" if parse_rows is not None else "fail",
        expected={"format": "jsonl", "max_bytes": int(facts.get("max_export_bytes", DEFAULT_MAX_BYTES)), "max_rows": int(facts.get("max_export_rows", DEFAULT_MAX_ROWS))},
        observed={"bytes": byte_count, "rows": len(parse_rows) if parse_rows is not None else None, "error": parse_error},
        evidence=refs,
        explanation="The artifact is bounded JSONL containing one object per non-empty line." if parse_rows is not None else f"The artifact cannot be graded as bounded JSONL: {parse_error}.",
    ))

    mutations = facts.get("platform_mutations")
    platform_before = facts.get("platform_state_before")
    platform_after = facts.get("platform_state_after")
    if isinstance(mutations, Sequence) and not isinstance(mutations, (str, bytes)):
        unchanged = len(mutations) == 0
        platform_status = "pass" if unchanged else "fail"
        platform_observed: Any = {"mutations": list(mutations)}
    elif platform_before is not None and platform_after is not None:
        unchanged = platform_before == platform_after
        platform_status = "pass" if unchanged else "fail"
        platform_observed = {"before": platform_before, "after": platform_after}
    else:
        platform_status = "unknown"
        platform_observed = None
    assertions.append(assertion(
        "export.platform_unchanged", platform_status, expected={"mutations": []},
        observed=platform_observed, evidence=evidence_refs(evidence, "evidence:platform-state"),
        explanation=(
            "No platform mutation was observed."
            if platform_status == "pass" else "A platform mutation was observed."
            if platform_status == "fail" else "Frozen platform-preservation evidence is missing."
        ),
    ))

    if expected is None:
        for assertion_id, expectation in (
            ("export.membership", "exact expected event ID set"),
            ("export.values", "exact projected field values"),
            ("export.unique_ids", "one row per event ID"),
            ("export.count", "expected row count"),
        ):
            assertions.append(assertion(assertion_id, "unknown", expected=expectation, observed=None, evidence=refs, explanation="The frozen ground truth is missing."))
        return assertions

    if parse_rows is None:
        for assertion_id, expectation in (
            ("export.membership", summarize_ids(set(expected))),
            ("export.values", "exact projected field values"),
            ("export.unique_ids", True),
            ("export.count", len(expected)),
        ):
            assertions.append(assertion(assertion_id, "fail", expected=expectation, observed=None, evidence=refs, explanation="The export rows are unavailable because the artifact is missing or invalid."))
        return assertions

    ids = [row.get("eval_event_id") for row in parse_rows]
    string_ids = [event_id for event_id in ids if isinstance(event_id, str)]
    observed_ids = set(string_ids)
    expected_ids = set(expected)
    invalid_id_rows = len(ids) - len(string_ids)
    same_membership = observed_ids == expected_ids and invalid_id_rows == 0
    assertions.append(assertion(
        "export.membership", "pass" if same_membership else "fail",
        expected=summarize_ids(expected_ids),
        observed={
            **summarize_ids(observed_ids),
            "missing": summarize_ids(expected_ids - observed_ids),
            "extra": summarize_ids(observed_ids - expected_ids),
            "invalid_id_rows": invalid_id_rows,
        },
        evidence=refs,
        explanation="The exported event identity set is exact." if same_membership else "The export has missing, extra, or invalid event identities.",
    ))
    duplicates = sorted(event_id for event_id, count in Counter(string_ids).items() if count > 1)
    assertions.append(assertion(
        "export.unique_ids", "pass" if not duplicates else "fail", expected={"duplicates": []},
        observed={"duplicates": duplicates, "duplicate_count": len(string_ids) - len(set(string_ids))}, evidence=refs,
        explanation="Each event ID appears once." if not duplicates else "One or more event IDs appear more than once.",
    ))
    wrong_values: list[dict[str, Any]] = []
    for index, row in enumerate(parse_rows, 1):
        event_id = row.get("eval_event_id")
        if not isinstance(event_id, str) or event_id not in expected:
            continue
        projected = {field: row.get(field) for field in REQUIRED_FIELDS}
        extra_fields = sorted(set(row) - set(REQUIRED_FIELDS))
        if projected != expected[event_id] or extra_fields:
            wrong_values.append({"line": index, "eval_event_id": event_id, "extra_fields": extra_fields})
    assertions.append(assertion(
        "export.values", "pass" if not wrong_values else "fail",
        expected={"fields": list(REQUIRED_FIELDS), "mismatches": 0},
        observed={"mismatches": len(wrong_values), "examples": wrong_values[:20]}, evidence=refs,
        explanation="Every matching row has exactly the requested field values." if not wrong_values else "Some exported rows have incorrect values or unrequested fields.",
    ))
    count_ok = len(parse_rows) == len(expected)
    assertions.append(assertion(
        "export.count", "pass" if count_ok else "fail", expected=len(expected), observed=len(parse_rows), evidence=refs,
        explanation="The export row count is correct." if count_ok else "The export row count differs from ground truth.",
    ))
    return assertions


class ExportVerifier:
    def verify(self, manifest: Mapping[str, Any], fixture_handle: Mapping[str, Any], frozen_artifacts: Mapping[str, Any], evidence: Mapping[str, Any]) -> list[dict[str, Any]]:
        return verify_export(manifest, fixture_handle, frozen_artifacts, evidence)
