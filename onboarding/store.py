"""Local case file for hires and events. CrewAI memory stays off."""

import json
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "onboarding.sqlite"
FIRST_HIRE_NUMBER = 1001

_SCHEMA = """
CREATE TABLE IF NOT EXISTS hire_seq (
    next_id INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    actor_role TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    body_json TEXT NOT NULL,
    contents_key TEXT NOT NULL,
    state TEXT NOT NULL,
    hire_id TEXT
);
CREATE TABLE IF NOT EXISTS hires (
    hire_id TEXT PRIMARY KEY,
    employee_name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    role TEXT NOT NULL,
    location TEXT NOT NULL,
    manager_name TEXT NOT NULL,
    plan_version INTEGER,
    readiness TEXT NOT NULL,
    readiness_reasons_json TEXT NOT NULL,
    failure_json TEXT
);
CREATE TABLE IF NOT EXISTS tasks (
    hire_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    body_json TEXT NOT NULL,
    PRIMARY KEY (hire_id, position)
);
CREATE TABLE IF NOT EXISTS messages (
    hire_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    body_json TEXT NOT NULL,
    PRIMARY KEY (hire_id, position)
);
CREATE TABLE IF NOT EXISTS versions (
    hire_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    body_json TEXT NOT NULL,
    PRIMARY KEY (hire_id, position)
);
CREATE TABLE IF NOT EXISTS decisions (
    hire_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    body_json TEXT NOT NULL,
    PRIMARY KEY (hire_id, position)
);
CREATE TABLE IF NOT EXISTS equipment_state (
    hire_id TEXT NOT NULL,
    device TEXT NOT NULL,
    state TEXT NOT NULL,
    ready_date TEXT,
    PRIMARY KEY (hire_id, device)
);
CREATE TABLE IF NOT EXISTS equipment_round (
    hire_id TEXT PRIMARY KEY,
    follow_ups INTEGER NOT NULL,
    bodies_json TEXT NOT NULL
);
"""


