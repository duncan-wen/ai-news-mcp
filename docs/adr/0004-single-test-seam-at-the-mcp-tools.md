# Tests go through the MCP tools only

The only test seam is the MCP tool interface. Tests call the five tools through FastMCP's in-memory client and check only what a client can see. They use a real SQLite database in a temporary file. Two dependencies at the edge of the system are replaced. The **Fetcher** returns trimmed real responses, saved as fixture files, and can simulate errors like 404, 410 and timeouts. The **Clock** is advanced by hand to test the 24-hour staleness rule, the 30-day backfill, the 7-day cap and Checkpoints. There are no unit tests for individual feed adapters or SQL queries. Every behaviour users care about shows up in tool output, so tests at this level let us refactor the internals freely. Fixtures copied from real responses (for example Mistral's feed, served as `text/plain`) cover parsing as well as adapter unit tests would.

## Consequences

- No automated test makes a real network call. Whether real Sources still work is checked with `list_sources`, by running `collect_now` by hand, and by the warning shown after three failures in a row.
