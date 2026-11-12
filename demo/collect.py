"""Calls collect_now once through the server in the demo's MCP config (see setup.sh)."""

import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main(config_path: Path) -> None:
    server = json.loads(config_path.read_text(encoding="utf-8"))["mcpServers"]["ai-news"]
    params = StdioServerParameters(
        command=server["command"], args=server["args"], env=server["env"]
    )
    async with (
        stdio_client(params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        result = await session.call_tool("collect_now", {})
        text = "".join(getattr(block, "text", "") for block in result.content)
        print(text[:300])


asyncio.run(main(Path(sys.argv[1])))
