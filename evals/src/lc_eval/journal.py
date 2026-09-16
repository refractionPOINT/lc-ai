"""Durable trial state and exact resource ownership, including partial creation."""
from __future__ import annotations

import contextlib
import fcntl
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any

from .models import safe_id

STATES = ("planned", "provisioning", "ready", "running", "stopping", "settling", "verifying", "cleaning", "finished")


class Journal:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.root, 0o700)
        self.path = self.root / "journal.sqlite"
        self.db = sqlite3.connect(self.path, timeout=30)
        os.chmod(self.path, 0o600)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS trials (
            id TEXT PRIMARY KEY, campaign TEXT NOT NULL, state TEXT NOT NULL,
            manifest TEXT NOT NULL, result TEXT, updated REAL NOT NULL);
          CREATE TABLE IF NOT EXISTS transitions (
            seq INTEGER PRIMARY KEY, trial TEXT REFERENCES trials(id), state TEXT, at REAL);
          CREATE TABLE IF NOT EXISTS resources (
            intent TEXT PRIMARY KEY, trial TEXT REFERENCES trials(id), kind TEXT NOT NULL,
            name TEXT NOT NULL, resource_id TEXT, handle TEXT NOT NULL,
            status TEXT NOT NULL, expires REAL NOT NULL, error TEXT);
        """)

    @contextlib.contextmanager
    def exclusive(self):
        with (self.root / "controller.lock").open("a+") as fp:
            try:
                fcntl.flock(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise RuntimeError("another controller owns this run directory") from exc
            try:
                yield
            finally:
                fcntl.flock(fp, fcntl.LOCK_UN)

    def create_trial(self, trial_id: str, campaign: str, manifest: dict) -> Path:
        safe_id(trial_id)
        safe_id(campaign)
        with self.db:
            self.db.execute("INSERT INTO trials VALUES (?,?,?,?,?,?)",
                            (trial_id, campaign, "planned", json.dumps(manifest), None, time.time()))
            self.db.execute("INSERT INTO transitions(trial,state,at) VALUES (?,?,?)",
                            (trial_id, "planned", time.time()))
        path = self.root / "trials" / trial_id
        path.mkdir(parents=True, mode=0o700)
        return path

    def transition(self, trial_id: str, state: str):
        if state not in STATES:
            raise ValueError("unknown state")
        row = self.db.execute("SELECT state FROM trials WHERE id=?", (trial_id,)).fetchone()
        if row is None:
            raise KeyError(trial_id)
        before = row["state"]
        if state == before:
            return
        valid = (state == "cleaning" and before != "finished") or (
            STATES.index(state) == STATES.index(before) + 1)
        if not valid:
            raise ValueError(f"invalid transition {before} -> {state}")
        with self.db:
            self.db.execute("UPDATE trials SET state=?,updated=? WHERE id=?", (state, time.time(), trial_id))
            self.db.execute("INSERT INTO transitions(trial,state,at) VALUES (?,?,?)", (trial_id, state, time.time()))

    def intent(self, trial_id: str, kind: str, name: str, handle: dict, ttl: int = 86400) -> str:
        import uuid
        ident = uuid.uuid4().hex
        with self.db:
            self.db.execute("INSERT INTO resources VALUES (?,?,?,?,?,?,?,?,?)", (
                ident, trial_id, kind, name, None, json.dumps(handle), "creating", time.time()+ttl, None))
        return ident

    def acquired(self, intent: str, resource_id: str, handle: dict | None = None):
        with self.db:
            row = self.db.execute("SELECT handle,status FROM resources WHERE intent=?", (intent,)).fetchone()
            if row is None:
                raise KeyError(intent)
            if row["status"] == "cleaned":
                raise ValueError("cannot reacquire cleaned resource")
            self.db.execute("UPDATE resources SET resource_id=?,handle=?,status='active' WHERE intent=?",
                            (resource_id, json.dumps(handle) if handle is not None else row["handle"], intent))

    def cleaned(self, intent: str):
        with self.db:
            self.db.execute("UPDATE resources SET status='cleaned',error=NULL WHERE intent=?", (intent,))

    def cleanup_failed(self, intent: str, error: str):
        with self.db:
            self.db.execute("UPDATE resources SET status='cleanup_failed',error=? WHERE intent=?", (error, intent))

    def resources(self, trial: str | None = None, pending: bool = True) -> list[dict[str, Any]]:
        sql = "SELECT * FROM resources WHERE 1=1"
        args = []
        if trial:
            sql += " AND trial=?"
            args.append(trial)
        if pending:
            sql += " AND status!='cleaned'"
        rows = [dict(r) for r in self.db.execute(sql, args)]
        for row in rows:
            row["handle"] = json.loads(row["handle"])
        return rows

    def finish(self, trial_id: str, result: dict):
        with self.db:
            self.db.execute("UPDATE trials SET result=?,updated=? WHERE id=?", (json.dumps(result), time.time(), trial_id))

    def trials(self, campaign: str | None = None) -> list[dict]:
        rows = self.db.execute("SELECT * FROM trials" + (" WHERE campaign=?" if campaign else ""),
                               (campaign,) if campaign else ())
        return [{**dict(r), "manifest": json.loads(r["manifest"]),
                 "result": json.loads(r["result"]) if r["result"] else None} for r in rows]

    def close(self):
        self.db.close()
