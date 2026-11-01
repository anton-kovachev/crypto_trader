import asyncio
import math
import os
from collections.abc import Awaitable, Callable

from dotenv import load_dotenv
from gradio.themes import Default
from output_models import AccountOutput
from redis_store import get_reporter_output, get_reporter_outputs
from ui import create_ui, css, js

load_dotenv(override=True)


def make_account_reporter(
    account_name: str,
) -> Callable[[], Awaitable[AccountOutput]]:
    async def report_account() -> AccountOutput:
        return await load_account(account_name)

    return report_account


async def load_account(account_name: str) -> AccountOutput:
    reporter_output = await asyncio.to_thread(get_reporter_output, account_name)
    if reporter_output is None:
        raise LookupError(f"No reporter output exists for account {account_name!r}")
    return reporter_output.account


async def main(refresh_every_n_seconds: float | None = None) -> None:
    is_lambda = bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
    if refresh_every_n_seconds is None and is_lambda:
        configured_interval = float(os.getenv("UI_REFRESH_EVERY_N_SECONDS", "30"))
        if not math.isfinite(configured_interval) or configured_interval < 0:
            raise ValueError("UI_REFRESH_EVERY_N_SECONDS must be finite and non-negative")
        refresh_every_n_seconds = configured_interval or None

    reporter_outputs = await asyncio.to_thread(get_reporter_outputs)
    account_reporters = [
        make_account_reporter(output.account.account_name)
        for output in reporter_outputs
    ]
    ui, _ = await create_ui(
        account_reporters,
        refresh_every_n_seconds=refresh_every_n_seconds,
    )

    ui.launch(
        theme=Default(
            primary_hue="violet", secondary_hue="purple", neutral_hue="slate"
        ),
        css=css,
        js=js,
        server_name="0.0.0.0" if is_lambda else None,
        server_port=int(os.getenv("PORT", "7860")),
        inbrowser=not is_lambda,
    )


if __name__ == "__main__":
    asyncio.run(main())
