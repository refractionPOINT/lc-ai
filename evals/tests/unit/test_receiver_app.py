from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
from pathlib import Path

from aiohttp.test_utils import TestClient, TestServer

from lc_eval.receiver import ReceiverStore, create_ingest_app, create_management_app


def _signature(secret: bytes, body: bytes) -> str:
    return hmac.new(secret, body, hashlib.sha256).hexdigest()


def test_ingest_records_exact_body_and_detects_duplicate(tmp_path: Path) -> None:
    async def exercise() -> None:
        store = ReceiverStore(tmp_path / "receiver.sqlite3")
        store.create_trial("trial-1", b"receipt-secret")
        client = TestClient(TestServer(create_ingest_app(store)))
        await client.start_server()
        try:
            body = b'{"probe_id":"stale-or-fresh","value":1}\n'
            headers = {
                "Content-Type": "application/json",
                "lc-signature": _signature(b"receipt-secret", body),
            }
            first = await client.post("/v1/ingest/trial-1", data=body, headers=headers)
            assert first.status == 202
            first_value = await first.json()
            assert first_value["duplicate_of"] is None

            second = await client.post("/v1/ingest/trial-1", data=body, headers=headers)
            assert second.status == 202
            second_value = await second.json()
            assert second_value["duplicate_of"] == first_value["receipt_id"]

            receipts = ReceiverStore(tmp_path / "receiver.sqlite3").list_receipts(
                "trial-1"
            )
            assert len(receipts) == 2
            assert receipts[0].raw_body == body
            assert receipts[0].raw_sha256 == hashlib.sha256(body).hexdigest()
            assert receipts[0].events == (
                {"probe_id": "stale-or-fresh", "value": 1},
            )
            assert receipts[1].duplicate_of == receipts[0].receipt_id
        finally:
            await client.close()

    asyncio.run(exercise())


def test_signature_is_checked_against_exact_transmitted_bytes(tmp_path: Path) -> None:
    async def exercise() -> None:
        store = ReceiverStore(tmp_path / "receiver.sqlite3")
        secret = b"secret"
        store.create_trial("trial", secret)
        client = TestClient(TestServer(create_ingest_app(store)))
        await client.start_server()
        try:
            signed_body = b'{"ok":true}'
            transmitted_body = signed_body + b"\n"
            response = await client.post(
                "/v1/ingest/trial",
                data=transmitted_body,
                headers={
                    "Content-Type": "application/json",
                    "lc-signature": _signature(secret, signed_body),
                },
            )
            assert response.status == 401
            receipts = store.list_receipts("trial")
            assert len(receipts) == 1
            assert receipts[0].signature_valid is False
            assert receipts[0].raw_body == transmitted_body
            # Invalid authentication attempts remain evidence rather than being
            # confused with authenticated deliveries by a verifier.
            assert receipts[0].events == ({"ok": True},)
        finally:
            await client.close()

    asyncio.run(exercise())


def test_declared_json_array_and_jsonl_are_parsed(tmp_path: Path) -> None:
    async def exercise() -> None:
        store = ReceiverStore(tmp_path / "receiver.sqlite3")
        secret = b"secret"
        store.create_trial("trial", secret)
        client = TestClient(TestServer(create_ingest_app(store)))
        await client.start_server()
        try:
            payloads = [
                (b'[{"id":1},{"id":2}]', "application/json", "array"),
                (b'{"id":3}\n\n{"id":4}\n', "application/x-ndjson", "jsonl"),
                # LC-compatible senders sometimes label JSONL as JSON.
                (b'{"id":5}\n{"id":6}\n', "application/json", "jsonl"),
            ]
            for body, content_type, expected_format in payloads:
                response = await client.post(
                    "/v1/ingest/trial",
                    data=body,
                    headers={
                        "Content-Type": content_type,
                        "lc-signature": _signature(secret, body),
                    },
                )
                assert response.status == 202
                assert (await response.json())["event_count"] == 2

            receipts = store.list_receipts("trial")
            assert [receipt.payload_format for receipt in receipts] == [
                "array",
                "jsonl",
                "jsonl",
            ]
            assert [event["id"] for item in receipts for event in item.events] == [
                1,
                2,
                3,
                4,
                5,
                6,
            ]
        finally:
            await client.close()

    asyncio.run(exercise())


