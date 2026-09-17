"""Real Cloud Security SARIF fixture and independent post-run collection."""

from __future__ import annotations

import asyncio
import hashlib
import time
from copy import deepcopy
from typing import Any

from ..config import atomic_json
from .hive import set_record, snapshot
from .local_cli import ControlError
from ..execution.broker import CommandSpec

EXTENSION = "ext-cloud-security"
POLICY_HIVE = "cloudsec_policy"
EXPORT_PATH = "/work/cloudsec-findings.csv"

PERMISSIONS = ["org.get", "cloudsec.get", "cloudsec.set"]
COMMANDS = {
    ("cloudsec", "export", "findings"): CommandSpec(
        value_options=frozenset({"--repo", "--source", "--status"}),
        fixed_values=(("--source", frozenset({"ingest"})), ("--status", frozenset({"open"}))),
        max_positionals=0,
    ),
    ("cloudsec", "finding", "list"): CommandSpec(
        value_options=frozenset({"--severity", "--class", "--status", "--repo", "--source", "--owner", "--sla", "--sort", "--order", "--cursor", "--limit", "-q"}),
        flag_options=frozenset({"--unassigned", "--reachable", "--no-reachable", "--kev", "--no-kev"}),
        max_positionals=0,
    ),
    ("cloudsec", "finding", "get"): CommandSpec(max_positionals=1),
    ("cloudsec", "finding", "set-owner"): CommandSpec(
        value_options=frozenset({"--owner"}), max_positionals=1,
    ),
    ("cloudsec", "finding", "resolve"): CommandSpec(
        value_options=frozenset({"--kind", "--reason"}),
        fixed_values=(("--kind", frozenset({"accepted"})),), max_positionals=1,
    ),
}


class CloudSecUnsupportedError(RuntimeError):
    """The selected backend cannot prove pushed-result findings support."""


def _sarif(trial: str, count: int) -> dict[str, Any]:
    rules, results = [], []
    for index in range(count):
        rule = f"LC-EVAL-SAST-{index:02d}"
        title = f"LC eval {trial} deterministic weakness {index:02d}"
        rules.append({
            "id": rule,
            "name": "code-weakness",
            "shortDescription": {"text": title},
            "properties": {"tags": ["security", "sast", "CWE-20"], "security-severity": 8.1},
        })
        results.append({
            "ruleId": rule,
            "level": "error",
            "message": {"text": title},
            "locations": [{"physicalLocation": {"artifactLocation": {"uri": f"src/eval_{index:02d}.go"}, "region": {"startLine": index + 10, "snippet": {"text": f"evalMarker{index:02d}(input)"}}}}],
            "properties": {"severity": "HIGH", "precision": "high", "cwe": "CWE-20"},
        })
    return {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "lc-eval-sarif", "version": "1.0", "rules": rules}}, "results": results}]}


def _cloudsec(cli, oid: str, method: str, path: str, **kwargs):
    return cli.api(oid, method, f"cloudsec/{oid}/{path}", **kwargs)


def list_all_findings(cli, oid: str, *, repo: str, source: str = "ingest") -> list[dict[str, Any]]:
    rows, cursor = [], None
    seen = set()
    while True:
        params: list[tuple[str, str]] = [("repo", repo), ("source", source), ("limit", "1000")]
        if cursor:
            params.append(("cursor", cursor))
        value = _cloudsec(cli, oid, "GET", "findings", params=params)
        if not isinstance(value, dict) or not isinstance(value.get("findings"), list):
            raise CloudSecUnsupportedError("Cloud Security findings response has an unsupported shape")
        rows.extend(dict(row) for row in value["findings"] if isinstance(row, dict))
        nxt = value.get("next_cursor")
        if not nxt:
            return rows
        if not isinstance(nxt, str) or nxt in seen:
            raise CloudSecUnsupportedError("Cloud Security findings cursor did not advance")
        seen.add(nxt)
        cursor = nxt


def _finding_id(row: dict[str, Any]) -> str | None:
    value = row.get("finding_id", row.get("id"))
    return value if isinstance(value, str) and value else None


