import os from "node:os";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { WebSocketServer } from "ws";
import { WebSocketServerTransport } from "../src/index.js";

// 1. Initialize MCP Server
const server = new Server(
  { name: "calculator-mcp-server", version: "1.0.0" },
  { capabilities: { tools: {} } },
);

// 2. Register MCP Tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "add_numbers",
      description: "Adds two numbers together and returns the sum.",
      inputSchema: {
        type: "object",
        properties: {
          a: { type: "number", description: "First number" },
          b: { type: "number", description: "Second number" },
        },
        required: ["a", "b"],
      },
    },
    {
      name: "get_system_info",
      description: "Returns host system information.",
      inputSchema: {
        type: "object",
        properties: {},
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "add_numbers") {
    const a = Number(args?.a ?? 0);
    const b = Number(args?.b ?? 0);
    const sum = a + b;
    return {
      content: [
        {
          type: "text",
          text: `Result: ${a} + ${b} = ${sum}`,
        },
      ],
    };
  }

  if (name === "get_system_info") {
    const info = {
      platform: os.platform(),
      architecture: os.arch(),
      cpus: os.cpus().length,
      uptime_seconds: Math.floor(os.uptime()),
    };
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(info, null, 2),
        },
      ],
    };
  }

  throw new Error(`Tool not found: ${name}`);
});

// 3. Start WebSocket Server
const port = 8765;
const wss = new WebSocketServer({ port });
console.log(`🚀 MCP WebSocket Tool Server listening on ws://localhost:${port}`);

wss.on("connection", async (ws) => {
  console.log("⚡ Client connected to MCP Server");
  const transport = new WebSocketServerTransport(ws);
  await server.connect(transport);
});
