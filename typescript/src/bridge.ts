#!/usr/bin/env node
import readline from "node:readline";
import WebSocket from "ws";

/**
 * CLI Entrypoint for STDIO-to-WebSocket Bridge.
 * Usage:
 *   mcp-ws-bridge ws://localhost:8765
 *   npx mcp-websocket ws://localhost:8765
 */
export async function runBridge(targetUrl?: string): Promise<void> {
  const url = targetUrl || process.env.MCP_WS_URL || "ws://localhost:8765";
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
    process.stderr.write(
      `❌ [mcp-ws-bridge] Failed to connect to MCP WebSocket server at ${url}: ${err.message}\n` +
        "   Ensure your MCP WebSocket server is running before launching the host.\n",
    );
    process.exit(1);
  });

  ws.on("close", () => {
    process.exit(0);
  });
}

// Auto-run if executed directly as a script
if (
  import.meta.url === `file://${process.argv[1]}` ||
  process.argv[1]?.endsWith("mcp-ws-bridge")
) {
  let targetUrl: string | undefined;
  const args = process.argv.slice(2);
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--url" && i + 1 < args.length) {
      targetUrl = args[i + 1];
      break;
    } else if (!args[i].startsWith("-") && !targetUrl) {
      targetUrl = args[i];
    }
  }

  runBridge(targetUrl).catch((err) => {
    process.stderr.write(`Bridge fatal error: ${err.message}\n`);
    process.exit(1);
  });
}
