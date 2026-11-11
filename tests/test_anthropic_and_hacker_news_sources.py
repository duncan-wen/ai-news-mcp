from __future__ import annotations

from datetime import timedelta

import pytest

from .conftest import OPENAI_NEWS, call, first_version_source

pytestmark = pytest.mark.anyio

ANTHROPIC_NEWS = first_version_source("anthropic-news")


async def test_anthropic_news_collects_only_news_urls_the_sitemap_did_not_list_before(
    connect, fetcher, clock
):
    fetcher.serve(ANTHROPIC_NEWS.url, "anthropic_sitemap.xml")
    async with connect((ANTHROPIC_NEWS,)) as client:
        # The first collection lists the sitemap's URLs as already there: its lastmod
        # times are edit times, so they can't tell which of them are new.
        first = await call(client, "whats_new")
        fetcher.serve(ANTHROPIC_NEWS.url, "anthropic_sitemap_next_day.xml")
        clock.advance(timedelta(days=1))
        # The next day's sitemap adds a /news/ and a /research/ URL, and an old /news/
        # URL has a new lastmod.
        report = await call(client, "collect_now")
        second = await call(client, "whats_new")

    assert first["items"] == []
    assert report["sources"] == [{"source": "anthropic-news", "added": 1}]
    [item] = second["items"]
    assert {key: item[key] for key in ("title", "source", "categories", "published_at", "url")} == {
        "title": "Open call guest investigators life sciences",
        "source": "anthropic-news",
        "categories": ["News"],
        "published_at": "2026-11-06T10:22:49Z",
        "url": "https://www.anthropic.com/news/open-call-guest-investigators-life-sciences",
    }


HACKER_NEWS = first_version_source("hacker-news-ai")


async def test_hacker_news_collects_ai_stories_linking_to_the_original_or_the_discussion(
    connect, fetcher
):
    fetcher.serve(HACKER_NEWS.url, "hn_algolia.json")
    async with connect((HACKER_NEWS,)) as client:
        result = await call(client, "whats_new")

    # 6 stories of 100 points or more: 2 not about AI, and 2 submissions of one URL.
    assert {item["title"]: item["url"] for item in result["items"]} == {
        "Claude Fable 5.2 and Mythos 5.2": "https://www.anthropic.com/claude-fable-and-mythos-5-2",
        "OpenAI raises $11B at a $1.25T valuation": (
            "https://247wallst.com/investing/2026/11/07/openai-just-raised-11-billion-at-a-1-25"
            "-trillion-valuation-below-the-1-4-trillion-it-first-sought/"
        ),
        # An Ask HN has no URL of its own.
        "Ask HN: What's your current AI agentic setup?": (
            "https://news.ycombinator.com/item?id=50366117"
        ),
    }


async def test_a_hacker_news_story_reaching_100_points_after_a_collection_is_collected_later(
    connect, fetcher, clock
):
    fetcher.serve(HACKER_NEWS.url, "hn_algolia.json")
    async with connect((HACKER_NEWS,)) as client:
        await call(client, "whats_new")  # waits for the start-up collection
        # The next day's response adds a story from 6 Nov that had under 100 points before.
        fetcher.serve(HACKER_NEWS.url, "hn_algolia_next_day.json")
        clock.advance(timedelta(days=1))
        report = await call(client, "collect_now")
        result = await call(client, "whats_new")

    assert report["sources"] == [{"source": "hacker-news-ai", "added": 1}]
    assert [item["title"] for item in result["items"]] == [
        "Memorilla: Latent Semantic Memory for LLMs"
    ]


@pytest.mark.parametrize(
    ("source", "error_mentions"),
    [(ANTHROPIC_NEWS, "not a sitemap"), (HACKER_NEWS, "not an Algolia HN Search response")],
)
async def test_an_html_page_instead_of_the_expected_response_fails_only_that_source(
    connect, fetcher, source, error_mentions
):
    fetcher.serve(source.url, "moved_page.html")
    async with connect((source, OPENAI_NEWS)) as client:
        report = await call(client, "collect_now")  # after the start-up collection

    [failure] = report["failed"]
    assert failure["source"] == source.id
    assert error_mentions in failure["error"]
