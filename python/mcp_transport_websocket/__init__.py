"""
MCP WebSocket Transport package for Python.
"""

from .bridge import main_cli, run_bridge
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
    "main_cli",
    "run_bridge",
    "serialize_message",
    "serve_websocket",
    "websocket_client",
]
