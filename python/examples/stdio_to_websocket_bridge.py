"""
STDIO-to-WebSocket Bridge for Model Context Protocol (MCP).

Allows ANY standard MCP Host (Antigravity, Claude Desktop, Cursor, LM Studio)
to communicate with a remote or Dockerized MCP WebSocket server.
"""

from mcp_websocket.bridge import main_cli

if __name__ == "__main__":
    main_cli()
