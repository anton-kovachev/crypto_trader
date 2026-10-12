import os
import uuid
from contextlib import AsyncExitStack
from pathlib import Path

from agents import (
    Agent,
    FunctionTool,
    ModelSettings,
    OpenAIChatCompletionsModel,
    RunConfig,
    Runner,
    SessionSettings,
    SQLiteSession,
    trace,
)
from agents.mcp import MCPServer
from instructions import researcher_instructions, researcher_tool_description
from mcp_servers import (
    get_crypto_research_mcp_servers,
)
from openai import AsyncOpenAI
from tracers import make_trace_id

RESEARCHER_DB_PATH = Path(__file__).parent.parent / "sessions" / "crypto_researcher.db"
RESEARCHER_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
RESEARCHER_DB_PATH.touch(exist_ok=True)


class CryptoCurrencyResearcher:

    def __init__(self, name: str, model_name: str = "gpt-5-mini"):
        self.name: str = name
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
            session_id=str(uuid.uuid4()), db_path=RESEARCHER_DB_PATH
        )

    def get_agent(self, mcp_servers: list[MCPServer]):
        # Prefer a MCP server labeled 'qdrant' by asking the model to choose that server

        return Agent(
            name=self.name,
            instructions=researcher_instructions(),
            model=self.model,
            mcp_servers=mcp_servers,
            model_settings=ModelSettings(max_tokens=30000),
        )

    def get_agent_as_tool(self, mcp_servers: list[MCPServer]) -> FunctionTool:
        agent = self.get_agent(mcp_servers)
        return agent.as_tool(
            tool_name="CryptoCurrencyResearcher",
            tool_description=researcher_tool_description(),
        )

    async def run_agent_with_mcp_servers(self, task: str):
        async with AsyncExitStack() as stack:
            researcher_servers = [
                await stack.enter_async_context(server)
                for server in get_crypto_research_mcp_servers()
            ]

            agent = self.get_agent(researcher_servers)
            trace_name = f"{self.name}-researcher"
            trace_id = make_trace_id(f"{self.name.lower()}")
            with trace(trace_name, trace_id=trace_id):
                response = await Runner.run(
                    agent,
                    session=self.session,
                    run_config=RunConfig(session_settings=SessionSettings(limit=10)),
                    input=task,
                    max_turns=10,
                )

                print(response.final_output)
