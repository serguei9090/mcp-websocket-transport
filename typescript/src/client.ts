import type {
  JSONRPCMessage,
  Transport,
  WebSocketClientOptions,
} from "./types.js";

/**
 * WebSocketClientTransport
 *
 * Implements the MCP Transport interface over a full-duplex WebSocket connection.
 * Isomorphic: works across Node.js (via 'ws' / 'isomorphic-ws') and browser/edge environments.
 */
export class WebSocketClientTransport implements Transport {
  private _ws?: any;
  public onmessage?: (message: JSONRPCMessage) => void;
  public onerror?: (error: Error) => void;
  public onclose?: () => void;
  public sessionId?: string;

  constructor(
    private _url: string | URL,
    private _options?: WebSocketClientOptions,
  ) {}

  /**
   * Returns the underlying WebSocket instance if connected.
   */
  public get socket(): any {
    return this._ws;
  }

  /**
   * Initializes and opens the WebSocket connection.
   */
  async start(): Promise<void> {
    if (this._ws) {
      throw new Error("WebSocketClientTransport has already been started.");
    }

    const WebSocketConstructor =
      this._options?.WebSocket ??
      (typeof WebSocket !== "undefined" ? WebSocket : undefined);

    if (!WebSocketConstructor) {
      throw new Error(
        "No WebSocket implementation available. In Node.js environments, provide the 'ws' constructor in options or install 'isomorphic-ws'.",
      );
    }

    return new Promise<void>((resolve, reject) => {
      let settled = false;
      try {
        const urlStr = this._url.toString();
        const ws = new WebSocketConstructor(urlStr, this._options?.protocols);
        this._ws = ws;

        const handleOpen = () => {
          if (!settled) {
            settled = true;
            resolve();
          }
        };

        const handleError = (event: any) => {
          const error =
            event instanceof Error
              ? event
              : new Error(event?.message || "WebSocket encountered an error");
          this.onerror?.(error);
          if (!settled) {
            settled = true;
            reject(error);
          }
        };

        const handleClose = () => {
          this.onclose?.();
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
          ws.addEventListener("open", handleOpen, { once: true });
          ws.addEventListener("error", handleError);
          ws.addEventListener("close", handleClose);
          ws.addEventListener("message", handleMessage);
        } else if (typeof ws.on === "function") {
          ws.once("open", handleOpen);
          ws.on("error", handleError);
          ws.on("close", handleClose);
          ws.on("message", handleMessage);
        } else {
          ws.onopen = handleOpen;
          ws.onerror = handleError;
          ws.onclose = handleClose;
          ws.onmessage = handleMessage;
        }
      } catch (err) {
        if (!settled) {
          settled = true;
          reject(err instanceof Error ? err : new Error(String(err)));
        }
      }
    });
  }

  /**
   * Sends a JSON-RPC message to the server over the WebSocket connection.
   */
  async send(message: JSONRPCMessage): Promise<void> {
    if (!this._ws) {
      throw new Error(
        "WebSocketClientTransport is not connected. Call start() first.",
      );
    }
    if (this._ws.readyState !== 1 /* WebSocket.OPEN */) {
      throw new Error(
        `WebSocket is not open. Current readyState: ${this._ws.readyState}`,
      );
    }
    const payload = JSON.stringify(message);
    this._ws.send(payload);
  }

  /**
   * Closes the active WebSocket connection.
   */
  async close(): Promise<void> {
    if (this._ws) {
      try {
        if (
          this._ws.readyState === 0 /* CONNECTING */ ||
          this._ws.readyState === 1 /* OPEN */
        ) {
          this._ws.close();
        }
      } finally {
        this._ws = undefined;
      }
    }
  }
}
