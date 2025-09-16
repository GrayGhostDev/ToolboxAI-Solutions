"""
WebSocket Handler for Roblox AI Agent

Handles WebSocket message routing and processing for the Roblox AI chat system.
Integrates with Pusher service and agent management.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

from apps.backend.services.pusher import trigger_event as pusher_trigger_event
from apps.backend.services.roblox_ai_agent import roblox_ai_agent
from apps.backend.core.config import settings
from apps.backend.services.design_file_converter import design_file_converter
from apps.backend.services.design_folder_scanner import design_folder_scanner

logger = logging.getLogger(__name__)

class WebSocketHandler:
    """Handles WebSocket message routing for Roblox AI agent"""

    def __init__(self):
        self.active_connections: Dict[str, Any] = {}
        self.message_handlers = {
            'agent_chat_user': self._handle_agent_chat_user,
            'ai_message': self._handle_ai_message,
            'roblox_agent_request': self._handle_roblox_agent_request,
            'design_file_process': self._handle_design_file_process,
            'design_folder_scan': self._handle_design_folder_scan,
            'design_file_search': self._handle_design_file_search,
            'ping': self._handle_ping,
            'subscribe': self._handle_subscribe,
            'unsubscribe': self._handle_unsubscribe
        }

    async def handle_message(self, message_type: str, payload: Dict[str, Any], connection_id: str = None) -> None:
        """Route incoming WebSocket message to appropriate handler"""
        try:
            handler = self.message_handlers.get(message_type)
            if handler:
                await handler(payload, connection_id)
            else:
                logger.warning(f"No handler for message type: {message_type}")

        except Exception as e:
            logger.error(f"Error handling WebSocket message {message_type}: {e}")
            await self._send_error_message(connection_id, f"Error processing message: {str(e)}")

    async def _handle_agent_chat_user(self, payload: Dict[str, Any], connection_id: str = None) -> None:
        """Handle user chat message to AI agent"""
        try:
            conversation_id = payload.get('conversationId')
            message = payload.get('text') or payload.get('content')
            context = payload.get('context', {})

            if not conversation_id or not message:
                raise ValueError("Missing conversationId or message")

            # Add connection context
            if connection_id:
                context['connection_id'] = connection_id

            # Process message with AI agent
            await roblox_ai_agent.handle_user_message(conversation_id, message, context)

        except Exception as e:
            logger.error(f"Error handling agent chat user message: {e}")
            raise

    async def _handle_ai_message(self, payload: Dict[str, Any], connection_id: str = None) -> None:
        """Handle AI message from frontend"""
        try:
            conversation_id = payload.get('conversation_id')
            message = payload.get('message')
            context = payload.get('context', {})

            if not conversation_id or not message:
                logger.error("Missing conversation_id or message in AI message payload")
                return

            logger.info(f"Processing AI message for conversation {conversation_id}: {message}")

            # Add connection context
            if connection_id:
                context['connection_id'] = connection_id

            # Process message with AI agent
            await roblox_ai_agent.handle_user_message(conversation_id, message, context)

        except Exception as e:
            logger.error(f"Error handling AI message: {e}")
            raise

    async def _handle_roblox_agent_request(self, payload: Dict[str, Any], connection_id: str = None) -> None:
        """Handle Roblox environment generation request"""
        try:
            conversation_id = payload.get('conversationId')
            spec = payload.get('spec', {})

            if not conversation_id or not spec:
                raise ValueError("Missing conversationId or spec")

            # Start environment generation
            await roblox_ai_agent.generate_environment(conversation_id, spec)

        except Exception as e:
            logger.error(f"Error handling Roblox agent request: {e}")
            raise

    async def _handle_ping(self, payload: Dict[str, Any], connection_id: str = None) -> None:
        """Handle ping message"""
        try:
            # Send pong response
            pusher_trigger_event(
                f"connection-{connection_id}",
                "message",
                {
                    "type": "pong",
                    "payload": {
                        "timestamp": payload.get('timestamp'),
                        "server_time": asyncio.get_event_loop().time()
                    }
                }
            )

        except Exception as e:
            logger.error(f"Error handling ping: {e}")

    async def _handle_subscribe(self, payload: Dict[str, Any], connection_id: str = None) -> None:
        """Handle channel subscription"""
        try:
            channel = payload.get('channel')
            if not channel:
                raise ValueError("Missing channel")

            # Track subscription
            if connection_id not in self.active_connections:
                self.active_connections[connection_id] = {'channels': set()}

            self.active_connections[connection_id]['channels'].add(channel)

            # Send subscription confirmation
            pusher_trigger_event(
                f"connection-{connection_id}",
                "message",
                {
                    "type": "subscribed",
                    "payload": {
                        "channel": channel,
                        "status": "success"
                    }
                }
            )

        except Exception as e:
            logger.error(f"Error handling subscribe: {e}")

    async def _handle_unsubscribe(self, payload: Dict[str, Any], connection_id: str = None) -> None:
        """Handle channel unsubscription"""
        try:
            channel = payload.get('channel')
            if not channel:
                raise ValueError("Missing channel")

            # Remove subscription
            if connection_id in self.active_connections:
                self.active_connections[connection_id]['channels'].discard(channel)

            # Send unsubscription confirmation
            pusher_trigger_event(
                f"connection-{connection_id}",
                "message",
                {
                    "type": "unsubscribed",
                    "payload": {
                        "channel": channel,
                        "status": "success"
                    }
                }
            )

        except Exception as e:
            logger.error(f"Error handling unsubscribe: {e}")

    async def _handle_design_file_process(self, payload: Dict[str, Any], connection_id: str = None) -> None:
        """Handle design file processing request"""
        try:
            file_path = payload.get('file_path')
            include_content = payload.get('include_content', True)

            if not file_path:
                raise ValueError("Missing file_path")

            logger.info(f"Processing design file: {file_path}")

            # Process the file
            result = await design_file_converter.process_design_file(file_path)

            # Send result back to client
            pusher_trigger_event(
                f"connection-{connection_id}",
                "message",
                {
                    "type": "design_file_processed",
                    "payload": {
                        "file_path": file_path,
                        "result": result
                    }
                }
            )

        except Exception as e:
            logger.error(f"Error handling design file process: {e}")
            await self._send_error_message(connection_id, f"Design file processing error: {str(e)}")

    async def _handle_design_folder_scan(self, payload: Dict[str, Any], connection_id: str = None) -> None:
        """Handle design folder scan request"""
        try:
            folder_path = payload.get('folder_path')
            include_content = payload.get('include_content', True)

            logger.info(f"Scanning design folder: {folder_path or 'default'}")

            # Scan the folder
            if folder_path:
                result = await design_folder_scanner.get_folder_contents(folder_path)
            else:
                result = await design_folder_scanner.scan_design_folder(include_content)

            # Send result back to client
            pusher_trigger_event(
                f"connection-{connection_id}",
                "message",
                {
                    "type": "design_folder_scanned",
                    "payload": {
                        "folder_path": folder_path,
                        "result": result
                    }
                }
            )

        except Exception as e:
            logger.error(f"Error handling design folder scan: {e}")
            await self._send_error_message(connection_id, f"Design folder scan error: {str(e)}")

    async def _handle_design_file_search(self, payload: Dict[str, Any], connection_id: str = None) -> None:
        """Handle design file search request"""
        try:
            query = payload.get('query')
            category = payload.get('category')

            if not query:
                raise ValueError("Missing search query")

            logger.info(f"Searching design files: {query} (category: {category})")

            # Search for files
            results = await design_folder_scanner.search_design_files(query, category)

            # Send result back to client
            pusher_trigger_event(
                f"connection-{connection_id}",
                "message",
                {
                    "type": "design_file_search_results",
                    "payload": {
                        "query": query,
                        "category": category,
                        "results": results
                    }
                }
            )

        except Exception as e:
            logger.error(f"Error handling design file search: {e}")
            await self._send_error_message(connection_id, f"Design file search error: {str(e)}")

    async def _send_error_message(self, connection_id: str, error_message: str) -> None:
        """Send error message to connection"""
        try:
            if connection_id:
                pusher_trigger_event(
                    f"connection-{connection_id}",
                    "message",
                    {
                        "type": "error",
                        "payload": {
                            "error": error_message,
                            "timestamp": asyncio.get_event_loop().time()
                        }
                    }
                )
        except Exception as e:
            logger.error(f"Error sending error message: {e}")

    def add_connection(self, connection_id: str, connection_info: Dict[str, Any]) -> None:
        """Add new WebSocket connection"""
        self.active_connections[connection_id] = {
            'channels': set(),
            'info': connection_info,
            'connected_at': asyncio.get_event_loop().time()
        }
        logger.info(f"Added WebSocket connection: {connection_id}")

    def remove_connection(self, connection_id: str) -> None:
        """Remove WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            logger.info(f"Removed WebSocket connection: {connection_id}")

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)

    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get connection information"""
        return self.active_connections.get(connection_id)

    async def broadcast_to_channel(self, channel: str, message_type: str, payload: Dict[str, Any]) -> None:
        """Broadcast message to all connections subscribed to a channel"""
        try:
            pusher_trigger_event(
                channel,
                "message",
                {
                    "type": message_type,
                    "payload": payload
                }
            )
        except Exception as e:
            logger.error(f"Error broadcasting to channel {channel}: {e}")

# Global WebSocket handler instance
websocket_handler = WebSocketHandler()

# Convenience functions
async def handle_websocket_message(message_type: str, payload: Dict[str, Any], connection_id: str = None) -> None:
    """Handle WebSocket message"""
    await websocket_handler.handle_message(message_type, payload, connection_id)

async def broadcast_message(channel: str, message_type: str, payload: Dict[str, Any]) -> None:
    """Broadcast message to channel"""
    await websocket_handler.broadcast_to_channel(channel, message_type, payload)

def add_websocket_connection(connection_id: str, connection_info: Dict[str, Any]) -> None:
    """Add WebSocket connection"""
    websocket_handler.add_connection(connection_id, connection_info)

def remove_websocket_connection(connection_id: str) -> None:
    """Remove WebSocket connection"""
    websocket_handler.remove_connection(connection_id)

# Placeholder functions for compatibility with main.py
async def broadcast_content_update(content_data: Dict[str, Any]) -> None:
    """Broadcast content update to all connected WebSocket clients."""
    logger.info(f"Broadcasting content update: {content_data}")
    try:
        # Use the existing websocket_handler to broadcast
        await websocket_handler.broadcast_to_channel("content_updates", "content_update", content_data)
    except Exception as e:
        logger.error(f"Failed to broadcast content update: {e}")

async def websocket_endpoint(websocket, client_id: str = None) -> None:
    """WebSocket endpoint handler."""
    logger.info(f"WebSocket connection established for client: {client_id}")
    try:
        # Accept the WebSocket connection
        await websocket.accept()

        # Add to connection tracking
        if client_id:
            add_websocket_connection(client_id, {"websocket": websocket})

        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_text()
                logger.info(f"Received WebSocket message: {data}")

                # Parse JSON message
                try:
                    message = json.loads(data)
                    message_type = message.get('type')
                    payload = message.get('payload', {})

                    if message_type:
                        # Route to appropriate handler
                        await websocket_handler.handle_message(message_type, payload, client_id)
                    else:
                        logger.warning("Received message without type field")

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse WebSocket message as JSON: {e}")
                    # Echo back the message for now
                    await websocket.send_text(f"Echo: {data}")

            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        # Clean up connection
        if client_id:
            remove_websocket_connection(client_id)

# WebSocket manager with basic RBAC, capacity, and rate limiting (2025-ready minimal impl)
class WebSocketManager:
    def __init__(self):
        # client_id -> { 'ws': websocket, 'user_id': str, 'user_role': str, 'channels': set() }
        self.connections: Dict[str, Dict[str, Any]] = {}
        # Aggregated stats used by tests and status endpoints
        self._stats: Dict[str, int] = {
            'active_connections': 0,
            'connections_rejected': 0,
            'rate_limited': 0,
        }

    async def connect(self, websocket, client_id: str, user_id: Optional[str] = None, user_role: str = "student", **kwargs):
        """Connect a WebSocket client with capacity enforcement.
        Accepts extra kwargs for forward-compatibility (e.g., username, metadata).
        Returns the client_id on success, or None if rejected.
        """
        try:
            max_conn = getattr(settings, 'WS_MAX_CONNECTIONS', None)
            if isinstance(max_conn, property):  # safety for monkeypatched properties
                try:
                    max_conn = max_conn.fget(settings)  # type: ignore
                except Exception:
                    max_conn = None
            if max_conn is None:
                max_conn = getattr(settings, 'WS_MAX_CONNECTIONS', 1000)
            # Enforce capacity
            if max_conn is not None and self._stats['active_connections'] >= int(max_conn):
                # Inform client
                try:
                    await websocket.send_text(json.dumps({
                        'type': 'error',
                        'error': 'WebSocket capacity reached. Please try again later.'
                    }))
                except Exception:
                    pass
                # Best-effort close
                try:
                    if hasattr(websocket, 'close'):
                        await websocket.close()
                except Exception:
                    pass
                self._stats['connections_rejected'] += 1
                return None

            # Accept and store
            if hasattr(websocket, 'accept'):
                try:
                    await websocket.accept()
                except Exception:
                    # Ignore accept errors in tests using AsyncMock
                    pass
            self.connections[client_id] = {
                'ws': websocket,
                'user_id': user_id,
                'user_role': user_role or 'student',
                'channels': set(),
            }
            add_websocket_connection(client_id, {"websocket": websocket, "user_id": user_id, "role": user_role})
            self._stats['active_connections'] = len(self.connections)
            logger.info(f"WebSocket client {client_id} connected (role={user_role})")
            return client_id
        except Exception as e:
            logger.error(f"Error during WebSocket connect for {client_id}: {e}")
            return None

    async def disconnect(self, client_id: str):
        """Disconnect a WebSocket client and update stats."""
        try:
            info = self.connections.pop(client_id, None)
            if info and info.get('ws') and hasattr(info['ws'], 'close'):
                try:
                    await info['ws'].close()
                except Exception:
                    pass
            remove_websocket_connection(client_id)
        finally:
            self._stats['active_connections'] = len(self.connections)
            logger.info(f"WebSocket client {client_id} disconnected")

    def _required_role_for_channel(self, channel: str) -> Optional[str]:
        prefix_map = getattr(settings, 'WS_CHANNEL_ROLE_PREFIXES', {}) or {}
        if not isinstance(prefix_map, dict):
            return None
        for prefix, req_role in prefix_map.items():
            try:
                if channel.startswith(str(prefix)):
                    return str(req_role)
            except Exception:
                continue
        return None

    @staticmethod
    def _role_level(role: Optional[str]) -> int:
        hierarchy = {"student": 1, "teacher": 2, "admin": 3}
        return hierarchy.get((role or 'student').lower(), 0)

    async def handle_message(self, client_id: str, raw_message: str) -> bool:
        """Handle a raw JSON message from a client. Returns True if processed, False if rejected/limited."""
        try:
            client = self.connections.get(client_id)
            if not client:
                return False
            ws = client['ws']
            # Parse message JSON
            data = raw_message
            if isinstance(raw_message, (bytes, bytearray)):
                try:
                    data = raw_message.decode('utf-8')
                except Exception:
                    data = str(raw_message)
            if isinstance(data, str):
                try:
                    msg = json.loads(data)
                except Exception:
                    await self._send(ws, {'type': 'error', 'error': 'Invalid JSON'})
                    return False
            elif isinstance(data, dict):
                msg = data
            else:
                await self._send(ws, {'type': 'error', 'error': 'Invalid message format'})
                return False

            msg_type = str(msg.get('type') or '').lower()

            # Rate limit per user and type
            try:
                from apps.backend.services.rate_limit_manager import get_rate_limit_manager
                rlm = get_rate_limit_manager()
                limit = getattr(settings, 'WS_RATE_LIMIT_PER_MINUTE', None) or getattr(settings, 'RATE_LIMIT_PER_MINUTE', 60)
                identifier = f"ws:{client.get('user_id') or client_id}:type:{msg_type or 'message'}"
                allowed, retry_after = await rlm.check_rate_limit(identifier=identifier, max_requests=int(limit), window_seconds=60, source='websocket')
                if not allowed:
                    self._stats['rate_limited'] = self._stats.get('rate_limited', 0) + 1
                    await self._send(ws, {
                        'type': 'error',
                        'error': f'Rate limit exceeded. Retry after {retry_after} seconds'
                    })
                    return False
            except Exception:
                pass

            # Handle subscribe/unsubscribe
            if msg_type == 'subscribe':
                channels = []
                # Accept {channels: [...]} or {'channel': '...'} or str
                payload = msg.get('payload') if isinstance(msg, dict) else None
                if isinstance(msg.get('channels'), list):
                    channels = [str(c) for c in msg.get('channels')]
                elif isinstance(payload, dict) and isinstance(payload.get('channels'), list):
                    channels = [str(c) for c in payload.get('channels')]
                elif isinstance(payload, str):
                    channels = [payload]
                elif isinstance(msg.get('channel'), str):
                    channels = [msg.get('channel')]
                if not channels:
                    await self._send(ws, {'type': 'error', 'error': 'No channels provided'})
                    return True

                subscribed = []
                for ch in channels:
                    if not ch:
                        continue
                    required = self._required_role_for_channel(ch)
                    if required and self._role_level(client.get('user_role')) < self._role_level(required):
                        # Inform forbidden due to role requirement
                        await self._send(ws, {'type': 'error', 'error': f"Channel '{ch}' requires role '{required}'"})
                        continue
                    client['channels'].add(ch)
                    subscribed.append(ch)
                await self._send(ws, {'type': 'subscribed', 'channels': subscribed})
                return True

            if msg_type == 'unsubscribe':
                payload = msg.get('payload') if isinstance(msg, dict) else None
                channels = []
                if isinstance(msg.get('channels'), list):
                    channels = [str(c) for c in msg.get('channels')]
                elif isinstance(payload, dict) and isinstance(payload.get('channels'), list):
                    channels = [str(c) for c in payload.get('channels')]
                elif isinstance(payload, str):
                    channels = [payload]
                elif isinstance(msg.get('channel'), str):
                    channels = [msg.get('channel')]
                for ch in channels:
                    client['channels'].discard(ch)
                await self._send(ws, {'type': 'unsubscribed', 'channels': channels})
                return True

            if msg_type == 'ping':
                await self._send(ws, {'type': 'pong'})
                return True

            # Default ack
            await self._send(ws, {'type': 'ack', 'message': 'ok'})
            return True
        except Exception as e:
            logger.error(f"Error handling message for {client_id}: {e}")
            try:
                client = self.connections.get(client_id)
                if client:
                    await self._send(client['ws'], {'type': 'error', 'error': 'Message handling failed'})
            except Exception:
                pass
            return False

    # Alias expected by tests
    async def handle_client_message(self, client_id: str, raw_message: str) -> bool:
        return await self.handle_message(client_id, raw_message)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        for cid, info in list(self.connections.items()):
            try:
                await self._send(info['ws'], message)
            except Exception as e:
                logger.error(f"Failed to send message to client {cid}: {e}")
                await self.disconnect(cid)

    async def send_to_client(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific client."""
        info = self.connections.get(client_id)
        if info:
            try:
                await self._send(info['ws'], message)
            except Exception as e:
                logger.error(f"Failed to send message to client {client_id}: {e}")
                await self.disconnect(client_id)

    async def _send(self, websocket, payload: Dict[str, Any]):
        # Prefer send_text with JSON for compatibility with tests
        try:
            if hasattr(websocket, 'send_text'):
                # Use ensure_ascii=False to properly handle UTF-8 characters
                # and prevent UTF-16 surrogate pair issues
                json_str = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
                await websocket.send_text(json_str)
                return
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            pass
        # Fallback
        if hasattr(websocket, 'send_json'):
            try:
                await websocket.send_json(payload)
            except Exception as e:
                logger.error(f"Error sending WebSocket JSON: {e}")
                pass

    async def get_connection_stats(self) -> Dict[str, Any]:
        """Return stats about connections, compatible with /ws/status."""
        return {
            'active_connections': len(self.connections),
            **self._stats,
        }

    async def list_channels(self) -> Dict[str, int]:
        """Aggregate channel subscriptions across clients."""
        counts: Dict[str, int] = {}
        for info in self.connections.values():
            for ch in info.get('channels', set()):
                counts[ch] = counts.get(ch, 0) + 1
        return counts

# Create global websocket manager instance
websocket_manager = WebSocketManager()
