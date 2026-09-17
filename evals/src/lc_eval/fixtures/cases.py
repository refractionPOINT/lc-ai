"""Bounded case-lifecycle fixture with independent cases API readback."""

from __future__ import annotations

import asyncio
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time
from typing import Any, Mapping
import uuid

from ..execution.broker import CommandSpec
from .local_cli import ControlError, decode_json


SCENARIO = "case-maintain-records"
EXTENSION = "ext-cases"
VARIANTS = ("clean", "partial", "distractor")
PERMISSIONS = [
    "org.get",
    "investigation.get",
    "investigation.set",
    "ext.request",
]
COMMANDS = {
    ("case", "create"): CommandSpec(
        value_options=frozenset({"--detection", "--severity", "--summary"}),
        fixed_values=(("--severity", frozenset({"critical", "high", "medium", "low", "info"})),),
    ),
    ("case", "list"): CommandSpec(value_options=frozenset({
        "--status", "--severity", "--classification", "--assignee", "--search", "--sid",
        "--tag", "--sort", "--order", "--limit", "--cursor",
    })),
    ("case", "get"): CommandSpec(value_options=frozenset({"--case-number"})),
    ("case", "update"): CommandSpec(value_options=frozenset({
        "--case-number", "--status", "--severity", "--assignees", "--classification",
        "--summary", "--conclusion", "--tag",
    })),
    ("case", "add-note"): CommandSpec(
        value_options=frozenset({"--case-number", "--content", "--input-file", "--type"}),
        flag_options=frozenset({"--is-public", "--no-is-public"}),
        path_options=frozenset({"--input-file"}),
    ),
    ("case", "detection", "list"): CommandSpec(value_options=frozenset({"--case"})),
    ("case", "entity", "list"): CommandSpec(value_options=frozenset({"--case"})),
    ("case", "entity", "add"): CommandSpec(
        value_options=frozenset({"--case", "--type", "--value", "--note", "--verdict"}),
    ),
}
CLI_NOTICE = """\
This scenario permits case create/list/get/update/add-note, case detection list,
and case entity list/add. Find a reusable case through case list and confirm its
linked detection with case detection list before mutating it. Organization scope
and authentication are already supplied.
"""

# ext-cases caches its subscribed-tenant inventory for five minutes. Tenant
# creation does not invalidate that cache, so every service instance must be
# allowed to age out a pre-subscription snapshot before list visibility proves
# candidate readiness.
SUBSCRIBED_CACHE_TTL_SECONDS = 300.0
SUBSCRIBED_CACHE_MARGIN_SECONDS = 15.0


class CaseCreateUnsupportedError(RuntimeError):
    """The pinned native case create command cannot encode detections."""


def _root(cli: Any, oid: str) -> str:
    value = cli.get_urls(oid).get("cases", "https://cases.limacharlie.io")
    if not value.startswith(("http://", "https://")):
        value = "https://" + value
    return value.rstrip("/") + "/api/v1"


def _api(cli: Any, oid: str, method: str, path: str, *, body: Any = None, params: Any = None) -> Any:
    query = {"oid": oid}
    if params:
        query.update(params)
    return cli.api(oid, method, path, root=_root(cli, oid), body=body, params=query)


def _wait_ready(cli: Any, oid: str, timeout_seconds: float, retry_seconds: float = 2.0) -> dict[str, Any]:
    """Wait until the extension subscription callback has created its tenant."""
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            value = _api(cli, oid, "GET", f"config/{oid}")
            if isinstance(value, Mapping) and isinstance(value.get("severity_mapping"), Mapping):
                return dict(value)
            last_error = ControlError("cases configuration readiness response is invalid")
        except ControlError as error:
            if error.status_code not in {404, 429, 500, 502, 503, 504}:
                raise
            last_error = error
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(retry_seconds, remaining))
    raise ControlError(f"cases extension did not become ready: {last_error}")


