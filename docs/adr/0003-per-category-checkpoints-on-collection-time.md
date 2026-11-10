# One Checkpoint per Category, compared against collection time

What's New is everything collected since the last Checkpoint, looking back at most 7 days. There is one Checkpoint per Category, not one global Checkpoint. With a single Checkpoint, asking only about Models in the morning would move it past the day's News, and that News would never appear in What's New. Only `whats_new` moves a Checkpoint; `search` never does.

Checkpoints are compared against when an Item was **collected**, not when it was published. Some feeds give inaccurate publish times or publish late; comparing publish times would let an Item collected after the Checkpoint, but dated before it, be skipped silently.

## Consequences

- An Item in two Categories can appear twice: once under each Category's Checkpoint. We prefer an occasional repeat to missing something.
- The 30-day backfill on the first collection still filters by publish time, because there is no earlier collection time to compare against.