def test_invalid_json_is_persisted_before_error_response(tmp_path: Path) -> None:
    async def exercise() -> None:
        store = ReceiverStore(tmp_path / "receiver.sqlite3")
        secret = b"secret"
        store.create_trial("trial", secret)
        client = TestClient(TestServer(create_ingest_app(store)))
        await client.start_server()
        try:
            body = b"{invalid"
            response = await client.post(
                "/v1/ingest/trial",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "lc-signature": _signature(secret, body),
                },
            )
            assert response.status == 400
            receipt = store.list_receipts("trial")[0]
            assert receipt.signature_valid is True
            assert receipt.parse_error
            assert receipt.raw_body == body
        finally:
            await client.close()

    asyncio.run(exercise())


def test_payload_bound_rejects_without_partial_receipt(tmp_path: Path) -> None:
    async def exercise() -> None:
        store = ReceiverStore(tmp_path / "receiver.sqlite3")
        store.create_trial("trial", b"secret")
        client = TestClient(
            TestServer(create_ingest_app(store, max_payload_bytes=8))
        )
        await client.start_server()
        try:
            body = b'{"long":true}'
            response = await client.post(
                "/v1/ingest/trial",
                data=body,
                headers={"lc-signature": _signature(b"secret", body)},
            )
            assert response.status == 413
            assert store.list_receipts("trial") == []
        finally:
            await client.close()

    asyncio.run(exercise())


def test_management_is_authenticated_and_returns_full_receipt(tmp_path: Path) -> None:
    async def exercise() -> None:
        store = ReceiverStore(tmp_path / "receiver.sqlite3")
        management = TestClient(
            TestServer(create_management_app(store, "management-token"))
        )
        ingest = TestClient(TestServer(create_ingest_app(store)))
        await management.start_server()
        await ingest.start_server()
        auth = {"Authorization": "Bearer management-token"}
        try:
            denied = await management.get("/healthz")
            assert denied.status == 401

            created = await management.put(
                "/v1/trials/trial", json={"secret": "secret"}, headers=auth
            )
            assert created.status == 201
            health = await management.get("/healthz", headers=auth)
            assert health.status == 200
            assert (await health.json())["bucket_count"] == 1

            body = b'{"probe_id":"old-but-retained"}'
            accepted = await ingest.post(
                "/v1/ingest/trial",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "lc-signature": _signature(b"secret", body),
                },
            )
            assert accepted.status == 202

            response = await management.get(
                "/v1/trials/trial/receipts", headers=auth
            )
            value = await response.json()
            assert value["count"] == 1
            assert base64.b64decode(value["receipts"][0]["raw_body_base64"]) == body
            assert value["receipts"][0]["events"] == [
                {"probe_id": "old-but-retained"}
            ]

            deleted = await management.delete("/v1/trials/trial", headers=auth)
            assert deleted.status == 204
            assert store.health()["receipt_count"] == 0
        finally:
            await ingest.close()
            await management.close()

    asyncio.run(exercise())


def test_ingest_route_rejects_get_and_unknown_trials(tmp_path: Path) -> None:
    async def exercise() -> None:
        store = ReceiverStore(tmp_path / "receiver.sqlite3")
        client = TestClient(TestServer(create_ingest_app(store)))
        await client.start_server()
        try:
            assert (await client.get("/v1/ingest/unknown")).status == 405
            assert (await client.post("/v1/ingest/unknown", data=b"{}")).status == 404
            assert (await client.get("/healthz")).status == 200
        finally:
            await client.close()

    asyncio.run(exercise())
