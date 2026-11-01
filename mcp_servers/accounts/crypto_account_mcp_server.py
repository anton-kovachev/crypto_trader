from entities import Account, AccountLog
from mcp.server import MCPServer
from typing import Any

mcp = MCPServer("crypto_account_mcp_server")


@mcp.tool()
def get_account_names() -> list[str]:
    """
    Retrieve the names of all existing accounts.

    Returns:
        list[str]: A list of account names.
    """
    return Account.get_account_names()


@mcp.tool()
def get_account(account_name: str) -> Account | None:
    """
    Retrieve an account by its account name. This tool should be used to fetch pre existing account information

    Args:
        account_name (str): The name of the account to retrieve.

    Returns:
        Account | None: The account object corresponding to the given name, or None if account with such name is not found.
    """
    return Account.get(account_name)


@mcp.tool()
def create_account(account_name: str) -> Account:
    """
    Create a new account with the given name.

    Args:
        account_name (str): The name of the account to create.

    Returns:
        Account: The newly created account object.
    Throws:
        ValueError: If an account with the given name already exists.
    """
    return Account.create_account(account_name)


@mcp.tool()
def generate_report_for_account(account_name: str) -> str | None:
    """
    Generates a detailed crypto portfolio holdings report for the given account.

    Args:
        account_name (str): The name of the account to generate a report for.

    Returns:
        str: The report of the account as a JSON string.

    Throws:
        ValueError: If an account with the given name does not exist.
    """
    account = Account.get(account_name)
    if account is None:
        raise ValueError(f"Account with name {account_name} does not exist.")
    return account.report()


@mcp.tool()
def record_swap_transaction(
    account_name: str,
    token_in_symbol: str,
    token_in_address: str,
    token_in_amount: int,
    token_out_symbol: str,
    token_out_address: str,
    token_out_amount: int,
    blockchain_transaction: dict[str, Any],
) -> str | None:
    """
    Record a swap transaction for the given account.

    Args:
        account_name (str): The name of the account.
        token_in_symbol (str): The symbol of the token being swapped in.
        token_in_address (str): The address of the token being swapped in.
        token_in_amount (int): The amount of the token being swapped in.
        token_out_symbol (str): The symbol of the token being swapped out.
        token_out_address (str): The address of the token being swapped out.
        token_out_amount (int): The amount of the token being swapped out.
        blockchain_transaction (dict[str, Any]): The blockchain transaction details.

    Returns:
        None if successful, or an error message string if failed describing the reason.
    """
    account = Account.get(account_name)
    if account is None:
        raise ValueError(f"Account with name {account_name} does not exist.")

    try:
        account.record_swap_transaction(
            token_in_symbol=token_in_symbol,
            token_in_address=token_in_address,
            token_in_amount=token_in_amount,
            token_out_symbol=token_out_symbol,
            token_out_address=token_out_address,
            token_out_amount=token_out_amount,
            blockchain_transaction=blockchain_transaction,
        )
    except Exception as e:
        return f"Failed to record swap transaction: {e}"


@mcp.tool()
def reset_account(account_name: str) -> None:
    """
    Reset the given account to its initial state.

    Args:
        account_name (str): The name of the account to reset.

    Returns:
        None

    Throws:
        ValueError: If an account with the given name does not exist.
    """
    account = Account.get(account_name)
    if account is None:
        raise ValueError(f"Account with name {account_name} does not exist.")
    account.reset_account()


@mcp.resource("accounts://accounts_server/{name}")
def get_account_resource(name: str) -> Account:
    """
    Get the account resource for the given account name.

    Args:
        name (str): The name of the account.

    Returns:
        Account: The account object.

    Throws:
        ValueError: If an account with the given name does not exist.
    """
    account = Account.get(name)
    if account is None:
        raise ValueError(f"Account with name {name} does not exist.")
    return account


# @mcp.resource("accounts://accounts_server/{name}/activity_logs/{last_n}")
@mcp.tool()
def get_account_activity_logs_resource(name: str, last_n: int = 10) -> list[AccountLog]:
    """
    Activity logs for the account returning a list of the last_n (10 by default) activity logs related with this account.
    Get the last n logs for the given account.

    Args:
        name (str): The name of the account.
        last_n (int): The number of most recent logs to retrieve.

    Returns:
        list[AccountLog]: A list of account logs.

    Throws:
        ValueError: If an account with the given name does not exist.
    """
    account = Account.get(name)
    if account is None:
        raise ValueError(f"Account with name {name} does not exist.")
    return account.get_logs(account_name=name, last_n=last_n)


if __name__ == "__main__":
    mcp.run(transport="stdio")
