mcp-websocket
  

Full-duplex WebSocket Transport for the Model Context Protocol (MCP) in Python. Built for maximum performance with AnyIO, FastAPI, Starlette, and websockets.


🚀 Why WebSocket Transport for MCP?
The standard Model Context Protocol (MCP) uses stdio for local processes and Streamable HTTP / SSE for remote communication.

While Streamable HTTP functions across standard HTTP proxies, it has key limitations:

Asymmetric Request/Event Channeling: Requires separate HTTP POST endpoints for upstream messages and SSE streams for downstream events.
Session Reconnection State: Requires custom headers, session tokens, or message replay buffers on connection drops.
Reverse Proxy Buffering: Some proxies buffer SSE chunks, delaying tool progress and LLM sampling responses.
🌟 WebSocket Advantages
True Full-Duplex Bi-Directional Streaming: Single persistent TCP connection for requests, responses, notifications, progress reporting, and server-initiated sampling.
Minimal Maintenance Surface (<50 LOC): Directly bridges WebSocket I/O frames into AnyIO memory streams used by the official mcp SDK.
Framework Agnostic: Native support for FastAPI, Starlette, and the standalone websockets package.
Low Latency & Low Overhead: Sub-millisecond packet delivery without HTTP header bloat per frame.


📦 Installation
# Basic installation

pip install mcp-websocket

# With FastAPI / Uvicorn support

pip install "mcp-websocket[fastapi]"

# With websockets support

pip install "mcp-websocket[websockets]"

# Using uv

uv add "mcp-websocket[all]"


🛠️ Quickstart
1. FastAPI / Starlette Server (fastapi_server.py)
from fastapi import FastAPI, WebSocket

from mcp.server import Server

from mcp.types import Tool, TextContent

from mcp_websocket import serve_websocket

import uvicorn

app = FastAPI(title="MCP WebSocket Server")

mcp_server = Server("fastapi-ws-demo")

@mcp_server.list_tools()

async def list_tools():

    return [

        Tool(

            name="ping",

            description="Health check tool",

            inputSchema={"type": "object"}

        )

    ]

@mcp_server.call_tool()

async def call_tool(name: str, arguments: dict):

    if name == "ping":

        return [TextContent(type="text", text="pong")]

    raise ValueError(f"Unknown tool: {name}")

@app.websocket("/ws")

async def websocket_endpoint(websocket: WebSocket):

    await serve_websocket(mcp_server, websocket)

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8765)


2. Standalone websockets Server (websockets_server.py)
import asyncio

import websockets

from mcp.server import Server

from mcp.types import Tool, TextContent

from mcp_websocket import serve_websocket

mcp_server = Server("websockets-demo")

@mcp_server.list_tools()

async def list_tools():

    return [Tool(name="ping", description="Health check tool", inputSchema={"type": "object"})]

@mcp_server.call_tool()

async def call_tool(name: str, arguments: dict):

    return [TextContent(type="text", text="pong")]

async def main():

    async def handler(websocket):

        await serve_websocket(mcp_server, websocket)

    async with websockets.serve(handler, "0.0.0.0", 8765):

        print("MCP WebSocket server running on ws://0.0.0.0:8765")

        await asyncio.Future()

if __name__ == "__main__":

    asyncio.run(main())


3. Python MCP Client (client.py)
import asyncio

from mcp.client.session import ClientSession

from mcp_websocket import websocket_client

async def main():

    url = "ws://localhost:8765/ws"

    

    async with websocket_client(url) as (read_stream, write_stream):

        async with ClientSession(read_stream, write_stream) as session:

            # 1. Initialize

            await session.initialize()

            print("MCP Session Initialized!")

            # 2. List tools

            tools = await session.list_tools()

            print("Available Tools:", [t.name for t in tools.tools])

            # 3. Call tool

            result = await session.call_tool("ping", {})

            print("Tool Result:", result)

if __name__ == "__main__":

    asyncio.run(main())


📖 API Reference
websocket_client(url, buffer_size=100, **websocket_kwargs)
Async context manager yielding (read_stream, write_stream) for mcp.client.session.ClientSession.
serve_websocket(server, websocket, buffer_size=100, auto_accept=True)
Async function that bridges a connected WebSocket (FastAPI/Starlette or websockets) to an mcp.server.Server instance.
WebSocketServerTransport(server, buffer_size=100)
Helper class encapsulating WebSocket connection handling for an MCP Server instance.


🧪 Manual Testing
Execute the test suite locally:

python -m pytest tests/

# or directly:

python tests/test_transport.py


🚢 Publishing to PyPI
1. Install Build Tools
pip install --upgrade build twine

# or using uv:

uv tool install twine
2. Build Source Distribution & Wheel
python -m build

# or using uv:

uv build

This creates distribution archives in ./dist/:

mcp_websocket-1.0.0-py3-none-any.whl
mcp_websocket-1.0.0.tar.gz
3. Verify Package
twine check dist/*
4. Upload to TestPyPI (Recommended first step)
twine upload --repository testpypi dist/*
5. Upload to Production PyPI
twine upload dist/*

# or using uv:

uv publish


📄 License
MIT License.
