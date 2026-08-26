export type RequestId = string | number;

export interface JSONRPCRequest {
  jsonrpc: "2.0";
  id: RequestId;
  method: string;
  params?: Record<string, unknown> | unknown[];
}

export interface JSONRPCNotification {
  jsonrpc: "2.0";
  method: string;
  params?: Record<string, unknown> | unknown[];
}

export interface JSONRPCResponse {
  jsonrpc: "2.0";
  id: RequestId;
  result?: unknown;
  error?: {
    code: number;
    message: string;
    data?: unknown;
  };
}

export type JSONRPCMessage =
  | JSONRPCRequest
  | JSONRPCNotification
  | JSONRPCResponse;

export interface Transport {
  onclose?: () => void;
  onerror?: (error: Error) => void;
  onmessage?: (message: JSONRPCMessage) => void;
  start(): Promise<void>;
  send(message: JSONRPCMessage): Promise<void>;
  close(): Promise<void>;
  sessionId?: string;
}

export interface WebSocketClientOptions {
  WebSocket?: any;
  protocols?: string | string[];
}