def _state(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {fid: deepcopy(row) for row in rows if (fid := _finding_id(row)) is not None}


def _subscribe(cli, oid: str) -> None:
    try:
        cli.invoke(["extension", "subscribe", "--name", EXTENSION], oid)
    except ControlError:
        # Existing subscriptions commonly report a conflict. Prove access below;
        # never treat this swallowed result as readiness.
        pass


def _ingest(cli, oid: str, repo: str, document: dict[str, Any], commit: str) -> dict[str, Any]:
    value = _cloudsec(cli, oid, "POST", "code/ingest", body={
        "repo": repo, "source": "sarif", "document": document,
        "commit": commit, "ref": "refs/heads/main", "default_branch": "main", "provider": "github",
    }, timeout=90)
    if not isinstance(value, dict):
        raise CloudSecUnsupportedError("SARIF ingest returned an unsupported shape")
    return value


def provision(config, cli, journal, trial_id, oid, seed, root):
    del journal
    suffix = hashlib.sha256(f"{trial_id}:{seed}".encode()).hexdigest()[:12]
    repo = f"lc-eval/cloudsec-{suffix}"
    distractor_repo = f"lc-eval/cloudsec-distractor-{suffix}"
    policy_name = f"eval-code-{suffix}"
    _subscribe(cli, oid)
    policy = {"data": {"policy_type": "code_scanning", "code_scanning": {"enabled": True, "repos": {"include": [repo, distractor_repo]}, "scanners": {"sast": True}, "severity_floor": "INFO", "schedule": "manual"}}, "usr_mtd": {"enabled": True, "tags": ["eval", trial_id]}}
    set_record(cli, oid, POLICY_HIVE, policy_name, policy)
    policy_before = snapshot(cli, oid, POLICY_HIVE)
    atomic_json(root / "cloudsec-sarif.json", _sarif(trial_id, 7))
    ingest = _ingest(cli, oid, repo, _sarif(trial_id, 7), f"eval-{suffix}-main")
    distractor_ingest = _ingest(cli, oid, distractor_repo, _sarif(f"{trial_id}-distractor", 3), f"eval-{suffix}-distractor")
    deadline = time.monotonic() + min(180, config.limits.verification_seconds)
    rows: list[dict[str, Any]] = []
    while time.monotonic() < deadline:
        try:
            rows = list_all_findings(cli, oid, repo=repo)
            distractors = list_all_findings(cli, oid, repo=distractor_repo)
        except (ControlError, CloudSecUnsupportedError):
            rows, distractors = [], []
        if len(rows) == 7 and len(distractors) == 3 and all(_finding_id(row) for row in rows + distractors):
            break
        time.sleep(3)
    else:
        raise CloudSecUnsupportedError(f"SARIF ingest was accepted but exact findings did not materialize (main={len(rows)}, distractor={len(distractors)})")
    baseline = _state(rows + distractors)
    ordered = sorted(_state(rows))
    targets = ordered[1:4]
    owner = f"appsec-eval-{suffix}@example.invalid"
    reason = f"eval-authorized-{suffix}"
    return {
        "expected_export": _state(rows), "baseline_findings": baseline,
        "target_ids": targets, "target_owner": owner, "acceptance_reason": reason,
        "policy_before": policy_before, "policy_name": policy_name,
        "readiness": {"main": len(rows), "distractors": len(distractors), "ingest": ingest, "distractor_ingest": distractor_ingest},
        "bad_variant": int(seed) % 3,
        "cli_notice": "Cloud Security finding list/get, full-set findings export, owner assignment, and accepted disposition are permitted. Write the CSV with shell redirection: limacharlie cloudsec export findings ... > /work/cloudsec-findings.csv. The export command's file-output option is unavailable through the controlled transport.",
        "public": {"organization_id": oid, "repository": repo, "target_owner": owner, "acceptance_reason": reason, "target_finding_ids": "\n".join(f"- `{fid}`" for fid in targets)},
    }


def collect(config, cli, oid, fixture, root):
    del root
    repos = {row.get("repo_name") for row in fixture["baseline_findings"].values() if row.get("repo_name")}
    # Repo names are not guaranteed in every API projection, so query both public
    # fixture repo and the complete target baseline by individual IDs.
    after = {}
    deadline = time.monotonic() + min(180, config.limits.verification_seconds)
    while time.monotonic() < deadline:
        after = {}
        for fid in fixture["baseline_findings"]:
            try:
                value = _cloudsec(cli, oid, "GET", f"findings/{fid}")
            except ControlError:
                continue
            row = value.get("finding") if isinstance(value, dict) else None
            if isinstance(row, dict):
                after[fid] = row
        if len(after) == len(fixture["baseline_findings"]):
            targets_ready = all(
                after[fid].get("owner") == fixture["target_owner"]
                and after[fid].get("status") == "accepted"
                and after[fid].get("resolution") == "accepted"
                for fid in fixture["target_ids"]
            )
            if targets_ready:
                break
        time.sleep(2)
    return {"findings_after": after, "policy_after": snapshot(cli, oid, POLICY_HIVE), "collection_complete": len(after) == len(fixture["baseline_findings"]), "queried_repos": sorted(str(x) for x in repos)}


async def reference(fixture, env, bad=False):
    from ..execution.docker import run
    public = fixture["public"]
    output = env.work / "cloudsec-findings.csv"
    raw = await asyncio.to_thread(run, ["docker", "exec", env.agent, "limacharlie", "cloudsec", "export", "findings", "--repo", public["repository"], "--source", "ingest", "--status", "open"], timeout=300)
    output.write_text(raw)
    targets = list(fixture["target_ids"])
    variant = fixture.get("bad_variant", 0)
    if bad and variant == 0:
        lines = output.read_text().splitlines(keepends=True)
        output.write_text("".join(lines[:-1]))
    changed = targets[:-1] if bad and variant == 1 else targets
    if bad and variant == 2:
        changed = targets + [next(fid for fid in fixture["baseline_findings"] if fid not in targets)]
    for fid in changed:
        await asyncio.to_thread(run, ["docker", "exec", env.agent, "limacharlie", "cloudsec", "finding", "set-owner", fid, "--owner", public["target_owner"]], timeout=90)
        await asyncio.to_thread(run, ["docker", "exec", env.agent, "limacharlie", "cloudsec", "finding", "resolve", fid, "--kind", "accepted", "--reason", public["acceptance_reason"]], timeout=90)
    return f"Exported Cloud Security findings and changed {len(changed)} IDs"
