from __future__ import annotations

import pytest

from ai_news_mcp.source_config import SourceConfigError

from .conftest import MISTRAL_AND_THE_VERGE, call

pytestmark = pytest.mark.anyio


@pytest.fixture
def config_path(tmp_path):
    return tmp_path / "sources.toml"


async def source_ids(connect, **settings) -> list[str]:
    async with connect(**settings) as client:
        result = await call(client, "list_sources")
    return [source["id"] for source in result["sources"]]


async def test_a_source_added_in_the_config_file_is_listed_after_the_built_in_sources(
    connect, config_path
):
    config_path.write_text(
        """
[sources.my-blog]
name = "My Blog"
url = "https://example.com/feed.xml"
default_categories = ["Engineering", "Applications"]
""",
        encoding="utf-8",
    )
    async with connect(config_path=config_path) as client:
        result = await call(client, "list_sources")

    openai, mine = result["sources"]
    assert openai["id"] == "openai-news"
    assert mine["id"] == "my-blog"
    assert mine["name"] == "My Blog"
    assert mine["url"] == "https://example.com/feed.xml"
    assert mine["default_categories"] == ["Engineering", "Applications"]


async def test_a_built_in_source_disabled_in_the_config_file_is_not_listed(connect, config_path):
    config_path.write_text('disabled = ["mistral-news"]\n', encoding="utf-8")

    ids = await source_ids(connect, sources=MISTRAL_AND_THE_VERGE, config_path=config_path)

    assert ids == ["the-verge-ai"]


async def test_a_built_in_source_overridden_in_the_config_file_keeps_its_place_and_other_fields(
    connect, config_path
):
    config_path.write_text(
        """
[sources.openai-news]
url = "https://openai.com/moved/rss.xml"
default_categories = ["Models"]
""",
        encoding="utf-8",
    )
    async with connect(config_path=config_path) as client:
        result = await call(client, "list_sources")

    [openai] = result["sources"]
    assert openai["id"] == "openai-news"
    assert openai["name"] == "OpenAI News"
    assert openai["url"] == "https://openai.com/moved/rss.xml"
    assert openai["default_categories"] == ["Models"]


async def test_without_a_config_file_only_the_built_in_sources_are_listed(connect, config_path):
    ids = await source_ids(connect, sources=MISTRAL_AND_THE_VERGE, config_path=config_path)

    assert ids == ["mistral-news", "the-verge-ai"]


NEW_SOURCE = """
[sources.my-blog]
name = "My Blog"
url = "https://example.com/feed.xml"
"""


@pytest.mark.parametrize(
    ("config", "error_mentions"),
    [
        ("[sources.my-blog\n", ["line 1"]),
        (
            '[sources.my-blog]\nname = "My Blog"\ndefault_categories = ["News"]\n',
            ["my-blog", "url"],
        ),
        (NEW_SOURCE + 'default_categories = ["Research"]\n', ["my-blog", "Research"]),
        (NEW_SOURCE + "default_categories = []\n", ["my-blog", "default_categories"]),
        (NEW_SOURCE + 'categories = ["News"]\n', ["my-blog", "categories"]),
        (NEW_SOURCE + 'default_categories = ["News"]\nkind = "atom"\n', ["my-blog", "atom"]),
        ("[sources.openai-news]\nurl = 3\n", ["openai-news", "url"]),
        ('[sources.openai-news]\nid = "openai"\n', ["openai-news", "id"]),
        ('disabled = ["openai-new"]\n', ["openai-new", "disabled"]),
        ('disabled = "openai-news"\n', ["disabled"]),
        ('[source.my-blog]\nname = "My Blog"\n', ["source"]),
        (
            'disabled = ["openai-news"]\n[sources.openai-news]\nurl = "https://example.com/"\n',
            ["openai-news", "disabled"],
        ),
    ],
)
async def test_a_malformed_config_file_stops_the_server_starting_and_names_the_bad_entry(
    connect, config_path, config, error_mentions
):
    config_path.write_text(config, encoding="utf-8")

    with pytest.raises(SourceConfigError) as error:
        async with connect(config_path=config_path):
            pass

    message = str(error.value)
    assert str(config_path) in message
    for mention in error_mentions:
        assert mention in message


async def test_an_unreadable_config_file_stops_the_server_starting_and_names_the_file(
    connect, config_path
):
    config_path.mkdir()  # exists, but cannot be read as a file

    with pytest.raises(SourceConfigError, match="cannot be read") as error:
        async with connect(config_path=config_path):
            pass

    assert str(config_path) in str(error.value)
