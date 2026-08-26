"""
Bidirectional MCP WebSocket Server Example.

Exposes:
- `ai_data_analyst`: Triggers Server -> Client Sampling (`sampling/createMessage`)
- `heavy_processing_job`: Streams real-time Progress (`notifications/progress`)
- Roots Query: Queries Client Roots (`roots/list`) unprompted
"""

import asyncio
import os
import sys
import uuid

import websockets

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from mcp_websocket import (
    JSONRPCNotification,
    JSONRPCRequest,
    JSONRPCResponse,
    serve_websocket,
)


class AdvancedBidirectionalMCPServer:
    def __init__(self):
        self.client_roots = []
        self.pending_requests: dict[str, asyncio.Future] = {}
        self.write_stream = None

    async def request_client(self, method: str, params: dict | None = None) -> dict:
        """Sends a Server -> Client JSON-RPC request and awaits the client's response."""
        req_id = f"srv-{uuid.uuid4().hex[:6]}"
        fut = asyncio.get_running_loop().create_future()
        self.pending_requests[req_id] = fut
        await self.write_stream.send(
            JSONRPCRequest(id=req_id, method=method, params=params or {})
        )
        return await fut

    async def run(self, read_stream, write_stream):
        self.write_stream = write_stream
        async with asyncio.TaskGroup() as tg:
            async for msg in read_stream:
                if not isinstance(msg, dict):
                    continue

                msg_id = str(msg.get("id"))
                if msg_id in self.pending_requests and (
                    "result" in msg or "error" in msg
                ):
                    fut = self.pending_requests.pop(msg_id)
                    if not fut.done():
                        if "error" in msg and msg["error"]:
                            fut.set_exception(Exception(msg["error"]))
                        else:
                            fut.set_result(msg.get("result", {}))
                    continue

                tg.create_task(self.dispatch_client_message(msg, write_stream, tg))

    async def dispatch_client_message(self, msg: dict, write_stream, tg):
        method = msg.get("method")
        msg_id = msg.get("id")

        # 1. Handshake
        if method == "initialize":
            await write_stream.send(
                JSONRPCResponse(
                    id=msg_id,
                    result={
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {},
                            "logging": {},
                        },
                        "serverInfo": {
                            "name": "bidirectional-mcp-server",
                            "version": "1.0.0",
                        },
                    },
                )
            )

            # Query roots from client unprompted
            async def fetch_roots():
                try:
                    res = await self.request_client("roots/list")
                    self.client_roots = res.get("roots", [])
                    print(
                        f"   📂 [Server] Discovered Client Roots: {self.client_roots}"
                    )
                except Exception:
                    pass

            tg.create_task(fetch_roots())

        # 2. List tools
        elif method == "tools/list":
            await write_stream.send(
                JSONRPCResponse(
                    id=msg_id,
                    result={
                        "tools": [
                            {
                                "name": "ai_data_analyst",
                                "description": "Server tool that triggers reverse sampling to ask the Client LLM for analysis.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {"data": {"type": "string"}},
                                    "required": ["data"],
                                },
                            },
                            {
                                "name": "heavy_processing_job",
                                "description": "Server tool that streams progress notifications.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {"steps": {"type": "integer"}},
                                },
                            },
                        ]
                    },
                )
            )

        # 3. Call tool
        elif method == "tools/call":
            params = msg.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            # Server-Initiated Sampling (Server calls Client LLM)
            if tool_name == "ai_data_analyst":
                raw_data = arguments.get("data", "")

                # Send Log Notification
                await write_stream.send(
                    JSONRPCNotification(
                        method="notifications/message",
                        params={
                            "level": "info",
                            "logger": "analyst",
                            "data": f"Initiating reverse sampling request for: {raw_data}",
                        },
                    )
                )

                print(
                    f"\n⚡ [Server] Requesting AI Sampling from Client for: '{raw_data}'..."
                )
                client_ai_response = await self.request_client(
                    method="sampling/createMessage",
                    params={
                        "messages": [
                            {
                                "role": "user",
                                "content": {
                                    "type": "text",
                                    "text": f"Extract sentiment and key summary from: '{raw_data}'",
                                },
                            }
                        ],
                        "maxTokens": 100,
                    },
                )

                ai_text = client_ai_response.get("content", {}).get("text", "")
                print(f"⚡ [Server] Received Client LLM response: '{ai_text}'")

                await write_stream.send(
                    JSONRPCResponse(
                        id=msg_id,
                        result={
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Analysis complete via Client Sampling: {ai_text}",
                                }
                            ]
                        },
                    )
                )

            # Server Progress Notifications
            elif tool_name == "heavy_processing_job":
                steps = arguments.get("steps", 4)
                progress_token = params.get("_meta", {}).get(
                    "progressToken", "prog-100"
                )

                for i in range(1, steps + 1):
                    await asyncio.sleep(0.02)
                    await write_stream.send(
                        JSONRPCNotification(
                            method="notifications/progress",
                            params={
                                "progressToken": progress_token,
                                "progress": i,
                                "total": steps,
                            },
                        )
                    )

                await write_stream.send(
                    JSONRPCResponse(
                        id=msg_id,
                        result={
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Finished {steps} computation steps successfully.",
                                }
                            ]
                        },
                    )
                )


async def main():
    port = int(os.getenv("PORT", "8767"))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"🚀 Bidirectional MCP WebSocket Server listening on ws://{host}:{port}")

    async def ws_handler(websocket):
        server = AdvancedBidirectionalMCPServer()
        await serve_websocket(server, websocket)

    async with websockets.serve(ws_handler, host, port):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