def _create(cli: Any, oid: str, detection: Mapping[str, Any], summary: str, severity: str) -> int:
    data = {
        "detection": json.dumps(detection, separators=(",", ":")),
        "severity": severity,
        "summary": summary,
    }
    raw = cli.invoke(
        ["extension", "request", "--name", EXTENSION, "--action", "create_case",
         "--data", json.dumps(data, separators=(",", ":"))],
        oid,
    )
    if isinstance(raw, Mapping) and isinstance(raw.get("data"), Mapping):
        raw = raw["data"]
    number = raw.get("case_number") if isinstance(raw, Mapping) else None
    if not isinstance(number, int):
        raise ControlError("case creation returned no case number")
    return number


def _case(cli: Any, oid: str, number: int) -> dict[str, Any]:
    value = _api(cli, oid, "GET", f"cases/{number}")
    if not isinstance(value, Mapping):
        raise ControlError("case read returned an invalid object")
    return deepcopy(dict(value))


def _component(cli: Any, oid: str, number: int, name: str) -> list[dict[str, Any]]:
    value = _api(cli, oid, "GET", f"cases/{number}/{name}")
    rows = value.get(name) if isinstance(value, Mapping) else None
    if not isinstance(rows, list) or not all(isinstance(row, Mapping) for row in rows):
        raise ControlError(f"case {name} read returned an invalid collection")
    return [deepcopy(dict(row)) for row in rows]


def snapshot_case(cli: Any, oid: str, number: int) -> dict[str, Any]:
    case = _case(cli, oid, number)
    return {
        "case": case.get("case", case),
        "events": deepcopy(case.get("events", [])),
        "detections": _component(cli, oid, number, "detections"),
        "entities": _component(cli, oid, number, "entities"),
    }


def _list_cases(cli: Any, oid: str, search: str | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    token: str | None = None
    for _ in range(20):
        params = {"oids": oid, "page_size": "200"}
        if search:
            params["search"] = search
        if token:
            params["page_token"] = token
        value = cli.api(oid, "GET", "cases", root=_root(cli, oid), params=params)
        page = value.get("cases") if isinstance(value, Mapping) else None
        if not isinstance(page, list):
            raise ControlError("case listing returned an invalid collection")
        rows.extend(deepcopy(dict(row)) for row in page if isinstance(row, Mapping))
        token = value.get("next_page_token") or value.get("page_token")
        if not isinstance(token, str) or not token:
            return rows
    raise ControlError("case listing exceeded the fixture pagination bound")


def _wait_list_ready(
    cli: Any,
    oid: str,
    expected: Mapping[int, str],
    tenant_ready_at: float,
    timeout_seconds: float,
    retry_seconds: float = 5.0,
) -> None:
    """Prove all seeded cases are listable after every stale tenant cache expires."""
    deadline = tenant_ready_at + timeout_seconds
    safe_after = tenant_ready_at + SUBSCRIBED_CACHE_TTL_SECONDS + SUBSCRIBED_CACHE_MARGIN_SECONDS
    last_detail = "not observed"
    while time.monotonic() < deadline:
        try:
            rows = _list_cases(cli, oid)
            listed = {
                row.get("case_number") for row in rows
                if isinstance(row.get("case_number"), int)
            }
            missing = set(expected) - listed
            wrong = []
            if not missing:
                for number, detect_id in expected.items():
                    detections = _component(cli, oid, number, "detections")
                    if sum(row.get("detect_id") == detect_id for row in detections) != 1:
                        wrong.append(number)
            last_detail = f"missing={sorted(missing)}, wrong_detections={sorted(wrong)}"
            if not missing and not wrong and time.monotonic() >= safe_after:
                return
        except ControlError as error:
            if error.status_code not in {404, 429, 500, 502, 503, 504}:
                raise
            last_detail = str(error)
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(retry_seconds, remaining))
    raise ControlError(f"seeded cases did not become safely list-visible: {last_detail}")


def _notes(snapshot: Mapping[str, Any]) -> list[dict[str, Any]]:
    events = snapshot.get("events", [])
    return [dict(event) for event in events if isinstance(event, Mapping) and event.get("event_type") == "case_note_added"]


