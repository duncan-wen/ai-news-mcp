Source URLs, auth, rate limits and quirks: `docs/research/ai-news-sources.md`.

Run `scripts/check` (lint, format, types, tests) before committing; CI runs the same script. `scripts/fix` applies the formatter and lint autofixes. Making a fixture: `tests/fixtures/README.md`.

## Agent skills

### Issue tracker

Issues live in GitHub Issues (private repo duncan-wen/ai-news-mcp), managed via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five labels: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
