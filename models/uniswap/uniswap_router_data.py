from dataclasses import dataclass
from typing import Any


@dataclass
class UniswapRouterData:
    router_address: str
    router_abi: list[dict[str, Any]]
    chain_name: str
    chain_rpc_url: str
    chain_id: int