def provision(config: Any, cli: Any, journal: Any, trial_id: str, oid: str, seed: int, root: Path) -> dict[str, Any]:
    """Subscribe the disposable org and seed one of three deterministic states."""
    del journal, root
    variant = VARIANTS[seed % len(VARIANTS)]
    if variant == "clean":
        raise CaseCreateUnsupportedError(
            "clean case creation is unsupported by the pinned native CLI: "
            "case create cannot encode a detection for ext-cases"
        )
    if config.lc.readiness_seconds < 360:
        raise ValueError("Cases fixture requires lc.readiness_seconds >= 360 for tenant-cache readiness")
    cli.invoke(["extension", "subscribe", "--name", EXTENSION], oid)
    _wait_ready(cli, oid, min(180, config.limits.verification_seconds))
    tenant_ready_at = time.monotonic()
    suffix = hashlib.sha256(f"{trial_id}:{seed}".encode()).hexdigest()[:12]
    detection = {
        "detect_id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"lc-eval:{trial_id}:{seed}:detection")),
        "cat": f"eval-case-{suffix}",
        "source": "lc-eval",
        "routing": {
            "sid": str(uuid.uuid5(uuid.NAMESPACE_URL, f"lc-eval:{trial_id}:{seed}:sensor")),
            "hostname": f"eval-host-{suffix}",
        },
        "detect_mtd": {"level": "2"},
    }
    desired = {
        "status": "in_progress",
        "severity": "high",
        "entity": {
            "entity_type": "domain",
            "entity_value": f"indicator-{suffix}.example.test",
            "note": "Supplied investigation entity",
            "verdict": "suspicious",
        },
        "note": {
            "content": f"eval={suffix}; action=triage; disposition=continue-monitoring",
            "note_type": "analysis",
            "is_public": False,
        },
    }
    summary = f"Evaluation case {suffix}"
    target_number: int | None = None
    if variant != "clean":
        target_number = _create(cli, oid, detection, summary, "low")
        _api(cli, oid, "POST", f"cases/{target_number}/notes", body={
            "content": "Pre-existing analyst note; preserve exactly.", "note_type": "handoff", "is_public": False,
        })
        _api(cli, oid, "POST", f"cases/{target_number}/entities", body={
            "entity_type": "user", "entity_value": f"existing-{suffix}",
            "note": "Pre-existing entity", "verdict": "informational",
        })

    distractor_numbers = []
    expected_detections = {target_number: detection["detect_id"]}
    distractor_count = 3 if variant == "distractor" else 1
    for index in range(distractor_count):
        distractor_detection = {
            **detection,
            "detect_id": str(uuid.uuid5(
                uuid.NAMESPACE_URL, f"lc-eval:{trial_id}:{seed}:distractor:{index}"
            )),
            "cat": f"eval-case-{suffix}-similar-{index}",
            "routing": {**detection["routing"], "hostname": f"other-host-{suffix}-{index}"},
        }
        distractor_number = _create(
            cli, oid, distractor_detection, f"Unrelated evaluation case {suffix}-{index}", "medium"
        )
        distractor_numbers.append(distractor_number)
        expected_detections[distractor_number] = distractor_detection["detect_id"]
        _api(cli, oid, "POST", f"cases/{distractor_number}/notes", body={
            "content": f"Unrelated note {index}; preserve exactly.", "note_type": "general", "is_public": False,
        })
    _wait_list_ready(
        cli, oid, expected_detections, tenant_ready_at,
        float(config.lc.readiness_seconds),
    )
    baseline_target = snapshot_case(cli, oid, target_number) if target_number is not None else None
    baseline_distractors = {
        str(number): snapshot_case(cli, oid, number) for number in distractor_numbers
    }
    return {
        "variant": variant,
        "target_case_number": target_number,
        "distractor_case_numbers": distractor_numbers,
        "detection": detection,
        "desired": desired,
        "summary": summary,
        "baseline_target": baseline_target,
        "baseline_distractors": baseline_distractors,
        "cli_notice": CLI_NOTICE,
        "public": {
            "organization_id": oid,
            "detection_json": json.dumps(detection, sort_keys=True),
            "detection_id": detection["detect_id"],
            "case_summary": summary,
            "target_status": desired["status"],
            "target_severity": desired["severity"],
            "entity_type": desired["entity"]["entity_type"],
            "entity_value": desired["entity"]["entity_value"],
            "entity_note": desired["entity"]["note"],
            "entity_verdict": desired["entity"]["verdict"],
            "note_content": desired["note"]["content"],
            "note_type": desired["note"]["note_type"],
        },
    }


