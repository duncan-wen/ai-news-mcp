# AI 新聞資料來源可用性調查（RSS / Public API）

- **調查日期（fetch date）**：2026-11-11（伺服器回應時間戳約為 2026-11-10 16:xx UTC）
- **方法**：以 `curl`（瀏覽器 User-Agent，跟隨 redirect）實際抓取每個 feed / API endpoint，記錄 HTTP status、Content-Type、項目數、`<content:encoded>`/`<content>` 是否存在與內文平均長度；官方文件以 WebFetch 讀取。
- **標記**：**Verified** = 本次親自抓取確認；**Unverified** = 未能直接確認（被擋或僅推論）。
- 「全文？」判斷依據：feed 內 `content:encoded` / Atom `content` 是否存在、平均長度（數千字元以上視為全文）。

---

## 1. 總覽表

| Source | 類別 | 存取方式 | URL | Auth | 全文？ | 狀態 |
|---|---|---|---|---|---|---|
| OpenAI News | News | RSS | https://openai.com/news/rss.xml | 無 | 否（摘要，avg ~180 字元） | Verified (200) |
| Anthropic News | News | **無官方 RSS** → RSSHub / scrape | RSSHub `/anthropic/news`；HTML https://www.anthropic.com/news；sitemap https://www.anthropic.com/sitemap.xml | 無 | 需另抓頁面 | Verified（RSS 404；RSSHub route 存在於原始碼） |
| Anthropic Engineering | Engineering | **無官方 RSS** → RSSHub / scrape | RSSHub `/anthropic/engineering`；HTML https://www.anthropic.com/engineering | 無 | 需另抓頁面 | Verified（同上） |
| Google DeepMind Blog | News/Research | RSS | https://deepmind.google/blog/rss.xml | 無 | 否（短摘要 ~110 字元） | Verified (200) |
| Google Keyword – AI | News | RSS | https://blog.google/technology/ai/rss/（301 → https://blog.google/innovation-and-ai/technology/ai/rss/） | 無 | 否（摘要） | Verified (200, redirect) |
| Google Research Blog | Research | RSS | https://research.google/blog/rss/ | 無 | 否（幾乎只有標題） | Verified (200) |
| Meta AI Blog | News | **無可用 RSS**（400）→ RSSHub `/meta/ai/blog` | https://ai.meta.com/blog/ | 無 | — | Verified（官方 400；RSSHub route 存在） |
| Microsoft Research Blog | Research | RSS | https://www.microsoft.com/en-us/research/feed/ | 無 | **是**（avg ~18k 字元） | Verified (200) |
| Microsoft Source – AI | News | RSS | https://news.microsoft.com/source/topics/ai/feed/ | 無 | 是（WordPress content:encoded） | Verified (200) |
| Microsoft AI Blog（舊） | News | **已失效** | https://blogs.microsoft.com/ai/feed/ → **410 Gone** | — | — | Verified (410) |
| Mistral News | News | RSS | https://mistral.ai/news/rss（`/rss.xml` 會 redirect 到此；`/news/rss.xml` 404） | 無 | 否（摘要） | Verified (200, Content-Type 為 text/plain) |
| Hugging Face Blog | News/Eng | RSS | https://huggingface.co/blog/feed.xml | 無 | 否（只有標題/連結） | Verified (200) |
| TechCrunch AI | News | RSS | https://techcrunch.com/category/artificial-intelligence/feed/ | 無 | 否（摘要） | Verified (200) |
| The Verge AI | News | Atom | https://www.theverge.com/rss/ai-artificial-intelligence/index.xml | 無 | 部分（avg ~960 字元） | Verified (200) |
| MIT Technology Review AI | News | RSS | https://www.technologyreview.com/topic/artificial-intelligence/feed | 無 | **是**（avg ~4k 字元） | Verified (200) |
| Product Hunt | Apps | API v2 GraphQL / Atom feed | API https://api.producthunt.com/v2/api/graphql；Feed https://www.producthunt.com/feed（可加 `?category=artificial-intelligence`） | API：OAuth / developer token；Feed：無 | Feed：摘要 | Verified（API 無 token 401；feed 200） |
| Hacker News（Firebase） | Apps/Eng | 官方 API | https://hacker-news.firebaseio.com/v0/topstories.json | 無 | 標題+URL（非文章全文） | Verified (200) |
| HN Algolia Search | Apps/Eng | API | https://hn.algolia.com/api/v1/search_by_date?query=LLM&tags=story | 無 | 同上 | Verified (200) |
| hnrss.org（第三方） | Apps/Eng | RSS | https://hnrss.org/frontpage、https://hnrss.org/newest?q=LLM&points=50 | 無 | 否 | Verified (200) |
| GitHub Trending | Apps | **無官方 API** → scrape / RSSHub（需 token） / Search API 近似 | https://github.com/trending；RSSHub `/github/trending/:since/:language/:spoken_language?` | RSSHub route 需 `GITHUB_ACCESS_TOKEN` | — | Verified |
| GitHub Releases | Eng | Atom | 例：https://github.com/vllm-project/vllm/releases.atom | 無 | release notes | Verified (200) |
| Reddit r/LocalLLaMA 等 | Apps | `.rss` 可用但限流極嚴；`.json` 未授權 **403** | https://www.reddit.com/r/LocalLLaMA/.rss | `.json`/API 需 OAuth | 部分 | Verified（.rss 200 但 remaining=0；r/MachineLearning .rss 429；.json 403） |
| Simon Willison | Eng | Atom | https://simonwillison.net/atom/everything/ | 無 | **是** | Verified (200) |
| Latent Space | Eng | RSS (Substack) | https://www.latent.space/feed（→ https://latent.space/feed） | 無 | **是** | Verified (200) |
| LangChain Blog | Eng | RSS | https://www.langchain.com/blog/rss.xml（舊 `blog.langchain.dev/rss/` 只會 redirect 到 HTML） | 無 | 否（摘要 ~160 字元） | Verified (200) |
| Vercel Blog | Eng | Atom | https://vercel.com/atom | 無 | 是（avg ~2.6k） | Verified (200) |
| Cloudflare Blog | Eng | RSS | https://blog.cloudflare.com/rss/ | 無 | **是** | Verified (200) |
| arXiv RSS (cs.AI/CL/LG) | Research | RSS | https://rss.arxiv.org/rss/cs.AI 、/cs.CL 、/cs.LG | 無 | abstract | Verified (200) |
| arXiv API | Research | Atom API | https://export.arxiv.org/api/query?search_query=cat:cs.CL&sortBy=submittedDate&sortOrder=descending | 無 | abstract | Verified (200) |
| HF Daily Papers API | Research | JSON API | https://huggingface.co/api/daily_papers | 無（rate limit 依 IP） | abstract + ai_summary | Verified (200) |
| HF Hub Models API | Evolution | JSON API | https://huggingface.co/api/models?sort=trendingScore&limit=20 、`?sort=createdAt&direction=-1` | 無（建議帶 HF_TOKEN） | metadata | Verified (200) |
| OpenRouter Models | Evolution | JSON API | https://openrouter.ai/api/v1/models | 實測不需 key（文件標示全域 bearer） | metadata+pricing | Verified (200, 467 models) |
| Papers with Code | Research | **已關閉** → redirect 到 HF | https://paperswithcode.com/ → 302 https://huggingface.co/papers/trending | — | — | Verified |
| LMArena（已改名 **Arena**, arena.ai） | Evolution | 網站 Cloudflare 擋；**HF dataset** | https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset | 無 | parquet 資料 | Verified（網站 403；dataset 200, CC-BY-4.0） |
| X/Twitter API | Social | 付費 API（pay-per-use） | https://docs.x.com/x-api/getting-started/pricing | OAuth + 付費 | — | Verified（文件） |
| RSSHub | Fallback | 自架 | https://github.com/DIYgod/RSSHub | — | — | Verified（public instance 403 並聲明僅供測試） |
| **加碼**：Import AI | Research/News | RSS | https://importai.substack.com/feed | 無 | 是 | Verified (200) |
| **加碼**：Interconnects | Research | RSS | https://www.interconnects.ai/feed | 無 | 是 | Verified (200) |
| **加碼**：NVIDIA Blog | News | RSS | https://blogs.nvidia.com/feed/ | 無 | 是 | Verified (200) |
| **加碼**：AWS ML Blog | Eng | RSS | https://aws.amazon.com/blogs/machine-learning/feed/ | 無 | 是 | Verified (200) |

