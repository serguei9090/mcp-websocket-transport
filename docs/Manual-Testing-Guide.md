# MCP WebSocket Transport: Manual Testing & Verification Guide

This guide covers:
1. **Testing with `mcp dev` (Official MCP Inspector)**
2. **Connecting a Real-Case AI Agent to your MCP Server over WebSocket**
3. **Running the TypeScript and Python test suites**

---

## 1. How to Test with `mcp dev` (Official MCP Inspector)

The official `mcp dev` command launches the **MCP Inspector** web UI, allowing you to visually inspect tools, schemas, resources, and execute tool calls interactively.

### Option A: Testing FastMCP Server with `mcp dev`
We created [`python/examples/fastmcp_server.py`](file:///i:/01-Master_Code/Apps/MCP-WebSocket-Transport/python/examples/fastmcp_server.py), which supports both `mcp dev` (stdio) and live WebSocket server modes.

Run the inspector:
```bash
cd python
uv run --with "mcp[cli]" mcp dev examples/fastmcp_server.py
```

**What happens:**
1. MCP Inspector starts a local web server (usually at `http://localhost:5173`).
2. Open the URL in your browser.
3. You will see all registered tools (`add_numbers`, `get_stock_price`, `summarize_text`).
4. You can click **"Call Tool"**, enter parameters, and view the response directly in the UI.

---

## 2. Real-Case Test: Connecting an AI Agent over WebSocket

This simulates the real-world production workflow where an AI model (OpenAI / Claude / Gemini / Local LLM) connects to your remote MCP server via WebSocket, discovers tools, and invokes them.

```
┌───────────────────────────────────────────────────────────┐
│                      AI Client / Agent                    │
│ 1. Connects to ws://localhost:8765                        │
│ 2. Handshake (`initialize`)                               │
│ 3. Fetches tools (`tools/list`)                           │
│ 4. LLM decides tool + args: `get_stock_price(NVDA)`       │
│ 5. Executes `tools/call` over WebSocket                   │
└─────────────────────────────┬─────────────────────────────┘
                              │
                    WebSocket │ Full-Duplex
                              │ JSON-RPC 2.0
                              ▼
┌───────────────────────────────────────────────────────────┐
│                  MCP WebSocket Server                     │
│ 1. Receives `tools/call`                                  │
│ 2. Executes Python/TS function                            │
│ 3. Streams result back over WebSocket                     │
└───────────────────────────────────────────────────────────┘
```

### Python Real-Case AI Test

#### Step 1: Start the MCP Server on WebSocket
```bash
cd python
uv run --with "mcp[cli]" python examples/fastmcp_server.py --ws
```
*Output:*
```text
🚀 FastMCP Server running over WebSocket on ws://localhost:8765
```

#### Step 2: Run the AI Agent Client
In a second terminal:
```bash
cd python
uv run python examples/ai_mcp_agent.py
```
*Output:*
```text
🤖 [AI Agent] Starting session with server at ws://localhost:8765
💬 [User Query]: "What is the real-time stock price of NVDA and what is 45 + 55?"

1️⃣ [AI Agent] Initializing MCP connection...
   Connected to: calculator-and-data-server (v1.0.0)

2️⃣ [AI Agent] Discovering available tools from MCP server...
   Found 3 tools:
   - add_numbers: Adds two numbers together and returns the sum.
   - get_stock_price: Fetches real-time stock price data for a ticker symbol.
   - summarize_text: Summarizes input text to a concise headline.

3️⃣ [AI Agent] Parsing query & planning tool calls...

4️⃣ [AI Agent] Executing tool calls over WebSocket transport...
   📤 Sending `tools/call` for 'get_stock_price' with args {"symbol": "NVDA"}...
   📥 Received result: [{"type": "text", "text": "{\"symbol\": \"NVDA\", \"price\": 128.9, \"currency\": \"USD\"}"}]
   📤 Sending `tools/call` for 'add_numbers' with args {"a": 45.0, "b": 55.0}...
   📥 Received result: [{"type": "text", "text": "100.0"}]

5️⃣ [AI Agent] Synthesizing final answer:
--------------------------------------------------
Based on the tools executed via MCP WebSocket server:
- NVDA Stock Price: $128.90 USD
- Calculation (45 + 55): 100.0
--------------------------------------------------
```

---

### TypeScript Real-Case AI Test

#### Step 1: Start the TypeScript MCP Server
```bash
cd typescript
bun run examples/mcp-tool-server.ts
```

#### Step 2: Run the TypeScript AI Client
In a second terminal:
```bash
cd typescript
bun run examples/ai-mcp-agent.ts
```

---

## 3. Connecting to External MCP Clients (Claude Desktop / Antigravity)

To connect standard MCP client apps to a WebSocket MCP Server:

### Configuration in `claude_desktop_config.json`:
Because standard desktop apps use `stdio` out of the box, you can use the WebSocket client as a bridge command:

```json
{
  "mcpServers": {
    "remote-websocket-tools": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "i:/01-Master_Code/Apps/MCP-WebSocket-Transport/python",
        "examples/mcp_tool_client.py"
      ]
    }
  }
}
```
Or connect directly from any custom agent using `WebSocketClientTransport("ws://localhost:8765")`.
