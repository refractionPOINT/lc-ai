"""Durable, atomic model-budget reservations in integer micro-US dollars."""

from __future__ import annotations

import json
import sqlite3
import time
from collections.abc import Iterable, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator


class BudgetError(RuntimeError):
    """Base class for budget ledger errors."""


class BudgetExceeded(BudgetError):
    """A reservation would exceed its trial or campaign cap."""


class UnknownBudgetEntity(BudgetError):
    """A campaign, trial, or reservation is absent."""


class InactiveTrial(BudgetError):
    """The request does not belong to an active trial."""


class ModelNotAllowed(BudgetError):
    """The requested model is not pinned for the trial."""


class DuplicateSettlementError(BudgetError):
    """A reservation was settled twice with conflicting facts."""


@dataclass(frozen=True)
class Reservation:
    request_id: str
    campaign_id: str
    trial_id: str
    model: str
    reserved_micro_usd: int
    state: str
    actual_micro_usd: int | None = None
    usage: Mapping[str, int] | None = None


@dataclass(frozen=True)
class BudgetSnapshot:
    cap_micro_usd: int
    settled_micro_usd: int
    reserved_micro_usd: int
    remaining_micro_usd: int


class BudgetLedger:
    """SQLite-backed budget ledger.

    Pending and uncertain requests consume their full reservation. Settled
    requests consume their trusted actual charge. All cap checks and inserts
    happen under ``BEGIN IMMEDIATE``, making concurrent reservation attempts
    serialize across processes.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode = WAL;
                CREATE TABLE IF NOT EXISTS budget_campaigns (
                    campaign_id TEXT PRIMARY KEY,
                    cap_micro_usd INTEGER NOT NULL CHECK(cap_micro_usd > 0),
                    created_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS budget_trials (
                    trial_id TEXT PRIMARY KEY,
                    campaign_id TEXT NOT NULL REFERENCES budget_campaigns(campaign_id),
                    cap_micro_usd INTEGER NOT NULL CHECK(cap_micro_usd > 0),
                    allowed_models_json TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0, 1)),
                    created_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS budget_reservations (
                    request_id TEXT PRIMARY KEY,
                    campaign_id TEXT NOT NULL REFERENCES budget_campaigns(campaign_id),
                    trial_id TEXT NOT NULL REFERENCES budget_trials(trial_id),
                    model TEXT NOT NULL,
                    reserved_micro_usd INTEGER NOT NULL CHECK(reserved_micro_usd > 0),
                    state TEXT NOT NULL CHECK(state IN ('pending', 'uncertain', 'settled')),
                    actual_micro_usd INTEGER CHECK(actual_micro_usd >= 0),
                    usage_json TEXT,
                    created_at REAL NOT NULL,
                    settled_at REAL
                );
                CREATE INDEX IF NOT EXISTS budget_reservations_campaign
                    ON budget_reservations(campaign_id, state);
                CREATE INDEX IF NOT EXISTS budget_reservations_trial
                    ON budget_reservations(trial_id, state);
                """
            )

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def create_campaign(self, campaign_id: str, cap_micro_usd: int) -> None:
        _positive(cap_micro_usd, "campaign cap")
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT cap_micro_usd FROM budget_campaigns WHERE campaign_id = ?", (campaign_id,)
            ).fetchone()
            if row is not None:
                if row["cap_micro_usd"] != cap_micro_usd:
                    raise BudgetError("campaign already exists with a different cap")
                return
            connection.execute(
                "INSERT INTO budget_campaigns(campaign_id, cap_micro_usd, created_at) VALUES (?, ?, ?)",
                (campaign_id, cap_micro_usd, time.time()),
            )

    def create_trial(
        self,
        trial_id: str,
        campaign_id: str,
        cap_micro_usd: int,
        allowed_models: Iterable[str],
    ) -> None:
        _positive(cap_micro_usd, "trial cap")
        models = sorted(set(allowed_models))
        if not models or any(not model for model in models):
            raise ValueError("at least one nonempty allowed model is required")
        encoded = json.dumps(models, separators=(",", ":"))
        with self._transaction() as connection:
            campaign = connection.execute(
                "SELECT cap_micro_usd FROM budget_campaigns WHERE campaign_id = ?", (campaign_id,)
            ).fetchone()
            if campaign is None:
                raise UnknownBudgetEntity(f"unknown campaign: {campaign_id}")
            if cap_micro_usd > campaign["cap_micro_usd"]:
                raise BudgetExceeded("trial cap exceeds campaign cap")
            row = connection.execute(
                "SELECT campaign_id, cap_micro_usd, allowed_models_json FROM budget_trials WHERE trial_id = ?",
                (trial_id,),
            ).fetchone()
            if row is not None:
                if (row["campaign_id"], row["cap_micro_usd"], row["allowed_models_json"]) != (
                    campaign_id,
                    cap_micro_usd,
                    encoded,
                ):
                    raise BudgetError("trial already exists with different limits")
                return
            connection.execute(
                """INSERT INTO budget_trials(
                       trial_id, campaign_id, cap_micro_usd, allowed_models_json, active, created_at
                   ) VALUES (?, ?, ?, ?, 1, ?)""",
                (trial_id, campaign_id, cap_micro_usd, encoded, time.time()),
            )

    def close_trial(self, trial_id: str) -> None:
        with self._transaction() as connection:
            cursor = connection.execute(
                "UPDATE budget_trials SET active = 0 WHERE trial_id = ?", (trial_id,)
            )
            if cursor.rowcount != 1:
                raise UnknownBudgetEntity(f"unknown trial: {trial_id}")

    def validate_active_trial(self, trial_id: str, model: str) -> str:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT campaign_id, allowed_models_json, active FROM budget_trials WHERE trial_id = ?",
                (trial_id,),
            ).fetchone()
        if row is None:
            raise UnknownBudgetEntity(f"unknown trial: {trial_id}")
        if not row["active"]:
            raise InactiveTrial(f"inactive trial: {trial_id}")
        if model not in json.loads(row["allowed_models_json"]):
            raise ModelNotAllowed(f"model {model!r} is not allowed for trial {trial_id!r}")
        return str(row["campaign_id"])

    def reserve(self, request_id: str, trial_id: str, model: str, amount_micro_usd: int) -> Reservation:
        _positive(amount_micro_usd, "reservation")
        with self._transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM budget_reservations WHERE request_id = ?", (request_id,)
            ).fetchone()
            if existing is not None:
                candidate = _reservation(existing)
                if (
                    candidate.trial_id,
                    candidate.model,
                    candidate.reserved_micro_usd,
                ) != (trial_id, model, amount_micro_usd):
                    raise BudgetError("request ID already has a different reservation")
                return candidate
            trial = connection.execute(
                "SELECT * FROM budget_trials WHERE trial_id = ?", (trial_id,)
            ).fetchone()
            if trial is None:
                raise UnknownBudgetEntity(f"unknown trial: {trial_id}")
            if not trial["active"]:
                raise InactiveTrial(f"inactive trial: {trial_id}")
            if model not in json.loads(trial["allowed_models_json"]):
                raise ModelNotAllowed(f"model {model!r} is not allowed for trial {trial_id!r}")
            campaign = connection.execute(
                "SELECT cap_micro_usd FROM budget_campaigns WHERE campaign_id = ?",
                (trial["campaign_id"],),
            ).fetchone()
            assert campaign is not None
            trial_exposure = self._exposure(connection, "trial_id", trial_id)
            campaign_exposure = self._exposure(connection, "campaign_id", trial["campaign_id"])
            if trial_exposure + amount_micro_usd > trial["cap_micro_usd"]:
                raise BudgetExceeded("reservation exceeds the trial cap")
            if campaign_exposure + amount_micro_usd > campaign["cap_micro_usd"]:
                raise BudgetExceeded("reservation exceeds the campaign cap")
            connection.execute(
                """INSERT INTO budget_reservations(
                       request_id, campaign_id, trial_id, model, reserved_micro_usd, state, created_at
                   ) VALUES (?, ?, ?, ?, ?, 'pending', ?)""",
                (request_id, trial["campaign_id"], trial_id, model, amount_micro_usd, time.time()),
            )
            return Reservation(
                request_id=request_id,
                campaign_id=trial["campaign_id"],
                trial_id=trial_id,
                model=model,
                reserved_micro_usd=amount_micro_usd,
                state="pending",
            )

    @staticmethod
    def _exposure(connection: sqlite3.Connection, column: str, entity_id: str) -> int:
        if column not in {"trial_id", "campaign_id"}:
            raise ValueError("invalid exposure dimension")
        row = connection.execute(
            f"""SELECT COALESCE(SUM(
                    CASE WHEN state = 'settled' THEN actual_micro_usd ELSE reserved_micro_usd END
                ), 0) AS exposure
                FROM budget_reservations WHERE {column} = ?""",
            (entity_id,),
        ).fetchone()
        return int(row["exposure"])

    def mark_uncertain(self, request_id: str) -> Reservation:
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT * FROM budget_reservations WHERE request_id = ?", (request_id,)
            ).fetchone()
            if row is None:
                raise UnknownBudgetEntity(f"unknown reservation: {request_id}")
            if row["state"] == "settled":
                return _reservation(row)
            connection.execute(
                "UPDATE budget_reservations SET state = 'uncertain' WHERE request_id = ?", (request_id,)
            )
            updated = dict(row)
            updated["state"] = "uncertain"
            return _reservation(updated)

    def settle(
        self,
        request_id: str,
        actual_micro_usd: int,
        usage: Mapping[str, int] | None = None,
    ) -> Reservation:
        if actual_micro_usd < 0:
            raise ValueError("actual cost cannot be negative")
        normalized_usage = _normalize_usage(usage)
        usage_json = json.dumps(normalized_usage, sort_keys=True, separators=(",", ":"))
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT * FROM budget_reservations WHERE request_id = ?", (request_id,)
            ).fetchone()
            if row is None:
                raise UnknownBudgetEntity(f"unknown reservation: {request_id}")
            if row["state"] == "settled":
                if row["actual_micro_usd"] != actual_micro_usd or (row["usage_json"] or "{}") != usage_json:
                    raise DuplicateSettlementError("conflicting duplicate settlement")
                return _reservation(row)
            if actual_micro_usd > row["reserved_micro_usd"]:
                raise BudgetExceeded("actual charge exceeds its conservative reservation")
            connection.execute(
                """UPDATE budget_reservations
                   SET state = 'settled', actual_micro_usd = ?, usage_json = ?, settled_at = ?
                   WHERE request_id = ?""",
                (actual_micro_usd, usage_json, time.time(), request_id),
            )
            updated = dict(row)
            updated.update(state="settled", actual_micro_usd=actual_micro_usd, usage_json=usage_json)
            return _reservation(updated)

    def reservation(self, request_id: str) -> Reservation:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM budget_reservations WHERE request_id = ?", (request_id,)
            ).fetchone()
        if row is None:
            raise UnknownBudgetEntity(f"unknown reservation: {request_id}")
        return _reservation(row)

    def campaign_snapshot(self, campaign_id: str) -> BudgetSnapshot:
        return self._snapshot("campaign", campaign_id)

    def trial_snapshot(self, trial_id: str) -> BudgetSnapshot:
        return self._snapshot("trial", trial_id)

    def _snapshot(self, kind: str, entity_id: str) -> BudgetSnapshot:
        table = "budget_campaigns" if kind == "campaign" else "budget_trials"
        column = "campaign_id" if kind == "campaign" else "trial_id"
        with self._connect() as connection:
            entity = connection.execute(
                f"SELECT cap_micro_usd FROM {table} WHERE {column} = ?", (entity_id,)
            ).fetchone()
            if entity is None:
                raise UnknownBudgetEntity(f"unknown {kind}: {entity_id}")
            rows = connection.execute(
                f"""SELECT state, reserved_micro_usd, actual_micro_usd
                    FROM budget_reservations WHERE {column} = ?""",
                (entity_id,),
            ).fetchall()
        settled = sum(int(row["actual_micro_usd"]) for row in rows if row["state"] == "settled")
        reserved = sum(int(row["reserved_micro_usd"]) for row in rows if row["state"] != "settled")
        cap = int(entity["cap_micro_usd"])
        return BudgetSnapshot(cap, settled, reserved, cap - settled - reserved)


def _positive(value: int, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be a positive integer number of micro-USD")


def _normalize_usage(usage: Mapping[str, int] | None) -> dict[str, int]:
    result: dict[str, int] = {}
    for key, value in (usage or {}).items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"usage value for {key!r} must be a nonnegative integer")
        result[str(key)] = value
    return result


def _reservation(row: Mapping[str, Any]) -> Reservation:
    usage_json = row["usage_json"]
    return Reservation(
        request_id=str(row["request_id"]),
        campaign_id=str(row["campaign_id"]),
        trial_id=str(row["trial_id"]),
        model=str(row["model"]),
        reserved_micro_usd=int(row["reserved_micro_usd"]),
        state=str(row["state"]),
        actual_micro_usd=None if row["actual_micro_usd"] is None else int(row["actual_micro_usd"]),
        usage=None if usage_json is None else json.loads(usage_json),
    )
