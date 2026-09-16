"""End-to-end production-only detection routing fixture."""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
import yaml

from ..receiver import (
    CloudflaredTunnel,
    ManagementClient,
    ReceiverRuntime,
    ReceiverStore,
    ensure_cloudflared,
)
from ..execution.processes import cleanup as cleanup_process
from ..execution.processes import process_handle
from ..journal import Journal
from .local_cli import ControlError, LocalCLI
from .search_dataset import RegionalSearchClient, SearchError
from .webhook import HostedWebhookFixture, WebhookSpec


ROUTING_EVENT_TYPE = "LC_EVAL_ROUTE"
CONTROL_EVENT_TYPE = "LC_EVAL_ROUTE_CONTROL"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def build_routing_rule(
    *, trial_id: str, report_name: str, event_type: str = ROUTING_EVENT_TYPE
) -> dict[str, Any]:
    if not all((trial_id, report_name, event_type)):
        raise ValueError("routing rule values must be non-empty")
    return {
        "detect": {
            "op": "and",
            "event": event_type,
            "rules": [
                {
                    "op": "is",
                    "path": "event/eval_trial_id",
                    "value": trial_id,
                },
                {
                    "op": "is",
                    "path": "event/environment",
                    "value": "production",
                },
            ],
        },
        "respond": [{"action": "report", "name": report_name}],
    }


def build_webhook_output(
    *, name: str, destination: str, secret: str, category: str
) -> dict[str, str]:
    if not all((name, destination, secret, category)):
        raise ValueError("output values must be non-empty")
    return {
        "name": name,
        "module": "webhook",
        "type": "detect",
        "dest_host": destination,
        "secret_key": secret,
        "cat": category,
    }


@dataclass(frozen=True, slots=True)
class RoutingSpec:
    oid: str
    trial_id: str
    adapter_name: str
    installation_key: str
    ingest_secret: str
    adapter_hostname: str
    sensor_seed_key: str
    target_rule_name: str
    target_output_name: str
    target_report_name: str
    receiver_public_url: str
    target_bucket_id: str
    target_receipt_secret: str
    baseline_rule_name: str
    baseline_output_name: str
    baseline_report_name: str
    baseline_bucket_id: str
    baseline_receipt_secret: str

    @property
    def webhook_spec(self) -> WebhookSpec:
        return WebhookSpec(
            oid=self.oid,
            name=self.adapter_name,
            installation_key=self.installation_key,
            ingest_secret=self.ingest_secret,
            hostname=self.adapter_hostname,
            sensor_seed_key=self.sensor_seed_key,
        )

    def receiver_destination(self, bucket_id: str) -> str:
        return (
            f"{self.receiver_public_url.rstrip('/')}/v1/ingest/"
            f"{quote(bucket_id, safe='')}"
        )

    @property
    def public_facts(self) -> dict[str, Any]:
        """Candidate-visible scoped inputs and structural skeleton."""
        return {
            "eval_trial_id": self.trial_id,
            "organization_id": self.oid,
            "trial_selector": self.trial_id,
            "event_type": ROUTING_EVENT_TYPE,
            "adapter_name": self.adapter_name,
            "rule_name": self.target_rule_name,
            "output_name": self.target_output_name,
            "report_category": self.target_report_name,
            "receiver_destination": self.receiver_destination(self.target_bucket_id),
            "destination_url": self.receiver_destination(self.target_bucket_id),
            "receiver_secret": self.target_receipt_secret,
            "output_secret": self.target_receipt_secret,
            "adapter_config": self.webhook_spec.public_config,
            "rule_requirements": {
                "event": ROUTING_EVENT_TYPE,
                "eval_trial_id": self.trial_id,
                "environment": "production",
                "report_name": self.target_report_name,
                "enabled": True,
            },
            "output_requirements": {
                "module": "webhook",
                "type": "detect",
                "cat": self.target_report_name,
            },
        }


@dataclass(frozen=True, slots=True)
class RoutingHandle:
    public_facts: dict[str, Any]
    baseline_output_before: Any
    stale_probe_id: str


def _find_output(value: Any, oid: str, name: str) -> Any:
    if isinstance(value, dict) and oid in value:
        value = value[oid]
    if isinstance(value, dict):
        if name in value:
            return value[name]
        if value.get("name") == name:
            return value
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict) and item.get("name") == name:
                return item
    return None


