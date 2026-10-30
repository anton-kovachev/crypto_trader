import argparse
import asyncio
import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from output_models import ReporterOutput

PROJECT_DIR = Path(__file__).resolve().parent
LOCAL_QDRANT_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _load_local_environment() -> None:
    load_dotenv(override=True)
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        raise RuntimeError("local_runner.py cannot run inside AWS Lambda")


def _ensure_local_qdrant() -> None:
    qdrant_url = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
    if urlparse(qdrant_url).hostname not in LOCAL_QDRANT_HOSTS:
        return

    from mcp_servers.qdrant_utils import ensure_qdrant_docker

    ensure_qdrant_docker(str(PROJECT_DIR))


async def run_local_trading() -> None:
    _load_local_environment()
    _ensure_local_qdrant()

    from lambda_function import run_trading_workflow

    await run_trading_workflow()


async def run_local_reporting() -> ReporterOutput:
    _load_local_environment()
    _ensure_local_qdrant()

    from lambda_function import run_reporting_workflow

    reporter_output = await run_reporting_workflow()
    print(f"Report saved to Redis for {reporter_output.account.account_name}")
    if reporter_output.error_message:
        print(f"Report warning: {reporter_output.error_message}")
    return reporter_output


async def run_local_ui() -> None:
    _load_local_environment()

    from app import main as launch_ui

    await launch_ui()


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a crypto trader workflow or dashboard locally."
    )
    parser.add_argument(
        "command",
        choices=("trading", "reporting", "ui"),
        help="Run one trading cycle, generate reports, or launch the Gradio UI.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    command = create_parser().parse_args(argv).command
    if command == "trading":
        asyncio.run(run_local_trading())
    elif command == "reporting":
        asyncio.run(run_local_reporting())
    else:
        asyncio.run(run_local_ui())


if __name__ == "__main__":
    main()
