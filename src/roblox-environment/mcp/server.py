"""
MCP Server - Model Context Protocol WebSocket Server

Manages real-time context synchronization between agents and services.
"""

import asyncio
import websockets
import json
import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ContextEntry:
    """Represents a single context entry"""

    timestamp: str
    content: Dict[str, Any]
    tokens: int
    source: str
    priority: int = 1

    def to_dict(self):
        return asdict(self)


class MCPServer:
    """
    Model Context Protocol server for managing agent context.

    Features:
    - WebSocket communication for real-time updates
    - Token-aware context management (128K limit)
    - Priority-based context pruning
    - Multi-client synchronization
    """

    DEFAULT_PORT = 9876
    DEFAULT_MAX_TOKENS = 128000

    def __init__(self, port: int = DEFAULT_PORT, max_tokens: int = DEFAULT_MAX_TOKENS):
        self.port = port
        self.max_tokens = max_tokens
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.context_store: Dict[str, ContextEntry] = {}
        self.client_metadata: Dict[str, Dict] = {}

    async def register(self, websocket: websockets.WebSocketServerProtocol):
        """Register a new client connection"""
        self.clients.add(websocket)
        client_id = self._get_client_id(websocket)
        self.client_metadata[client_id] = {
            "connected_at": datetime.now().isoformat(),
            "websocket": websocket,
        }
        logger.info(f"Client {client_id} connected")

        # Send current context to new client
        await self.send_context(websocket)

    async def unregister(self, websocket: websockets.WebSocketServerProtocol):
        """Unregister a client connection"""
        self.clients.discard(websocket)
        client_id = self._get_client_id(websocket)
        if client_id in self.client_metadata:
            del self.client_metadata[client_id]
        logger.info(f"Client {client_id} disconnected")

    def _get_client_id(self, websocket: websockets.WebSocketServerProtocol) -> str:
        """Generate unique client ID"""
        # Safely handle remote_address to avoid null pointer (SonarQube: S2259)
        if websocket.remote_address and len(websocket.remote_address) >= 2:
            remote_address = (
                f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
            )
        else:
            # Fallback to a unique identifier if remote_address is not available
            remote_address = f"unknown_{id(websocket)}"
        # Use SHA256 instead of MD5 for better security (SonarQube: S4790)
        return hashlib.sha256(remote_address.encode()).hexdigest()[:8]

    async def handle_message(
        self, websocket: websockets.WebSocketServerProtocol, message: str
    ):
        """Process incoming messages from clients"""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "update_context":
                await self._handle_update_context(data, websocket)
            elif message_type == "get_context":
                await self.send_context(websocket)
            elif message_type == "clear_context":
                await self._handle_clear_context(data)
            elif message_type == "query_context":
                await self._handle_query_context(data, websocket)
            elif message_type == "set_priority":
                await self._handle_set_priority(data)
            else:
                await self._send_error(
                    websocket, f"Unknown message type: {message_type}"
                )

        except json.JSONDecodeError as e:
            await self._send_error(websocket, f"Invalid JSON: {e}")
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error(f"Error handling message: {e}")
            await self._send_error(websocket, str(e))

    async def _handle_update_context(
        self, data: Dict, websocket: websockets.WebSocketServerProtocol
    ):
        """Handle context update request"""
        context = data.get("context", {})
        source = data.get("source", self._get_client_id(websocket))
        priority = data.get("priority", 1)

        # Calculate token count (simplified - in production use tiktoken)
        tokens = len(json.dumps(context))

        # Create context entry
        entry = ContextEntry(
            timestamp=datetime.now().isoformat(),
            content=context,
            tokens=tokens,
            source=source,
            priority=priority,
        )

        # Store with unique key
        context_key = f"{source}_{datetime.now().timestamp()}"
        self.context_store[context_key] = entry

        # Prune if necessary
        self._prune_context()

        # Broadcast update to all clients
        await self.broadcast_context()

    async def _handle_clear_context(self, data: Dict):
        """Handle context clear request"""
        source = data.get("source")

        if source:
            # Clear context from specific source
            keys_to_remove = [
                k for k, v in self.context_store.items() if v.source == source
            ]
            for key in keys_to_remove:
                del self.context_store[key]
        else:
            # Clear all context
            self.context_store.clear()

        await self.broadcast_context()

    async def _handle_query_context(
        self, data: Dict, websocket: websockets.WebSocketServerProtocol
    ):
        """Handle context query request"""
        query = data.get("query", {})
        source_filter = query.get("source")
        priority_filter = query.get("min_priority", 0)

        filtered_context = {}
        for key, entry in self.context_store.items():
            if source_filter and entry.source != source_filter:
                continue
            if entry.priority < priority_filter:
                continue
            filtered_context[key] = entry.to_dict()

        await websocket.send(
            json.dumps({"type": "query_response", "data": filtered_context})
        )

    async def _handle_set_priority(self, data: Dict):
        """Handle priority update for existing context"""
        context_key = data.get("key")
        new_priority = data.get("priority", 1)

        if context_key in self.context_store:
            self.context_store[context_key].priority = new_priority
            self._prune_context()
            await self.broadcast_context()

    def _prune_context(self):
        """
        Remove old context to stay within token limit.
        Prioritizes keeping high-priority and recent context.
        """
        total_tokens = sum(entry.tokens for entry in self.context_store.values())

        if total_tokens <= self.max_tokens:
            return

        # Sort by priority (descending) and timestamp (descending)
        sorted_entries = sorted(
            self.context_store.items(),
            key=lambda x: (
                -x[1].priority,
                -float(datetime.fromisoformat(x[1].timestamp).timestamp()),
            ),
        )

        # Keep entries until we exceed token limit
        kept_entries = {}
        current_tokens = 0

        for key, entry in sorted_entries:
            if current_tokens + entry.tokens <= self.max_tokens:
                kept_entries[key] = entry
                current_tokens += entry.tokens
            else:
                break

        self.context_store = kept_entries
        logger.info(f"Pruned context to {current_tokens} tokens")

    async def send_context(self, websocket: websockets.WebSocketServerProtocol):
        """Send current context to a specific client"""
        context_data = {
            key: entry.to_dict() for key, entry in self.context_store.items()
        }

        await websocket.send(
            json.dumps(
                {
                    "type": "context",
                    "data": context_data,
                    "metadata": {
                        "total_tokens": sum(
                            e.tokens for e in self.context_store.values()
                        ),
                        "max_tokens": self.max_tokens,
                        "entry_count": len(self.context_store),
                    },
                }
            )
        )

    async def broadcast_context(self):
        """Broadcast current context to all connected clients"""
        if not self.clients:
            return

        # Prepare message once
        context_data = {
            key: entry.to_dict() for key, entry in self.context_store.items()
        }
        message = json.dumps(
            {
                "type": "context_update",
                "data": context_data,
                "metadata": {
                    "total_tokens": sum(e.tokens for e in self.context_store.values()),
                    "max_tokens": self.max_tokens,
                    "entry_count": len(self.context_store),
                },
            }
        )

        # Send to all clients concurrently
        disconnected_clients = []
        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(client)

        # Clean up disconnected clients
        for client in disconnected_clients:
            await self.unregister(client)

    async def _send_error(
        self, websocket: websockets.WebSocketServerProtocol, error_message: str
    ):
        """Send error message to client"""
        await websocket.send(json.dumps({"type": "error", "message": error_message}))

    async def handler(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """WebSocket connection handler"""
        await self.register(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)

    async def start(self):
        """Start the MCP server"""
        logger.info(f"Starting MCP server on port {self.port}")
        logger.info(f"Max context tokens: {self.max_tokens}")

        async with websockets.serve(self.handler, "localhost", self.port):
            logger.info(f"MCP server listening on ws://localhost:{self.port}")
            await asyncio.Future()  # Run forever

    def get_status(self) -> Dict:
        """Get current server status"""
        return {
            "connected_clients": len(self.clients),
            "context_entries": len(self.context_store),
            "total_tokens": sum(e.tokens for e in self.context_store.values()),
            "max_tokens": self.max_tokens,
            "clients": list(self.client_metadata.keys()),
        }


async def main():
    """Main entry point for running the MCP server"""
    server = MCPServer(
        port=MCPServer.DEFAULT_PORT, max_tokens=MCPServer.DEFAULT_MAX_TOKENS
    )
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
