from __future__ import annotations

import asyncio
import json

import pytest

from lc_eval.fixtures.search_dataset import (
    EVENT_TYPE,
    PaginationNotObservedError,
    RegionalSearchClient,
    SearchPage,
    SearchError,
    SearchResult,
    adaptive_event_targets,
    generate_search_dataset,
    grow_search_dataset,
    normalize_event_row,
)
from lc_eval.fixtures.local_cli import ControlError


class FakeSearchCLI:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []
        self.polls = 0

    def get_urls(self, oid: str) -> dict[str, str]:
        assert oid == "oid-1"
        return {"search": "region.replay-search.example"}

    def api(self, oid: str, method: str, path: str, **kwargs):
        self.calls.append((method, path, kwargs))
        assert oid == "oid-1"
        assert kwargs["root"] == "https://region.replay-search.example/v1"
        if method == "POST":
            return {"queryId": "query-1"}
        if method == "DELETE":
            return {}
        self.polls += 1
        if self.polls == 1:
            return {"completed": False, "nextPollInMs": 0, "results": []}
        if self.polls == 2:
            assert kwargs["params"] is None
            return {
                "completed": True,
                "results": [
                    {
                        "type": "events",
                        "rows": [{"data": {"eval_event_id": "one"}, "mtd": {}}],
                        "nextToken": "continuation",
                    }
                ],
            }
        assert kwargs["params"] == {"token": "continuation"}
        return {
            "completed": True,
            "results": [
                {
                    "type": "events",
                    "fields": ["data", "mtd"],
                    "rows": [[{"eval_event_id": "two"}, {"sid": "s"}]],
                }
            ],
        }


def test_regional_search_polls_and_follows_inner_continuation() -> None:
    async def exercise() -> None:
        cli = FakeSearchCLI()
        search = RegionalSearchClient(
            cli, "oid-1", timeout_seconds=2, poll_interval_seconds=0
        )
        result = await search.execute("*", 100, 200)
        assert result.query_id == "query-1"
        assert result.events == (
            {"eval_event_id": "one"},
            {"eval_event_id": "two"},
        )
        assert result.traversed_continuation
        assert result.pages[0].polls == 2
        assert result.pages[0].next_token == "continuation"
        assert result.pages[1].token_used == "continuation"
        assert cli.calls[0][2]["body"] == {
            "oid": "oid-1",
            "query": "*",
            "startTime": "100",
            "endTime": "200",
            "paginated": True,
            "stream": "event",
        }
        assert cli.calls[-1][0] == "DELETE"

    asyncio.run(exercise())


def test_empty_continuation_page_is_not_pagination_proof() -> None:
    result = SearchResult(
        query_id="query",
        events=({"eval_event_id": "one"},),
        pages=(
            SearchPage(1, None, "continuation", 1, 1, 1),
            SearchPage(2, "continuation", None, 1, 0, 0),
        ),
    )

    assert result.traversed_continuation is False


def test_regional_search_retries_transient_poll_500(monkeypatch) -> None:
    async def exercise() -> None:
        class TransientCLI(FakeSearchCLI):
            failures = 0

            def api(self, oid: str, method: str, path: str, **kwargs):
                if method == "GET" and self.failures == 0:
                    self.failures += 1
                    raise ControlError("temporary", status_code=500)
                return super().api(oid, method, path, **kwargs)

        monkeypatch.setattr("lc_eval.fixtures.search_dataset.time.sleep", lambda _: None)
        cli = TransientCLI()
        result = await RegionalSearchClient(
            cli, "oid-1", timeout_seconds=2, poll_interval_seconds=0
        ).execute("*", 100, 200)
        assert cli.failures == 1
        assert result.traversed_continuation

    asyncio.run(exercise())


def test_normalize_event_rows_rejects_mismatched_fields() -> None:
    assert normalize_event_row({"event": {"id": "a"}}) == {"id": "a"}
    assert normalize_event_row(
        {"data": {"event": {"id": "nested"}, "routing": {"event_type": "X"}}}
    ) == {"id": "nested"}
    assert normalize_event_row(
        {
            "data": {
                "event": {
                    "data": {
                        "event": {
                            "eval_event_id": "deeply-nested",
                            "message": "ok",
                        }
                    }
                }
            }
        }
    ) == {"eval_event_id": "deeply-nested", "message": "ok"}
    try:
        normalize_event_row([1], ["a", "b"])
    except RuntimeError as error:
        assert "fields" in str(error)
    else:
        raise AssertionError("malformed positional row was accepted")


