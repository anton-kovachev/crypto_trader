from importlib import import_module
from types import ModuleType
from typing import TYPE_CHECKING

from .crypto_currency_research_mcp_servers import get_crypto_research_mcp_servers
from .cryptocurrency_trader_mcp_servers import get_cryptocurrency_trader_mcp_servers
from .cryptocurrency_reporter_mcp_servers import get_cryptocurrency_reporter_mcp_servers

if TYPE_CHECKING:
    from . import blockchain_data, coinmarketcap_data
    from .blockchain_data import server as blockchain_data_server
    from .coinmarketcap_data import server as coinmarketcap_data_server

_LAZY_SERVER_MODULES = {
    "blockchain_data": ".blockchain_data",
    "coinmarketcap_data": ".coinmarketcap_data",
    "blockchain_data_server": ".blockchain_data.server",
    "coinmarketcap_data_server": ".coinmarketcap_data.server",
}


def __getattr__(name: str) -> ModuleType:
    module_path = _LAZY_SERVER_MODULES.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(module_path, __name__)
    globals()[name] = module
    return module


__all__ = [
    "get_crypto_research_mcp_servers",
    "get_cryptocurrency_trader_mcp_servers",
    "get_cryptocurrency_reporter_mcp_servers",
    "blockchain_data",
    "coinmarketcap_data",
    "blockchain_data_server",
    "coinmarketcap_data_server",
]
