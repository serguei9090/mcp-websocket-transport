import { runBridge } from "../src/bridge.js";

// Execute bridge with CLI arguments
const args = process.argv.slice(2);
let targetUrl: string | undefined;
for (let i = 0; i < args.length; i++) {
  if (args[i] === "--url" && i + 1 < args.length) {
    targetUrl = args[i + 1];
    break;
  } else if (!args[i].startsWith("-") && !targetUrl) {
    targetUrl = args[i];
  }
}

runBridge(targetUrl).catch((err) => {
  console.error("Bridge failed:", err);
  process.exit(1);
});
