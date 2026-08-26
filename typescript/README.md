# 🟦 TypeScript `mcp-websocket-transport`

[![npm Version](https://img.shields.io/npm/v/mcp-websocket-transport?color=red&label=npm)](https://www.npmjs.com/package/mcp-websocket-transport)
[![Runtime Support](https://img.shields.io/badge/runtime-Node.js%20%7C%20Bun%20%7C%20Browser-green)](https://www.npmjs.com/package/mcp-websocket-transport)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)

Full-duplex WebSocket Transport for the Model Context Protocol (MCP) in TypeScript, Node.js, Bun, and modern browser runtimes.

---

## 📦 Installation

```bash
# Using bun (recommended)
bun add mcp-websocket-transport @modelcontextprotocol/sdk ws

# Using npm
npm install mcp-websocket-transport @modelcontextprotocol/sdk ws

# Using pnpm
pnpm add mcp-websocket-transport @modelcontextprotocol/sdk ws
```

---

## 🛠️ Quickstart

### 1. TypeScript MCP Server (`examples/mcp-tool-server.ts`)
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
    tools: [
      {
        name: "add_numbers",
        description: "Adds two numbers together and returns the sum.",
        inputSchema: {
          type: "object",
          properties: { a: { type: "number" }, b: { type: "number" } },
          required: ["a", "b"]
        }
      }
    ]
  }));

  server.setRequestHandler(CallToolRequestSchema, async (req) => {
    const { a, b } = req.params.arguments as any;
    return { content: [{ type: "text", text: `Result: ${Number(a) + Number(b)}` }] };
  });

  await server.connect(new WebSocketServerTransport(ws));
});
```

### 2. TypeScript MCP Client (`examples/mcp-tool-client.ts`)
```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { WebSocketClientTransport } from "mcp-websocket-transport";
import WebSocket from "ws";

async function main() {
  const client = new Client({ name: "ts-client", version: "1.0.0" });
  await client.connect(new WebSocketClientTransport("ws://localhost:8765", { WebSocket }));

  const tools = await client.listTools();
  console.log("Discovered Tools:", tools.tools.map(t => t.name));

  const result = await client.callTool({ name: "add_numbers", arguments: { a: 25, b: 75 } });
  console.log("Tool Result:", result.content[0].text);

  await client.close();
}

main();
```

---

## 🌉 Desktop Host Bridge (`mcp-ws-bridge`)

To connect **Claude Desktop, LM Studio, Cursor, or Antigravity** to a running TypeScript WebSocket server:

```json
{
  "mcpServers": {
    "my-ts-websocket-tools": {
      "command": "bun",
      "args": [
        "run",
        "path/to/mcp-websocket/typescript/examples/stdio-to-websocket-bridge.ts",
        "--url",
        "ws://localhost:8765"
      ]
    }
  }
}
```

---

## 🧪 Testing & Build

```bash
# Build TypeScript
bun run build

# Run automated tests
bun run test
```

---

## 📄 License

MIT License.
