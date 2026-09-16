"""Independent paginated search reader and randomized export ground truth."""

from __future__ import annotations

import asyncio
import random
import secrets
import time
import uuid
from dataclasses import dataclass, replace
from typing import Any

import httpx

from .local_cli import ControlError, LocalCLI


DEFAULT_MATCHING_EVENTS = 5_003
DEFAULT_NONMATCHING_EVENTS = 137
DEFAULT_GROWTH_EVENTS = 5_000
MAX_FIXTURE_EVENTS = 25_000
MAX_FIXTURE_BYTES = 100 * 1024 * 1024
EVENT_TYPE = "LC_EVAL_EXPORT"


class SearchError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        query_id: str | None = None,
        status_code: int | None = None,
    ):
        super().__init__(message)
        self.query_id = query_id
        self.status_code = status_code


class DatasetReadinessError(RuntimeError):
    pass


class PaginationNotObservedError(DatasetReadinessError):
    """The complete, exact dataset was returned without a nonempty continuation."""

    def __init__(self, result: SearchResult):
        super().__init__(
            "all events are searchable but the search did not traverse pagination"
        )
        self.result = result


class PaginationFixtureUnsupportedError(DatasetReadinessError):
    """The bounded fixture ceiling was reached without proving pagination."""

    def __init__(self, fixture_event_count: int, result: SearchResult):
        super().__init__(
            f"pagination was not observed at the {fixture_event_count}-event fixture ceiling"
        )
        self.fixture_event_count = fixture_event_count
        self.result = result


def _service_root(value: str, *, suffix: str = "/v1") -> str:
    if not value:
        raise SearchError("organization URL mapping omitted the search service")
    root = value if value.startswith(("http://", "https://")) else f"https://{value}"
    root = root.rstrip("/")
    if not root.endswith(suffix):
        root += suffix
    return root


def _field_names(fields: Any) -> list[str]:
    if not isinstance(fields, list):
        return []
    names: list[str] = []
    for field in fields:
        if isinstance(field, str):
            names.append(field)
        elif isinstance(field, dict):
            name = field.get("name", field.get("field"))
            if not isinstance(name, str):
                return []
            names.append(name)
        else:
            return []
    return names


def normalize_event_row(row: Any, fields: Any = None) -> dict[str, Any]:
    """Normalize dict rows and positional rows described by ``fields``.

    Event search rows commonly wrap the source event in ``data``. Returning
    that source object gives graders one stable shape while leaving any
    unrecognized dictionary row intact.
    """
    if isinstance(row, dict):
        normalized = dict(row)
    elif isinstance(row, (list, tuple)):
        names = _field_names(fields)
        if len(names) != len(row):
            raise SearchError("search row does not match its fields declaration")
        normalized = dict(zip(names, row, strict=True))
    else:
        raise SearchError("search event row is neither an object nor a field array")

    # Search deployments have returned both ``{data: <event>}`` and
    # ``{data: {event: <event>, routing: ...}}``. Walk those known envelope
    # keys with a hard depth bound so another compatibility wrapper does not
    # leak into the verifier's event shape or create unbounded traversal.
    current = normalized
    for _ in range(8):
        if "eval_event_id" in current:
            return dict(current)
        data = current.get("data")
        if isinstance(data, dict):
            current = data
            continue
        event = current.get("event")
        if isinstance(event, dict):
            current = event
            continue
        return dict(current)
    raise SearchError("search event row exceeds the envelope nesting limit")


@dataclass(frozen=True, slots=True)
class SearchPage:
    page_number: int
    token_used: str | None
    next_token: str | None
    polls: int
    result_items: int
    event_rows: int


@dataclass(frozen=True, slots=True)
class SearchResult:
    query_id: str
    events: tuple[dict[str, Any], ...]
    pages: tuple[SearchPage, ...]
    transient_failures: tuple[dict[str, Any], ...] = ()

    @property
    def traversed_continuation(self) -> bool:
        return (
            len(self.pages) > 1
            and any(page.next_token for page in self.pages[:-1])
            and any(page.event_rows > 0 for page in self.pages[1:])
        )


