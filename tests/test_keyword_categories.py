from __future__ import annotations

import pytest

from .conftest import MISTRAL_AND_THE_VERGE, call, serve_mistral_and_the_verge

pytestmark = pytest.mark.anyio


@pytest.fixture
def fetcher(fetcher):
    serve_mistral_and_the_verge(fetcher)
    return fetcher


@pytest.mark.parametrize(
    ("query", "categories"),
    [
        # No keyword: the Source's default Category only.
        ("indie game community", ["News"]),
        # "open-weight model" and "weights" in the summary.
        ("Built for Coders", ["News", "Models"]),
        # A model name with a version in the title; "rolling out" in the summary.
        ("Gemini 4 Carbon with agent", ["News", "Applications", "Models"]),
        # "Voxtral 3" in the title; "SDK" in the summary.
        ("Voxtral 3", ["News", "Engineering", "Models"]),
        # "apps" in the summary.
        ("Photoshop, Lightroom", ["News", "Applications"]),
    ],
)
async def test_keywords_in_the_title_or_summary_add_categories_to_the_sources_default(
    connect, query, categories
):
    async with connect(MISTRAL_AND_THE_VERGE) as client:
        await call(client, "whats_new")  # waits for the start-up collection
        result = await call(client, "search", query=query)

    [item] = result["items"]
    assert item["categories"] == categories


async def test_whats_new_in_models_includes_news_items_that_announce_a_model(connect):
    async with connect(MISTRAL_AND_THE_VERGE) as client:
        result = await call(client, "whats_new", categories=["Models"])

    assert [item["title"] for item in result["items"]] == [
        "Google releases Gemini 4 Carbon with agent ‘swarm’ feature",
        "Le Chonk: Built for Coders, Trusted by Defenders.",
        "Voxtral 3",
        "Introducing Timestral",  # "209M params" in the summary
    ]
