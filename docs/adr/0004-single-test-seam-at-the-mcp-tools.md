# Tests go through the MCP tools only

The only test seam is the MCP tool interface. Tests call the five tools through the MCP SDK's in-memory client (`mcp.Client(server)`) and check only what a client can see. They use a real SQLite database in a temporary file. Two dependencies at the edge of the system are replaced. The **Fetcher** returns trimmed real responses, saved as fixture files, and can simulate errors like 404, 410 and timeouts. The **Clock** is advanced by hand to test the 24-hour staleness rule, the 30-day backfill, the 7-day cap and Checkpoints. Tests may also pass their own Source list to `create_server`; the Source list is configuration, not a test double. There are no unit tests for individual feed adapters or SQL queries. Every behaviour users care about shows up in tool output, so tests at this level let us refactor the internals freely. Fixtures copied from real responses (for example Mistral's feed, served as `text/plain`) cover parsing as well as adapter unit tests would.

## Consequences

- No automated test makes a real network call. Whether real Sources still work is checked with `list_sources`, by running `collect_now` by hand, and by the warning shown after three failures in a row.

---

## 中文

### 測試只透過 MCP tool

唯一的測試 seam 是 MCP tool 介面。測試透過 MCP SDK 的 in-memory client（`mcp.Client(server)`）呼叫五個 tool，只檢查 client 看得到的結果，資料庫用暫存檔裡真的 SQLite。只替換系統邊緣的兩個依賴：**Fetcher** 回傳從真實回應精簡而來的 fixture 檔，也能模擬 404、410、逾時等錯誤；**Clock** 由測試手動推進，用來測 24 小時過舊、30 天回溯、7 天上限和 Checkpoint。測試也可以傳入自己的 Source 清單給 `create_server`；Source 清單是設定，不算替身。不為個別 feed adapter 或 SQL 查詢寫單元測試。使用者在意的每個行為都會反映在 tool 的輸出上，所以在這一層測試，就能放心重構內部。fixture 取自真實回應（例如 Mistral 回傳 `text/plain` 的 feed），對解析的涵蓋程度和 adapter 單元測試一樣好。

### 影響

- 沒有任何自動化測試會真的連網。真實 Source 還能不能用，靠 `list_sources`、手動執行 `collect_now`，以及連續失敗三次後出現的警告來確認。
