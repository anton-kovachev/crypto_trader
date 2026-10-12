import os
from dotenv import load_dotenv

load_dotenv(override=True)


def get_env_var(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise EnvironmentError(f"Missing required environment variable: {name}")
    return value


CHAIN_RPC_URL = get_env_var("CHAIN_RPC_URL")
CHAIN_ID = int(get_env_var("CHAIN_ID"))
CHAIN_NAME = get_env_var("CHAIN_NAME")

USD_TOKEN_SYMBOL = get_env_var("USD_TOKEN_SYMBOL")
USD_TOKEN_ADDRESS = get_env_var("USD_TOKEN_ADDRESS")
INITIAL_USDC_AMOUNT = int(get_env_var("INITIAL_USDC_AMOUNT"))

USER_PRIVATE_KEY = get_env_var("USER_PRIVATE_KEY")
USER_ADDRESS = get_env_var("USER_ADDRESS", "")
RELAYER_PRIVATE_KEY = get_env_var("RELAYER_PRIVATE_KEY")
# WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
# USDC = "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"


UNISWAP_API_KEY = get_env_var("UNISWAP_API_KEY")
UNISWAP_QUOTE_URL = "https://trade-api.gateway.uniswap.org/v1/quote"
UNISWAP_ROUTER_ADDRESS = get_env_var("UNISWAP_ROUTER_ADDRESS")
