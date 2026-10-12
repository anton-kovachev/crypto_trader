from agents.mcp import MCPServerStdio, MCPServerStdioParams
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.resolve()


def get_cryptocurrency_reporter_mcp_servers() -> list[MCPServerStdio]:
    return [
        # MCPServerStdio(
        #     name="blockchain_data_mcp_server",
        #     params=MCPServerStdioParams(
        #         {
        #             "command": "uv",
        #             "args": ["run", "-m", "mcp_servers.blockchain_data_server"],
        #             "cwd": PROJECT_DIR,
        #         }
        #     ),
        # ),
        MCPServerStdio(
            name="crypto_account_mcp_server",
            params=MCPServerStdioParams(
                {
                    "command": "uv",
                    "args": [
                        "run",
                        "-m",
                        "mcp_servers.accounts.crypto_account_mcp_server",
                    ],
                    "cwd": PROJECT_DIR,
                }
            ),
        ),
    ]
