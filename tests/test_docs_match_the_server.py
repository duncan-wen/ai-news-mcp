"""The docs that copy facts from the server or the glossary still match them."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import pytest

from ai_news_mcp.server import SHOWN_SUMMARY_LENGTH
from ai_news_mcp.sources import DEFAULT_SOURCES, Category

from .conftest import call

pytestmark = pytest.mark.anyio

ROOT = Path(__file__).parent.parent
GLOSSARY = ROOT / "GLOSSARY.md"
READMES = {"en": ROOT / "README.md", "zh-TW": ROOT / "README.zh-TW.md"}
PYPROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
SERVER_JSON = ROOT / "server.json"


def glossary_definitions(term: str) -> dict[str, str]:
    """A GLOSSARY.md term's definitions: the English and Chinese lines after its heading."""
    match = re.search(
        rf"^\*\*{re.escape(term)}（[^）]+）\*\*:\n(.+)\n(.+)$",
        GLOSSARY.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert match, f"{term} is not in GLOSSARY.md"
    return {"en": match.group(1), "zh-TW": match.group(2)}


def collapse_whitespace(text: str) -> str:
    return " ".join(text.split())


def readme_table(language: str, heading: str) -> list[list[str]]:
    """The body rows of the table under the README `## <heading>` section, as cells."""
    sections = READMES[language].read_text(encoding="utf-8").split("\n## ")
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


@pytest.mark.parametrize("tool", ["whats_new", "search"])
async def test_tool_descriptions_give_the_shown_summary_length(connect, tool):
    async with connect() as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    description = tools[tool].description
    assert description is not None
    assert f"about {SHOWN_SUMMARY_LENGTH} characters" in collapse_whitespace(description)


@pytest.mark.parametrize("language", READMES)
async def test_readme_gives_the_whats_new_limit(connect, language):
    async with connect() as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}

    limit = tools["whats_new"].input_schema["properties"]["limit"]["default"]
    [row] = [row for row in readme_table(language, "Tools") if row[0] == "`whats_new`"]
    assert f" {limit} " in row[1]


def readme_code_blocks(language: str, block_language: str) -> list[str]:
    """The bodies of the README's fenced code blocks opened with ```<block_language>."""
    text = READMES[language].read_text(encoding="utf-8")
    return re.findall(rf"^```{block_language}\n(.*?)^```$", text, re.MULTILINE | re.DOTALL)


@pytest.mark.parametrize("language", READMES)
def test_readme_claude_desktop_example_runs_the_package_script(language):
    [block] = readme_code_blocks(language, "json")
    [server] = json.loads(block)["mcpServers"].values()

    [script] = PYPROJECT["scripts"]
    assert [server["command"], *server["args"]] == ["uvx", script]


def test_registry_server_json_publishes_this_package_version():
    server = json.loads(SERVER_JSON.read_text(encoding="utf-8"))

    [package] = server["packages"]
    assert (package["registryType"], package["identifier"]) == ("pypi", PYPROJECT["name"])
    assert server["version"] == package["version"] == PYPROJECT["version"]


def test_package_readme_names_the_registry_server_for_ownership_checks():
    server = json.loads(SERVER_JSON.read_text(encoding="utf-8"))

    readme = (ROOT / PYPROJECT["readme"]).read_text(encoding="utf-8")
    assert f"<!-- mcp-name: {server['name']} -->" in readme
