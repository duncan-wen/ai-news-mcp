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


# openai_rss.xml, collected on 11 Nov 12:00, holds 4 Items from 9-10 Nov and 2 from 28 Oct.
LAST_7_DAYS = {
    "https://openai.com/index/helping-caregivers-use-ai-in-everyday-life",
    "https://openai.com/index/closing-ai-guidance-gap-education",
    "https://openai.com/index/ai-effect-on-freelance-work",
    "https://openai.com/index/chatgpt-enterprise-aws-marketplace",
}


def urls(result) -> set[str]:
    return {item["url"] for item in result["items"]}


async def test_first_whats_new_leaves_out_backfilled_items_published_over_7_days_ago(connect):
    async with connect() as client:
        await call(client, "collect_now")
        result = await call(client, "whats_new")

    assert urls(result) == LAST_7_DAYS


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

    assert urls(first) == LAST_7_DAYS
    assert again["items"] == []
    [item] = later["items"]
    assert {key: item[key] for key in ("title", "source", "categories", "published_at", "url")} == {
        "title": "Control Room: A central system to track and stop model workloads across our "
        "research infrastructure",
        "source": "openai-news",
        "categories": ["News"],
        "published_at": "2026-11-09T13:00:00Z",
        "url": "https://openai.com/index/control-room",
    }
    assert item["summary"].startswith("Learn how OpenAI’s Control Room tracks model workloads")


async def test_whats_new_leaves_out_an_item_collected_late_but_published_over_7_days_ago(
    connect, fetcher, clock
):
    fetcher.serve_nothing()  # every collection fails until the fixture is served
    async with connect() as client:
        await call(client, "whats_new")  # 11 Nov: Checkpoint before anything is collected
        fetcher.serve(OPENAI_NEWS_URL, "openai_rss_next_day.xml")
        clock.advance(timedelta(days=10))
        await call(client, "collect_now")  # 21 Nov: Control Room, published 9 Nov
        result = await call(client, "whats_new")
        found = await call(client, "search", query="Control Room")

    assert result["items"] == []
    assert [item["url"] for item in found["items"]] == ["https://openai.com/index/control-room"]


async def test_items_carry_every_default_category_of_their_source(connect):
    async with connect(NEWS_AND_MODELS) as client:
        await call(client, "collect_now")
        result = await call(client, "whats_new")
        found = await call(client, "search", query="AWS Marketplace")

    assert all({"News", "Models"} <= set(item["categories"]) for item in result["items"])
    assert [item["categories"] for item in found["items"]] == [["News", "Models"]]


async def test_whats_new_for_some_categories_leaves_other_categories_checkpoints_alone(
    connect, clock
):
    async with connect(NEWS_AND_MODELS) as client:
        await call(client, "collect_now")
        models = await call(client, "whats_new", categories=["Models"])
        clock.advance(timedelta(hours=1))
        models_again = await call(client, "whats_new", categories=["Models"])
        everything = await call(client, "whats_new")
        clock.advance(timedelta(hours=1))
        news_again = await call(client, "whats_new", categories=["News"])

    # Every Item is in both Categories: seen under Models, it still shows up under News.
    assert urls(models) == LAST_7_DAYS
    assert models_again["items"] == []
    assert [item["id"] for item in everything["items"]] == [item["id"] for item in models["items"]]
    assert news_again["items"] == []


async def test_whats_new_for_one_category_returns_only_items_in_it(connect):
    async with connect() as client:  # openai-news is News only
        await call(client, "collect_now")
        models = await call(client, "whats_new", categories=["Models"])
        news = await call(client, "whats_new", categories=["News"])

    assert models["items"] == []
    assert urls(news) == LAST_7_DAYS


async def test_search_does_not_move_any_checkpoint(connect):
    async with connect() as client:
        await call(client, "collect_now")
        await call(client, "search", query="chatgpt")
        result = await call(client, "whats_new")

    assert urls(result) == LAST_7_DAYS


async def test_collecting_does_not_move_any_checkpoint(connect, fetcher, clock):
    async with connect() as client:
        await call(client, "collect_now")
        fetcher.serve(OPENAI_NEWS_URL, "openai_rss_next_day.xml")
        clock.advance(timedelta(hours=1))
        await call(client, "collect_now")
        result = await call(client, "whats_new")

    assert urls(result) == LAST_7_DAYS | {"https://openai.com/index/control-room"}


async def test_whats_new_for_no_categories_moves_no_checkpoint(connect):
    async with connect() as client:
        await call(client, "collect_now")
        none = await call(client, "whats_new", categories=[])
        result = await call(client, "whats_new")

    assert none["items"] == []
    assert urls(result) == LAST_7_DAYS


async def test_whats_new_gives_the_checkpoints_it_moved_from(connect, clock):
    async with connect() as client:
        await call(client, "collect_now")
        first = await call(client, "whats_new")  # 11 Nov 12:00
        clock.advance(timedelta(hours=3))
        news = await call(client, "whats_new", categories=["News"])

    assert first["previous_checkpoints"] == {
        "News": None,
        "Applications": None,
        "Engineering": None,
        "Models": None,
    }
    assert news["previous_checkpoints"] == {"News": "2026-11-11T12:00:00Z"}


async def test_whats_new_returns_the_newest_items_up_to_its_limit_and_counts_the_rest(
    connect, clock
):
    async with connect() as client:
        await call(client, "collect_now")
        first = await call(client, "whats_new", limit=2)
        clock.advance(timedelta(hours=1))
        again = await call(client, "whats_new")
        rest = await call(
            client, "search", since="2026-11-04T12:00:00Z", until=first["items"][-1]["published_at"]
        )

    assert [item["published_at"] for item in first["items"]] == [
        "2026-11-10T12:00:00Z",
        "2026-11-10T09:00:00Z",
    ]
    assert first["more"] == 2
    assert again["items"] == []  # the 2 left out count as seen
    assert again["more"] == 0
    assert urls(rest) == LAST_7_DAYS - urls(first)


async def test_whats_new_never_leaves_out_an_item_published_at_the_same_time_as_one_shown(
    connect, fetcher
):
    # Its 4 Items from the last 7 days: 2 published 10 Nov 09:00, 2 published 10 Nov 07:00.
    fetcher.serve(OPENAI_NEWS_URL, "openai_rss_same_times.xml")
    async with connect() as client:
        await call(client, "collect_now")
        first = await call(client, "whats_new", limit=3)
        rest = await call(
            client, "search", since="2026-11-04T12:00:00Z", until=first["items"][-1]["published_at"]
        )

    # The 3rd Item would split the 07:00 pair, so both wait for `search`.
    assert [item["published_at"] for item in first["items"]] == [
        "2026-11-10T09:00:00Z",
        "2026-11-10T09:00:00Z",
    ]
    assert first["more"] == 2
    assert [item["published_at"] for item in rest["items"]] == [
        "2026-11-10T07:00:00Z",
        "2026-11-10T07:00:00Z",
    ]


async def test_whats_new_goes_over_its_limit_rather_than_split_the_newest_items(connect, fetcher):
    fetcher.serve(OPENAI_NEWS_URL, "openai_rss_same_times.xml")
    async with connect() as client:
        await call(client, "collect_now")
        first = await call(client, "whats_new", limit=1)

    assert [item["published_at"] for item in first["items"]] == [
        "2026-11-10T09:00:00Z",
        "2026-11-10T09:00:00Z",
    ]
    assert first["more"] == 2
