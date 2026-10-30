"""SQLite persistence for GhostEvents."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import aiosqlite

from ghostwatch.core.schema import GhostEvent

log = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id          TEXT PRIMARY KEY,
    timestamp   TEXT NOT NULL,
    source      TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    summary     TEXT NOT NULL,
    severity    TEXT NOT NULL,
    data        TEXT NOT NULL    -- full JSON blob of the event
);

CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events (timestamp);
CREATE INDEX IF NOT EXISTS idx_events_source    ON events (source);
"""


class EventStore:
    def __init__(self, db_path: Path) -> None:
        self._path = db_path
        self._db: aiosqlite.Connection | None = None

    async def open(self) -> None:
        self._db = await aiosqlite.connect(self._path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(_SCHEMA)
        await self._db.commit()
        log.info("Database opened: %s", self._path)

    async def close(self) -> None:
        if self._db:
            await self._db.close()

    async def save_event(self, event: GhostEvent) -> bool:
        """
        Persist *event*. Returns True if inserted, False if deduplicated (already exists).
        """
        assert self._db, "call open() first"
        try:
            await self._db.execute(
                """
                INSERT OR IGNORE INTO events
                    (id, timestamp, source, event_type, summary, severity, data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.id,
                    event.timestamp.isoformat(),
                    event.source.value,
                    event.event_type,
                    event.summary,
                    event.severity.value,
                    event.model_dump_json(),
                ),
            )
            await self._db.commit()
            changes = self._db.total_changes  # type: ignore[attr-defined]
            return changes > 0
        except Exception:
            log.exception("Failed to save event %s", event.id)
            return False

    async def list_events(
        self,
        limit: int = 200,
        source: str | None = None,
        since: datetime | None = None,
    ) -> list[GhostEvent]:
        assert self._db, "call open() first"
        clauses: list[str] = []
        params: list[str] = []

        if source:
            clauses.append("source = ?")
            params.append(source)
        if since:
            clauses.append("timestamp >= ?")
            params.append(since.isoformat())

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT data FROM events {where} ORDER BY timestamp DESC LIMIT ?"
        params.append(str(limit))

        rows = await self._db.execute_fetchall(sql, params)
        events: list[GhostEvent] = []
        for row in rows:
            try:
                events.append(GhostEvent.model_validate_json(row["data"]))
            except Exception:
                log.warning("Skipping corrupt event row", exc_info=True)
        return events

    async def clear(self) -> int:
        """Delete all events. Returns number of rows deleted."""
        assert self._db, "call open() first"
        cursor = await self._db.execute("DELETE FROM events")
        await self._db.commit()
        return cursor.rowcount
