"""
MCP / JSON-RPC 2.0 Types and serialization helpers.
"""

from typing import Any

from pydantic import BaseModel


class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int
    method: str
    params: dict[str, Any] | list[Any] | None = None


class JSONRPCNotification(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: dict[str, Any] | list[Any] | None = None


class JSONRPCError(BaseModel):
    code: int
    message: str
    data: Any | None = None


class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int
    result: Any | None = None
    error: JSONRPCError | None = None


JSONRPCMessage = JSONRPCRequest | JSONRPCNotification | JSONRPCResponse | dict[str, Any]


def serialize_message(msg: Any) -> str:
    """Serializes an MCP or JSON-RPC message into a JSON string."""
    if hasattr(msg, "message") and hasattr(msg.message, "model_dump_json"):
        return msg.message.model_dump_json(by_alias=True, exclude_unset=True)
    if hasattr(msg, "model_dump_json"):
        return msg.model_dump_json(by_alias=True, exclude_none=True)
    elif hasattr(msg, "json"):
        return msg.json(by_alias=True, exclude_none=True)
    elif isinstance(msg, dict):
        import json

        return json.dumps(msg)
    elif isinstance(msg, str):
        return msg
    else:
        import json

        return json.dumps(msg, default=str)
