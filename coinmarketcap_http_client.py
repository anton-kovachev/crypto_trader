#!/usr/bin/env python3
"""Simple demo HTTP client that calls the CoinMarketCap MCP server over streamable HTTP.

Make sure the server is running (for example via `python3 debug_coinmarketcap_http.py`).
"""

import asyncio
import json
import os

from mcp.client.streamable_http import streamable_http_client
from mcp.client.session import ClientSession


async def main():
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    path = os.environ.get("MCP_PATH", "/mcp")
    url = f"http://{host}:{port}{path}"

    print(f"Connecting to MCP server at: {url}")
    async with streamable_http_client(url) as (read, write, *rest):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("calling get_cryptocurrency_data(symbol='BTC', limit=5)")
            result = await session.call_tool(
                "get_cryptocurrency_data", {"symbol": "BTC", "start": 1, "limit": 5}
            )
            print(json.dumps(result, default=str, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