def _event_id(value: Any, depth: int = 0) -> str | None:
    if depth > 8:
        return None
    if isinstance(value, dict):
        for key in ("eval_event_id", "probe_id"):
            if isinstance(value.get(key), str):
                return value[key]
        for nested in value.values():
            found = _event_id(nested, depth + 1)
            if found:
                return found
    elif isinstance(value, list):
        for nested in value:
            found = _event_id(nested, depth + 1)
            if found:
                return found
    return None


class RoutingFixture:
    """Provision hidden controls and collect bounded independent evidence."""

    def __init__(
        self,
        cli: LocalCLI,
        management: ManagementClient,
        spec: RoutingSpec,
        *,
        search: RegionalSearchClient | None = None,
    ):
        self.cli = cli
        self.management = management
        self.spec = spec
        self.webhook = HostedWebhookFixture(cli, spec.webhook_spec)
        self.search = search or RegionalSearchClient(cli, spec.oid)

    def reference_configs(self) -> dict[str, dict[str, Any]]:
        return {
            "rule": build_routing_rule(
                trial_id=self.spec.trial_id,
                report_name=self.spec.target_report_name,
            ),
            "output": build_webhook_output(
                name=self.spec.target_output_name,
                destination=self.spec.receiver_destination(self.spec.target_bucket_id),
                secret=self.spec.target_receipt_secret,
                category=self.spec.target_report_name,
            ),
        }

    async def _set_rule(self, name: str, rule: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps(rule, separators=(",", ":"))
        return await asyncio.to_thread(
            self.cli.invoke,
            ["dr", "set", "--key", name, "--enabled"],
            self.spec.oid,
            True,
            payload,
            90,
        )

    async def _delete_rule(self, name: str) -> dict[str, Any]:
        return await asyncio.to_thread(
            self.cli.invoke,
            ["dr", "delete", "--key", name, "--confirm"],
            self.spec.oid,
            True,
            None,
            90,
        )

    async def _set_output(self, config: dict[str, str]) -> dict[str, Any]:
        return await asyncio.to_thread(
            self.cli.api,
            self.spec.oid,
            "POST",
            f"outputs/{quote(self.spec.oid, safe='')}",
            form=config,
        )

    async def _delete_output(self, name: str) -> dict[str, Any]:
        return await asyncio.to_thread(
            self.cli.api,
            self.spec.oid,
            "DELETE",
            f"outputs/{quote(self.spec.oid, safe='')}",
            params={"name": name},
        )

    async def read_outputs(self) -> Any:
        return await asyncio.to_thread(
            self.cli.api,
            self.spec.oid,
            "GET",
            f"outputs/{quote(self.spec.oid, safe='')}",
        )

    async def read_rule(self, name: str) -> dict[str, Any]:
        path = (
            f"hive/dr-general/{quote(self.spec.oid, safe='')}/"
            f"{quote(name, safe='')}/data"
        )
        value = await asyncio.to_thread(self.cli.api, self.spec.oid, "GET", path)
        if not isinstance(value, dict):
            raise ControlError("D&R Hive read returned no object")
        return value

    async def configure_reference(self) -> dict[str, Any]:
        configs = self.reference_configs()
        await self.webhook.provision()
        await self._set_rule(self.spec.target_rule_name, configs["rule"])
        await self._set_output(configs["output"])
        return {
            "rule": await self.read_rule(self.spec.target_rule_name),
            "output": _find_output(
                await self.read_outputs(), self.spec.oid, self.spec.target_output_name
            ),
        }

    async def _post_signed_stale_receipt(self, probe_id: str) -> None:
        body = json.dumps(
            {"eval_event_id": probe_id, "kind": "signed-stale-control"},
            separators=(",", ":"),
        ).encode("utf-8")
        signature = hmac.new(
            self.spec.target_receipt_secret.encode("utf-8"), body, hashlib.sha256
        ).hexdigest()
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                self.spec.receiver_destination(self.spec.target_bucket_id),
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "lc-signature": signature,
                },
            )
        if response.status_code != 202:
            raise ControlError(
                f"receiver rejected stale control with HTTP {response.status_code}"
            )

    async def provision(self) -> RoutingHandle:
        await self.management.create_trial(
            self.spec.target_bucket_id, self.spec.target_receipt_secret
        )
        await self.management.create_trial(
            self.spec.baseline_bucket_id, self.spec.baseline_receipt_secret
        )
        baseline_rule = build_routing_rule(
            trial_id=self.spec.trial_id,
            report_name=self.spec.baseline_report_name,
            event_type=CONTROL_EVENT_TYPE,
        )
        baseline_output = build_webhook_output(
            name=self.spec.baseline_output_name,
            destination=self.spec.receiver_destination(self.spec.baseline_bucket_id),
            secret=self.spec.baseline_receipt_secret,
            category=self.spec.baseline_report_name,
        )
        await self._set_rule(self.spec.baseline_rule_name, baseline_rule)
        await self._set_output(baseline_output)
        baseline_before = _find_output(
            await self.read_outputs(), self.spec.oid, self.spec.baseline_output_name
        )
        if baseline_before is None:
            raise ControlError("baseline output was not independently readable")
        stale_probe_id = str(uuid.uuid4())
        await self._post_signed_stale_receipt(stale_probe_id)
        return RoutingHandle(
            public_facts=self.spec.public_facts,
            baseline_output_before=baseline_before,
            stale_probe_id=stale_probe_id,
        )

    def _probe_events(self) -> tuple[list[dict[str, str]], set[str], set[str], str]:
        matching = {
            "eval_event_id": str(uuid.uuid4()),
            "eval_trial_id": self.spec.trial_id,
            "event_type": ROUTING_EVENT_TYPE,
            "environment": "production",
            "message": "fresh matching routing probe",
        }
        staging = {
            **matching,
            "eval_event_id": str(uuid.uuid4()),
            "environment": "staging",
            "message": "fresh staging negative probe",
        }
        wrong_type = {
            **matching,
            "eval_event_id": str(uuid.uuid4()),
            "event_type": f"{ROUTING_EVENT_TYPE}_OTHER",
            "message": "fresh wrong-type negative probe",
        }
        wrong_trial = {
            **matching,
            "eval_event_id": str(uuid.uuid4()),
            "eval_trial_id": f"other-{uuid.uuid4()}",
            "message": "fresh wrong-trial negative probe",
        }
        control = {
            **matching,
            "eval_event_id": str(uuid.uuid4()),
            "event_type": CONTROL_EVENT_TYPE,
            "message": "fresh receiver positive control",
        }
        events = [matching, staging, wrong_type, wrong_trial, control]
        return (
            events,
            {matching["eval_event_id"]},
            {
                staging["eval_event_id"],
                wrong_type["eval_event_id"],
                wrong_trial["eval_event_id"],
            },
            control["eval_event_id"],
        )

    async def _wait_ingested(
        self,
        events: list[dict[str, str]],
        *,
        start_time: int,
        end_time: int,
        deadline: float,
        poll_seconds: float,
    ) -> tuple[set[str], list[dict[str, Any]]]:
        expected = {event["eval_event_id"] for event in events}
        observed: set[str] = set()
        valid_searches: set[str] = set()
        transient_failures: list[dict[str, Any]] = []
        last_transient: BaseException | None = None
        while time.monotonic() < deadline:
            for event in events:
                event_id = event["eval_event_id"]
                if event_id in observed:
                    continue
                query = f"* | event/eval_event_id == '{event_id}'"
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return observed
                try:
                    result = await asyncio.wait_for(
                        self.search.execute(query, start_time, end_time),
                        timeout=remaining,
                    )
                except SearchError as error:
                    if error.status_code not in {500, 502, 503, 504}:
                        raise
                    last_transient = error
                    transient_failures.append(
                        {
                            "attempt": len(transient_failures) + 1,
                            "event_id": event_id,
                            "status_code": error.status_code,
                            "query_id": error.query_id,
                        }
                    )
                    # A failed query ID cannot recover when a fresh-org
                    # search dataset is still initializing. Move on and issue
                    # a new search for this probe on the next pass.
                    continue
                except TimeoutError as error:
                    last_transient = error
                    transient_failures.append(
                        {
                            "attempt": len(transient_failures) + 1,
                            "event_id": event_id,
                            "status_code": None,
                            "query_id": None,
                            "timeout": True,
                        }
                    )
                    break
                valid_searches.add(event_id)
                if any(item.get("eval_event_id") == event_id for item in result.events):
                    observed.add(event_id)
            if observed == expected:
                break
            await asyncio.sleep(min(poll_seconds, max(0, deadline - time.monotonic())))
        unavailable = expected - valid_searches
        if unavailable:
            raise ControlError(
                "routing ingestion search remained unavailable for "
                f"{len(unavailable)} of {len(expected)} probes after "
                f"{len(transient_failures)} transient failures"
            ) from last_transient
        return observed, transient_failures

    @staticmethod
    def _flatten_receipts(receipts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        flattened: list[dict[str, Any]] = []
        for receipt in receipts:
            events = receipt.get("events")
            if not isinstance(events, list) or not events:
                flattened.append(receipt)
                continue
            for event in events:
                item = dict(receipt)
                item["payload"] = event
                item.pop("events", None)
                flattened.append(item)
        return flattened

    async def collect_verification(
        self,
        handle: RoutingHandle,
        *,
        settle_seconds: float = 0,
        negative_window_seconds: float = 180,
        total_timeout_seconds: float = 600,
        poll_seconds: float = 2,
    ) -> dict[str, Any]:
        """Inject hidden probes after mutation stops and collect frozen facts."""
        if min(negative_window_seconds, total_timeout_seconds) < 0 or poll_seconds <= 0:
            raise ValueError("routing verification timing bounds are invalid")
        if settle_seconds:
            await asyncio.sleep(settle_seconds)
        loop = asyncio.get_running_loop()
        deadline = loop.time() + total_timeout_seconds
        events, matching_ids, negative_ids, control_id = self._probe_events()
        observation_start = _utc_now()
        search_start = int(time.time()) - 60
        await self.webhook.send_events(events)
        ingested, search_transient_failures = await self._wait_ingested(
            events,
            start_time=search_start,
            end_time=int(time.time()) + max(60, int(total_timeout_seconds)),
            deadline=deadline,
            poll_seconds=poll_seconds,
        )

        positive_ready_at: float | None = None
        target_receipts: list[dict[str, Any]] = []
        baseline_receipts: list[dict[str, Any]] = []
        while loop.time() < deadline:
            target_receipts = await self.management.list_receipts(
                self.spec.target_bucket_id
            )
            baseline_receipts = await self.management.list_receipts(
                self.spec.baseline_bucket_id
            )
            target_seen = {_event_id(item) for item in target_receipts}
            baseline_seen = {_event_id(item) for item in baseline_receipts}
            positives = matching_ids <= target_seen and control_id in baseline_seen
            all_ingested = {event["eval_event_id"] for event in events} <= ingested
            if positives and all_ingested and positive_ready_at is None:
                positive_ready_at = loop.time()
            if (
                positive_ready_at is not None
                and loop.time() - positive_ready_at >= negative_window_seconds
            ):
                break
            await asyncio.sleep(min(poll_seconds, max(0, deadline - loop.time())))

        window_complete = (
            positive_ready_at is not None
            and loop.time() - positive_ready_at >= negative_window_seconds
        )
        observation_end = _utc_now()
        health: dict[str, Any]
        try:
            health = await self.management.health()
            management_reachable = health.get("status") == "ok"
        except Exception:
            health = {}
            management_reachable = False
        baseline_after = _find_output(
            await self.read_outputs(), self.spec.oid, self.spec.baseline_output_name
        )
        baseline_seen = {_event_id(item) for item in baseline_receipts}
        return {
            "expected_match_ids": sorted(matching_ids),
            "expected_negative_ids": sorted(negative_ids),
            "observed_ingestion_ids": sorted(ingested),
            "search_transient_failures": search_transient_failures,
            "receiver_health": {
                "management_reachable": management_reachable,
                "receiver_ready": health.get("database") == "ok",
                "positive_control_received": control_id in baseline_seen,
            },
            "observation_window": {
                "start": observation_start,
                "end": observation_end,
                "complete": window_complete,
                "minimum_seconds": negative_window_seconds,
            },
            "minimum_negative_window_seconds": negative_window_seconds,
            "received_records": self._flatten_receipts(target_receipts),
            "baseline_output_before": handle.baseline_output_before,
            "baseline_output_after": baseline_after,
            "probe_ids": {
                "matching": sorted(matching_ids),
                "negative": sorted(negative_ids),
                "positive_control": control_id,
                "signed_stale": handle.stale_probe_id,
            },
        }

    async def cleanup(self) -> None:
        errors: list[Exception] = []
        for operation in (
            lambda: self._delete_output(self.spec.target_output_name),
            lambda: self._delete_rule(self.spec.target_rule_name),
            lambda: self._delete_output(self.spec.baseline_output_name),
            lambda: self._delete_rule(self.spec.baseline_rule_name),
            self.webhook.delete,
            lambda: self.management.delete_trial(self.spec.target_bucket_id),
            lambda: self.management.delete_trial(self.spec.baseline_bucket_id),
        ):
            try:
                await operation()
            except Exception as error:
                errors.append(error)
        if errors:
            raise ControlError(f"routing cleanup had {len(errors)} failed operations")


class RoutingRuntime:
    """Own receiver, public stimulus, and routing fixture cleanup for one trial."""

    def __init__(
        self,
        routing: RoutingFixture,
        management: ManagementClient,
        receiver: ReceiverRuntime | None,
        *,
        feed_seconds: float = 5.0,
        process_journal: Journal | None = None,
        process_intent: str | None = None,
    ):
        if feed_seconds <= 0:
            raise ValueError("feed_seconds must be positive")
        self.routing = routing
        self.management = management
        self.receiver = receiver
        self.feed_seconds = feed_seconds
        self.process_journal = process_journal
        self.process_intent = process_intent
        self._feed_task: asyncio.Task[None] | None = None
        self._stopped = False

    async def start_feed(self) -> None:
        if self._feed_task is not None:
            raise RuntimeError("routing feed is already started")
        self._feed_task = asyncio.create_task(self._feed(), name="routing-public-feed")

    async def _feed(self) -> None:
        sequence = 0
        while True:
            sequence += 1
            events = [
                {
                    "event_type": ROUTING_EVENT_TYPE,
                    "eval_trial_id": self.routing.spec.trial_id,
                    "eval_event_id": f"documented-feed-{sequence}-{uuid.uuid4()}",
                    "environment": "production",
                    "message": "controller documented production sample",
                },
                {
                    "event_type": ROUTING_EVENT_TYPE,
                    "eval_trial_id": self.routing.spec.trial_id,
                    "eval_event_id": f"documented-feed-negative-{sequence}-{uuid.uuid4()}",
                    "environment": "staging",
                    "message": "controller documented staging sample",
                },
            ]
            try:
                await self.routing.webhook.send_events(events)
            except (ControlError, httpx.HTTPError):
                # Missing/unready adapter is expected while the candidate works.
                pass
            await asyncio.sleep(self.feed_seconds)

    async def stop_feed(self) -> None:
        task, self._feed_task = self._feed_task, None
        if task is not None:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    async def stop(self) -> None:
        if self._stopped:
            return
        self._stopped = True
        await self.stop_feed()
        try:
            await self.routing.cleanup()
        finally:
            try:
                await self.management.close()
                if self.receiver is not None:
                    await self.receiver.stop()
            finally:
                if self.process_journal is not None and self.process_intent is not None:
                    try:
                        resource = next(
                            item
                            for item in self.process_journal.resources()
                            if item["intent"] == self.process_intent
                        )
                    except StopIteration:
                        pass
                    else:
                        cleanup_process(resource, self.process_journal)
                if self.process_journal is not None:
                    self.process_journal.close()


def _routing_names(trial: str, seed: int) -> dict[str, str]:
    suffix = hashlib.sha256(f"{trial}:{seed}".encode()).hexdigest()[:12]
    return {
        "adapter": f"eval-route-{suffix}",
        "rule": f"eval-route-rule-{suffix}",
        "output": f"eval-route-output-{suffix}",
        "report": f"eval-route-report-{suffix}",
        "target_bucket": f"target-{suffix}",
        "baseline_rule": f"eval-control-rule-{suffix}",
        "baseline_output": f"eval-control-output-{suffix}",
        "baseline_report": f"eval-control-report-{suffix}",
        "baseline_bucket": f"control-{suffix}",
    }


def _public_skeleton(spec: RoutingSpec) -> str:
    configs = {
        "adapter": {
            "name": spec.adapter_name,
            "config": spec.webhook_spec.public_config,
        },
        "rule": {
            "name": spec.target_rule_name,
            "config": build_routing_rule(
                trial_id=spec.trial_id, report_name=spec.target_report_name
            ),
        },
        "output": {
            "name": spec.target_output_name,
            "module": "webhook",
            "type": "detect",
            "config": {
                "dest_host": spec.receiver_destination(spec.target_bucket_id),
                "secret_key": spec.target_receipt_secret,
                "cat": spec.target_report_name,
            },
        },
    }
    return yaml.safe_dump(configs, sort_keys=False)


def _verify_configured_cloudflared(path: Path, expected: str | None) -> Path:
    executable = path.expanduser().resolve()
    if not executable.is_file():
        raise ControlError("configured cloudflared executable is missing")
    if not expected:
        raise ControlError("configured cloudflared executable requires a SHA-256 pin")
    digest = hashlib.sha256(executable.read_bytes()).hexdigest()
    if not hmac.compare_digest(digest, expected.lower()):
        raise ControlError("configured cloudflared executable digest changed")
    return executable


async def _start_receiver(
    config: Any, root: Path, trial: str
) -> tuple[
    str,
    ManagementClient,
    ReceiverRuntime | None,
    Journal | None,
    str | None,
]:
    receiver_config = config.receiver
    if receiver_config.mode == "existing":
        if not receiver_config.public_url or not receiver_config.management_url:
            raise ControlError("existing receiver requires public_url and management_url")
        token_name = receiver_config.management_token_env
        if not token_name or not os.environ.get(token_name):
            raise ControlError(
                "existing receiver management token environment variable is missing"
            )
        management = ManagementClient(
            receiver_config.management_url, os.environ[token_name]
        )
        try:
            await management.health()
        except BaseException:
            await management.close()
            raise
        return receiver_config.public_url.rstrip("/"), management, None, None, None

    configured = receiver_config.cloudflared
    executable = (
        await asyncio.to_thread(
            _verify_configured_cloudflared,
            configured,
            receiver_config.cloudflared_sha256,
        )
        if configured is not None
        else await asyncio.to_thread(ensure_cloudflared, config.run_data_dir / "tools")
    )
    management_token = secrets.token_urlsafe(32)
    runtime = ReceiverRuntime(
        ReceiverStore(root / "receiver.sqlite3"),
        management_token,
    )
    process_journal = Journal(config.run_data_dir)
    process_intent: str | None = None
    try:
        await runtime.server.start()
        tunnel = CloudflaredTunnel(
            executable,
            runtime.server.ingest_url,
            root / "cloudflared",
        )
        runtime.tunnel = tunnel
        pending_handle = process_handle(
            executable=executable,
            argv=tunnel.command_argv(),
            config_dir=tunnel.config_dir,
        )
        process_intent = process_journal.intent(
            trial,
            "local_process",
            f"cloudflared-{trial}",
            pending_handle,
            ttl=config.limits.lease_seconds,
        )
        await tunnel.start()
        if tunnel.pid is None:
            raise ControlError("cloudflared started without a process ID")
        acquired_handle = process_handle(
            executable=executable,
            argv=tunnel.command_argv(),
            config_dir=tunnel.config_dir,
            pid=tunnel.pid,
        )
        process_journal.acquired(process_intent, str(tunnel.pid), acquired_handle)
        management = runtime.management_client
        await management.health()
    except BaseException:
        with contextlib.suppress(Exception):
            await runtime.stop()
        try:
            if process_intent is not None:
                resource = next(
                    item
                    for item in process_journal.resources()
                    if item["intent"] == process_intent
                )
                cleanup_process(resource, process_journal)
        finally:
            process_journal.close()
        raise
    return runtime.public_url, management, runtime, process_journal, process_intent


async def provision(
    config: Any,
    cli: LocalCLI,
    oid: str,
    trial: str,
    seed: int,
    root: str | Path,
) -> dict[str, Any]:
    """Provision evaluator controls and start the declared public feed."""
    from .scenario_runtime import installation_key

    names = _routing_names(trial, seed)
    installation = await asyncio.to_thread(installation_key, cli, oid, trial)
    trial_root = Path(root).resolve()
    (
        public_url,
        management,
        receiver,
        process_journal,
        process_intent,
    ) = await _start_receiver(config, trial_root, trial)
    spec = RoutingSpec(
        oid=oid,
        trial_id=trial,
        adapter_name=names["adapter"],
        installation_key=installation,
        ingest_secret=secrets.token_hex(24),
        adapter_hostname=f"eval-route-{names['adapter'][-12:]}",
        sensor_seed_key=secrets.token_hex(16),
        target_rule_name=names["rule"],
        target_output_name=names["output"],
        target_report_name=names["report"],
        receiver_public_url=public_url,
        target_bucket_id=names["target_bucket"],
        target_receipt_secret=secrets.token_hex(32),
        baseline_rule_name=names["baseline_rule"],
        baseline_output_name=names["baseline_output"],
        baseline_report_name=names["baseline_report"],
        baseline_bucket_id=names["baseline_bucket"],
        baseline_receipt_secret=secrets.token_hex(32),
    )
    routing = RoutingFixture(cli, management, spec)
    runtime = RoutingRuntime(
        routing,
        management,
        receiver,
        process_journal=process_journal,
        process_intent=process_intent,
    )
    try:
        handle = await routing.provision()
        await runtime.start_feed()
    except BaseException:
        with contextlib.suppress(Exception):
            await runtime.stop()
        raise
    return {
        "public": dict(spec.public_facts),
        "public_files": {"config-skeleton.yaml": _public_skeleton(spec)},
        "baseline_output_before": handle.baseline_output_before,
        "signed_stale_probe_id": handle.stale_probe_id,
        "_handle": handle,
        "_routing": routing,
        "_runtime": runtime,
    }


async def collect(
    config: Any,
    cli: LocalCLI,
    oid: str,
    fixture: dict[str, Any],
) -> dict[str, Any]:
    """Stop public stimuli and collect fresh, bounded verification evidence."""
    del cli, oid
    runtime = fixture.get("_runtime")
    routing = fixture.get("_routing")
    handle = fixture.get("_handle")
    if not isinstance(runtime, RoutingRuntime) or not isinstance(
        routing, RoutingFixture
    ):
        raise ControlError("routing fixture runtime is missing")
    if not isinstance(handle, RoutingHandle):
        raise ControlError("routing fixture handle is missing")
    await runtime.stop_feed()
    return await routing.collect_verification(
        handle,
        settle_seconds=3,
        negative_window_seconds=config.limits.negative_window_seconds,
        total_timeout_seconds=config.limits.verification_seconds,
    )


async def reference(
    fixture: dict[str, Any], env: Any, *, bad: bool = False
) -> str:
    """Configure the reference solely through the candidate's brokered CLI."""
    from ..execution.docker import run

    routing = fixture.get("_routing")
    if not isinstance(routing, RoutingFixture):
        raise ControlError("routing fixture runtime is missing")
    spec = routing.spec
    configs = routing.reference_configs()
    if bad:
        configs["rule"] = {
            **configs["rule"],
            "detect": {
                **configs["rule"]["detect"],
                "rules": [
                    rule
                    for rule in configs["rule"]["detect"]["rules"]
                    if rule.get("path") != "event/environment"
                ],
            },
        }
    adapter_path = env.work / "reference-adapter.json"
    rule_path = env.work / "reference-rule.json"
    output_path = env.work / "reference-output.json"
    adapter_path.write_text(json.dumps(spec.webhook_spec.public_config))
    rule_path.write_text(json.dumps(configs["rule"]))
    output_path.write_text(
        json.dumps(
            {
                key: value
                for key, value in configs["output"].items()
                if key not in {"name", "module", "type"}
            }
        )
    )

    commands = [
        [
            "cloud-adapter",
            "set",
            "--key",
            spec.adapter_name,
            "--input-file",
            "/work/reference-adapter.json",
            "--enabled",
        ],
        [
            "dr",
            "set",
            "--key",
            spec.target_rule_name,
            "--input-file",
            "/work/reference-rule.json",
            "--enabled",
        ],
        [
            "output",
            "create",
            "--name",
            spec.target_output_name,
            "--module",
            "webhook",
            "--type",
            "detect",
            "--input-file",
            "/work/reference-output.json",
        ],
    ]
    for args in commands:
        await asyncio.to_thread(
            run,
            [
                "docker",
                "exec",
                env.agent,
                "limacharlie",
                "--output",
                "json",
                *args,
            ],
            timeout=120,
        )
    return (
        f"Configured {'known-bad ' if bad else ''}adapter {spec.adapter_name}, "
        f"rule {spec.target_rule_name}, "
        f"and output {spec.target_output_name}."
    )
