"""Every tool tells clients whether it changes anything and whether it reaches the web."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.anyio

# (read only, destructive, idempotent, open world)
EXPECTED_HINTS = {
    "collect_now": (False, False, False, True),
    "list_sources": (True, False, True, False),
    "search": (True, False, True, False),
    "read_item": (True, False, True, True),
    "whats_new": (False, False, False, True),
}


async def test_every_tool_sets_all_four_hints(connect):
    async with connect() as client:
        tools = (await client.list_tools()).tools

    hints = {}
    for tool in tools:
        annotations = tool.annotations
        assert annotations is not None, tool.name
        hints[tool.name] = (
            annotations.read_only_hint,
            annotations.destructive_hint,
            annotations.idempotent_hint,
            annotations.open_world_hint,
        )
    assert hints == EXPECTED_HINTS
