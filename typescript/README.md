@modelcontextprotocol/transport-websocket
 

Full-duplex WebSocket Transport for the Model Context Protocol (MCP) in TypeScript, Node.js, and modern browser runtimes.


🚀 Why WebSocket Transport for MCP?
The standard Model Context Protocol (MCP) specifies two primary transports: stdio (for local CLI processes) and HTTP with SSE (Streamable HTTP / Server-Sent Events for remote connections).

While Streamable HTTP works across standard HTTP infrastructure, it introduces notable architectural tradeoffs:

Asymmetric Duplexing: Client-to-server requests go over standard HTTP POST requests, while server-to-client messages travel over long-lived SSE streams.
Connection & Session Reconnection Overhead: SSE drops require stateful session tokens, message replay buffers, or complex reconnection polling.
Firewall / Reverse Proxy Buffering: Some proxies aggressively buffer SSE chunks, delaying real-time tool execution or progress notifications.
🌟 WebSocket Advantages
True Full-Duplex Bi-Directional Streaming: Single TCP connection for requests, responses, notifications, progress streams, and server-initiated sampling.
Minimal Maintenance Surface (<50 LOC): Bridges raw WebSocket JSON-RPC frames directly into the official MCP SDK message pipeline.
Isomorphic Compatibility: Works in Node.js (via ws / isomorphic-ws), Bun, Deno, and standard Web Browsers.
Zero Polling Overhead: Instant bi-directional messaging with sub-millisecond overhead.


📦 Installation
# Using npm

npm install @modelcontextprotocol/transport-websocket @modelcontextprotocol/sdk ws

# Using bun

bun add @modelcontextprotocol/transport-websocket @modelcontextprotocol/sdk ws

# Using pnpm

pnpm add @modelcontextprotocol/transport-websocket @modelcontextprotocol/sdk ws


🛠️ Quickstart
1. TypeScript MCP Server (server.ts)
import { Server } from "@modelcontextprotocol/sdk/server/index.js";

import {

  CallToolRequestSchema,

  ListToolsRequestSchema,

} from "@modelcontextprotocol/sdk/types.js";

import { WebSocketServer } from "ws";

import { WebSocketServerTransport } from "@modelcontextprotocol/transport-websocket";

// 1. Initialize MCP Server

const server = new Server(

  { name: "ws-mcp-server", version: "1.0.0" },

  { capabilities: { tools: {} } }

);

// 2. Register MCP Tools

server.setRequestHandler(ListToolsRequestSchema, async () => ({

  tools: [

    {

      name: "ping",

      description: "Health check tool",

      inputSchema: { type: "object" },

    },

  ],

}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {

  if (request.params.name === "ping") {

    return { content: [{ type: "text", text: "pong" }] };

  }

  throw new Error(`Tool not found: ${request.params.name}`);

});

// 3. Start WebSocket Server

const wss = new WebSocketServer({ port: 8765 });

console.log("MCP WebSocket server running at ws://localhost:8765");

wss.on("connection", async (ws) => {

  console.log("Client connected");

  const transport = new WebSocketServerTransport(ws);

  await server.connect(transport);

});


2. TypeScript MCP Client (client.ts)
import { Client } from "@modelcontextprotocol/sdk/client/index.js";

import WebSocket from "ws";

import { WebSocketClientTransport } from "@modelcontextprotocol/transport-websocket";

async function run() {

  const client = new Client(

    { name: "ws-mcp-client", version: "1.0.0" },

    { capabilities: {} }

  );

  // In Node.js pass the 'ws' constructor; in browsers pass undefined

  const transport = new WebSocketClientTransport("ws://localhost:8765", {

    WebSocket,

  });

  await client.connect(transport);

  console.log("Connected to MCP server!");

  // List tools

  const tools = await client.listTools();

  console.log("Tools:", tools);

  // Call tool

  const result = await client.callTool({ name: "ping", arguments: {} });

  console.log("Result:", result);

  await client.close();

}

run().catch(console.error);


📖 API Reference
WebSocketClientTransport
Implements the official MCP Transport interface.

constructor(url: string | URL, options?: WebSocketClientOptions)

options.WebSocket: Custom WebSocket class (required in Node.js, e.g. import WebSocket from 'ws').
options.protocols: Subprotocol list string or array.
start(): Promise<void>: Connects to the server.
send(message: JSONRPCMessage): Promise<void>: Sends a message.
close(): Promise<void>: Closes the connection.
WebSocketServerTransport
Wraps an incoming server-side WebSocket client connection.

constructor(socket: any, options?: WebSocketServerTransportOptions)

start(): Promise<void>: Attaches event listeners to the socket.
send(message: JSONRPCMessage): Promise<void>: Sends a message to the client.
close(): Promise<void>: Closes the client connection.


🧪 Manual Testing
Run the included end-to-end test suite:

npm test


🚢 Publishing to npm
Follow these steps to publish to the official npm registry:
1. Build the Package
npm run build
2. Authenticate with npm
npm login
3. Verify Package Manifest
Ensure package.json contains:

Correct package name (@modelcontextprotocol/transport-websocket or mcp-websocket)
Correct semantic version (e.g. 1.0.0)
Valid repository, author, and license fields
4. Publish
# For scoped public packages:

npm publish --access public

# For unscoped packages:

npm publish


📄 License
MIT License.
