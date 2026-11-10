"""Source adapters turn a raw response into ParsedItems."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import UTC, datetime

import feedparser


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