class RegionalSearchClient:
    """Search through regional HTTP endpoints using evaluator-owned auth."""

    def __init__(
        self,
        cli: LocalCLI,
        oid: str,
        *,
        timeout_seconds: float = 600.0,
        poll_interval_seconds: float = 0.5,
    ):
        if timeout_seconds <= 0 or poll_interval_seconds < 0:
            raise ValueError("search timing bounds are invalid")
        self.cli = cli
        self.oid = oid
        self.timeout_seconds = timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds

    async def execute(
        self,
        query: str,
        start_time: int,
        end_time: int,
        *,
        stream: str = "event",
    ) -> SearchResult:
        return await asyncio.to_thread(self._execute_blocking, query, start_time, end_time, stream)

    def _execute_blocking(self, query: str, start_time: int, end_time: int, stream: str) -> SearchResult:
        urls = self.cli.get_urls(self.oid)
        root = _service_root(urls.get("search", urls.get("search_api", "")))
        request = {
            "oid": self.oid,
            "query": query,
            "startTime": str(int(start_time)),
            "endTime": str(int(end_time)),
            "paginated": True,
            "stream": stream,
        }
        response = self.cli.api(self.oid, "POST", "search", root=root, body=request, timeout=60)
        if not isinstance(response, dict) or response.get("error"):
            raise SearchError("search initiation failed")
        query_id = response.get("queryId", response.get("query_id"))
        if not isinstance(query_id, str) or not query_id:
            raise SearchError("search initiation omitted queryId")

        deadline = time.monotonic() + self.timeout_seconds
        events: list[dict[str, Any]] = []
        pages: list[SearchPage] = []
        token: str | None = None
        try:
            while True:
                token_used = token
                polls = 0
                page_items = 0
                page_rows = 0
                next_token: str | None = None
                while True:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(f"search {query_id} exceeded its deadline")
                    poll = self._poll_with_retry(
                        query_id,
                        root,
                        token_used,
                        deadline,
                    )
                    polls += 1
                    if not isinstance(poll, dict) or poll.get("error"):
                        raise SearchError("search poll failed")
                    results = poll.get("results", [])
                    if not isinstance(results, list):
                        raise SearchError("search poll results are not a list")
                    for item in results:
                        if not isinstance(item, dict):
                            raise SearchError("search result item is not an object")
                        page_items += 1
                        candidate_token = item.get("nextToken")
                        if candidate_token is not None:
                            if not isinstance(candidate_token, str) or not candidate_token:
                                raise SearchError("search nextToken is invalid")
                            next_token = candidate_token
                        if item.get("type") != "events":
                            continue
                        rows = item.get("rows") or []
                        if not isinstance(rows, list):
                            raise SearchError("search event rows are not a list")
                        for row in rows:
                            events.append(normalize_event_row(row, item.get("fields")))
                        page_rows += len(rows)
                    if poll.get("completed") is True:
                        break
                    delay_ms = poll.get("nextPollInMs", self.poll_interval_seconds * 1000)
                    try:
                        delay = max(float(delay_ms) / 1000, self.poll_interval_seconds)
                    except (TypeError, ValueError) as error:
                        raise SearchError("search poll delay is invalid") from error
                    time.sleep(min(delay, max(0, deadline - time.monotonic())))

                pages.append(
                    SearchPage(
                        page_number=len(pages) + 1,
                        token_used=token_used,
                        next_token=next_token,
                        polls=polls,
                        result_items=page_items,
                        event_rows=page_rows,
                    )
                )
                if next_token is None:
                    break
                if next_token == token_used:
                    raise SearchError("search returned a non-advancing continuation token")
                token = next_token
        finally:
            try:
                self.cli.api(
                    self.oid,
                    "DELETE",
                    f"search/{query_id}",
                    root=root,
                    timeout=30,
                )
            except Exception:
                pass
        return SearchResult(query_id=query_id, events=tuple(events), pages=tuple(pages))

    def _poll_with_retry(
        self,
        query_id: str,
        root: str,
        token: str | None,
        deadline: float,
        *,
        max_retries: int = 3,
    ) -> Any:
        """Retry only transient search poll failures with bounded backoff."""
        transient_statuses = {500, 502, 503, 504}
        for attempt in range(max_retries + 1):
            try:
                return self.cli.api(
                    self.oid,
                    "GET",
                    f"search/{query_id}",
                    root=root,
                    params={"token": token} if token else None,
                    timeout=min(60, max(1, int(deadline - time.monotonic()))),
                )
            except ControlError as error:
                retryable = error.status_code in transient_statuses
                if not retryable or attempt >= max_retries:
                    raise SearchError(
                        "search poll failed",
                        query_id=query_id,
                        status_code=error.status_code,
                    ) from error
            except (httpx.TransportError, TimeoutError, OSError) as error:
                if attempt >= max_retries:
                    raise SearchError("search poll transport failed", query_id=query_id) from error
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"search {query_id} exceeded its deadline")
            time.sleep(min(2**attempt, 30, remaining))
        raise AssertionError("unreachable search poll retry state")


