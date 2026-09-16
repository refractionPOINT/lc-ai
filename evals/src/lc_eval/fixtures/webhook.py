"""Hosted JSON webhook provisioning and bounded event sender."""

from __future__ import annotations

import asyncio
import gzip
import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx

from .local_cli import ControlError, LocalCLI
from .search_dataset import MAX_FIXTURE_BYTES


DEFAULT_BATCH_EVENTS = 250
DEFAULT_MAX_BATCH_BYTES = 5 * 1024 * 1024


def build_webhook_config(
    *,
    oid: str,
    installation_key: str,
    ingest_secret: str,
    hostname: str,
    sensor_seed_key: str,
) -> dict[str, Any]:
    if not all((oid, installation_key, ingest_secret, hostname, sensor_seed_key)):
        raise ValueError("webhook configuration values must be non-empty")
    return {
        "sensor_type": "webhook",
        "webhook": {
            "secret": ingest_secret,
            "signature_secret": "",
            "signature_header": "",
            "signature_scheme": "",
            "client_options": {
                "hostname": hostname,
                "identity": {"oid": oid, "installation_key": installation_key},
                "platform": "json",
                "sensor_seed_key": sensor_seed_key,
                "mapping": {"event_type_path": "event_type"},
            },
        },
    }


def _normalize_service_url(value: str, service: str) -> str:
    if not value:
        raise ControlError(f"organization URL mapping omitted the {service} service")
    url = value if value.startswith(("http://", "https://")) else f"https://{value}"
    return url.rstrip("/")


@dataclass(frozen=True, slots=True)
class WebhookSpec:
    oid: str
    name: str
    installation_key: str
    ingest_secret: str
    hostname: str
    sensor_seed_key: str

    @property
    def public_config(self) -> dict[str, Any]:
        """Candidate-visible reference input using only trial-scoped values."""
        return build_webhook_config(
            oid=self.oid,
            installation_key=self.installation_key,
            ingest_secret=self.ingest_secret,
            hostname=self.hostname,
            sensor_seed_key=self.sensor_seed_key,
        )


@dataclass(frozen=True, slots=True)
class BatchReceipt:
    batch_number: int
    event_count: int
    uncompressed_bytes: int
    transmitted_bytes: int
    compressed: bool
    status_code: int


class HostedWebhookFixture:
    """Configure a hosted webhook with trusted CLI and verify through HTTP."""

    def __init__(self, cli: LocalCLI, spec: WebhookSpec):
        self.cli = cli
        self.spec = spec

    async def provision(self) -> dict[str, Any]:
        payload = json.dumps(self.spec.public_config, separators=(",", ":"))
        return await asyncio.to_thread(
            self.cli.invoke,
            ["cloud-adapter", "set", "--key", self.spec.name, "--enabled"],
            self.spec.oid,
            True,
            payload,
            90,
        )

    async def read(self) -> dict[str, Any]:
        path = (
            f"hive/cloud_sensor/{quote(self.spec.oid, safe='')}/"
            f"{quote(self.spec.name, safe='')}/data"
        )
        value = await asyncio.to_thread(
            self.cli.api, self.spec.oid, "GET", path
        )
        if not isinstance(value, dict):
            raise ControlError("cloud adapter Hive read returned no object")
        data = value.get("data")
        if isinstance(data, str):
            try:
                value = dict(value)
                value["data"] = json.loads(data)
            except json.JSONDecodeError as error:
                raise ControlError("cloud adapter Hive data is not JSON") from error
        return value

    async def delete(self) -> dict[str, Any]:
        return await asyncio.to_thread(
            self.cli.invoke,
            ["cloud-adapter", "delete", "--key", self.spec.name, "--confirm"],
            self.spec.oid,
            True,
            None,
            90,
        )

    async def hook_url(self) -> str:
        urls = await asyncio.to_thread(self.cli.get_urls, self.spec.oid)
        hooks = _normalize_service_url(
            urls.get("hooks", urls.get("hook", "")), "hooks"
        )
        return (
            f"{hooks}/{quote(self.spec.oid, safe='')}/"
            f"{quote(self.spec.name, safe='')}"
        )

    async def send_events(
        self,
        events: list[dict[str, Any]] | tuple[dict[str, Any], ...],
        *,
        batch_events: int = DEFAULT_BATCH_EVENTS,
        max_batch_bytes: int = DEFAULT_MAX_BATCH_BYTES,
        gzip_payload: bool = False,
        timeout_seconds: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ) -> list[BatchReceipt]:
        if not 1 <= batch_events <= 10_000:
            raise ValueError("batch_events must be between 1 and 10000")
        if max_batch_bytes <= 0 or timeout_seconds <= 0:
            raise ValueError("webhook send limits must be positive")
        url = await self.hook_url()
        own_client = client is None
        http = client or httpx.AsyncClient(timeout=timeout_seconds)
        receipts: list[BatchReceipt] = []
        total_bytes = 0
        try:
            for offset in range(0, len(events), batch_events):
                batch = events[offset : offset + batch_events]
                raw = json.dumps(
                    batch, separators=(",", ":"), ensure_ascii=False
                ).encode("utf-8")
                total_bytes += len(raw)
                if len(raw) > max_batch_bytes:
                    raise ValueError("serialized webhook batch exceeds max_batch_bytes")
                if total_bytes > MAX_FIXTURE_BYTES:
                    raise ValueError("webhook fixture exceeds its total byte ceiling")
                body = gzip.compress(raw, mtime=0) if gzip_payload else raw
                headers = {
                    "Content-Type": "application/json",
                    "lc-secret": self.spec.ingest_secret,
                }
                if gzip_payload:
                    headers["Content-Encoding"] = "gzip"
                response = await http.post(url, content=body, headers=headers)
                if not 200 <= response.status_code < 300:
                    raise ControlError(
                        f"hosted webhook rejected batch {len(receipts) + 1} "
                        f"with HTTP {response.status_code}"
                    )
                receipts.append(
                    BatchReceipt(
                        batch_number=len(receipts) + 1,
                        event_count=len(batch),
                        uncompressed_bytes=len(raw),
                        transmitted_bytes=len(body),
                        compressed=gzip_payload,
                        status_code=response.status_code,
                    )
                )
        finally:
            if own_client:
                await http.aclose()
        return receipts
