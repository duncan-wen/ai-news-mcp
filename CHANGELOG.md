# Changelog

Notable changes in each release. Versions follow [Semantic Versioning](https://semver.org/); until 1.0.0, a minor version can change the tools or the `sources.toml` format.

## 0.2.0

- `search` takes `summary_length` to shorten the summaries it shows (0: none).
- `read_item` returns the first `max_length` characters (default 10,000), with no marker added, and reports `truncated` and `full_length`.

## 0.1.0

The first release.

- Tools: `whats_new`, `search`, `read_item`, `list_sources` and `collect_now`.
- 23 built-in Sources in four Categories (News, Applications, Engineering, Models), with keyword rules that add Categories.
- Collection on demand when the data is over 24 hours old; the first collection reaches back 30 days.
- One Checkpoint per Category; What's New shows Items published in the last 7 days.
- `sources.toml` to add, disable or change Sources.
