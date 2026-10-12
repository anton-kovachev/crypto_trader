import os
import uuid
from collections.abc import Coroutine
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

from agents import (
    Agent,
    ModelSettings,
    OpenAIChatCompletionsModel,
    RunConfig,
    Runner,
    RunResult,
    SessionSettings,
    SQLiteSession,
    Tool,
    trace,
)
from agents.mcp import MCPServer
from instructions import default_trader_stratergy, trade_message
from mcp_servers import (
    get_cryptocurrency_trader_mcp_servers,
)
from mcp_servers.uniswap import get_uniswap_trading_servers
from openai import AsyncOpenAI
from tracers import make_trace_id

TRADER_DB_PATH = Path(__file__).parent.parent / "sessions" / "cryptocurrency_trader.db"
TRADER_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
TRADER_DB_PATH.touch(exist_ok=True)


class CryptoCurrencyTrader:

    def __init__(
        self,
        name: str,
        strategy: str | None = None,
        model_name: str = "gpt-5-mini",
    ):
        self.name: str = name
        self.strategy: str = (
            strategy if strategy is not None else default_trader_stratergy(name)
        )
        self.model = OpenAIChatCompletionsModel(
            openai_client=AsyncOpenAI(
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url=os.getenv(
                    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
                ),
            ),
            model=model_name,
        )

        self.session = SQLiteSession(
            session_id=str(uuid.uuid4()), db_path=TRADER_DB_PATH
        )

    async def run_with_tools_async(
        self, tools: list[Tool] | None = None
    ) -> Coroutine[None, None, Any]:
        async with AsyncExitStack() as stack:
            mcp_servers: list[MCPServer] = [
                await stack.enter_async_context(server)
                for server in get_uniswap_trading_servers()
                + get_cryptocurrency_trader_mcp_servers()
            ]
            agent = Agent(
                name=self.name,
                model=self.model,
                tools=tools if tools is not None else [],
                mcp_servers=mcp_servers,
                instructions=self.strategy,
                model_settings=ModelSettings(max_tokens=30000),
            )

            trace_name = f"{self.name}-trader"
            trace_id = make_trace_id(f"{self.name.lower()}")
            with trace(trace_name, trace_id=trace_id):
                response: RunResult = await Runner.run(
                    agent,
                    input=trade_message(self.name, self.strategy),
                    session=self.session,
                    max_turns=20,
                    run_config=RunConfig(session_settings=SessionSettings(limit=10)),
                )
                print(response.final_output)
                return response.final_output
