import asyncio
import json
import logging
import os
from collections.abc import Callable, Coroutine, Mapping
from contextlib import AsyncExitStack
from typing import Any, TypeVar

import boto3
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
LOGGER = logging.getLogger(__name__)

_BACKEND_SECRET_KEYS = {
    "OPENROUTER_API_KEY",
    "COINMARKETCAP_API_KEY",
    "CHAIN_RPC_URL",
    "USER_PRIVATE_KEY",
    "RELAYER_PRIVATE_KEY",
    "UNISWAP_API_KEY",
    "QDRANT_API_KEY",
    "PUSHOVER_API_TOKEN",
    "PUSHOVER_USER_KEY",
    "OPENAI_API_KEY",
}
_REQUIRED_BACKEND_SECRET_KEYS = {
    "OPENROUTER_API_KEY",
    "COINMARKETCAP_API_KEY",
    "CHAIN_RPC_URL",
    "USER_PRIVATE_KEY",
    "RELAYER_PRIVATE_KEY",
    "UNISWAP_API_KEY",
}


def _load_backend_secrets() -> None:
    if not os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return

    secret_arn = os.getenv("BACKEND_SECRETS_ARN")
    if not secret_arn:
        raise RuntimeError("BACKEND_SECRETS_ARN must be set in AWS Lambda")

    response = boto3.client("secretsmanager").get_secret_value(SecretId=secret_arn)
    secret_string = response.get("SecretString")
    if not isinstance(secret_string, str):
        raise RuntimeError("Backend Secrets Manager secret must contain SecretString")

    secret_values = json.loads(secret_string)
    if not isinstance(secret_values, dict):
        raise TypeError("Backend secret must be a JSON object of environment values")

    unknown_keys = set(secret_values) - _BACKEND_SECRET_KEYS
    if unknown_keys:
        raise ValueError(
            "Backend secret contains unsupported keys: "
            + ", ".join(sorted(unknown_keys))
        )

    invalid_values = [
        key for key, value in secret_values.items() if not isinstance(value, str)
    ]
    if invalid_values:
        raise TypeError(
            "Backend secret values must be strings: "
            + ", ".join(sorted(invalid_values))
        )

    missing_keys = _REQUIRED_BACKEND_SECRET_KEYS - secret_values.keys()
    if missing_keys:
        raise RuntimeError(
            "Backend secret is missing required values: "
            + ", ".join(sorted(missing_keys))
        )

    os.environ.update(secret_values)


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

    required_variables = [
        "ACCOUNT_DB_S3_BUCKET",
        "BACKEND_SECRETS_ARN",
        "QDRANT_URL",
        "UV_EXECUTABLE",
    ]
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
        _load_backend_secrets()
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
    reporter = CryptoCurrencyReporter(os.getenv("REPORTER_NAME", "Max Kaiser"))
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

    if "Records" in event:
        records = event["Records"]
        if not isinstance(records, list):
            raise TypeError("SQS Records must be a list")
        failed_records: list[dict[str, str]] = []
        for record in records:
            if not isinstance(record, Mapping):
                raise TypeError("Each SQS record must be a JSON object")
            message_id = record.get("messageId")
            if not isinstance(message_id, str) or not message_id:
                raise ValueError("Each SQS record must include a messageId")
            try:
                message_body = json.loads(record["body"])
                if not isinstance(message_body, Mapping):
                    raise TypeError("SQS message body must decode to a JSON object")
                _dispatch_workflow(message_body)
            except Exception:
                LOGGER.exception("Failed to process SQS message %s", message_id)
                failed_records.append({"itemIdentifier": message_id})
        return {"batchItemFailures": failed_records}

    return _dispatch_workflow(event)


def _dispatch_workflow(event: Mapping[str, Any]) -> dict[str, Any]:
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
