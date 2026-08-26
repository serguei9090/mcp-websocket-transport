# 🧪 MCP WebSocket Transport: Complete Manual & Automated Testing Guide

This guide provides end-to-end instructions for testing the **`mcp-websocket`** packages across all layers:
1. **Automated Unit & Integration Tests** (Pytest & Bun/Node)
2. **Standalone Client-Server Execution** (Python & TypeScript)
3. **End-to-End Desktop Host Testing** (Antigravity, LM Studio / Gemma 4, Claude Desktop)
4. **Docker Multi-Container Testing** (`docker compose`)

---

## 📋 Table of Contents
- [1. Automated Unit & Integration Tests](#1-automated-unit--integration-tests)
  - [A. Python Test Suite](#a-python-test-suite)
  - [B. TypeScript Test Suite](#b-typescript-test-suite)
- [2. Standalone Client-Server Execution](#2-standalone-client-server-execution)
  - [A. Python Server & Client](#a-python-server--client)
  - [B. TypeScript Server & Client](#b-typescript-server--client)
- [3. End-to-End Testing with AI Hosts (Antigravity & LM Studio)](#3-end-to-end-testing-with-ai-hosts-antigravity--lm-studio)
  - [A. Testing with Google Antigravity](#a-testing-with-google-antigravity)
  - [B. Testing with LM Studio & Local Gemma Model](#b-testing-with-lm-studio--local-gemma-model)
- [4. Docker Multi-Container Testing](#4-docker-multi-container-testing)

---

## 1. Automated Unit & Integration Tests

Both language implementations include comprehensive test suites verifying:
- Client $\rightarrow$ Server: Tool Discovery (`tools/list`) and Execution (`tools/call`)
- Server $\rightarrow$ Client: Reverse Sampling (`sampling/createMessage`)
- Server $\rightarrow$ Client: Workspace Roots Query (`roots/list`)
- Server $\rightarrow$ Client: Real-time Progress Notifications (`notifications/progress`)
- Server $\rightarrow$ Client: Live Log Streaming (`notifications/message`)

### A. Python Test Suite

```bash
cd python
uv run --all-extras pytest -v -s
```

**Expected Output:**
```text
============================= test session starts =============================
platform win32 -- Python 3.13.3, pytest-9.1.1, pluggy-1.6.0
collected 2 items

tests/test_bidirectional_sampling_and_progress.py::test_full_duplex_bidirectional_transport PASSED [ 50%]
tests/test_transport.py::test_websocket_transport_roundtrip PASSED                                 [100%]

============================== 2 passed in 1.54s ==============================
```

---

### B. TypeScript Test Suite

```bash
cd typescript
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

=== Starting TypeScript Full-Duplex Bidirectional Test Suite ===

[TEST 1] Handshake & Reverse Roots Query...
   📥 [Client] Received Server-Initiated `roots/list` request!
✓ Test 1 Passed: Handshake and Server-Initiated Roots successful.

[TEST 2] Server-Initiated Sampling (Server calls Client LLM)...
   📥 [Client] Received Server-Initiated `sampling/createMessage` request!
✓ Test 2 Passed: Reverse Sampling roundtrip completed over WebSocket.

[TEST 3] Server Progress Notifications...
   📊 [Client] Received progress notification: 1/3
   📊 [Client] Received progress notification: 2/3
   📊 [Client] Received progress notification: 3/3
✓ Test 3 Passed: Real-time progress push verified.

=== All TypeScript Bidirectional Tests Passed 100%! ===
```

---

## 2. Standalone Client-Server Execution

### A. Python Server & Client

1. **Start Python Server (Terminal 1):**
   ```bash
   cd python
   uv run python examples/mcp_tool_server.py
   ```
   *Output: `[SERVER] Python MCP Tool Server listening on ws://0.0.0.0:8767`*

2. **Run Python Client (Terminal 2):**
   ```bash
   cd python
   uv run python examples/mcp_tool_client.py
   ```
   *Executes `calculate_bmi` and `reverse_string` over the WebSocket connection.*

---

### B. TypeScript Server & Client

1. **Start TypeScript Server (Terminal 1):**
   ```bash
   cd typescript
   bun run examples/mcp-tool-server.ts
   ```
   *Output: `🚀 TypeScript MCP WebSocket Tool Server listening on ws://0.0.0.0:8765`*

2. **Run TypeScript Client (Terminal 2):**
   ```bash
   cd typescript
   bun run examples/mcp-tool-client.ts
   ```
   *Executes `add_numbers` and `get_system_info` over the WebSocket connection.*

---

## 3. End-to-End Testing with AI Hosts (Antigravity & LM Studio)

Desktop MCP hosts communicate over standard I/O (`stdio`).  
Both packages include the **`mcp-ws-bridge`** CLI to seamlessly connect any desktop host to the live WebSocket server.

```
┌────────────────────────────────────────────────────────────┐
│          Antigravity / LM Studio / Claude Desktop          │
│                      (STDIO Interface)                     │
└─────────────────────────────┬──────────────────────────────┘
                              │ stdin / stdout
                              ▼
┌────────────────────────────────────────────────────────────┐
│                    `mcp-ws-bridge`                         │
│            (Transparent Auto-Retrying Pipe)                │
└─────────────────────────────┬──────────────────────────────┘
                              │ WebSocket (ws://)
                              ▼
┌────────────────────────────────────────────────────────────┐
│                 MCP WebSocket Server                       │
│    Python (ws://localhost:8767) | TS (ws://localhost:8765)  │
└────────────────────────────────────────────────────────────┘
```

---

### A. Testing with Google Antigravity

#### Step 1: Start the target WebSocket Server in your terminal
* For Python:
  ```bash
  cd python && uv run python examples/mcp_tool_server.py
  ```
* For TypeScript:
  ```bash
  cd typescript && bun run examples/mcp-tool-server.ts
  ```

#### Step 2: Add to Antigravity Configuration (`mcp_config.json`):
```json
{
  "mcpServers": {
    "websocket-python-tools": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "i:/01-Master_Code/Apps/MCP-WebSocket-Transport/python",
        "python",
        "examples/stdio_to_websocket_bridge.py",
        "--url",
        "ws://localhost:8767"
      ]
    },
    "websocket-ts-tools": {
      "command": "bun",
      "args": [
        "run",
        "i:/01-Master_Code/Apps/MCP-WebSocket-Transport/typescript/examples/stdio-to-websocket-bridge.ts",
        "--url",
        "ws://localhost:8765"
      ]
    }
  }
}
```

#### Step 3: Test in Antigravity Chat
Prompt the AI:
> *"Use the Python MCP tools to calculate the BMI for 75 kg and 1.78 m, and reverse the text 'Model Context Protocol'."*

**Result:** Antigravity executes the tools in real time and returns:
- `BMI: 23.67 (Normal weight)`
- `Reversed: 'locotorP txetnoC ledoM'`

---

### B. Testing with LM Studio & Local Gemma Model

1. Start your Python WebSocket server (`ws://0.0.0.0:8767`).
2. Add the same `websocket-python-tools` config to LM Studio's MCP settings.
3. In LM Studio, load your model (e.g. **`google/gemma-4-e2b`**).
4. Verify the MCP tools indicator shows green.
5. In the chat, send your prompt. Gemma will invoke the tools and display the structured tool call frames directly in the UI!

---

## 4. Docker Multi-Container Testing

To verify containerized execution:

1. **Launch Containers:**
   ```bash
   cd docker
   docker compose up --build -d
   ```

2. **Verify Running Ports:**
   - Python Server: `ws://localhost:8767`
   - TypeScript Server: `ws://localhost:8765`

3. **Test against Containers from Host:**
   ```bash
   # Test Python container
   cd python && uv run python examples/mcp_tool_client.py
   
   # Test TypeScript container
   cd typescript && bun run examples/mcp-tool-client.ts
   ```

4. **Stop Containers:**
   ```bash
   cd docker && docker compose down
   ```
