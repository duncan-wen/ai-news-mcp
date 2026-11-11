# Contributing

## Issues first

Report a bug or suggest a change by [opening an issue](https://github.com/duncan-wen/ai-news-mcp/issues/new). Issues are triaged with labels: `needs-triage` until the maintainer has read it, then `needs-info` (a question for you), `ready-for-agent` or `ready-for-human` (accepted, with the work specified), or `wontfix` (with the reason). The labels are described in [docs/agents/triage-labels.md](docs/agents/triage-labels.md).

A pull request is not a feature request: open an issue first and wait for it to be accepted. A pull request that fixes an accepted issue, and says which one, is welcome. A Source that fails or moved is a good issue: give the Source id and the error from `list_sources`.

## Developing

You need [uv](https://docs.astral.sh/uv/).

```sh
uv sync         # create .venv with the package and the dev tools
scripts/check   # lint, format, types, workflows, tests and the package build, as CI runs them
scripts/fix     # apply the formatter and lint autofixes
```

Run `scripts/check` before every commit; CI runs the same script on Linux, macOS and Windows with Python 3.11 to 3.13.

- Tests go through the MCP tools only, with an in-memory client, a fake Fetcher that serves fixture files and a controllable Clock: see [ADR 0004](docs/adr/0004-single-test-seam-at-the-mcp-tools.md) and `tests/conftest.py`. No test reaches the network.
- A new or changed Source needs a fixture: [tests/fixtures/README.md](tests/fixtures/README.md) says how to make one. Source URLs, rate limits and quirks are in [docs/research/ai-news-sources.md](docs/research/ai-news-sources.md).
- Use the terms in [GLOSSARY.md](GLOSSARY.md) (Source, Item, Category, Checkpoint, What's New and the Category names) in code, docs and issues, and follow [CODING_STANDARDS.md](CODING_STANDARDS.md). The decisions in [docs/adr/](docs/adr/) hold unless an issue changes them; the server never calls an LLM ([ADR 0002](docs/adr/0002-no-llm-in-the-server.md)).
- Both READMEs (`README.md`, `README.zh-TW.md`) change together; `tests/test_docs_match_the_server.py` checks their tables against the server.

## Releasing

1. On a branch: `uv version X.Y.Z` (updates `pyproject.toml` and `uv.lock`; CI's `uv sync --locked` fails on a stale lock), set both `version` fields in `server.json` to match (a test checks), and add a `## X.Y.Z` section to `CHANGELOG.md`. Merge it once `scripts/check` and CI pass.
2. On `main`: `git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin vX.Y.Z`. `publish.yml` runs the checks, stops if the tag differs from the package version, publishes to PyPI, then lists `server.json` on the MCP Registry.
3. `gh release create vX.Y.Z --verify-tag --title vX.Y.Z --notes-file <the CHANGELOG section>`.
4. Check `uvx ai-news-mcp==X.Y.Z` starts. PyPI's JSON API can answer 404 for a few minutes after the upload; `https://pypi.org/project/ai-news-mcp/X.Y.Z/` shows it sooner.

If `publish.yml` fails at the artifact upload or download, suspect a recent Dependabot upgrade of those actions.

## Security

Do not open a public issue for a vulnerability: see [SECURITY.md](SECURITY.md).
