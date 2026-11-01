import uuid
from contextlib import AsyncExitStack
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
from tracers import make_trace_id
from .openrouter_client import create_openrouter_client
from .session_storage import get_session_db_path
from model_config import resolve_model_name

RESEARCHER_DB_PATH = get_session_db_path("crypto_researcher.db")


class CryptoCurrencyResearcher:

    def __init__(self, name: str, model_name: str | None = None):
        self.name: str = name
        self.model = OpenAIChatCompletionsModel(
            openai_client=create_openrouter_client(),
            model=resolve_model_name(model_name),
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
