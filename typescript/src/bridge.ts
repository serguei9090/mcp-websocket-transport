#!/usr/bin/env node
import readline from "node:readline";
import WebSocket from "ws";

/**
 * CLI Entrypoint for STDIO-to-WebSocket Bridge.
 * Usage:
 *   mcp-ws-bridge ws://localhost:8765
 *   mcp-ws-bridge --url ws://localhost:8765
 */
export async function runBridge(
  targetUrl?: string,
  retries = 3,
  retryDelay = 1000,
): Promise<void> {
  const url = targetUrl || process.env.MCP_WS_URL || "ws://localhost:8765";

  let ws: WebSocket | null = null;

  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      ws = await new Promise<WebSocket>((resolve, reject) => {
        const socket = new WebSocket(url);
        const onErr = (err: any) => {
          socket.removeAllListeners();
          try {
            socket.terminate();
          } catch {}
          reject(err);
        };
        const onOp = () => {
          socket.removeListener("error", onErr);
          resolve(socket);
        };
        socket.once("error", onErr);
        socket.once("open", onOp);
      });
      break;
    } catch (err: any) {
      if (attempt < retries) {
        process.stderr.write(
          `⏳ [mcp-ws-bridge] Waiting for server at ${url} (attempt ${attempt}/${retries})...\n`,
        );
        await new Promise((r) => setTimeout(r, retryDelay));
      } else {
        process.stderr.write(
          `❌ [mcp-ws-bridge] Connection refused at ${url}: ${err.message}\n` +
            "   💡 Start your TypeScript server first: 'bun run examples/mcp-tool-server.ts'\n",
        );
        process.exit(1);
      }
    }
  }

  if (!ws) {
    process.exit(1);
  }

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false,
  });

  rl.on("line", (line) => {
    if (line.trim() && ws && ws.readyState === WebSocket.OPEN) {
      ws.send(line);
    }
  });

  rl.on("close", () => {
    if (ws) ws.close();
  });

  ws.on("message", (data) => {
    const text = data.toString();
    process.stdout.write(`${text}\n`);
  });

  ws.on("error", (err) => {
    process.stderr.write(`[mcp-ws-bridge] Socket error: ${err.message}\n`);
    process.exit(1);
  });

  ws.on("close", () => {
    process.exit(0);
  });
}

// Auto-run if executed directly as a script
if (
  import.meta.url === `file://${process.argv[1]}` ||
  process.argv[1]?.endsWith("mcp-ws-bridge") ||
  process.argv[1]?.endsWith("bridge.js") ||
  process.argv[1]?.endsWith("bridge.ts") ||
  process.argv[1]?.endsWith("stdio-to-websocket-bridge.ts")
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
