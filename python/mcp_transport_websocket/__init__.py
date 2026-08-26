"""
MCP WebSocket Transport package for Python.
"""

from .client import WebSocketClientTransport, websocket_client
from .server import WebSocketServerTransport, serve_websocket
from .types import (
    JSONRPCError,
    JSONRPCMessage,
    JSONRPCNotification,
    JSONRPCRequest,
    JSONRPCResponse,
    serialize_message,
)

__all__ = [
    "JSONRPCError",
    "JSONRPCMessage",
    "JSONRPCNotification",
    "JSONRPCRequest",
    "JSONRPCResponse",
    "WebSocketClientTransport",
    "WebSocketServerTransport",
    "serialize_message",
    "serve_websocket",
    "websocket_client",
]
