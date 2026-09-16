"""Small native-protocol model gateway for API-key budget enforcement.

Subscription credentials are intentionally unsupported: their local CLI auth
sessions are not interchangeable with provider API keys and their dollar spend
cannot be inferred by this service.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import partial
from urllib.parse import urljoin, urlsplit

from aiohttp import ClientError, ClientSession, ClientTimeout, web

from .budget import BudgetError, BudgetLedger


_LEDGER_KEY = web.AppKey("budget_ledger", BudgetLedger)
_CONFIG_KEY = web.AppKey("gateway_config", "GatewayConfig")


@dataclass(frozen=True)
class BillableUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_write_tokens": self.cache_write_tokens,
        }


@dataclass(frozen=True)
class ModelPricing:
    """Rates in integer micro-USD per one million tokens."""

    input_per_million: int
    output_per_million: int
    cache_read_per_million: int = 0
    cache_write_per_million: int = 0

    def __post_init__(self) -> None:
        if any(value < 0 for value in vars(self).values()):
            raise ValueError("model rates cannot be negative")
        if self.input_per_million == 0 or self.output_per_million == 0:
            raise ValueError("input and output rates must be positive")

    def conservative_cost(self, max_input_tokens: int, max_output_tokens: int) -> int:
        input_rate = max(
            self.input_per_million,
            self.cache_read_per_million,
            self.cache_write_per_million,
        )
        return _ceil_micro(max_input_tokens * input_rate + max_output_tokens * self.output_per_million)

    def cost(self, usage: BillableUsage) -> int:
        numerator = (
            usage.input_tokens * self.input_per_million
            + usage.output_tokens * self.output_per_million
            + usage.cache_read_tokens * self.cache_read_per_million
            + usage.cache_write_tokens * self.cache_write_per_million
        )
        return _ceil_micro(numerator) if numerator else 0


@dataclass(frozen=True)
class ModelLimits:
    context_tokens: int
    max_output_tokens: int

    def __post_init__(self) -> None:
        if self.context_tokens <= 0 or self.max_output_tokens <= 0:
            raise ValueError("model token limits must be positive")


@dataclass(frozen=True)
class UpstreamRoute:
    protocol: str
    inbound_path: str
    upstream_base_url: str
    upstream_path: str
    credential_ref: str
    allow_insecure_http: bool = False

    def __post_init__(self) -> None:
        if self.protocol not in {"anthropic", "responses"}:
            raise ValueError("protocol must be 'anthropic' or 'responses'")
        if not self.inbound_path.startswith("/") or not self.upstream_path.startswith("/"):
            raise ValueError("gateway paths must be absolute URL paths")
        if "?" in self.upstream_path or "#" in self.upstream_path:
            raise ValueError("upstream_path cannot contain a query or fragment")
        parsed = urlsplit(self.upstream_base_url)
        allowed_schemes = {"https"} | ({"http"} if self.allow_insecure_http else set())
        if parsed.scheme not in allowed_schemes or not parsed.netloc or parsed.query or parsed.fragment:
            raise ValueError("invalid fixed upstream base URL")

    @property
    def upstream_url(self) -> str:
        return urljoin(self.upstream_base_url.rstrip("/") + "/", self.upstream_path.lstrip("/"))


@dataclass(frozen=True)
class GatewayConfig:
    routes: Mapping[str, UpstreamRoute]
    pricing: Mapping[str, ModelPricing]
    limits: Mapping[str, ModelLimits]
    trial_tokens: Mapping[str, str]
    upstream_keys: Mapping[str, str] = field(repr=False)
    request_timeout_seconds: float = 600.0
    gateway_token_header: str = "X-LC-Eval-Gateway-Token"
    allowed_tool_types: frozenset[str] = frozenset({"function", "custom"})

    def __post_init__(self) -> None:
        if self.request_timeout_seconds <= 0:
            raise ValueError("request timeout must be positive")
        if not self.routes:
            raise ValueError("at least one fixed model route is required")
        for model, route in self.routes.items():
            if model not in self.pricing or model not in self.limits:
                raise ValueError(f"model {model!r} is missing pricing or limits")
            if route.credential_ref not in self.upstream_keys:
                raise ValueError(f"route for {model!r} is missing its upstream credential")
        paths = [route.inbound_path for route in self.routes.values()]
        if len(set(paths)) != len(paths):
            raise ValueError("each model route must have a unique inbound path")


class _UsageCapture:
    def __init__(self, protocol: str) -> None:
        self.protocol = protocol
        self.usage = BillableUsage()
        self.complete = False
        self._buffer = bytearray()

    def feed(self, chunk: bytes) -> None:
        self._buffer.extend(chunk)
        self._buffer = bytearray(bytes(self._buffer).replace(b"\r\n", b"\n"))
        while b"\n\n" in self._buffer:
            frame, _, remainder = self._buffer.partition(b"\n\n")
            self._buffer = bytearray(remainder)
            self._frame(bytes(frame))

    def finish_json(self, body: bytes) -> None:
        try:
            payload = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return
        if isinstance(payload, dict):
            self._payload(payload)
            response = payload.get("response") if isinstance(payload.get("response"), dict) else payload
            if isinstance(response, dict) and isinstance(response.get("usage"), dict):
                self.complete = True

    def _frame(self, frame: bytes) -> None:
        data_parts = []
        for line in frame.replace(b"\r\n", b"\n").split(b"\n"):
            if line.startswith(b"data:"):
                data_parts.append(line[5:].lstrip())
        if not data_parts:
            return
        data = b"\n".join(data_parts)
        if data == b"[DONE]":
            return
        try:
            payload = json.loads(data)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return
        if isinstance(payload, dict):
            self._payload(payload)

    def _payload(self, payload: Mapping[str, object]) -> None:
        if self.protocol == "anthropic":
            self._anthropic(payload)
        else:
            self._responses(payload)

    def _anthropic(self, payload: Mapping[str, object]) -> None:
        kind = payload.get("type")
        usage: object = payload.get("usage")
        if kind == "message_start" and isinstance(payload.get("message"), dict):
            usage = payload["message"].get("usage")
        if isinstance(usage, dict):
            self.usage = BillableUsage(
                input_tokens=max(self.usage.input_tokens, _token(usage.get("input_tokens"))),
                output_tokens=max(self.usage.output_tokens, _token(usage.get("output_tokens"))),
                cache_read_tokens=max(
                    self.usage.cache_read_tokens, _token(usage.get("cache_read_input_tokens"))
                ),
                cache_write_tokens=max(
                    self.usage.cache_write_tokens, _token(usage.get("cache_creation_input_tokens"))
                ),
            )
        if kind == "message_stop" or (kind is None and isinstance(payload.get("usage"), dict)):
            self.complete = True

    def _responses(self, payload: Mapping[str, object]) -> None:
        kind = payload.get("type")
        response = payload.get("response") if isinstance(payload.get("response"), dict) else payload
        usage = response.get("usage") if isinstance(response, dict) else None
        if isinstance(usage, dict):
            total_input = _token(usage.get("input_tokens"))
            details = usage.get("input_tokens_details")
            cached = _token(details.get("cached_tokens")) if isinstance(details, dict) else 0
            self.usage = BillableUsage(
                input_tokens=max(self.usage.input_tokens, max(0, total_input - cached)),
                output_tokens=max(self.usage.output_tokens, _token(usage.get("output_tokens"))),
                cache_read_tokens=max(self.usage.cache_read_tokens, cached),
                cache_write_tokens=self.usage.cache_write_tokens,
            )
        if kind == "response.completed" or (kind is None and isinstance(payload.get("usage"), dict)):
            self.complete = True


def create_gateway_app(ledger: BudgetLedger, config: GatewayConfig) -> web.Application:
    """Create an aiohttp application; callers own runner/site lifecycle."""
    app = web.Application()
    app[_LEDGER_KEY] = ledger
    app[_CONFIG_KEY] = config
    for model, route in config.routes.items():
        app.router.add_post(route.inbound_path, partial(_handler, route_model=model))
    return app


async def _handler(request: web.Request, *, route_model: str) -> web.StreamResponse:
    ledger = request.app[_LEDGER_KEY]
    config = request.app[_CONFIG_KEY]
    model = route_model
    route = config.routes[model]
    token = request.headers.get(config.gateway_token_header)
    trial_id = config.trial_tokens.get(token or "")
    if trial_id is None:
        raise web.HTTPUnauthorized(text="invalid gateway trial token")
    body = await request.read()
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise web.HTTPBadRequest(text="request body must be a JSON object") from exc
    if not isinstance(payload, dict):
        raise web.HTTPBadRequest(text="request body must be a JSON object")
    if payload.get("model") != model:
        raise web.HTTPForbidden(text="request model does not match the pinned route")
    _validate_tools(payload.get("tools"), config.allowed_tool_types, route.protocol)
    limits = config.limits[model]
    requested_output = payload.get("max_tokens") if route.protocol == "anthropic" else payload.get("max_output_tokens")
    if isinstance(requested_output, bool) or not isinstance(requested_output, int):
        raise web.HTTPBadRequest(text="a finite maximum output token limit is required")
    if requested_output <= 0 or requested_output > limits.max_output_tokens:
        raise web.HTTPBadRequest(text="maximum output token limit exceeds the configured bound")
    request_id = uuid.uuid4().hex
    reservation = config.pricing[model].conservative_cost(limits.context_tokens, requested_output)
    try:
        ledger.reserve(request_id, trial_id, model, reservation)
    except BudgetError as exc:
        raise web.HTTPPaymentRequired(text=str(exc)) from exc

    capture = _UsageCapture(route.protocol)
    response_started = False
    try:
        timeout = ClientTimeout(total=config.request_timeout_seconds)
        async with ClientSession(timeout=timeout) as session:
            async with session.post(
                route.upstream_url,
                data=body,
                headers=_upstream_headers(request.headers, route, config.upstream_keys[route.credential_ref]),
            ) as upstream:
                headers = _response_headers(upstream.headers)
                downstream = web.StreamResponse(status=upstream.status, headers=headers)
                await downstream.prepare(request)
                response_started = True
                collected = bytearray()
                is_sse = "text/event-stream" in upstream.headers.get("Content-Type", "")
                async for chunk in upstream.content.iter_chunked(64 * 1024):
                    if is_sse:
                        capture.feed(chunk)
                    else:
                        collected.extend(chunk)
                    await downstream.write(chunk)
                if not is_sse:
                    capture.finish_json(bytes(collected))
                await downstream.write_eof()
                if capture.complete:
                    ledger.settle(
                        request_id,
                        config.pricing[model].cost(capture.usage),
                        capture.usage.as_dict(),
                    )
                else:
                    ledger.mark_uncertain(request_id)
                return downstream
    except (ClientError, TimeoutError, ConnectionError):
        ledger.mark_uncertain(request_id)
        if response_started:
            raise
        raise web.HTTPBadGateway(text="upstream model request failed")
    except BaseException:
        ledger.mark_uncertain(request_id)
        raise


def _validate_tools(value: object, allowed: frozenset[str], protocol: str) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        raise web.HTTPBadRequest(text="tools must be an array")
    for tool in value:
        if not isinstance(tool, dict):
            raise web.HTTPBadRequest(text="unsupported or billable upstream tool type")
        tool_type = tool.get("type")
        # Anthropic's ordinary caller-provided tools have no type field. Its
        # provider-hosted tools use versioned type names and are billable or
        # otherwise outside this gateway's bounded accounting contract.
        if protocol == "anthropic" and tool_type is None and isinstance(tool.get("name"), str):
            continue
        if tool_type not in allowed:
            raise web.HTTPBadRequest(text="unsupported or billable upstream tool type")


def _upstream_headers(headers: Mapping[str, str], route: UpstreamRoute, key: str) -> dict[str, str]:
    allowed = {"content-type", "accept", "anthropic-version", "anthropic-beta", "openai-organization"}
    result = {name: value for name, value in headers.items() if name.lower() in allowed}
    if route.protocol == "anthropic":
        result["x-api-key"] = key
    else:
        result["Authorization"] = f"Bearer {key}"
    return result


def _response_headers(headers: Mapping[str, str]) -> dict[str, str]:
    excluded = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade", "content-length"}
    return {name: value for name, value in headers.items() if name.lower() not in excluded}


def _token(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


def _ceil_micro(rate_token_product: int) -> int:
    return (rate_token_product + 999_999) // 1_000_000
