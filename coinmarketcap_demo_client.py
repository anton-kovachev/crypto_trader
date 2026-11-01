#!/usr/bin/env python3
"""Demo MCP stdio client for the CoinMarketCap data server.

Usage:
  python3 coinmarketcap_demo_client.py

This script spawns the server using the same `uv run -m` command you use
for local development, connects over stdio, lists tools, and calls a sample tool.
"""

import asyncio
import json
import pathlib

import mcp
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters

from pathlib import Path

CWD_PATH = Path(__file__).parent.resolve()


def _server_params() -> StdioServerParameters:
    return StdioServerParameters(
        command="python3",
        args=[
            "-m",
            "debugpy",
            "--listen",
            "5679",
            "--wait-for-client",
            "-m",
            "uv",
            "run",
            "-m",
            "mcp_servers.coinmarketcap_data.server",
        ],
        env=None,
        cwd=CWD_PATH,
    )


async def main():
    params = _server_params()
    async with stdio_client(params) as streams:
        async with mcp.ClientSession(*streams) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Available tools:", [t.name for t in tools.tools])

            print(
                "Calling get_current_cryptocurrency_data(start=1, limit=5, time_period='24h')..."
            )
            result = await session.call_tool(
                "get_current_cryptocurrency_data",
                {"start": 1, "limit": 5, "time_period": "24h"},
            )
            # print JSON-safe output
            print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
