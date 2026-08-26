"""
Interactive Live Demo: Progress Streaming & Reverse Roots Discovery.

Demonstrates:
1. [Server -> Client] Roots Discovery (`roots/list`): Server queries Client's workspace folders.
2. [Server -> Client] Progress Streaming (`notifications/progress`): Server pushes real-time progress bars.
3. [Server -> Client] Live Logging (`notifications/message`): Server streams log notifications unprompted.
"""

import asyncio
import sys
import websockets
from mcp_websocket import (
    JSONRPCNotification,
    JSONRPCRequest,
    JSONRPCResponse,
    WebSocketClientTransport,
    serve_websocket,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class DemoServer:
    def __init__(self):
        self.client_roots = []
        self.pending_client_requests = {}
        self.write_stream = None

    async def run(self, read_stream, write_stream):
        self.write_stream = write_stream
        async with asyncio.TaskGroup() as tg:
            async for msg in read_stream:
                if not isinstance(msg, dict):
                    continue

                msg_id = str(msg.get("id"))
                # If this is a response to a server-initiated request (roots/list)
                if msg_id in self.pending_client_requests and "result" in msg:
                    fut = self.pending_client_requests.pop(msg_id)
                    fut.set_result(msg["result"])
                    continue

                method = msg.get("method")
                req_id = msg.get("id")

                # Handshake
                if method == "initialize":
                    await write_stream.send(
                        JSONRPCResponse(
                            id=req_id,
                            result={
                                "protocolVersion": "2024-11-05",
                                "capabilities": {"tools": {}, "logging": {}},
                                "serverInfo": {"name": "progress-and-roots-demo", "version": "0.1.0"},
                            },
                        )
                    )

                    # SERVER -> CLIENT: Reverse query for Client Roots!
                    async def fetch_roots():
                        await asyncio.sleep(0.05)
                        print("   ⚡ [Server] Initiating Server -> Client reverse request: `roots/list`...")
                        fut = asyncio.get_running_loop().create_future()
                        self.pending_client_requests["srv-roots-1"] = fut
                        await write_stream.send(
                            JSONRPCRequest(id="srv-roots-1", method="roots/list", params={})
                        )
                        roots_res = await fut
                        self.client_roots = roots_res.get("roots", [])
                        print(f"   📂 [Server] Successfully discovered Client roots: {self.client_roots}\n")

                    tg.create_task(fetch_roots())

                # Tool call (triggers progress streaming)
                elif method == "tools/call":
                    params = msg.get("params", {})
                    tool_name = params.get("name")

                    if tool_name == "stream_download_task":
                        total_steps = 5
                        token = params.get("_meta", {}).get("progressToken", "dl-token-1")

                        # Send Log Notification
                        await write_stream.send(
                            JSONRPCNotification(
                                method="notifications/message",
                                params={"level": "info", "logger": "downloader", "data": "Starting 5-step data download..."},
                            )
                        )

                        # Stream Progress frames
                        for step in range(1, total_steps + 1):
                            await asyncio.sleep(0.4)  # Simulate work
                            await write_stream.send(
                                JSONRPCNotification(
                                    method="notifications/progress",
                                    params={"progressToken": token, "progress": step, "total": total_steps},
                                )
                            )

                        await write_stream.send(
                            JSONRPCResponse(
                                id=req_id,
                                result={"content": [{"type": "text", "text": "Download and indexing completed 100%!"}]},
                            )
                        )


def render_progress_bar(progress: int, total: int, width: int = 25):
    """Renders a live terminal progress bar."""
    percent = int((progress / total) * 100)
    filled = int(width * progress // total)
    bar = "█" * filled + "░" * (width - filled)
    sys.stdout.write(f"\r   📊 [Client Live Stream] [{bar}] {percent}% (Step {progress}/{total})")
    sys.stdout.flush()
    if progress == total:
        sys.stdout.write("\n")


async def run_demo():
    print("=" * 70)
    print("🚀 Live Demo: Progress Streaming & Reverse Roots Discovery over WebSocket")
    print("=" * 70)

    server = DemoServer()

    async def ws_handler(ws):
        await serve_websocket(server, ws)

    async with websockets.serve(ws_handler, "localhost", 8769):
        url = "ws://localhost:8769"

        async with WebSocketClientTransport(url) as (read_stream, write_stream):
            # 1. Client sends Handshake (declaring roots capability)
            print("\n1️⃣ [Handshake] Client connects and declares roots capability...")
            await write_stream.send(
                JSONRPCRequest(
                    id=1,
                    method="initialize",
                    params={
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"roots": {"listChanged": True}},
                        "clientInfo": {"name": "demo-client", "version": "0.1.0"},
                    },
                )
            )

            # Receive initialize response
            init_res = await read_stream.receive()
            print("   ✅ Handshake response received.")

            # 2. Receive Server-Initiated `roots/list` request!
            roots_req = await read_stream.receive()
            if roots_req.get("method") == "roots/list":
                print(f"   📥 [Client] Received Server-Initiated request: `roots/list` (id: {roots_req.get('id')})")
                print("   📤 [Client] Responding with open project directories...")
                await write_stream.send(
                    JSONRPCResponse(
                        id=roots_req.get("id"),
                        result={
                            "roots": [
                                {"uri": "file:///i:/01-Master_Code/Apps/MCP-WebSocket-Transport", "name": "MCP-WebSocket-Transport"},
                                {"uri": "file:///workspace/ai-agent", "name": "AI Agent Workspace"},
                            ]
                        },
                    )
                )

            await asyncio.sleep(0.2)

            # 3. Client calls heavy task and requests progress streaming
            print("\n2️⃣ [Client -> Server] Invoking tool `stream_download_task`...")
            await write_stream.send(
                JSONRPCRequest(
                    id=2,
                    method="tools/call",
                    params={
                        "name": "stream_download_task",
                        "_meta": {"progressToken": "download-job-42"},
                    },
                )
            )

            print("\n3️⃣ [Server -> Client] Streaming live progress & logs unprompted:")
            while True:
                msg = await read_stream.receive()
                if not isinstance(msg, dict):
                    continue

                method = msg.get("method")

                # Live Log Notification
                if method == "notifications/message":
                    print(f"   📢 [Log Notification]: {msg['params']['data']}")

                # Live Progress Notification
                elif method == "notifications/progress":
                    p = msg["params"]["progress"]
                    tot = msg["params"]["total"]
                    render_progress_bar(p, tot)

                # Final Tool Response
                elif msg.get("id") == 2:
                    print(f"\n4️⃣ [Result] Tool Completed: {msg['result']['content'][0]['text']}")
                    break

    print("\n🎉 Verification of Progress Streaming & Reverse Roots Discovery 100% Successful!")


if __name__ == "__main__":
    asyncio.run(run_demo())
