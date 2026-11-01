import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from mcp_servers.qdrant_utils import ensure_qdrant_docker

load_dotenv(override=True)

RUN_EVERY_N_MINUTES = int(os.getenv("RUN_EVERY_N_MINUTES", "10"))


async def run_trade_every_n_minutes():
    from lambda_function import run_trading_workflow

    while True:
        ensure_qdrant_docker(str(Path(__file__).parent))
        await run_trading_workflow()
        await asyncio.sleep(
            RUN_EVERY_N_MINUTES * 60
        )  # Wait for the specified interval before the next trade


if __name__ == "__main__":
    asyncio.run(run_trade_every_n_minutes())
