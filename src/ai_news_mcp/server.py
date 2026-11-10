"""The MCP server and its tools."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar

from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel

from .clock import Clock
from .collector import Collector
from .fetcher import PROJECT_NAME, VERSION, Fetcher
from .sources import DEFAULT_SOURCES, Source
from .store import Store

SEARCH_LIMIT = 20

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


class CollectReport(BaseModel):
    sources: list[SourceCollectReport]


class ItemView(BaseModel):
    id: int
    title: str
    source: str
    published_at: datetime
    summary: str
    url: str


class SearchResult(BaseModel):
    items: list[ItemView]


def create_server(
    *,
    store_path: Path,
    fetcher: Fetcher,
    clock: Clock,
    sources: tuple[Source, ...] = DEFAULT_SOURCES,
) -> MCPServer:
    store = Store(store_path)
    collector = Collector(sources, store, fetcher, clock)
    server = MCPServer(PROJECT_NAME, version=VERSION)
    tool = async_tool(server)

    @tool
    async def collect_now() -> CollectReport:
        """Collect new Items from every Source now and report how many each Source added."""
        reports = await collector.collect()
        return CollectReport(
            sources=[SourceCollectReport(source=r.source, added=r.added) for r in reports]
        )

    @tool
    async def search(query: str) -> SearchResult:
        """Search stored Items whose title or summary contains `query` (case-insensitive).

        Results are newest first, at most 20. Searching never moves a Checkpoint.
        """
        return SearchResult(
            items=[
                ItemView(
                    id=item.id,
                    title=item.title,
                    source=item.source_id,
                    published_at=item.published_at,
                    summary=item.summary,
                    url=item.original_url,
                )
                for item in store.search(query, SEARCH_LIMIT)
            ]
        )

    return server