@dataclass(frozen=True, slots=True)
class SearchDataset:
    trial_id: str
    events: tuple[dict[str, str], ...]
    production: dict[str, dict[str, str]]
    nonproduction: dict[str, dict[str, str]]
    total_json_bytes: int

    @property
    def expected_ids(self) -> frozenset[str]:
        return frozenset(self.production)

    @property
    def all_ids(self) -> frozenset[str]:
        return frozenset((*self.production, *self.nonproduction))

    @property
    def public_facts(self) -> dict[str, Any]:
        return {
            "eval_trial_id": self.trial_id,
            "event_type": EVENT_TYPE,
            "fields": ["eval_event_id", "environment", "message"],
        }

    def readiness_query(self) -> str:
        if "'" in self.trial_id:
            raise ValueError("trial_id cannot contain a single quote")
        return f"* | {EVENT_TYPE} | event/eval_trial_id == '{self.trial_id}'"

    async def wait_until_ready(
        self,
        search: RegionalSearchClient,
        *,
        start_time: int,
        end_time: int,
        timeout_seconds: float = 600.0,
        retry_interval_seconds: float = 2.0,
        require_pagination: bool = True,
        observer=None,
    ) -> SearchResult:
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        last_missing = len(self.events)
        transient_failures: list[dict[str, Any]] = []
        while True:
            try:
                result = await search.execute(self.readiness_query(), start_time, end_time, stream="event")
            except SearchError as error:
                if error.status_code not in {500, 502, 503, 504}:
                    raise
                transient_failures.append(
                    {
                        "attempt": len(transient_failures) + 1,
                        "status_code": error.status_code,
                        "query_id": error.query_id,
                    }
                )
                if observer:
                    observer({"state": "retrying", "transient_failures": transient_failures})
                remaining = deadline - asyncio.get_running_loop().time()
                if remaining <= 0:
                    raise DatasetReadinessError(
                        f"dataset readiness expired after {len(transient_failures)} transient search failures"
                    ) from error
                await asyncio.sleep(min(retry_interval_seconds, remaining))
                continue
            observed: dict[str, dict[str, Any]] = {}
            for event in result.events:
                event_id = event.get("eval_event_id")
                if isinstance(event_id, str):
                    observed[event_id] = event
            missing = self.all_ids - observed.keys()
            last_missing = len(missing)
            if observer:
                observer(
                    {
                        "state": "searchable" if not missing else "waiting",
                        "query_id": result.query_id,
                        "observed_count": len(observed),
                        "missing_count": last_missing,
                        "pages": len(result.pages),
                        "paginated": result.traversed_continuation,
                        "transient_failures": transient_failures,
                    }
                )
            if not missing:
                for event_id, expected in (*self.production.items(), *self.nonproduction.items()):
                    actual = observed[event_id]
                    for field in ("eval_event_id", "eval_trial_id", "event_type", "environment", "message"):
                        if actual.get(field) != expected[field]:
                            raise DatasetReadinessError(f"search event {event_id} has an unexpected {field}")
                if require_pagination and not result.traversed_continuation:
                    raise PaginationNotObservedError(
                        replace(result, transient_failures=tuple(transient_failures))
                    )
                return replace(result, transient_failures=tuple(transient_failures))
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise DatasetReadinessError(f"dataset readiness expired with {last_missing} events missing")
            await asyncio.sleep(min(retry_interval_seconds, remaining))


