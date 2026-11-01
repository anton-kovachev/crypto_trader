import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from database import AccountsDatabase
from entities.account_log import AccountLog


class DatabaseLogTimestampTests(unittest.TestCase):
    def test_write_log_stores_an_explicit_utc_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "accounts.db"
            with AccountsDatabase(database_path) as database:
                database.write_log("test-account", "account", "created")

            with sqlite3.connect(database_path) as connection:
                timestamp = connection.execute(
                    "SELECT datetime FROM logs WHERE name = ?",
                    ("test-account",),
                ).fetchone()[0]

        self.assertRegex(timestamp, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
        parsed_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        self.assertEqual(parsed_timestamp.tzinfo, timezone.utc)

    def test_account_log_parses_legacy_naive_timestamp_as_utc(self) -> None:
        log = AccountLog.from_dict(
            {
                "name": "test-account",
                "type": "account",
                "message": "created",
                "datetime": "2026-10-30 08:06:55",
            }
        )

        self.assertEqual(
            log.timestamp,
            datetime(2026, 10, 30, 8, 6, 55, tzinfo=timezone.utc),
        )

    def test_account_log_parses_z_timestamp_as_utc(self) -> None:
        log = AccountLog.from_dict(
            {
                "name": "test-account",
                "type": "account",
                "message": "created",
                "datetime": "2026-10-30T08:06:55Z",
            }
        )

        self.assertEqual(
            log.timestamp,
            datetime(2026, 10, 30, 8, 6, 55, tzinfo=timezone.utc),
        )


if __name__ == "__main__":
    unittest.main()
