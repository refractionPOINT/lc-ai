"""Verifier for real native endpoint enrollment, tagging, and tasking."""

from __future__ import annotations

import json
import shlex
from collections.abc import Mapping, Sequence
from typing import Any

from .base import assertion, evidence_refs, merge_evidence

PATH = "/work/process-observation.json"


def _tag_values(value: Any) -> set[str] | None:
    if isinstance(value, Mapping):
        value = value.get("tags")
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return None
    if not all(isinstance(item, str) for item in value):
        return None
    return set(value)


def _key_records(value: Any) -> dict[str, dict[str, Any]] | None:
    """Normalize the documented CLI mapping keyed by installation-key IID."""
    if not isinstance(value, Mapping):
        return None
    records = value.get("keys", value)
    if not isinstance(records, Mapping):
        return None
    normalized = {}
    for iid, record in records.items():
        if not isinstance(iid, str) or not isinstance(record, Mapping):
            return None
        normalized[iid] = dict(record)
    return normalized


def _command_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def _process_events(value: Any) -> list[Mapping[str, Any]] | None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return None
    events = []
    for item in value:
        if not isinstance(item, Mapping):
            return None
        routing, event = item.get("routing"), item.get("event")
        if not isinstance(routing, Mapping) or routing.get("event_type") != "OS_PROCESSES_REP":
            continue
        if not isinstance(event, Mapping) or not isinstance(event.get("PROCESSES"), list):
            return None
        if not all(isinstance(process, Mapping) for process in event["PROCESSES"]):
            return None
        events.append(item)
    return events or None


def _marker_identities(value: Any, marker: str) -> set[tuple[Any, Any, Any]] | None:
    events = _process_events(value)
    if events is None:
        return None
    identities = set()
    for item in events:
        for process in item["event"]["PROCESSES"]:
            command = process.get("COMMAND_LINE")
            if isinstance(command, str) and marker in _command_tokens(command):
                identities.add((process.get("PROCESS_ID"), process.get("FILE_PATH"), command))
    return identities


def _artifact(frozen):
    files = frozen.get("files") if isinstance(frozen, Mapping) else None
    return files.get(PATH) if isinstance(files, Mapping) and isinstance(files.get(PATH), Mapping) else None


def _ids(rows):
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return set()
    return {str(row.get("sid", row.get("id"))) for row in rows if isinstance(row, Mapping) and row.get("sid", row.get("id"))}


