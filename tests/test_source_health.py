from __future__ import annotations

from datetime import timedelta

import pytest

from ai_news_mcp.fetcher import FetchError
from ai_news_mcp.sources import Category, Source

from .conftest import OPENAI_NEWS, OPENAI_NEWS_URL, FakeFetcher, call

pytestmark = pytest.mark.anyio

MOVED_URL = "https://example.com/moved/rss.xml"
MOVED = Source(
    id="moved-blog",
    name="Moved Blog",
    kind="rss",
    url=MOVED_URL,
    default_categories=(Category.ENGINEERING,),
)
MOVED_THEN_OPENAI = (MOVED, OPENAI_NEWS)  # the broken Source first, then a working one


def not_found(fetcher: FakeFetcher) -> None:
    pass  # the fake Fetcher answers any URL it does not serve with a 404


def gone(fetcher: FakeFetcher) -> None:
    fetcher.fail(MOVED_URL, FetchError(f"Client error '410 Gone' for url '{MOVED_URL}'"))


def timed_out(fetcher: FakeFetcher) -> None:
    fetcher.fail(MOVED_URL, FetchError(f"{MOVED_URL}: timed out"))


def not_a_feed(fetcher: FakeFetcher) -> None:
    fetcher.serve(MOVED_URL, "moved_page.html")


@pytest.mark.parametrize(
    ("break_source", "error_mentions"),
    [(not_found, "404"), (gone, "410"), (timed_out, "timed out"), (not_a_feed, "not an RSS")],
)
async def test_a_failing_source_does_not_stop_the_other_sources_and_collect_now_lists_it(
    connect, fetcher, break_source, error_mentions
):
    break_source(fetcher)
    async with connect(MOVED_THEN_OPENAI) as client:
        report = await call(client, "collect_now")  # after the start-up collection
        result = await call(client, "search", query="AWS Marketplace")

    assert [source["source"] for source in report["sources"]] == ["moved-blog", "openai-news"]
    assert report["sources"][0]["added"] == 0
    [failure] = report["failed"]
    assert failure["source"] == "moved-blog"
    assert error_mentions in failure["error"]
    assert len(result["items"]) == 1


async def test_list_sources_shows_each_sources_categories_and_collection_state(connect, clock):
    async with connect(MOVED_THEN_OPENAI) as client:
        await call(client, "whats_new")  # 11 Nov 12:00: the start-up collection
        clock.advance(timedelta(hours=1))
        await call(client, "collect_now")  # 13:00
        result = await call(client, "list_sources")

    moved, openai = result["sources"]
    assert "404" in moved.pop("last_error")
    assert moved == {
        "id": "moved-blog",
        "name": "Moved Blog",
        "default_categories": ["Engineering"],
        "last_attempt_at": "2026-11-11T13:00:00Z",
        "last_success_at": None,
        "consecutive_failures": 2,
    }
    assert openai == {
        "id": "openai-news",
        "name": "OpenAI News",
        "default_categories": ["News"],
        "last_attempt_at": "2026-11-11T13:00:00Z",
        "last_success_at": "2026-11-11T13:00:00Z",
        "last_error": None,
        "consecutive_failures": 0,
    }


async def test_whats_new_warns_first_about_a_source_failing_3_times_in_a_row_until_it_works(
    connect, fetcher, clock
):
    async with connect(MOVED_THEN_OPENAI) as client:
        one = await call(client, "whats_new")  # failure 1 at start-up
        clock.advance(timedelta(hours=1))
        await call(client, "collect_now")  # failure 2
        two = await call(client, "whats_new")
        clock.advance(timedelta(hours=1))
        await call(client, "collect_now")  # failure 3
        three = await call(client, "whats_new")
        fetcher.serve(MOVED_URL, "openai_rss.xml")
        clock.advance(timedelta(hours=1))
        await call(client, "collect_now")  # works again
        fixed = await call(client, "whats_new")

    assert one["warning"] is None
    assert two["warning"] is None
    assert next(iter(three)) == "warning"  # the first thing a client reads
    assert "Moved Blog (moved-blog)" in three["warning"]
    assert "3 collections in a row" in three["warning"]
    assert "404" in three["warning"]
    assert "openai-news" not in three["warning"]
    assert fixed["warning"] is None


async def test_a_collection_where_every_source_failed_does_not_count_as_fresh_data(
    connect, fetcher, clock
):
    fetcher.serve_nothing()  # offline: every Source fails
    async with connect() as client:
        await call(client, "collect_now")  # fails
        fetcher.serve(OPENAI_NEWS_URL, "openai_rss.xml")
        fetcher.requests.clear()
        clock.advance(timedelta(hours=1))
        result = await call(client, "whats_new")  # collects again: the data is still old

    assert fetcher.requests == [OPENAI_NEWS_URL]
    assert len(result["items"]) == 6
