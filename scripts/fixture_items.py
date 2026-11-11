"""Print the Items that fixtures collect into, as a test would see them.

    uv run scripts/fixture_items.py mistral-news=mistral_rss.xml the-verge-ai=verge_atom.xml

Each argument is a Source id from the first-version list and a file in tests/fixtures.
The script collects them once through the MCP tools, at the fixtures' download time
(11 Nov 2026 12:00 UTC, the tests' Clock; `--now` changes it), so the 30-day backfill
applies. It prints one line per Item, newest first: publish time, Source, Categories
(after keyword classification) and title.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from mcp import Client

from ai_news_mcp.fetcher import FetchError
from ai_news_mcp.server import create_server
from ai_news_mcp.sources import DEFAULT_SOURCES, Source

FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures"
DOWNLOADED = datetime(2026, 11, 11, 12, 0, tzinfo=UTC)


class FixtureFetcher:
    def __init__(self, responses: dict[str, bytes]) -> None:
        self._responses = responses

    async def get(self, url: str) -> bytes:
        if url not in self._responses:
            raise FetchError(f"404 Not Found: {url}")
        return self._responses[url]


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


def parse_pair(text: str) -> tuple[Source, Path]:
    source_id, _, fixture = text.partition("=")
    source = next((source for source in DEFAULT_SOURCES if source.id == source_id), None)
    if source is None:
        known = ", ".join(source.id for source in DEFAULT_SOURCES)
        raise argparse.ArgumentTypeError(f"no Source has id {source_id!r}; known: {known}")
    path = FIXTURES / fixture
    if not fixture or not path.is_file():
        raise argparse.ArgumentTypeError(f"no fixture {path}")
    return source, path


async def main() -> None:
    parser = argparse.ArgumentParser(description="Print the Items that fixtures collect into.")
    parser.add_argument("pairs", nargs="+", type=parse_pair, metavar="SOURCE_ID=FIXTURE")
    parser.add_argument(
        "--now", type=datetime.fromisoformat, default=DOWNLOADED, help="ISO 8601, with offset"
    )
    arguments = parser.parse_args()
    if arguments.now.tzinfo is None:
        parser.error("--now needs an offset, such as 2026-11-11T12:00:00+00:00")
    pairs: list[tuple[Source, Path]] = arguments.pairs
    source_ids = [source.id for source, _ in pairs]
    repeated = sorted({source_id for source_id in source_ids if source_ids.count(source_id) > 1})
    if repeated:
        # One URL serves one fixture, so a second fixture would replace the first.
        parser.error(f"one fixture per Source; run once per fixture of {', '.join(repeated)}")
    with tempfile.TemporaryDirectory() as store_dir:
        server = create_server(
            store_path=Path(store_dir) / "store.sqlite3",
            fetcher=FixtureFetcher({source.url: path.read_bytes() for source, path in pairs}),
            clock=FixedClock(arguments.now),
            sources=tuple(source for source, _ in pairs),
            host_interval=timedelta(0),
        )
        async with Client(server) as client:
            report = (await client.call_tool("collect_now", {})).structured_content or {}
            result = await client.call_tool("search", {"limit": 10_000})
    for failure in report.get("failed", []):
        print(f"failed: {failure['source']}: {failure['error']}", file=sys.stderr)
    for item in (result.structured_content or {}).get("items", []):
        categories = ",".join(item["categories"])
        print(
            f"{item['published_at']}  {item['source']}  [{categories}]  {item['title']}  "
            f"{item['url']}"
        )


if __name__ == "__main__":
    asyncio.run(main())
