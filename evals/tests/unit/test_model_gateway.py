from __future__ import annotations

import json

import aiohttp
import pytest
from aiohttp import web

from lc_eval.execution.budget import BudgetLedger
from lc_eval.execution.model_gateway import (
    GatewayConfig,
    ModelLimits,
    ModelPricing,
    UpstreamRoute,
    create_gateway_app,
)


async def start_app(app: web.Application) -> tuple[web.AppRunner, str]:
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    sockets = site._server.sockets  # type: ignore[union-attr]
    return runner, f"http://127.0.0.1:{sockets[0].getsockname()[1]}"


def setup_ledger(tmp_path) -> BudgetLedger:
    ledger = BudgetLedger(tmp_path / "budget.sqlite")
    ledger.create_campaign("campaign", 10_000)
    ledger.create_trial("trial", "campaign", 10_000, ["fixed-model"])
    return ledger


@pytest.mark.asyncio
async def test_anthropic_sse_is_forwarded_exactly_and_settled(tmp_path) -> None:
    ledger = setup_ledger(tmp_path)
    seen: dict[str, object] = {}

    async def upstream(request: web.Request) -> web.StreamResponse:
        seen["body"] = await request.read()
        seen["key"] = request.headers.get("x-api-key")
        # The reservation exists before the gateway starts upstream I/O.
        seen["reserved"] = ledger.trial_snapshot("trial").reserved_micro_usd
        response = web.StreamResponse(headers={"Content-Type": "text/event-stream"})
        await response.prepare(request)
        frames = [
            {"type": "message_start", "message": {"usage": {"input_tokens": 4}}},
            {"type": "message_delta", "usage": {"output_tokens": 3}},
            # Duplicate cumulative usage must not be summed.
            {"type": "message_delta", "usage": {"output_tokens": 3}},
            {"type": "message_stop"},
        ]
        wire = b"".join(b"data: " + json.dumps(frame).encode() + b"\n\n" for frame in frames)
        await response.write(wire[:17])
        await response.write(wire[17:])
        await response.write_eof()
        return response

    upstream_app = web.Application()
    upstream_app.router.add_post("/v1/messages", upstream)
    upstream_runner, upstream_url = await start_app(upstream_app)
    body = b'{"model":"fixed-model","max_tokens":5,"messages":[{"role":"user","content":"hi"}]}'
    route = UpstreamRoute(
        protocol="anthropic",
        inbound_path="/v1/messages",
        upstream_base_url=upstream_url,
        upstream_path="/v1/messages",
        credential_ref="anthropic-key",
        allow_insecure_http=True,
    )
    gateway = create_gateway_app(
        ledger,
        GatewayConfig(
            routes={"fixed-model": route},
            pricing={"fixed-model": ModelPricing(1_000_000, 1_000_000)},
            limits={"fixed-model": ModelLimits(100, 10)},
            trial_tokens={"candidate-token": "trial"},
            upstream_keys={"anthropic-key": "secret-upstream-key"},
        ),
    )
    gateway_runner, gateway_url = await start_app(gateway)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                gateway_url + "/v1/messages",
                data=body,
                headers={
                    "content-type": "application/json",
                    "x-api-key": "candidate-must-not-control-this",
                    "X-LC-Eval-Gateway-Token": "candidate-token",
                },
            ) as response:
                assert response.status == 200
                assert "message_stop" in await response.text()
        assert seen["body"] == body
        assert seen["key"] == "secret-upstream-key"
        assert seen["reserved"] == 105
        snapshot = ledger.trial_snapshot("trial")
        assert snapshot.reserved_micro_usd == 0
        assert snapshot.settled_micro_usd == 7
    finally:
        await gateway_runner.cleanup()
        await upstream_runner.cleanup()


@pytest.mark.asyncio
async def test_missing_final_usage_keeps_full_reservation(tmp_path) -> None:
    ledger = setup_ledger(tmp_path)

    async def upstream(request: web.Request) -> web.StreamResponse:
        response = web.StreamResponse(headers={"Content-Type": "text/event-stream"})
        await response.prepare(request)
        await response.write(b'data: {"type":"response.output_text.delta","delta":"hi"}\n\n')
        await response.write_eof()
        return response

    upstream_app = web.Application()
    upstream_app.router.add_post("/v1/responses", upstream)
    upstream_runner, upstream_url = await start_app(upstream_app)
    route = UpstreamRoute(
        protocol="responses",
        inbound_path="/v1/responses",
        upstream_base_url=upstream_url,
        upstream_path="/v1/responses",
        credential_ref="openai-key",
        allow_insecure_http=True,
    )
    gateway_runner, gateway_url = await start_app(
        create_gateway_app(
            ledger,
            GatewayConfig(
                routes={"fixed-model": route},
                pricing={"fixed-model": ModelPricing(1_000_000, 2_000_000)},
                limits={"fixed-model": ModelLimits(100, 10)},
                trial_tokens={"candidate-token": "trial"},
                upstream_keys={"openai-key": "secret"},
            ),
        )
    )
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                gateway_url + "/v1/responses",
                json={"model": "fixed-model", "max_output_tokens": 5, "input": "hi"},
                headers={"X-LC-Eval-Gateway-Token": "candidate-token"},
            ) as response:
                assert response.status == 200
                await response.read()
        snapshot = ledger.trial_snapshot("trial")
        assert snapshot.settled_micro_usd == 0
        assert snapshot.reserved_micro_usd == 110
    finally:
        await gateway_runner.cleanup()
        await upstream_runner.cleanup()


@pytest.mark.asyncio
async def test_rejects_unpinned_model_and_billable_tools_before_upstream(tmp_path) -> None:
    ledger = setup_ledger(tmp_path)
    calls = 0

    async def upstream(request: web.Request) -> web.Response:
        nonlocal calls
        calls += 1
        return web.json_response({"usage": {"input_tokens": 1, "output_tokens": 1}})

    upstream_app = web.Application()
    upstream_app.router.add_post("/v1/responses", upstream)
    upstream_runner, upstream_url = await start_app(upstream_app)
    route = UpstreamRoute(
        protocol="responses",
        inbound_path="/v1/responses",
        upstream_base_url=upstream_url,
        upstream_path="/v1/responses",
        credential_ref="key",
        allow_insecure_http=True,
    )
    gateway_runner, gateway_url = await start_app(
        create_gateway_app(
            ledger,
            GatewayConfig(
                routes={"fixed-model": route},
                pricing={"fixed-model": ModelPricing(1, 1)},
                limits={"fixed-model": ModelLimits(100, 10)},
                trial_tokens={"candidate-token": "trial"},
                upstream_keys={"key": "secret"},
            ),
        )
    )
    try:
        headers = {"X-LC-Eval-Gateway-Token": "candidate-token"}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                gateway_url + "/v1/responses",
                json={"model": "other", "max_output_tokens": 5},
                headers=headers,
            ) as response:
                assert response.status == 403
            async with session.post(
                gateway_url + "/v1/responses",
                json={
                    "model": "fixed-model",
                    "max_output_tokens": 5,
                    "tools": [{"type": "web_search_preview"}],
                },
                headers=headers,
            ) as response:
                assert response.status == 400
        assert calls == 0
        assert ledger.trial_snapshot("trial").reserved_micro_usd == 0
    finally:
        await gateway_runner.cleanup()
        await upstream_runner.cleanup()
