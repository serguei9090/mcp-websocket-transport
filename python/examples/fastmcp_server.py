"""
FastMCP Server Example with WebSocket & `mcp dev` Support.

This file can be run in two ways:
1. With official MCP Inspector / CLI:
   uv run --with "mcp[cli]" mcp dev examples/fastmcp_server.py

2. Standalone over WebSocket Transport:
   uv run --with "mcp[cli]" python examples/fastmcp_server.py --ws
"""

import argparse
import asyncio
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    # MCP SDK 2.x
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:
    # MCP SDK 1.x
    from mcp.server.fastmcp import FastMCP

from mcp_websocket import serve_websocket

# 1. Initialize MCP Server (FastMCP / MCPServer)
mcp = FastMCP("calculator-and-data-server")


# 2. Define MCP Tools using standard FastMCP decorators
@mcp.tool()
def add_numbers(a: float, b: float) -> float:
    """Adds two numbers together and returns the sum."""
    return a + b


@mcp.tool()
def get_stock_price(symbol: str) -> dict:
    """Fetches real-time stock price data for a ticker symbol."""
    mock_prices = {"AAPL": 225.50, "GOOGL": 178.25, "MSFT": 415.80, "NVDA": 128.90}
    price = mock_prices.get(symbol.upper(), 100.0)
    return {"symbol": symbol.upper(), "price": price, "currency": "USD"}


@mcp.tool()
def summarize_text(text: str, max_words: int = 10) -> str:
    """Summarizes input text to a concise headline."""
    words = text.strip().split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."


# 3. WebSocket Bridge Handler
async def run_websocket_server(port: int = 8765):
    import websockets

    # Extract the underlying low-level MCP server from FastMCP / MCPServer
    lowlevel_server = getattr(mcp, "_lowlevel_server", None) or getattr(
        mcp, "_mcp_server", None
    )

    async def ws_handler(websocket):
        print(f"[SERVER] Client connected from {websocket.remote_address}")
        await serve_websocket(lowlevel_server, websocket)
        print("[SERVER] Client disconnected")

    print(f"🚀 FastMCP Server running over WebSocket on ws://localhost:{port}")
    async with websockets.serve(ws_handler, "localhost", port):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run FastMCP Server")
    parser.add_argument(
        "--ws",
        action="store_true",
        help="Run as WebSocket server (default: stdio for mcp dev)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8765")),
        help="WebSocket port (default: 8765)",
    )
    args = parser.parse_args()

    if args.ws:
        asyncio.run(run_websocket_server(port=args.port))
    else:
        # Default: run stdio transport (compatible with mcp dev / Claude Desktop)
        mcp.run()