---

## 2. 各來源細節

### 2.1 News

**OpenAI** — Verified
- `https://openai.com/news/rss.xml` → 200 `text/xml`；舊 `https://openai.com/blog/rss.xml` 會 redirect 到同一個 URL。
- 驚喜點：feed 一次回傳 **1,375 個 item**（整個歷史），約 1.1 MB，只有 `<description>` 摘要（avg ~178 字元），沒有 `content:encoded`。實作時要用 `pubDate`/guid 去重並只取最新 N 筆。

**Anthropic（News / Engineering / Research）** — Verified：**沒有官方 RSS**
- 測試 `https://www.anthropic.com/rss.xml`、`/news/rss.xml`、`/news/rss`、`/feed.xml`、`/engineering/rss.xml`（會 redirect 到 `/research/rss.xml`）全部 **404**；HTML 頁 https://www.anthropic.com/news 和 https://www.anthropic.com/engineering 沒有 `<link rel="alternate" type="application/rss+xml">`。
- Fallback 1：`https://www.anthropic.com/sitemap.xml`（200）列出 280 個 `/news/` 和 217 個 `/research/` URL，但**沒有 `/engineering/` 文章**，所以 engineering 只能解析 HTML 列表頁。
- Fallback 2：RSSHub routes `/anthropic/news`、`/anthropic/engineering`、`/anthropic/research`（以及 `red`），已從原始碼確認存在：https://github.com/DIYgod/RSSHub/tree/master/lib/routes/anthropic

