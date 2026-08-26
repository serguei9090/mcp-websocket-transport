"""
MCP WebSocket Server Transport implementation supporting FastAPI, Starlette, and websockets.
"""

import json
from typing import Any

import anyio

from .types import serialize_message


async def serve_websocket(
    server: Any,
    websocket: Any,
    buffer_size: int = 100,
    auto_accept: bool = True,
) -> None:
    """
    Bridges an incoming WebSocket connection to an MCP Server instance.
    Automatically detects Starlette/FastAPI WebSocket vs. websockets.WebSocketServerProtocol.

    Args:
        server: MCP Server instance (e.g. `mcp.server.Server` or any standard MCP runner)
        websocket: Connected WebSocket instance
        buffer_size: AnyIO stream buffer size
        auto_accept: Automatically accept connection for FastAPI/Starlette WebSockets
    """
    read_send, read_recv = anyio.create_memory_object_stream(buffer_size)
    write_send, write_recv = anyio.create_memory_object_stream(buffer_size)

    import contextlib

    # Detect framework / protocol type
    is_starlette = hasattr(websocket, "receive_text") and hasattr(
        websocket, "send_text"
    )

    if is_starlette and auto_accept and hasattr(websocket, "accept"):
        with contextlib.suppress(Exception):
            await websocket.accept()

    async def ws_reader():
        try:
            if is_starlette:
                while True:
                    raw_msg = await websocket.receive_text()
                    data = json.loads(raw_msg)
                    if hasattr(server, "parse_message"):
                        msg = server.parse_message(data)
                    else:
                        msg = data
                    await read_send.send(msg)
            else:
                async for raw_msg in websocket:
                    data = (
                        json.loads(raw_msg)
                        if isinstance(raw_msg, (str, bytes))
                        else raw_msg
                    )
                    if hasattr(server, "parse_message"):
                        msg = server.parse_message(data)
                    else:
                        msg = data
                    await read_send.send(msg)
        except Exception:
            pass
        finally:
            await read_send.aclose()

    async def ws_writer():
        try:
            async for msg in write_recv:
                payload = serialize_message(msg)
                if is_starlette:
                    await websocket.send_text(payload)
                else:
                    await websocket.send(payload)
        except Exception:
            pass
        finally:
            if is_starlette:
                with contextlib.suppress(Exception):
                    await websocket.close()

    async with anyio.create_task_group() as tg:
        tg.start_soon(ws_reader)
        tg.start_soon(ws_writer)

        init_options = (
            server.create_initialization_options()
            if hasattr(server, "create_initialization_options")
            else None
        )

        try:
            if init_options is not None:
                await server.run(read_recv, write_send, init_options)
            else:
                await server.run(read_recv, write_send)
        finally:
            tg.cancel_scope.cancel()
            await write_send.aclose()
            await read_recv.aclose()


class WebSocketServerTransport:
    """
    Helper wrapper for running an MCP Server over a WebSocket connection.
    """

    def __init__(self, server: Any, buffer_size: int = 100):
        self.server = server
        self.buffer_size = buffer_size

    async def handle(self, websocket: Any, auto_accept: bool = True) -> None:
        """Handles an incoming WebSocket connection."""
        await serve_websocket(
            server=self.server,
            websocket=websocket,
            buffer_size=self.buffer_size,
            auto_accept=auto_accept,
        )
