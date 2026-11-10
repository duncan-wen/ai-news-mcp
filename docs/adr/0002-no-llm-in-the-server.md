# The server never calls an LLM; Claude does the reasoning

At collection time, Categories are assigned without an LLM: each Item gets its Source's default Categories, plus Categories added by keyword rules on the title and summary. The server does not summarise anything, does not classify in detail, and does not merge reports of the same event. The Claude client that calls the MCP tools does all of that at query time: it already reads every result, so asking another LLM to pre-process them would cost twice. This also means no API key is needed and running the server costs nothing, which matters for an open-source tool.

## Consequences

- Keyword rules will misclassify some Items. We accept this, because an Item can have several Categories and Claude can re-judge at query time.
- De-duplication only merges Items whose normalised URLs match. Different reports of the same event are kept as separate Items for Claude to group.
