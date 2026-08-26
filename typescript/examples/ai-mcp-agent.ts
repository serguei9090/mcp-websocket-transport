import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import WebSocket from "ws";
import { WebSocketClientTransport } from "../src/index.js";

/**
 * Real-case AI Agent in TypeScript connecting over WebSocket Transport.
 */
async function main() {
  const port = process.env.PORT || 8765;
  const serverUrl = `ws://localhost:${port}`;
  const userQuery = "What is the system information and what is 42 + 58?";

  console.log(`🤖 [AI Agent] Starting session with server at ${serverUrl}`);
  console.log(`💬 [User Query]: "${userQuery}"\n`);

  // 1. Initialize MCP Client with WebSocket Transport
  const client = new Client(
    { name: "ai-ts-websocket-agent", version: "1.0.0" },
    { capabilities: {} },
  );

  const transport = new WebSocketClientTransport(serverUrl, { WebSocket });
  await client.connect(transport);
  console.log("1️⃣ [AI Agent] Connected & Initialized MCP session.");

  // 2. Discover Tools Dynamically
  console.log("\n2️⃣ [AI Agent] Discovering tools...");
  const { tools } = await client.listTools();
  console.log(`   Found ${tools.length} available tools:`);
  for (const t of tools) {
    console.log(`   - ${t.name}: ${t.description}`);
  }

  // 3. AI Planning (Maps user intent to available tools)
  console.log("\n3️⃣ [AI Agent] Planning tool invocations...");
  const plannedCalls: Array<{ name: string; args: Record<string, unknown> }> =
    [];

  if (userQuery.includes("+") || userQuery.toLowerCase().includes("add")) {
    plannedCalls.push({ name: "add_numbers", args: { a: 42, b: 58 } });
  }
  if (userQuery.toLowerCase().includes("system")) {
    plannedCalls.push({ name: "get_system_info", args: {} });
  }

  // 4. Execute Tools over WebSocket
  console.log("\n4️⃣ [AI Agent] Invoking tools over WebSocket transport...");
  for (const call of plannedCalls) {
    console.log(
      `   📤 Calling '${call.name}' with ${JSON.stringify(call.args)}...`,
    );
    const result = await client.callTool({
      name: call.name,
      arguments: call.args,
    });
    console.log(`   📥 Result:`, result.content);
  }

  // 5. Cleanup
  await client.close();
  console.log("\n5️⃣ [AI Agent] Closed connection cleanly.");
}

main().catch(console.error);
