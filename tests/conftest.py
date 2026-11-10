from __future__ import annotations

from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from mcp import Client

from ai_news_mcp.fetcher import FetchError
from ai_news_mcp.server import create_server

FIXTURES = Path(__file__).parent / "fixtures"
OPENAI_NEWS_URL = "https://openai.com/news/rss.xml"


class FakeFetcher:
    """Serves fixture files by URL; any other URL fails like a 404."""

    def __init__(self) -> None:
        self.responses: dict[str, bytes] = {}

    def serve(self, url: str, fixture: str) -> None:
        self.responses[url] = (FIXTURES / fixture).read_bytes()

    async def get(self, url: str) -> bytes:
        if url not in self.responses:
            raise FetchError(f"404 Not Found: {url}")
        return self.responses[url]


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
    """Opens an in-memory MCP client against a server on a temporary store."""

    @asynccontextmanager
    async def _connect() -> AsyncGenerator[Client]:
        server = create_server(store_path=tmp_path / "store.sqlite3", fetcher=fetcher, clock=clock)
        async with Client(server) as client:
            yield client

    return _connect


async def call(client: Client, tool: str, **arguments: Any) -> Any:
    result = await client.call_tool(tool, arguments)
    assert not result.is_error, result.content
    assert result.structured_content is not None
    return result.structured_content
