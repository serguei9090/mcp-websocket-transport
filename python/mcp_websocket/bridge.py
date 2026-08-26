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


async def run_bridge(url: str, retries: int = 3, retry_delay: float = 1.0):
    """Connects to target WebSocket URL and bridges bidirectional stdio traffic with retry support."""
    ws = None
    for attempt in range(1, retries + 1):
        try:
            ws = await websockets.connect(url)
            break
        except (ConnectionRefusedError, OSError) as err:
            if attempt < retries:
                sys.stderr.write(
                    f"⏳ [mcp-ws-bridge] Waiting for server at {url} (attempt {attempt}/{retries})...\n"
                )
                sys.stderr.flush()
                await asyncio.sleep(retry_delay)
            else:
                sys.stderr.write(
                    f"❌ [mcp-ws-bridge] Connection refused at {url}: {err}\n"
                    "   💡 Start your server first: 'uv run python examples/mcp_tool_server.py'\n"
                )
                sys.stderr.flush()
                sys.exit(1)

    try:
        await asyncio.gather(
            pipe_stdin_to_ws(ws),
            pipe_ws_to_stdout(ws),
        )
    finally:
        if ws:
            await ws.close()


def main_cli():
    parser = argparse.ArgumentParser(
        prog="mcp-ws-bridge",
        description="Bridge standard I/O (stdin/stdout) to an MCP WebSocket server.",
    )
    parser.add_argument(
        "url_pos",
        nargs="?",
        default=None,
        help="Target MCP WebSocket URL (positional)",
    )
    parser.add_argument(
        "--url",
        dest="url_opt",
        default=None,
        help="Target MCP WebSocket URL (--url flag)",
    )
    args = parser.parse_args()

    target_url = (
        args.url_opt
        or args.url_pos
        or os.getenv("MCP_WS_URL")
        or "ws://localhost:8767"
    )

    with contextlib.suppress(KeyboardInterrupt, asyncio.CancelledError):
        asyncio.run(run_bridge(target_url))


if __name__ == "__main__":
    main_cli()
