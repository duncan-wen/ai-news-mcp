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
CREATE TABLE IF NOT EXISTS source_health (
    source_id TEXT PRIMARY KEY,
    last_attempt_at TEXT NOT NULL,
    last_success_at TEXT,
    last_error TEXT,
    consecutive_failures INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS listed_urls (
    source_id TEXT NOT NULL,
    url TEXT NOT NULL,
    PRIMARY KEY (source_id, url)
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


@dataclass(frozen=True)
class SourceHealth:
    last_attempt_at: datetime
    last_success_at: datetime | None
    last_error: str | None
    consecutive_failures: int


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

    def record_attempt(self, source_id: str, at: datetime, error: str | None) -> None:
        """Record one collection attempt for a Source: a success when `error` is None.

        A success resets the consecutive failures; the last error is kept for reference.
        """
        succeeded = error is None
        with self._db:
            self._db.execute(
                """
                INSERT INTO source_health
                    (source_id, last_attempt_at, last_success_at, last_error, consecutive_failures)
                VALUES (:source_id, :at, :success_at, :error, :failures)
                ON CONFLICT (source_id) DO UPDATE SET
                    last_attempt_at = excluded.last_attempt_at,
                    last_success_at = coalesce(excluded.last_success_at, last_success_at),
                    last_error = coalesce(excluded.last_error, last_error),
                    consecutive_failures = CASE
                        WHEN :succeeded THEN 0 ELSE consecutive_failures + 1 END
                """,
                {
                    "source_id": source_id,
                    "at": _to_text(at),
                    "success_at": _to_text(at) if succeeded else None,
                    "error": error,
                    "failures": 0 if succeeded else 1,
                    "succeeded": succeeded,
                },
            )

    def newly_listed(self, source_id: str, urls: list[str]) -> set[str]:
        """Record the URLs a Source lists now; return those it never listed before.

        The first call for a Source returns nothing: what it lists then is already there,
        not new.
        """
        with self._db:
            listed_before = self._db.execute(
                "SELECT 1 FROM listed_urls WHERE source_id = ? LIMIT 1", (source_id,)
            ).fetchone()
            new: set[str] = set()
            for url in dict.fromkeys(urls):
                cursor = self._db.execute(
                    "INSERT OR IGNORE INTO listed_urls (source_id, url) VALUES (?, ?)",
                    (source_id, url),
                )
                if cursor.rowcount:
                    new.add(url)
        return new if listed_before else set()

    def source_health(self) -> dict[str, SourceHealth]:
        """The health of every Source with at least one recorded attempt."""
        return {
            source_id: SourceHealth(
                last_attempt_at=datetime.fromisoformat(attempt),
                last_success_at=None if success is None else datetime.fromisoformat(success),
                last_error=error,
                consecutive_failures=failures,
            )
            for source_id, attempt, success, error, failures in self._db.execute(
                """
                SELECT source_id, last_attempt_at, last_success_at, last_error,
                    consecutive_failures
                FROM source_health
                """
            )
        }

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

    def item(self, item_id: int) -> StoredItem | None:
        """The Item with this id, or None if there is none."""
        rows = self._db.execute(
            """
            SELECT id, original_url, title, summary, published_at, source_id
            FROM items
            WHERE id = ?
            """,
            (item_id,),
        ).fetchall()
        return next(iter(self._with_categories(rows)), None)

    def search(
        self,
        *,
        query: str | None,
        since: datetime | None,
        until: datetime | None,
        categories: list[Category] | None,
        source_ids: list[str] | None,
        limit: int,
    ) -> list[StoredItem]:
        """Items matching every given filter, newest first; None means no such filter.

        `query`: the title or summary contains it (ASCII case-insensitive).
        `since` / `until`: published at or after `since`, and before `until`.
        `categories` / `source_ids`: in any of them; an empty list matches nothing.
        """
        if categories == [] or source_ids == []:
            return []
        conditions: list[str] = []
        parameters: dict[str, object] = {"limit": limit}
        if query is not None:
            conditions.append(
                r"(title LIKE :pattern ESCAPE '\' OR summary LIKE :pattern ESCAPE '\')"
            )
            escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            parameters["pattern"] = f"%{escaped}%"
        if since is not None:
            conditions.append("published_at >= :since")
            parameters["since"] = _to_text(since)
        if until is not None:
            conditions.append("published_at < :until")
            parameters["until"] = _to_text(until)
        if categories is not None:
            names = _named_placeholders(parameters, "category", [c.value for c in categories])
            conditions.append(
                f"id IN (SELECT item_id FROM item_categories WHERE category IN ({names}))"
            )
        if source_ids is not None:
            names = _named_placeholders(parameters, "source", source_ids)
            conditions.append(f"source_id IN ({names})")
        where = " AND ".join(conditions) or "1"
        rows = self._db.execute(
            f"""
            SELECT id, original_url, title, summary, published_at, source_id
            FROM items
            WHERE {where}
            ORDER BY published_at DESC, id DESC
            LIMIT :limit
            """,
            parameters,
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


def _named_placeholders(parameters: dict[str, object], prefix: str, values: list[str]) -> str:
    """Add each value to `parameters` under a numbered name; return the names for an IN list."""
    names = [f"{prefix}{index}" for index in range(len(values))]
    parameters.update(zip(names, values, strict=True))
    return ", ".join(f":{name}" for name in names)


def _to_text(moment: datetime) -> str:
    """UTC ISO 8601, so that text order is time order.

    Refuses a time without an offset: `astimezone` would silently take it as local time.
    """
    if moment.tzinfo is None:
        raise ValueError(f"Time without an offset: {moment}")
    return moment.astimezone(UTC).isoformat()
