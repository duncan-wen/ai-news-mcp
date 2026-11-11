from __future__ import annotations

import pytest

from .conftest import call, call_error, first_version_source

pytestmark = pytest.mark.anyio

SIMON_WILLISON = first_version_source("simon-willison")


@pytest.fixture
def fetcher(fetcher):
    fetcher.serve(SIMON_WILLISON.url, "simon_willison_atom.xml")
    return fetcher


async def test_a_summary_is_shown_as_plain_text(connect):
    async with connect((SIMON_WILLISON,)) as client:
        await call(client, "whats_new")  # waits for the start-up collection
        result = await call(client, "search", query="datasette-llm 0.1a10")

    [item] = result["items"]
    assert item["summary"] == (
        "Release: datasette-llm 0.1a10 Fixes a bug that affected my agent.datasette.io demo "
        "site, where the set of available LLM models was not correctly restricted to just "
        "those in the configuration. Tags: llm, datasette"
    )


async def test_a_long_summary_is_cut_to_500_characters(connect):
    async with connect((SIMON_WILLISON,)) as client:
        result = await call(client, "whats_new")

    [item] = [i for i in result["items"] if i["title"] == "Quoting Prompting Claude Fable 5.2"]
    assert item["summary"].startswith(
        "Claude Fable 5.2 responds closely to what the prompt says about who owns the code"
    )
    assert "<" not in item["summary"]
    assert len(item["summary"]) == 501
    assert item["summary"].endswith("…")


async def test_search_matches_the_whole_summary_not_only_the_part_shown(connect):
    async with connect((SIMON_WILLISON,)) as client:
        await call(client, "whats_new")  # waits for the start-up collection
        result = await call(client, "search", query="claude-mythos-fable")  # its last tag

    assert [item["title"] for item in result["items"]] == ["Quoting Prompting Claude Fable 5.2"]


async def test_read_item_falls_back_to_the_whole_summary_as_plain_text(connect):
    async with connect((SIMON_WILLISON,)) as client:
        await call(client, "whats_new")  # waits for the start-up collection
        [item] = (await call(client, "search", query="Quoting Prompting Claude"))["items"]
        error = await call_error(client, "read_item", id=item["id"])  # its page answers 404

    assert "Its summary: Claude Fable 5.2 responds closely" in error
    assert "— Prompting Claude Fable 5.2, Anthropic documentation" in error  # past 500
    assert "<" not in error
