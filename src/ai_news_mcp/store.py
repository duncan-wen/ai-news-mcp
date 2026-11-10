"""SQLite access layer for Items and Source state."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .sources import Category

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
CREATE TABLE IF NOT EXISTS item_categories (
    item_id INTEGER NOT NULL REFERENCES items (id),
    category TEXT NOT NULL,
    PRIMARY KEY (item_id, category)
);
CREATE TABLE IF NOT EXISTS checkpoints (
    category TEXT PRIMARY KEY,
    at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS last_collection (
    only_row INTEGER PRIMARY KEY CHECK (only_row = 1),
    finished_at TEXT NOT NULL
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
    categories: tuple[Category, ...]


@dataclass(frozen=True)
class StoredItem:
    id: int
    original_url: str
    title: str
    summary: str
    published_at: datetime
    source_id: str
    categories: tuple[Category, ...]


class Store:
    """Use from the event loop thread only: the SQLite connection is bound to it."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path)
        self._db.executescript(SCHEMA)

    def last_collection(self) -> datetime | None:
        """When the last collection finished, or None if there has never been one."""
        row = self._db.execute("SELECT finished_at FROM last_collection").fetchone()
        return None if row is None else datetime.fromisoformat(row[0])

    def record_collection(self, finished_at: datetime) -> None:
        with self._db:
            self._db.execute(
                "INSERT OR REPLACE INTO last_collection (only_row, finished_at) VALUES (1, ?)",
                (_to_text(finished_at),),
            )

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
        added = 0
        with self._db:
            for item in items:
                cursor = self._db.execute(
                    """
                    INSERT OR IGNORE INTO items
                        (url, original_url, title, summary, published_at, collected_at, source_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.url,
                        item.original_url,
                        item.title,
                        item.summary,
                        _to_text(item.published_at),
                        _to_text(item.collected_at),
                        item.source_id,
                    ),
                )
                if cursor.rowcount == 0:
                    continue
                added += 1
                self._db.executemany(
                    "INSERT INTO item_categories (item_id, category) VALUES (?, ?)",
                    [(cursor.lastrowid, category.value) for category in item.categories],
                )
        return added

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
        ).fetchall()
        return self._with_categories(rows)

    def collected_after(self, since: dict[Category, datetime]) -> list[StoredItem]:
        """Items in any given Category collected after that Category's time, newest first."""
        if not since:
            return []
        conditions = " OR ".join(
            "(item_categories.category = ? AND items.collected_at > ?)" for _ in since
        )
        parameters = [
            value
            for category, moment in since.items()
            for value in (category.value, _to_text(moment))
        ]
        rows = self._db.execute(
            f"""
            SELECT DISTINCT items.id, original_url, title, summary, published_at, source_id
            FROM items JOIN item_categories ON item_categories.item_id = items.id
            WHERE {conditions}
            ORDER BY published_at DESC, items.id DESC
            """,
            parameters,
        ).fetchall()
        return self._with_categories(rows)

    def checkpoints(self) -> dict[Category, datetime]:
        """The Checkpoint of every Category that has one."""
        return {
            Category(category): datetime.fromisoformat(at)
            for category, at in self._db.execute("SELECT category, at FROM checkpoints")
        }

    def move_checkpoints(self, categories: list[Category], to: datetime) -> None:
        with self._db:
            self._db.executemany(
                "INSERT OR REPLACE INTO checkpoints (category, at) VALUES (?, ?)",
                [(category.value, _to_text(to)) for category in categories],
            )

    def _with_categories(self, rows: list[tuple[int, str, str, str, str, str]]) -> list[StoredItem]:
        categories: dict[int, set[Category]] = {row[0]: set() for row in rows}
        if categories:
            placeholders = ", ".join("?" for _ in categories)
            for item_id, category in self._db.execute(
                f"SELECT item_id, category FROM item_categories WHERE item_id IN ({placeholders})",
                list(categories),
            ):
                categories[item_id].add(Category(category))
        return [
            StoredItem(
                id=row[0],
                original_url=row[1],
                title=row[2],
                summary=row[3],
                published_at=datetime.fromisoformat(row[4]),
                source_id=row[5],
                categories=tuple(
                    category for category in Category if category in categories[row[0]]
                ),
            )
            for row in rows
        ]


def _to_text(moment: datetime) -> str:
    """UTC ISO 8601, so that text order is time order."""
    return moment.astimezone(UTC).isoformat()
