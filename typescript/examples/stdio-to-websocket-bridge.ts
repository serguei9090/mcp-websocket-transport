import readline from "node:readline";
import WebSocket from "ws";

/**
 * TypeScript STDIO-to-WebSocket Bridge for MCP Hosts.
 */
async function main() {
  const url = process.env.MCP_WS_URL || "ws://localhost:8765";
  const ws = new WebSocket(url);

  ws.on("open", () => {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      terminal: false,
    });

    rl.on("line", (line) => {
      if (line.trim() && ws.readyState === WebSocket.OPEN) {
        ws.send(line);
      }
    });

    rl.on("close", () => {
      ws.close();
    });
  });

  ws.on("message", (data) => {
    const text = data.toString();
    process.stdout.write(`${text}\n`);
  });

  ws.on("error", (err) => {
    process.stderr.write(`WebSocket error: ${err.message}\n`);
  });

  ws.on("close", () => {
    process.exit(0);
  });
}

main().catch((err) => {
  console.error("Bridge failed:", err);
  process.exit(1);
});
