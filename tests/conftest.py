from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from mcp import Client
from mcp.types import TextContent

from ai_news_mcp.fetcher import FetchError
from ai_news_mcp.server import create_server
from ai_news_mcp.sources import DEFAULT_SOURCES, Source

FIXTURES = Path(__file__).parent / "fixtures"
OPENAI_NEWS_URL = "https://openai.com/news/rss.xml"


def first_version_source(source_id: str) -> Source:
    return next(source for source in DEFAULT_SOURCES if source.id == source_id)


# Most tests collect this one Source; a test of the whole first-version list passes it.
OPENAI_NEWS = first_version_source("openai-news")

# Two News Sources whose keywords add other Categories to some Items.
# A test file collecting them overrides `fetcher` to call serve_mistral_and_the_verge.
MISTRAL_AND_THE_VERGE = (first_version_source("mistral-news"), first_version_source("the-verge-ai"))


def serve_mistral_and_the_verge(fetcher: FakeFetcher) -> None:
    fetcher.serve(MISTRAL_AND_THE_VERGE[0].url, "mistral_rss.xml")  # served as text/plain
    fetcher.serve(MISTRAL_AND_THE_VERGE[1].url, "verge_atom.xml")


class FakeFetcher:
    """Serves fixture files by URL; any other URL fails like a 404.

    A body is served only from a fixture file (`serve`), since parsing is tested only
    through them. `fail(url, error)` makes a URL raise that error instead, such as a 410 or
    a timeout; `serve_nothing()` makes every URL fail, as when offline.
    `hold()` makes every request wait until `release()`, to keep a collection running.
    """

    def __init__(self) -> None:
        self._responses: dict[str, bytes] = {}
        self.failures: dict[str, FetchError] = {}
        self.requests: list[str] = []
        self.requested = asyncio.Event()
        self._released = asyncio.Event()
        self._released.set()

    def serve(self, url: str, fixture: str) -> None:
        self.failures.pop(url, None)
        self._responses[url] = (FIXTURES / fixture).read_bytes()

    def serve_nothing(self) -> None:
        self._responses.clear()

    def fail(self, url: str, error: FetchError) -> None:
        self.failures[url] = error

    def hold(self) -> None:
        self._released.clear()

    def release(self) -> None:
        self._released.set()

    async def get(self, url: str) -> bytes:
        self.requests.append(url)
        self.requested.set()
        await self._released.wait()
        if url in self.failures:
            raise self.failures[url]
        if url not in self._responses:
            raise FetchError(f"404 Not Found: {url}")
        return self._responses[url]


class FakeClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        self._now += delta


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def fetcher() -> FakeFetcher:
    fake = FakeFetcher()
    fake.serve(OPENAI_NEWS_URL, "openai_rss.xml")
    return fake


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(datetime(2026, 11, 11, 12, 0, tzinfo=UTC))


@pytest.fixture
def connect(tmp_path: Path, fetcher: FakeFetcher, clock: FakeClock) -> Callable[[], Any]:
    """Opens an in-memory MCP client against a server on a temporary store.

    A server whose store was never collected, or last collected over 24 hours ago, starts
    a collection on connect, before the test's first tool call. `whats_new` waits for it.
    `fetcher.hold()` keeps it running, so a tool call can join it or see what a client
    gets meanwhile. Without `hold()` it may finish before the first tool call: a following
    `collect_now` then runs a second collection, so assert its `added`, or count
    `fetcher.requests`, only after a collection the test itself waited for, or after
    clearing them.

    Advancing the Clock by exactly 1 day does not make the data stale (it must be over
    24 hours old), so `whats_new` does not collect then: call `collect_now` to collect the
    next day's fixture.

    Requests to one host are not spaced out unless a test passes `host_interval`: the
    production interval is real time, which the Clock does not control.
    """

    @asynccontextmanager
    async def _connect(
        sources: tuple[Source, ...] = (OPENAI_NEWS,), **settings: Any
    ) -> AsyncGenerator[Client]:
        settings.setdefault("host_interval", timedelta(0))
        server = create_server(
            store_path=tmp_path / "store.sqlite3",
            fetcher=fetcher,
            clock=clock,
            sources=sources,
            **settings,
        )
        async with Client(server) as client:
            yield client

    return _connect


async def call(client: Client, tool: str, **arguments: Any) -> Any:
    result = await client.call_tool(tool, arguments)
    assert not result.is_error, result.content
    assert result.structured_content is not None
    return result.structured_content


async def call_error(client: Client, tool: str, **arguments: Any) -> str:
    """Call a tool that should fail; return the error text a client sees.

    The SDK puts "Error executing tool <name>: " before the tool's own message, so match
    the message with `in`, not `==`.
    """
    result = await client.call_tool(tool, arguments)
    assert result.is_error, result.structured_content
    [content] = result.content
    assert isinstance(content, TextContent)
    return content.text