**Google DeepMind** — Verified：`https://deepmind.google/blog/rss.xml` → 200，100 items，description ~110 字元。

**Google AI（The Keyword）** — Verified：`https://blog.google/technology/ai/rss/` 會 301 到 `https://blog.google/innovation-and-ai/technology/ai/rss/`（路徑已改，建議直接用新 URL），20 items，摘要。

**Google Research** — Verified：`https://research.google/blog/rss/` → 200，100 items，description 幾乎是空的（avg 20 字元），只能拿到標題和連結。

**Meta AI** — Verified：`https://ai.meta.com/blog/`、`/blog/rss/` 對 curl 都回 **400**（Meta 擋非瀏覽器請求）。RSSHub route `/meta/ai/blog` 存在（原始碼 https://github.com/DIYgod/RSSHub/blob/master/lib/routes/meta/ai-blog.ts ，它呼叫的是 `https://ai.meta.com/api/graphql/`）。從自家伺服器呼叫是否一樣被 400 擋：**Unverified**。

**Microsoft** — Verified
- Microsoft Research：`https://www.microsoft.com/en-us/research/feed/` → 200，10 items，**全文**（avg ~18k 字元）。
- 驚喜點：`https://blogs.microsoft.com/ai/feed/` → **410 Gone**；`https://www.microsoft.com/en-us/ai/blog/` 會 redirect 到 Microsoft Cloud Blog（企業行銷取向）。
- 改用 Microsoft Source 的 AI 分類：`https://news.microsoft.com/source/topics/ai/feed/`（在 https://news.microsoft.com/source/topics/ai/ 的 `<link rel=alternate>` 中找到）→ 200。

**Mistral** — Verified：`https://mistral.ai/news/rss`（在 https://mistral.ai/news 的 `<link rel=alternate>` 中找到）→ 200，94 items，摘要。注意 Content-Type 是 `text/plain`，解析器不要依 MIME type 判斷；`/news/rss.xml` 是 404。

**Hugging Face Blog** — Verified：`https://huggingface.co/blog/feed.xml` → 200，901 items（全歷史），description 幾乎是空的，只有標題和連結。

**TechCrunch AI** — Verified：`https://techcrunch.com/category/artificial-intelligence/feed/` → 200，20 items，摘要。

**The Verge AI** — Verified：`https://www.theverge.com/rss/ai-artificial-intelligence/index.xml` → 200 Atom，10 items，`<content>` avg ~960 字元（部分內文）。

