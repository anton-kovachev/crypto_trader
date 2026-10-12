from pathlib import Path
from agents.mcp import MCPServerStdio, MCPServerStdioParams

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)


def get_uniswap_trading_servers() -> list[MCPServerStdio]:
    return [
        MCPServerStdio(params)
        for params in [
            MCPServerStdioParams(
                {
                    "command": "uv",
                    "args": ["run", "-m", "mcp_servers.uniswap.uniswap_trading_server"],
                    "cwd": PROJECT_ROOT,
                }
            )
        ]
    ]
