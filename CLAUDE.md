Source URLs, auth, rate limits and quirks: `docs/research/ai-news-sources.md`.

Run `scripts/check` (lint, format, types, tests) before committing; CI runs the same script. `scripts/fix` applies the formatter and lint autofixes. Making a fixture: `tests/fixtures/README.md`.

## Agent skills

### Test seams

Pre-agreed: the MCP tools only, through the in-memory client (`docs/adr/0004-single-test-seam-at-the-mcp-tools.md`). No need to confirm them first.

### Issue tracker

Issues live in GitHub Issues (private repo duncan-wen/ai-news-mcp), managed via the `gh` CLI. See `docs/agents/issue-tracker.md`, also for recording a decision the issue leaves open.

### Triage labels

Default five labels: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
