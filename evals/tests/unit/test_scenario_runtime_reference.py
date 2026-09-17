from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from lc_eval.fixtures.local_cli import ControlError
from lc_eval.fixtures.scenario_runtime import (
    _prepare_export_dataset,
    installation_key,
    provision,
    reference,
    wait_for_webhook_search_ready,
)
from lc_eval.fixtures.search_dataset import (
    PaginationFixtureUnsupportedError,
    SearchPage,
    SearchResult,
    generate_search_dataset,
)
from lc_eval.fixtures.webhook import BatchReceipt


def test_installation_key_selects_adapter_iid() -> None:
    class FakeCLI:
        def invoke(self, args, oid):
            assert args == [
                "installation-key",
                "create",
                "--description",
                "eval-trial",
                "--get",
            ]
            assert oid == "oid"
            return {
                "iid": "00000000-0000-4000-8000-000000000001",
                "key": "binary-rpcm-key",
                "json_key": "encoded-json-sensor-key",
            }

    assert installation_key(FakeCLI(), "oid", "trial") == (
        "00000000-0000-4000-8000-000000000001"
    )


def test_installation_key_rejects_encoded_keys_without_iid() -> None:
    class FakeCLI:
        def invoke(self, args, oid):
            return {"key": "binary-rpcm-key", "json_key": "encoded-json-sensor-key"}

    try:
        installation_key(FakeCLI(), "oid", "trial")
    except ControlError as error:
        assert "iid" in str(error)
    else:
        raise AssertionError("encoded sensor key was accepted for an adapter")


def test_webhook_warmup_waits_until_accepted_probe_is_searchable(
    monkeypatch,
) -> None:
    async def exercise() -> None:
        sent: list[dict] = []
        observed_states: list[dict] = []

        class Hook:
            async def send_events(self, events):
                sent.extend(events)
                return [SimpleNamespace(status_code=202)]

        class Search:
            calls = 0

            async def execute(self, query, start, end, *, stream):
                self.calls += 1
                assert query == "* | LC_EVAL_READY | event/eval_trial_id == 'trial'"
                assert (start, stream) == (100, "event")
                events = () if self.calls == 1 else (sent[0],)
                return SearchResult(
                    query_id=f"query-{self.calls}",
                    events=events,
                    pages=(SearchPage(1, None, None, 1, 1, len(events)),),
                )

        async def no_sleep(_delay):
            return None

        monkeypatch.setattr(
            "lc_eval.fixtures.scenario_runtime.asyncio.sleep", no_sleep
        )
        search = Search()
        result = await wait_for_webhook_search_ready(
            Hook(),
            search,
            "trial",
            start_time=100,
            timeout_seconds=1,
            observer=observed_states.append,
        )

        assert len(sent) == 2
        assert search.calls == 2
        assert result["state"] == "ready"
        assert result["attempt_count"] == 2
        assert result["ready_probe_id"] == sent[0]["eval_event_id"]
        assert [value["state"] for value in observed_states] == ["waiting", "ready"]

    asyncio.run(exercise())


def test_webhook_warmup_times_out_when_accepted_probes_stay_missing() -> None:
    async def exercise() -> None:
        observed_states: list[dict] = []

        class Hook:
            async def send_events(self, events):
                return [SimpleNamespace(status_code=202)]

        class Search:
            async def execute(self, *_args, **_kwargs):
                await asyncio.sleep(0.02)
                return SearchResult(query_id="late", events=(), pages=())

        try:
            await wait_for_webhook_search_ready(
                Hook(),
                Search(),
                "trial",
                start_time=100,
                timeout_seconds=0.005,
                retry_interval_seconds=0,
                observer=observed_states.append,
            )
        except ControlError as error:
            assert "searchable readiness probe" in str(error)
        else:
            raise AssertionError("unsearchable webhook was treated as ready")

        assert observed_states[-1]["state"] == "timeout"
        assert observed_states[-1]["attempt_count"] == 1
        assert observed_states[-1]["attempts"][0]["hook_accepted"] is True
        assert observed_states[-1]["attempts"][0]["search_timeout"] is True

    asyncio.run(exercise())