def collect(config: Any, cli: Any, oid: str, fixture: Mapping[str, Any], root: Path) -> dict[str, Any]:
    """Find the target by detection identity and freeze independent state."""
    del config, root
    detection = fixture["detection"]
    matches: list[dict[str, Any]] = []
    listed = _list_cases(cli, oid)
    candidate_numbers = {
        candidate.get("case_number") for candidate in listed
        if isinstance(candidate, Mapping) and isinstance(candidate.get("case_number"), int)
    }
    # The target number is trusted fixture identity. Include it even if a list
    # index is briefly stale, then use the detection collection as ground truth.
    target_number = fixture.get("target_case_number")
    if isinstance(target_number, int):
        candidate_numbers.add(target_number)
    for number in sorted(candidate_numbers):
        snap = snapshot_case(cli, oid, number)
        count = sum(item.get("detect_id") == detection["detect_id"] for item in snap["detections"])
        if count:
            matches.append({"case_number": number, "detection_count": count, "snapshot": snap})
    return {
        "target_matches": matches,
        "observed_distractors": {
            str(number): snapshot_case(cli, oid, number)
            for number in fixture["distractor_case_numbers"]
        },
        "evidence_refs": ["evidence:cases-after"],
    }


async def reference(fixture: Mapping[str, Any], env: Any, bad: bool = False) -> str:
    """Exercise the same brokered case CLI available to candidates."""
    from ..execution.docker import run

    public = fixture["public"]

    async def command(args: list[str]) -> Any:
        raw = await asyncio.to_thread(
            run, ["docker", "exec", env.agent, "limacharlie", "--output", "json", *args], timeout=120,
        )
        return decode_json(raw)

    matching_numbers: list[int] = []
    cursor: str | None = None
    for _ in range(20):
        args = ["case", "list", "--limit", "200"]
        if cursor:
            args += ["--cursor", cursor]
        listed = await command(args)
        if isinstance(listed, Mapping) and isinstance(listed.get("data"), Mapping):
            listed = listed["data"]
        rows = listed.get("cases") if isinstance(listed, Mapping) else None
        if not isinstance(rows, list):
            raise ControlError("reference case list returned an invalid collection")
        for row in rows:
            number = row.get("case_number") if isinstance(row, Mapping) else None
            if not isinstance(number, int):
                continue
            linked = await command(["case", "detection", "list", "--case", str(number)])
            if isinstance(linked, Mapping) and isinstance(linked.get("data"), Mapping):
                linked = linked["data"]
            detections = linked.get("detections") if isinstance(linked, Mapping) else None
            if not isinstance(detections, list):
                raise ControlError("reference detection list returned an invalid collection")
            if any(isinstance(item, Mapping) and item.get("detect_id") == public["detection_id"]
                   for item in detections):
                matching_numbers.append(number)
        cursor = listed.get("next_page_token") if isinstance(listed, Mapping) else None
        if not isinstance(cursor, str) or not cursor:
            break
    else:
        raise ControlError("reference case discovery exceeded the pagination bound")

    if len(matching_numbers) != 1:
        raise ControlError("reference did not discover exactly one case for the supplied detection")
    number = matching_numbers[0]
    expected_number = fixture.get("target_case_number")
    if isinstance(expected_number, int) and number != expected_number:
        raise ControlError("reference discovery did not match the trusted seeded case")
    await command(["case", "update", "--case-number", str(number), "--status", public["target_status"],
                   "--severity", public["target_severity"]])
    if not bad:
        await command(["case", "entity", "add", "--case", str(number), "--type", public["entity_type"],
                       "--value", public["entity_value"], "--note", public["entity_note"],
                       "--verdict", public["entity_verdict"]])
    await command(["case", "add-note", "--case-number", str(number), "--type", public["note_type"],
                   "--no-is-public", "--content", public["note_content"]])
    return f"Maintained case {number} for detection {public['detection_id']}"
