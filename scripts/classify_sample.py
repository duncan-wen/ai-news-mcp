"""Show what the keyword rules add to the newest real Items of every default Source.

    uv run scripts/classify_sample.py [--items 10] [--source mistral-news ...]

Downloads each Source now (real network, by hand only: tests never do, ADR 0004) and
prints, per Item, the Categories added beyond the Source's defaults and the keywords
that added them. Use it to tune the rules in src/ai_news_mcp/classification.py.
"""

from __future__ import annotations

import argparse
import asyncio

from ai_news_mcp.adapters import FormatError, parse_rss
from ai_news_mcp.classification import keyword_matches
from ai_news_mcp.fetcher import HOST_INTERVAL, FetchError, HostPacedFetcher, HttpFetcher
from ai_news_mcp.sources import DEFAULT_SOURCES, Source


async def sample(source: Source, fetcher: HostPacedFetcher, items: int) -> str:
    defaults = "+".join(source.default_categories)
    lines = [f"== {source.id} [{defaults}]"]
    try:
        parsed_items = parse_rss(await fetcher.get(source.url))
    except (FetchError, FormatError) as error:
        return "\n".join([*lines, f"   failed: {error}"])
    for parsed in parsed_items[:items]:
        added = {
            category.value: sorted(set(keywords), key=str.lower)
            for category, keywords in keyword_matches(parsed.title, parsed.summary).items()
            if category not in source.default_categories
        }
        lines.append(f"   {added or '-'} | {parsed.title[:90]}")
    return "\n".join(lines)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Show what the keyword rules add.")
    parser.add_argument("--items", type=int, default=10, help="newest Items per Source")
    parser.add_argument("--source", action="append", help="a Source id (default: all)")
    arguments = parser.parse_args()

    sources = [s for s in DEFAULT_SOURCES if arguments.source is None or s.id in arguments.source]
    fetcher = HostPacedFetcher(HttpFetcher(), HOST_INTERVAL)
    for report in await asyncio.gather(*(sample(s, fetcher, arguments.items) for s in sources)):
        print(report)


if __name__ == "__main__":
    asyncio.run(main())
