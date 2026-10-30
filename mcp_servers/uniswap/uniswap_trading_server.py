from mcp.server import MCPServer
from numpy import uint
from services.uniswap import (
    get_quote as uniswap_get_quote,
    build_permit2_signature as uniswap_build_permit2_signature,
    submit_swap_transaction as uniswap_submit_swap_transaction,
    check_allowance as uniswap_check_allowance,
    allow as uniswap_allow,
)
from models.uniswap import QuoteResult, SwapTransaction
from typing import Any

mcp = MCPServer("uniswap_server")


@mcp.tool()
def get_quote(token_in: str, token_out: str, amount_in: str) -> QuoteResult:
    """
    Get a real-time swap quote from the Uniswap Aggregator API to determine the
    optimal route and expected output amount for a token trade.

    This tool provides the current market price, estimated price impact,
    and the necessary transaction data (calldata) required to execute
    the swap on the blockchain via the Uniswap router.

    Args:
        token_in: The contract address of the token to swap from.
        token_out: The contract address of the token to swap to.
        amount_in: The amount of tokens to swap, provided as a string
            representing the value in the token's smallest unit (wei).
        amount_out: The desired output amount for the swap, provided as a string
            representing the value in the token's smallest unit (wei). This is used when performing an 'exactOut' swap.
        type: The swap type. 'exactIn' specifies the input amount,
            'exactOut' specifies the desired output amount (default is 'exactIn').
        chainId: The network ID where the swap should be quoted (default is 1 for Ethereum).

    Returns:
        QuoteResult: A quote object containing the expected output amount,
        the current price, price impact, and a 'txData' object with the
        encoded calldata needed for the swap transaction.
    """
    return uniswap_get_quote(token_in, token_out, amount_in)


# @mcp.tool()
# def build_permit2_signature(
#     private_key: str,
#     token: str,
#     amount: int,
#     nonce: int,
#     expiration: int,
#     permit2_address: str,
#     spender: str,
# ) -> str:
#     """
#     Generate an EIP-712 Permit2 signature for a token. This signature allows a
#     third-party relayer or router to spend a specific amount of tokens on
#     behalf of the user without requiring a prior on-chain 'approve' transaction.

#     This is a critical step for implementing gasless swaps or intent-based
#     trading flows.

#     Args:
#         private_key: The private key of the user signing the permit.
#         token: The contract address of the ERC-20 token being authorized.
#         amount: The maximum amount of tokens the spender is authorized to move (in wei).
#         nonce: The current nonce for the user's Permit2 authorization.
#         expiration: The Unix timestamp after which the signature is no longer valid.
#         permit2_address: The address of the Permit2 contract on the network.
#         spender: The address authorized to spend the tokens (e.g., the Uniswap Router).

#     Returns:
#         str: The hex-encoded signature that can be submitted to the blockchain.
#     """
#     return uniswap_build_permit2_signature(
#         private_key, token, amount, nonce, expiration, permit2_address, spender
#     )


@mcp.tool()
def submit_swap_transaction(tx: SwapTransaction) -> dict[str, Any]:
    """
    Submit a signed swap transaction to the blockchain via the provided account private key.
    This tool should be used after obtaining a quote for price verification and fetching the current blockchain account data to ensure the transaction is valid and executable.
    Always prepare the calldata for the swap transaction accurately to match the expected swap parameters.

    Args:
        tx: A SwapTransaction object containing the destination address,
            encoded calldata, value, gas limit

    Returns:
        dict[str, Any]: A dictionary containing the transaction details and the transaction hash.
    """
    return uniswap_submit_swap_transaction(tx)


@mcp.tool()
def check_allowance(token: str, owner: str, spender: str, amount_to_spend: int) -> bool:
    """
    Check the allowance of a spender for a specific ERC-20 token and owner.

    Args:
        token: The contract address of the ERC-20 token.
        owner: The address of the token owner.
        spender: The address of the spender.
        amount_to_spend: The amount the spender is attempting to spend (in wei).

    Returns:
        bool: True if the spender is allowed to spend the specified amount, False otherwise.
    """
    return uniswap_check_allowance(token, owner, spender, amount_to_spend)


@mcp.tool()
def allow(token: str, owner: str, spender: str, amount_to_approve: int) -> bool:
    """
    Approve a spender to spend a specific amount of an ERC-20 token on behalf of the owner.

    Args:
        token: The contract address of the ERC-20 token.
        owner: The address of the token owner.
        spender: The address of the spender.
        amount_to_approve: The amount the spender is authorized to spend (in wei).

    Returns:
        bool: True if the approval was successful, False otherwise.
    """
    return uniswap_allow(token, owner, spender, amount_to_approve)


if __name__ == "__main__":
    mcp.run(transport="stdio")
