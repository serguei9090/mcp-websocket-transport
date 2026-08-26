import { WebSocket, WebSocketServer } from "ws";
import {
  WebSocketClientTransport,
  WebSocketServerTransport,
} from "../src/index.js";

/**
 * TypeScript Live Demo: Progress Streaming & Reverse Roots Discovery
 */
async function runDemo() {
  console.log("=".repeat(70));
  console.log(
    "🚀 TypeScript Demo: Progress Streaming & Reverse Roots Discovery",
  );
  console.log("=".repeat(70));

  const port = 8770;
  const wss = new WebSocketServer({ port });

  const pendingRequests = new Map();
  let clientRoots = [];

  wss.on("connection", async (ws) => {
    const serverTransport = new WebSocketServerTransport(ws);

    serverTransport.onmessage = async (msg: any) => {
      // Check if response to server-initiated request
      if (
        msg.id &&
        pendingRequests.has(msg.id) &&
        (msg.result !== undefined || msg.error !== undefined)
      ) {
        const resolve = pendingRequests.get(msg.id);
        pendingRequests.delete(msg.id);
        resolve(msg);
        return;
      }

      if (msg.method === "initialize") {
        await serverTransport.send({
          jsonrpc: "2.0",
          id: msg.id,
          result: {
            protocolVersion: "2024-11-05",
            capabilities: { tools: {}, logging: {} },
            serverInfo: { name: "ts-demo-server", version: "0.1.0" },
          },
        });

        // 1. SERVER -> CLIENT: Reverse query for Client Roots!
        setTimeout(async () => {
          console.log(
            "   ⚡ [Server] Initiating Server -> Client reverse request: `roots/list`...",
          );
          const rootsPromise = new Promise((res) =>
            pendingRequests.set("srv-roots-1", res),
          );
          await serverTransport.send({
            jsonrpc: "2.0",
            id: "srv-roots-1",
            method: "roots/list",
            params: {},
          });
          const rootsRes: any = await rootsPromise;
          clientRoots = rootsRes.result?.roots || [];
          console.log(
            `   📂 [Server] Successfully discovered Client roots:`,
            clientRoots,
            "\n",
          );
        }, 50);
      } else if (msg.method === "tools/call") {
        if (msg.params?.name === "heavy_computation_task") {
          const token = msg.params._meta?.progressToken || "job-token-1";
          const totalSteps = 5;

          // Send Log Notification
          await serverTransport.send({
            jsonrpc: "2.0",
            method: "notifications/message",
            params: {
              level: "info",
              logger: "computation",
              data: "Starting 5-step distributed task...",
            },
          });

          // Stream Progress frames unprompted
          for (let step = 1; step <= totalSteps; step++) {
            await new Promise((r) => setTimeout(r, 300));
            await serverTransport.send({
              jsonrpc: "2.0",
              method: "notifications/progress",
              params: {
                progressToken: token,
                progress: step,
                total: totalSteps,
              },
            });
          }

          await serverTransport.send({
            jsonrpc: "2.0",
            id: msg.id,
            result: {
              content: [
                {
                  type: "text",
                  text: "Heavy computation task completed with 100% success.",
                },
              ],
            },
          });
        }
      }
    };

    await serverTransport.start();
  });

  // Client side
  const clientTransport = new WebSocketClientTransport(
    `ws://localhost:${port}`,
    { WebSocket },
  );

  const pendingClientResolutions = new Map();

  function renderProgressBar(
    progress: number,
    total: number,
    width: number = 25,
  ) {
    const percent = Math.floor((progress / total) * 100);
    const filled = Math.floor((width * progress) / total);
    const bar = "█".repeat(filled) + "░".repeat(width - filled);
    process.stdout.write(
      `\r   📊 [Client Live Stream] [${bar}] ${percent}% (Step ${progress}/${total})`,
    );
    if (progress === total) {
      process.stdout.write("\n");
    }
  }

  clientTransport.onmessage = async (msg: any) => {
    // Check for Server -> Client roots request
    if (msg.method === "roots/list") {
      console.log(
        `   📥 [Client] Received Server-Initiated request: \`roots/list\` (id: ${msg.id})`,
      );
      console.log("   📤 [Client] Responding with open project directories...");
      await clientTransport.send({
        jsonrpc: "2.0",
        id: msg.id,
        result: {
          roots: [
            {
              uri: "file:///i:/01-Master_Code/Apps/MCP-WebSocket-Transport",
              name: "MCP-WebSocket-Transport",
            },
            {
              uri: "file:///workspace/node-app",
              name: "Node App Workspace",
            },
          ],
        },
      });
      return;
    }

    // Check for log notification
    if (msg.method === "notifications/message") {
      console.log(`   📢 [Log Notification]: ${msg.params.data}`);
      return;
    }

    // Check for progress notification
    if (msg.method === "notifications/progress") {
      renderProgressBar(msg.params.progress, msg.params.total);
      return;
    }

    if (msg.id && pendingClientResolutions.has(msg.id)) {
      const resolve = pendingClientResolutions.get(msg.id);
      pendingClientResolutions.delete(msg.id);
      resolve(msg);
    }
  };

  await clientTransport.start();

  // 1. Handshake
  console.log(
    "\n1️⃣ [Handshake] Client connects and declares roots capability...",
  );
  await new Promise((res) => {
    pendingClientResolutions.set(1, res);
    clientTransport.send({
      jsonrpc: "2.0",
      id: 1,
      method: "initialize",
      params: {
        protocolVersion: "2024-11-05",
        capabilities: { roots: { listChanged: true } },
        clientInfo: { name: "demo-ts-client", version: "0.1.0" },
      },
    });
  });
  console.log("   ✅ Handshake response received.");

  await new Promise((r) => setTimeout(r, 200));

  // 2. Call Tool
  console.log(
    "\n2️⃣ [Client -> Server] Invoking tool `heavy_computation_task`...",
  );
  console.log(
    "\n3️⃣ [Server -> Client] Streaming live progress & logs unprompted:",
  );
  const toolResult: any = await new Promise((res) => {
    pendingClientResolutions.set(2, res);
    clientTransport.send({
      jsonrpc: "2.0",
      id: 2,
      method: "tools/call",
      params: {
        name: "heavy_computation_task",
        _meta: { progressToken: "job-token-1" },
      },
    });
  });

  console.log(
    `\n4️⃣ [Result] Tool Completed: ${toolResult.result.content[0].text}`,
  );

  await clientTransport.close();
  wss.close();
  console.log(
    "\n🎉 TypeScript Progress Streaming & Roots Discovery 100% Successful!",
  );
}

runDemo().catch(console.error);
