"""
STDIO-to-WebSocket Bridge for Model Context Protocol (MCP).

Allows ANY standard MCP Host (Antigravity, Claude Desktop, Cursor, LM Studio)
to communicate with a remote or Dockerized MCP WebSocket server.
"""

import sys
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent.parent
if str(PKG_DIR) not in sys.path:
    sys.path.insert(0, str(PKG_DIR))

from mcp_websocket_transport.bridge import main_cli  # noqa: E402

if __name__ == "__main__":
    main_cli()
