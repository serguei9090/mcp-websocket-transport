"""
Python MCP Tool Client using WebSocket Transport.
Connects, lists tools, calls `calculate_bmi` and `reverse_string`.
"""

import asyncio
import json
import sys

from mcp_websocket_transport import JSONRPCRequest, WebSocketClientTransport

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


async def main():
    url = "ws://localhost:8767"
    print(f"[CLIENT] Connecting Python Client to {url}...")

    async with WebSocketClientTransport(url) as (read_stream, write_stream):
        print("[CLIENT] Connected to Python MCP WebSocket Server!")

        # 1. Initialize Handshake
        print("\n[CLIENT] Initializing handshake...")
        await write_stream.send(
            JSONRPCRequest(
                id=1,
                method="initialize",
                params={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "python-mcp-client", "version": "1.0.0"},
                },
            )
        )
        init_resp = await read_stream.receive()
        print("Server Info:", init_resp.get("result", {}).get("serverInfo"))

        # 2. List tools
        print("\n[CLIENT] Listing available tools...")
        await write_stream.send(JSONRPCRequest(id=2, method="tools/list"))
        tools_resp = await read_stream.receive()
        tools = tools_resp.get("result", {}).get("tools", [])
        print("Available Tools:", json.dumps(tools, indent=2))

        # 3. Call calculate_bmi tool
        print("\n[CLIENT] Calling 'calculate_bmi' (weight_kg: 75, height_m: 1.78)...")
        await write_stream.send(
            JSONRPCRequest(
                id=3,
                method="tools/call",
                params={
                    "name": "calculate_bmi",
                    "arguments": {"weight_kg": 75, "height_m": 1.78},
                },
            )
        )
        bmi_resp = await read_stream.receive()
        print("Result:", bmi_resp.get("result", {}).get("content"))

        # 4. Call reverse_string tool
        print("\n[CLIENT] Calling 'reverse_string' (text: 'Model Context Protocol')...")
        await write_stream.send(
            JSONRPCRequest(
                id=4,
                method="tools/call",
                params={
                    "name": "reverse_string",
                    "arguments": {"text": "Model Context Protocol"},
                },
            )
        )
        rev_resp = await read_stream.receive()
        print("Result:", rev_resp.get("result", {}).get("content"))

        print("\n[CLIENT] Disconnecting client.")


if __name__ == "__main__":
    asyncio.run(main())
