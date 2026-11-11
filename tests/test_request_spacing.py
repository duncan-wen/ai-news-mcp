from __future__ import annotations

from datetime import timedelta

import anyio
import pytest

from .conftest import OPENAI_NEWS, OPENAI_NEWS_URL, call, first_version_source

pytestmark = pytest.mark.anyio

VLLM = first_version_source("vllm-releases")
TRANSFORMERS = first_version_source("transformers-releases")
TWO_ON_GITHUB_THEN_OPENAI = (VLLM, TRANSFORMERS, OPENAI_NEWS)


async def test_a_second_request_to_a_host_waits_while_other_hosts_are_requested(connect, fetcher):
    async with connect(TWO_ON_GITHUB_THEN_OPENAI, host_interval=timedelta(hours=1)) as client:
        await anyio.wait_all_tasks_blocked()  # the start-up collection waits on github.com
        found = await call(client, "search", query="AWS Marketplace")

    assert fetcher.requests == [VLLM.url, OPENAI_NEWS_URL]
    assert len(found["items"]) == 1  # OpenAI's Items did not wait for github.com


async def test_every_source_on_a_host_is_requested_once_the_interval_has_passed(connect, fetcher):
    async with connect(
        TWO_ON_GITHUB_THEN_OPENAI, host_interval=timedelta(milliseconds=10)
    ) as client:
        report = await call(client, "whats_new")  # waits for the start-up collection

    assert sorted(fetcher.requests) == sorted([VLLM.url, TRANSFORMERS.url, OPENAI_NEWS_URL])
    assert len(report["items"]) == 4  # 4 of its 6 Items published in the last 7 days
