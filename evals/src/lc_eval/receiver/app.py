"""Public ingest and loopback management aiohttp applications."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from aiohttp import web

from .store import BucketExistsError, BucketNotFoundError, ReceiverStore


DEFAULT_MAX_PAYLOAD_BYTES = 2 * 1024 * 1024
DEFAULT_MAX_EVENTS = 10_000

STORE_KEY: web.AppKey[ReceiverStore] = web.AppKey("receiver_store", ReceiverStore)
MAX_PAYLOAD_KEY: web.AppKey[int] = web.AppKey("max_payload_bytes", int)
MAX_EVENTS_KEY: web.AppKey[int] = web.AppKey("max_events", int)
MANAGEMENT_TOKEN_DIGEST_KEY: web.AppKey[bytes] = web.AppKey(
    "management_token_digest", bytes
)


def _json_error(status: int, code: str, message: str) -> web.Response:
    return web.json_response({"error": code, "message": message}, status=status)


async def _read_bounded(request: web.Request, maximum: int) -> bytes:
    length = request.content_length
    if length is not None and length > maximum:
        raise web.HTTPRequestEntityTooLarge(max_size=maximum, actual_size=length)
    body = bytearray()
    async for chunk in request.content.iter_chunked(min(64 * 1024, maximum + 1)):
        body.extend(chunk)
        if len(body) > maximum:
            raise web.HTTPRequestEntityTooLarge(max_size=maximum, actual_size=len(body))
    return bytes(body)


def _as_events(value: Any, maximum: int) -> tuple[str, list[dict[str, Any]]]:
    if isinstance(value, dict):
        return "object", [value]
    if isinstance(value, list):
        if len(value) > maximum:
            raise ValueError(f"payload contains more than {maximum} events")
        if not all(isinstance(item, dict) for item in value):
            raise ValueError("JSON arrays must contain only objects")
        return "array", value
    raise ValueError("payload must be a JSON object, an array of objects, or JSONL")


def parse_payload(
    body: bytes, content_type: str, *, maximum_events: int
) -> tuple[str | None, list[dict[str, Any]], str | None]:
    """Parse JSON object/array/JSONL without altering the signed bytes."""
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as error:
        return None, [], f"payload is not UTF-8: {error}"

    media_type = content_type.partition(";")[0].strip().lower()
    jsonl_types = {"application/x-ndjson", "application/jsonl", "application/json-seq"}
    if media_type not in {"", "application/json", *jsonl_types} and not media_type.endswith(
        "+json"
    ):
        return None, [], f"unsupported content type: {media_type}"

    if media_type not in jsonl_types:
        try:
            return (*_as_events(json.loads(text), maximum_events), None)
        except json.JSONDecodeError:
            # Some webhook senders label JSONL as application/json. Try the
            # line-delimited form before recording the original parse failure.
            pass
        except ValueError as error:
            return None, [], str(error)

    events: list[dict[str, Any]] = []
    try:
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"JSONL line {line_number} is not an object")
            events.append(value)
            if len(events) > maximum_events:
                raise ValueError(f"payload contains more than {maximum_events} events")
        if not events:
            raise ValueError("payload contains no JSON events")
    except (json.JSONDecodeError, ValueError) as error:
        return None, [], str(error)
    return "jsonl", events, None


def _valid_signature(secret: bytes, body: bytes, supplied: str | None) -> bool:
    expected = hmac.digest(secret, body, "sha256")
    valid_hex = True
    try:
        candidate = bytes.fromhex(supplied or "")
        if len(candidate) != len(expected):
            valid_hex = False
            candidate = b"\x00" * len(expected)
    except ValueError:
        valid_hex = False
        candidate = b"\x00" * len(expected)
    return hmac.compare_digest(expected, candidate) and valid_hex


async def _public_health(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def _ingest(request: web.Request) -> web.Response:
    store = request.app[STORE_KEY]
    trial_id = request.match_info["trial_id"]
    try:
        secret = store.get_secret(trial_id)
    except (BucketNotFoundError, ValueError):
        return _json_error(404, "unknown_trial", "trial receipt bucket does not exist")

    try:
        body = await _read_bounded(request, request.app[MAX_PAYLOAD_KEY])
    except web.HTTPRequestEntityTooLarge as error:
        return _json_error(413, "payload_too_large", error.reason)

    signature = request.headers.get("lc-signature")
    signature_valid = _valid_signature(secret, body, signature)
    content_type = request.headers.get("Content-Type", "")
    payload_format, events, parse_error = parse_payload(
        body, content_type, maximum_events=request.app[MAX_EVENTS_KEY]
    )
    receipt = store.record_receipt(
        trial_id=trial_id,
        content_type=content_type,
        signature=signature,
        signature_valid=signature_valid,
        raw_body=body,
        payload_format=payload_format,
        events=events,
        parse_error=parse_error,
    )
    if not signature_valid:
        return _json_error(401, "invalid_signature", "lc-signature is invalid")
    if parse_error is not None:
        status = 415 if parse_error.startswith("unsupported content type") else 400
        return _json_error(status, "invalid_payload", parse_error)
    return web.json_response(
        {
            "status": "accepted",
            "receipt_id": receipt.receipt_id,
            "event_count": len(receipt.events),
            "duplicate_of": receipt.duplicate_of,
        },
        status=202,
    )


def create_ingest_app(
    store: ReceiverStore,
    *,
    max_payload_bytes: int = DEFAULT_MAX_PAYLOAD_BYTES,
    max_events: int = DEFAULT_MAX_EVENTS,
) -> web.Application:
    if max_payload_bytes <= 0 or max_events <= 0:
        raise ValueError("ingest limits must be positive")
    app = web.Application(
        client_max_size=max_payload_bytes + 1,
        handler_args={"auto_decompress": False},
    )
    app[STORE_KEY] = store
    app[MAX_PAYLOAD_KEY] = max_payload_bytes
    app[MAX_EVENTS_KEY] = max_events
    app.router.add_get("/healthz", _public_health)
    app.router.add_post("/v1/ingest/{trial_id}", _ingest)
    return app


def _presented_bearer(request: web.Request) -> bytes:
    authorization = request.headers.get("Authorization", "")
    scheme, separator, token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer":
        return b""
    return token.encode("utf-8")


@web.middleware
async def _management_auth(
    request: web.Request, handler: Any
) -> web.StreamResponse:
    presented_digest = hashlib.sha256(_presented_bearer(request)).digest()
    if not hmac.compare_digest(
        request.app[MANAGEMENT_TOKEN_DIGEST_KEY], presented_digest
    ):
        return _json_error(401, "unauthorized", "valid bearer token required")
    return await handler(request)


async def _management_health(request: web.Request) -> web.Response:
    return web.json_response(request.app[STORE_KEY].health())


async def _create_trial(request: web.Request) -> web.Response:
    try:
        body = await _read_bounded(request, 8192)
        value = json.loads(body)
        if not isinstance(value, dict) or set(value) != {"secret"}:
            raise ValueError("body must contain only a secret field")
        secret = value["secret"]
        if not isinstance(secret, str):
            raise ValueError("secret must be a string")
        bucket = request.app[STORE_KEY].create_trial(
            request.match_info["trial_id"], secret
        )
    except web.HTTPRequestEntityTooLarge as error:
        return _json_error(413, "payload_too_large", error.reason)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError, TypeError) as error:
        if isinstance(error, BucketExistsError):
            return _json_error(409, "trial_exists", "trial exists with another secret")
        return _json_error(400, "invalid_request", str(error))
    return web.json_response(bucket.to_dict(), status=201)


async def _get_trial(request: web.Request) -> web.Response:
    try:
        bucket = request.app[STORE_KEY].get_trial(request.match_info["trial_id"])
    except (BucketNotFoundError, ValueError):
        return _json_error(404, "unknown_trial", "trial receipt bucket does not exist")
    return web.json_response(bucket.to_dict())


async def _delete_trial(request: web.Request) -> web.Response:
    try:
        deleted = request.app[STORE_KEY].delete_trial(request.match_info["trial_id"])
    except ValueError:
        deleted = False
    if not deleted:
        return _json_error(404, "unknown_trial", "trial receipt bucket does not exist")
    return web.Response(status=204)


async def _list_receipts(request: web.Request) -> web.Response:
    try:
        after_id = int(request.query.get("after_receipt_id", "0"))
        limit = int(request.query.get("limit", "1000"))
        receipts = request.app[STORE_KEY].list_receipts(
            request.match_info["trial_id"],
            after_receipt_id=after_id,
            limit=limit,
        )
    except (ValueError, TypeError) as error:
        return _json_error(400, "invalid_query", str(error))
    except BucketNotFoundError:
        return _json_error(404, "unknown_trial", "trial receipt bucket does not exist")
    return web.json_response(
        {
            "receipts": [item.to_dict(include_body=True) for item in receipts],
            "count": len(receipts),
        }
    )


def create_management_app(
    store: ReceiverStore, management_token: str
) -> web.Application:
    if not isinstance(management_token, str) or not management_token:
        raise ValueError("management_token must be a non-empty string")
    app = web.Application(client_max_size=8192, middlewares=[_management_auth])
    app[STORE_KEY] = store
    app[MANAGEMENT_TOKEN_DIGEST_KEY] = hashlib.sha256(
        management_token.encode("utf-8")
    ).digest()
    app.router.add_get("/healthz", _management_health)
    app.router.add_put("/v1/trials/{trial_id}", _create_trial)
    app.router.add_get("/v1/trials/{trial_id}", _get_trial)
    app.router.add_delete("/v1/trials/{trial_id}", _delete_trial)
    app.router.add_get("/v1/trials/{trial_id}/receipts", _list_receipts)
    return app
