# AI News MCP

[English](https://github.com/duncan-wen/ai-news-mcp/blob/main/README.md)

一個 MCP server：從 23 個 Source（公司部落格、科技新聞網站、工程部落格、版本發布頁、Hacker News、Product Hunt、Hugging Face 與 OpenRouter）收集 AI 動態存進本機，讓 Claude 查詢有什麼新進內容、搜尋，以及讀取 Item 的全文。

它在你自己的電腦上執行，不需要 API key、排程器或任何雲端服務，也從不呼叫 LLM：你提問時，由 Claude 負責整理摘要。

**適合你嗎？** 如果你想讓 Claude 幫你整理 AI 動態，不用自己逛十幾個網站，也能接受 Claude 讀取公開 Source 上 Items 的標題與摘要，就適合。它不是有自己介面的新聞閱讀器，不會自己摘要 Items，也不會合併同一事件的 Items，也只知道它的 Source 發布過的內容。

## 功能

- **What's New（新進內容）**：依 Category 列出你上次查看之後收進、而且是最近 7 天內發布的所有內容。
- **搜尋**：依文字、發布時間、Category 和 Source 搜尋所有已收集的內容（歷史會保留，所以「上週」也查得到）。
- **全文**：摘要不夠時，抓取 Item 的原始網頁並擷取正文。
- **查詢時才收集**：資料超過 24 小時，server 啟動時或你問有什麼新進內容時，就會自己收集。第一次收集會往回抓 30 天。
- **Source 狀態**：列出每個 Source 與它最近的錯誤；某個 Source 連續 3 次收集失敗時會發出警告。

## 示範

可以這樣問 Claude：

- 「AI 最近有什麼新消息？」
- 「Models 有什麼新的？把同一個模型的 Items 放在一起。」
- 「找上週關於 MCP 的 Engineering Items。」
- 「讀第二篇的全文，幫我摘要。」
- 「哪些新聞 Source 抓不到？」

前兩個問題 Claude 會呼叫 `whats_new`，第三個呼叫 `search`，第四個呼叫 `read_item`，最後一個呼叫 `list_sources`，再根據取得的 Items 寫出回答。

## 安裝

需要 [uv](https://docs.astral.sh/uv/) 與 [Claude Code](https://claude.com/claude-code)。

```sh
claude mcp add --scope user ai-news -- uvx ai-news-mcp
```

這樣就完成了：`uvx` 會下載並執行這個套件，`--scope user` 讓它在每個專案都能用。開一個新的 Claude Code session，問「AI 最近有什麼新消息？」。第一次回答可能要等一分鐘左右，server 正在收集。

如果要改從 clone 下來的 repo 執行：

```sh
git clone https://github.com/duncan-wen/ai-news-mcp.git
claude mcp add --scope user ai-news -- uv run --directory /path/to/ai-news-mcp ai-news-mcp
```

其他 MCP client 也用同樣方式啟動：指令是 `uvx ai-news-mcp`，透過 stdio 溝通。Claude Desktop 的話，把它加進 `claude_desktop_config.json`（Settings > Developer > Edit Config；macOS 在 `~/Library/Application Support/Claude/`，Windows 在 `%APPDATA%\Claude\`），再重新啟動 Claude Desktop：

```json
{
  "mcpServers": {
    "ai-news": {
      "command": "uvx",
      "args": ["ai-news-mcp"]
    }
  }
}
```

如果 Claude Desktop 找不到 `uvx`，就把它的完整路徑寫進 `command`（`which uvx` 的輸出，Windows 上是 `where uvx`）。

## Tools（工具）

| Tool | 用途 |
| --- | --- |
| `whats_new` | 所問的每個 Category（未指定則全部）自上次 Checkpoint 以來收進、而且是最近 7 天內發布的 Items，大約最多 100 則，並把這些 Checkpoint 移到現在。 |
| `search` | 依文字、`since` / `until`、Category 和 Source id 搜尋 Items，新的在前。從不移動 Checkpoint。 |
| `read_item` | Item 原始網頁的正文。 |
| `list_sources` | 每個 Source 的網址、預設 Category 與收集狀態。 |
| `collect_now` | 立刻從每個 Source 收集，回報各自新增幾則或失敗原因。 |

## Categories（分類）

每則 Item 有一個以上的 Category。Source 提供預設的 Category，標題與摘要上的關鍵字規則再加上其他 Category（例如新聞 Source 的一則 Item 提到新模型，就也屬於 Models）。

| Category | 定義 |
| --- | --- |
| News（新聞） | AI 產業事件，例如發布會、融資、政策、人事異動。 |
| Applications（應用） | 可以直接拿來用的新 AI 產品或工具。 |
| Engineering（工程） | 關於怎麼打造 AI 系統的內容，例如技術文章、框架、實作經驗、版本更新。 |
| Models（模型） | 新發布或新上架的 AI 模型，以及它們的能力和價格變化。不包含學術論文與理論研究。 |

每個 Category 有自己的 Checkpoint，所以只問 Models 不會讓當天的 News 被當成已看過。

What's New 裡的每則 Item 只會出現一次：馬上再問一次會是空的，要等下一次收集收進新的 Items。想再看最近的 Items，就改用時間來問（「這週發布了什麼？」），Claude 會呼叫 `search`，它從不移動 Checkpoint。只有在你問「上次看過之後有什麼新的」時，Claude 才會呼叫 `whats_new`；帶時間（「今天」、「最近」）或帶主題的問題都會用 `search`，所以不會不小心把 Items 標成看過。所有連到這個 server 的 client（Claude Code、Claude Desktop、MCP Inspector）共用同一個 store 和同一組 Checkpoint，所以測試時在 Inspector 呼叫 `whats_new`，這些 Items 對 Claude 來說也算看過了。

這裡用到的名詞定義在 [GLOSSARY.md](https://github.com/duncan-wen/ai-news-mcp/blob/main/GLOSSARY.md)。

## Sources（來源）

| Source id | 名稱 | 預設 Category |
| --- | --- | --- |
| `openai-news` | OpenAI News | News |
| `google-deepmind` | Google DeepMind Blog | News |
| `google-ai` | Google AI (The Keyword) | News |
| `anthropic-news` | Anthropic News | News |
| `mistral-news` | Mistral News | News |
| `microsoft-ai` | Microsoft Source: AI | News |
| `techcrunch-ai` | TechCrunch AI | News |
| `the-verge-ai` | The Verge AI | News |
| `mit-technology-review-ai` | MIT Technology Review AI | News |
| `simon-willison` | Simon Willison | Engineering |
| `latent-space` | Latent Space | Engineering |
| `langchain-blog` | LangChain Blog | Engineering |
| `vercel-blog` | Vercel Blog | Engineering |
| `cloudflare-blog` | Cloudflare Blog | Engineering |
| `hugging-face-blog` | Hugging Face Blog | Engineering |
| `nvidia-blog` | NVIDIA Blog | Engineering |
| `aws-machine-learning` | AWS Machine Learning Blog | Engineering |
| `vllm-releases` | vLLM releases | Engineering |
| `transformers-releases` | Transformers releases | Engineering |
| `hacker-news-ai` | Hacker News: AI（100 分以上、標題與 AI 有關的 story） | Applications |
| `product-hunt-ai` | Product Hunt: AI | Applications |
| `hugging-face-models` | Hugging Face: trending models | Models |
| `openrouter-models` | OpenRouter: new models | Models |

## Source config file（來源設定檔）

要新增自己的 Source、停用內建的 Source 或修改它們的欄位，就在設定目錄建立 `sources.toml`。沒有這個檔案 server 也能正常執行。

| 平台 | 位置 |
| --- | --- |
| Linux、WSL | `~/.config/ai-news-mcp/sources.toml`（或 `$XDG_CONFIG_HOME/ai-news-mcp/`） |
| macOS | `~/Library/Application Support/ai-news-mcp/sources.toml` |
| Windows | `%LOCALAPPDATA%\ai-news-mcp\sources.toml` |

```toml
disabled = ["techcrunch-ai"]          # 不要收集的內建 Source id

[sources.my-blog]                     # 新的 Source：name、url 與 default_categories
name = "My Blog"
url = "https://example.com/feed.xml"  # RSS 或 Atom
default_categories = ["Engineering"]  # News、Applications、Engineering、Models 任選

[sources.openai-news]                 # 內建 Source 的 id：只改寫出來的欄位
url = "https://openai.com/news/rss.xml"
```

- 新的 Source 需要 `name`、`url` 和 `default_categories`。它的 `kind` 預設是 `rss`（RSS 或 Atom）；其他 kind 就是內建 Source 用的那些（`anthropic-sitemap`、`hn-algolia`、`hf-models`、`openrouter-models`）。
- 以內建 Source 命名的 table 只改它寫出來的欄位（`name`、`url`、`default_categories`、`kind`）。
- 檔案格式有誤（不認得的鍵或 Category、`disabled` 裡的 id 不是內建 Source）時 server 不會啟動，錯誤訊息會說明要修正什麼。修改後要重新啟動 server（開一個新的 Claude Code session）。

收集到的 Items 存在資料目錄的 SQLite 檔（Linux 上是 `~/.local/share/ai-news-mcp/store.sqlite3`）。刪掉它就會重新開始，再做一次 30 天的收集。

## 設計決策

每個決策都有一份架構決策紀錄（ADR），放在 [docs/adr/](https://github.com/duncan-wen/ai-news-mcp/blob/main/docs/adr/)：

- [收集由查詢觸發，不用排程器](https://github.com/duncan-wen/ai-news-mcp/blob/main/docs/adr/0001-query-triggered-collection.md)：不用安裝或維持任何東西運作，常關機的筆電與 WSL 也能用。
- [Server 從不呼叫 LLM，由 Claude 負責推理](https://github.com/duncan-wen/ai-news-mcp/blob/main/docs/adr/0002-no-llm-in-the-server.md)：Category 來自關鍵字規則，不需要 API key，執行不花錢。
- [每個 Category 一個 Checkpoint，以收集時間比較](https://github.com/duncan-wen/ai-news-mcp/blob/main/docs/adr/0003-per-category-checkpoints-on-collection-time.md)：問某個 Category 不會讓別的 Category 的 Items 消失，發布時間標得晚的 Item 也不會被跳過。
- [測試只透過 MCP tools](https://github.com/duncan-wen/ai-news-mcp/blob/main/docs/adr/0004-single-test-seam-at-the-mcp-tools.md)。

## 使用條款

本專案不營運任何服務：在你電腦上的 server 直接向各個 Source 抓取，以連到本 repo 的 User-Agent 表明身分，並拉開對同一主機的請求間隔。各 Source 的使用條款由使用者自行遵守。資料庫只存在你的電腦上；Claude 只會看到 tools 回傳的 Items。

## 開發

```sh
uv sync
scripts/check   # lint、格式、型別與測試，和 CI 跑的一樣
scripts/fix     # 套用格式化與 lint 自動修正
uv build        # 把 sdist 與 wheel 建置到 dist/
```

回報問題與提出修改的方式在 [CONTRIBUTING.md](https://github.com/duncan-wen/ai-news-mcp/blob/main/CONTRIBUTING.md)（英文），各版本的變更在 [CHANGELOG.md](https://github.com/duncan-wen/ai-news-mcp/blob/main/CHANGELOG.md)。Source 的網址、速率限制與特殊狀況記在 [docs/research/ai-news-sources.md](https://github.com/duncan-wen/ai-news-mcp/blob/main/docs/research/ai-news-sources.md)，程式規範在 [CODING_STANDARDS.md](https://github.com/duncan-wen/ai-news-mcp/blob/main/CODING_STANDARDS.md)。

## 授權

[MIT](https://github.com/duncan-wen/ai-news-mcp/blob/main/LICENSE)
