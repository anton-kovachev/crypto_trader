import asyncio
from contextlib import AsyncExitStack
from pathlib import Path

import gradio as gr
from agents import OutputGuardrailTripwireTriggered
from crypto_agents import CryptoCurrencyReporter, CryptoCurrencyResearcher
from dotenv import load_dotenv
from mcp_servers import get_crypto_research_mcp_servers
from mcp_servers.qdrant_utils import ensure_qdrant_docker
from mcp_servers.uniswap import get_uniswap_trading_servers
from output_models import AccountOutput, ReporterOutput
from services import get_historical_listings
from ui import create_ui, css, js
from agents import add_trace_processor
from tracers import LogTracer

load_dotenv(override=True)


async def run_reporter(
    reporter: CryptoCurrencyReporter, researcher: CryptoCurrencyResearcher, task: str
) -> ReporterOutput:
    async with AsyncExitStack() as stack:
        researcher_mcp_servers = [
            await stack.enter_async_context(server)
            for server in get_crypto_research_mcp_servers()
        ]

        reporter_output = await reporter.run_with_tools(
            task,
            tools=[researcher.get_agent_as_tool(mcp_servers=researcher_mcp_servers)],
        )
        return reporter_output


async def generate_account_reports(
    reporter: CryptoCurrencyReporter, researcher: CryptoCurrencyResearcher
) -> ReporterOutput:
    task = "Generate report for the holdings of all accounts"
    last_guardrail_error: OutputGuardrailTripwireTriggered | None = None

    for attempt in range(1, 4):
        if last_guardrail_error is not None:
            validation = last_guardrail_error.guardrail_result.output.output_info
            failure_reasons = getattr(validation, "failure_reasons", [])
            task = (
                f"Retry {attempt - 1} of 2: generate report for the holdings of all "
                "accounts. "
                "The previous report failed validation for these reasons: "
                f"{'; '.join(failure_reasons)}. Correct the report and verify it."
            )

        try:
            return await run_reporter(reporter, researcher, task)
        except OutputGuardrailTripwireTriggered as error:
            last_guardrail_error = error

    if last_guardrail_error is None:
        raise RuntimeError(
            "Report generation ended without a result or validation error"
        )

    invalid_report = ReporterOutput.model_validate(
        last_guardrail_error.guardrail_result.agent_output
    )
    validation = last_guardrail_error.guardrail_result.output.output_info
    failure_reasons = getattr(validation, "failure_reasons", [])
    error_message = (
        "Report validation failed after 3 attempts. "
        + (
            "Validation issues: " + "; ".join(failure_reasons)
            if failure_reasons
            else "The validator rejected the report without providing specific reasons."
        )
    )
    if invalid_report.error_message:
        error_message = f"{invalid_report.error_message} {error_message}"
    return invalid_report.model_copy(update={"error_message": error_message})


async def generate_account_output_for_ui(
    reporter: CryptoCurrencyReporter, researcher: CryptoCurrencyResearcher
) -> AccountOutput:
    reporter_output = await generate_account_reports(reporter, researcher)
    if reporter_output.error_message:
        print(f"Account report validation error: {reporter_output.error_message}")
    return reporter_output.account


async def run_researcher(researcher: CryptoCurrencyResearcher, task: str):
    await researcher.run_agent_with_mcp_servers(task)


async def main():
    researcher = CryptoCurrencyResearcher(name="Edd Researcher")
    reporter = CryptoCurrencyReporter(name="Max Kaiser")

    ensure_qdrant_docker(str(Path(__file__).resolve().parent.parent))

    ui, trader_views = await create_ui(
        [lambda: generate_account_output_for_ui(reporter, researcher)]
    )

    add_trace_processor(LogTracer())
    try:
        ui.launch(
            theme=gr.themes.Default(primary_hue="sky"), css=css, js=js, inbrowser=True
        )
    except ValueError as e:
        # Gradio sometimes raises a ValueError when localhost is not accessible.
        print(f"Gradio launch ValueError: {e}. Launching with share=True.")
        ui.launch(
            theme=gr.themes.Default(primary_hue="sky"),
            css=css,
            js=js,
            inbrowser=True,
            share=True,
        )


if __name__ == "__main__":
    asyncio.run(main())
