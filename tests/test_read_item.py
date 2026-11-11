from __future__ import annotations

import pytest

from ai_news_mcp.fetcher import FetchError

from .conftest import call, first_version_source

pytestmark = pytest.mark.anyio

THE_VERGE_AI = first_version_source("the-verge-ai")
THE_VERGE_AI_URL = "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"
CARBON_URL = "https://www.theverge.com/ai-artificial-intelligence/1030787/google-gemini-4-carbon-public-rollout"


@pytest.fixture
def fetcher(fetcher):
    fetcher.serve(THE_VERGE_AI_URL, "verge_atom.xml")
    return fetcher


async def carbon_item(client) -> dict:
    await call(client, "collect_now")
    [item] = (await call(client, "search", query="Gemini 4 Carbon"))["items"]
    return item


async def test_read_item_returns_the_main_text_of_the_original_page(connect, fetcher):
    fetcher.serve(CARBON_URL, "verge_item_page.html")
    async with connect((THE_VERGE_AI,)) as client:
        item = await carbon_item(client)
        result = await call(client, "read_item", id=item["id"])

    assert result["title"] == "Google releases Gemini 4 Carbon with agent ‘swarm’ feature"
    assert result["url"] == CARBON_URL
    # The feed's summary stops at "pushes […]"; the page goes on.
    assert result["text"].startswith("Google is rolling out its latest AI model, Gemini 4 Carbon")
    page_only = "referring to the company’s other frontier model that launched only last month"
    assert page_only in result["text"]


async def read_item_error(client, item_id: int) -> str:
    result = await client.call_tool("read_item", {"id": item_id})
    assert result.is_error
    [content] = result.content
    return content.text


CARBON_SUMMARY_START = "Google is rolling out its latest AI model, Gemini 4 Carbon, to the general"


async def test_a_page_that_cannot_be_fetched_gives_an_error_with_the_summary_and_link(
    connect, fetcher
):
    fetcher.fail(CARBON_URL, FetchError(f"403 Forbidden: {CARBON_URL}"))
    async with connect((THE_VERGE_AI,)) as client:
        item = await carbon_item(client)
        error = await read_item_error(client, item["id"])

    assert "could not be fetched" in error
    assert "403 Forbidden" in error
    assert CARBON_SUMMARY_START in error
    assert f"Link: {CARBON_URL}" in error


async def test_a_page_with_no_main_text_gives_an_error_with_the_summary_and_link(connect, fetcher):
    fetcher.serve(CARBON_URL, "script_only_page.html")
    async with connect((THE_VERGE_AI,)) as client:
        item = await carbon_item(client)
        error = await read_item_error(client, item["id"])

    assert "no main text could be extracted" in error
    assert CARBON_SUMMARY_START in error
    assert f"Link: {CARBON_URL}" in error


async def test_an_id_no_item_has_gives_an_error(connect):
    async with connect((THE_VERGE_AI,)) as client:
        await carbon_item(client)
        error = await read_item_error(client, 999)

    assert "No Item has id 999. Use an id from whats_new or search." in error


async def test_collecting_does_not_fetch_the_pages_of_items(connect, fetcher):
    async with connect((THE_VERGE_AI,)) as client:
        await carbon_item(client)

    assert set(fetcher.requests) == {THE_VERGE_AI_URL}
