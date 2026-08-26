"""
Python MCP Tool Server using WebSocket Transport.
Registers tools: `calculate_bmi` and `reverse_string`.
"""

import asyncio
import sys

import websockets

from mcp_websocket_transport import serve_websocket

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class MCPToolServer:
    """MCP Server exposing sample tools over WebSocket transport."""

    async def run(self, read_stream, write_stream):
        async for msg in read_stream:
            if not isinstance(msg, dict):
                continue

            method = msg.get("method")
            msg_id = msg.get("id")

            # 1. Initialize
            if method == "initialize":
                await write_stream.send(
                    {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {"tools": {}},
                            "serverInfo": {
                                "name": "python-mcp-tool-server",
                                "version": "1.0.0",
                            },
                        },
                    }
                )
            # 2. List tools
            elif method == "tools/list":
                await write_stream.send(
                    {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "tools": [
                                {
                                    "name": "calculate_bmi",
                                    "description": "Calculates Body Mass Index given weight (kg) and height (m).",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "weight_kg": {"type": "number"},
                                            "height_m": {"type": "number"},
                                        },
                                        "required": ["weight_kg", "height_m"],
                                    },
                                },
                                {
                                    "name": "reverse_string",
                                    "description": "Reverses an input string.",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {"text": {"type": "string"}},
                                        "required": ["text"],
                                    },
                                },
                            ]
                        },
                    }
                )
            # 3. Call tool
            elif method == "tools/call":
                params = msg.get("params", {})
                name = params.get("name")
                arguments = params.get("arguments", {})

                if name == "calculate_bmi":
                    weight = float(arguments.get("weight_kg", 0))
                    height = float(arguments.get("height_m", 1))
                    bmi = round(weight / (height**2), 2)
                    status = (
                        "Normal weight"
                        if 18.5 <= bmi < 25
                        else "Overweight"
                        if bmi >= 25
                        else "Underweight"
                    )
                    res_text = f"BMI: {bmi} ({status})"
                elif name == "reverse_string":
                    text = str(arguments.get("text", ""))
                    res_text = f"Reversed: '{text[::-1]}'"
                else:
                    res_text = f"Unknown tool: {name}"

                await write_stream.send(
                    {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {"content": [{"type": "text", "text": res_text}]},
                    }
                )
            # 4. Ping
            elif method == "ping":
                await write_stream.send({"jsonrpc": "2.0", "id": msg_id, "result": {}})
            # 5. Prompts / Resources (return empty lists instead of hanging)
            elif method == "prompts/list":
                await write_stream.send(
                    {"jsonrpc": "2.0", "id": msg_id, "result": {"prompts": []}}
                )
            elif method == "resources/list":
                await write_stream.send(
                    {"jsonrpc": "2.0", "id": msg_id, "result": {"resources": []}}
                )
            elif msg_id is not None:
                # Catch-all for any unhandled request so the client never hangs waiting
                await write_stream.send(
                    {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method '{method}' not supported",
                        },
                    }
                )


async def handler(websocket):
    server = MCPToolServer()
    await serve_websocket(server, websocket)


async def main():
    import os

    port = int(os.getenv("PORT", "8767"))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"[SERVER] Python MCP Tool Server listening on ws://{host}:{port}")
    async with websockets.serve(handler, host, port):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
