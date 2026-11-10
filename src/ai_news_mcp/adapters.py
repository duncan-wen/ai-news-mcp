"""Source adapters turn a raw response into ParsedItems."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import UTC, datetime

import feedparser


@dataclass(frozen=True)
class ParsedItem:
    url: str
    title: str
    summary: str
    published_at: datetime | None


def parse_rss(body: bytes) -> list[ParsedItem]:
    """Parse an RSS or Atom document."""
    parsed = feedparser.parse(body)
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
