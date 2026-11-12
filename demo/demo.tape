# README demo: Claude Code asks what's new, searches, then reads an Item's full text.
# Record with demo/record.sh, which rebuilds /tmp/ai-news-demo first.

# record.sh turns the mp4 into the GIF: vhs rendering both runs past ten minutes.
Output demo/out/demo.mp4

Set Shell "bash"
Set FontFamily "WenQuanYi Zen Hei Mono"
Set FontSize 15
Set Width 1280
Set Height 800
Set Padding 12
Set Framerate 20
Set TypingSpeed 40ms

# whats_new can return more than Claude Code's default MCP output limit, which saves it to a
# file that Claude then reads with Bash: an approval prompt that eats the next question and
# a path that shows the home directory. A higher limit and no Bash keep to the three tools.
Hide
Type "cd /tmp/ai-news-demo && clear && MAX_MCP_OUTPUT_TOKENS=100000 claude --strict-mcp-config --mcp-config mcp.json --setting-sources project --permission-mode default --allowedTools mcp__ai-news --disallowedTools Bash --append-system-prompt '用繁體中文回答。'" Enter
Sleep 4s
# A new directory asks for folder trust, defaulting to "No, exit": pick "Yes". Once the
# folder is trusted there is no prompt, and Down then Enter on an empty input does nothing.
Down
Enter
Wait+Screen@30s /Claude Code v/
Sleep 1s
Show

Sleep 1s
Type "從上次看過之後，Models 和 Engineering 有什麼新的？各挑三則，一則一行" Sleep 400ms Enter
# Fixed waits: vhs misses footer text such as "esc to interrupt" now and then, and an
# answer's own text scrolls away. Answers took 9-25 s in test takes.
Sleep 32s

Type "找最近一週關於 MCP 的 Engineering 文章，列出標題和來源" Sleep 400ms Enter
Sleep 35s

Type "讀第一篇的全文，用三句話摘要" Sleep 400ms Enter
Sleep 30s
