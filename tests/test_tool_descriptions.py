from __future__ import annotations

import re
from pathlib import Path

import pytest

from ai_news_mcp.sources import Category

pytestmark = pytest.mark.anyio

GLOSSARY = Path(__file__).parent.parent / "GLOSSARY.md"


def glossary_definition(term: str) -> str:
    """The English definition of a GLOSSARY.md term: the line after its bold heading."""
    match = re.search(
        rf"^\*\*{re.escape(term)}（[^）]+）\*\*:\n(.+)$", GLOSSARY.read_text(), re.MULTILINE
    )
    assert match, f"{term} is not in GLOSSARY.md"
    return match.group(1)


def collapse_whitespace(text: str) -> str:
    return " ".join(text.split())


@pytest.mark.parametrize("category", list(Category))
async def test_whats_new_defines_each_category_as_the_glossary_does(connect, category):
    async with connect() as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    description = tools["whats_new"].description
    assert description is not None
    assert collapse_whitespace(glossary_definition(category.value)) in collapse_whitespace(
        description
    )
