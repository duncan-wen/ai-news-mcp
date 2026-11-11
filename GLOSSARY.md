# AI News

A personal AI news tracker. Every day it collects AI content from many sources and sorts it into Categories. Claude reads it through MCP.

個人使用的 AI 動態彙整：每天從多個來源收集 AI 相關內容並依分類整理，讓 Claude 透過 MCP 查詢。

## Language

### Content（內容）

**Item（一則）**:
One piece of content from a Source, such as a blog post, a new model, or a release.
從某個 Source 取得的單一內容，例如一篇部落格文章、一個新模型、一次版本發布。
_Avoid_: Article, post, entry, news（News is a Category, not a unit of content／News 是分類名稱，不是內容單位）

**Source（來源）**:
One fixed channel that provides Items, such as an RSS feed or an API endpoint.
提供 Item 的一個固定管道，例如某個 RSS feed 或某個 API 端點。
_Avoid_: Feed, site, channel

**Source config file（來源設定檔）**:
The user's own file, `sources.toml`, that adds Sources, disables built-in Sources, or changes their fields.
使用者自己的檔案 `sources.toml`，用來新增 Source、停用內建的 Source，或修改它們的欄位。
_Avoid_: Settings, feed list

### Viewing（查看）

**What's New（新進內容）**:
The Items collected since the last Checkpoint, going back 7 days at most. A query with no time range returns this.
自上次 Checkpoint 以來收進的 Items，最多回看 7 天。沒有指定時間範圍的查詢就回傳這個。
_Avoid_: Digest, feed, unread, latest

**Checkpoint（查看點）**:
The time you last viewed What's New. Items collected before it count as already seen.
上次查看 What's New 的時間點；早於它收進的 Items 視為已看過。
_Avoid_: Read marker, last seen, cursor

### Categories（分類）

**Category（分類）**:
The topic an Item belongs to. One Item can belong to several Categories. A Source gives only the default Categories.
Item 所屬的主題。一則 Item 可以同時屬於多個 Category；Source 只提供預設的 Category。
_Avoid_: Tag, topic, section

**News（新聞）**:
Events in the AI industry, such as launches, funding, policy, and people changes.
AI 產業事件，例如發布會、融資、政策、人事異動。
_Avoid_: Updates, headlines

**Applications（應用）**:
New AI products or tools that you can use right away.
可以直接拿來用的新 AI 產品或工具。
_Avoid_: Apps, products, tools

**Engineering（工程）**:
Content about how to build AI systems, such as technical posts, frameworks, lessons from practice, and releases.
關於怎麼打造 AI 系統的內容，例如技術文章、框架、實作經驗、版本更新。
_Avoid_: Dev, tech

**Models（模型）**:
Newly released or newly listed AI models, and changes to what they can do and what they cost. Academic papers and theory are not included.
新發布或新上架的 AI 模型，以及它們的能力和價格變化。不包含學術論文與理論研究。
_Avoid_: Research, Evolution（進化）, papers
