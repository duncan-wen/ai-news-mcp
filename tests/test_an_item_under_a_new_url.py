from __future__ import annotations

from datetime import timedelta

import pytest

from .conftest import call, first_version_source, search_collected

pytestmark = pytest.mark.anyio

TECHCRUNCH_AI = first_version_source("techcrunch-ai")
CORMA_URL = (
    "https://techcrunch.com/2026/{day}/cybersecurity-ai-startup-corma-reaches-1b-valuation-"
    "in-about-3-months/"
)


async def test_an_item_moved_to_a_url_with_a_later_date_is_not_stored_again(
    connect, fetcher, clock
):
    # The fixture was downloaded 17 Nov 2026.
    clock.advance(timedelta(days=6, hours=5))
    fetcher.serve(TECHCRUNCH_AI.url, "techcrunch_rss.xml")
    async with connect((TECHCRUNCH_AI,)) as client:
        await call(client, "whats_new")  # waits for the start-up collection
        # TechCrunch updated the Corma Item: its URL now has 18 Nov in its path.
        fetcher.serve(TECHCRUNCH_AI.url, "techcrunch_rss_updated.xml")
        clock.advance(timedelta(days=1))
        report = await call(client, "collect_now")
        result = await search_collected(client, query="Corma")

    assert report["sources"] == [{"source": "techcrunch-ai", "added": 0}]
    [item] = result["items"]
    assert item["url"] == CORMA_URL.format(day="11/16")
    assert item["published_at"] == "2026-11-16T23:32:32Z"


OPENROUTER_MODELS = first_version_source("openrouter-models")


@pytest.mark.parametrize(
    ("first", "then", "kept"),
    [
        # A model, then its variants listed without it.
        (
            "openrouter_models.json",
            "openrouter_models_variants_alone.json",
            {
                "https://openrouter.ai/anthropic/claude-fable-5.2",
                "https://openrouter.ai/liquid/lfm-3-1.7b",
            },
        ),
        # Variants listed without their model, then the model.
        (
            "openrouter_models_variants_alone.json",
            "openrouter_models.json",
            {
                "https://openrouter.ai/anthropic/claude-fable-5.2:batch",
                "https://openrouter.ai/liquid/lfm-3-1.7b:free",
            },
        ),
    ],
)
async def test_an_openrouter_model_and_its_variant_are_one_item_across_collections(
    connect, fetcher, first, then, kept
):
    fetcher.serve(OPENROUTER_MODELS.url, first)
    async with connect((OPENROUTER_MODELS,)) as client:
        await call(client, "whats_new")  # waits for the start-up collection
        fetcher.serve(OPENROUTER_MODELS.url, then)
        report = await call(client, "collect_now")
        result = await search_collected(client)

    assert report["sources"] == [{"source": "openrouter-models", "added": 0}]
    # Both fixtures also list these two, the same each time.
    listed_in_both = {
        "https://openrouter.ai/thinkingmachines/inkling-2-small:free",
        "https://openrouter.ai/particle-ai/particle-1",
    }
    assert {item["url"] for item in result["items"]} == listed_in_both | kept
