"""
STDIO-to-WebSocket Bridge for Model Context Protocol (MCP).

Provides a transparent pipe connecting any standard STDIO MCP host
(Claude Desktop, Cursor, Antigravity, LM Studio) to a remote/Dockerized
MCP WebSocket server.
"""

import argparse
import asyncio
import contextlib
import os
import sys

import websockets

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")


async def pipe_stdin_to_ws(ws):
    """Reads lines from stdin asynchronously and forwards them over the WebSocket."""
    while True:
        line = await asyncio.to_thread(sys.stdin.readline)
        if not line:
            break
        text = line.strip()
        if text:
            await ws.send(text)


async def pipe_ws_to_stdout(ws):
    """Reads JSON-RPC messages from WebSocket and writes them to stdout."""
    async for msg in ws:
        text = msg if isinstance(msg, str) else msg.decode("utf-8")
        sys.stdout.write(f"{text}\n")
        sys.stdout.flush()


async def run_bridge(url: str):
    """Connects to target WebSocket URL and bridges bidirectional stdio traffic."""
    try:
        async with websockets.connect(url) as ws:
            await asyncio.gather(
                pipe_stdin_to_ws(ws),
                pipe_ws_to_stdout(ws),
            )
    except (ConnectionRefusedError, OSError) as err:
        sys.stderr.write(
            f"❌ [mcp-ws-bridge] Failed to connect to MCP WebSocket server at {url}: {err}\n"
            "   Ensure your MCP WebSocket server is running before launching the host.\n"
        )
        sys.stderr.flush()
        sys.exit(1)


def main_cli():
    parser = argparse.ArgumentParser(
        prog="mcp-ws-bridge",
        description="Bridge standard I/O (stdin/stdout) to an MCP WebSocket server.",
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=os.getenv("MCP_WS_URL", "ws://localhost:8765"),
        help="Target MCP WebSocket URL (default: ws://localhost:8765 or MCP_WS_URL env)",
    )
    args = parser.parse_args()

    with contextlib.suppress(KeyboardInterrupt, asyncio.CancelledError):
        asyncio.run(run_bridge(args.url))


if __name__ == "__main__":
    main_cli()
