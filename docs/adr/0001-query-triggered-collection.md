# Collection is triggered by queries, not by a scheduler

There is no cron job, systemd timer or cloud scheduler. The MCP server starts a collection itself, in three cases: when it starts and the data is more than 24 hours old, when `whats_new` is called on data that old, and when `collect_now` is called. `whats_new` waits up to 90 seconds for a running collection before it returns the data it already has, with a note. We chose this because every user runs the server on their own machine, often under WSL or on a laptop that isn't always on. A scheduler is one more thing to install and debug, and it can silently stop running. Fresh data only matters at the moment someone asks, and the server is always running at that moment.

## Considered Options

- **Live fetch on every query**: rejected. Some feeds return their whole history (OpenAI: 1,375 items). Fetching that on every call is slow, makes us de-duplicate again each time, and keeps no history for "what happened last week".
- **OS scheduler (cron, systemd timer, Windows Task Scheduler)**: rejected. It is set up differently on each platform and doesn't run while the machine or WSL is off.
- **GitHub Actions in the cloud**: rejected. The SQLite store would then have to be synced back to every user's machine.

## Consequences

- The first `whats_new` of the day can take up to about a minute.
- Collection must be safe to run concurrently with queries, and only one collection may run at a time.
