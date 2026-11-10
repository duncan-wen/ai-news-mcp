# One Checkpoint per Category, compared against collection time

What's New is everything collected since the last Checkpoint, looking back at most 7 days. There is one Checkpoint per Category, not one global Checkpoint. With a single Checkpoint, asking only about Models in the morning would move it past the day's News, and that News would never appear in What's New. Only `whats_new` moves a Checkpoint; `search` never does.

Checkpoints are compared against when an Item was **collected**, not when it was published. Some feeds give inaccurate publish times or publish late; comparing publish times would let an Item collected after the Checkpoint, but dated before it, be skipped silently.

## Consequences

- An Item in two Categories can appear twice: once under each Category's Checkpoint. We prefer an occasional repeat to missing something.
- The 30-day backfill on the first collection still filters by publish time, because there is no earlier collection time to compare against.

---

## 中文

### 每個 Category 各一個 Checkpoint，並以收集時間比較

What's New 是上次 Checkpoint 之後收進的所有內容，最多回看 7 天。每個 Category 各有一個 Checkpoint，而不是全部共用一個。如果只有一個，早上只問 Models，Checkpoint 就會越過當天的 News，那些 News 就永遠不會出現在 What's New。只有 `whats_new` 會推進 Checkpoint；`search` 永遠不會。

Checkpoint 比較的是 Item **收進來**的時間，不是發布時間。有些 feed 的發布時間不準，或是很晚才出現；如果比較發布時間，一則在 Checkpoint 之後才收進來、但發布時間標在 Checkpoint 之前的 Item，就會被默默跳過。

### 影響

- 屬於兩個 Category 的 Item 可能出現兩次，每個 Category 的 Checkpoint 各一次。偶爾重複，總比漏掉好。
- 第一次收集的 30 天回溯仍然用發布時間篩選，因為那時還沒有更早的收集時間可以比較。
