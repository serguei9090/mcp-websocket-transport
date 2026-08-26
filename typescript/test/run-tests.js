import assert from "node:assert";
import WebSocket, { WebSocketServer } from "ws";
import {
  WebSocketClientTransport,
  WebSocketServerTransport,
} from "../dist/index.js";

async function runTestSuite() {
  console.log("=== Starting TypeScript MCP WebSocket Transport Test Suite ===");

  const port = 8766;
  const wss = new WebSocketServer({ port });

  let serverTransport;
  const serverConnected = new Promise((resolve) => {
    wss.on("connection", async (ws) => {
      serverTransport = new WebSocketServerTransport(ws);
      serverTransport.onmessage = (message) => {
        if (message.method === "ping") {
          serverTransport.send({
            jsonrpc: "2.0",
            id: message.id,
            result: { pong: true },
          });
        } else if (message.method === "echo") {
          serverTransport.send({
            jsonrpc: "2.0",
            id: message.id,
            result: message.params,
          });
        }
      };
      await serverTransport.start();
      resolve(serverTransport);
    });
  });

  const clientTransport = new WebSocketClientTransport(
    `ws://localhost:${port}`,
    {
      WebSocket,
    },
  );

  const receivedMessages = [];
  clientTransport.onmessage = (msg) => {
    receivedMessages.push(msg);
  };

  await clientTransport.start();
  await serverConnected;

  // Test 1: Ping Request / Response
  console.log("Test 1: Sending Ping request...");
  await clientTransport.send({ jsonrpc: "2.0", id: 1, method: "ping" });
  await new Promise((r) => setTimeout(r, 200));

  assert.strictEqual(receivedMessages.length, 1);
  assert.strictEqual(receivedMessages[0].id, 1);
  assert.strictEqual(receivedMessages[0].result.pong, true);
  console.log("✓ Test 1 Passed: Ping roundtrip successful");

  // Test 2: Echo Request with Params
  console.log("Test 2: Sending Echo request...");
  await clientTransport.send({
    jsonrpc: "2.0",
    id: 2,
    method: "echo",
    params: { text: "Hello MCP WebSocket!" },
  });
  await new Promise((r) => setTimeout(r, 200));

  assert.strictEqual(receivedMessages.length, 2);
  assert.strictEqual(receivedMessages[1].id, 2);
  assert.strictEqual(receivedMessages[1].result.text, "Hello MCP WebSocket!");
  console.log("✓ Test 2 Passed: Echo roundtrip successful");

  // Cleanup
  await clientTransport.close();
  wss.close();
  console.log("=== All TypeScript Tests Passed Successfully! ===");
}

runTestSuite().catch((err) => {
  console.error("Test Suite Failed:", err);
  process.exit(1);
});
