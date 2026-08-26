"""
Example standalone websockets server using MCP WebSocket Transport.
"""

import asyncio

import websockets

from mcp_transport_websocket import serve_websocket


class DummyMCPServer:
    """Mock MCP Server implementation for standalone testing."""

    async def run(self, read_stream, write_stream):
        async for msg in read_stream:
            if isinstance(msg, dict) and msg.get("method") == "ping":
                response = {
                    "jsonrpc": "2.0",
                    "id": msg.get("id"),
                    "result": {"status": "pong"},
                }
                await write_stream.send(response)
            elif isinstance(msg, dict) and msg.get("method") == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": msg.get("id"),
                    "result": {
                        "tools": [
                            {
                                "name": "echo",
                                "description": "Echo back input",
                                "inputSchema": {"type": "object"},
                            }
                        ]
                    },
                }
                await write_stream.send(response)


async def handler(websocket):
    server = DummyMCPServer()
    await serve_websocket(server, websocket)


async def main():
    print("Starting Standalone MCP WebSocket Server on ws://localhost:8765...")
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())
