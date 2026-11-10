# Coding Standards

Rules for reviewing changes in this repo. Each rule is a judgement call. Anything a tool can check (lint, formatting, types, banned imports) is enforced by the repo's check command and CI instead, so it is left out of this file.

## Tests go through the MCP tools

Tests call the MCP tools through the MCP SDK's in-memory client (`mcp.Client(server)`) and check only what a client can see. The only test doubles are a fake Fetcher and a controllable Clock, and the store is a real SQLite file. A test may also pass its own Source list to `create_server`: that is configuration, not a test double. Flag any test that calls a Source adapter, the Store or SQL directly, or that mocks anything other than the Fetcher and the Clock. Why: `docs/adr/0004-single-test-seam-at-the-mcp-tools.md`.

## Omitted is not empty

A tool's list parameter (for example `categories`, `sources`) means the default when omitted (`None`) and nothing when empty (`[]`). Flag code that treats the two alike, such as `if not categories:` or `categories or ALL`.

## Name things with the glossary's words

Names of modules, classes, functions, variables, tool parameters and test cases use the terms in `GLOSSARY.md`: Item, Source, Category, What's New, Checkpoint, and the Category names News, Applications, Engineering, Models. Flag any synonym the glossary lists under _Avoid_ (for example `article`, `feed` for a Source, `tag`, `digest`, `research`).

## Keep bilingual docs in step

`GLOSSARY.md` and every ADR in `docs/adr/` have an English part followed by a Traditional Chinese part with the same meaning, and `README.md` has a matching `README.zh-TW.md`. A change to one language's text includes the matching change to the other.

## Write code in English

Identifiers, comments, docstrings, log and error messages, and commit messages are in English. Text written for users of the tools (tool descriptions, warnings) is also in English.
