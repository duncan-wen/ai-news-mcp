"""The MCP server and its tools."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, TypeVar

from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel

from .clock import Clock
from .collector import Collector
from .fetcher import PROJECT_NAME, VERSION, Fetcher
from .sources import DEFAULT_SOURCES, Category, Source
from .store import SourceHealth, Store, StoredItem

SEARCH_LIMIT = 20
WHATS_NEW_LOOKBACK = timedelta(days=7)
COLLECTION_WAIT = timedelta(seconds=90)
STILL_COLLECTING = (
    "A collection is still running, so these are only the Items collected before it. "
    "Call whats_new again in a minute or two for the rest."
)
FAILURES_BEFORE_WARNING = 3

ToolFunction = TypeVar("ToolFunction", bound=Callable[..., Awaitable[Any]])


def async_tool(server: MCPServer) -> Callable[[ToolFunction], ToolFunction]:
    """Register a tool, refusing plain `def` functions.

    The SDK runs sync tools on a worker thread, but the Store's SQLite connection
    only works on the event loop thread that opened it.
    """

    def register(function: ToolFunction) -> ToolFunction:
        if not inspect.iscoroutinefunction(function):
            raise TypeError(f"Tool {function.__name__!r} must be `async def`: see async_tool")
        return server.tool()(function)

    return register


class SourceCollectReport(BaseModel):
    source: str
    added: int


class SourceFailure(BaseModel):
    source: str
    error: str


class CollectReport(BaseModel):
    sources: list[SourceCollectReport]
    failed: list[SourceFailure]


class SourceView(BaseModel):
    id: str
    name: str
    default_categories: list[Category]
    last_attempt_at: datetime | None
    last_success_at: datetime | None
    last_error: str | None
    consecutive_failures: int

    @classmethod
    def of(cls, source: Source, health: SourceHealth | None) -> SourceView:
        """`health` is None for a Source never tried yet."""
        return cls(
            id=source.id,
            name=source.name,
            default_categories=list(source.default_categories),
            last_attempt_at=health.last_attempt_at if health else None,
            last_success_at=health.last_success_at if health else None,
            last_error=health.last_error if health else None,
            consecutive_failures=health.consecutive_failures if health else 0,
        )


class SourceList(BaseModel):
    sources: list[SourceView]


class ItemView(BaseModel):
    id: int
    title: str
    source: str
    categories: list[Category]
    published_at: datetime
    summary: str
    url: str

    @classmethod
    def of(cls, item: StoredItem) -> ItemView:
        return cls(
            id=item.id,
            title=item.title,
            source=item.source_id,
            categories=list(item.categories),
            published_at=item.published_at,
            summary=item.summary,
            url=item.original_url,
        )


class SearchResult(BaseModel):
    items: list[ItemView]


class WhatsNew(BaseModel):
    warning: str | None = None  # first, so that a client reads it before the Items
    items: list[ItemView]
    note: str | None = None


def failing_sources_warning(
    sources: tuple[Source, ...], health: dict[str, SourceHealth]
) -> str | None:
    """A warning naming every Source that failed 3 or more collections in a row, if any."""
    failing = [
        f"{source.name} ({source.id}): failed {state.consecutive_failures} collections in a row, "
        f"last error: {state.last_error}"
        for source in sources
        if (state := health.get(source.id))
        and state.consecutive_failures >= FAILURES_BEFORE_WARNING
    ]
    if not failing:
        return None
    return (
        "Some Sources keep failing, so their Items are missing: "
        + "; ".join(failing)
        + ". Call list_sources for details."
    )


def create_server(
    *,
    store_path: Path,
    fetcher: Fetcher,
    clock: Clock,
    sources: tuple[Source, ...] = DEFAULT_SOURCES,
    collection_wait: timedelta = COLLECTION_WAIT,
) -> MCPServer:
    store = Store(store_path)
    collector = Collector(sources, store, fetcher, clock)

    @asynccontextmanager
    async def lifespan(_: MCPServer) -> AsyncGenerator[None]:
        if collector.is_stale():
            collector.start()  # in the background: the server answers queries meanwhile
        try:
            yield
        finally:
            collector.stop()

    server = MCPServer(PROJECT_NAME, version=VERSION, lifespan=lifespan)
    tool = async_tool(server)

    @tool
    async def collect_now() -> CollectReport:
        """Collect new Items from every Source now.

        Reports how many Items each Source added (0 for a failed one), and which Sources
        failed and why.
        """
        reports = await collector.collect()
        return CollectReport(
            sources=[SourceCollectReport(source=r.source, added=r.added) for r in reports],
            failed=[
                SourceFailure(source=r.source, error=r.error)
                for r in reports
                if r.error is not None
            ],
        )

    @tool
    async def list_sources() -> SourceList:
        """Every Source with its default Categories and collection state.

        The state is when it was last tried, when it last succeeded, its last error and
        how many collections in a row it has failed. The last error is kept after a success,
        so with 0 failures in a row it is from before `last_success_at`. Use it to check
        which Sources work.
        """
        health = store.source_health()
        return SourceList(
            sources=[SourceView.of(source, health.get(source.id)) for source in sources]
        )

    @tool
    async def search(query: str) -> SearchResult:
        """Search stored Items whose title or summary contains `query` (case-insensitive).

        Results are newest first, at most 20. Searching never moves a Checkpoint.
        """
        return SearchResult(items=[ItemView.of(item) for item in store.search(query, SEARCH_LIMIT)])

    @tool
    async def whats_new(categories: list[Category] | None = None) -> WhatsNew:
        """What's New: Items collected since the last Checkpoint, looking back at most 7 days.

        Use when the user asks what's new in AI. Each Category has its own Checkpoint;
        only the Checkpoints of the Categories asked about (omitted: all) move to now.
        Categories: News (industry events: launches, funding, policy, people),
        Applications (AI products and tools to use right away), Engineering (how to build
        AI systems: technical posts, frameworks, releases) and Models (new or newly listed
        models and changes to their abilities or prices). An Item can be in several
        Categories. If the data is over 24 hours old this collects first, which can take
        about a minute; `note` says when the collection was still running. `warning` names
        Sources that failed 3 or more collections in a row: tell the user.
        """
        if collector.is_stale():
            collector.start()
        note = None
        running = collector.running()
        if running is not None:
            # A failed collection still leaves the Items already stored to return.
            done, _ = await asyncio.wait({running}, timeout=collection_wait.total_seconds())
            if not done:
                note = STILL_COLLECTING
        now = clock.now()
        # Omitted means every Category; a repeated Category counts once.
        categories = list(Category) if categories is None else list(dict.fromkeys(categories))
        oldest = now - WHATS_NEW_LOOKBACK
        checkpoints = store.checkpoints()
        items = store.collected_after(
            {category: max(checkpoints.get(category, oldest), oldest) for category in categories}
        )
        store.move_checkpoints(categories, now)
        return WhatsNew(
            warning=failing_sources_warning(sources, store.source_health()),
            items=[ItemView.of(item) for item in items],
            note=note,
        )

    return server
