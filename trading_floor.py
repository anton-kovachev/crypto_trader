import asyncio
import os
from contextlib import AsyncExitStack
from pathlib import Path

from agents import add_trace_processor
from crypto_agents import CryptoCurrencyResearcher, CryptoCurrencyTrader
from dotenv import load_dotenv
from mcp_servers.crypto_currency_research_mcp_servers import (
    get_crypto_research_mcp_servers,
)
from mcp_servers.qdrant_utils import ensure_qdrant_docker
from tracers import LogTracer

load_dotenv(override=True)

TRADER_NAME = os.getenv("TRADER_NAME", "Max Kaiser")
RESEARCHER_NAME = os.getenv("RESEARCHER_NAME", "Guy Researcher")

RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "10"))


async def run_trade_every_n_minutes():
    add_trace_processor(LogTracer())
    while True:
        researcher = CryptoCurrencyResearcher(RESEARCHER_NAME)
        trader = CryptoCurrencyTrader(TRADER_NAME)

        ensure_qdrant_docker(str(Path(__file__).parent))
        async with AsyncExitStack() as stack:
            researcher_mcp_servers = [
                await stack.enter_async_context(server)
                for server in get_crypto_research_mcp_servers()
            ]

            researcher_tool = researcher.get_agent_as_tool(
                mcp_servers=researcher_mcp_servers
            )

            await trader.run_with_tools_async(tools=[researcher_tool])
        await asyncio.sleep(
            RUN_EVERY_N_MINUTES * 60
        )  # Wait for the specified interval before the next trade


if __name__ == "__main__":
    asyncio.run(run_trade_every_n_minutes())
