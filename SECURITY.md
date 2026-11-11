# Security

## Reporting a vulnerability

Report it privately through [GitHub private vulnerability reporting](https://github.com/duncan-wen/ai-news-mcp/security/advisories/new), not in a public issue. Say what an attacker controls, what they get, and how to reproduce it.

Only the latest release is supported: fixes go into a new release.

## What the server trusts

The server runs on your machine with your permissions and fetches URLs it does not choose itself:

- each Source's URL, including any Source you add in `sources.toml`;
- with `read_item`, an Item's original page, whose URL comes from the Source's feed. A Source that is compromised, or a Source you added, can point an Item at any `http` or `https` URL, including a host on your local network, and `read_item` returns that page's main text to the MCP client;
- any URL those redirect to: the server follows redirects, so a Source or an Item's page can send it anywhere a link could.

Fetched content is untrusted: titles, summaries and page text reach Claude as tool results, so a Source can put text in them that tries to instruct Claude. Treat what Claude reads from a Source as you would the Source's website.

Reports that matter most: content from a Source that makes the server read or write files, run code, or crash or hang the server.
