import WebSocket from "ws";
import { WebSocketClientTransport } from "../src/index.js";

async function run() {
  const url = "ws://localhost:8765";
  console.log(`Connecting to ${url}...`);

  const transport = new WebSocketClientTransport(url, { WebSocket });

  transport.onmessage = (message) => {
    console.log("Client received message:", message);
  };

  await transport.start();
  console.log("Connected! Sending ping...");

  await transport.send({
    jsonrpc: "2.0",
    id: 1,
    method: "ping",
  });

  setTimeout(async () => {
    await transport.close();
    console.log("Client closed connection.");
  }, 1000);
}

run().catch(console.error);
