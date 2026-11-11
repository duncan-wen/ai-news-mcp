from __future__ import annotations

import time

import pytest

from .conftest import OPENAI_NEWS, call, call_error, first_version_source

pytestmark = pytest.mark.anyio

# openai_rss.xml's 6 Items published in the last 30 days, newest first.
OPENAI_TITLES = [
    "Helping caregivers use AI in everyday life",  # 10 Nov 12:00
    "Closing the AI guidance gap in education",  # 10 Nov 09:00
    "Work at the Frontier: AI’s effect on freelance work",  # 10 Nov 07:00
    "ChatGPT Enterprise now available in AWS Marketplace",  # 9 Nov 19:00
    "Evernote turns AI-driven discovery into paid subscriptions",  # 28 Oct 19:40:49
    "OpenAI and ServiceNow expand partnership across enterprise workflows",  # 28 Oct 13:15
]


# Two News Sources whose keywords add other Categories to some Items.
MISTRAL_AND_THE_VERGE = (first_version_source("mistral-news"), first_version_source("the-verge-ai"))


@pytest.fixture
def fetcher(fetcher):
    fetcher.serve("https://mistral.ai/news/rss", "mistral_rss.xml")
    fetcher.serve(
        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "verge_atom.xml"
    )
    return fetcher


def titles(result) -> list[str]:
    return [item["title"] for item in result["items"]]


async def test_search_without_a_query_returns_every_item_newest_first(connect):
    async with connect() as client:
        await call(client, "collect_now")
        result = await call(client, "search")

    assert titles(result) == OPENAI_TITLES


async def test_search_since_returns_items_published_at_or_after_it(connect):
    async with connect() as client:
        await call(client, "collect_now")
        result = await call(client, "search", since="2026-11-10T09:00:00Z")

    assert titles(result) == OPENAI_TITLES[:2]


async def test_search_until_returns_items_published_before_it(connect):
    async with connect() as client:
        await call(client, "collect_now")
        result = await call(client, "search", until="2026-11-10T09:00:00Z")

    assert titles(result) == OPENAI_TITLES[2:]


@pytest.fixture
def local_time_zone_not_utc(monkeypatch):
    """So that a test can tell UTC from the machine's local time zone."""
    monkeypatch.setenv("TZ", "Asia/Taipei")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


@pytest.mark.usefixtures("local_time_zone_not_utc")
async def test_search_dates_without_a_time_or_offset_are_utc_midnight(connect):
    async with connect() as client:
        await call(client, "collect_now")
        result = await call(client, "search", since="2026-10-29", until="2026-11-10")

    assert titles(result) == OPENAI_TITLES[3:4]


@pytest.mark.usefixtures("local_time_zone_not_utc")
async def test_search_times_without_an_offset_are_utc(connect):
    async with connect() as client:
        await call(client, "collect_now")
        result = await call(client, "search", since="2026-11-10T09:00:00")

    assert titles(result) == OPENAI_TITLES[:2]


async def test_search_in_categories_returns_items_in_any_of_them(connect):
    async with connect(MISTRAL_AND_THE_VERGE) as client:
        await call(client, "collect_now")
        result = await call(client, "search", categories=["Engineering", "Applications"])

    assert titles(result) == [
        "Google releases Gemini 4 Carbon with agent ‘swarm’ feature",
        "Photoshop, Lightroom, and Premiere are making it easier to remove things",
        "Hands-on with Ring’s new AI drone camera for your home",
        "Le Chonk brings the brains. Studio puts it to work.",
        "Voxtral 3",  # Engineering
    ]


async def test_search_in_no_categories_returns_nothing(connect):
    async with connect() as client:
        await call(client, "collect_now")
        result = await call(client, "search", categories=[])

    assert result["items"] == []


async def test_search_in_sources_returns_only_their_items(connect):
    async with connect(MISTRAL_AND_THE_VERGE) as client:
        await call(client, "collect_now")
        result = await call(client, "search", sources=["mistral-news"])

    assert titles(result) == [
        "Le Chonk brings the brains. Studio puts it to work.",
        "Le Chonk: Built for Coders, Trusted by Defenders.",
        "Voxtral 3",
        "Introducing Timestral",
    ]


async def test_search_in_no_sources_returns_nothing(connect):
    async with connect() as client:
        await call(client, "collect_now")
        result = await call(client, "search", sources=[])

    assert result["items"] == []


async def test_search_in_an_unknown_source_names_the_known_ones(connect):
    async with connect(MISTRAL_AND_THE_VERGE) as client:
        error = await call_error(client, "search", sources=["mistral", "the-verge-ai", "verge"])

    assert "No Source has id 'mistral', 'verge'" in error
    assert "mistral-news, the-verge-ai" in error


async def test_search_filters_combine(connect):
    async with connect((OPENAI_NEWS, *MISTRAL_AND_THE_VERGE)) as client:
        await call(client, "collect_now")
        result = await call(
            client,
            "search",
            query="remove",
            since="2026-11-10T13:45:00Z",  # not Ring's drone camera (13:30)
            until="2026-11-10T16:00:00Z",  # not Gemini 4 Carbon (16:00)
            categories=["Applications"],  # not the Anthropic IPO (14:06, News only)
            sources=["the-verge-ai", "openai-news"],  # not Mistral's Le Chonk Studio
        )

    assert titles(result) == [
        "Photoshop, Lightroom, and Premiere are making it easier to remove things"
    ]


@pytest.fixture
def many_items(fetcher):
    """24 Items: 15 from the news Sources and 9 from the model Sources."""
    model_sources = (
        first_version_source("openrouter-models"),
        first_version_source("hugging-face-models"),
    )
    fetcher.serve(model_sources[0].url, "openrouter_models.json")
    fetcher.serve(model_sources[1].url, "hf_models.json")
    return (OPENAI_NEWS, *MISTRAL_AND_THE_VERGE, *model_sources)


async def test_search_returns_at_most_20_items_by_default_newest_first(connect, many_items):
    async with connect(many_items) as client:
        await call(client, "collect_now")
        everything = await call(client, "search", limit=100)
        result = await call(client, "search")

    assert len(everything["items"]) == 24
    assert result["items"] == everything["items"][:20]
    published = [item["published_at"] for item in everything["items"]]
    assert published == sorted(published, reverse=True)


async def test_search_limit_sets_the_most_items_returned(connect):
    async with connect() as client:
        await call(client, "collect_now")
        result = await call(client, "search", limit=2)

    assert titles(result) == OPENAI_TITLES[:2]


async def test_search_limit_below_1_is_refused(connect):
    async with connect() as client:
        error = await call_error(client, "search", limit=0)

    assert "limit" in error