def generate_search_dataset(
    trial_id: str,
    *,
    matching_count: int = DEFAULT_MATCHING_EVENTS,
    nonmatching_count: int = DEFAULT_NONMATCHING_EVENTS,
) -> SearchDataset:
    total = matching_count + nonmatching_count
    if matching_count <= 0 or nonmatching_count < 0 or total > MAX_FIXTURE_EVENTS:
        raise ValueError("dataset event counts are outside fixture bounds")
    if not trial_id or len(trial_id) > 128 or "'" in trial_id:
        raise ValueError("trial_id is invalid for the readiness query")

    def new_event(environment: str, ordinal: int) -> dict[str, str]:
        event_id = str(uuid.uuid4())
        return {
            "eval_event_id": event_id,
            "eval_trial_id": trial_id,
            "event_type": EVENT_TYPE,
            "environment": environment,
            "message": f"lc-eval-{environment}-{ordinal}-{secrets.token_hex(8)}",
        }

    production_events = [new_event("production", index) for index in range(matching_count)]
    negative_events = [new_event("staging", index) for index in range(nonmatching_count)]
    events = [*production_events, *negative_events]
    random.SystemRandom().shuffle(events)
    # This conservative compact-JSON approximation is checked again by the
    # webhook sender using the exact serialized request bytes.
    import json

    total_json_bytes = sum(len(json.dumps(event, separators=(",", ":")).encode("utf-8")) for event in events)
    if total_json_bytes > MAX_FIXTURE_BYTES:
        raise ValueError("dataset exceeds the fixture byte ceiling")
    return SearchDataset(
        trial_id=trial_id,
        events=tuple(events),
        production={event["eval_event_id"]: event for event in production_events},
        nonproduction={event["eval_event_id"]: event for event in negative_events},
        total_json_bytes=total_json_bytes,
    )


def adaptive_event_targets(
    initial_event_count: int,
    *,
    ceiling: int = MAX_FIXTURE_EVENTS,
    growth_events: int = DEFAULT_GROWTH_EVENTS,
) -> tuple[int, ...]:
    """Return deterministic cumulative sizes, including the initial size and ceiling."""
    if (
        initial_event_count <= 0
        or ceiling < initial_event_count
        or ceiling > MAX_FIXTURE_EVENTS
        or growth_events <= 0
    ):
        raise ValueError("adaptive fixture bounds are invalid")
    targets = [initial_event_count]
    while targets[-1] < ceiling:
        targets.append(min(ceiling, targets[-1] + growth_events))
    return tuple(targets)


def grow_search_dataset(
    dataset: SearchDataset,
    target_event_count: int,
) -> tuple[SearchDataset, tuple[dict[str, str], ...]]:
    """Append random production events while preserving the existing exact prefix."""
    current_count = len(dataset.events)
    if target_event_count <= current_count or target_event_count > MAX_FIXTURE_EVENTS:
        raise ValueError("target event count is outside adaptive fixture bounds")

    existing_ids = set(dataset.all_ids)
    added: list[dict[str, str]] = []
    next_ordinal = len(dataset.production)
    while len(added) < target_event_count - current_count:
        event_id = str(uuid.uuid4())
        if event_id in existing_ids:
            continue
        existing_ids.add(event_id)
        ordinal = next_ordinal + len(added)
        added.append(
            {
                "eval_event_id": event_id,
                "eval_trial_id": dataset.trial_id,
                "event_type": EVENT_TYPE,
                "environment": "production",
                "message": (
                    f"lc-eval-production-{ordinal}-{secrets.token_hex(8)}"
                ),
            }
        )
    random.SystemRandom().shuffle(added)

    import json

    added_bytes = sum(
        len(json.dumps(event, separators=(",", ":")).encode("utf-8"))
        for event in added
    )
    total_json_bytes = dataset.total_json_bytes + added_bytes
    if total_json_bytes > MAX_FIXTURE_BYTES:
        raise ValueError("dataset exceeds the fixture byte ceiling")
    production = dict(dataset.production)
    production.update({event["eval_event_id"]: event for event in added})
    grown = SearchDataset(
        trial_id=dataset.trial_id,
        events=(*dataset.events, *added),
        production=production,
        nonproduction=dict(dataset.nonproduction),
        total_json_bytes=total_json_bytes,
    )
    return grown, tuple(added)
