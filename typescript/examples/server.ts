import { WebSocketServer } from "ws";
import { WebSocketServerTransport } from "../src/index.js";

const wss = new WebSocketServer({ port: 8765 });
console.log("TypeScript MCP WebSocket server running on ws://localhost:8765");

wss.on("connection", async (ws) => {
  console.log("Client connected to server");
  const transport = new WebSocketServerTransport(ws);

  transport.onmessage = (message) => {
    console.log("Received message:", message);
    if (
      message.jsonrpc === "2.0" &&
      "method" in message &&
      message.method === "ping"
    ) {
      transport.send({
        jsonrpc: "2.0",
        id: message.id,
        result: { status: "pong" },
      });
    }
  };

  transport.onerror = (err) => {
    console.error("Transport error:", err);
  };

  transport.onclose = () => {
    console.log("Connection closed");
  };

  await transport.start();
});
