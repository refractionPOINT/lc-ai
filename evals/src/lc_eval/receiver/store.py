"""SQLite journal for receiver buckets and webhook delivery attempts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_TRIAL_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._~-]{0,127}\Z")


class BucketNotFoundError(KeyError):
    """The requested trial bucket does not exist."""


class BucketExistsError(ValueError):
    """The requested trial bucket exists with a different secret."""


def validate_trial_id(trial_id: str) -> str:
    """Validate an opaque, URL-safe trial identifier."""
    if not isinstance(trial_id, str) or not _TRIAL_ID_RE.fullmatch(trial_id):
        raise ValueError("trial_id must be a URL-safe string of 1 to 128 characters")
    return trial_id


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


@dataclass(frozen=True, slots=True)
class TrialBucket:
    trial_id: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {"trial_id": self.trial_id, "created_at": self.created_at}


@dataclass(frozen=True, slots=True)
class Receipt:
    receipt_id: int
    trial_id: str
    received_at: str
    content_type: str
    signature: str | None
    signature_valid: bool
    raw_sha256: str
    raw_body: bytes
    payload_format: str | None
    events: tuple[dict[str, Any], ...]
    parse_error: str | None
    duplicate_of: int | None

    def to_dict(
        self,
        *,
        include_body: bool = False,
        include_events: bool = True,
    ) -> dict[str, Any]:
        import base64

        value: dict[str, Any] = {
            "receipt_id": self.receipt_id,
            "trial_id": self.trial_id,
            "received_at": self.received_at,
            "content_type": self.content_type,
            "signature": self.signature,
            "signature_valid": self.signature_valid,
            "raw_sha256": self.raw_sha256,
            "raw_size": len(self.raw_body),
            "payload_format": self.payload_format,
            "event_count": len(self.events),
            "parse_error": self.parse_error,
            "duplicate_of": self.duplicate_of,
        }
        if include_events:
            value["events"] = list(self.events)
        if include_body:
            value["raw_body_base64"] = base64.b64encode(self.raw_body).decode("ascii")
        return value


class ReceiverStore:
    """A small durable receipt store using one SQLite transaction per operation.

    The store intentionally performs no freshness filtering. A verifier can select
    a trial-specific observation window from the recorded ``received_at`` values.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = FULL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS trial_buckets (
                    trial_id TEXT PRIMARY KEY,
                    secret BLOB NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS receipts (
                    receipt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trial_id TEXT NOT NULL REFERENCES trial_buckets(trial_id)
                        ON DELETE CASCADE,
                    received_at TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    signature TEXT,
                    signature_valid INTEGER NOT NULL CHECK(signature_valid IN (0, 1)),
                    raw_sha256 TEXT NOT NULL,
                    raw_body BLOB NOT NULL,
                    payload_format TEXT,
                    events_json TEXT NOT NULL,
                    parse_error TEXT,
                    duplicate_of INTEGER REFERENCES receipts(receipt_id)
                );

                CREATE INDEX IF NOT EXISTS receipts_by_trial
                    ON receipts(trial_id, receipt_id);
                CREATE INDEX IF NOT EXISTS receipts_by_digest
                    ON receipts(trial_id, raw_sha256, receipt_id);
                """
            )
        os.chmod(self.path, 0o600)

    @staticmethod
    def _secret_bytes(secret: str | bytes) -> bytes:
        if isinstance(secret, str):
            value = secret.encode("utf-8")
        elif isinstance(secret, bytes):
            value = secret
        else:
            raise TypeError("secret must be str or bytes")
        if not value or len(value) > 4096:
            raise ValueError("secret must contain between 1 and 4096 bytes")
        return value

    def create_trial(self, trial_id: str, secret: str | bytes) -> TrialBucket:
        trial_id = validate_trial_id(trial_id)
        secret_bytes = self._secret_bytes(secret)
        created_at = _utc_now()
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT secret, created_at FROM trial_buckets WHERE trial_id = ?",
                (trial_id,),
            ).fetchone()
            if existing is not None:
                if bytes(existing["secret"]) != secret_bytes:
                    raise BucketExistsError(trial_id)
                return TrialBucket(trial_id=trial_id, created_at=existing["created_at"])
            connection.execute(
                "INSERT INTO trial_buckets(trial_id, secret, created_at) VALUES (?, ?, ?)",
                (trial_id, secret_bytes, created_at),
            )
        return TrialBucket(trial_id=trial_id, created_at=created_at)

    create_bucket = create_trial

    def get_trial(self, trial_id: str) -> TrialBucket:
        trial_id = validate_trial_id(trial_id)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT trial_id, created_at FROM trial_buckets WHERE trial_id = ?",
                (trial_id,),
            ).fetchone()
        if row is None:
            raise BucketNotFoundError(trial_id)
        return TrialBucket(trial_id=row["trial_id"], created_at=row["created_at"])

    get_bucket = get_trial

    def get_secret(self, trial_id: str) -> bytes:
        trial_id = validate_trial_id(trial_id)
        with self._connect() as connection:
            row = connection.execute(
                "SELECT secret FROM trial_buckets WHERE trial_id = ?", (trial_id,)
            ).fetchone()
        if row is None:
            raise BucketNotFoundError(trial_id)
        return bytes(row["secret"])

    def delete_trial(self, trial_id: str) -> bool:
        trial_id = validate_trial_id(trial_id)
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM trial_buckets WHERE trial_id = ?", (trial_id,)
            )
        return cursor.rowcount > 0

    delete_bucket = delete_trial

    def record_receipt(
        self,
        *,
        trial_id: str,
        content_type: str,
        signature: str | None,
        signature_valid: bool,
        raw_body: bytes,
        payload_format: str | None,
        events: list[dict[str, Any]] | tuple[dict[str, Any], ...],
        parse_error: str | None,
        received_at: str | None = None,
    ) -> Receipt:
        trial_id = validate_trial_id(trial_id)
        digest = hashlib.sha256(raw_body).hexdigest()
        event_tuple = tuple(events)
        events_json = json.dumps(event_tuple, separators=(",", ":"), ensure_ascii=False)
        received_at = received_at or _utc_now()

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if connection.execute(
                "SELECT 1 FROM trial_buckets WHERE trial_id = ?", (trial_id,)
            ).fetchone() is None:
                raise BucketNotFoundError(trial_id)
            candidates = connection.execute(
                """
                SELECT receipt_id, raw_body FROM receipts
                WHERE trial_id = ? AND raw_sha256 = ?
                ORDER BY receipt_id LIMIT 1
                """,
                (trial_id, digest),
            ).fetchall()
            duplicate_of = next(
                (
                    int(row["receipt_id"])
                    for row in candidates
                    if bytes(row["raw_body"]) == raw_body
                ),
                None,
            )
            cursor = connection.execute(
                """
                INSERT INTO receipts(
                    trial_id, received_at, content_type, signature,
                    signature_valid, raw_sha256, raw_body, payload_format,
                    events_json, parse_error, duplicate_of
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trial_id,
                    received_at,
                    content_type,
                    signature,
                    int(signature_valid),
                    digest,
                    raw_body,
                    payload_format,
                    events_json,
                    parse_error,
                    duplicate_of,
                ),
            )
            receipt_id = int(cursor.lastrowid)

        return Receipt(
            receipt_id=receipt_id,
            trial_id=trial_id,
            received_at=received_at,
            content_type=content_type,
            signature=signature,
            signature_valid=signature_valid,
            raw_sha256=digest,
            raw_body=raw_body,
            payload_format=payload_format,
            events=event_tuple,
            parse_error=parse_error,
            duplicate_of=duplicate_of,
        )

    @staticmethod
    def _receipt_from_row(row: sqlite3.Row) -> Receipt:
        events = json.loads(row["events_json"])
        return Receipt(
            receipt_id=int(row["receipt_id"]),
            trial_id=row["trial_id"],
            received_at=row["received_at"],
            content_type=row["content_type"],
            signature=row["signature"],
            signature_valid=bool(row["signature_valid"]),
            raw_sha256=row["raw_sha256"],
            raw_body=bytes(row["raw_body"]),
            payload_format=row["payload_format"],
            events=tuple(events),
            parse_error=row["parse_error"],
            duplicate_of=row["duplicate_of"],
        )

    def list_receipts(
        self,
        trial_id: str,
        *,
        after_receipt_id: int = 0,
        limit: int = 1000,
    ) -> list[Receipt]:
        trial_id = validate_trial_id(trial_id)
        if after_receipt_id < 0:
            raise ValueError("after_receipt_id must be non-negative")
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        self.get_trial(trial_id)
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM receipts
                WHERE trial_id = ? AND receipt_id > ?
                ORDER BY receipt_id LIMIT ?
                """,
                (trial_id, after_receipt_id, limit),
            ).fetchall()
        return [self._receipt_from_row(row) for row in rows]

    def health(self) -> dict[str, Any]:
        with self._connect() as connection:
            connection.execute("SELECT 1").fetchone()
            bucket_count = int(
                connection.execute("SELECT COUNT(*) FROM trial_buckets").fetchone()[0]
            )
            receipt_count = int(
                connection.execute("SELECT COUNT(*) FROM receipts").fetchone()[0]
            )
        return {
            "status": "ok",
            "database": "ok",
            "bucket_count": bucket_count,
            "receipt_count": receipt_count,
        }
