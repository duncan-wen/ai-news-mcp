Source URLs, auth, rate limits and quirks: `docs/research/ai-news-sources.md` (too long to read whole: grep it by Source name).

Run `scripts/check` (lint, format, types, tests) before committing; CI runs the same script. `scripts/fix` applies the formatter and lint autofixes. Making a fixture: `tests/fixtures/README.md`.

## Agent skills

### Test seams

Pre-agreed: the MCP tools only, through the in-memory client (`docs/adr/0004-single-test-seam-at-the-mcp-tools.md`). No need to confirm them first.

### Issue tracker

Issues live in GitHub Issues (private repo duncan-wen/ai-news-mcp), managed via the `gh` CLI. Read one with `gh issue view <n> --json title,body,labels,comments` (`--comments` alone hides the body). See `docs/agents/issue-tracker.md`, also for recording a decision the issue leaves open.

No ticket named: take the lowest-numbered open ready-for-agent issue whose blockers are closed, and state which one you picked before starting.

### Triage labels

Default five labels: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
