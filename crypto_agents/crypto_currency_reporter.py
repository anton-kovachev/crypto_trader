import uuid
from contextlib import AsyncExitStack
from typing import Any

from agents import (
    Agent,
    GuardrailFunctionOutput,
    OpenAIChatCompletionsModel,
    OutputGuardrail,
    RunConfig,
    RunContextWrapper,
    Runner,
    RunResult,
    SessionSettings,
    SQLiteSession,
    ModelSettings,
    Tool,
    trace,
)
from agents.mcp import MCPServer
from .crypto_currency_validator import CryptoCurrencyValidator
from .openrouter_client import create_openrouter_client
from .session_storage import get_session_db_path
from instructions import reporter_instructions
from model_config import resolve_model_name
from mcp_servers import get_cryptocurrency_reporter_mcp_servers
from output_models import ReporterOutput
from tracers import make_trace_id

REPORTER_DB_PATH = get_session_db_path("cryptocurrency_reporter.db")


def _make_report_validation_guardrail(
    mcp_servers: list[MCPServer], tools: list[Tool]
) -> OutputGuardrail[None]:
    async def validate_report(
        _context: RunContextWrapper[None],
        _agent: Agent[Any],
        output: ReporterOutput,
    ) -> GuardrailFunctionOutput:
        del _context, _agent
        validator = CryptoCurrencyValidator(reporter_output=output)
        validation = await validator.run_with_tools_and_mcp_servers(
            mcp_servers=mcp_servers,
            tools=tools,
        )
        return GuardrailFunctionOutput(
            output_info=validation,
            tripwire_triggered=validation.validity_check_failed,
        )

    return OutputGuardrail(
        guardrail_function=validate_report,
        name="reporter-output-validation",
    )


class CryptoCurrencyReporter:

    def __init__(
        self,
        name: str,
        model_name: str | None = None,
        strategy: str | None = None,
    ):
        self.name: str = name
        self.model = OpenAIChatCompletionsModel(
            openai_client=create_openrouter_client(),
            model=resolve_model_name(model_name),
        )

        self.session = SQLiteSession(
            session_id=str(uuid.uuid4()), db_path=REPORTER_DB_PATH
        )
        self.instructions = (
            strategy if strategy is not None else reporter_instructions(name)
        )

    async def run_with_tools(
        self, task: str, tools: list[Tool] | None = None
    ) -> ReporterOutput:
        async with AsyncExitStack() as stack:
            mcp_servers: list[MCPServer] = [
                await stack.enter_async_context(server)
                for server in get_cryptocurrency_reporter_mcp_servers()
            ]
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
                output_type=ReporterOutput,
                # output_guardrails=[
                #     _make_report_validation_guardrail(mcp_servers, agent_tools)
                # ],
            )

            trace_name = f"{self.name}-reporter"
            trace_id = make_trace_id(f"{self.name.lower()}")
            with trace(trace_name, trace_id=trace_id):
                response: RunResult = await Runner.run(
                    agent,
                    input=task,
                    session=self.session,
                    max_turns=30,
                    run_config=RunConfig(session_settings=SessionSettings(limit=50)),
                )
                print(response.final_output)
            return ReporterOutput.model_validate(response.final_output)
