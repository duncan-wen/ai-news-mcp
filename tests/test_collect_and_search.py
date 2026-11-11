from __future__ import annotations

from datetime import timedelta

import pytest

from .conftest import OPENAI_NEWS_URL, call, search_collected

pytestmark = pytest.mark.anyio


async def test_first_collection_only_keeps_items_published_in_the_last_30_days(connect):
    async with connect() as client:
        result = await search_collected(client)

    # The fixture has 8 Items: 6 from 28 Oct - 10 Nov 2026, 2 from June 2026.
    assert len(result["items"]) == 6


async def test_search_returns_the_matching_item_with_its_details(connect):
    async with connect() as client:
        await call(client, "collect_now")
        result = await call(client, "search", query="AWS Marketplace")

    [item] = result["items"]
    assert {key: item[key] for key in ("title", "source", "published_at", "url")} == {
        "title": "ChatGPT Enterprise now available in AWS Marketplace",
        "source": "openai-news",
        "published_at": "2026-11-09T19:00:00Z",
        "url": "https://openai.com/index/chatgpt-enterprise-aws-marketplace",
    }
    assert item["summary"].startswith("ChatGPT Enterprise is now available through AWS Marketplace")


async def test_search_matches_title_or_summary_ignoring_case_newest_first(connect):
    async with connect() as client:
        await call(client, "collect_now")
        result = await call(client, "search", query="chatgpt")

    assert [item["title"] for item in result["items"]] == [
        "Helping caregivers use AI in everyday life",  # summary only
        "ChatGPT Enterprise now available in AWS Marketplace",
        "Evernote turns AI-driven discovery into paid subscriptions",  # summary only
        "OpenAI and ServiceNow expand partnership across enterprise workflows",  # summary only
    ]


async def test_collecting_the_same_items_again_adds_nothing(connect, clock):
    async with connect() as client:
        await call(client, "collect_now")
        clock.advance(timedelta(hours=1))
        report = await call(client, "collect_now")
        result = await call(client, "search", query="AWS Marketplace")

    assert report["sources"] == [{"source": "openai-news", "added": 0}]
    assert len(result["items"]) == 1


async def test_urls_differing_only_by_tracking_parameters_or_trailing_slash_are_one_item(
    connect, fetcher, clock
):
    async with connect() as client:
        await call(client, "collect_now")
        fetcher.serve(OPENAI_NEWS_URL, "openai_rss_next_day.xml")
        clock.advance(timedelta(days=1))
        report = await call(client, "collect_now")
        caregivers = await call(client, "search", query="caregivers")
        education = await call(client, "search", query="guidance gap")

    assert report["sources"] == [{"source": "openai-news", "added": 1}]
    assert [item["url"] for item in caregivers["items"]] == [
        "https://openai.com/index/helping-caregivers-use-ai-in-everyday-life"
    ]
    assert [item["url"] for item in education["items"]] == [
        "https://openai.com/index/closing-ai-guidance-gap-education"
    ]


async def test_later_collections_keep_items_published_since_the_first_collections_backfill(
    connect, fetcher, clock
):
    async with connect() as client:
        await call(client, "collect_now")  # 11 Nov: backfill starts 12 Oct
        fetcher.serve(OPENAI_NEWS_URL, "openai_rss_next_day.xml")
        clock.advance(timedelta(days=45))  # 26 Dec: "Control Room" (9 Nov) is now 47 days old
        report = await call(client, "collect_now")
        result = await call(client, "search", query="Control Room")

    assert report["sources"] == [{"source": "openai-news", "added": 1}]
    assert [item["published_at"] for item in result["items"]] == ["2026-11-09T13:00:00Z"]
