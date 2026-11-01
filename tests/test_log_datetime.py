import os
import time
import unittest
from datetime import datetime, timezone

from ui.trader_ui import parse_log_datetime


class ParseLogDatetimeTests(unittest.TestCase):
    def test_naive_timestamp_is_interpreted_in_local_timezone(self) -> None:
        previous_timezone = os.environ.get("TZ")
        try:
            os.environ["TZ"] = "Etc/GMT-2"
            time.tzset()

            parsed = parse_log_datetime("2026-10-30T09:00:00")

            self.assertEqual(
                parsed,
                datetime(2026, 10, 30, 7, 0, tzinfo=timezone.utc),
            )
        finally:
            if previous_timezone is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = previous_timezone
            time.tzset()

    def test_z_and_offset_timestamps_normalize_to_utc(self) -> None:
        expected = datetime(2026, 10, 30, 7, 0, tzinfo=timezone.utc)

        self.assertEqual(parse_log_datetime("2026-10-30T07:00:00Z"), expected)
        self.assertEqual(
            parse_log_datetime("2026-10-30T09:00:00+02:00"),
            expected,
        )

    def test_datetime_input_is_supported(self) -> None:
        timestamp = datetime(2026, 10, 30, 9, 0, tzinfo=timezone.utc)

        self.assertEqual(parse_log_datetime(timestamp), timestamp)


if __name__ == "__main__":
    unittest.main()
