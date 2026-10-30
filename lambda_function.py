import asyncio
import os
from collections.abc import Callable, Coroutine, Mapping
from contextlib import AsyncExitStack
from typing import Any, TypeVar

from agents import (
    OutputGuardrailTripwireTriggered,
    Tool,
    add_trace_processor,
)
from agents.mcp import MCPServer
from crypto_agents import CryptoCurrencyReporter, CryptoCurrencyResearcher
from database import AccountsDatabase
from mcp_servers import get_crypto_research_mcp_servers
from output_models import ReporterOutput
from redis_store import save_reporter_output
from tracers import LogTracer

_trace_processor_registered = False
WorkflowResult = TypeVar("WorkflowResult")


async def run_reporter(
    reporter: CryptoCurrencyReporter,
    researcher: CryptoCurrencyResearcher,
    task: str,
) -> ReporterOutput:
    async with AsyncExitStack() as stack:
        researcher_mcp_servers: list[MCPServer] = [
            await stack.enter_async_context(server)
            for server in get_crypto_research_mcp_servers()
        ]
        researcher_tool: Tool = researcher.get_agent_as_tool(
            mcp_servers=researcher_mcp_servers
        )
        return await reporter.run_with_tools(
            task,
            tools=[researcher_tool],
        )


async def generate_account_reports(
    reporter: CryptoCurrencyReporter,
    researcher: CryptoCurrencyResearcher,
) -> ReporterOutput:
    task = f"Generate report for the holdings of account name: ```{reporter.name}```"
    last_guardrail_error: OutputGuardrailTripwireTriggered | None = None

    for attempt in range(1, 4):
        if last_guardrail_error is not None:
            validation = last_guardrail_error.guardrail_result.output.output_info
            failure_reasons = getattr(validation, "failure_reasons", [])
            task = (
                f"Retry {attempt - 1} of 2: generate report for the holdings for account name ```{reporter.name}```"
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
    error_message = "Report validation failed after 3 attempts. " + (
        "Validation issues: " + "; ".join(failure_reasons)
        if failure_reasons
        else "The validator rejected the report without providing specific reasons."
    )
    if invalid_report.error_message:
        error_message = f"{invalid_report.error_message} {error_message}"
    return invalid_report.model_copy(update={"error_message": error_message})


def _ensure_trace_processor() -> None:
    global _trace_processor_registered
    if not _trace_processor_registered:
        add_trace_processor(LogTracer())
        _trace_processor_registered = True


def _validate_lambda_configuration(workflow: str) -> None:
    if not os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return

    required_variables = ["ACCOUNT_DB_S3_BUCKET", "QDRANT_URL"]
    redis_mode = os.getenv("REDIS_MODE", "elasticache").strip().lower()
    if workflow == "reporter":
        if redis_mode == "url":
            required_variables.append("REDIS_URL")
        elif redis_mode == "elasticache":
            required_variables.extend(
                [
                    "ELASTICACHE_HOST",
                    "ELASTICACHE_USERNAME",
                    "ELASTICACHE_RESOURCE_ID",
                ]
            )
        else:
            raise ValueError("REDIS_MODE must be 'url' or 'elasticache'")

    missing_variables = [name for name in required_variables if not os.getenv(name)]
    if workflow == "reporter" and redis_mode == "elasticache":
        if not (os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")):
            missing_variables.append("AWS_REGION")
    if missing_variables:
        raise RuntimeError(
            "Missing required Lambda environment variables: "
            + ", ".join(missing_variables)
        )


def _run_workflow(
    workflow: str,
    runner: Callable[[], Coroutine[Any, Any, WorkflowResult]],
) -> WorkflowResult:
    _validate_lambda_configuration(workflow)
    is_lambda = bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
    if is_lambda:
        AccountsDatabase.load_from_s3()
        with AccountsDatabase():
            pass

    try:
        return asyncio.run(runner())
    finally:
        if is_lambda:
            AccountsDatabase.save_to_s3()


async def run_reporting_workflow() -> ReporterOutput:
    _ensure_trace_processor()
    reporter = CryptoCurrencyReporter(os.getenv("TRADER_NAME", "Max Kaiser"))
    researcher = CryptoCurrencyResearcher(
        os.getenv("RESEARCHER_NAME", "Edd Researcher")
    )

    reporter_output = await generate_account_reports(reporter, researcher)

    if not reporter_output.error_message:
        save_reporter_output(reporter_output)

    return reporter_output


async def run_trading_workflow() -> Any:
    from crypto_agents import CryptoCurrencyTrader

    _ensure_trace_processor()
    researcher = CryptoCurrencyResearcher(
        os.getenv("RESEARCHER_NAME", "Guy Researcher")
    )
    trader = CryptoCurrencyTrader(os.getenv("TRADER_NAME", "Max Kaiser"))

    async with AsyncExitStack() as stack:
        researcher_mcp_servers: list[MCPServer] = [
            await stack.enter_async_context(server)
            for server in get_crypto_research_mcp_servers()
        ]
        researcher_tool = researcher.get_agent_as_tool(
            mcp_servers=researcher_mcp_servers
        )
        return await trader.run_with_tools_async(
            tools=[researcher_tool],
        )


def lambda_handler(event: Mapping[str, Any], context: Any) -> dict[str, Any]:
    del context
    if not isinstance(event, Mapping):
        raise TypeError("Lambda event must be a JSON object")

    workflow = event.get("workflow")
    if workflow == "trading_floor":
        _run_workflow(workflow, run_trading_workflow)
        return {"workflow": workflow, "status": "completed"}
    if workflow == "reporter":
        reporter_output = _run_workflow(workflow, run_reporting_workflow)
        return {
            "workflow": workflow,
            "status": "completed",
            "account_name": reporter_output.account.account_name,
            "error_message": reporter_output.error_message,
        }
    raise ValueError("Unsupported workflow; expected 'trading_floor' or 'reporter'")
