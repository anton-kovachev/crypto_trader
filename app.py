import asyncio
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


async def main() -> None:
    reporter_outputs = await asyncio.to_thread(get_reporter_outputs)
    account_reporters = [
        make_account_reporter(output.account.account_name)
        for output in reporter_outputs
    ]
    ui, _ = await create_ui(account_reporters)

    ui.launch(
        theme=Default(
            primary_hue="violet", secondary_hue="purple", neutral_hue="slate"
        ),
        css=css,
        js=js,
        inbrowser=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
