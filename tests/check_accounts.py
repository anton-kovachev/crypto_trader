from entities import Account


def print_account(account_name: str):
    account = Account.get(account_name)
    if account is None:
        print(f"Account '{account_name}' not found.")
        return
    print(f"Account Name: {account.account_name}")
    print(f"Account Last Updated At: {account.last_updated_at}")
    print(f"Account Holdings: {account.holdings}")


if __name__ == "__main__":
    print_account("Max Kaiser")
