"""Ledger-owned disposable organization lifecycle."""

from __future__ import annotations

import json
import time
import uuid

from ..journal import Journal
from .local_cli import ControlError, LocalCLI


INVENTORY_POLL_SECONDS = 3
MINIMUM_ABSENCE_SECONDS = 60


def unwrap(value):
    if isinstance(value, dict) and "data" in value:
        data = value["data"]
        if isinstance(data, str):
            try:
                return json.loads(data)
            except ValueError:
                pass
        elif isinstance(data, dict):
            return data
    return value


def exact_owned_org(cli: LocalCLI, name: str, oid: str | None = None) -> dict | None:
    """Return an exact owned org through server-filtered, bounded inventory."""
    if not isinstance(name, str) or not name:
        raise ValueError("owned organization name must be non-empty")
    result = cli.invoke(
        ["org", "list", "--filter", name, "--limit", "200", "--offset", "0"]
    )
    if not isinstance(result, list):
        raise ControlError("owner organization inventory has an unsupported shape")
    exact_name = [
        item
        for item in result
        if isinstance(item, dict) and item.get("name") == name
    ]
    if len(exact_name) > 1:
        raise ControlError("owner organization inventory returned a duplicate exact name")
    if oid is not None:
        same_oid = [
            item
            for item in result
            if isinstance(item, dict) and item.get("oid") == oid
        ]
        if any(item.get("name") != name for item in same_oid):
            raise ControlError("owned organization identity mismatch")
        if exact_name and exact_name[0].get("oid") != oid:
            raise ControlError("owned organization name resolves to another OID")
    return exact_name[0] if exact_name else None


def _confirmed_delete_result(value) -> bool:
    value = unwrap(value)
    if isinstance(value, bool):
        return value
    if not isinstance(value, dict):
        return False
    for key in ("success", "ok", "deleted"):
        if key in value:
            return value[key] is True
    return value.get("status") in {"ok", "success", "deleted"}


class Organizations:
    def __init__(self, cli: LocalCLI, journal: Journal, max_orgs: int = 2):
        self.cli, self.journal, self.max_orgs = cli, journal, max_orgs

    def create(self, trial: str, location: str = "auto") -> dict:
        active = [r for r in self.journal.resources() if r["kind"] == "org"]
        if len(active) >= self.max_orgs:
            raise ControlError("owned organization limit reached; reconcile first")
        name = "lc-eval-" + uuid.uuid4().hex[:20]
        intent = self.journal.intent(trial, "org", name, {"name": name, "location": location})
        raw = unwrap(self.cli.invoke(["org", "create", "--name", name, "--location", location]))
        oid = raw.get("oid") if isinstance(raw, dict) else None
        try:
            uuid.UUID(oid)
        except (ValueError, TypeError, AttributeError) as exc:
            raise ControlError("create response has no valid OID; reconcile create intent") from exc
        handle = {"oid": oid, "name": name, "intent": intent, "location": location}
        self.journal.acquired(intent, oid, handle)
        deadline = time.monotonic() + self.cli.config.readiness_seconds
        last_error = None
        while time.monotonic() < deadline:
            try:
                self.cli.invoke(["auth", "test"], oid, json_output=False)
                info = self.cli.api(oid, "GET", f"orgs/{oid}")
                if not isinstance(info, dict) or info.get("oid") != oid or info.get("name") != name:
                    raise ControlError("organization readiness identity mismatch")
                handle["info"] = info
                handle["urls"] = self.cli.get_urls(oid)
                return handle
            except ControlError as exc:
                last_error = str(exc)
                time.sleep(3)
        raise ControlError(f"organization readiness timeout: {last_error}")

    def cleanup(self, resource: dict):
        if resource["kind"] != "org":
            raise ValueError("wrong resource kind")
        oid = resource["resource_id"]
        if not oid:
            match = exact_owned_org(self.cli, resource["name"])
            if match is None:
                deadline = time.monotonic() + MINIMUM_ABSENCE_SECONDS
                while time.monotonic() < deadline:
                    time.sleep(
                        min(INVENTORY_POLL_SECONDS, deadline - time.monotonic())
                    )
                    if exact_owned_org(self.cli, resource["name"]) is not None:
                        raise ControlError(
                            "ambiguous organization appeared during absence confirmation"
                        )
                self.journal.cleaned(resource["intent"])
                return
            oid = match["oid"]
            self.journal.acquired(resource["intent"], oid, {**resource["handle"], "oid": oid})
        handle = dict(resource["handle"])
        delete_confirmed = handle.get("delete_confirmed") is True
        existing = exact_owned_org(self.cli, resource["name"], oid)
        authoritative_absence = False
        if existing is None and not delete_confirmed:
            try:
                identity = self.cli.api(oid, "GET", f"orgs/{oid}")
            except ControlError as error:
                authoritative_absence = error.status_code == 404
                if not authoritative_absence:
                    visibility_deadline = (
                        time.monotonic() + self.cli.config.readiness_seconds
                    )
                    while time.monotonic() < visibility_deadline:
                        time.sleep(INVENTORY_POLL_SECONDS)
                        existing = exact_owned_org(
                            self.cli, resource["name"], oid
                        )
                        if existing is not None:
                            break
                    if existing is None:
                        raise ControlError(
                            "owned organization never became visible for deletion"
                        ) from error
            else:
                if (
                    not isinstance(identity, dict)
                    or identity.get("oid") != oid
                    or identity.get("name") != resource["name"]
                ):
                    raise ControlError("organization API identity mismatch")
                existing = identity

        if authoritative_absence:
            deadline = time.monotonic() + MINIMUM_ABSENCE_SECONDS
            while time.monotonic() < deadline:
                time.sleep(
                    min(INVENTORY_POLL_SECONDS, deadline - time.monotonic())
                )
                if exact_owned_org(self.cli, resource["name"], oid) is not None:
                    raise ControlError(
                        "organization reappeared after authoritative absence"
                    )
            self.journal.cleaned(resource["intent"])
            return
        if existing is not None:
            result = unwrap(self.cli.invoke(["org", "delete"], oid))
            token = next(
                (
                    result[key]
                    for key in ("confirmation", "confirmation_token", "token")
                    if isinstance(result, dict) and result.get(key)
                ),
                None,
            )
            if not isinstance(token, str):
                raise ControlError("unrecognized org deletion confirmation response")
            deleted = self.cli.invoke(["org", "delete", "--confirm-token", token], oid)
            if not _confirmed_delete_result(deleted):
                raise ControlError("organization delete response did not confirm success")
            handle.update(
                {
                    "oid": oid,
                    "delete_confirmed": True,
                    "delete_confirmed_at": time.time(),
                }
            )
            self.journal.acquired(resource["intent"], oid, handle)
            delete_confirmed = True
        if not delete_confirmed:
            raise ControlError(
                "owned organization is absent without a confirmed delete; refusing to infer cleanup"
            )

        deadline = time.monotonic() + self.cli.config.deletion_seconds
        absent_since = None
        while time.monotonic() < deadline:
            existing = exact_owned_org(self.cli, resource["name"], oid)
            if existing is None:
                absent_since = absent_since or time.monotonic()
                if time.monotonic() - absent_since >= MINIMUM_ABSENCE_SECONDS:
                    self.journal.cleaned(resource["intent"])
                    return
            else:
                absent_since = None
            time.sleep(
                min(INVENTORY_POLL_SECONDS, max(0, deadline - time.monotonic()))
            )
        raise ControlError("organization deletion did not reach sustained absence")
