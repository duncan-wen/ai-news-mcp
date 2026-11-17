# The server never calls an LLM; Claude does the reasoning

At collection time, Categories are assigned without an LLM: each Item gets its Source's default Categories, plus Categories added by keyword rules on the title and summary. The server does not summarise anything, does not classify in detail, and does not merge reports of the same event. The Claude client that calls the MCP tools does all of that at query time: it already reads every result, so asking another LLM to pre-process them would cost twice. This also means no API key is needed and running the server costs nothing, which matters for an open-source tool.

## Consequences

- Keyword rules will misclassify some Items. We accept this, because an Item can have several Categories and Claude can re-judge at query time.
- De-duplication only merges Items whose normalised URLs match, or that one Source lists again under a URL that differs in a known way: a `/YYYY/MM/DD` date segment on the Source's own site (TechCrunch moves an updated Item to a URL with the new date), or an OpenRouter variant (`:free`, `:batch`) of a model. Different reports of the same event are kept as separate Items for Claude to group.
- To keep that grouping cheap, the tools let a client ask for less text (`summary_length`), so it can read a week of Items by title.

## Considered Options

- **Group reports of one event by title similarity, without an LLM**: rejected. On the Items published 2026-11-10 to 2026-11-16, grouping titles with word overlap (Jaccard ≥ 0.5) within 48 hours turned 309 Items into 293 groups. Different Sources word one event's headline too differently: the ten or so Items about one model launch mostly stayed apart, and a lower threshold starts joining unrelated launches with similar names. Grouping that works needs embeddings or an LLM.

---

## 中文

### Server 不呼叫 LLM，推理交給 Claude

收集時分類不用 LLM：每則 Item 先拿到所屬 Source 的預設 Category，再用標題和摘要的關鍵字規則補上其他 Category。Server 不做摘要、不做細部分類，也不合併同一事件的不同報導。這些都由呼叫 MCP tool 的 Claude 在查詢時處理：反正它本來就會讀每一筆結果，再讓另一個 LLM 先處理一次等於付兩次錢。這也代表不需要 API key、執行 server 不花錢，這對開源工具很重要。

### 影響

- 關鍵字規則會把一些 Item 分錯類。我們接受這一點，因為一則 Item 可以有多個 Category，Claude 在查詢時也能重新判斷。
- 去重複只合併正規化後網址相同的 Item，或同一個 Source 換了已知差異的網址重新列出的 Item：Source 自家網站上路徑只差一段 `/YYYY/MM/DD` 日期（TechCrunch 更新文章後會把它搬到帶新日期的網址），或 OpenRouter 模型的變體（`:free`、`:batch`）。同一事件的不同報導會保留成不同的 Item，交給 Claude 歸納。
- 為了讓歸納便宜，tool 讓 client 可以要求少一點文字（`summary_length`），只看標題就能讀完一週的 Item。

### 考慮過的選項

- **不用 LLM，靠標題相似度把同一事件的報導分成一群**：不採用。用 2026-11-10 到 2026-11-16 發布的 Item 試算，48 小時內標題字詞重疊（Jaccard ≥ 0.5）就算同一群，309 則只併成 293 群。不同 Source 對同一事件的標題寫法差太多：同一個模型發布的十則左右報導大多沒有併在一起，門檻再調低又會把名字相近、但無關的發布併在一起。要分得好，得用 embedding 或 LLM。
