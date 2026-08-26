# MCP WebSocket Transport: Manual Testing & Verification Guide

This guide walks you through verifying both the **TypeScript (Node.js/Bun)** and **Python (uv/websockets/FastAPI)** implementations of the WebSocket Transport for Model Context Protocol (MCP).

---

## 📋 Table of Contents
1. [Prerequisites & Tooling](#1-prerequisites--tooling)
2. [TypeScript / Node.js Manual Testing](#2-typescript--nodejs-manual-testing)
   - [A. Automated Unit Test Verification](#a-automated-unit-test-verification)
   - [B. Interactive Tool Server & Client Test](#b-interactive-tool-server--client-test)
   - [C. Low-level JSON-RPC Ping-Pong Test](#c-low-level-json-rpc-ping-pong-test)
3. [Python Manual Testing](#3-python-manual-testing)
   - [A. Automated Unit Test Verification](#a-automated-unit-test-verification-1)
   - [B. Interactive Tool Server & Client Test](#b-interactive-tool-server--client-test-1)
   - [C. FastAPI / Starlette WebSocket Test](#c-fastapi--starlette-websocket-test)
4. [Cross-Language Interoperability Test (TS Client ⟷ Python Server)](#4-cross-language-interoperability-test)
5. [Pre-Publish Registry Dry-Run Checklist](#5-pre-publish-registry-dry-run-checklist)

---

## 1. Prerequisites & Tooling

Ensure the following tools are available in your terminal:
- **Bun**: For building and executing TypeScript scripts (`bun run`, `bun test`)
- **Node.js**: v18+ (optional runtime)
- **uv**: For running Python isolated environments (`uv run`)
- **Biome**: Pre-installed globally for TS formatting/linting
- **Ruff**: Integrated with `uv` for Python formatting/linting

---

## 2. TypeScript / Node.js Manual Testing

Navigate to the `typescript` directory:
```bash
cd typescript
```

### A. Automated Unit Test Verification
Run the unit test suite that validates handshake, ping-pong, and echo messaging:
```bash
# Build the TypeScript dist output first
bun run build

# Execute the test suite
bun run test
```
**Expected Output:**
```text
=== Starting TypeScript MCP WebSocket Transport Test Suite ===
Test 1: Sending Ping request...
✓ Test 1 Passed: Ping roundtrip successful
Test 2: Sending Echo request...
✓ Test 2 Passed: Echo roundtrip successful
=== All TypeScript Tests Passed Successfully! ===
```

---

### B. Interactive Tool Server & Client Test
This tests full integration with `@modelcontextprotocol/sdk` (tool registration, schema validation, and tool invocation).

#### Step 1: Start the MCP WebSocket Tool Server (Terminal 1)
```bash
bun run examples/mcp-tool-server.ts
```
**Expected Output:**
```text
🚀 MCP WebSocket Tool Server listening on ws://localhost:8765
```

#### Step 2: Run the MCP WebSocket Tool Client (Terminal 2)
```bash
bun run examples/mcp-tool-client.ts
```
**Expected Output:**
```text
🔌 Connecting to MCP Server at ws://localhost:8765...
✅ Connected to MCP WebSocket Server!

📋 Requesting available tools...
Available Tools: [
  {
    "name": "add_numbers",
    "description": "Adds two numbers together and returns the sum.",
    "inputSchema": { ... }
  },
  {
    "name": "get_system_info",
    "description": "Returns host system information.",
    "inputSchema": { ... }
  }
]

🧮 Calling 'add_numbers' tool (a: 42, b: 58)...
Tool Response: {
  content: [ { type: 'text', text: 'Result: 42 + 58 = 100' } ]
}

💻 Calling 'get_system_info' tool...
Tool Response: {
  content: [
    {
      type: 'text',
      text: '{\n  "platform": "win32",\n  "architecture": "x64",\n  "cpus": 16,\n  "uptime_seconds": 123456\n}'
    }
  ]
}

👋 Connection closed.
```

---

### C. Low-level JSON-RPC Ping-Pong Test

#### Terminal 1:
```bash
bun run examples/server.ts
```
#### Terminal 2:
```bash
bun run examples/client.ts
```

---

## 3. Python Manual Testing

Navigate to the `python` directory:
```bash
cd python
```

### A. Automated Unit Test Verification
Run pytest via `uv`:
```bash
uv run --all-extras pytest -v
```
**Expected Output:**
```text
tests/test_transport.py::test_websocket_transport_roundtrip PASSED [100%]
============================== 1 passed in 0.43s ==============================
```

---

### B. Interactive Tool Server & Client Test
Tests the Python AnyIO WebSocket transport with `calculate_bmi` and `reverse_string` tools.

#### Step 1: Start the Python MCP Tool Server (Terminal 1)
```bash
uv run examples/mcp_tool_server.py
```
**Expected Output:**
```text
[SERVER] Python MCP Tool Server listening on ws://localhost:8767
```

#### Step 2: Run the Python MCP Tool Client (Terminal 2)
```bash
uv run examples/mcp_tool_client.py
```
**Expected Output:**
```text
[CLIENT] Connecting Python Client to ws://localhost:8767...
[CLIENT] Connected to Python MCP WebSocket Server!

[CLIENT] Initializing handshake...
Server Info: {'name': 'python-mcp-tool-server', 'version': '1.0.0'}

[CLIENT] Listing available tools...
Available Tools: [
  {
    "name": "calculate_bmi",
    "description": "Calculates Body Mass Index given weight (kg) and height (m)."
  },
  {
    "name": "reverse_string",
    "description": "Reverses an input string."
  }
]

[CLIENT] Calling 'calculate_bmi' (weight_kg: 75, height_m: 1.78)...
Result: [{'type': 'text', 'text': 'BMI: 23.67 (Normal weight)'}]

[CLIENT] Calling 'reverse_string' (text: 'Model Context Protocol')...
Result: [{'type': 'text', 'text': "Reversed: 'locotorP txetnoC ledoM'"}]

[CLIENT] Disconnecting client.
```

---

### C. FastAPI / Starlette WebSocket Test
Verifies integration with standard ASGI frameworks (`Starlette` / `FastAPI`).

#### Terminal 1: Start FastAPI Server
```bash
uv run examples/fastapi_server.py
```
**Expected Output:**
```text
Uvicorn running on http://127.0.0.1:8000 (WebSocket endpoint: ws://127.0.0.1:8000/ws)
```

#### Terminal 2: Run Client against FastAPI endpoint
```bash
uv run examples/client.py
```

---

## 4. Cross-Language Interoperability Test

Because WebSocket Transport standardizes on JSON-RPC 2.0 framing, you can mix and match clients and servers across languages:

```
┌─────────────────────────────────┐           ┌─────────────────────────────────┐
│     TypeScript MCP Client       │  ◄═════►  │      Python MCP Server          │
│   (mcp-transport-websocket)     │    ws     │   (mcp-transport-websocket)     │
└─────────────────────────────────┘           └─────────────────────────────────┘
```

1. Start Python Server on port `8767`:
   ```bash
   uv run examples/mcp_tool_server.py
   ```
2. Connect using TypeScript Client:
   ```bash
   bun run -e '
     import WebSocket from "ws";
     import { WebSocketClientTransport } from "./src/index.ts";
     const transport = new WebSocketClientTransport("ws://localhost:8767", { WebSocket });
     await transport.start();
     transport.onmessage = (msg) => console.log("Received from Python Server:", msg);
     await transport.send({ jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: "2024-11-05", capabilities: {}, clientInfo: { name: "ts-client", version: "1.0.0" } } });
   '
   ```

---

## 5. Pre-Publish Registry Dry-Run Checklist

Before publishing to **npm** and **PyPI**:

### TypeScript (`typescript/`):
- [x] Package name updated in `package.json` to valid unreserved name/scope (`mcp-transport-websocket`).
- [x] Biome formatting clean: `biome check --write typescript/`
- [x] Build output ready: `bun run build`
- [ ] Dry-run publish:
  ```bash
  npm publish --dry-run
  ```

### Python (`python/`):
- [x] `requires-python = ">=3.10"` configured in `pyproject.toml`.
- [x] Ruff lint & format clean: `uv run ruff check --fix` and `uv run ruff format`
- [x] Tests passing: `uv run --all-extras pytest`
- [ ] Build distributions:
  ```bash
  uv build
  ```
- [ ] Dry-run / staging check:
  ```bash
  uv publish --dry-run
  # or upload to TestPyPI
  # twine upload --repository testpypi dist/*
  ```
