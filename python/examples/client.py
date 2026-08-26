"""
Example Python client using MCP WebSocket Transport.
"""

import asyncio

from mcp_transport_websocket import JSONRPCRequest, WebSocketClientTransport


async def main():
    url = "ws://localhost:8765"
    print(f"Connecting to MCP WebSocket Server at {url}...")

    async with WebSocketClientTransport(url) as (read_stream, write_stream):
        print("Connected! Sending ping request...")
        ping_req = JSONRPCRequest(id=1, method="ping")
        await write_stream.send(ping_req)

        async for response in read_stream:
            print("Received response:", response)
            break


if __name__ == "__main__":
    asyncio.run(main())
