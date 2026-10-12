from pathlib import Path
from agents.mcp import MCPServerStdio, MCPServerStdioParams

PROJECT_DIR = str(Path(__file__).resolve().parent.parent)
QDRANT_LOCAL_PATH = Path("memory/qdrant")


def get_crypto_research_mcp_servers() -> list[MCPServerStdio]:
    return [
        MCPServerStdio(
            MCPServerStdioParams(
                {
                    "command": "uv",
                    "args": ["--verbose", "run", "-m", "mcp_servers.coinmarketcap_data_server"],
                    "cwd": PROJECT_DIR,
                }
            ),
            client_session_timeout_seconds=120,
        ),
        # MCPServerStdio(
        #     name="qdrant",
        #     params=MCPServerStdioParams(
        #         {
        #             "command": "uv",
        #             "args": ["run", "-m", "mcp_servers.qdrant_data_server"],
        #             "cwd": PROJECT_DIR,
        #         }
        #     ),
        #     client_session_timeout_seconds=30,
        # ),
        MCPServerStdio(
            name="qdrant",
            params=MCPServerStdioParams(
                {
                    "command": "uvx",
                    "args": [
                        "--python",
                        "3.12",
                        "mcp-server-qdrant",
                        "--transport",
                        "stdio",
                    ],
                    "env": {
                        # "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
                        # "QDRANT_LOCAL_PATH": str(QDRANT_LOCAL_PATH),
                        "COLLECTION_NAME": "crypto_currency_knowledge_base",
                        "QDRANT_URL": "http://127.0.0.1:6333",
                        "HF_HUB_VERBOSITY": "info",
                        "TRANSFORMERS_VERBOSITY": "info"
                    },
                }
            ),
            client_session_timeout_seconds=300,
        ),
    ]
