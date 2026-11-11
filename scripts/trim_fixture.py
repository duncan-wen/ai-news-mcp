"""Trim a downloaded response into a fixture, keeping the chosen Items.

    uv run scripts/trim_fixture.py SAVED.xml tests/fixtures/NAME.xml \\
        --keep "<title>First title" --keep "<title>Second title"

The format goes by the saved file:

- RSS `<item>`, Atom `<entry>` or sitemap `<url>` (a `<urlset>` document): every byte
  outside the Items (declaration, namespaces, channel fields) and every kept Item is
  copied unchanged, so the response's quirks survive.
- JSON (a `.json` file): the Items are the elements of its one top-level array, such as
  Algolia's `hits`, or of the document itself when it is an array (Hugging Face
  models). Every other field is kept; the fixture is written pretty-printed.

Each `--keep` text must be found in exactly one Item (for JSON, in the element's JSON
text: a title, or an `objectID` when two Items share a title); the script stops
otherwise, before writing anything.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, TypeVar

FEED_ITEM = re.compile(rb"<(item|entry)[\s>].*?</\1>", re.DOTALL)  # RSS <item>, Atom <entry>
# Only in a sitemap: an RSS channel's <image> also holds a <url>.
SITEMAP_ITEM = re.compile(rb"<url[\s>].*?</url>", re.DOTALL)

T = TypeVar("T")


def main() -> int:
    parser = argparse.ArgumentParser(description="Trim a downloaded response into a fixture.")
    parser.add_argument("saved", type=Path, help="the response as downloaded")
    parser.add_argument("fixture", type=Path, help="the fixture file to write")
    parser.add_argument(
        "--keep", action="append", required=True, help="text found in one Item to keep"
    )
    arguments = parser.parse_args()

    body = arguments.saved.read_bytes()
    if body[:2] == b"\x1f\x8b":
        sys.exit(f"{arguments.saved} is gzip: download with `curl --compressed`")
    if arguments.saved.suffix == ".json":
        _trim_json(body, arguments.fixture, arguments.keep)
    else:
        _trim_xml(body, arguments.fixture, arguments.keep)
    return 0


def _trim_xml(body: bytes, fixture: Path, keep: list[str]) -> None:
    pattern = SITEMAP_ITEM if b"<urlset" in body else FEED_ITEM
    items = list(pattern.finditer(body))
    if not items:
        sys.exit("the saved file has no <item>, <entry> or sitemap <url>")
    kept = _choose(items, keep, lambda item: item.group(0).decode(errors="replace"), _xml_title)
    kept.sort(key=lambda item: item.start())  # in the response's order
    fixture.write_bytes(
        body[: items[0].start()]
        + b"".join(item.group(0) for item in kept)
        + body[items[-1].end() :]
    )
    _report(fixture, [_xml_title(item) for item in kept], len(items))


def _trim_json(body: bytes, fixture: Path, keep: list[str]) -> None:
    document: Any = json.loads(body)
    if isinstance(document, list):  # the document is the array (Hugging Face models)
        items: list[Any] = document
        wrapper: dict[str, Any] | None = None
        key = ""
    else:
        wrapper = document
        arrays = [name for name, value in document.items() if isinstance(value, list)]
        if len(arrays) != 1:
            sys.exit(f"the saved JSON needs exactly one top-level array, not {arrays}")
        [key] = arrays
        items = document[key]
    kept = _choose(items, keep, lambda item: json.dumps(item, ensure_ascii=False), _json_title)
    kept.sort(key=lambda item: next(i for i, other in enumerate(items) if other is item))
    trimmed: Any = kept if wrapper is None else {**wrapper, key: kept}
    fixture.write_text(json.dumps(trimmed, indent=2, ensure_ascii=False) + "\n")
    _report(fixture, [_json_title(item) for item in kept], len(items))


def _choose(
    items: Sequence[T], keep: list[str], text_of: Callable[[T], str], title_of: Callable[[T], str]
) -> list[T]:
    kept: list[T] = []
    for text in keep:
        matching = [item for item in items if text in text_of(item)]
        if len(matching) != 1:
            titles = [title_of(item) for item in matching]
            sys.exit(f"--keep {text!r} is in {len(matching)} Items, not 1: {titles}")
        if any(matching[0] is item for item in kept):
            sys.exit(f"--keep {text!r} picks an Item another --keep already kept")
        kept.append(matching[0])
    return kept


def _report(fixture: Path, titles: list[str], total: int) -> None:
    print(f"{fixture}: kept {len(titles)} of {total} Items")
    for title in titles:
        print(f"  {title}")


def _xml_title(item: re.Match[bytes]) -> str:
    title = re.search(rb"<(title|loc)[^>]*>(.*?)</\1>", item.group(0), re.DOTALL)
    return title.group(2).decode(errors="replace").strip() if title else "(no title)"


def _json_title(item: Any) -> str:
    return (
        str(item.get("title") or item.get("url") or item.get("id") or "(no title)")
        if isinstance(item, dict)
        else "?"
    )


if __name__ == "__main__":
    raise SystemExit(main())
