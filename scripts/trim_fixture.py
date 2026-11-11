"""Trim a downloaded RSS or Atom response into a fixture, keeping the chosen Items.

    uv run scripts/trim_fixture.py SAVED.xml tests/fixtures/NAME.xml \\
        --keep "<title>First title" --keep "<title>Second title"

Every byte outside the Items (declaration, namespaces, channel fields) and every kept
Item is copied unchanged, so the response's quirks survive. Each `--keep` text must be
found in exactly one Item; the script stops otherwise, before writing anything.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ITEM = re.compile(rb"<(item|entry)[\s>].*?</\1>", re.DOTALL)  # RSS <item>, Atom <entry>


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
    items = list(ITEM.finditer(body))
    if not items:
        sys.exit(f"{arguments.saved} has no <item> or <entry>")

    kept: list[re.Match[bytes]] = []
    for text in arguments.keep:
        matching = [item for item in items if text.encode() in item.group(0)]
        if len(matching) != 1:
            titles = [_title(item) for item in matching]
            sys.exit(f"--keep {text!r} is in {len(matching)} Items, not 1: {titles}")
        if matching[0] in kept:
            sys.exit(f"--keep {text!r} picks an Item another --keep already kept")
        kept.append(matching[0])
    kept.sort(key=lambda item: item.start())  # in the response's order

    arguments.fixture.write_bytes(
        body[: items[0].start()]
        + b"".join(item.group(0) for item in kept)
        + body[items[-1].end() :]
    )
    print(f"{arguments.fixture}: kept {len(kept)} of {len(items)} Items")
    for item in kept:
        print(f"  {_title(item)}")
    return 0


def _title(item: re.Match[bytes]) -> str:
    title = re.search(rb"<title[^>]*>(.*?)</title>", item.group(0), re.DOTALL)
    return title.group(1).decode(errors="replace").strip() if title else "(no title)"


if __name__ == "__main__":
    raise SystemExit(main())
