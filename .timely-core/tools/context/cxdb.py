"""SQLite-backed context database for Timely orchestration state."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


SCHEMA_VERSION = 1


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class ContextDocument:
    doc_id: str
    kind: str
    title: str
    body: str
    source_path: str | None = None
    metadata: Dict[str, Any] | None = None


class CXDB:
    """Persist orchestrator state and local context documents in SQLite."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def ensure(self) -> None:
        with closing(self._connect()) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS state_snapshot (
                    section TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS state_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS context_documents (
                    doc_id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    source_path TEXT,
                    metadata TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                INSERT INTO metadata(key, value)
                VALUES('schema_version', ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                (str(SCHEMA_VERSION),),
            )
            conn.commit()

    def exists(self) -> bool:
        return self.db_path.exists()

    def load_state(self) -> Dict[str, Any]:
        self.ensure()
        payload: Dict[str, Any] = {
            "goal": "",
            "plan": {},
            "tasks": [],
            "ci_runs": [],
            "decisions": [],
        }
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT section, payload FROM state_snapshot"
            ).fetchall()
        if not rows:
            return payload
        for row in rows:
            value = json.loads(row["payload"])
            if row["section"] == "goal":
                payload["goal"] = value.get("goal", "")
            elif row["section"] == "plan":
                payload["plan"] = value
            elif row["section"] == "tasks":
                payload["tasks"] = value
            elif row["section"] == "ci_runs":
                payload["ci_runs"] = value
            elif row["section"] == "decisions":
                payload["decisions"] = value
        return payload

    def save_state(self, payload: Dict[str, Any], event_type: str = "state_saved") -> None:
        self.ensure()
        now = _utc_now()
        sections = {
            "goal": {"goal": payload.get("goal", "")},
            "plan": payload.get("plan", {}),
            "tasks": payload.get("tasks", []),
            "ci_runs": payload.get("ci_runs", []),
            "decisions": payload.get("decisions", []),
        }
        with closing(self._connect()) as conn:
            for section, section_payload in sections.items():
                conn.execute(
                    """
                    INSERT INTO state_snapshot(section, payload, updated_at)
                    VALUES(?, ?, ?)
                    ON CONFLICT(section) DO UPDATE
                    SET payload=excluded.payload, updated_at=excluded.updated_at
                    """,
                    (section, json.dumps(section_payload), now),
                )
            conn.execute(
                "INSERT INTO state_events(event_type, payload, created_at) VALUES(?, ?, ?)",
                (
                    event_type,
                    json.dumps(
                        {
                            "goal": payload.get("goal", ""),
                            "task_count": len(payload.get("tasks", [])),
                            "ci_runs": len(payload.get("ci_runs", [])),
                            "decisions": len(payload.get("decisions", [])),
                        },
                    ),
                    now,
                ),
            )
            conn.commit()

    def replace_documents(self, documents: Iterable[ContextDocument]) -> int:
        self.ensure()
        now = _utc_now()
        rows = list(documents)
        with closing(self._connect()) as conn:
            conn.execute("DELETE FROM context_documents")
            conn.executemany(
                """
                INSERT INTO context_documents(
                    doc_id, kind, title, body, source_path, metadata, updated_at
                ) VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        doc.doc_id,
                        doc.kind,
                        doc.title,
                        doc.body,
                        doc.source_path,
                        json.dumps(doc.metadata or {}, sort_keys=True),
                        now,
                    )
                    for doc in rows
                ],
            )
            conn.commit()
        return len(rows)

    def load_documents(self) -> List[ContextDocument]:
        self.ensure()
        with closing(self._connect()) as conn:
            rows = conn.execute(
                """
                SELECT doc_id, kind, title, body, source_path, metadata
                FROM context_documents
                ORDER BY doc_id
                """
            ).fetchall()
        return [
            ContextDocument(
                doc_id=row["doc_id"],
                kind=row["kind"],
                title=row["title"],
                body=row["body"],
                source_path=row["source_path"],
                metadata=json.loads(row["metadata"]),
            )
            for row in rows
        ]
