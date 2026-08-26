"""
Pytest unit tests for MCP WebSocket Transport.
"""

import pytest
import websockets

from mcp_websocket import (
    JSONRPCRequest,
    WebSocketClientTransport,
    serve_websocket,
)


class MockMCPServer:
    async def run(self, read_stream, write_stream):
        async for msg in read_stream:
            if isinstance(msg, dict):
                method = msg.get("method")
                msg_id = msg.get("id")
                if method == "ping":
                    await write_stream.send(
                        {"jsonrpc": "2.0", "id": msg_id, "result": {"pong": True}}
                    )
                elif method == "echo":
                    params = msg.get("params", {})
                    await write_stream.send(
                        {"jsonrpc": "2.0", "id": msg_id, "result": params}
                    )


@pytest.mark.asyncio
async def test_websocket_transport_roundtrip():
    async def handler(websocket):
        server = MockMCPServer()
        await serve_websocket(server, websocket)

    async with websockets.serve(handler, "127.0.0.1", 0) as server:
        host, port = server.sockets[0].getsockname()
        url = f"ws://{host}:{port}"

        async with WebSocketClientTransport(url) as (read_stream, write_stream):
            # Test Ping
            await write_stream.send(JSONRPCRequest(id=101, method="ping"))
            resp = await read_stream.receive()
            assert resp["id"] == 101
            assert resp["result"] == {"pong": True}

            # Test Echo
            await write_stream.send(
                JSONRPCRequest(id=102, method="echo", params={"message": "hello"})
            )
            resp2 = await read_stream.receive()
            assert resp2["id"] == 102
            assert resp2["result"] == {"message": "hello"}
