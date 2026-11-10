# Collection is triggered by queries, not by a scheduler

There is no cron job, systemd timer or cloud scheduler. The MCP server starts a collection itself, in three cases: when it starts and the data is more than 24 hours old, when `whats_new` is called on data that old, and when `collect_now` is called. `whats_new` waits up to 90 seconds for a running collection before it returns the data it already has, with a note. We chose this because every user runs the server on their own machine, often under WSL or on a laptop that isn't always on. A scheduler is one more thing to install and debug, and it can silently stop running. Fresh data only matters at the moment someone asks, and the server is always running at that moment.

## Considered Options

- **Live fetch on every query**: rejected. Some feeds return their whole history (OpenAI: 1,375 items). Fetching that on every call is slow, makes us de-duplicate again each time, and keeps no history for "what happened last week".
- **OS scheduler (cron, systemd timer, Windows Task Scheduler)**: rejected. It is set up differently on each platform and doesn't run while the machine or WSL is off.
- **GitHub Actions in the cloud**: rejected. The SQLite store would then have to be synced back to every user's machine.

## Consequences

- The first `whats_new` of the day can take up to about a minute.
- Collection must be safe to run concurrently with queries, and only one collection may run at a time.
- A collection in which every Source failed, for example while the machine is offline, does not count: the data stays over 24 hours old, so the next `whats_new` collects again. Each of those attempts counts as one more failure in a row for every Source, so after three `whats_new` calls offline, the warning about failing Sources appears.

---

## 中文

### 由查詢觸發收集，不使用排程器

不使用 cron、systemd timer 或雲端排程。收集由 MCP server 自己觸發，有三種情況：server 啟動時資料已超過 24 小時沒更新、呼叫 `whats_new` 時資料已超過 24 小時沒更新、呼叫 `collect_now`。`whats_new` 遇到收集正在進行時，最多等 90 秒；超過就先回傳現有資料，並附上說明。這樣決定，是因為每位使用者都在自己的電腦上執行 server，常常是在 WSL 裡，或是在不會一直開機的筆電上。排程器是多一個要安裝、要除錯的東西，而且可能停了也沒人發現。資料只有在有人查詢的那一刻才需要是新的，而那一刻 server 一定在執行。

### 考慮過的選項

- **每次查詢都即時抓取**：否決。有些 feed 會回傳完整歷史（OpenAI 一次給 1,375 則），每次都抓既慢、又要重新去重複，而且留不下「上週發生什麼事」的歷史資料。
- **作業系統排程器（cron、systemd timer、Windows 工作排程器）**：否決。每個平台的設定方式都不同，而且電腦或 WSL 沒開時就不會執行。
- **在雲端用 GitHub Actions 執行**：否決。SQLite 資料庫還得同步回每位使用者的電腦。

### 影響

- 每天第一次呼叫 `whats_new` 可能要等一分鐘左右。
- 收集必須能和查詢同時進行而不出錯，而且同一時間只能有一次收集。
- 如果一次收集裡每個 Source 都失敗（例如電腦沒有連網），這次收集不算數：資料仍然超過 24 小時沒更新，下一次呼叫 `whats_new` 會再收集一次。每一次這樣的嘗試，都會讓每個 Source 的連續失敗次數加一，所以沒連網時呼叫三次 `whats_new`，就會出現 Source 一直失敗的警告。
