import os
import sys
from pathlib import Path

from agents.mcp import MCPServerStdio, MCPServerStdioParams

PROJECT_DIR = str(Path(__file__).resolve().parent.parent)


def _qdrant_url() -> str:
    qdrant_url = os.getenv("QDRANT_URL")
    if qdrant_url:
        return qdrant_url
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        raise EnvironmentError("QDRANT_URL must be set when running in AWS Lambda")
    return "http://127.0.0.1:6333"


def get_crypto_research_mcp_servers() -> list[MCPServerStdio]:
    return [
        MCPServerStdio(
            MCPServerStdioParams(
                {
                    "command": sys.executable,
                    "args": ["-m", "mcp_servers.coinmarketcap_data_server"],
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
                        "COLLECTION_NAME": "crypto_currency_knowledge_base",
                        "QDRANT_URL": _qdrant_url(),
                        **(
                            {"QDRANT_API_KEY": os.environ["QDRANT_API_KEY"]}
                            if os.getenv("QDRANT_API_KEY")
                            else {}
                        ),
                        "HF_HUB_VERBOSITY": "info",
                        "TRANSFORMERS_VERBOSITY": "info",
                        **(
                            {
                                "UV_CACHE_DIR": "/tmp/uv-cache",
                                "HF_HOME": "/tmp/huggingface",
                            }
                            if os.getenv("AWS_LAMBDA_FUNCTION_NAME")
                            else {}
                        ),
                    },
                }
            ),
            client_session_timeout_seconds=300,
        ),
    ]
