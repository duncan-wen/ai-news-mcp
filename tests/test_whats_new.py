from __future__ import annotations

from datetime import timedelta

import pytest

from ai_news_mcp.sources import Category, Source

from .conftest import OPENAI_NEWS_URL, call

pytestmark = pytest.mark.anyio

NEWS_AND_MODELS = (
    Source(
        id="openai-news",
        name="OpenAI News",
        kind="rss",
        url=OPENAI_NEWS_URL,
        default_categories=(Category.NEWS, Category.MODELS),
    ),
)


async def test_first_whats_new_returns_items_collected_in_the_last_7_days(connect, fetcher, clock):
    async with connect() as client:
        await call(client, "collect_now")  # 11 Nov: 6 Items
        fetcher.serve(OPENAI_NEWS_URL, "openai_rss_next_day.xml")
        clock.advance(timedelta(days=8))
        await call(client, "collect_now")  # 19 Nov: 1 new Item ("Control Room")
        result = await call(client, "whats_new")

    [item] = result["items"]
    assert {key: item[key] for key in ("title", "source", "categories", "published_at", "url")} == {
        "title": "Control Room: A central system to track and stop model workloads across our "
        "research infrastructure",
        "source": "openai-news",
        "categories": ["News"],
        "published_at": "2026-11-09T13:00:00Z",
        "url": "https://openai.com/index/control-room",
    }
    assert item["summary"].startswith("Learn how OpenAI’s Control Room tracks model workloads")


async def test_whats_new_returns_only_items_collected_since_the_last_whats_new(
    connect, fetcher, clock
):
    async with connect() as client:
        await call(client, "collect_now")
        first = await call(client, "whats_new")
        clock.advance(timedelta(hours=1))
        again = await call(client, "whats_new")
        fetcher.serve(OPENAI_NEWS_URL, "openai_rss_next_day.xml")
        clock.advance(timedelta(hours=1))
        await call(client, "collect_now")
        later = await call(client, "whats_new")

    assert len(first["items"]) == 6
    assert again["items"] == []
    assert [item["url"] for item in later["items"]] == ["https://openai.com/index/control-room"]


async def test_whats_new_looks_back_at_most_7_days_even_after_a_long_absence(
    connect, fetcher, clock
):
    async with connect() as client:
        await call(client, "whats_new")  # 11 Nov: Checkpoint before anything is collected
        clock.advance(timedelta(days=1))
        await call(client, "collect_now")  # 12 Nov: 6 Items
        fetcher.serve(OPENAI_NEWS_URL, "openai_rss_next_day.xml")
        clock.advance(timedelta(days=10))
        await call(client, "collect_now")  # 22 Nov: 1 new Item
        result = await call(client, "whats_new")

    assert [item["url"] for item in result["items"]] == ["https://openai.com/index/control-room"]


async def test_items_carry_every_default_category_of_their_source(connect):
    async with connect(NEWS_AND_MODELS) as client:
        await call(client, "collect_now")
        result = await call(client, "whats_new")
        found = await call(client, "search", query="AWS Marketplace")

    assert {tuple(item["categories"]) for item in result["items"]} == {("News", "Models")}
    assert [item["categories"] for item in found["items"]] == [["News", "Models"]]


async def test_whats_new_for_some_categories_leaves_other_categories_checkpoints_alone(
    connect, clock
):
    async with connect(NEWS_AND_MODELS) as client:
        await call(client, "collect_now")
        models = await call(client, "whats_new", categories=["Models"])
        clock.advance(timedelta(hours=1))
        models_again = await call(client, "whats_new", categories=["Models"])
        news = await call(client, "whats_new", categories=["News"])
        clock.advance(timedelta(hours=1))
        everything = await call(client, "whats_new")

    # Every Item is in both Categories: seen under Models, it still shows up under News.
    assert len(models["items"]) == 6
    assert models_again["items"] == []
    assert [item["id"] for item in news["items"]] == [item["id"] for item in models["items"]]
    assert everything["items"] == []


async def test_whats_new_for_one_category_returns_only_items_in_it(connect):
    async with connect() as client:  # openai-news is News only
        await call(client, "collect_now")
        models = await call(client, "whats_new", categories=["Models"])
        news = await call(client, "whats_new", categories=["News"])

    assert models["items"] == []
    assert len(news["items"]) == 6


async def test_search_does_not_move_any_checkpoint(connect):
    async with connect() as client:
        await call(client, "collect_now")
        await call(client, "search", query="chatgpt")
        result = await call(client, "whats_new")

    assert len(result["items"]) == 6


async def test_collecting_does_not_move_any_checkpoint(connect, fetcher, clock):
    async with connect() as client:
        await call(client, "collect_now")
        fetcher.serve(OPENAI_NEWS_URL, "openai_rss_next_day.xml")
        clock.advance(timedelta(hours=1))
        await call(client, "collect_now")
        result = await call(client, "whats_new")

    assert len(result["items"]) == 7


async def test_whats_new_for_no_categories_moves_no_checkpoint(connect):
    async with connect() as client:
        await call(client, "collect_now")
        none = await call(client, "whats_new", categories=[])
        result = await call(client, "whats_new")

    assert none["items"] == []
    assert len(result["items"]) == 6