def test_dataset_has_random_unique_full_ground_truth() -> None:
    first = generate_search_dataset("trial", matching_count=5_003, nonmatching_count=137)
    second = generate_search_dataset("trial", matching_count=2, nonmatching_count=1)
    assert len(first.events) == 5_140
    assert len(first.production) == 5_003
    assert len(first.nonproduction) == 137
    assert len(first.all_ids) == 5_140
    assert first.all_ids.isdisjoint(second.all_ids)
    assert {event["environment"] for event in first.production.values()} == {
        "production"
    }
    assert {event["environment"] for event in first.nonproduction.values()} == {
        "staging"
    }
    assert all(event["event_type"] == EVENT_TYPE for event in first.events)
    assert "5003" not in str(first.public_facts)


def test_dataset_readiness_requires_values_and_pagination() -> None:
    async def exercise() -> None:
        dataset = generate_search_dataset("trial", matching_count=2, nonmatching_count=1)

        class Search:
            async def execute(self, *_args, **_kwargs):
                return SearchResult(
                    query_id="q",
                    events=dataset.events,
                    pages=(
                        SearchPage(1, None, "token", 1, 1, 2),
                        SearchPage(2, "token", None, 1, 1, 1),
                    ),
                )

        result = await dataset.wait_until_ready(
            Search(), start_time=1, end_time=2, timeout_seconds=1
        )
        assert result.traversed_continuation

    asyncio.run(exercise())


def test_dataset_readiness_starts_fresh_query_after_transient_poll_failure() -> None:
    async def exercise() -> None:
        dataset = generate_search_dataset("trial", matching_count=2, nonmatching_count=1)

        class Search:
            calls = 0

            async def execute(self, *_args, **_kwargs):
                self.calls += 1
                if self.calls == 1:
                    raise SearchError(
                        "warming", query_id="failed-query", status_code=500
                    )
                return SearchResult(
                    query_id="successful-query",
                    events=dataset.events,
                    pages=(
                        SearchPage(1, None, "token", 1, 1, 2),
                        SearchPage(2, "token", None, 1, 1, 1),
                    ),
                )

        result = await dataset.wait_until_ready(
            Search(),
            start_time=1,
            end_time=2,
            timeout_seconds=1,
            retry_interval_seconds=0,
        )
        assert result.transient_failures == (
            {
                "attempt": 1,
                "status_code": 500,
                "query_id": "failed-query",
            },
        )

    asyncio.run(exercise())


def test_complete_single_page_readiness_has_distinct_growth_signal() -> None:
    async def exercise() -> None:
        dataset = generate_search_dataset(
            "single-page", matching_count=2, nonmatching_count=1
        )

        class Search:
            async def execute(self, *_args, **_kwargs):
                return SearchResult(
                    query_id="single-page-query",
                    events=dataset.events,
                    pages=(SearchPage(1, None, None, 1, 1, len(dataset.events)),),
                )

        with pytest.raises(PaginationNotObservedError) as raised:
            await dataset.wait_until_ready(
                Search(), start_time=1, end_time=2, timeout_seconds=1
            )
        assert raised.value.result.query_id == "single-page-query"
        assert raised.value.result.traversed_continuation is False

    asyncio.run(exercise())


def test_dataset_growth_preserves_exact_prefix_and_uses_bounded_targets() -> None:
    dataset = generate_search_dataset(
        "growth", matching_count=2, nonmatching_count=1
    )
    original_rows = {
        event_id: dict(event)
        for event_id, event in (*dataset.production.items(), *dataset.nonproduction.items())
    }

    grown, added = grow_search_dataset(dataset, 7)

    assert adaptive_event_targets(3, ceiling=12, growth_events=4) == (3, 7, 11, 12)
    assert len(dataset.events) == 3
    assert len(grown.events) == 7
    assert grown.events[:3] == dataset.events
    assert grown.events[3:] == added
    assert len(added) == 4
    assert len(grown.production) == 6
    assert grown.nonproduction == dataset.nonproduction
    assert all(event["environment"] == "production" for event in added)
    for event_id, expected in original_rows.items():
        actual = grown.production.get(event_id, grown.nonproduction.get(event_id))
        assert actual == expected
    assert grown.total_json_bytes == sum(
        len(json.dumps(event, separators=(",", ":")).encode("utf-8"))
        for event in grown.events
    )
