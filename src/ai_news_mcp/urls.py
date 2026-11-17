from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .sources import Source

TRACKING_PARAMETERS = frozenset(
    {"fbclid", "gclid", "dclid", "msclkid", "mc_cid", "mc_eid", "ref", "ref_src", "_hsenc", "_hsmi"}
)


def normalize_url(url: str) -> str:
    """The form of a URL used to decide whether two Items are the same.

    Lowercases the scheme and host, drops the fragment, tracking query parameters
    (`utm_*` and common click IDs) and a trailing slash on the path.
    """
    parts = urlsplit(url.strip())
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in TRACKING_PARAMETERS
    ]
    path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))


_DATE_SEGMENT = re.compile(r"/\d{4}/\d{2}/\d{2}(?=/|$)")


def same_item_key(url: str, source: Source) -> str:
    """The form of a normalised URL under which one Source lists an Item again.

    Two URLs of one Source with the same key are one Item. On the Source's own site a
    `/YYYY/MM/DD` path segment is dropped: TechCrunch moves an updated Item to a URL with
    the update's date. Only there: elsewhere (a Hacker News story's link) one slug under
    two dates may be two Items. An OpenRouter variant (`:free`, `:batch`) is its model:
    a model's page without the variant mark.
    """
    parts = urlsplit(url)
    path = parts.path
    if _site(parts.netloc) == _site(urlsplit(source.url).netloc):
        path = _DATE_SEGMENT.sub("", path)
    if source.kind == "openrouter-models":
        path = path.partition(":")[0]
    return urlunsplit(parts._replace(path=path))


def _site(host: str) -> str:
    return host.lower().removeprefix("www.")
