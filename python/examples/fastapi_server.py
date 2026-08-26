"""
Example FastAPI server using MCP WebSocket Transport.
"""

import uvicorn
from fastapi import FastAPI, WebSocket

from mcp_websocket import serve_websocket

app = FastAPI(title="MCP WebSocket Server")


class DummyMCPServer:
    """Mock MCP Server implementation for FastAPI testing."""

    async def run(self, read_stream, write_stream):
        async for msg in read_stream:
            if isinstance(msg, dict) and msg.get("method") == "ping":
                response = {
                    "jsonrpc": "2.0",
                    "id": msg.get("id"),
                    "result": {"status": "pong"},
                }
                await write_stream.send(response)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    server = DummyMCPServer()
    await serve_websocket(server, websocket)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
