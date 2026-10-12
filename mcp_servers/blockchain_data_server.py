import config
import json
from mcp.server import FastMCP
from models import BlockchainAccountData
from pathlib import Path
from models.uniswap import UniswapRouterData
from services.blockchain.account_service import (
    get_suggested_gas_price as get_suggested_network_gas_price,
    get_account_nonce as get_account_network_nonce,
)

RESOURCES_DIR = Path(__file__).parent.parent.resolve() / "resources"

mcp = FastMCP("blockchain_data_server")


@mcp.tool()
def get_blockchain_account_data():
    """
    Retrieves the blockchain account data for the user.

    Returns:
        BlockchainAccountData: The blockchain account data object containing
        the user's account address, private key, and chain information such as official chain name, chain id, RPC url .
    """

    return BlockchainAccountData(
        account_address=config.USER_ADDRESS,
        account_private_key=config.USER_PRIVATE_KEY,
        chain_name=config.CHAIN_NAME,
        chain_rpc_url=config.CHAIN_RPC_URL,
        chain_id=config.CHAIN_ID,
    )


@mcp.tool()
def get_uniswap_router_data() -> UniswapRouterData:
    """
    Retrieves the Uniswap router data for the user.

    Returns:
        UniswapRouterData: The Uniswap router data object containing the router address, the router ABI and the chain information such as official chain name, chain id, RPC url.
    """

    with open(RESOURCES_DIR / "uniswap_router_v2_abi.json", "r") as f:
        router_abi = json.load(f)

    return UniswapRouterData(
        router_address=config.UNISWAP_ROUTER_ADDRESS,
        router_abi=router_abi,
        chain_name=config.CHAIN_NAME,
        chain_rpc_url=config.CHAIN_RPC_URL,
        chain_id=config.CHAIN_ID,
    )


@mcp.tool()
def get_suggested_gas_price() -> int:
    """
    Retrieves the suggested gas price for the current blockchain network.

    Returns:
        int: The suggested gas price in wei.
    """
    return get_suggested_network_gas_price()


@mcp.tool()
def get_account_nonce(account_address: str) -> int:
    """
    Retrieves the account nonce for the specified blockchain account address.

    Args:
        account_address (str): The blockchain account address for which to retrieve the nonce.

    Returns:
        int: The account nonce for the specified blockchain account address.
    """

    return get_account_network_nonce(account_address)


if __name__ == "__main__":
    mcp.run(transport="stdio")
