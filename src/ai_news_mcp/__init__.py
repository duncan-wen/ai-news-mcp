"""AI News MCP server: collects AI news Items into a local store for Claude to query."""

from __future__ import annotations

import sys
from pathlib import Path

import platformdirs

from .clock import SystemClock
from .fetcher import PROJECT_NAME, HttpFetcher
from .server import create_server
from .source_config import SourceConfigError


def default_store_path() -> Path:
    """The per-user store location, outside any repository."""
    return Path(platformdirs.user_data_dir(PROJECT_NAME, appauthor=False)) / "store.sqlite3"


def default_config_path() -> Path:
    """The per-user Source config file (see source_config); the server runs without one."""
    return Path(platformdirs.user_config_dir(PROJECT_NAME, appauthor=False)) / "sources.toml"


def main() -> None:
    try:
        server = create_server(
            store_path=default_store_path(),
            fetcher=HttpFetcher(),
            clock=SystemClock(),
            config_path=default_config_path(),
        )
    except SourceConfigError as error:
        sys.exit(str(error))
    server.run()
