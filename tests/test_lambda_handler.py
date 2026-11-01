import json
import asyncio
import os
import unittest
from unittest.mock import AsyncMock, Mock, patch

import lambda_function


class LambdaHandlerTests(unittest.TestCase):
    def test_reporting_workflow_uses_reporter_account_name(self) -> None:
        reporter_output = Mock(error_message="")
        with (
            patch.dict(os.environ, {"REPORTER_NAME": "Reporting Account"}),
            patch.object(lambda_function, "_ensure_trace_processor"),
            patch.object(lambda_function, "CryptoCurrencyReporter") as reporter_type,
            patch.object(lambda_function, "CryptoCurrencyResearcher"),
            patch.object(
                lambda_function,
                "generate_account_reports",
                new=AsyncMock(return_value=reporter_output),
            ),
            patch.object(lambda_function, "save_reporter_output") as save_report,
        ):
            result = asyncio.run(lambda_function.run_reporting_workflow())

        reporter_type.assert_called_once_with("Reporting Account")
        save_report.assert_called_once_with(reporter_output)
        self.assertIs(result, reporter_output)

    def test_sqs_message_dispatches_workflow_payload(self) -> None:
        message = {"workflow": "trading_floor"}
        with patch.object(lambda_function, "_run_workflow") as run_workflow:
            response = lambda_function.lambda_handler(
                {
                    "Records": [
                        {
                            "messageId": "message-1",
                            "body": json.dumps(message),
                        }
                    ]
                },
                None,
            )

        run_workflow.assert_called_once_with(
            "trading_floor",
            lambda_function.run_trading_workflow,
        )
        self.assertEqual(response, {"batchItemFailures": []})

    def test_failed_sqs_message_is_reported_for_retry(self) -> None:
        with self.assertLogs("lambda_function", level="ERROR"):
            response = lambda_function.lambda_handler(
                {
                    "Records": [
                        {
                            "messageId": "message-2",
                            "body": json.dumps({"workflow": "unknown"}),
                        }
                    ]
                },
                None,
            )

        self.assertEqual(
            response,
            {"batchItemFailures": [{"itemIdentifier": "message-2"}]},
        )


if __name__ == "__main__":
    unittest.main()
