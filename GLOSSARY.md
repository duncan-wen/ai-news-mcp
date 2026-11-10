# AI News

一個個人使用的 AI 動態彙整：每天從多個來源收集 AI 相關內容，依分類整理，供 Claude 透過 MCP 查詢。

## Language

### 內容

**Item（一則）**:
從某個 Source 取得的單一內容，例如一篇部落格文章、一篇論文、一個新模型、一次版本發布。
_Avoid_: Article, post, entry, news（News 是分類名稱，不是內容單位）

**Source（來源）**:
提供 Item 的一個固定管道，例如某個 RSS feed 或某個 API 端點。
_Avoid_: Feed, site, channel

### 查看

**What's New（新進內容）**:
自上次 Checkpoint 以來收進的 Items，最多回看 7 天。沒有指定時間範圍時，查詢就回這個。
_Avoid_: Digest, feed, unread, latest

**Checkpoint（查看點）**:
上次查看 What's New 的時間點；早於它的 Items 視為已看過。
_Avoid_: Read marker, last seen, cursor

### 分類

**Category（分類）**:
Item 所屬的主題。一則 Item 可以同時屬於多個 Category；Source 只提供預設 Category。
_Avoid_: Tag, topic, section

**News（新聞）**:
AI 產業事件，例如發布會、融資、政策、人事異動。
_Avoid_: Updates, headlines

**Applications（應用）**:
可以直接拿來用的新 AI 產品或工具。
_Avoid_: Apps, products, tools

**Engineering（工程）**:
關於怎麼打造 AI 系統的內容，例如技術文章、框架、實作經驗、版本更新。
_Avoid_: Dev, tech

**Research（研究）**:
論文、新模型，以及 benchmark 和排行榜的變化。
_Avoid_: Evolution（進化）, papers, science
