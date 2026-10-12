import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from config import INITIAL_USDC_AMOUNT, USD_TOKEN_ADDRESS, USD_TOKEN_SYMBOL
from database import AccountsDatabase
from utils.json_utils import DateTimeEncoder

from .account_log import AccountLog


@dataclass
class AccountTransaction:
    token_out_symbol: str
    token_out_address: str
    token_out_amount: float
    token_in_symbol: str
    token_in_address: str
    token_in_amount: int
    executed_at: datetime
    blockchain_transaction: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AccountTransaction":
        return cls(
            token_out_symbol=data["token_out_symbol"],
            token_out_address=data["token_out_address"],
            token_out_amount=data["token_out_amount"],
            token_in_symbol=data["token_in_symbol"],
            token_in_address=data["token_in_address"],
            token_in_amount=data["token_in_amount"],
            executed_at=data["executed_at"],
            blockchain_transaction=data["blockchain_transaction"],
        )

    def __str__(self) -> str:
        return (
            f"AccountTransaction(token_out_symbol={self.token_out_symbol}, "
            f"token_out_address={self.token_out_address}, "
            f"token_out_amount={self.token_out_amount}, "
            f"token_in_symbol={self.token_in_symbol}, "
            f"token_in_address={self.token_in_address}, "
            f"token_in_amount={self.token_in_amount}, "
            f"executed_at={self.executed_at}, "
            f"blockchain_transaction={json.dumps(self.blockchain_transaction, cls=DateTimeEncoder)})"
        )


@dataclass
class AccountHolding:
    token_symbol: str
    token_address: str
    amount: int
    last_updated_at: datetime
    buy_transactions: list[AccountTransaction]
    sell_transactions: list[AccountTransaction]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AccountHolding":
        return cls(
            token_symbol=data["token_symbol"],
            token_address=data["token_address"],
            amount=data["amount"],
            last_updated_at=data["last_updated_at"],
            buy_transactions=[
                AccountTransaction.from_dict(t)
                for t in data.get("buy_transactions", [])
            ],
            sell_transactions=[
                AccountTransaction.from_dict(t)
                for t in data.get("sell_transactions", [])
            ],
        )

    def __str__(self) -> str:
        return (
            f"AccountHolding(token_symbol={self.token_symbol}, "
            f"token_address={self.token_address}, "
            f"amount={self.amount}, "
            f"last_updated_at={self.last_updated_at}, "
            f"buy_transactions={[str(t) for t in self.buy_transactions]}, "
            f"sell_transactions={[str(t) for t in self.sell_transactions]})"
        )


