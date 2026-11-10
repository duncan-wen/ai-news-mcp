from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class Category(StrEnum):
    NEWS = "News"
    APPLICATIONS = "Applications"
    ENGINEERING = "Engineering"
    MODELS = "Models"


SourceKind = Literal["rss"]


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    kind: SourceKind
    url: str
    default_categories: tuple[Category, ...]


DEFAULT_SOURCES: tuple[Source, ...] = (
    Source(
        id="openai-news",
        name="OpenAI News",
        kind="rss",
        url="https://openai.com/news/rss.xml",
        default_categories=(Category.NEWS,),
    ),
)
