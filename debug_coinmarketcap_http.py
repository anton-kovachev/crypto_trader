#!/usr/bin/env python3
"""Run the CoinMarketCap MCP server using the HTTP (streamable) transport.

Usage:
  DEBUGPY=1 python3 debug_coinmarketcap_http.py
or
  python3 debug_coinmarketcap_http.py

If `DEBUGPY` environment variable is set, the wrapper starts `debugpy`
and waits for a debugger to attach on port 5678 before starting the server.
The server will be available at http://127.0.0.1:8000/mcp by default.
"""

import os
import sys
import logging

DEBUGPY_PORT = int(os.environ.get("DEBUGPY_PORT", "5678"))
USE_DEBUGPY = os.environ.get("DEBUGPY", "0") in ("1", "true", "True")
# If WAIT_FOR_CLIENT is set to "0" the wrapper will not block on debugpy.wait_for_client()
WAIT_FOR_CLIENT = os.environ.get("WAIT_FOR_CLIENT", "1") in ("1", "true", "True")
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))


def enable_debugpy():
    try:
        import debugpy
    except Exception as exc:  # pragma: no cover - debug helper
        print(
            "debugpy is not installed. Install it with: python -m pip install debugpy",
            file=sys.stderr,
        )
        raise

    print(f"Starting debugpy and listening on 0.0.0.0:{DEBUGPY_PORT}...")
    debugpy.listen(("0.0.0.0", DEBUGPY_PORT))
    if WAIT_FOR_CLIENT:
        print("Waiting for debugger to attach...")
        debugpy.wait_for_client()
    else:
        print("Not waiting for debugger (WAIT_FOR_CLIENT=0). Continuing startup.")


def main():
    logging.basicConfig(level=logging.INFO)

    if USE_DEBUGPY:
        enable_debugpy()

    # Import the server module and run with HTTP transport (streamable HTTP)
    # This uses the same FastMCP `mcp` instance defined in the module.
    from mcp_servers import coinmarketcap_data_server as server_mod

    # configure host/port on the server settings (FastMCP.run does not accept host/port)
    server_mod.mcp.settings.host = HOST
    server_mod.mcp.settings.port = PORT
    print(
        f"Starting CoinMarketCap MCP server at http://{HOST}:{PORT}{server_mod.mcp.settings.streamable_http_path} (transport=streamable-http)"
    )
    # run using the streamable-http transport (FastMCP expects "streamable-http")
    server_mod.mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