**MIT Technology Review AI** — Verified：`https://www.technologyreview.com/topic/artificial-intelligence/feed` → 200，10 items，`content:encoded` avg ~4k 字元（接近全文；付費牆文章可能截斷，Unverified）。

### 2.2 Applications

**Product Hunt** — Verified
- API v2 GraphQL：`POST https://api.producthunt.com/v2/api/graphql` 不帶 token 會回 **401** `invalid_oauth_token`。
- 文件 https://api.producthunt.com/v2/docs ：可用 dashboard 發的 `developer_token`（不會過期）或 OAuth client-credentials（只能存取公開 endpoint）。rate limit 採「fair-use」，文件頁沒有列出數字。
- **ToS 重點**：文件寫明 API "must not be used for commercial purposes"，商業用途要寫信到 hello@producthunt.com 洽談。
- 替代方案：官方 Atom feed `https://www.producthunt.com/feed` → 200，50 entries，免 auth；`?category=artificial-intelligence` 回傳的內容不同（hash 不同），分類過濾看起來有效，但沒有逐筆核對分類。RSSHub 也有 `/producthunt/today`。

**Hacker News** — Verified
- 官方 Firebase API（文件 https://github.com/HackerNews/API ）：`/v0/topstories.json`、`newstories`、`beststories`、`askstories`、`showstories`、`item/<id>.json`、`updates`、`maxitem`。文件寫明 "There is currently no rate limit."；不需 auth。
- Algolia HN Search：`https://hn.algolia.com/api/v1/search`、`/search_by_date` → 200。限流文字從 https://hn.algolia.com/api 頁面的 JS bundle 取得："We are limiting the number of API requests from a single IP to 10,000 per hour."
- 第三方 hnrss.org 支援關鍵字和分數門檻（例如 `?q=LLM&points=50`），可直接當 RSS 用。

**GitHub Trending** — Verified：**沒有官方 Trending API**
- https://docs.github.com/en/rest/search/search 沒有提到 trending。Search API 限流：authenticated 30 req/min，unauthenticated 10 req/min（`/rate_limit` 實測未授權：core 60/hr、search 10）。
- 近似做法：`/search/repositories?q=created:>YYYY-MM-DD+topic:llm&sort=stars`（200，已實測）。
- Scrape：https://github.com/trending → 200，HTML 內有 `Box-row`（實測 12 個 match）。
- RSSHub `/github/trending/:since/:language/:spoken_language?`：從原始碼 https://github.com/DIYgod/RSSHub/blob/master/lib/routes/github/trending.tsx 確認，**必須設定 `GITHUB_ACCESS_TOKEN`**，否則會丟出 ConfigNotFoundError。

**Reddit** — Verified（行為）/ 部分 Unverified（政策細節）
- `https://www.reddit.com/r/LocalLLaMA/.rss` → 200 Atom，但 response header 是 `x-ratelimit-remaining: 0.0`、`x-ratelimit-reset: 55`，**第一個請求就把配額用完**。
- 接著 `r/MachineLearning/.rss` → **429**。
- `https://www.reddit.com/r/LocalLLaMA/hot.json` 未授權 → **403**；`old.reddit.com/.json` → 302。
- 結論：未授權的 `.json` 實際上已不能用，`.rss` 只能做極低頻輪詢；正式使用需走 OAuth Data API。
- Data API Terms（https://redditinc.com/policies/data-api-terms ，Last Revised July 20, 2026）：商業用途或超出 rate limit 需另簽協議；未經權利人許可，不得用 User Content 訓練 ML/AI 模型。
- Reddit Data API Wiki（support.reddithelp.com）對 curl 和 WebFetch 都回 403，具體 QPM 數字（一般流傳為 OAuth 100 QPM）為 **Unverified**。

### 2.3 Engineering

