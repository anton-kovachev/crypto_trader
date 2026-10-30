import uuid
from contextlib import AsyncExitStack
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
from instructions import account_verifier_instructions
from mcp_servers import get_cryptocurrency_reporter_mcp_servers
from output_models import AccountValidationOutput, ReporterOutput
from tracers import make_trace_id
from .bedrock_client import create_bedrock_client
from .session_storage import get_session_db_path
from model_config import resolve_model_name

VALIDATOR_DB_PATH = get_session_db_path("cryptocurrency_validator.db")


class CryptoCurrencyValidator:
    def __init__(
        self,
        reporter_output: ReporterOutput,
        name: str = "CryptoCurrencyValidator",
        model_name: str | None = None,
        strategy: str | None = None,
    ):
        self.name = name
        self.reporter_output = reporter_output
        self.model = OpenAIChatCompletionsModel(
            openai_client=create_bedrock_client(),
            model=resolve_model_name(model_name),
        )
        self.session = SQLiteSession(
            session_id=str(uuid.uuid4()), db_path=VALIDATOR_DB_PATH
        )
        self.instructions = (
            strategy if strategy is not None else account_verifier_instructions()
        )

    async def run_with_tools(
        self, tools: list[Tool] | None = None
    ) -> AccountValidationOutput:
        async with AsyncExitStack() as stack:
            mcp_servers: list[MCPServer] = [
                await stack.enter_async_context(server)
                for server in get_cryptocurrency_reporter_mcp_servers()
            ]
            return await self.run_with_tools_and_mcp_servers(
                mcp_servers=mcp_servers,
                tools=tools,
            )

    async def run_with_tools_and_mcp_servers(
        self,
        mcp_servers: list[MCPServer],
        tools: list[Tool] | None = None,
    ) -> AccountValidationOutput:
        agent_tools = tools if tools is not None else []
        agent = Agent(
            name=self.name,
            model=self.model,
            tools=agent_tools,
            mcp_servers=mcp_servers,
            instructions=self.instructions,
            model_settings=ModelSettings(
                tool_choice=(
                    "CryptoCurrencyResearcher"
                    if "CryptoCurrencyResearcher"
                    in [tool.name for tool in agent_tools]
                    else "required"
                )
            ),
            output_type=AccountValidationOutput,
        )

        trace_name = f"{self.name}-validator"
        trace_id = make_trace_id(f"{self.name.lower()}")
        with trace(trace_name, trace_id=trace_id):
            response: RunResult = await Runner.run(
                agent,
                input=self.reporter_output.model_dump_json(),
                session=self.session,
                max_turns=30,
                run_config=RunConfig(session_settings=SessionSettings(limit=50)),
            )
            print(response.final_output)
        return AccountValidationOutput.model_validate(response.final_output)
