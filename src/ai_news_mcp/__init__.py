"""AI News MCP server: collects AI news Items into a local store for Claude to query."""

from __future__ import annotations

from pathlib import Path

import platformdirs

from .clock import SystemClock
from .fetcher import PROJECT_NAME, HttpFetcher
from .server import create_server


def default_store_path() -> Path:
    """The per-user store location, outside any repository."""
    return Path(platformdirs.user_data_dir(PROJECT_NAME, appauthor=False)) / "store.sqlite3"


def main() -> None:
    server = create_server(
        store_path=default_store_path(), fetcher=HttpFetcher(), clock=SystemClock()
    )
    server.run()