@dataclass
class Account:
    id: int
    account_name: str
    last_updated_at: datetime
    holdings: list[AccountHolding]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Account":
        return cls(
            id=data["id"],
            account_name=data["account_name"],
            last_updated_at=data["last_updated_at"],
            holdings=[AccountHolding.from_dict(h) for h in data.get("holdings", [])],
        )

    @classmethod
    def initial_account(cls, account_name: str) -> "Account":
        return cls(
            id=0,
            account_name=account_name,
            last_updated_at=datetime.now(),
            holdings=[
                AccountHolding(
                    token_symbol=USD_TOKEN_SYMBOL,
                    token_address=USD_TOKEN_ADDRESS,
                    amount=INITIAL_USDC_AMOUNT,
                    last_updated_at=datetime.now(),
                    buy_transactions=[],
                    sell_transactions=[],
                )
            ],
        )

    @classmethod
    def create_account(cls, account_name: str) -> "Account":
        with AccountsDatabase() as db:
            account = db.get_account(account_name)
            if account is not None:
                raise ValueError(f"Account with name {account_name} already exists.")

            initial_account = cls.initial_account(account_name)
            db.add_account(account_name, asdict(initial_account))
            db.write_log(
                name=account_name,
                type="account",
                message=f"Created account with name {account_name}",
            )
        return initial_account

    @classmethod
    def get_account_names(cls) -> list[str]:
        with AccountsDatabase() as db:
            return db.get_account_name()

    @classmethod
    def get(cls, account_name: str) -> "Account | None":
        with AccountsDatabase() as db:
            account_data = db.get_account(account_name)
            if account_data is None:
                return None

            return Account.from_dict(account_data)

    def reset_account(self):
        initial_account = self.initial_account(self.account_name)
        self.id = initial_account.id
        self.last_updated_at = initial_account.last_updated_at
        self.holdings = initial_account.holdings
        self._save()
        self._write_log(
            type="account",
            message=f"Reset account {self.account_name} to initial state",
        )

    @classmethod
    def delete_account(cls, account_name: str):
        with AccountsDatabase() as db:
            db.delete_account(account_name)
            db.write_log(
                name=account_name,
                type="account",
                message=f"Deleted account with name {account_name}",
            )

    @classmethod
    def delete_all_accounts(cls):
        with AccountsDatabase() as db:
            db.delete_all_accounts()
            db.write_log(
                name="all",
                type="account",
                message="Deleted all accounts",
            )

    @classmethod
    def get_logs(cls, account_name: str, last_n: int = 10) -> list[AccountLog]:
        with AccountsDatabase() as db:
            return [
                AccountLog.from_dict(log)
                for log in db.read_logs(account_name, last_n=last_n)
            ]

    def record_swap_transaction(
        self,
        token_in_symbol: str,
        token_in_address: str,
        token_in_amount: int,
        token_out_symbol: str,
        token_out_address: str,
        token_out_amount: int,
        blockchain_transaction: dict[str, Any],
    ):
        swap_transaction = AccountTransaction(
            token_in_symbol=token_in_symbol,
            token_in_address=token_in_address,
            token_in_amount=token_in_amount,
            token_out_symbol=token_out_symbol,
            token_out_address=token_out_address,
            token_out_amount=token_out_amount,
            executed_at=datetime.now(),
            blockchain_transaction=blockchain_transaction,
        )
        # New behavior:
        # - `token_in` must be a token the account already holds and is being spent (validated and decremented)
        # - `token_out` may be an existing holding (received) or a new holding (created)

        # 1) Validate token_in holding exists and has enough amount (it is the spent token)
        token_in_holding = None
        for h in self.holdings:
            if (
                h.token_symbol == token_in_symbol
                and h.token_address == token_in_address
            ):
                token_in_holding = h
                break

        if token_in_holding is None:
            raise ValueError(f"Account does not hold token_in: {token_in_symbol}")

        if token_in_holding.amount < token_in_amount:
            raise ValueError(
                f"Insufficient holdings for {token_in_symbol}: have {token_in_holding.amount}, need {token_in_amount}"
            )

        # 2) Update token_in holding: record that tokens were spent (token_out transaction relative to this holding), adjust amount and last_updated_at
        token_in_holding.sell_transactions.append(swap_transaction)
        token_in_holding.amount -= token_in_amount
        token_in_holding.last_updated_at = datetime.now()

        if token_in_holding.amount == 0:
            self.holdings.remove(token_in_holding)

        # 3) Find or create token_out holding (the token being received)
        token_out_holding = None
        for h in self.holdings:
            if (
                h.token_symbol == token_out_symbol
                and h.token_address == token_out_address
            ):
                token_out_holding = h
                break

        if token_out_holding is None:
            # create a new holding record for token_out
            token_out_holding = AccountHolding(
                token_symbol=token_out_symbol,
                token_address=token_out_address,
                amount=0,
                last_updated_at=datetime.now(),
                buy_transactions=[],
                sell_transactions=[],
            )
            self.holdings.append(token_out_holding)

        # 3a) Update token_out holding: record incoming tokens, adjust amount and last_updated_at
        token_out_holding.buy_transactions.append(swap_transaction)
        token_out_holding.amount += token_out_amount
        token_out_holding.last_updated_at = datetime.now()

        # 4) Update account-level last_updated and persist
        self.last_updated_at = datetime.now()
        self._save()
        self._write_log(
            type="account",
            message=f"Executed swap transaction {json.dumps(asdict(swap_transaction), cls=DateTimeEncoder)}",
        )

    def report(self) -> str:
        return json.dumps(asdict(self), cls=DateTimeEncoder)

    def _save(self):
        with AccountsDatabase() as db:
            db.update_account(self.account_name, asdict(self))

    def _write_log(self, type: str, message: str):
        with AccountsDatabase() as db:
            db.write_log(
                name=self.account_name,
                type=type,
                message=message,
            )

    def __str__(self) -> str:
        return f"Account(name={self.account_name}, created_at={self.last_updated_at}) holdings={self.holdings}"
