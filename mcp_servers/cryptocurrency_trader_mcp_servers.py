import sys
from agents.mcp import MCPServerStdio, MCPServerStdioParams
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.resolve()


def get_cryptocurrency_trader_mcp_servers() -> list[MCPServerStdio]:
    return [
        MCPServerStdio(
            name="blockchain_data_mcp_server",
            params=MCPServerStdioParams(
                {
                    "command": sys.executable,
                    "args": ["-m", "mcp_servers.blockchain_data.server"],
                    "cwd": PROJECT_DIR,
                }
            ),
        ),
        MCPServerStdio(
            name="crypto_account_mcp_server",
            params=MCPServerStdioParams(
                {
                    "command": sys.executable,
                    "args": [
                        "-m",
                        "mcp_servers.accounts.crypto_account_mcp_server",
                    ],
                    "cwd": PROJECT_DIR,
                }
            ),
        ),
        MCPServerStdio(
            name="pushover_push_server",
            params=MCPServerStdioParams(
                {
                    "command": sys.executable,
                    "args": [
                        "-m",
                        "mcp_servers.pushover_push_server",
                    ],
                    "cwd": PROJECT_DIR,
                }
            ),
        ),
    ]
