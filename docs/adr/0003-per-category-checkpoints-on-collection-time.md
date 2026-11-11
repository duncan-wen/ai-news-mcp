# One Checkpoint per Category, compared against collection time

What's New is everything collected since the last Checkpoint and published in the last 7 days. There is one Checkpoint per Category, not one global Checkpoint. With a single Checkpoint, asking only about Models in the morning would move it past the day's News, and that News would never appear in What's New. Only `whats_new` moves a Checkpoint; `search` never does.

Checkpoints are compared against when an Item was **collected**, not when it was published. Some feeds give inaccurate publish times or publish late; comparing publish times would let an Item collected after the Checkpoint, but dated before it, be skipped silently.

The 7-day limit is compared against when an Item was **published**. A first collection backfills 30 days, and so does a Source added later. All of those Items are collected at the same moment. Comparing the limit against collection time would put every one of them in What's New: 676 Items on a first use, about a million characters.

## Consequences

- An Item in two Categories can appear twice: once under each Category's Checkpoint. We prefer an occasional repeat to missing something.
- An Item collected after the Checkpoint but dated more than 7 days back is not in What's New. Only `search` finds it. This is the cost of keeping backfills out of What's New.
- `whats_new` returns at most `limit` Items, the most recently published. When there are more, the Checkpoints still move to now, so the Items left out count as seen, and the response says how many were left out. All of them were published in the last 7 days, before the oldest Item shown, so `search` finds them. Not moving the Checkpoints would return the same Items on every call. A paging cursor would need server state for a once-a-day view.

---

## 中文

### 每個 Category 各一個 Checkpoint，並以收集時間比較

What's New 是上次 Checkpoint 之後收進、而且是最近 7 天內發布的所有內容。每個 Category 各有一個 Checkpoint，而不是全部共用一個。如果只有一個，早上只問 Models，Checkpoint 就會越過當天的 News，那些 News 就永遠不會出現在 What's New。只有 `whats_new` 會推進 Checkpoint；`search` 永遠不會。

Checkpoint 比較的是 Item **收進來**的時間，不是發布時間。有些 feed 的發布時間不準，或是很晚才出現；如果比較發布時間，一則在 Checkpoint 之後才收進來、但發布時間標在 Checkpoint 之前的 Item，就會被默默跳過。

7 天上限比較的是 Item 的**發布**時間。第一次收集會往回抓 30 天，之後新增的 Source 也一樣，這些 Items 全都在同一刻收進來。如果 7 天上限也比較收集時間，它們會全部進入 What's New：第一次使用就是 676 則，大約一百萬個字元。

### 影響

- 屬於兩個 Category 的 Item 可能出現兩次，每個 Category 的 Checkpoint 各一次。偶爾重複，總比漏掉好。
- 一則在 Checkpoint 之後才收進來、但發布時間標在 7 天以前的 Item，不會出現在 What's New，只能用 `search` 找到。這是讓回溯內容不進 What's New 的代價。
- `whats_new` 最多回傳 `limit` 則，取發布時間最新的。超過時 Checkpoint 照樣移到現在，所以沒顯示的 Items 視為已看過，回應裡會寫明有幾則沒顯示。它們都是最近 7 天內、比顯示的最舊一則更早發布的，用 `search` 一定找得到。如果不移動 Checkpoint，每次呼叫都會拿到同樣的 Items；分頁游標則要在 server 記住狀態，對每天一次的查看來說太複雜。
