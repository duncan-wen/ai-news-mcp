# Fixtures

Each fixture is a real Source response, trimmed. The fake Fetcher in `tests/conftest.py` serves them by URL (`fetcher.serve(url, "file.xml")`).

Making one:

1. Download with the project's User-Agent, e.g. `curl --compressed -A "ai-news-mcp/0.1.0 (+https://github.com/duncan-wen/ai-news-mcp)" <url>`. Save it outside the repo. `--compressed` matters: some Sources (DeepMind) send gzip even unasked, and httpx decodes it in production.
2. Keep a handful of Items, chosen to straddle the windows the tests need: some within 30 days and some older (backfill), some within 7 days (What's New). For RSS or Atom, `uv run scripts/trim_fixture.py SAVED tests/fixtures/NAME.xml --keep "<title>..."` keeps the chosen Items byte for byte.
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
| `anthropic_sitemap.xml` | Anthropic sitemap | 2026-11-11 | 10 of 570 URLs: 3 outside /news/, the /news listing pages (`/news`, `/news/models`, no lastmod), 3 /news/ pages (one with a lastmod from a bulk edit on 19 Oct), 1 /research/ page |
| `anthropic_sitemap_next_day.xml` | Anthropic sitemap | 2026-11-11 | `anthropic_sitemap.xml` plus 1 /news/ and 1 /research/ URL left out of it, as if newly listed; 1 hand edit: an old /news/ page's lastmod moved to 12 Nov |
| `hn_algolia.json` | Algolia HN Search (the `hacker-news-ai` Source's query) | 2026-11-11 | Pretty-printed. 6 of 500 hits: 2 not about AI, 2 submissions of one URL, 1 Ask HN with no `url` |
| `hn_algolia_next_day.json` | Algolia HN Search | 2026-11-11 | `hn_algolia.json` plus 1 hit from 6 Nov left out of it, standing in for a story that reached 100 points after the first collection |
