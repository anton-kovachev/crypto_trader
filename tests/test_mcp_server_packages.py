import unittest
from types import ModuleType
from unittest.mock import patch

import mcp_servers
from mcp_servers import blockchain_data, coinmarketcap_data


class MCPServerPackageTests(unittest.TestCase):
    def test_data_packages_are_reexported(self) -> None:
        self.assertEqual(blockchain_data.__name__, "mcp_servers.blockchain_data")
        self.assertEqual(coinmarketcap_data.__name__, "mcp_servers.coinmarketcap_data")

    def test_server_modules_are_lazily_reexported(self) -> None:
        module = ModuleType("mcp_servers.blockchain_data.server")
        with patch("mcp_servers.import_module", return_value=module) as importer:
            exported_module = mcp_servers.__getattr__("blockchain_data_server")

        self.assertIs(exported_module, module)
        importer.assert_called_once_with(".blockchain_data.server", "mcp_servers")
        self.assertIn("blockchain_data_server", mcp_servers.__all__)
        self.assertIn("coinmarketcap_data_server", mcp_servers.__all__)


if __name__ == "__main__":
    unittest.main()
