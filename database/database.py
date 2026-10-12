import sqlite3
from pathlib import Path
from typing import Any
import logging
import json
from datetime import datetime
from utils.json_utils import DateTimeEncoder, DateTimeDecoder

logging.basicConfig(level=logging.INFO)


class AccountsDatabase:
    DB_PATH = Path(__file__).parent.resolve() / "accounts.db"

    def __init__(self, db_name=DB_PATH):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_accounts_table()
        self.create_logs_table()

    def create_accounts_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_name TEXT NOT NULL UNIQUE,
                account_state TEXT NOT NULL
            )
        """)
        self.connection.commit()

    def create_logs_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                datetime TEXT NOT NULL,
                type TEXT NOT NULL,
                message TEXT NOT NULL
            )
        """)
        self.connection.commit()

    def get_account_name(self) -> list[str]:
        self.cursor.execute("""
            SELECT account_name FROM accounts
            """)
        rows = self.cursor.fetchall()
        return [row[0] for row in rows]

    def get_account(self, account) -> dict[str, Any] | None:
        self.cursor.execute(
            """
            SELECT * FROM accounts WHERE account_name = ?
            """,
            (account,),
        )
        row = self.cursor.fetchone()
        if row is None:
            return None

        # Load account_state using DateTimeDecoder to convert ISO datetime strings back to datetimes
        account_state = json.loads(row[2], cls=DateTimeDecoder)

        # Stored JSON contains the account_state dict; merge top-level fields so callers can do Account(**data)
        if isinstance(account_state, dict):
            account_state["id"] = row[0]
            account_state["account_name"] = row[1]
            return account_state

        return {
            "id": row[0],
            "account_name": row[1],
            "account_state": account_state,
        }

    def add_account(self, name: str, account_dict: dict[str, Any]):
        self.cursor.execute(
            """
            INSERT INTO accounts (account_name, account_state)
            VALUES (?, ?)
            ON CONFLICT(account_name) DO UPDATE SET account_state=excluded.account_state
        """,
            (name, json.dumps(account_dict, cls=DateTimeEncoder)),
        )
        self.connection.commit()

    def update_account(self, account_name: str, account_state: dict[str, Any]):
        self.cursor.execute(
            """
            UPDATE accounts SET account_state = ? WHERE account_name = ?
            """,
            (json.dumps(account_state, cls=DateTimeEncoder), account_name),
        )
        self.connection.commit()

    def reset_account(self, account_name: str):
        self.cursor.execute(
            """
            UPDATE accounts SET account_state = '{}' WHERE account_name = ?
            """,
            (account_name,),
        )
        self.connection.commit()

    def reset_all_accounts(self):
        self.cursor.execute("""
            UPDATE accounts SET account_state = '{}'
            """)
        self.connection.commit()

    def delete_account(self, account_name: str):
        self.cursor.execute(
            """
            DELETE FROM accounts WHERE account_name = ?
            """,
            (account_name,),
        )
        self.connection.commit()

    def delete_all_accounts(self):
        self.cursor.execute("""
            TRUNCATE TABLE accounts
            """)
        self.connection.commit()

    def write_log(self, name: str, type: str, message: str):
        self.cursor.execute(
            """
            INSERT INTO logs (name, datetime, type, message)
            VALUES (?, datetime('now'), ?, ?)
            """,
            (name, type, message),
        )
        self.connection.commit()

    def read_logs(self, name: str, last_n=10) -> list[dict[str, Any]]:
        self.cursor.execute(
            """
            SELECT * FROM logs WHERE name = ? ORDER BY datetime DESC LIMIT ?
            """,
            (name, last_n),
        )
        rows = self.cursor.fetchall()
        return [
            {
                "id": row[0],
                "name": row[1],
                "datetime": row[2],
                "type": row[3],
                "message": row[4],
            }
            for row in rows
        ]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if exc_type is not None:
                # An exception occurred inside the with-block: rollback
                try:
                    self.connection.rollback()
                except Exception:
                    logging.error("Failed to rollback transaction", exc_info=True)
                    pass
            else:
                # No exception: commit any pending transaction
                try:
                    self.connection.commit()
                except Exception:
                    logging.error("Failed to commit transaction", exc_info=True)
                    pass
        finally:
            # Always try to close cursor and connection
            try:
                self.cursor.close()
            except Exception:
                logging.error("Failed to close cursor", exc_info=True)
                pass
            try:
                self.connection.close()
            except Exception:
                logging.error("Failed to close connection", exc_info=True)
                pass
        # Do not suppress exceptions
        return False


if __name__ == "__main__":
    pass
    # Short usage example showing context-manager support
    # This will create `accounts.db` next to this file.
    # with AccountsDatabase() as db:
    # add a test account
    # db.add_account("alice", {"balance": 100.0})
    # retrieve and print the account row (id, account, account_state)
    # print(db.get_account("alice"))
