"""Extracts the main text of an Item's original page, for `read_item`."""

from __future__ import annotations

import trafilatura


def extract_main_text(page: bytes) -> str | None:
    """The page's main text, without navigation, ads or comments; None if it has none."""
    return trafilatura.extract(page, include_comments=False) or None
