"""The MCP server and its tools."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Any, TypeVar

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field

from .classification import plain_text
from .clock import Clock
from .collector import Collector
from .fetcher import (
    HOST_INTERVAL,
    PROJECT_NAME,
    VERSION,
    Fetcher,
    FetchError,
    HostPacedFetcher,
)
from .full_text import extract_main_text
from .source_config import configured_sources
from .sources import DEFAULT_SOURCES, Category, Source
from .store import SourceHealth, Store, StoredItem

SEARCH_LIMIT = 20
WHATS_NEW_LOOKBACK = timedelta(days=7)
# About 46,000 characters: under the 50,000 at which Claude Code writes a tool result to a
# file instead of showing it.
WHATS_NEW_LIMIT = 100
# The rest of a summary is one `read_item` away. The tool descriptions say "about 500".
SHOWN_SUMMARY_LENGTH = 500
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
    url: str
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
            url=source.url,
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
            summary=shown_summary(item.summary),
            url=item.original_url,
        )


def shown_summary(summary: str) -> str:
    """A summary as a client sees it: plain text, cut to SHOWN_SUMMARY_LENGTH characters."""
    text = plain_text(summary)
    return text if len(text) <= SHOWN_SUMMARY_LENGTH else text[:SHOWN_SUMMARY_LENGTH] + "…"


class SearchResult(BaseModel):
    items: list[ItemView]


class FullText(BaseModel):
    id: int
    title: str
    url: str
    text: str


class WhatsNew(BaseModel):
    warning: str | None = None  # first, so that a client reads it before the Items
    previous_checkpoints: dict[Category, datetime | None]
    items: list[ItemView]
    more: int = 0
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


def shown_items(items: list[StoredItem], limit: int) -> list[StoredItem]:
    """The newest `limit` Items (newest first), never splitting Items published at one time.

    The Items left out must all be older than the oldest shown, so that `search` with that
    time as `until` finds them. Fewer than `limit` are shown when the cut would split a
    publish time; more when the newest publish time alone has more than `limit` Items.
    """
    if len(items) <= limit:
        return items
    boundary = items[limit].published_at  # the newest Item left out
    shown = [item for item in items[:limit] if item.published_at > boundary]
    return shown or [item for item in items if item.published_at == boundary]


def as_utc(moment: datetime | None) -> datetime | None:
    """A time from a client; one without an offset is taken as UTC."""
    if moment is None or moment.tzinfo is not None:
        return moment
    return moment.replace(tzinfo=UTC)


def unreadable_message(item: StoredItem, reason: str) -> str:
    """The error for an Item whose full text cannot be read: its summary and link instead."""
    text = plain_text(item.summary)  # whole: here it stands in for the full text
    summary = f"Its summary: {text} " if text else "It has no summary. "
    return (
        f"Could not read the full text of Item {item.id}: {reason}. "
        f"{summary}Link: {item.original_url}"
    )


def create_server(
    *,
    store_path: Path,
    fetcher: Fetcher,
    clock: Clock,
    sources: tuple[Source, ...] = DEFAULT_SOURCES,
    config_path: Path | None = None,
    collection_wait: timedelta = COLLECTION_WAIT,
    host_interval: timedelta = HOST_INTERVAL,
) -> MCPServer:
    sources = configured_sources(sources, config_path)
    store = Store(store_path)
    paced_fetcher = HostPacedFetcher(fetcher, host_interval)
    collector = Collector(sources, store, paced_fetcher, clock)

    @asynccontextmanager
    async def lifespan(_: MCPServer) -> AsyncGenerator[None]:
        if collector.is_stale():
            collector.start()  # in the background: the server answers queries meanwhile
        try:
            yield
        finally:
            collector.stop()

    known_source_ids = {source.id for source in sources}
    server = MCPServer(PROJECT_NAME, version=VERSION, lifespan=lifespan)
    tool = async_tool(server)

    @tool
    async def collect_now() -> CollectReport:
        """Collect new Items from every Source now.

        Use only when the user asks to refresh or collect now: `whats_new` already
        collects by itself when the data is over 24 hours old. Takes about a minute.
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
        """Every Source with its URL, default Categories and collection state.

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
    async def search(
        query: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        categories: list[Category] | None = None,
        sources: list[str] | None = None,
        limit: Annotated[int, Field(ge=1)] = SEARCH_LIMIT,
    ) -> SearchResult:
        """Search stored Items by text, publish time, Category and Source, in any mix.

        Use for a question about a subject or time span, such as last week's Engineering
        Items about MCP or what was published today, and whenever `whats_new` is not
        clearly asked for. Every filter is optional; an omitted one matches every Item.
        `query`: the title or the whole summary contains it (case-insensitive); a summary
        shown is plain text cut to about 500 characters; `read_item` gives the full text.
        `since` / `until`:
        published at or after `since` and before `until`, ISO 8601; a time without an
        offset, or a date alone (midnight), is UTC. `categories`: in any of them (News,
        Applications, Engineering, Models; see `whats_new`). `sources`: from any of these
        Source ids (see `list_sources`). An empty `categories` or `sources` list matches
        nothing. Results are newest first, at most `limit` (default 20). Searching never
        moves a Checkpoint.
        """
        if sources is not None:
            unknown = [source_id for source_id in sources if source_id not in known_source_ids]
            if unknown:
                raise ToolError(
                    f"No Source has id {', '.join(map(repr, unknown))}. "
                    f"Known Source ids: {', '.join(sorted(known_source_ids))}."
                )
        items = store.search(
            query=query,
            since=as_utc(since),
            until=as_utc(until),
            categories=categories,
            source_ids=sources,
            limit=limit,
        )
        return SearchResult(items=[ItemView.of(item) for item in items])

    @tool
    async def read_item(id: int) -> FullText:
        """The full text of an Item: fetches its original page and extracts the main text.

        Use when an Item's summary is not enough. `id` is an Item's `id` from `whats_new`
        or `search`. If the page cannot be fetched or has no main text, the error gives the
        Item's summary and link instead.
        """
        item = store.item(id)
        if item is None:
            raise ToolError(f"No Item has id {id}. Use an id from whats_new or search.")
        try:
            page = await paced_fetcher.get(item.original_url)
        except FetchError as error:
            reason = f"its page could not be fetched ({error})"
            raise ToolError(unreadable_message(item, reason)) from error
        text = await asyncio.to_thread(extract_main_text, page)
        if text is None:
            reason = "no main text could be extracted from its page"
            raise ToolError(unreadable_message(item, reason))
        return FullText(id=item.id, title=item.title, url=item.original_url, text=text)

    @tool
    async def whats_new(
        categories: list[Category] | None = None,
        limit: Annotated[int, Field(ge=1)] = WHATS_NEW_LIMIT,
    ) -> WhatsNew:
        """What's New: Items collected since the last Checkpoint and published in the last 7 days.

        Use only when the user asks for what is new since they last looked: what's new in
        AI or in some Categories, anything new, today's briefing. Calling it marks Items as
        seen and cannot be undone, so for anything else use `search`, which never does: a
        time span ("today", "recently", "this week"), a subject ("what's new with MCP"), or
        when unsure. Each Category has its own Checkpoint;
        only the Checkpoints of the Categories asked about (omitted: all) move to now, so
        Items shown once are not shown again. Every client of this server shares the
        Checkpoints. `previous_checkpoints` gives each asked Category's Checkpoint before this
        call (null: never viewed). If `items` is empty, tell the user when they last looked
        and offer `search` for recently published Items.

        Results are newest first, up to `limit` (default 100); Items published at the same
        time are never split, so a few more or fewer can be shown. `more` counts the Items
        left out; they count as seen too, so tell the user and offer `search` with the same
        `categories`, `since` 7 days ago and `until` the oldest shown Item's `published_at`.
        Summaries are plain text cut to about 500 characters; `read_item` gives the full text.

        Categories (an Item can be in several):
        News: Events in the AI industry, such as launches, funding, policy, and people
        changes.
        Applications: New AI products or tools that you can use right away.
        Engineering: Content about how to build AI systems, such as technical posts,
        frameworks, lessons from practice, and releases.
        Models: Newly released or newly listed AI models, and changes to what they can do and
        what they cost. Academic papers and theory are not included.

        If the data is over 24 hours old this collects first, which can take about a minute;
        `note` says when the collection was still running. `warning` names Sources that
        failed 3 or more collections in a row: tell the user.
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
        checkpoints = store.checkpoints()
        previous = {category: checkpoints.get(category) for category in categories}
        items = store.collected_after(previous, published_since=now - WHATS_NEW_LOOKBACK)
        shown = shown_items(items, limit)
        store.move_checkpoints(categories, now)
        return WhatsNew(
            warning=failing_sources_warning(sources, store.source_health()),
            previous_checkpoints=previous,
            items=[ItemView.of(item) for item in shown],
            more=len(items) - len(shown),
            note=note,
        )

    return server