class CaseStore:
    """SQLite file owned by the application. It is not agent memory."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path is not None else DEFAULT_DB_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._migrate_events()
        self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def ping(self) -> bool:
        with self._lock:
            row = self._conn.execute("SELECT 1").fetchone()
        return row is not None and row[0] == 1

    def begin_attempt(self, event: dict) -> dict:
        """Reserve the event id, or return the earlier result."""
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                answer = self._begin_locked(event)
                self._conn.commit()
                return answer
            except Exception:
                self._conn.rollback()
                raise

    def finish_attempt(self, event: dict, outcome: dict) -> dict:
        """Write the rule result for an attempt that is already in flight."""
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                answer = self._finish_locked(event, outcome)
                self._conn.commit()
                return answer
            except Exception:
                self._conn.rollback()
                raise

    def abort_attempt(self, event_id: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE events SET state = 'failed', hire_id = NULL WHERE event_id = ? AND state = 'in_flight'",
                (event_id,),
            )
            self._conn.commit()

    def load_hire(self, hire_id: str) -> dict | None:
        with self._lock:
            hire = self._conn.execute(
                "SELECT * FROM hires WHERE hire_id = ?",
                (hire_id,),
            ).fetchone()
            if hire is None:
                return None
            tasks = self._bodies("tasks", hire_id)
            messages = self._bodies("messages", hire_id)
            versions = self._bodies("versions", hire_id)
            decisions = self._bodies("decisions", hire_id)
            events = self._events(hire_id)
        failure = json.loads(hire["failure_json"]) if hire["failure_json"] else None
        return {
            "hire_id": hire["hire_id"],
            "start_date": hire["start_date"],
            "role": hire["role"],
            "location": hire["location"],
            "plan_version": hire["plan_version"],
            "readiness": hire["readiness"],
            "readiness_reasons": json.loads(hire["readiness_reasons_json"]),
            "tasks": tasks,
            "messages": messages,
            "versions": versions,
            "decisions": decisions,
            "events": events,
            "failure": failure,
            "activation": hire["activation"] if "activation" in hire.keys() else "active",
            "employee_name": hire["employee_name"],
            "manager_name": hire["manager_name"],
        }

    def reply_context(self, hire_id: str) -> dict | None:
        """Hire read plus the equipment ledger. The HTTP hire read does not call this."""
        hire = self.load_hire(hire_id)
        if hire is None:
            return None
        with self._lock:
            hire["ledger"] = self._ledger(hire_id)
            row = self._conn.execute(
                "SELECT follow_ups, bodies_json FROM equipment_round WHERE hire_id = ?",
                (hire_id,),
            ).fetchone()
        if row is None:
            hire["follow_ups"] = 0
            hire["round_bodies"] = []
        else:
            hire["follow_ups"] = int(row["follow_ups"])
            hire["round_bodies"] = json.loads(row["bodies_json"])
        return hire

    def finish_reply(self, event_id: str, outcome: dict) -> None:
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._finish_reply_locked(event_id, outcome)
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise

    def fail_reply(self, event_id: str, failure: dict, message: dict) -> None:
        self.finish_reply(
            event_id,
            {"ok": False, "failure": failure, "message": message},
        )

    def wait_for_event(self, event_id: str, timeout: float = 5.0) -> str:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                row = self._conn.execute(
                    "SELECT state FROM events WHERE event_id = ?",
                    (event_id,),
                ).fetchone()
            if row is not None and row["state"] != "in_flight":
                return row["state"]
            time.sleep(0.01)
        raise TimeoutError(event_id)

    def _begin_locked(self, event: dict) -> dict:
        row = self._conn.execute(
            "SELECT state, contents_key, hire_id FROM events WHERE event_id = ?",
            (event["event_id"],),
        ).fetchone()
        if row is None:
            busy = self._other_in_flight(event["event_id"])
            if busy is not None:
                return {"action": "reply", "status": 409, "body": _busy(event, busy)}
            self._insert_event(event, "in_flight", event.get("hire_id"))
            return {"action": "run"}
        if row["state"] == "in_flight":
            return {"action": "reply", "status": 409, "body": _conflict(event, row["hire_id"])}
        if row["contents_key"] != event["contents_key"]:
            return {
                "action": "reply",
                "status": 400,
                "body": _mismatch(event, row["hire_id"]),
            }
        if row["state"] == "committed":
            return {"action": "reply", "status": 202, "body": _ack(event["event_id"], row["hire_id"])}
        busy = self._other_in_flight(event["event_id"])
        if busy is not None:
            return {"action": "reply", "status": 409, "body": _busy(event, busy)}
        self._conn.execute(
            """
            UPDATE events
            SET state = 'in_flight', hire_id = ?, failure_json = NULL
            WHERE event_id = ?
            """,
            (event.get("hire_id"), event["event_id"]),
        )
        return {"action": "run"}

    def _finish_locked(self, event: dict, outcome: dict) -> dict:
        row = self._conn.execute(
            "SELECT state FROM events WHERE event_id = ?",
            (event["event_id"],),
        ).fetchone()
        if row is None or row["state"] != "in_flight":
            raise RuntimeError("intake attempt was not in flight")
        if not outcome["ok"]:
            self._conn.execute(
                """
                UPDATE events
                SET state = 'failed', hire_id = NULL, failure_json = ?, finished_at = ?
                WHERE event_id = ?
                """,
                (json.dumps(outcome["error"]), _now(), event["event_id"]),
            )
            body = dict(outcome["error"])
            body["event_id"] = event["event_id"]
            return {"status": 400, "body": body}

        hire_id = self._next_hire_id()
        hire = outcome["hire"]
        self._conn.execute(
            """
            INSERT INTO hires (
                hire_id, employee_name, start_date, role, location, manager_name,
                plan_version, readiness, readiness_reasons_json, failure_json, activation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                hire_id,
                hire["employee_name"],
                hire["start_date"],
                hire["role"],
                hire["location"],
                hire["manager_name"],
                hire["plan_version"],
                hire["readiness"],
                json.dumps(hire["readiness_reasons"]),
                None,
                hire.get("activation", "active"),
            ),
        )
        self._insert_bodies("tasks", hire_id, outcome["tasks"])
        self._insert_bodies("messages", hire_id, outcome["messages"])
        versions = []
        for version in outcome["versions"]:
            stored = dict(version)
            stored["hire_id"] = hire_id
            versions.append(stored)
        self._insert_bodies("versions", hire_id, versions)
        self._conn.execute(
            """
            UPDATE events
            SET state = 'committed', hire_id = ?, failure_json = NULL, finished_at = ?
            WHERE event_id = ?
            """,
            (hire_id, _now(), event["event_id"]),
        )
        return {"status": 202, "body": _ack(event["event_id"], hire_id)}

    def _insert_event(self, event: dict, state: str, hire_id: str | None) -> None:
        self._conn.execute(
            """
            INSERT INTO events (
                event_id, event_type, actor_id, actor_role, occurred_at,
                body_json, contents_key, state, hire_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["event_id"],
                event["event_type"],
                event["actor_id"],
                event["actor_role"],
                event["occurred_at"],
                event["body_json"],
                event["contents_key"],
                state,
                hire_id,
            ),
        )

    def _next_hire_id(self) -> str:
        row = self._conn.execute("SELECT next_id FROM hire_seq").fetchone()
        if row is None:
            number = FIRST_HIRE_NUMBER
            self._conn.execute("INSERT INTO hire_seq (next_id) VALUES (?)", (number + 1,))
        else:
            number = int(row["next_id"])
            self._conn.execute("UPDATE hire_seq SET next_id = ?", (number + 1,))
        return f"H-{number}"

    def _insert_bodies(self, table: str, hire_id: str, items: list) -> None:
        for position, item in enumerate(items):
            self._conn.execute(
                f"INSERT INTO {table} (hire_id, position, body_json) VALUES (?, ?, ?)",
                (hire_id, position, json.dumps(item)),
            )

    def _migrate_events(self) -> None:
        columns = {row[1] for row in self._conn.execute("PRAGMA table_info(events)")}
        if "failure_json" not in columns:
            self._conn.execute("ALTER TABLE events ADD COLUMN failure_json TEXT")
        if "finished_at" not in columns:
            self._conn.execute("ALTER TABLE events ADD COLUMN finished_at TEXT")
        hire_columns = {row[1] for row in self._conn.execute("PRAGMA table_info(hires)")}
        if "activation" not in hire_columns:
            self._conn.execute("ALTER TABLE hires ADD COLUMN activation TEXT NOT NULL DEFAULT 'active'")
            self._conn.execute(
                """
                UPDATE hires SET activation = 'held'
                WHERE plan_version IS NULL AND readiness_reasons_json LIKE '%role was not on the intake%'
                """
            )
            self._conn.execute(
                """
                UPDATE hires SET activation = 'review'
                WHERE plan_version IS NULL AND activation = 'active'
                """
            )

    def _finish_reply_locked(self, event_id: str, outcome: dict) -> None:
        row = self._conn.execute(
            "SELECT state, hire_id FROM events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        if row is None or row["state"] != "in_flight":
            return
        hire_id = row["hire_id"]
        if not outcome["ok"]:
            self._append("messages", hire_id, outcome["message"])
            failure = outcome["failure"]
            self._conn.execute(
                """
                UPDATE events
                SET state = 'failed', failure_json = ?, finished_at = ?
                WHERE event_id = ?
                """,
                (json.dumps(failure), _now(), event_id),
            )
            self._conn.execute(
                "UPDATE hires SET failure_json = ? WHERE hire_id = ?",
                (json.dumps(failure), hire_id),
            )
            return
        if outcome["tasks"] is not None:
            self._replace_bodies("tasks", hire_id, outcome["tasks"])
            current = self._conn.execute(
                "SELECT activation, start_date, role FROM hires WHERE hire_id = ?",
                (hire_id,),
            ).fetchone()
            self._conn.execute(
                """
                UPDATE hires
                SET plan_version = ?, readiness = ?, readiness_reasons_json = ?, failure_json = NULL,
                    activation = ?, start_date = ?, role = ?
                WHERE hire_id = ?
                """,
                (
                    outcome["plan_version"],
                    outcome["readiness"],
                    json.dumps(outcome["readiness_reasons"]),
                    outcome.get("activation") or current["activation"],
                    outcome.get("start_date") or current["start_date"],
                    outcome["role"] if outcome.get("role") else current["role"],
                    hire_id,
                ),
            )
            self._write_ledger(hire_id, outcome["ledger"])
            self._conn.execute(
                """
                INSERT INTO equipment_round (hire_id, follow_ups, bodies_json)
                VALUES (?, ?, ?)
                ON CONFLICT(hire_id) DO UPDATE SET
                    follow_ups = excluded.follow_ups,
                    bodies_json = excluded.bodies_json
                """,
                (hire_id, outcome["follow_ups"], json.dumps(outcome["round_bodies"])),
            )
        else:
            self._conn.execute(
                "UPDATE hires SET failure_json = NULL WHERE hire_id = ?",
                (hire_id,),
            )
        for message in outcome["messages"]:
            self._append("messages", hire_id, message)
        self._append("decisions", hire_id, outcome["decision"])
        if outcome["version"] is not None:
            self._append("versions", hire_id, outcome["version"])
        if outcome.get("flag_reviews"):
            self._flag_reviews(hire_id, event_id)
        self._conn.execute(
            """
            UPDATE events
            SET state = 'committed', failure_json = NULL, finished_at = ?
            WHERE event_id = ?
            """,
            (_now(), event_id),
        )

    def _events(self, hire_id: str) -> list:
        rows = self._conn.execute(
            """
            SELECT event_id, event_type, state, failure_json
            FROM events
            WHERE hire_id = ?
            ORDER BY rowid
            """,
            (hire_id,),
        ).fetchall()
        visible = []
        for row in rows:
            failure = json.loads(row["failure_json"]) if row["failure_json"] else None
            visible.append(
                {
                    "event_id": row["event_id"],
                    "event_type": row["event_type"],
                    "state": _public_state(row["state"]),
                    "failure": failure,
                }
            )
        return visible

    def _ledger(self, hire_id: str) -> dict:
        rows = self._conn.execute(
            "SELECT device, state, ready_date FROM equipment_state WHERE hire_id = ?",
            (hire_id,),
        ).fetchall()
        return {
            row["device"]: {"state": row["state"], "ready_date": row["ready_date"]}
            for row in rows
        }

    def _write_ledger(self, hire_id: str, ledger: dict) -> None:
        self._conn.execute("DELETE FROM equipment_state WHERE hire_id = ?", (hire_id,))
        for device, state in ledger.items():
            self._conn.execute(
                """
                INSERT INTO equipment_state (hire_id, device, state, ready_date)
                VALUES (?, ?, ?, ?)
                """,
                (hire_id, device, state["state"], state["ready_date"]),
            )

    def _other_in_flight(self, event_id: str):
        return self._conn.execute(
            """
            SELECT event_id, hire_id FROM events
            WHERE state = 'in_flight' AND event_id != ?
            """,
            (event_id,),
        ).fetchone()

    def _replace_bodies(self, table: str, hire_id: str, items: list) -> None:
        self._conn.execute(f"DELETE FROM {table} WHERE hire_id = ?", (hire_id,))
        self._insert_bodies(table, hire_id, items)

    def _flag_reviews(self, hire_id: str, except_event_id: str) -> None:
        rows = self._conn.execute(
            "SELECT position, body_json FROM decisions WHERE hire_id = ? ORDER BY position",
            (hire_id,),
        ).fetchall()
        for row in rows:
            body = json.loads(row["body_json"])
            if not isinstance(body, dict):
                continue
            if body.get("decision_type") != "escalation_disposition":
                continue
            if body.get("event_id") == except_event_id:
                continue
            body["needs_review"] = True
            self._conn.execute(
                "UPDATE decisions SET body_json = ? WHERE hire_id = ? AND position = ?",
                (json.dumps(body), hire_id, row["position"]),
            )

    def _append(self, table: str, hire_id: str, item: dict) -> None:
        row = self._conn.execute(
            f"SELECT COALESCE(MAX(position), -1) + 1 AS next_pos FROM {table} WHERE hire_id = ?",
            (hire_id,),
        ).fetchone()
        self._conn.execute(
            f"INSERT INTO {table} (hire_id, position, body_json) VALUES (?, ?, ?)",
            (hire_id, int(row["next_pos"]), json.dumps(item)),
        )

    def _bodies(self, table: str, hire_id: str) -> list:
        rows = self._conn.execute(
            f"SELECT body_json FROM {table} WHERE hire_id = ? ORDER BY position",
            (hire_id,),
        ).fetchall()
        return [json.loads(row["body_json"]) for row in rows]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _public_state(state: str) -> str:
    if state == "in_flight":
        return "processing"
    if state == "committed":
        return "complete"
    return "failed"


def _busy(event: dict, other) -> dict:
    body = {
        "code": "conflict",
        "message": (
            f"Event {other['event_id']} is already running. "
            f"Event {event['event_id']} was not started."
        ),
        "event_id": event["event_id"],
    }
    hire_id = event.get("hire_id") or other["hire_id"]
    if hire_id:
        body["hire_id"] = hire_id
    return body


def _ack(event_id: str, hire_id: str) -> dict:
    return {"event_id": event_id, "hire_id": hire_id, "status": "processing"}


def _conflict(event: dict, hire_id: str | None) -> dict:
    body = {
        "code": "conflict",
        "message": "This event is already running.",
        "event_id": event["event_id"],
    }
    if hire_id:
        body["hire_id"] = hire_id
    return body


def _mismatch(event: dict, hire_id: str | None) -> dict:
    body = {
        "code": "event_mismatch",
        "message": "This event id was already used with different contents. The new contents were not applied.",
        "event_id": event["event_id"],
    }
    if hire_id:
        body["hire_id"] = hire_id
    return body
