"""Source adapters turn a raw response into ParsedItems."""

from __future__ import annotations

import calendar
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlsplit
from xml.etree import ElementTree

import feedparser

from .classification import is_about_ai
from .sources import SourceKind


class FormatError(Exception):
    """A response is not in the format its Source's adapter reads."""


@dataclass(frozen=True)
class ParsedItem:
    url: str
    title: str
    summary: str
    published_at: datetime | None


def parse_rss(body: bytes) -> list[ParsedItem]:
    """Parse an RSS or Atom document; raise FormatError if the body is neither."""
    parsed = feedparser.parse(body)
    if not parsed.version:  # feedparser recognised no feed format, e.g. an HTML page
        raise FormatError(f"not an RSS or Atom document: {parsed.get('bozo_exception')}")
    items: list[ParsedItem] = []
    for raw in parsed.entries:
        url = str(raw.get("link") or "")
        if not url:
            continue
        items.append(
            ParsedItem(
                url=url,
                title=str(raw.get("title") or "").strip(),
                summary=str(raw.get("summary") or "").strip(),
                published_at=_publish_time(raw),
            )
        )
    return items


def _publish_time(raw: feedparser.FeedParserDict) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        value = raw.get(key)
        if value:
            return datetime.fromtimestamp(calendar.timegm(value), UTC)  # type: ignore[arg-type]
    return None


_SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
ANTHROPIC_NEWS_PATH = "/news/"


def parse_anthropic_sitemap(body: bytes) -> list[ParsedItem]:
    """The /news/ URLs of anthropic.com's sitemap; raise FormatError if it is not a sitemap.

    A sitemap has no titles or summaries: the title is the URL's last path segment, words
    split at hyphens. Its lastmod is the publish time, but only for a page not edited
    since: old pages get new lastmod times when edited. A URL without lastmod is skipped:
    the Category listing pages (/news/models) have none, the news pages all do.
    """
    try:
        root = ElementTree.fromstring(body)
    except ElementTree.ParseError as error:
        raise FormatError(f"not a sitemap: {error}") from error
    if root.tag != f"{_SITEMAP_NS}urlset":
        raise FormatError(f"not a sitemap: the root element is {root.tag}")
    items: list[ParsedItem] = []
    for entry in root.iter(f"{_SITEMAP_NS}url"):
        url = (entry.findtext(f"{_SITEMAP_NS}loc") or "").strip()
        path = urlsplit(url).path
        slug = path.removeprefix(ANTHROPIC_NEWS_PATH).strip("/")
        if not path.startswith(ANTHROPIC_NEWS_PATH) or not slug:
            continue
        published_at = _iso_time((entry.findtext(f"{_SITEMAP_NS}lastmod") or "").strip())
        if published_at is None:
            continue
        title = slug.replace("-", " ")
        items.append(
            ParsedItem(
                url=url,
                title=title[:1].upper() + title[1:],
                summary="",
                published_at=published_at,
            )
        )
    return items


def _iso_time(text: str) -> datetime | None:
    """An ISO 8601 time, as UTC; None if empty or unreadable. Without an offset, UTC."""
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return None
    return moment.replace(tzinfo=UTC) if moment.tzinfo is None else moment.astimezone(UTC)


HACKER_NEWS_ITEM_URL = "https://news.ycombinator.com/item?id="


def parse_hn_algolia(body: bytes) -> list[ParsedItem]:
    """The stories about AI in an Algolia HN Search response; raise FormatError otherwise.

    A story links to its original URL, or to its HN discussion page when it has none
    (Ask HN). Its summary is its own text, if any.
    """
    try:
        hits = json.loads(body)["hits"]
    except (ValueError, TypeError, KeyError) as error:
        raise FormatError(f"not an Algolia HN Search response: {error!r}") from error
    if not isinstance(hits, list):
        raise FormatError("not an Algolia HN Search response: `hits` is not a list")
    items: list[ParsedItem] = []
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        title = str(hit.get("title") or "").strip()
        story_id = str(hit.get("objectID") or "")
        if not story_id or not is_about_ai(title):
            continue
        items.append(
            ParsedItem(
                url=str(hit.get("url") or "") or HACKER_NEWS_ITEM_URL + story_id,
                title=title,
                summary=str(hit.get("story_text") or "").strip(),
                published_at=_iso_time(str(hit.get("created_at") or "")),
            )
        )
    return items


ADAPTERS: dict[SourceKind, Callable[[bytes], list[ParsedItem]]] = {
    "rss": parse_rss,
    "anthropic-sitemap": parse_anthropic_sitemap,
    "hn-algolia": parse_hn_algolia,
}
