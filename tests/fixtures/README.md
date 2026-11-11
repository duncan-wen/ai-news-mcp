# Fixtures

Each fixture is a real Source response, trimmed. The fake Fetcher in `tests/conftest.py` serves them by URL (`fetcher.serve(url, "file.xml")`).

Making one:

1. Download with the project's User-Agent, e.g. `curl -A "ai-news-mcp/0.1.0 (+https://github.com/duncan-wen/ai-news-mcp)" <url>`. Save it outside the repo.
2. Keep a handful of Items, chosen to straddle the windows the tests need: some within 30 days and some older (backfill), some within 7 days (What's New).
3. Keep the response's quirks (content type, encoding, odd fields): parsing is only tested through these files.
4. Mark any hand edit with an XML or JSON comment at the edited spot, saying what changed. Example: `openai_rss_next_day.xml`.
5. Note the download date below. Tests set the Clock relative to it.

| File | Source | Downloaded | Notes |
|---|---|---|---|
| `openai_rss.xml` | OpenAI News RSS | 2026-11-11 | 8 Items: 6 from 28 Oct to 10 Nov 2026, 2 from June 2026 |
| `moved_page.html` | none (hand-made) | 2026-11-11 | An HTML page where an RSS document should be: the format error |
| `openai_rss_next_day.xml` | OpenAI News RSS | 2026-11-11 | 2 Items from `openai_rss.xml` with a tracking query or trailing slash added; 1 Item (9 Nov) not in `openai_rss.xml` |
| `mistral_rss.xml` | Mistral News RSS | 2026-11-11 | Served as `text/plain`. 6 Items: 4 from 15 Oct to 5 Nov 2026, 1 from 6 Oct, 1 from Sept 2026 |
| `verge_atom.xml` | The Verge AI Atom | 2026-11-11 | 5 Items, all 10 Nov 2026, with Atom `<content>` |
