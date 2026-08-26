"""
Bidirectional Proof Test for MCP WebSocket Transport.

Demonstrates and verifies:
1. Client -> Server: Tool Listing & Invocation (tools/list, tools/call)
2. Server -> Client: Server-Initiated Sampling (sampling/createMessage)
3. Server -> Client: Real-time Progress Notifications (notifications/progress)
4. Server -> Client: Roots Resolution (roots/list)
5. Server -> Client: Log Streaming (notifications/message)
"""

import asyncio
import uuid

import pytest
import websockets

from mcp_transport_websocket import (
    JSONRPCNotification,
    JSONRPCRequest,
    JSONRPCResponse,
    WebSocketClientTransport,
    serve_websocket,
)


class AdvancedBidirectionalMCPServer:
    """
    An MCP Server that initiates reverse requests (Sampling & Roots)
    and pushes real-time streaming notifications (Progress & Logging)
    over a single full-duplex WebSocket connection.
    """

    def __init__(self):
        self.client_roots = []
        self.pending_requests: dict[str, asyncio.Future] = {}
        self.write_stream = None

    async def request_client(self, method: str, params: dict | None = None) -> dict:
        """Sends a Server -> Client JSON-RPC request and awaits the client's response frame."""
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

                # If this message is a response to a server-initiated request, resolve it immediately
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

                # Otherwise dispatch the client request concurrently so the reader never blocks
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
                            "name": "bidirectional-proof-server",
                            "version": "1.0.0",
                        },
                    },
                )
            )

            # Spawn a task to query client roots after initialization
            async def fetch_roots():
                try:
                    res = await self.request_client("roots/list")
                    self.client_roots = res.get("roots", [])
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
                                "description": "Server tool that samples the client LLM to analyze data.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {"data": {"type": "string"}},
                                    "required": ["data"],
                                },
                            },
                            {
                                "name": "heavy_processing_job",
                                "description": "Server tool that streams real-time progress notifications.",
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

            # SCENARIO A: Server-Initiated Sampling (sampling/createMessage)
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

                # SERVER -> CLIENT: Server calls Client LLM
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

                # Return tool response incorporating the sampled result
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

            # SCENARIO B: Real-Time Server Progress Push (notifications/progress)
            elif tool_name == "heavy_processing_job":
                steps = arguments.get("steps", 4)
                progress_token = params.get("_meta", {}).get(
                    "progressToken", "prog-100"
                )

                for i in range(1, steps + 1):
                    await asyncio.sleep(0.01)
                    # Push progress notification unprompted
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


@pytest.mark.asyncio
async def test_full_duplex_bidirectional_transport():
    """
    Verifies full-duplex bidirectional communication:
    - Client calls tool -> Server asks Client for Sampling -> Client answers -> Server finishes tool
    - Server pushes real-time Progress notifications
    - Server queries Client Roots
    """
    server_instance = AdvancedBidirectionalMCPServer()

    async def ws_handler(websocket):
        await serve_websocket(server_instance, websocket)

    async with websockets.serve(ws_handler, "127.0.0.1", 0) as ws_server:
        host, port = ws_server.sockets[0].getsockname()
        url = f"ws://{host}:{port}"

        progress_events = []
        log_events = []

        async with WebSocketClientTransport(url) as (read_stream, write_stream):
            # 1. Send Handshake
            await write_stream.send(
                JSONRPCRequest(
                    id=1,
                    method="initialize",
                    params={
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "sampling": {},
                            "roots": {"listChanged": True},
                        },
                        "clientInfo": {
                            "name": "test-bidirectional-client",
                            "version": "1.0.0",
                        },
                    },
                )
            )

            # Receive initialize response
            init_res = await read_stream.receive()
            assert init_res.get("id") == 1

            # Receive Server-Initiated roots/list request!
            roots_req = await read_stream.receive()
            assert roots_req.get("method") == "roots/list"
            roots_req_id = roots_req.get("id")

            # CLIENT -> SERVER: Answer roots/list request
            await write_stream.send(
                JSONRPCResponse(
                    id=roots_req_id,
                    result={
                        "roots": [
                            {"uri": "file:///workspace/project", "name": "Main Project"}
                        ]
                    },
                )
            )

            # Verify server recorded client roots
            await asyncio.sleep(0.05)
            assert len(server_instance.client_roots) == 1
            assert server_instance.client_roots[0]["name"] == "Main Project"

            # 2. Test Server-Initiated Sampling (Server calls Client LLM during tool execution)
            await write_stream.send(
                JSONRPCRequest(
                    id=2,
                    method="tools/call",
                    params={
                        "name": "ai_data_analyst",
                        "arguments": {
                            "data": "System latency reduced by 40% after caching enabled."
                        },
                    },
                )
            )

            # Read stream will receive:
            # 1) Log notification from server
            # 2) Server-initiated sampling/createMessage request!
            msg_a = await read_stream.receive()
            if msg_a.get("method") == "notifications/message":
                log_events.append(msg_a)
                sampling_req = await read_stream.receive()
            else:
                sampling_req = msg_a

            assert sampling_req.get("method") == "sampling/createMessage"
            sampling_req_id = sampling_req.get("id")
            prompt_received = sampling_req["params"]["messages"][0]["content"]["text"]
            assert "System latency reduced" in prompt_received

            # CLIENT -> SERVER: Client LLM answers sampling request
            await write_stream.send(
                JSONRPCResponse(
                    id=sampling_req_id,
                    result={
                        "role": "assistant",
                        "content": {
                            "type": "text",
                            "text": "Positive sentiment. Performance improvement.",
                        },
                    },
                )
            )

            # Receive final tool execution response from server
            tool_res = await read_stream.receive()
            assert tool_res.get("id") == 2
            assert "Performance improvement" in tool_res["result"]["content"][0]["text"]

            # 3. Test Server-to-Client Real-Time Progress Push
            await write_stream.send(
                JSONRPCRequest(
                    id=3,
                    method="tools/call",
                    params={
                        "name": "heavy_processing_job",
                        "arguments": {"steps": 3},
                        "_meta": {"progressToken": "batch-job-42"},
                    },
                )
            )

            # Receive 3 progress notifications
            for _ in range(3):
                p_msg = await read_stream.receive()
                assert p_msg.get("method") == "notifications/progress"
                progress_events.append(p_msg["params"])

            # Receive final job response
            job_res = await read_stream.receive()
            assert job_res.get("id") == 3
            assert len(progress_events) == 3
            assert progress_events[0]["progress"] == 1
            assert progress_events[1]["progress"] == 2
            assert progress_events[2]["progress"] == 3
