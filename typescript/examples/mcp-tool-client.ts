import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import WebSocket from "ws";
import { WebSocketClientTransport } from "../src/index.js";

async function run() {
  const serverUrl = "ws://localhost:8765";
  console.log(`🔌 Connecting to MCP Server at ${serverUrl}...`);

  const client = new Client(
    { name: "mcp-test-client", version: "1.0.0" },
    { capabilities: {} },
  );

  const transport = new WebSocketClientTransport(serverUrl, { WebSocket });
  await client.connect(transport);
  console.log("✅ Connected to MCP WebSocket Server!");

  // 1. List tools
  console.log("\n📋 Requesting available tools...");
  const toolsResponse = await client.listTools();
  console.log("Available Tools:", JSON.stringify(toolsResponse.tools, null, 2));

  // 2. Call add_numbers tool
  console.log("\n🧮 Calling 'add_numbers' tool (a: 42, b: 58)...");
  const addResult = await client.callTool({
    name: "add_numbers",
    arguments: { a: 42, b: 58 },
  });
  console.log("Tool Response:", addResult);

  // 3. Call get_system_info tool
  console.log("\n💻 Calling 'get_system_info' tool...");
  const sysResult = await client.callTool({
    name: "get_system_info",
    arguments: {},
  });
  console.log("Tool Response:", sysResult);

  // Close connection
  await client.close();
  console.log("\n👋 Connection closed.");
}

run().catch(console.error);
