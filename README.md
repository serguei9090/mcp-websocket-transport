# 🌐 MCP WebSocket Transport (`mcp-websocket-transport`)

> [!NOTE]
> ### 🎓 Educational & Academic Research Notice
> This project is an **academic research implementation and open-source library** exploring full-duplex WebSocket transports for the Model Context Protocol (MCP).
> - **Status:** Research Prototype & Open Source Library.
> - **License:** Open source under the [MIT License](LICENSE) (published on PyPI and npm). Free for community use and contribution.

---


>
> - **Status:** Personal Sandbox / Portfolio Piece.
> - **Terms of Use:** Free for personal exploration, educational study, and non-commercial research.
> - **Production / Commercial Use:** For enterprise or commercial production usage, prior authorization and permission from the author are required.
> - **Purpose:** Academic research, technical skill development, and architectural prototyping.

---


[![PyPI Version](https://img.shields.io/pypi/v/mcp-websocket-transport?color=blue&label=PyPI)](https://pypi.org/project/mcp-websocket-transport/)
[![npm Version](https://img.shields.io/npm/v/mcp-websocket-transport?color=red&label=npm)](https://www.npmjs.com/package/mcp-websocket-transport)
[![Python Support](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://pypi.org/project/mcp-websocket-transport/)
[![Node / Bun](https://img.shields.io/badge/runtime-Node.js%20%7C%20Bun-green)](https://www.npmjs.com/package/mcp-websocket-transport)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **High-Performance, Full-Duplex WebSocket Transport & Universal Bridge for the Model Context Protocol (MCP).**  
> *Available in both **Python** and **TypeScript / JavaScript** with 100% feature parity.*

---

## 🚀 Why WebSocket Transport?

The standard Model Context Protocol (MCP) defines `stdio` (local subprocesses) and `StreamableHTTP` (HTTP POST + Server-Sent Events). While `StreamableHTTP` works for simple requests, it struggles with complex multi-agent architectures:

* ⚠️ **Asymmetric Reverse Requests**: In advanced MCP workflows—such as **Sampling** (`sampling/createMessage`) and **Roots Discovery** (`roots/list`)—the *server* must initiate requests to the *client*. Over SSE, this requires complex HTTP POST correlation headers and fragile session tracking.
* ⚠️ **Progress Streaming Overhead**: Streaming live progress bars (`notifications/progress`) and log messages over HTTP connections often triggers proxy timeouts (504 Gateway Timeout).
* ⚠️ **Header Bloat**: HTTP adds 500+ bytes of headers to every single JSON-RPC frame.

### 🌟 The WebSocket Advantage:
* ✅ **Full-Duplex Symmetrical Connection**: Both Client and Server can initiate requests and stream notifications over a single persistent TCP/TLS socket (`ws://` / `wss://`).
* ✅ **Sub-Millisecond Overhead**: Frame headers are only 2–10 bytes.
* ✅ **Zero-State Complexities**: 1 persistent connection per session—no distributed session caches or sticky routing required.
* ✅ **Universal Desktop Host Bridge (`mcp-ws-bridge`)**: Connect **Claude Desktop, LM Studio, Cursor, and Antigravity** to any remote or Dockerized WebSocket server with a single command!

---

## 📦 Packages in this Repository

| Language | Directory | Package Name | Registry | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Python** | [`python/`](python/) | **`mcp-websocket-transport`** | PyPI (`v1.0.0`) | [![PyPI](https://img.shields.io/pypi/v/mcp-websocket-transport)](https://pypi.org/project/mcp-websocket-transport/) |
| **TypeScript** | [`typescript/`](typescript/) | **`mcp-websocket-transport`** | npm (`v1.0.0`) | [![npm](https://img.shields.io/npm/v/mcp-websocket-transport)](https://www.npmjs.com/package/mcp-websocket-transport) |
| **CLI Bridge** | [`python/`](python/) & [`typescript/`](typescript/) | **`mcp-ws-bridge`** | PyPI / npm | Built-in CLI |

---

## ⚡ Quickstart: Python

### Installation
```bash
# With uv (recommended)
uv add mcp-websocket-transport

# With pip
pip install mcp-websocket-transport
```

### 1. Server Example (Python)
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

async def main():
    async def handler(websocket):
        await serve_websocket(mcp._mcp_server, websocket)

    print("🚀 MCP WebSocket Server running on ws://localhost:8765")
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Client Example (Python)
```python
import asyncio
from mcp.client.session import ClientSession
from mcp_websocket_transport import WebSocketClientTransport

async def main():
    async with WebSocketClientTransport("ws://localhost:8765") as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Discovered tools:", [t.name for t in tools.tools])
            
            result = await session.call_tool("add", {"a": 10, "b": 25})
            print("Tool Result:", result.content[0].text)

asyncio.run(main())
```

---

## ⚡ Quickstart: TypeScript / JavaScript

### Installation
```bash
# With bun
bun add mcp-websocket-transport

# With npm
npm install mcp-websocket-transport
```

### 1. Server Example (TypeScript)
```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { WebSocketServer } from "ws";
import { WebSocketServerTransport } from "mcp-websocket-transport";

const wss = new WebSocketServer({ port: 8765 });
console.log("🚀 MCP WebSocket Server running on ws://localhost:8765");

wss.on("connection", async (ws) => {
  const server = new Server(
    { name: "calculator-server", version: "1.0.0" },
    { capabilities: { tools: {} } }
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: [{
      name: "add",
      description: "Adds two numbers",
      inputSchema: {
        type: "object",
        properties: { a: { type: "number" }, b: { type: "number" } },
        required: ["a", "b"]
      }
    }]
  }));

  server.setRequestHandler(CallToolRequestSchema, async (req) => {
    const { a, b } = req.params.arguments as any;
    return { content: [{ type: "text", text: `Sum: ${Number(a) + Number(b)}` }] };
  });

  await server.connect(new WebSocketServerTransport(ws));
});
```

### 2. Client Example (TypeScript / Browser)
```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { WebSocketClientTransport } from "mcp-websocket-transport";
import WebSocket from "ws";

async function main() {
  const client = new Client({ name: "ts-agent", version: "1.0.0" });
  await client.connect(new WebSocketClientTransport("ws://localhost:8765", { WebSocket }));

  const tools = await client.listTools();
  console.log("Discovered tools:", tools.tools.map(t => t.name));

  const res = await client.callTool({ name: "add", arguments: { a: 12, b: 30 } });
  console.log("Tool Result:", res.content[0].text);
}

main();
```

---

## 🌉 Universal Desktop Host Bridge (`mcp-ws-bridge`)

Desktop MCP hosts (**Claude Desktop, LM Studio, Cursor, Antigravity**) communicate exclusively via standard I/O (`stdio`).

Both Python and TypeScript packages bundle the **`mcp-ws-bridge` CLI**, allowing desktop hosts to seamlessly connect to any local, Docker, or remote WebSocket server without writing a single line of bridge code!

```
┌────────────────────────────────────────────────────────────┐
│      Claude Desktop / LM Studio / Cursor / Antigravity     │
│                     (STDIO Interface)                      │
└─────────────────────────────┬──────────────────────────────┘
                              │ Standard I/O (stdin/stdout)
                              ▼
┌────────────────────────────────────────────────────────────┐
│                     `mcp-ws-bridge`                        │
│           (Cross-Platform Transparent Pipe)                │
└─────────────────────────────┬──────────────────────────────┘
                              │ Full-Duplex WebSocket (ws://)
                              ▼
┌────────────────────────────────────────────────────────────┐
│                  Remote MCP WebSocket Server               │
│                (Localhost, Docker, Cloud)                  │
└────────────────────────────────────────────────────────────┘
```

### ⚙️ Desktop Configuration Examples

#### Claude Desktop / LM Studio / Antigravity Config (`mcp_config.json`):

**Using Python `uv` / `uvx`:**
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

**Using Node / `npx` / `bunx`:**
```json
{
  "mcpServers": {
    "my-websocket-tools": {
      "command": "bunx",
      "args": ["mcp-ws-bridge", "--url", "ws://localhost:8765"]
    }
  }
}
```

---

## 🐳 Docker Support

Run both Python and TypeScript servers concurrently with Docker Compose:

```bash
cd docker
docker compose up --build -d
```

* **Python MCP Server**: listening on `ws://localhost:8767`
* **TypeScript MCP Server**: listening on `ws://localhost:8765`

To stop:
```bash
docker compose down
```

---

## 🧪 Testing & Verification

Run the automated test suites in either language:

### Python Tests
```bash
cd python
uv run --all-extras pytest -v
```

### TypeScript Tests
```bash
cd typescript
bun run test
```

---

## 📚 Technical Documentation & Manifest

* 📄 [**Protocol Architecture & Formal Specification**](docs/MCP-WebSocket-Transport-Specification.md): Complete RFC-style specification with sequence diagrams and comparison matrices.
* 📖 [**Manual Testing & Verification Guide**](docs/Manual-Testing-Guide.md): Interactive instructions for testing with LM Studio, Antigravity, and Google GenAI.

---

## 📄 License

MIT License. Designed and authored by **Serguei Castillo** with high-performance standards.