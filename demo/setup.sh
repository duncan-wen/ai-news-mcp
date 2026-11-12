#!/usr/bin/env bash
# Rebuilds the demo directory: an MCP config that runs the published package with its own
# store, so the recording never moves your own Checkpoints, then collects once so the
# recording starts from a full store instead of a one-minute first collection.
set -euo pipefail
cd "$(dirname "$0")/.."

DEMO_DIR="${DEMO_DIR:-/tmp/ai-news-demo}"
rm -rf "$DEMO_DIR"
mkdir -p "$DEMO_DIR/data"

cat > "$DEMO_DIR/mcp.json" <<JSON
{
  "mcpServers": {
    "ai-news": {
      "type": "stdio",
      "command": "uvx",
      "args": ["ai-news-mcp"],
      "env": {"XDG_DATA_HOME": "$DEMO_DIR/data"}
    }
  }
}
JSON

uv run python demo/collect.py "$DEMO_DIR/mcp.json"
