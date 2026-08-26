"""
MCP WebSocket Client Transport implementation using AnyIO memory streams.
"""

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import anyio
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream

from .types import serialize_message


@asynccontextmanager
async def websocket_client(
    url: str,
    buffer_size: int = 100,
    **websocket_kwargs: Any,
) -> AsyncIterator[tuple[MemoryObjectReceiveStream[Any], MemoryObjectSendStream[Any]]]:
    """
    Asynchronous context manager providing bidirectional AnyIO memory streams connected to an MCP WebSocket server.
    Compatible with `mcp.client.session.ClientSession(read_stream, write_stream)`.

    Args:
        url: WebSocket URL (e.g. "ws://localhost:8765/ws")
        buffer_size: AnyIO stream buffer size
        websocket_kwargs: Keyword arguments passed to `websockets.connect()`
    """
    import contextlib

    import websockets

    read_send, read_recv = anyio.create_memory_object_stream(buffer_size)
    write_send, write_recv = anyio.create_memory_object_stream(buffer_size)

    async with (
        websockets.connect(url, **websocket_kwargs) as ws,
        anyio.create_task_group() as tg,
    ):

        async def ws_reader():
            try:
                async for raw_msg in ws:
                    try:
                        data = (
                            json.loads(raw_msg)
                            if isinstance(raw_msg, (str, bytes))
                            else raw_msg
                        )
                        await read_send.send(data)
                    except Exception as exc:
                        await read_send.send(exc)
            except Exception:
                pass
            finally:
                await read_send.aclose()

        async def ws_writer():
            try:
                async for msg in write_recv:
                    payload = serialize_message(msg)
                    await ws.send(payload)
            except Exception:
                pass
            finally:
                with contextlib.suppress(Exception):
                    await ws.close()

        tg.start_soon(ws_reader)
        tg.start_soon(ws_writer)

        try:
            yield (read_recv, write_send)
        finally:
            tg.cancel_scope.cancel()
            await write_send.aclose()
            await read_recv.aclose()


class WebSocketClientTransport:
    """
    Object-oriented WebSocket Client Transport for MCP.
    """

    def __init__(self, url: str, buffer_size: int = 100, **ws_kwargs: Any):
        self.url = url
        self.buffer_size = buffer_size
        self.ws_kwargs = ws_kwargs
        self._client_cm = None
        self.read_stream: MemoryObjectReceiveStream[Any] | None = None
        self.write_stream: MemoryObjectSendStream[Any] | None = None

    async def __aenter__(
        self,
    ) -> tuple[MemoryObjectReceiveStream[Any], MemoryObjectSendStream[Any]]:
        self._client_cm = websocket_client(
            self.url, buffer_size=self.buffer_size, **self.ws_kwargs
        )
        self.read_stream, self.write_stream = await self._client_cm.__aenter__()
        return self.read_stream, self.write_stream

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._client_cm:
            await self._client_cm.__aexit__(exc_type, exc_val, exc_tb)
            self._client_cm = None
            self.read_stream = None
            self.write_stream = None
