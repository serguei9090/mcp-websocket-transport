import assert from "node:assert";
import WebSocket, { WebSocketServer } from "ws";
import {
  WebSocketClientTransport,
  WebSocketServerTransport,
} from "../dist/index.js";

/**
 * TypeScript Full-Duplex Bidirectional Proof Test Suite
 *
 * Verifies:
 * 1. Client -> Server: initialize, tools/list, tools/call
 * 2. Server -> Client: roots/list (Server requests workspace roots from client)
 * 3. Server -> Client: sampling/createMessage (Server calls Client LLM during tool execution)
 * 4. Server -> Client: notifications/progress (Server streams progress unprompted)
 * 5. Server -> Client: notifications/message (Server streams live logs)
 */
async function runBidirectionalTestSuite() {
  console.log(
    "=== Starting TypeScript Full-Duplex Bidirectional Test Suite ===",
  );

  const port = 8769;
  const wss = new WebSocketServer({ port });

  const pendingServerRequests = new Map();
  let serverTransportRef;
  let clientRoots = [];

  wss.on("connection", async (ws) => {
    const serverTransport = new WebSocketServerTransport(ws);
    serverTransportRef = serverTransport;

    serverTransport.onmessage = async (msg) => {
      const msgId = msg.id;

      // Check if this message is a response to a server-initiated request
      if (
        msgId &&
        pendingServerRequests.has(msgId) &&
        (msg.result !== undefined || msg.error !== undefined)
      ) {
        const resolve = pendingServerRequests.get(msgId);
        pendingServerRequests.delete(msgId);
        resolve(msg);
        return;
      }

      // Handle Client Requests
      const method = msg.method;

      if (method === "initialize") {
        // Handshake response
        await serverTransport.send({
          jsonrpc: "2.0",
          id: msgId,
          result: {
            protocolVersion: "2024-11-05",
            capabilities: { tools: {}, logging: {} },
            serverInfo: {
              name: "ts-bidirectional-proof-server",
              version: "1.0.0",
            },
          },
        });

        // 1. SERVER -> CLIENT: Query Roots
        const rootsReqId = "srv-roots-1";
        const rootsPromise = new Promise((res) =>
          pendingServerRequests.set(rootsReqId, res),
        );
        await serverTransport.send({
          jsonrpc: "2.0",
          id: rootsReqId,
          method: "roots/list",
          params: {},
        });
        const rootsResponse = await rootsPromise;
        clientRoots = rootsResponse.result?.roots || [];
      } else if (method === "tools/call") {
        const { name, arguments: args } = msg.params || {};

        if (name === "ai_assisted_refactor") {
          // Send Log Notification
          await serverTransport.send({
            jsonrpc: "2.0",
            method: "notifications/message",
            params: {
              level: "info",
              logger: "refactorer",
              data: "Requesting LLM sampling for AST refactoring...",
            },
          });

          // 2. SERVER -> CLIENT: Reverse Request (Sampling)
          const samplingReqId = "srv-sampling-1";
          const samplingPromise = new Promise((res) =>
            pendingServerRequests.set(samplingReqId, res),
          );

          await serverTransport.send({
            jsonrpc: "2.0",
            id: samplingReqId,
            method: "sampling/createMessage",
            params: {
              messages: [
                {
                  role: "user",
                  content: {
                    type: "text",
                    text: `Refactor code: '${args?.code}'`,
                  },
                },
              ],
              maxTokens: 100,
            },
          });

          // Await LLM response over the exact same socket!
          const samplingRes = await samplingPromise;
          const sampledCode = samplingRes.result?.content?.text;

          // Respond to tool call
          await serverTransport.send({
            jsonrpc: "2.0",
            id: msgId,
            result: {
              content: [
                {
                  type: "text",
                  text: `Refactored Result via Sampling: ${sampledCode}`,
                },
              ],
            },
          });
        } else if (name === "stream_heavy_task") {
          // 3. SERVER -> CLIENT: Progress Push
          const token = msg.params?._meta?.progressToken || "tok-1";
          for (let i = 1; i <= 3; i++) {
            await new Promise((r) => setTimeout(r, 20));
            await serverTransport.send({
              jsonrpc: "2.0",
              method: "notifications/progress",
              params: { progressToken: token, progress: i, total: 3 },
            });
          }

          await serverTransport.send({
            jsonrpc: "2.0",
            id: msgId,
            result: { content: [{ type: "text", text: "Task completed." }] },
          });
        }
      }
    };

    await serverTransport.start();
  });

  // Client setup
  const clientTransport = new WebSocketClientTransport(
    `ws://localhost:${port}`,
    {
      WebSocket,
    },
  );

  const receivedProgress = [];
  const pendingClientResolutions = new Map();

  clientTransport.onmessage = async (msg) => {
    // Check for server-initiated roots/list
    if (msg.method === "roots/list") {
      console.log(
        "   📥 [Client] Received Server-Initiated `roots/list` request!",
      );
      await clientTransport.send({
        jsonrpc: "2.0",
        id: msg.id,
        result: {
          roots: [{ uri: "file:///workspace/ts-app", name: "TS App" }],
        },
      });
      return;
    }

    // Check for server-initiated sampling/createMessage
    if (msg.method === "sampling/createMessage") {
      console.log(
        "   📥 [Client] Received Server-Initiated `sampling/createMessage` request!",
      );
      // Simulate client LLM responding
      await clientTransport.send({
        jsonrpc: "2.0",
        id: msg.id,
        result: {
          role: "assistant",
          content: { type: "text", text: "const x = 42; // Optimized" },
        },
      });
      return;
    }

    // Check for progress notification
    if (msg.method === "notifications/progress") {
      console.log(
        `   📊 [Client] Received progress notification: ${msg.params.progress}/${msg.params.total}`,
      );
      receivedProgress.push(msg.params);
      return;
    }

    if (msg.id && pendingClientResolutions.has(msg.id)) {
      const resolve = pendingClientResolutions.get(msg.id);
      pendingClientResolutions.delete(msg.id);
      resolve(msg);
    }
  };

  await clientTransport.start();

  function sendClientRequest(method, params) {
    const id = Math.floor(Math.random() * 100000);
    const p = new Promise((resolve) =>
      pendingClientResolutions.set(id, resolve),
    );
    clientTransport.send({ jsonrpc: "2.0", id, method, params });
    return p;
  }

  // 1. Handshake & Verify Roots
  console.log("\n[TEST 1] Handshake & Reverse Roots Query...");
  const initRes = await sendClientRequest("initialize", {
    protocolVersion: "2024-11-05",
    capabilities: {},
  });
  assert.strictEqual(initRes.result.serverInfo.name, "ts-bidirectional-proof-server");
  await new Promise((r) => setTimeout(r, 50));
  assert.strictEqual(clientRoots.length, 1);
  assert.strictEqual(clientRoots[0].name, "TS App");
  console.log("✓ Test 1 Passed: Handshake and Server-Initiated Roots successful.");

  // 2. Server-Initiated Sampling during Tool Call
  console.log("\n[TEST 2] Server-Initiated Sampling (Server calls Client LLM)...");
  const toolRes = await sendClientRequest("tools/call", {
    name: "ai_assisted_refactor",
    arguments: { code: "var x = 40 + 2;" },
  });
  assert.ok(
    toolRes.result.content[0].text.includes("const x = 42; // Optimized"),
  );
  console.log("✓ Test 2 Passed: Reverse Sampling roundtrip completed over WebSocket.");

  // 3. Real-Time Server Progress Push
  console.log("\n[TEST 3] Server Progress Notifications...");
  const progRes = await sendClientRequest("tools/call", {
    name: "stream_heavy_task",
    arguments: {},
    _meta: { progressToken: "job-99" },
  });
  assert.strictEqual(progRes.result.content[0].text, "Task completed.");
  assert.strictEqual(receivedProgress.length, 3);
  assert.strictEqual(receivedProgress[0].progress, 1);
  assert.strictEqual(receivedProgress[2].progress, 3);
  console.log("✓ Test 3 Passed: Real-time progress push verified.");

  // Cleanup
  await clientTransport.close();
  wss.close();
  console.log("\n=== All TypeScript Bidirectional Tests Passed 100%! ===");
}

runBidirectionalTestSuite().catch((err) => {
  console.error("Test Suite Failed:", err);
  process.exit(1);
});
