import type { JSONRPCMessage, Transport } from "./types.js";

/**
 * Options for WebSocketServerTransport.
 */
export interface WebSocketServerTransportOptions {
  sessionId?: string;
}

/**
 * WebSocketServerTransport
 *
 * Implements the MCP Transport interface for a single incoming server-side WebSocket connection.
 * Compatible with Node.js 'ws' WebSocket server and standard WebSocket instances.
 */
export class WebSocketServerTransport implements Transport {
  public onmessage?: (message: JSONRPCMessage) => void;
  public onerror?: (error: Error) => void;
  public onclose?: () => void;
  public sessionId?: string;

  constructor(
    private _socket: any,
    options?: WebSocketServerTransportOptions,
  ) {
    this.sessionId = options?.sessionId;
  }

  /**
   * Returns the underlying WebSocket instance.
   */
  public get socket(): any {
    return this._socket;
  }

  /**
   * Attaches event handlers to the connected WebSocket socket.
   */
  async start(): Promise<void> {
    const ws = this._socket;

    const handleClose = () => {
      this.onclose?.();
    };

    const handleError = (err: any) => {
      const errorObj =
        err instanceof Error
          ? err
          : new Error(
              err?.message || "WebSocket error occurred on server transport",
            );
      this.onerror?.(errorObj);
    };

    const handleMessage = (data: any) => {
      try {
        const raw =
          typeof data === "string"
            ? data
            : data?.data !== undefined
              ? typeof data.data === "string"
                ? data.data
                : data.data.toString()
              : data.toString();
        const parsed = JSON.parse(raw) as JSONRPCMessage;
        this.onmessage?.(parsed);
      } catch (err) {
        const parseErr =
          err instanceof Error
            ? err
            : new Error(
                `Failed to parse incoming JSON-RPC message: ${String(err)}`,
              );
        this.onerror?.(parseErr);
      }
    };

    if (typeof ws.addEventListener === "function") {
      ws.addEventListener("close", handleClose);
      ws.addEventListener("error", handleError);
      ws.addEventListener("message", handleMessage);
    } else if (typeof ws.on === "function") {
      ws.on("close", handleClose);
      ws.on("error", handleError);
      ws.on("message", handleMessage);
    } else {
      ws.onclose = handleClose;
      ws.onerror = handleError;
      ws.onmessage = handleMessage;
    }
  }

  /**
   * Sends a JSON-RPC message to the connected client.
   */
  async send(message: JSONRPCMessage): Promise<void> {
    if (this._socket.readyState !== 1 /* WebSocket.OPEN */) {
      throw new Error(
        `WebSocket is not open. Current readyState: ${this._socket.readyState}`,
      );
    }
    const payload = JSON.stringify(message);
    this._socket.send(payload);
  }

  /**
   * Closes the active WebSocket connection.
   */
  async close(): Promise<void> {
    try {
      if (
        this._socket.readyState === 0 /* CONNECTING */ ||
        this._socket.readyState === 1 /* OPEN */
      ) {
        this._socket.close();
      }
    } catch {
      // Ignored if socket is already closed
    }
  }
}
