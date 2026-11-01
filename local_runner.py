import argparse
import asyncio
import math
import os
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent
LOCAL_QDRANT_HOSTS = {"localhost", "127.0.0.1", "::1"}


def parse_run_every_n_seconds(value: str) -> float | None:
    if value.strip().casefold() in {"none", "null"}:
        return None
    try:
        seconds = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a number, 0, or none") from error
    if not math.isfinite(seconds) or seconds < 0:
        raise argparse.ArgumentTypeError("must be a finite non-negative number")
    return seconds


def _normalize_run_every_n_seconds(
    seconds: float | None,
) -> float | None:
    if seconds is None or seconds == 0:
        return None
    if not math.isfinite(seconds) or seconds < 0:
        raise ValueError("run_every_n_seconds must be finite and non-negative")
    return seconds


async def _run_repeatedly(
    runner: Callable[[], Awaitable[Any]],
    workflow_name: str,
    run_every_n_seconds: float | None,
) -> None:
    interval = _normalize_run_every_n_seconds(run_every_n_seconds)
    while True:
        await runner()
        if interval is None:
            return
        print(
            f"{workflow_name} completed; next run in {interval:g} seconds. "
            "Press Ctrl+C to stop."
        )
        await asyncio.sleep(interval)


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


async def run_local_trading(
    run_every_n_seconds: float | None = None,
) -> None:
    _load_local_environment()
    _ensure_local_qdrant()

    from lambda_function import run_trading_workflow

    await _run_repeatedly(
        run_trading_workflow,
        "Trading workflow",
        run_every_n_seconds,
    )


async def run_local_reporting(
    run_every_n_seconds: float | None = None,
) -> None:
    _load_local_environment()
    _ensure_local_qdrant()

    from lambda_function import run_reporting_workflow

    async def run_once() -> None:
        reporter_output = await run_reporting_workflow()
        print(f"Report saved to Redis for {reporter_output.account.account_name}")
        if reporter_output.error_message:
            print(f"Report warning: {reporter_output.error_message}")

    await _run_repeatedly(
        run_once,
        "Reporting workflow",
        run_every_n_seconds,
    )


async def run_local_ui(
    run_every_n_seconds: float | None = None,
) -> None:
    _load_local_environment()

    from app import main as launch_ui

    await launch_ui(
        refresh_every_n_seconds=_normalize_run_every_n_seconds(
            run_every_n_seconds
        )
    )


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a crypto trader workflow or dashboard locally."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name, description in (
        ("trading", "Run the trading workflow."),
        ("reporting", "Generate and save account reports."),
        ("ui", "Launch the Gradio dashboard."),
    ):
        command = commands.add_parser(name, description=description)
        command.add_argument(
            "--run-every-n-seconds",
            "--run_every_n_seconds",
            dest="run_every_n_seconds",
            type=parse_run_every_n_seconds,
            default=None,
            help="Repeat after this many seconds; 0 or none runs once.",
        )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = create_parser().parse_args(argv)
    if args.command == "trading":
        asyncio.run(run_local_trading(args.run_every_n_seconds))
    elif args.command == "reporting":
        asyncio.run(run_local_reporting(args.run_every_n_seconds))
    else:
        asyncio.run(run_local_ui(args.run_every_n_seconds))


if __name__ == "__main__":
    main()
