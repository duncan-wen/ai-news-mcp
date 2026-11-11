"""The docs that copy facts from the server or the glossary still match them."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from ai_news_mcp.sources import DEFAULT_SOURCES, Category

from .conftest import call

pytestmark = pytest.mark.anyio

ROOT = Path(__file__).parent.parent
GLOSSARY = ROOT / "GLOSSARY.md"
READMES = {"en": ROOT / "README.md", "zh-TW": ROOT / "README.zh-TW.md"}


def glossary_definitions(term: str) -> dict[str, str]:
    """A GLOSSARY.md term's definitions: the English and Chinese lines after its heading."""
    match = re.search(
        rf"^\*\*{re.escape(term)}（[^）]+）\*\*:\n(.+)\n(.+)$", GLOSSARY.read_text(), re.MULTILINE
    )
    assert match, f"{term} is not in GLOSSARY.md"
    return {"en": match.group(1), "zh-TW": match.group(2)}


def collapse_whitespace(text: str) -> str:
    return " ".join(text.split())


def readme_table(language: str, heading: str) -> list[list[str]]:
    """The body rows of the table under the README `## <heading>` section, as cells."""
    sections = READMES[language].read_text().split("\n## ")
    [section] = [s for s in sections if s.startswith(heading)]
    rows = [line for line in section.splitlines() if line.startswith("|")]
    return [[cell.strip() for cell in row.strip("|").split("|")] for row in rows[2:]]


@pytest.mark.parametrize("category", list(Category))
async def test_whats_new_defines_each_category_as_the_glossary_does(connect, category):
    async with connect() as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    description = tools["whats_new"].description
    assert description is not None
    definition = glossary_definitions(category.value)["en"]
    assert collapse_whitespace(definition) in collapse_whitespace(description)


@pytest.mark.parametrize("language", READMES)
async def test_readme_lists_every_tool(connect, language):
    async with connect() as client:
        tools = {tool.name for tool in (await client.list_tools()).tools}

    listed = {row[0].strip("`") for row in readme_table(language, "Tools")}
    assert listed == tools


@pytest.mark.parametrize("language", READMES)
async def test_readme_lists_every_source_with_its_default_categories(connect, language):
    async with connect(DEFAULT_SOURCES) as client:
        result = await call(client, "list_sources")

    sources = {
        source["id"]: ", ".join(source["default_categories"]) for source in result["sources"]
    }
    listed = {row[0].strip("`"): row[2] for row in readme_table(language, "Sources")}
    assert listed == sources


@pytest.mark.parametrize("language", READMES)
@pytest.mark.parametrize("category", list(Category))
async def test_readme_defines_each_category_as_the_glossary_does(language, category):
    definitions = {row[0]: row[1] for row in readme_table(language, "Categories")}
    [definition] = [text for name, text in definitions.items() if name.startswith(category)]
    assert definition == glossary_definitions(category.value)[language]
