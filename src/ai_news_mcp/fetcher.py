from __future__ import annotations

from importlib.metadata import version
from typing import Protocol

import httpx

PROJECT_NAME = "ai-news-mcp"
REPOSITORY_URL = "https://github.com/duncan-wen/ai-news-mcp"
VERSION = version(PROJECT_NAME)
USER_AGENT = f"{PROJECT_NAME}/{VERSION} (+{REPOSITORY_URL})"
TIMEOUT_SECONDS = 30.0


class FetchError(Exception):
    """A request failed: network error, timeout or non-2xx status."""


class Fetcher(Protocol):
    """Every outbound HTTP request goes through a Fetcher."""

    async def get(self, url: str) -> bytes:
        """Return the response body, or raise FetchError."""
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
