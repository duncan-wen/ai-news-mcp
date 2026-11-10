"""Runs one collection across all Sources."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from .adapters import parse_rss
from .clock import Clock
from .fetcher import Fetcher
from .sources import Source
from .store import NewItem, Store
from .urls import normalize_url

BACKFILL = timedelta(days=30)


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

    async def collect(self) -> list[SourceReport]:
        return [await self._collect_source(source) for source in self._sources]

    async def _collect_source(self, source: Source) -> SourceReport:
        now = self._clock.now()
        cutoff = self._store.backfill_from(source.id, default=now - BACKFILL)
        body = await self._fetcher.get(source.url)
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
                )
            )
        return SourceReport(source=source.id, added=self._store.add_items(new_items))
