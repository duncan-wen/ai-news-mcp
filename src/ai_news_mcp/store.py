"""SQLite access layer for Items and Source state."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    original_url TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    published_at TEXT NOT NULL,
    collected_at TEXT NOT NULL,
    source_id TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS source_state (
    source_id TEXT PRIMARY KEY,
    backfill_from TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class NewItem:
    url: str
    original_url: str
    title: str
    summary: str
    published_at: datetime
    collected_at: datetime
    source_id: str


@dataclass(frozen=True)
class StoredItem:
    id: int
    original_url: str
    title: str
    summary: str
    published_at: datetime
    source_id: str


class Store:
    """Use from the event loop thread only: the SQLite connection is bound to it."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path)
        self._db.executescript(SCHEMA)

    def backfill_from(self, source_id: str, default: datetime) -> datetime:
        """The earliest publish time collected for a Source, fixed by its first collection."""
        with self._db:
            self._db.execute(
                "INSERT OR IGNORE INTO source_state (source_id, backfill_from) VALUES (?, ?)",
                (source_id, _to_text(default)),
            )
            (value,) = self._db.execute(
                "SELECT backfill_from FROM source_state WHERE source_id = ?", (source_id,)
            ).fetchone()
        return datetime.fromisoformat(value)

    def add_items(self, items: list[NewItem]) -> int:
        """Insert Items whose URL is not stored yet; return how many were added."""
        with self._db:
            before = self._db.total_changes
            self._db.executemany(
                """
                INSERT OR IGNORE INTO items
                    (url, original_url, title, summary, published_at, collected_at, source_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item.url,
                        item.original_url,
                        item.title,
                        item.summary,
                        _to_text(item.published_at),
                        _to_text(item.collected_at),
                        item.source_id,
                    )
                    for item in items
                ],
            )
            return self._db.total_changes - before

    def search(self, query: str, limit: int) -> list[StoredItem]:
        """Items whose title or summary contains query (ASCII case-insensitive), newest first."""
        pattern = "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        rows = self._db.execute(
            r"""
            SELECT id, original_url, title, summary, published_at, source_id
            FROM items
            WHERE title LIKE :pattern ESCAPE '\' OR summary LIKE :pattern ESCAPE '\'
            ORDER BY published_at DESC, id DESC
            LIMIT :limit
            """,
            {"pattern": pattern, "limit": limit},
        )
        return [
            StoredItem(
                id=row[0],
                original_url=row[1],
                title=row[2],
                summary=row[3],
                published_at=datetime.fromisoformat(row[4]),
                source_id=row[5],
            )
            for row in rows
        ]


def _to_text(moment: datetime) -> str:
    """UTC ISO 8601, so that text order is time order."""
    return moment.astimezone(UTC).isoformat()
