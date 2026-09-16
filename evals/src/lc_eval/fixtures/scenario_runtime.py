"""Glue between independent fixture primitives and controller evidence contracts."""

from __future__ import annotations
import asyncio
from dataclasses import asdict
import json
import secrets
import time

from ..config import atomic_json
from .local_cli import ControlError
from .organization import unwrap
from .hive import snapshot
from .webhook import WebhookSpec, HostedWebhookFixture
from .search_dataset import generate_search_dataset, RegionalSearchClient


def installation_key(cli, oid, trial):
    raw = unwrap(cli.invoke(["installation-key", "create", "--description", "eval-" + trial, "--get"], oid))
    # The CLI returns both ``key`` (the binary RPCM key for native sensors)
    # and ``json_key`` (the JSON key accepted by adapters).  Supplying the
    # binary form to a hosted adapter provisions the record successfully but
    # leaves it unable to enroll, with "installation key not authorized".
    value = raw.get("json_key") if isinstance(raw, dict) else None
    if not value:
        raise ControlError("installation key response missing adapter json_key")
    return value


async def provision(config, cli, oid, trial, name, seed, root):
    if name == "webhook-production-routing":
        from .routing import provision as routing_provision

        return await routing_provision(config, cli, oid, trial, seed, root)
    key = installation_key(cli, oid, trial)
    hook = HostedWebhookFixture(
        cli,
        WebhookSpec(
            oid, "export-" + trial[-10:], key, secrets.token_hex(24), "eval-export", secrets.token_hex(12)
        ),
    )
    await hook.provision()
    dataset = generate_search_dataset(trial)
    atomic_json(
        root / "injected-events.json",
        {"events": dataset.events, "total_json_bytes": dataset.total_json_bytes},
    )
    start = int(time.time()) - 120
    deadline = time.monotonic() + config.limits.verification_seconds
    while True:
        try:
            # Initial readiness event; it does not belong to the scored dataset.
            await hook.send_events([{"event_type": "LC_EVAL_READY", "eval_trial_id": trial}])
            break
        except ControlError:
            if time.monotonic() >= deadline:
                raise
            await asyncio.sleep(3)
    receipts = await hook.send_events(dataset.events)
    atomic_json(root / "injection-receipts.json", [asdict(receipt) for receipt in receipts])
    end = int(time.time()) + 60
    search = RegionalSearchClient(cli, oid, timeout_seconds=config.limits.verification_seconds)
    ready = await dataset.wait_until_ready(
        search,
        start_time=start,
        end_time=end,
        timeout_seconds=config.limits.verification_seconds,
        observer=lambda value: atomic_json(root / "readiness.json", value),
    )
    expected = {
        event_id: {k: row[k] for k in ("eval_event_id", "environment", "message")}
        for event_id, row in dataset.production.items()
    }
    baseline = {
        "cloud_sensor": snapshot(cli, oid, "cloud_sensor"),
        "dr-general": snapshot(cli, oid, "dr-general"),
        "outputs": cli.api(oid, "GET", f"outputs/{oid}"),
    }
    return {
        "expected_rows": expected,
        "platform_state_before": baseline,
        "search_readiness": {
            "pages": [asdict(p) for p in ready.pages],
            "event_count": len(ready.events),
            "paginated": ready.traversed_continuation,
            "transient_failures": list(ready.transient_failures),
        },
        "public": {"organization_id": oid, "window_start": start, "window_end": end, "trial_selector": trial},
        "_hook": hook,
    }


async def collect(config, cli, oid, name, fixture):
    if name == "webhook-production-routing":
        from .routing import collect as routing_collect

        return await routing_collect(config, cli, oid, fixture)
    return {
        "platform_state_after": {
            "cloud_sensor": snapshot(cli, oid, "cloud_sensor"),
            "dr-general": snapshot(cli, oid, "dr-general"),
            "outputs": cli.api(oid, "GET", f"outputs/{oid}"),
        }
    }


async def reference(name, fixture, env, *, bad=False):
    if name == "webhook-production-routing":
        from .routing import reference as routing_reference

        return await routing_reference(fixture, env, bad=bad)
    # Reference independently exercises the candidate CLI's complete result stream,
    # then projects only the requested event fields; it does not copy hidden truth.
    from ..execution.docker import run

    public = fixture["public"]
    query = f"* | LC_EVAL_EXPORT | event/eval_trial_id == '{public['trial_selector']}' and event/environment == 'production'"
    raw = await asyncio.to_thread(
        run,
        [
            "docker",
            "exec",
            env.agent,
            "limacharlie",
            "--output",
            "json",
            "search",
            "run",
            "--query",
            query,
            "--start",
            str(public["window_start"]),
            "--end",
            str(public["window_end"]),
            "--stream",
            "event",
        ],
        timeout=600,
    )
    from .local_cli import decode_json

    data = decode_json(raw)
    from .search_dataset import normalize_event_row

    def event_rows(value):
        if isinstance(value, list):
            for item in value:
                yield from event_rows(item)
            return
        if not isinstance(value, dict):
            raise ControlError("search JSON output contains a non-object item")
        if "type" in value:
            if value.get("type") != "events":
                return
            rows = value.get("rows") or []
            if not isinstance(rows, list):
                raise ControlError("search event result rows are not a list")
            for row in rows:
                yield normalize_event_row(row, value.get("fields"))
            return
        for key in ("results", "events"):
            if key in value:
                rows = value[key]
                if not isinstance(rows, list):
                    raise ControlError(f"search JSON {key} value is not a list")
                for row in rows:
                    yield from event_rows(row)
                return
        yield normalize_event_row(value)

    normalized = {}
    for row in event_rows(data):
        event = row.get("event", row)
        if not isinstance(event, dict):
            raise ControlError("search event payload is not an object")
        event_id = event.get("eval_event_id")
        if not isinstance(event_id, str):
            raise ControlError("search event omitted eval_event_id")
        normalized[event["eval_event_id"]] = {
            k: event[k] for k in ("eval_event_id", "environment", "message")
        }
    (env.work / "export.jsonl").write_text("".join(json.dumps(row) + "\n" for row in normalized.values()))
    if bad:
        lines = (env.work / "export.jsonl").read_text().splitlines(keepends=True)
        (env.work / "export.jsonl").write_text("".join(lines[:1]))
    return f"Exported {len(normalized)} events"
