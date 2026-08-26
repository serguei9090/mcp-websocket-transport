"""
Real-case AI Agent connecting to an MCP Server over WebSocket Transport.

Demonstrates the complete AI Loop:
1. Connects to the MCP WebSocket server.
2. Performs the MCP handshake (initialize).
3. Discovers available tools dynamically (`tools/list`).
4. Converts MCP tools into LLM Function Calling format (OpenAI / Anthropic / Gemini format).
5. User asks a question ("What is the stock price of NVDA and what is 45 + 55?").
6. The AI decides which tool to call, generates arguments, and calls `tools/call` over WebSocket.
7. Displays the response.
"""

import asyncio
import json
import os
import sys

from mcp_websocket import JSONRPCRequest, WebSocketClientTransport

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class AIAgentWithMCPWebSocket:
    """An AI Agent that leverages an MCP WebSocket server for tool execution."""

    def __init__(self, server_url: str):
        self.server_url = server_url
        self.tools = []
        self._msg_id = 0

    def _next_id(self) -> int:
        self._msg_id += 1
        return self._msg_id

    async def run(self, user_query: str):
        print(f"🤖 [AI Agent] Starting session with server at {self.server_url}")
        print(f'💬 [User Query]: "{user_query}"\n')

        async with WebSocketClientTransport(self.server_url) as (
            read_stream,
            write_stream,
        ):
            # Step 1: MCP Handshake
            print("1️⃣ [AI Agent] Initializing MCP connection...")
            await write_stream.send(
                JSONRPCRequest(
                    id=self._next_id(),
                    method="initialize",
                    params={
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"roots": {"listChanged": True}},
                        "clientInfo": {
                            "name": "ai-mcp-websocket-agent",
                            "version": "1.0.0",
                        },
                    },
                )
            )
            init_resp = await read_stream.receive()
            server_info = init_resp.get("result", {}).get("serverInfo", {})
            print(
                f"   Connected to: {server_info.get('name')} (v{server_info.get('version')})"
            )

            # Acknowledge initialization
            await write_stream.send(
                {"jsonrpc": "2.0", "method": "notifications/initialized"}
            )

            # Step 2: Tool Discovery
            print("\n2️⃣ [AI Agent] Discovering available tools from MCP server...")
            await write_stream.send(
                JSONRPCRequest(id=self._next_id(), method="tools/list")
            )
            tools_resp = await read_stream.receive()
            self.tools = tools_resp.get("result", {}).get("tools", [])

            print(f"   Found {len(self.tools)} tools:")
            for tool in self.tools:
                print(
                    f"   - {tool['name']}: {tool.get('description', 'No description')}"
                )

            # Step 3: AI Reasoning & Tool Planning
            print("\n3️⃣ [AI Agent] Parsing query & planning tool calls...")

            # In production, you pass `self.tools` to OpenAI/Claude/Gemini API:
            # response = client.chat.completions.create(model="gpt-4o", messages=[...], tools=mcp_to_openai_tools(self.tools))
            # Here we simulate the LLM's function call decision based on the user prompt:
            planned_calls = []
            if "stock" in user_query.lower() or "nvda" in user_query.lower():
                planned_calls.append(
                    {"name": "get_stock_price", "arguments": {"symbol": "NVDA"}}
                )
            if "+" in user_query or "add" in user_query.lower():
                planned_calls.append(
                    {"name": "add_numbers", "arguments": {"a": 45.0, "b": 55.0}}
                )

            # Step 4: Execute Tool Calls over WebSocket
            print("\n4️⃣ [AI Agent] Executing tool calls over WebSocket transport...")
            tool_results = []
            for call in planned_calls:
                tool_name = call["name"]
                args = call["arguments"]
                call_id = self._next_id()

                print(
                    f"   📤 Sending `tools/call` for '{tool_name}' with args {json.dumps(args)}..."
                )
                await write_stream.send(
                    JSONRPCRequest(
                        id=call_id,
                        method="tools/call",
                        params={"name": tool_name, "arguments": args},
                    )
                )

                response = await read_stream.receive()
                result_content = response.get("result", {}).get("content", [])
                tool_results.append(
                    {
                        "tool": tool_name,
                        "args": args,
                        "result": result_content,
                    }
                )
                print(f"   📥 Received result: {json.dumps(result_content)}")

            # Step 5: Synthesize Final AI Answer
            print("\n5️⃣ [AI Agent] Synthesizing final answer:")
            print("-" * 50)
            print(
                f"Based on the tools executed via MCP WebSocket server:\n"
                f"- NVDA Stock Price: ${tool_results[0]['result'] if len(tool_results) > 0 else 'N/A'}\n"
                f"- Calculation (45 + 55): {tool_results[1]['result'] if len(tool_results) > 1 else 'N/A'}"
            )
            print("-" * 50)


async def main():
    port = int(os.getenv("PORT", "8765"))
    agent = AIAgentWithMCPWebSocket(server_url=f"ws://localhost:{port}")
    await agent.run("What is the real-time stock price of NVDA and what is 45 + 55?")


if __name__ == "__main__":
    asyncio.run(main())
