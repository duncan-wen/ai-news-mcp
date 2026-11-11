from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import timedelta
from importlib.metadata import version
from typing import Protocol
from urllib.parse import urlsplit

import httpx

PROJECT_NAME = "ai-news-mcp"
REPOSITORY_URL = "https://github.com/duncan-wen/ai-news-mcp"
VERSION = version(PROJECT_NAME)
USER_AGENT = f"{PROJECT_NAME}/{VERSION} (+{REPOSITORY_URL})"
TIMEOUT_SECONDS = 30.0
HOST_INTERVAL = timedelta(seconds=1)


class FetchError(Exception):
    """A request failed: network error, timeout or non-2xx status."""


class Fetcher(Protocol):
    """Every outbound HTTP request goes through a Fetcher."""

    async def get(self, url: str) -> bytes:
        """Return the response body, or raise FetchError.

        Only the body: adapters never see the content type, which some Sources get wrong
        (Mistral serves its RSS as text/plain).
        """
        ...


class HttpFetcher:
    async def get(self, url: str) -> bytes:
        try:
            async with httpx.AsyncClient(
                headers={"User-Agent": USER_AGENT},
                timeout=TIMEOUT_SECONDS,
                follow_redirects=True,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
        except httpx.HTTPError as error:
            raise FetchError(f"{url}: {error}") from error


class HostPacedFetcher:
    """Wraps a Fetcher so that requests to one host go one at a time, `interval` apart.

    The interval runs from the end of one request to the start of the next. Requests to
    different hosts do not wait for each other.
    """

    def __init__(self, fetcher: Fetcher, interval: timedelta) -> None:
        self._fetcher = fetcher
        self._interval = interval.total_seconds()
        self._locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._finished_at: dict[str, float] = {}  # event loop time

    async def get(self, url: str) -> bytes:
        host = (urlsplit(url).hostname or "").lower()
        loop = asyncio.get_running_loop()
        async with self._locks[host]:
            if host in self._finished_at:
                await asyncio.sleep(self._finished_at[host] + self._interval - loop.time())
            try:
                return await self._fetcher.get(url)
            finally:
                self._finished_at[host] = loop.time()
