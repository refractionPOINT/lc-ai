from __future__ import annotations

import asyncio
import gzip
import json

import httpx

from lc_eval.fixtures.webhook import HostedWebhookFixture, WebhookSpec


class FakeCLI:
    def __init__(self) -> None:
        self.invocations: list[tuple] = []
        self.api_calls: list[tuple] = []

    def invoke(self, *args):
        self.invocations.append(args)
        return {"ok": True}

    def api(self, *args, **kwargs):
        self.api_calls.append((args, kwargs))
        return {
            "data": json.dumps({"sensor_type": "webhook"}),
            "usr_mtd": {"enabled": True},
        }

    def get_urls(self, oid: str):
        assert oid == "oid"
        return {"hooks": "hooks.example.test/"}


def _fixture(cli: FakeCLI) -> HostedWebhookFixture:
    return HostedWebhookFixture(
        cli,
        WebhookSpec(
            oid="oid",
            name="adapter name",
            installation_key="install-key",
            ingest_secret="ingest-secret",
            hostname="eval-host",
            sensor_seed_key="eval-seed",
        ),
    )


def test_webhook_provision_uses_trusted_cli_and_http_readback() -> None:
    async def exercise() -> None:
        cli = FakeCLI()
        fixture = _fixture(cli)
        await fixture.provision()
        command, oid, json_output, stdin, timeout = cli.invocations[0]
        assert command == [
            "cloud-adapter",
            "set",
            "--key",
            "adapter name",
            "--enabled",
        ]
        assert (oid, json_output, timeout) == ("oid", True, 90)
        config = json.loads(stdin)
        assert config["webhook"]["client_options"]["mapping"] == {
            "event_type_path": "event_type"
        }
        assert config["webhook"]["client_options"]["identity"] == {
            "oid": "oid",
            "installation_key": "install-key",
        }

        record = await fixture.read()
        assert record["data"] == {"sensor_type": "webhook"}
        assert cli.api_calls[0][0][1:] == (
            "GET",
            "hive/cloud_sensor/oid/adapter%20name/data",
        )

    asyncio.run(exercise())


def test_webhook_sends_bounded_gzip_batches_with_header_secret() -> None:
    async def exercise() -> None:
        seen: list[httpx.Request] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            return httpx.Response(202, request=request)

        cli = FakeCLI()
        fixture = _fixture(cli)
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            receipts = await fixture.send_events(
                [{"id": 1}, {"id": 2}, {"id": 3}],
                batch_events=2,
                gzip_payload=True,
                client=client,
            )
        assert [receipt.event_count for receipt in receipts] == [2, 1]
        assert all(receipt.compressed for receipt in receipts)
        assert seen[0].url == "https://hooks.example.test/oid/adapter%20name"
        assert seen[0].headers["lc-secret"] == "ingest-secret"
        assert seen[0].headers["content-encoding"] == "gzip"
        assert json.loads(gzip.decompress(seen[0].content)) == [{"id": 1}, {"id": 2}]

    asyncio.run(exercise())


def test_webhook_batches_by_exact_bytes_and_paces_across_calls(monkeypatch) -> None:
    async def exercise() -> None:
        seen: list[httpx.Request] = []
        sleeps: list[float] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            return httpx.Response(202, request=request)

        async def fake_sleep(delay: float) -> None:
            sleeps.append(delay)

        monkeypatch.setattr("lc_eval.fixtures.webhook.asyncio.sleep", fake_sleep)
        fixture = _fixture(FakeCLI())
        events = [{"id": index, "message": "x" * 48} for index in range(4)]
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            first = await fixture.send_events(
                events,
                batch_events=10,
                max_batch_bytes=80,
                bytes_per_second=1_000,
                client=client,
            )
            second = await fixture.send_events(
                [{"id": 5}], bytes_per_second=1_000, client=client
            )

        assert sum(receipt.event_count for receipt in first) == len(events)
        assert all(receipt.uncompressed_bytes <= 80 for receipt in first)
        assert len(first) == len(events)
        assert second[0].event_count == 1
        assert len(seen) == len(events) + 1
        assert sleeps and all(delay > 0 for delay in sleeps)

    asyncio.run(exercise())
