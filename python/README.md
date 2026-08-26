# 🐍 Python `mcp-websocket-transport`

[![PyPI Version](https://img.shields.io/pypi/v/mcp-websocket-transport?color=blue&label=PyPI)](https://pypi.org/project/mcp-websocket-transport/)
[![Python Support](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://pypi.org/project/mcp-websocket-transport/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)

Full-duplex WebSocket Transport for the Model Context Protocol (MCP) in Python. Built on **AnyIO** and compatible with **FastAPI**, **Starlette**, and standalone **websockets**.

---

## 📦 Installation

```bash
# Using uv (recommended)
uv add mcp-websocket-transport

# With pip
pip install mcp-websocket-transport

# With all extras (FastAPI, uvicorn, websockets, mcp CLI)
pip install "mcp-websocket-transport[all]"
```

---

## 🛠️ Quickstart

### 1. FastMCP Server with WebSocket (`examples/fastmcp_server.py`)
```python
import asyncio
import websockets
from mcp.server.fastmcp import FastMCP
from mcp_websocket_transport import serve_websocket

mcp = FastMCP("calculator-server")

@mcp.tool()
def add(a: float, b: float) -> float:
    """Adds two numbers."""
    return a + b

@mcp.tool()
def get_stock(symbol: str) -> dict:
    """Fetches mock stock price."""
    return {"symbol": symbol.upper(), "price": 225.50}

async def main():
    async def handler(websocket):
        await serve_websocket(mcp._mcp_server, websocket)

    print("🚀 MCP WebSocket Server running on ws://0.0.0.0:8765")
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Python Client (`examples/mcp_tool_client.py`)
```python
import asyncio
from mcp.client.session import ClientSession
from mcp_websocket_transport import WebSocketClientTransport

async def main():
    async with WebSocketClientTransport("ws://localhost:8765") as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])
            
            # Call tool
            result = await session.call_tool("add", {"a": 15, "b": 27})
            print("Result:", result.content[0].text)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🌉 Desktop Host Bridge (`mcp-ws-bridge`)

To connect **Claude Desktop, LM Studio, Cursor, or Antigravity** to a running WebSocket server:

```json
{
  "mcpServers": {
    "my-websocket-tools": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "path/to/mcp-websocket/python",
        "python",
        "-m",
        "mcp_websocket_transport.bridge",
        "--url",
        "ws://localhost:8767"
      ]
    }
  }
}
```

---

## 🧪 Testing

```bash
uv run --all-extras pytest -v
```

---

## 📄 License

MIT License.