- **Simon Willison** — Verified：`https://simonwillison.net/atom/everything/` → 200 Atom，30 entries，全文（avg ~3.4k）。另有 `/atom/entries/`（只有長文），未測。
- **Latent Space** — Verified：`https://www.latent.space/feed` → redirect `https://latent.space/feed` → 200，`content:encoded` 全文（含 podcast transcript，單篇最大約 228 KB）。
- **LangChain** — Verified：驚喜點是舊的 `blog.langchain.dev/rss/` 和 `blog.langchain.com/rss/` 都 redirect 到 HTML（`www.langchain.com/blog`，已搬到 Webflow），正確 URL 是 `https://www.langchain.com/blog/rss.xml`（100 items，摘要）。RSSHub 也有 `/langchain/blog`。
- **Vercel** — Verified：`https://vercel.com/atom` → 200 Atom，100 entries，`<content>` avg ~2.6k。
- **Cloudflare** — Verified：`https://blog.cloudflare.com/rss/` → 200，20 items，全文（avg ~7k）。
- **GitHub Releases**（例如 vLLM、llama.cpp、transformers）— Verified：`https://github.com/<owner>/<repo>/releases.atom` → 200。

### 2.4 Research / Model evolution

**arXiv** — Verified
- RSS：`https://rss.arxiv.org/rss/cs.AI`、`cs.CL`、`cs.LG` 都回 200；cs.AI 單日 887 items，內含 abstract（avg ~1.5k）。
- API：`https://export.arxiv.org/api/query?...` → 200 Atom（feed 內 self link 已改為 `arxiv.org/api/query`）。
- ToU（https://info.arxiv.org/help/api/tou.html ）：
  - RSS、OAI-PMH、API 都算 legacy API，"make no more than one request every three seconds"，"limit requests to a single connection at a time"，不得靠多台機器規避限流。
  - metadata 採 CC0。
  - 未經許可不得從自己的伺服器 store/serve e-prints（PDF、source）。
  - 不得暗示 arXiv 背書。

**Hugging Face Daily Papers** — Verified
- `https://huggingface.co/api/daily_papers?limit=N` → 200 JSON。欄位：title、summary、upvotes、githubRepo、githubStars、`ai_summary`、`ai_keywords`、arXiv id 等。
- OpenAPI（https://huggingface.co/.well-known/openapi.json ）列出參數 `p, limit, date, week, month, submitter, sort`，另有 `/api/papers/search`、`/api/papers/{paperId}`。
- 驚喜點：`https://huggingface.co/papers.rss` 是 404，**沒有官方 RSS**。RSSHub 有 `/huggingface/daily-papers/:cycle?/:voteFliter?`。

**Hugging Face Hub Models** — Verified
- `?sort=trendingScore`（回傳 trendingScore 欄位）和 `?sort=createdAt&direction=-1` 都實測可用。
- 新模型列表雜訊很多（例如 `ringtone-ro/...`），需要用 likes、downloads、author 白名單過濾。
- Rate limits（https://huggingface.co/docs/hub/rate-limits ，September '25 表格）：Anonymous 每 IP 500 API req / 5 分鐘；Free user 1,000；PRO 2,500。建議一律帶 `HF_TOKEN`。

**OpenRouter Models** — Verified
- `https://openrouter.ai/api/v1/models` 不帶 key 也回 200，共 467 models。
- 欄位：`created`（unix）、`pricing`、`context_length`、`knowledge_cutoff`、`hugging_face_id` 等。用 `created` 排序就能追「新模型上架」。
- 文件 https://openrouter.ai/docs/api-reference/models/get-models 把 bearer 列為全域 security；目前實測公開可用，但未來可能改變。

**Papers with Code** — Verified：**已停止服務**。`https://paperswithcode.com/`、`/sota`、`/api/v1/papers/` 全部 302 到 `https://huggingface.co/papers/trending`，舊 API 已不存在。RSSHub 也沒有相關 route（`lib/routes/paperswithcode` 404）。

**LMArena** — Verified
- 驚喜點：`lmarena.ai/leaderboard` 會 redirect 到 **`arena.ai/leaderboard`**（已改名），而且被 Cloudflare challenge 擋（403 "Just a moment..."）。
- 官方 HF Space `lmarena-ai/chatbot-arena-leaderboard` 已改名為 `lmarena-ai/arena-leaderboard`，lastModified 是 2026-02，看起來已不再更新。
- **最佳來源**：HF dataset `lmarena-ai/leaderboard-dataset`（https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset ）。lastModified 2026-11-10，license CC-BY-4.0。subsets 有 text、text_style_control、vision、webdev、search、agent、text_to_image、text_to_video 等，每個都有 `latest` 和 `full`（歷史）parquet split，可用 HF datasets-server 或直接下載 parquet。

