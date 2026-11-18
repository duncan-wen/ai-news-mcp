# Changelog

Notable changes in each release. Versions follow [Semantic Versioning](https://semver.org/); until 1.0.0, a minor version can change the tools or the `sources.toml` format.

## 0.3.0

- `whats_new` takes `summary_length` to shorten the summaries it shows (0: none), as `search` does.
- `whats_new` shows up to 60 Items by default instead of 100, so a default call fits under Claude Code's 50,000-character tool-result threshold.
- `search` never splits Items published at the same time across pages, and reports `more`, how many matching Items were left out. Page back with `until` the oldest shown Item's `published_at`.
- A collection keeps one Item when its Source lists it again under a new URL: a TechCrunch update under a new date, or an OpenRouter variant (`:free`, `:batch`) of a stored model. Items already stored twice stay.
- Product Hunt summaries leave out the "Discussion | Link" line after the tagline. Items already stored keep their summaries.

## 0.2.1

- Every tool sets the four MCP annotation hints (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`): `list_sources`, `search` and `read_item` are read-only; `collect_now` and `whats_new` only add or move state, never delete.
- The READMEs show the mcprush and M8ven badges.

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
