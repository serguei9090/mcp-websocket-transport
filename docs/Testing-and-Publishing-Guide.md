MCP WebSocket Transport: Testing & Official Publishing Guide
This guide covers local manual verification and the complete release process to the official package registries (npm for JavaScript/TypeScript and PyPI for Python).


1. Overview of the WebSocket Architecture for MCP
Why WebSocket over Streamable HTTP / SSE?
Full-Duplex Bidirectional Channel: Both client and server can send JSON-RPC requests, notifications, and responses over a single persistent TCP connection.
No Complex SSE Reconnection Workarounds: Eliminates the need to track stream reconnect state, session headers (Mcp-Session-Id), or buffering proxies.
Server-Initiated Requests: Directly supports server-to-client sampling (sampling/createMessage) and bidirectional notifications without requiring separate HTTP webhook endpoints.
Low Overhead: Avoids HTTP header serialization overhead on each request/response.


2. TypeScript / JavaScript Package (@modelcontextprotocol/transport-websocket)
Project Structure
mcp-transport-websocket-ts/

├── package.json

├── tsconfig.json

├── README.md

├── src/

│   ├── index.ts

│   ├── client.ts

│   ├── server.ts

│   └── types.ts

├── examples/

│   ├── server.ts

│   └── client.ts

└── test/

    └── run-tests.js
Manual Testing
Automated Protocol Verification:

npm test

Verifies:

Client-Server handshake (initialize / notifications/initialized)
Health check (ping)
Tool listing and tool execution (tools/list, tools/call)
Resource listing and retrieval (resources/list, resources/read)
Prompt listing and expansion (prompts/list, prompts/get)
Error handling (-32601 Method Not Found, -32602 Invalid Params)
Connection lifecycle (clean start and close)

Running the Example Server & Client with Live SDK:

# Terminal 1: Start the MCP Server

npx ts-node examples/server.ts

# Terminal 2: Run the MCP Client

npx ts-node examples/client.ts
Publishing to npm
Prepare the Build:

npm run build

Login to npm:

npm login

Dry-run verification:

npm publish --dry-run

Publish to npm Registry:

# For scoped packages (@organization/package-name):

npm publish --access public

# For unscoped packages:

npm publish


3. Python Package (mcp-transport-websocket)
Project Structure
mcp-transport-websocket-py/

├── pyproject.toml

├── setup.py

├── README.md

├── mcp_transport_websocket/

│   ├── __init__.py

│   ├── client.py

│   ├── server.py

│   └── types.py

├── examples/

│   ├── fastapi_server.py

│   ├── websockets_server.py

│   └── client.py

└── tests/

    └── test_transport.py
Manual Testing
Automated Protocol Verification:

python -m pytest tests/

# or

python tests/test_transport.py

Running the FastAPI WebSocket Server:

# Terminal 1: Start FastAPI WebSocket Server

python examples/fastapi_server.py

# Terminal 2: Run Client

python examples/client.py

Running the websockets Standalone Server:

python examples/websockets_server.py
Publishing to PyPI
Install Build & Upload Tools:

pip install --upgrade build twine

# or using uv:

uv tool install twine

Build Distribution Packages:

python -m build

# or using uv:

uv build

This generates:

dist/mcp_transport_websocket-1.0.0-py3-none-any.whl
dist/mcp_transport_websocket-1.0.0.tar.gz

Validate Package Distribution:

twine check dist/*

Upload to TestPyPI (Recommended for staging):

twine upload --repository testpypi dist/*

Upload to Official PyPI:

twine upload dist/*

# or using uv:

uv publish