def test_search_reference_projects_rows_from_raw_result_pages(
    tmp_path: Path, monkeypatch
) -> None:
    async def exercise() -> None:
        raw = json.dumps(
            [
                {"type": "stats", "rows": []},
                {
                    "type": "events",
                    "rows": [
                        {
                            "data": {
                                "event": {
                                    "eval_event_id": "one",
                                    "environment": "production",
                                    "message": "first",
                                }
                            },
                            "mtd": {"stream": "event"},
                        }
                    ],
                },
                {
                    "type": "events",
                    "fields": ["data", "mtd"],
                    "rows": [
                        [
                            {
                                "event": {
                                    "eval_event_id": "two",
                                    "environment": "production",
                                    "message": "second",
                                }
                            },
                            {"stream": "event"},
                        ]
                    ],
                },
            ]
        )

        def fake_run(argv, *, timeout):
            assert argv[:4] == ["docker", "exec", "candidate", "limacharlie"]
            assert timeout == 600
            return raw

        monkeypatch.setattr("lc_eval.execution.docker.run", fake_run)
        fixture = {
            "public": {
                "trial_selector": "trial",
                "window_start": 100,
                "window_end": 200,
            }
        }
        env = SimpleNamespace(agent="candidate", work=tmp_path)
        completion = await reference("search-complete-export", fixture, env)
        rows = [
            json.loads(line)
            for line in (tmp_path / "export.jsonl").read_text().splitlines()
        ]
        assert completion == "Exported 2 events"
        assert rows == [
            {
                "eval_event_id": "one",
                "environment": "production",
                "message": "first",
            },
            {
                "eval_event_id": "two",
                "environment": "production",
                "message": "second",
            },
        ]

        await reference("search-complete-export", fixture, env, bad=True)
        assert len((tmp_path / "export.jsonl").read_text().splitlines()) == 1

    asyncio.run(exercise())


class _AdaptiveHook:
    def __init__(self) -> None:
        self.accepted: list[dict] = []
        self.sends: list[tuple[dict, ...]] = []

    async def send_events(self, events, *, observer):
        stage = tuple(events)
        self.sends.append(stage)
        self.accepted.extend(stage)
        uncompressed_bytes = sum(len(json.dumps(event)) for event in stage)
        observer(
            {
                "target_events": len(stage),
                "accepted_batches": 1,
                "accepted_events": len(stage),
                "uncompressed_bytes": uncompressed_bytes,
            }
        )
        return [
            BatchReceipt(
                batch_number=1,
                event_count=len(stage),
                uncompressed_bytes=uncompressed_bytes,
                transmitted_bytes=uncompressed_bytes,
                compressed=False,
                status_code=202,
            )
        ]


class _AdaptiveSearch:
    def __init__(self, hook: _AdaptiveHook, paginate_at: int | None) -> None:
        self.hook = hook
        self.paginate_at = paginate_at
        self.calls = 0

    async def execute(self, *_args, **_kwargs):
        self.calls += 1
        events = tuple(self.hook.accepted)
        if self.paginate_at is not None and len(events) >= self.paginate_at:
            split = len(events) - 1
            pages = (
                SearchPage(1, None, "next", 1, 1, split),
                SearchPage(2, "next", None, 1, 1, 1),
            )
        else:
            pages = (SearchPage(1, None, None, 1, 1, len(events)),)
        return SearchResult(
            query_id=f"query-{self.calls}", events=events, pages=pages
        )


def _small_adaptive_fixture(monkeypatch) -> None:
    monkeypatch.setattr(
        "lc_eval.fixtures.scenario_runtime.generate_search_dataset",
        lambda trial, **bounds: generate_search_dataset(
            trial, matching_count=2, nonmatching_count=1, **bounds
        ),
    )
    monkeypatch.setattr(
        "lc_eval.fixtures.scenario_runtime.DEFAULT_GROWTH_EVENTS", 2
    )


def _adaptive_config(*, max_events=7, max_fixture_bytes=100_000_000):
    return SimpleNamespace(
        limits=SimpleNamespace(
            verification_seconds=1,
            max_events=max_events,
            max_fixture_bytes=max_fixture_bytes,
        )
    )


def test_adaptive_export_grows_only_after_complete_single_page(tmp_path, monkeypatch) -> None:
    async def exercise() -> None:
        _small_adaptive_fixture(monkeypatch)
        hook = _AdaptiveHook()
        search = _AdaptiveSearch(hook, paginate_at=5)
        config = _adaptive_config(max_fixture_bytes=123_456)

        dataset, ready, _end = await _prepare_export_dataset(
            config,
            hook,
            search,
            "trial",
            tmp_path,
            start_time=100,
        )

        assert [len(stage) for stage in hook.sends] == [3, 2]
        assert hook.sends[0] == dataset.events[:3]
        assert hook.sends[1] == dataset.events[3:]
        assert len(dataset.events) == 5
        assert len(dataset.production) == 4
        assert len(dataset.nonproduction) == 1
        assert ready.traversed_continuation

        ledger = json.loads((tmp_path / "injected-events.json").read_text())
        assert ledger["events"] == list(dataset.events)
        assert ledger["event_count"] == 5
        assert ledger["fixture_event_ceiling"] == 7
        assert ledger["fixture_byte_ceiling"] == 123_456
        progress = json.loads((tmp_path / "injection-progress.json").read_text())
        assert progress["target_events"] == 5
        assert progress["accepted_events"] == 5
        assert progress["fixture_event_ceiling"] == 7
        assert progress["fixture_byte_ceiling"] == 123_456
        receipts = json.loads((tmp_path / "injection-receipts.json").read_text())
        assert [row["batch_number"] for row in receipts] == [1, 2]
        assert [row["growth_stage"] for row in receipts] == [1, 2]
        growth = json.loads((tmp_path / "fixture-growth.json").read_text())
        assert growth["state"] == "ready"
        assert growth["final_event_count"] == 5
        assert growth["fixture_event_ceiling"] == 7
        assert growth["fixture_byte_ceiling"] == 123_456
        assert [stage["state"] for stage in growth["stages"]] == [
            "complete_single_page",
            "ready",
        ]

    asyncio.run(exercise())


