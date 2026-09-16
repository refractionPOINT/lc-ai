from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import yaml

from lc_eval.fixtures.routing import (
    CONTROL_EVENT_TYPE,
    ROUTING_EVENT_TYPE,
    RoutingFixture,
    RoutingHandle,
    RoutingSpec,
    _public_skeleton,
    build_routing_rule,
    reference,
)
from lc_eval.fixtures.local_cli import ControlError
from lc_eval.fixtures.search_dataset import SearchError, SearchPage, SearchResult
from lc_eval.verifiers.routing import verify_routing


def _spec() -> RoutingSpec:
    return RoutingSpec(
        oid="oid-1",
        trial_id="trial-1",
        adapter_name="adapter-1",
        installation_key="installation-key",
        ingest_secret="ingest-secret",
        adapter_hostname="eval-host",
        sensor_seed_key="sensor-seed",
        target_rule_name="target-rule",
        target_output_name="target-output",
        target_report_name="target-report",
        receiver_public_url="https://receiver.example",
        target_bucket_id="target-bucket",
        target_receipt_secret="target-secret",
        baseline_rule_name="baseline-rule",
        baseline_output_name="baseline-output",
        baseline_report_name="baseline-report",
        baseline_bucket_id="baseline-bucket",
        baseline_receipt_secret="baseline-secret",
    )


def test_public_skeleton_contains_scoped_candidate_configuration() -> None:
    spec = _spec()
    public = spec.public_facts
    assert public["destination_url"] == (
        "https://receiver.example/v1/ingest/target-bucket"
    )
    assert public["output_secret"] == "target-secret"
    assert public["adapter_config"]["webhook"]["client_options"]["identity"] == {
        "oid": "oid-1",
        "installation_key": "installation-key",
    }

    skeleton = yaml.safe_load(_public_skeleton(spec))
    assert skeleton["adapter"]["config"] == spec.webhook_spec.public_config
    assert skeleton["rule"]["config"] == build_routing_rule(
        trial_id="trial-1", report_name="target-report"
    )
    assert skeleton["output"]["config"] == {
        "dest_host": "https://receiver.example/v1/ingest/target-bucket",
        "secret_key": "target-secret",
        "cat": "target-report",
    }


def test_reference_runs_all_mutations_through_container_cli(
    tmp_path: Path, monkeypatch
) -> None:
    async def exercise() -> None:
        calls: list[tuple[list[str], int]] = []

        def fake_run(argv, *, timeout):
            calls.append((argv, timeout))
            return "{}"

        monkeypatch.setattr("lc_eval.execution.docker.run", fake_run)
        fixture = RoutingFixture(SimpleNamespace(), SimpleNamespace(), _spec())
        result = await reference(
            {"_routing": fixture},
            SimpleNamespace(work=tmp_path, agent="candidate-container"),
        )

        assert len(calls) == 3
        assert all(call[0][:5] == [
            "docker",
            "exec",
            "candidate-container",
            "limacharlie",
            "--output",
        ] for call in calls)
        assert calls[0][0][6:8] == ["cloud-adapter", "set"]
        assert calls[1][0][6:8] == ["dr", "set"]
        assert calls[2][0][6:8] == ["output", "create"]
        assert json.loads((tmp_path / "reference-output.json").read_text()) == {
            "dest_host": "https://receiver.example/v1/ingest/target-bucket",
            "secret_key": "target-secret",
            "cat": "target-report",
        }
        assert "adapter-1" in result and "target-rule" in result

        calls.clear()
        await reference(
            {"_routing": fixture},
            SimpleNamespace(work=tmp_path, agent="candidate-container"),
            bad=True,
        )
        bad_rule = json.loads((tmp_path / "reference-rule.json").read_text())
        assert [item["path"] for item in bad_rule["detect"]["rules"]] == [
            "event/eval_trial_id"
        ]
        assert len(calls) == 3

    asyncio.run(exercise())


def test_verification_uses_fresh_probes_and_positive_control() -> None:
    async def exercise() -> None:
        sent: list[dict[str, str]] = []

        class Webhook:
            async def send_events(self, events):
                sent.extend(events)

        class Search:
            calls = 0
            queries: list[str] = []

            async def execute(self, query, *_args, **_kwargs):
                self.calls += 1
                self.queries.append(query)
                if self.calls == 1:
                    raise SearchError(
                        "dataset initializing",
                        query_id="stale-query",
                        status_code=500,
                    )
                return SearchResult(
                    query_id="query",
                    events=tuple(sent),
                    pages=(SearchPage(1, None, None, 1, 1, len(sent)),),
                )

        class Management:
            async def list_receipts(self, bucket):
                event_type = (
                    CONTROL_EVENT_TYPE if bucket == "baseline-bucket" else ROUTING_EVENT_TYPE
                )
                return [
                    {
                        "events": [{"event": event}],
                        "signature_valid": True,
                        "received_at": datetime.now(timezone.utc).isoformat(),
                    }
                    for event in sent
                    if event["event_type"] == event_type
                    and event["environment"] == "production"
                    and event["eval_trial_id"] == "trial-1"
                ]

            async def health(self):
                return {"status": "ok", "database": "ok"}

        search = Search()
        fixture = RoutingFixture(SimpleNamespace(), Management(), _spec(), search=search)
        fixture.webhook = Webhook()

        async def read_outputs():
            return {"baseline-output": {"name": "baseline-output", "cat": "baseline"}}

        fixture.read_outputs = read_outputs
        handle = RoutingHandle(
            public_facts={},
            baseline_output_before={"name": "baseline-output", "cat": "baseline"},
            stale_probe_id="stale",
        )
        evidence = await fixture.collect_verification(
            handle,
            negative_window_seconds=0,
            total_timeout_seconds=1,
            poll_seconds=0.001,
        )

        assert len(evidence["expected_match_ids"]) == 1
        assert len(evidence["expected_negative_ids"]) == 3
        assert len(evidence["observed_ingestion_ids"]) == 5
        assert evidence["search_transient_failures"] == [
            {
                "attempt": 1,
                "event_id": sent[0]["eval_event_id"],
                "status_code": 500,
                "query_id": "stale-query",
            }
        ]
        assert search.queries
        assert all(
            query.startswith("* | * | event/eval_event_id == '")
            for query in search.queries
        )
        assert evidence["receiver_health"] == {
            "management_reachable": True,
            "receiver_ready": True,
            "positive_control_received": True,
        }
        assert evidence["observation_window"]["complete"] is True
        target_ids = {
            item["payload"]["event"]["eval_event_id"]
            for item in evidence["received_records"]
        }
        assert target_ids == set(evidence["expected_match_ids"])
        assert all(
            item["status"] == "pass"
            for item in verify_routing({}, {}, {}, evidence)
        )

    asyncio.run(exercise())


def test_ingestion_search_persistent_transient_is_infrastructure_error() -> None:
    async def exercise() -> None:
        class Search:
            async def execute(self, *_args, **_kwargs):
                raise SearchError(
                    "dataset unavailable", query_id="query", status_code=503
                )

        fixture = RoutingFixture(
            SimpleNamespace(), SimpleNamespace(), _spec(), search=Search()
        )
        events = [{"eval_event_id": "probe"}]
        try:
            await fixture._wait_ingested(
                events,
                start_time=1,
                end_time=2,
                deadline=time.monotonic() + 0.01,
                poll_seconds=0.001,
            )
        except ControlError as error:
            assert "search remained unavailable" in str(error)
            assert isinstance(error.__cause__, SearchError)
        else:
            raise AssertionError("persistent transient search failure was hidden")

    asyncio.run(exercise())
