import asyncio
import io
import sys
import types
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import AsyncMock, call, patch

from local_runner import (
    _run_repeatedly,
    create_parser,
    run_local_ui,
)


class LocalRunnerParserTests(unittest.TestCase):
    def test_each_command_accepts_a_run_interval(self) -> None:
        for command in ("trading", "reporting", "ui"):
            with self.subTest(command=command):
                args = create_parser().parse_args(
                    [command, "--run_every_n_seconds", "2.5"]
                )
                self.assertEqual(args.command, command)
                self.assertEqual(args.run_every_n_seconds, 2.5)

    def test_missing_zero_and_none_intervals_mean_one_shot(self) -> None:
        cases = (
            (["trading"], None),
            (["reporting", "--run-every-n-seconds", "0"], 0),
            (["ui", "--run-every-n-seconds", "none"], None),
        )
        for arguments, expected in cases:
            with self.subTest(arguments=arguments):
                args = create_parser().parse_args(arguments)
                self.assertEqual(args.run_every_n_seconds, expected)

    def test_negative_interval_is_rejected(self) -> None:
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                create_parser().parse_args(
                    ["trading", "--run-every-n-seconds", "-1"]
                )


class LocalRunnerAsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_one_shot_does_not_sleep(self) -> None:
        runner = AsyncMock()
        sleeper = AsyncMock()

        with patch("local_runner.asyncio.sleep", sleeper):
            await _run_repeatedly(runner, "Test workflow", 0)

        runner.assert_awaited_once()
        sleeper.assert_not_awaited()

    async def test_repeats_after_each_interval(self) -> None:
        runner = AsyncMock()
        sleeper = AsyncMock(side_effect=[None, asyncio.CancelledError()])

        with (
            patch("local_runner.asyncio.sleep", sleeper),
            redirect_stdout(io.StringIO()),
            self.assertRaises(asyncio.CancelledError),
        ):
            await _run_repeatedly(runner, "Test workflow", 2.5)

        self.assertEqual(runner.await_count, 2)
        sleeper.assert_has_awaits([call(2.5), call(2.5)])

    async def test_ui_interval_is_forwarded_as_refresh_cadence(self) -> None:
        fake_app = types.ModuleType("app")
        launch_ui = AsyncMock()
        setattr(fake_app, "main", launch_ui)

        with (
            patch("local_runner._load_local_environment"),
            patch.dict(sys.modules, {"app": fake_app}),
        ):
            await run_local_ui(15)

        launch_ui.assert_awaited_once_with(refresh_every_n_seconds=15)


if __name__ == "__main__":
    unittest.main()
