from __future__ import annotations

from datetime import timedelta

import anyio
import pytest
from mcp import Client

from .conftest import OPENAI_NEWS_URL, call

pytestmark = pytest.mark.anyio


async def test_collect_now_during_a_collection_waits_for_it_instead_of_starting_another(
    connect, fetcher
):
    fetcher.hold()
    async with connect() as client:
        reports: list[dict] = []

        async def collect_now(client: Client) -> None:
            reports.append(await call(client, "collect_now"))

        async with anyio.create_task_group() as tasks:
            tasks.start_soon(collect_now, client)
            tasks.start_soon(collect_now, client)
            await anyio.wait_all_tasks_blocked()  # both calls are waiting on the held request
            fetcher.release()

    assert fetcher.requests == [OPENAI_NEWS_URL]
    assert reports == [{"sources": [{"source": "openai-news", "added": 6}]}] * 2


async def test_server_start_collects_in_the_background_when_never_collected(connect, fetcher):
    fetcher.hold()
    async with connect() as client:
        with anyio.fail_after(1):
            await fetcher.requested.wait()  # started before any tool call
        during = await call(client, "search", query="chatgpt")
        fetcher.release()
        result = await call(client, "whats_new")

    assert during["items"] == []  # queries are answered while the collection runs
    assert len(result["items"]) == 6
    assert fetcher.requests == [OPENAI_NEWS_URL]


@pytest.mark.parametrize(("hours_later", "collects"), [(23, False), (25, True)])
async def test_server_start_collects_only_when_the_last_collection_is_over_24_hours_old(
    connect, fetcher, clock, hours_later, collects
):
    async with connect() as client:
        await call(client, "collect_now")
    clock.advance(timedelta(hours=hours_later))
    fetcher.requests.clear()
    fetcher.requested.clear()

    async with connect() as client:
        await anyio.wait_all_tasks_blocked()  # a start-up collection would have fetched by now
        found = await call(client, "search", query="chatgpt")

    assert fetcher.requests == ([OPENAI_NEWS_URL] if collects else [])
    assert found["items"]  # Items stored before the restart are still there


@pytest.mark.parametrize(("hours_later", "collects"), [(23, False), (25, True)])
async def test_whats_new_collects_first_only_when_the_last_collection_is_over_24_hours_old(
    connect, fetcher, clock, hours_later, collects
):
    async with connect() as client:
        await call(client, "whats_new")  # sees the start-up collection's 6 Items
        fetcher.serve(OPENAI_NEWS_URL, "openai_rss_next_day.xml")
        fetcher.requests.clear()
        clock.advance(timedelta(hours=hours_later))
        result = await call(client, "whats_new")

    assert fetcher.requests == ([OPENAI_NEWS_URL] if collects else [])
    assert [item["url"] for item in result["items"]] == (
        ["https://openai.com/index/control-room"] if collects else []
    )
    assert result["note"] is None


async def test_whats_new_stops_waiting_for_a_slow_collection_and_says_it_is_still_running(
    connect, fetcher, clock
):
    async with connect() as client:
        await call(client, "whats_new")  # sees the start-up collection's 6 Items
    fetcher.serve(OPENAI_NEWS_URL, "openai_rss_next_day.xml")
    clock.advance(timedelta(days=2))
    fetcher.hold()

    async with connect(collection_wait=timedelta(seconds=0.1)) as client:
        with anyio.fail_after(5):
            early = await call(client, "whats_new")
        clock.advance(timedelta(minutes=2))
        fetcher.release()
        later = await call(client, "whats_new")  # waits for the same collection to finish

    assert early["items"] == []
    assert "still running" in early["note"]
    assert [item["url"] for item in later["items"]] == ["https://openai.com/index/control-room"]
    assert later["note"] is None