def test_adaptive_export_reports_unsupported_at_event_ceiling(
    tmp_path, monkeypatch
) -> None:
    async def exercise() -> None:
        _small_adaptive_fixture(monkeypatch)
        hook = _AdaptiveHook()
        search = _AdaptiveSearch(hook, paginate_at=None)
        config = _adaptive_config()

        with pytest.raises(PaginationFixtureUnsupportedError) as raised:
            await _prepare_export_dataset(
                config,
                hook,
                search,
                "trial",
                tmp_path,
                start_time=100,
            )

        assert raised.value.fixture_event_count == 7
        assert [len(stage) for stage in hook.sends] == [3, 2, 2]
        growth = json.loads((tmp_path / "fixture-growth.json").read_text())
        assert growth["state"] == "unsupported"
        assert growth["final_event_count"] == 7
        assert len(growth["stages"]) == 3
        assert all(
            stage["state"] == "complete_single_page"
            for stage in growth["stages"]
        )

    asyncio.run(exercise())


def test_adaptive_export_reports_unsupported_when_byte_ceiling_blocks_growth(
    tmp_path, monkeypatch
) -> None:
    async def exercise() -> None:
        initial = generate_search_dataset(
            "trial", matching_count=2, nonmatching_count=1
        )
        byte_ceiling = initial.total_json_bytes + 1

        def fixed_dataset(trial, **bounds):
            assert trial == "trial"
            assert bounds == {"max_events": 7, "max_bytes": byte_ceiling}
            return initial

        monkeypatch.setattr(
            "lc_eval.fixtures.scenario_runtime.generate_search_dataset",
            fixed_dataset,
        )
        monkeypatch.setattr(
            "lc_eval.fixtures.scenario_runtime.DEFAULT_GROWTH_EVENTS", 2
        )
        hook = _AdaptiveHook()
        search = _AdaptiveSearch(hook, paginate_at=None)

        with pytest.raises(PaginationFixtureUnsupportedError) as raised:
            await _prepare_export_dataset(
                _adaptive_config(max_fixture_bytes=byte_ceiling),
                hook,
                search,
                "trial",
                tmp_path,
                start_time=100,
            )

        assert raised.value.fixture_event_count == 3
        assert raised.value.limiting_ceiling == "bytes"
        assert [len(stage) for stage in hook.sends] == [3]
        growth = json.loads((tmp_path / "fixture-growth.json").read_text())
        assert growth["state"] == "unsupported"
        assert growth["limiting_ceiling"] == "bytes"
        assert growth["fixture_byte_ceiling"] == byte_ceiling

    asyncio.run(exercise())


@pytest.mark.parametrize(
    ("max_events", "max_fixture_bytes", "error"),
    [
        (2, 100_000_000, "event counts"),
        (7, 1, "byte ceiling"),
    ],
)
def test_adaptive_export_rejects_initial_dataset_over_configured_ceiling_before_send(
    tmp_path,
    monkeypatch,
    max_events,
    max_fixture_bytes,
    error,
) -> None:
    async def exercise() -> None:
        _small_adaptive_fixture(monkeypatch)
        hook = _AdaptiveHook()
        search = _AdaptiveSearch(hook, paginate_at=None)

        with pytest.raises(ValueError, match=error):
            await _prepare_export_dataset(
                _adaptive_config(
                    max_events=max_events,
                    max_fixture_bytes=max_fixture_bytes,
                ),
                hook,
                search,
                "trial",
                tmp_path,
                start_time=100,
            )

        assert hook.sends == []
        assert not (tmp_path / "injected-events.json").exists()

    asyncio.run(exercise())


def test_export_provision_checks_initial_ceilings_before_remote_setup(
    tmp_path, monkeypatch
) -> None:
    async def exercise() -> None:
        _small_adaptive_fixture(monkeypatch)

        class NoRemoteCalls:
            def __getattr__(self, name):
                raise AssertionError(f"unexpected remote access through {name}")

        with pytest.raises(ValueError, match="event counts"):
            await provision(
                _adaptive_config(max_events=2),
                NoRemoteCalls(),
                "oid",
                "trial",
                "search-complete-export",
                1,
                tmp_path,
            )

        assert list(tmp_path.iterdir()) == []

    asyncio.run(exercise())