def verify_native_sensor(manifest, fixture_handle, frozen_artifacts, evidence):
    del manifest
    facts = merge_evidence(fixture_handle, evidence)
    out = []
    enrollment_state = facts.get("enrollment_state")
    if enrollment_state in {"missing", "invalid"}:
        enrollment_status = "fail"
    elif enrollment_state in {"validated", "deploying", "registered"}:
        enrollment_status = "pass"
    else:
        enrollment_status = "unknown"
    out.append(assertion("native_sensor.enrollment.request", enrollment_status,
                         expected={"schema_version": 1, "deployment": "native_linux_sensor_v1", "native_key": True},
                         observed={"state": enrollment_state, "error_stage": facts.get("error_stage")},
                         evidence=["evidence:enrollment-contract"],
                         explanation="The candidate submitted a valid bounded native enrollment request." if enrollment_status == "pass" else "The enrollment request was absent, invalid, or could not be observed."))
    deployment = facts.get("deployment")
    safe = isinstance(deployment, Mapping) and deployment.get("network_mode") not in {"host", "none"} and deployment.get("privileged") is False and deployment.get("read_only") is True and deployment.get("binds") in (None, []) and deployment.get("mounts") in (None, []) and "ALL" in (deployment.get("cap_drop") or [])
    out.append(assertion("native_sensor.deployment.safe", "pass" if safe else "unknown" if deployment is None else "fail", expected={"host_network": False, "privileged": False, "bind_mounts": [], "cap_drop": "ALL"}, observed=deployment, evidence=["evidence:docker-inspect"], explanation="The real sensor ran in an owned read-only unprivileged container without host networking or mounts." if safe else "Native container isolation evidence is missing or unsafe."))
    sid, sensor = facts.get("sensor_id"), facts.get("sensor")
    online_sensors = facts.get("online_sensors")
    online_ids = _ids(online_sensors)
    registered = (isinstance(sid, str) and isinstance(sensor, Mapping)
                  and sensor.get("sid") == sid and sid in online_ids)
    registration_observed = isinstance(sensor, Mapping) and isinstance(online_sensors, Sequence) and not isinstance(online_sensors, (str, bytes))
    registration_status = "pass" if registered else "fail" if registration_observed else "unknown"
    out.append(assertion("native_sensor.registered", registration_status, expected={"sensor_get_sid_exact": sid, "online_list_membership": True}, observed={"sensor_id": sid, "sensor_get_sid": sensor.get("sid") if isinstance(sensor, Mapping) else None, "online_sensor_ids": sorted(online_ids), "sensor_version": sensor.get("version") if isinstance(sensor, Mapping) else None, "alive_display": sensor.get("alive") if isinstance(sensor, Mapping) else None, "runtime_error": facts.get("runtime_error"), "binary_sha256": facts.get("binary_sha256")}, evidence=["evidence:sensor-get", "evidence:sensor-list-online"], explanation="The downloaded native binary has an exact sensor record and exact online-list membership." if registered else "Independent native sensor identity or online membership is absent."))
    tags = facts.get("tags")
    normalized_tags = _tag_values(tags)
    tagged = isinstance(facts.get("required_tag"), str) and normalized_tags is not None and facts["required_tag"] in normalized_tags
    out.append(assertion("native_sensor.tagged", "pass" if tagged else "unknown" if tags is None else "fail", expected=facts.get("required_tag"), observed=tags, evidence=["evidence:tag-list"], explanation="The enrolled sensor has the required tag." if tagged else "The required tag was not independently observed."))
    trusted = facts.get("trusted_task_result")
    trusted_processes = _process_events(trusted)
    real_response = trusted_processes is not None
    out.append(assertion("native_sensor.task.real_response", "pass" if real_response else "unknown", expected="trusted os_processes response", observed={"present": real_response}, evidence=["evidence:trusted-task-request"], explanation="Trusted tasking received a real sensor response." if real_response else "Trusted task response evidence is unavailable."))
    artifact = _artifact(frozen_artifacts)
    candidate = None
    parse_error = None
    if isinstance(artifact, Mapping) and isinstance(artifact.get("content"), str):
        try:
            candidate = json.loads(artifact["content"])
        except json.JSONDecodeError as error:
            parse_error = str(error)
    marker = facts.get("marker", "__missing__")
    trusted_ids = _marker_identities(trusted, marker)
    candidate_ids = _marker_identities(candidate, marker)
    matching_ids = (trusted_ids or set()) & (candidate_ids or set())
    observed = bool(matching_ids)
    artifact_status = "pass" if observed else "fail" if real_response else "unknown"
    out.append(assertion("native_sensor.task.marker_observed", artifact_status, expected={"marker_token": marker, "matching_process_identity": True}, observed={"trusted_shape": trusted_processes is not None, "candidate_shape": _process_events(candidate) is not None, "trusted_marker_count": len(trusted_ids or ()), "candidate_marker_count": len(candidate_ids or ()), "matching_identity_count": len(matching_ids), "parse_error": parse_error}, evidence=evidence_refs(artifact, f"artifact:{PATH}") + ["evidence:trusted-task-request"], explanation="Candidate and trusted OS_PROCESSES_REP payloads contain the same marker process identity." if observed else "The candidate artifact is missing, malformed, or does not match the trusted marker process identity."))
    before_keys, after_keys = facts.get("baseline_keys"), facts.get("keys_after")
    before_records, after_records = _key_records(before_keys), _key_records(after_keys)
    description = facts.get("installation_key_description")
    matching_keys = [] if after_records is None else [iid for iid, record in after_records.items() if record.get("desc") == description]
    baseline_exact = before_records is not None and after_records is not None and all(after_records.get(iid) == record for iid, record in before_records.items())
    expected_key_ids = None
    extra_key_ids: list[str] = []
    missing_key_ids: list[str] = []
    if before_records is not None and after_records is not None and len(matching_keys) == 1:
        expected_key_ids = set(before_records) | {matching_keys[0]}
        extra_key_ids = sorted(set(after_records) - expected_key_ids)
        missing_key_ids = sorted(expected_key_ids - set(after_records))
    exact_membership = expected_key_ids is not None and not extra_key_ids and not missing_key_ids
    keys_preserved = baseline_exact and exact_membership
    keys_status = "unknown" if before_records is None or after_records is None else "pass" if keys_preserved else "fail"
    out.append(assertion("native_sensor.keys.preserved", keys_status, expected={"baseline_unchanged": True, "requested_description_exact_count": 1, "additional_keys": "only requested key unless reused"}, observed={"baseline_unchanged": baseline_exact, "requested_description_exact_ids": matching_keys, "extra_key_ids": extra_key_ids, "missing_key_ids": missing_key_ids}, evidence=["evidence:installation-keys"], explanation="Every baseline key is exact and the key set adds only the requested deployment key, unless it was reused." if keys_preserved else "Installation-key preservation or exact requested membership is not proven."))
    before_ids, after_ids = _ids(facts.get("baseline_sensors")), _ids(facts.get("sensors_after"))
    distractors = before_ids <= after_ids if facts.get("sensors_after") is not None else False
    out.append(assertion("native_sensor.distractors.preserved", "pass" if distractors else "unknown" if facts.get("sensors_after") is None else "fail", expected=sorted(before_ids), observed=sorted(after_ids), evidence=["evidence:sensor-list"], explanation="All pre-existing sensor identities remain present." if distractors else "Pre-existing sensor preservation is not proven."))
    return out


verify = verify_native_sensor
