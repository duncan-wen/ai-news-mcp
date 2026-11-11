from __future__ import annotations

from datetime import timedelta

import anyio
import pytest

from .conftest import OPENAI_NEWS, call, first_version_source, search_collected

pytestmark = pytest.mark.anyio

HUGGING_FACE_MODELS = first_version_source("hugging-face-models")


async def test_hugging_face_models_collects_trending_models_created_in_the_last_30_days(
    connect, fetcher
):
    fetcher.serve(HUGGING_FACE_MODELS.url, "hf_models.json")
    async with connect((HUGGING_FACE_MODELS,)) as client:
        result = await search_collected(client)

    # 7 trending models: 2 created over 30 days ago (July 2026, Nov 2025).
    assert {item["url"]: item["published_at"] for item in result["items"]} == {
        "https://huggingface.co/tencent/Qwen3.8-27B-DSpine-b16": "2026-11-07T14:20:29Z",
        "https://huggingface.co/NousResearch/Arete-27B": "2026-11-06T19:31:28Z",
        "https://huggingface.co/ricursiveAI/Ripple-65B-Preview": "2026-11-04T02:41:21Z",
        "https://huggingface.co/moonshotai/Kimi-K3.1-Pro": "2026-11-02T04:13:51Z",
        "https://huggingface.co/speridlabs/idol": "2026-10-28T15:55:17Z",
    }
    item = next(i for i in result["items"] if i["url"].endswith("Kimi-K3.1-Pro"))
    assert item["title"] == "moonshotai/Kimi-K3.1-Pro"
    assert "Models" in item["categories"]


async def test_a_model_trending_over_30_days_after_it_was_created_is_not_new(
    connect, fetcher, clock
):
    fetcher.serve(HUGGING_FACE_MODELS.url, "hf_models.json")
    async with connect((HUGGING_FACE_MODELS,)) as client:
        await call(client, "whats_new")  # waits for the start-up collection
        # 9 days later, 2 more models are trending: one created 14 Oct, after the first
        # collection's 30-day backfill began (12 Oct) but now 37 days old, and one created
        # 5 Nov.
        fetcher.serve(HUGGING_FACE_MODELS.url, "hf_models_later.json")
        clock.advance(timedelta(days=9))
        report = await call(client, "collect_now")
        result = await call(client, "search", query="Underdog-Woof")

    assert report["sources"] == [{"source": "hugging-face-models", "added": 1}]
    assert [item["title"] for item in result["items"]] == ["ConwayResearch/Underdog-Woof"]


OPENROUTER_MODELS = first_version_source("openrouter-models")


async def test_openrouter_collects_models_listed_in_the_last_30_days_once_per_model(
    connect, fetcher
):
    fetcher.serve(OPENROUTER_MODELS.url, "openrouter_models.json")
    async with connect((OPENROUTER_MODELS,)) as client:
        result = await search_collected(client)

    # 7 listings: Claude Fable 5.1 from 1 Sept, and a batch and a free variant listed
    # beside their model.
    assert {item["title"]: item["url"] for item in result["items"]} == {
        # A free variant listed alone links to its own page.
        "Thinking Machines: Inkling 2 Small (free)": (
            "https://openrouter.ai/thinkingmachines/inkling-2-small:free"
        ),
        "Anthropic: Claude Fable 5.2": "https://openrouter.ai/anthropic/claude-fable-5.2",
        "LiquidAI: LFM3-1.7B": "https://openrouter.ai/liquid/lfm-3-1.7b",
        "Particle AI: Particle-1": "https://openrouter.ai/particle-ai/particle-1",
    }
    item = next(i for i in result["items"] if i["title"] == "Anthropic: Claude Fable 5.2")
    assert item["published_at"] == "2026-11-09T19:49:41Z"
    assert "Models" in item["categories"]
    assert item["summary"].startswith("Claude Fable 5.2 is Anthropic's most capable model")


@pytest.mark.parametrize(
    ("source", "error_mentions"),
    [
        (HUGGING_FACE_MODELS, "not a Hugging Face models response"),
        (OPENROUTER_MODELS, "not an OpenRouter models response"),
    ],
)
async def test_an_html_page_instead_of_the_models_list_fails_only_that_source(
    connect, fetcher, source, error_mentions
):
    fetcher.serve(source.url, "moved_page.html")
    async with connect((source, OPENAI_NEWS)) as client:
        report = await call(client, "collect_now")  # after the start-up collection

    [failure] = report["failed"]
    assert failure["source"] == source.id
    assert error_mentions in failure["error"]


HUGGING_FACE_BLOG = first_version_source("hugging-face-blog")


async def test_hugging_face_models_waits_for_the_interval_after_another_hugging_face_request(
    connect, fetcher
):
    # Hugging Face allows 500 anonymous requests per IP every 5 minutes: its Sources share
    # the spacing of one host.
    async with connect(
        (HUGGING_FACE_BLOG, HUGGING_FACE_MODELS, OPENAI_NEWS), host_interval=timedelta(hours=1)
    ):
        await anyio.wait_all_tasks_blocked()  # the start-up collection waits on huggingface.co

    assert fetcher.requests == [HUGGING_FACE_BLOG.url, OPENAI_NEWS.url]