### 2.5 其他

**X / Twitter API** — Verified（https://docs.x.com/x-api/getting-started/pricing ）
- 現行是 **pay-per-usage**，沒有訂閱或最低消費，文件頁**沒有提到 free tier**。
- 價格：Post read $0.005/則、User read $0.010、Post create $0.015、Trends $0.010/req。
- Pay-per-use 上限是每月 3M post reads，超過要 Enterprise。同一資源在 24h UTC 內去重，不重複計費。
- 結論：可行但要付費，建議 MVP 先跳過。

**RSSHub** — Verified
- Public instance `https://rsshub.app/anthropic/news` 回 **403**，回應內容寫明：rsshub.app "is intended for testing purposes only and should not be used as a production RSS source… we strongly recommend self-hosting RSSHub."
- docs.rsshub.app 對 curl 回 403、對 WebFetch 回 404，所以本報告的 route 存在性改以 **GitHub 原始碼**為準（`lib/routes/<namespace>/*.ts` 的 `path`/`example` 欄位）：anthropic(news/engineering/research)、github/trending（需 token）、producthunt/today、meta/ai/blog、huggingface/daily-papers、langchain/blog、openai(news/research/cookbook)、arxiv/query。docs 頁本身是否列出這些 route：**Unverified**。

---

## 3. 建議

### 直接用 RSS/Atom（免 auth，穩定）
- **News**：OpenAI、DeepMind、Google Keyword AI（新 URL）、Google Research、Microsoft Research、Microsoft Source AI、Mistral（`/news/rss`）、HF Blog、TechCrunch AI、The Verge AI、MIT Tech Review AI、NVIDIA Blog
- **Engineering**：Simon Willison、Latent Space、LangChain（`www.langchain.com/blog/rss.xml`）、Vercel、Cloudflare、AWS ML、GitHub releases.atom
- **Research**：arXiv RSS（cs.AI/CL/LG，量大，建議搭配 HF Daily Papers 篩選）、Import AI、Interconnects
- **Apps**：Product Hunt Atom feed（避開 API 的商業條款）、hnrss.org

> 多數 feed 只有摘要（OpenAI、DeepMind、Google、HF、TechCrunch、Mistral、LangChain）。若 MCP 要提供全文，需要另外抓原文 HTML，並注意各站 ToS。OpenAI 和 HF blog 的 feed 是全歷史（1k+ items），要做增量去重。

### 用 API
- Hacker News Firebase API（免 auth、無限流）＋ Algolia search（10k req/hr/IP），用來做 AI 關鍵字搜尋
- HF Daily Papers `/api/daily_papers`、HF Hub `/api/models?sort=trendingScore`（帶 `HF_TOKEN`）
- OpenRouter `/api/v1/models`（新模型、價格演進）
- arXiv API（嚴守每 3 秒 1 req、單連線）
- LMArena：HF dataset `lmarena-ai/leaderboard-dataset` 的 `latest` parquet
- GitHub Search API（帶 token）做 trending 的近似

### 需要 scrape 或自架 RSSHub
- **Anthropic** news/engineering/research：沒有 RSS。可解析 sitemap.xml（news/research）加 HTML 列表頁，或用自架 RSSHub `/anthropic/*`
- **Meta AI blog**：官方回 400，用 RSSHub `/meta/ai/blog`（實際能不能用尚未驗證）
- **GitHub Trending**：scrape `github.com/trending`，或用 RSSHub（需 `GITHUB_ACCESS_TOKEN`）
- RSSHub 一律**自架**，不要依賴 rsshub.app

### 跳過或延後
- **Papers with Code**：已關閉，改用 HF Papers
- **X/Twitter API**：需付費 pay-per-use
- **Reddit**：`.json` 未授權 403、`.rss` 限流極嚴；要用就申請 OAuth app，並遵守 Data API Terms（商業用途需另簽約，禁止用於 AI 訓練）
- **Product Hunt API**：預設禁止商業用途，用 feed 替代
- **Microsoft AI blog**（`blogs.microsoft.com/ai/feed/`）：410，已失效
- **arena.ai 網站**：Cloudflare 擋，改用 HF dataset
