"""The user's Source config file: Sources to add, built-in Sources to disable or override.

disabled = ["techcrunch-ai"]          # built-in Source ids not to collect

[sources.my-blog]                     # a new Source: name, url, default_categories
name = "My Blog"
url = "https://example.com/feed.xml"
default_categories = ["Engineering"]  # News, Applications, Engineering, Models
# kind = "rss"                        # the default; see sources.SourceKind

[sources.openai-news]                 # a built-in Source id: only these fields change
url = "https://openai.com/news/rss.xml"
"""

from __future__ import annotations

import dataclasses
import tomllib
from pathlib import Path
from typing import Any, get_args

from .sources import Category, Source, SourceKind

FIELDS = ("name", "kind", "url", "default_categories")
NEW_SOURCE_FIELDS = ("name", "url", "default_categories")
KINDS: tuple[str, ...] = get_args(SourceKind)
CATEGORIES = tuple(category.value for category in Category)


class SourceConfigError(Exception):
    """The Source config file is malformed: the server does not start."""


def configured_sources(
    built_in: tuple[Source, ...], config_path: Path | None
) -> tuple[Source, ...]:
    """The built-in Sources merged with the config file at `config_path`, if it exists.

    Overridden built-in Sources keep their place; added Sources come after them, in file order.
    """
    if config_path is None or not config_path.exists():
        return built_in
    try:
        text = config_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise SourceConfigError(
            f"Source config file {config_path} cannot be read: {error}"
        ) from error
    try:
        return _merge(built_in, tomllib.loads(text))
    except (tomllib.TOMLDecodeError, ValueError) as error:
        raise SourceConfigError(f"Source config file {config_path}: {error}") from error


def _merge(built_in: tuple[Source, ...], config: dict[str, Any]) -> tuple[Source, ...]:
    unknown = sorted(set(config) - {"disabled", "sources"})
    if unknown:
        raise ValueError(
            f"unknown top-level key {', '.join(map(repr, unknown))}; "
            "expected 'disabled' and '[sources.<id>]' tables"
        )
    built_in_ids = [source.id for source in built_in]
    disabled = _disabled(config.get("disabled", []), built_in_ids)
    entries = config.get("sources", {})
    if not isinstance(entries, dict):
        raise ValueError("'sources' must be tables, written [sources.<id>]")
    overrides: dict[str, dict[str, Any]] = {}
    added: list[Source] = []
    for source_id, entry in entries.items():
        if not isinstance(entry, dict):
            raise ValueError(f"Source {source_id!r} must be a table, written [sources.{source_id}]")
        try:
            fields = _fields(entry)
            if source_id in disabled:
                raise ValueError("it is in 'disabled', so overriding its fields does nothing")
            if source_id in built_in_ids:
                overrides[source_id] = fields
            else:
                added.append(_new_source(source_id, fields))
        except ValueError as error:
            raise ValueError(f"Source {source_id!r}: {error}") from None
    kept = tuple(
        dataclasses.replace(source, **overrides.get(source.id, {}))
        for source in built_in
        if source.id not in disabled
    )
    return kept + tuple(added)


def _disabled(value: Any, built_in_ids: list[str]) -> set[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError("'disabled' must be a list of built-in Source ids")
    unknown = [source_id for source_id in value if source_id not in built_in_ids]
    if unknown:
        raise ValueError(
            f"'disabled' names {', '.join(map(repr, unknown))}, which is no built-in Source. "
            f"Built-in Source ids: {', '.join(built_in_ids)}"
        )
    return set(value)


def _new_source(source_id: str, fields: dict[str, Any]) -> Source:
    missing = [name for name in NEW_SOURCE_FIELDS if name not in fields]
    if missing:
        raise ValueError(
            f"it is no built-in Source, so it needs {', '.join(NEW_SOURCE_FIELDS)}; "
            f"missing {', '.join(missing)}"
        )
    return Source(id=source_id, **{"kind": "rss", **fields})


def _fields(entry: dict[str, Any]) -> dict[str, Any]:
    unknown = [key for key in entry if key not in FIELDS]
    if unknown:
        raise ValueError(f"unknown key {', '.join(map(repr, unknown))}; keys: {', '.join(FIELDS)}")
    for name in ("name", "url"):
        if name in entry and not (isinstance(entry[name], str) and entry[name]):
            raise ValueError(f"{name!r} must be a non-empty string")
    fields = dict(entry)
    if "kind" in fields and fields["kind"] not in KINDS:
        raise ValueError(f"'kind' {fields['kind']!r} is unknown; kinds: {', '.join(KINDS)}")
    if "default_categories" in fields:
        fields["default_categories"] = _categories(fields["default_categories"])
    return fields


def _categories(value: Any) -> tuple[Category, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(
            f"'default_categories' must be a non-empty list of: {', '.join(CATEGORIES)}"
        )
    unknown = [name for name in value if name not in CATEGORIES]
    if unknown:
        raise ValueError(
            f"'default_categories' has {', '.join(map(repr, unknown))}, which is no Category; "
            f"Categories: {', '.join(CATEGORIES)}"
        )
    return tuple(dict.fromkeys(Category(name) for name in value))
