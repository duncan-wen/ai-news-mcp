"""Runs one collection across all Sources."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta

from .adapters import parse_rss
from .clock import Clock
from .fetcher import Fetcher
from .sources import Source
from .store import NewItem, Store
from .urls import normalize_url

BACKFILL = timedelta(days=30)
STALE_AFTER = timedelta(hours=24)


@dataclass(frozen=True)
class SourceReport:
    source: str
    added: int


class Collector:
    def __init__(
        self, sources: tuple[Source, ...], store: Store, fetcher: Fetcher, clock: Clock
    ) -> None:
        self._sources = sources
        self._store = store
        self._fetcher = fetcher
        self._clock = clock
        self._running: asyncio.Task[list[SourceReport]] | None = None

    def start(self) -> asyncio.Task[list[SourceReport]]:
        """The collection now running, or a new one if none is: only one runs at a time."""
        if self._running is None or self._running.done():
            self._running = asyncio.create_task(self._collect_all())
            # A background collection nobody awaits must not log "exception never retrieved".
            self._running.add_done_callback(lambda task: task.cancelled() or task.exception())
        return self._running

    async def collect(self) -> list[SourceReport]:
        """Wait for the running collection, starting one if none is running."""
        # Shielded: a cancelled request must not cancel the collection other callers share.
        return await asyncio.shield(self.start())

    def running(self) -> asyncio.Task[list[SourceReport]] | None:
        """The collection now running, if any."""
        if self._running is None or self._running.done():
            return None
        return self._running

    def stop(self) -> None:
        """Cancel the running collection, if any, when the server shuts down."""
        if self._running is not None:
            self._running.cancel()

    def is_stale(self) -> bool:
        """True when the data was never collected or last collected over 24 hours ago."""
        last = self._store.last_collection()
        return last is None or self._clock.now() - last > STALE_AFTER

    async def _collect_all(self) -> list[SourceReport]:
        reports = [await self._collect_source(source) for source in self._sources]
        self._store.record_collection(self._clock.now())
        return reports

    async def _collect_source(self, source: Source) -> SourceReport:
        body = await self._fetcher.get(source.url)
        # Read after the fetch: an Item must not be stamped earlier than a Checkpoint
        # that whats_new moved while this request was waiting.
        now = self._clock.now()
        cutoff = self._store.backfill_from(source.id, default=now - BACKFILL)
        new_items: list[NewItem] = []
        for parsed in parse_rss(body):
            published_at = parsed.published_at or now
            if published_at < cutoff:
                continue
            new_items.append(
                NewItem(
                    url=normalize_url(parsed.url),
                    original_url=parsed.url,
                    title=parsed.title,
                    summary=parsed.summary,
                    published_at=published_at,
                    collected_at=now,
                    source_id=source.id,
                    categories=source.default_categories,
                )
            )
        return SourceReport(source=source.id, added=self._store.add_items(new_items))
