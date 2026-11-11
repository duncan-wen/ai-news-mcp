from __future__ import annotations

import pytest

from ai_news_mcp.sources import DEFAULT_SOURCES

from .conftest import call, search_collected, serve_mistral_and_the_verge

pytestmark = pytest.mark.anyio


@pytest.fixture
def fetcher(fetcher):
    serve_mistral_and_the_verge(fetcher)
    return fetcher


async def test_the_first_version_sources_collect_rss_atom_and_text_plain_responses(connect):
    # Every other Source answers 404 from the fake Fetcher.
    async with connect(DEFAULT_SOURCES) as client:
        result = await search_collected(client)

    collected: dict[str, int] = {}
    for item in result["items"]:
        collected[item["source"]] = collected.get(item["source"], 0) + 1
    # Since 12 Oct (30 days): OpenAI 6 of 8 Items, Mistral 4 of 6, The Verge all 5.
    assert collected == {"openai-news": 6, "mistral-news": 4, "the-verge-ai": 5}


async def test_every_first_version_source_has_default_categories(connect):
    async with connect(DEFAULT_SOURCES) as client:
        result = await call(client, "list_sources")

    by_category: dict[str, set[str]] = {}
    for source in result["sources"]:
        assert source["default_categories"], source["id"]
        for category in source["default_categories"]:
            by_category.setdefault(category, set()).add(source["id"])
    assert {"openai-news", "mistral-news", "the-verge-ai", "anthropic-news"} <= by_category["News"]
    assert {"simon-willison", "vllm-releases"} <= by_category["Engineering"]
    assert by_category["Applications"] == {"product-hunt-ai", "hacker-news-ai"}
    assert by_category["Models"] == {"hugging-face-models", "openrouter-models"}
