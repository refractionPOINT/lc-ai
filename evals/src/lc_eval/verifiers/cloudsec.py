"""Deterministic verifier for Cloud Security export and prescribed triage."""

from __future__ import annotations

import csv
import io
from collections.abc import Mapping
from typing import Any

from .base import assertion, evidence_refs, merge_evidence, summarize_ids

PATH = "/work/cloudsec-findings.csv"
REQUIRED_COLUMNS = {"finding_id", "severity", "status", "owner", "title", "finding_class", "rule_id"}
VALUE_COLUMNS = ("severity", "status", "owner", "title", "finding_class", "rule_id")


def _artifact(frozen: Mapping[str, Any] | None):
    if not isinstance(frozen, Mapping):
        return None
    files = frozen.get("files")
    if isinstance(files, Mapping) and isinstance(files.get(PATH), Mapping):
        return files[PATH]
    value = frozen.get("cloudsec_findings")
    return value if isinstance(value, Mapping) else None


def _parse(artifact):
    if not isinstance(artifact, Mapping) or not isinstance(artifact.get("content"), str):
        return None, "frozen file content is missing"
    try:
        reader = csv.DictReader(io.StringIO(artifact["content"]))
        if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
            return None, "CSV header is missing or duplicated"
        if not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            return None, "CSV header omits required native columns"
        rows = list(reader)
    except (csv.Error, UnicodeError) as error:
        return None, str(error)
    if any(None in row for row in rows):
        return None, "CSV row has more cells than the header"
    if any(row.get("finding_id", "").startswith("#") for row in rows):
        return None, "server marked the export truncated"
    return rows, None


def verify_cloudsec(manifest, fixture_handle, frozen_artifacts, evidence):
    del manifest
    facts = merge_evidence(fixture_handle, evidence)
    artifact = _artifact(frozen_artifacts)
    refs = evidence_refs(artifact, f"artifact:{PATH}")
    safe = bool(artifact and artifact.get("path") == PATH and artifact.get("within_workspace") is not False and artifact.get("kind") not in {"symlink", "device", "fifo", "socket"})
    out = [assertion("cloudsec.export.safe_file", "pass" if safe else "fail", expected=PATH, observed=artifact.get("path") if artifact else None, evidence=refs, explanation="The required frozen CSV is a safe workspace file." if safe else "The required safe CSV artifact is missing.")]
    rows, error = _parse(artifact)
    out.append(assertion("cloudsec.export.valid_csv", "pass" if rows is not None else "fail", expected={"format": "native Cloud Security CSV", "truncated": False}, observed={"rows": len(rows) if rows is not None else None, "error": error}, evidence=refs, explanation="The native CSV is complete and parseable." if rows is not None else f"The CSV is invalid: {error}."))
    expected = facts.get("expected_export")
    if not isinstance(expected, Mapping):
        export_status = "unknown"
        expected_ids: set[str] = set()
    else:
        export_status = "pass" if rows is not None else "fail"
        expected_ids = {str(x) for x in expected}
    observed_ids = [row.get("finding_id") for row in rows or []]
    observed_set = {x for x in observed_ids if isinstance(x, str) and x}
    exact = export_status == "pass" and observed_set == expected_ids and len(observed_ids) == len(observed_set)
    out.append(assertion("cloudsec.export.membership", "unknown" if export_status == "unknown" else "pass" if exact else "fail", expected=summarize_ids(expected_ids), observed={**summarize_ids(observed_set), "row_count": len(observed_ids), "missing": sorted(expected_ids-observed_set), "extra": sorted(observed_set-expected_ids)}, evidence=refs, explanation="The export contains every and only fixture finding once." if exact else "The export membership is incomplete, duplicated, or contains extras."))
    mismatches = []
    if rows is not None and isinstance(expected, Mapping):
        for row in rows:
            fid = row.get("finding_id")
            baseline = expected.get(fid)
            if not isinstance(baseline, Mapping):
                continue
            for column in VALUE_COLUMNS:
                want = str(baseline.get(column, ""))
                if row.get(column, "") != want:
                    mismatches.append({"finding_id": fid, "column": column})
    values_status = "unknown" if not isinstance(expected, Mapping) else "pass" if rows is not None and not mismatches else "fail"
    out.append(assertion("cloudsec.export.values", values_status, expected={"columns": list(VALUE_COLUMNS), "mismatches": 0}, observed={"mismatches": len(mismatches), "examples": mismatches[:20]}, evidence=refs, explanation="Exported immutable and pre-triage values match backend truth." if values_status == "pass" else "Export values differ from backend truth."))

    baseline, after = facts.get("baseline_findings"), facts.get("findings_after")
    targets = set(facts.get("target_ids", ()))
    complete = facts.get("collection_complete") is True and isinstance(baseline, Mapping) and isinstance(after, Mapping)
    owner_bad, status_bad, resolution_bad, preserved_bad = [], [], [], []
    if complete:
        for fid, before in baseline.items():
            current = after.get(fid)
            if not isinstance(current, Mapping):
                preserved_bad.append(fid)
                continue
            if fid in targets:
                if current.get("owner") != facts.get("target_owner"):
                    owner_bad.append(fid)
                if current.get("status") != "accepted":
                    status_bad.append(fid)
                if current.get("resolution") != "accepted":
                    resolution_bad.append(fid)
            else:
                for field in ("status", "resolution", "owner", "ticket"):
                    if current.get(field, "") != before.get(field, ""):
                        preserved_bad.append(fid)
                        break
    def mutation(assertion_id, bad, expected_value, explanation):
        status = "unknown" if not complete else "pass" if not bad else "fail"
        return assertion(assertion_id, status, expected=expected_value, observed={"wrong_ids": sorted(set(bad))} if complete else None, evidence=evidence_refs(evidence, "evidence:cloudsec-findings"), explanation=explanation if status == "pass" else "Independent post-run finding evidence is missing or differs.")
    out.extend([
        mutation("cloudsec.targets.owner", owner_bad, facts.get("target_owner"), "Every specified target has the requested owner."),
        mutation("cloudsec.targets.status", status_bad, "accepted", "Every specified target is accepted."),
        mutation("cloudsec.targets.resolution", resolution_bad, "accepted", "Every specified target carries the accepted disposition."),
        mutation("cloudsec.nontargets.preserved", preserved_bad, {"changed": []}, "All non-target triage fields are preserved."),
    ])
    policy_before, policy_after = facts.get("policy_before"), facts.get("policy_after")
    policy_status = "unknown" if policy_before is None or policy_after is None else "pass" if policy_before == policy_after else "fail"
    out.append(assertion("cloudsec.policy.preserved", policy_status, expected=policy_before, observed=policy_after, evidence=evidence_refs(evidence, "evidence:cloudsec-policy"), explanation="Cloud Security policy state is unchanged." if policy_status == "pass" else "Policy evidence is missing or changed."))
    ready = facts.get("readiness")
    readiness_ok = isinstance(ready, Mapping) and ready.get("main") == 7 and ready.get("distractors") == 3
    out.append(assertion("cloudsec.readiness", "pass" if readiness_ok else "unknown", expected={"main": 7, "distractors": 3}, observed=ready, evidence=["fixture:cloudsec-readiness"], explanation="The real backend materialized the exact SARIF fixture and distractors." if readiness_ok else "Exact real-backend readiness evidence is unavailable."))
    return out


verify = verify_cloudsec
