from __future__ import annotations

import asyncio
import hashlib
import hmac
from pathlib import Path

from aiohttp import ClientSession

from lc_eval.receiver import (
    CloudflaredTunnel,
    LocalReceiverServer,
    ManagementClientError,
    ReceiverStore,
)


def test_local_server_and_management_client_use_separate_ports(tmp_path: Path) -> None:
    async def exercise() -> None:
        store = ReceiverStore(tmp_path / "receiver.sqlite3")
        async with LocalReceiverServer(store, "token") as server:
            assert server.ingest_port != server.management_port
            async with server.management_client as management:
                assert (await management.health())["status"] == "ok"
                await management.create_trial("trial", "secret")

                body = b'{"probe_id":"p1"}'
                signature = hmac.new(b"secret", body, hashlib.sha256).hexdigest()
                async with ClientSession() as session:
                    async with session.post(
                        f"{server.ingest_url}/v1/ingest/trial",
                        data=body,
                        headers={
                            "Content-Type": "application/json",
                            "lc-signature": signature,
                        },
                    ) as response:
                        assert response.status == 202

                receipts = await management.list_receipts("trial")
                assert receipts[0]["events"] == [{"probe_id": "p1"}]

            bad_client = server.management_client
            bad_client._token = "incorrect"
            try:
                try:
                    await bad_client.health()
                except ManagementClientError as error:
                    assert error.status == 401
                else:
                    raise AssertionError("bad management credential was accepted")
            finally:
                await bad_client.close()

    asyncio.run(exercise())


def test_local_server_refuses_non_loopback_management_listener(tmp_path: Path) -> None:
    store = ReceiverStore(tmp_path / "receiver.sqlite3")
    try:
        LocalReceiverServer(store, "token", management_host="0.0.0.0")
    except ValueError as error:
        assert "loopback" in str(error)
    else:
        raise AssertionError("non-loopback management listener was accepted")


def test_cloudflared_uses_supplied_executable_and_discovers_url(tmp_path: Path) -> None:
    async def exercise() -> None:
        executable = tmp_path / "cloudflared-pinned"
        executable.write_text(
            "#!/bin/sh\n"
            "echo 'INF Your quick Tunnel has been created! https://unit-test.trycloudflare.com' >&2\n"
            "trap 'exit 0' TERM INT\n"
            "while true; do sleep 1; done\n",
            encoding="utf-8",
        )
        executable.chmod(0o700)
        probed: list[str] = []

        async def probe(url: str) -> None:
            probed.append(url)

        tunnel = CloudflaredTunnel(
            executable,
            "http://127.0.0.1:43210",
            tmp_path / "isolated-cloudflared-config",
            startup_timeout_seconds=2,
            shutdown_grace_seconds=2,
            readiness_probe=probe,
        )
        url = await tunnel.start()
        pid = tunnel.pid
        assert url == "https://unit-test.trycloudflare.com"
        assert probed == [url]
        assert isinstance(pid, int)
        assert (tmp_path / "isolated-cloudflared-config" / "config.yml").is_file()
        await tunnel.stop()
        assert tunnel.pid is None

    asyncio.run(exercise())
