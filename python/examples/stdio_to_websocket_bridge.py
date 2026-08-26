"""
STDIO-to-WebSocket Bridge for Model Context Protocol (MCP).

Allows ANY standard MCP Host (Antigravity, Claude Desktop, Cursor, MCP Inspector)
to communicate with a remote or Dockerized MCP WebSocket server.

Flow:
[Antigravity / Claude Desktop] (stdin/stdout)
           ▲
           │
[stdio_to_websocket_bridge.py]
           │
           ▼
(WebSocket ws://localhost:8767)
[Remote / Docker MCP Server]
"""

import argparse
import asyncio
import os
import sys

import websockets

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")


async def pipe_stdin_to_ws(ws):
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    while True:
        line = await reader.readline()
        if not line:
            break
        text = line.decode("utf-8").strip()
        if text:
            await ws.send(text)


async def pipe_ws_to_stdout(ws):
    async for msg in ws:
        text = msg if isinstance(msg, str) else msg.decode("utf-8")
        sys.stdout.write(text + "\n")
        sys.stdout.flush()


async def main():
    parser = argparse.ArgumentParser(description="MCP STDIO-to-WebSocket Bridge")
    parser.add_argument(
        "--url",
        default=os.getenv("MCP_WS_URL", "ws://localhost:8767"),
        help="Target MCP WebSocket URL (default: ws://localhost:8767)",
    )
    args = parser.parse_args()

    async with websockets.connect(args.url) as ws:
        await asyncio.gather(
            pipe_stdin_to_ws(ws),
            pipe_ws_to_stdout(ws),
        )


if __name__ == "__main__":
    import contextlib

    with contextlib.suppress(KeyboardInterrupt, asyncio.CancelledError):
        asyncio.run(main())
