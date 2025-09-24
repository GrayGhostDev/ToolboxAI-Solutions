"""
Pusher Handler for Real-time Communication

Replaces WebSocket implementations with Pusher channels for better scalability
and simplified real-time communication management.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timezone

from apps.backend.core.config import settings
from apps.backend.services.pusher import (
    trigger_event as pusher_trigger_event,
    authenticate_channel as pusher_authenticate,
    PusherUnavailable,
)
from apps.backend.services.roblox_ai_agent import roblox_ai_agent
from apps.backend.services.design_file_converter import design_file_converter
from apps.backend.services.design_folder_scanner import design_folder_scanner

logger = logging.getLogger(__name__)


class PusherHandler:
    """Handles real-time communication through Pusher channels"""

    def __init__(self):
        self.active_users: Dict[str, Dict[str, Any]] = {}
        self.channel_subscriptions: Dict[str, Set[str]] = {}  # channel -> set of user_ids
        self.message_handlers = {
            'agent_chat_user': self._handle_agent_chat_user,
            'ai_message': self._handle_ai_message,
            'roblox_agent_request': self._handle_roblox_agent_request,
            'design_file_process': self._handle_design_file_process,
            'design_folder_scan': self._handle_design_folder_scan,
            'design_file_search': self._handle_design_file_search,
            'environment_create': self._handle_environment_create,
            'analytics_request': self._handle_analytics_request,
        }

        # Pusher channel configuration
        self.channels = {
            'public': 'public-updates',  # Public channel for all users
            'content': 'presence-content-updates',  # Content generation updates
            'agent': 'presence-agent-status',  # Agent status updates
            'roblox': 'private-roblox-sync',  # Roblox synchronization
            'analytics': 'presence-analytics-realtime',  # Real-time analytics
            'admin': 'private-admin-broadcast',  # Admin-only broadcasts
        }

    async def handle_message(
        self,
        message_type: str,
        payload: Dict[str, Any],
        user_id: str = None,
        channel: str = None
    ) -> None:
        """Route incoming message to appropriate handler"""
        try:
            handler = self.message_handlers.get(message_type)
            if handler:
                await handler(payload, user_id, channel)
            else:
                logger.warning(f"No handler for message type: {message_type}")
                await self._send_error_message(
                    user_id,
                    f"Unknown message type: {message_type}",
                    channel
                )

        except PusherUnavailable:
            logger.error("Pusher service unavailable")
            # Store message for retry or fallback handling
            await self._queue_message_for_retry(message_type, payload, user_id)

        except Exception as e:
            logger.error(f"Error handling message {message_type}: {e}")
            await self._send_error_message(
                user_id,
                f"Error processing message: {str(e)}",
                channel
            )

    async def _handle_agent_chat_user(
        self,
        payload: Dict[str, Any],
        user_id: str = None,
        channel: str = None
    ) -> None:
        """Handle user chat message to AI agent"""
        try:
            conversation_id = payload.get('conversationId')
            message = payload.get('text') or payload.get('content')
            context = payload.get('context', {})

            if not conversation_id or not message:
                raise ValueError("Missing conversationId or message")

            # Add user context
            if user_id:
                context['user_id'] = user_id

            # Process message with AI agent
            result = await roblox_ai_agent.handle_user_message(
                conversation_id,
                message,
                context
            )

            # Send response through Pusher
            await self._send_to_user(
                user_id,
                {
                    'type': 'agent_response',
                    'conversationId': conversation_id,
                    'response': result
                },
                channel or self.channels['agent']
            )

        except Exception as e:
            logger.error(f"Error handling agent chat user message: {e}")
            raise

    async def _handle_ai_message(
        self,
        payload: Dict[str, Any],
        user_id: str = None,
        channel: str = None
    ) -> None:
        """Handle AI message from frontend"""
        try:
            conversation_id = payload.get('conversation_id')
            message = payload.get('message')
            context = payload.get('context', {})

            if not conversation_id or not message:
                logger.error("Missing conversation_id or message in AI message payload")
                return

            logger.info(f"Processing AI message for conversation {conversation_id}")

            # Add user context
            if user_id:
                context['user_id'] = user_id

            # Process message with AI agent
            response = await roblox_ai_agent.handle_user_message(
                conversation_id,
                message,
                context
            )

            # Send response through Pusher
            await self._send_to_conversation(
                conversation_id,
                {
                    'type': 'ai_response',
                    'response': response,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            )

        except Exception as e:
            logger.error(f"Error handling AI message: {e}")
            raise

    async def _handle_roblox_agent_request(
        self,
        payload: Dict[str, Any],
        user_id: str = None,
        channel: str = None
    ) -> None:
        """Handle Roblox environment generation request"""
        try:
            conversation_id = payload.get('conversationId')
            spec = payload.get('spec', {})

            if not conversation_id or not spec:
                raise ValueError("Missing conversationId or spec")

            # Start environment generation
            result = await roblox_ai_agent.generate_environment(conversation_id, spec)

            # Send progress updates through Pusher
            await self._send_to_channel(
                self.channels['roblox'],
                'environment_generation_started',
                {
                    'conversationId': conversation_id,
                    'spec': spec,
                    'status': 'started'
                }
            )

            # Monitor progress and send updates
            asyncio.create_task(
                self._monitor_environment_generation(
                    conversation_id,
                    user_id
                )
            )

        except Exception as e:
            logger.error(f"Error handling Roblox agent request: {e}")
            raise

    async def _handle_environment_create(
        self,
        payload: Dict[str, Any],
        user_id: str = None,
        channel: str = None
    ) -> None:
        """Handle environment creation request"""
        try:
            environment_type = payload.get('type')
            config = payload.get('config', {})

            logger.info(f"Creating environment: {environment_type}")

            # Send initial status
            await self._send_to_user(
                user_id,
                {
                    'type': 'environment_creation_started',
                    'environment_type': environment_type,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                },
                self.channels['content']
            )

            # Simulate environment creation process
            for progress in [25, 50, 75, 100]:
                await asyncio.sleep(1)  # Simulate work
                await self._send_to_user(
                    user_id,
                    {
                        'type': 'environment_creation_progress',
                        'environment_type': environment_type,
                        'progress': progress,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    },
                    self.channels['content']
                )

            # Send completion
            await self._send_to_user(
                user_id,
                {
                    'type': 'environment_creation_completed',
                    'environment_type': environment_type,
                    'result': {
                        'id': f"env_{environment_type}_{datetime.now().timestamp()}",
                        'status': 'ready'
                    },
                    'timestamp': datetime.now(timezone.utc).isoformat()
                },
                self.channels['content']
            )

        except Exception as e:
            logger.error(f"Error handling environment creation: {e}")
            await self._send_error_message(
                user_id,
                f"Environment creation failed: {str(e)}",
                self.channels['content']
            )

    async def _handle_analytics_request(
        self,
        payload: Dict[str, Any],
        user_id: str = None,
        channel: str = None
    ) -> None:
        """Handle real-time analytics request"""
        try:
            metric_type = payload.get('metric_type', 'all')

            # Generate mock analytics data
            analytics_data = {
                'active_users': 42,
                'courses_in_progress': 15,
                'content_generated_today': 238,
                'average_session_duration': '45m',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            # Send analytics update
            await self._send_to_channel(
                self.channels['analytics'],
                'analytics_update',
                analytics_data
            )

        except Exception as e:
            logger.error(f"Error handling analytics request: {e}")
            raise

    async def _handle_design_file_process(
        self,
        payload: Dict[str, Any],
        user_id: str = None,
        channel: str = None
    ) -> None:
        """Handle design file processing request"""
        try:
            file_path = payload.get('file_path')
            include_content = payload.get('include_content', True)

            if not file_path:
                raise ValueError("Missing file_path")

            logger.info(f"Processing design file: {file_path}")

            # Process the file
            result = await design_file_converter.process_design_file(file_path)

            # Send result through Pusher
            await self._send_to_user(
                user_id,
                {
                    'type': 'design_file_processed',
                    'file_path': file_path,
                    'result': result
                },
                channel or self.channels['content']
            )

        except Exception as e:
            logger.error(f"Error handling design file process: {e}")
            await self._send_error_message(
                user_id,
                f"Design file processing error: {str(e)}",
                channel
            )

    async def _handle_design_folder_scan(
        self,
        payload: Dict[str, Any],
        user_id: str = None,
        channel: str = None
    ) -> None:
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

            # Send result through Pusher
            await self._send_to_user(
                user_id,
                {
                    'type': 'design_folder_scanned',
                    'folder_path': folder_path,
                    'result': result
                },
                channel or self.channels['content']
            )

        except Exception as e:
            logger.error(f"Error handling design folder scan: {e}")
            await self._send_error_message(
                user_id,
                f"Design folder scan error: {str(e)}",
                channel
            )

    async def _handle_design_file_search(
        self,
        payload: Dict[str, Any],
        user_id: str = None,
        channel: str = None
    ) -> None:
        """Handle design file search request"""
        try:
            query = payload.get('query')
            category = payload.get('category')

            if not query:
                raise ValueError("Missing search query")

            logger.info(f"Searching design files: {query} (category: {category})")

            # Search for files
            results = await design_folder_scanner.search_design_files(query, category)

            # Send result through Pusher
            await self._send_to_user(
                user_id,
                {
                    'type': 'design_file_search_results',
                    'query': query,
                    'category': category,
                    'results': results
                },
                channel or self.channels['content']
            )

        except Exception as e:
            logger.error(f"Error handling design file search: {e}")
            await self._send_error_message(
                user_id,
                f"Design file search error: {str(e)}",
                channel
            )

    async def _monitor_environment_generation(
        self,
        conversation_id: str,
        user_id: str
    ) -> None:
        """Monitor environment generation progress and send updates"""
        try:
            progress_steps = [
                (10, "Initializing environment"),
                (25, "Loading assets"),
                (40, "Generating terrain"),
                (60, "Placing objects"),
                (80, "Applying scripts"),
                (95, "Finalizing"),
                (100, "Complete")
            ]

            for progress, status in progress_steps:
                await asyncio.sleep(2)  # Simulate processing time

                await self._send_to_channel(
                    self.channels['roblox'],
                    'environment_generation_progress',
                    {
                        'conversationId': conversation_id,
                        'progress': progress,
                        'status': status,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                )

        except Exception as e:
            logger.error(f"Error monitoring environment generation: {e}")

    async def _send_to_user(
        self,
        user_id: str,
        message: Dict[str, Any],
        channel: str = None
    ) -> None:
        """Send message to specific user through Pusher"""
        try:
            if not user_id:
                return

            # Use user-specific channel or default
            user_channel = f"private-user-{user_id}"

            pusher_trigger_event(
                user_channel,
                "message",
                message
            )

            # Also send to specified channel if provided
            if channel:
                pusher_trigger_event(
                    channel,
                    "message",
                    message
                )

        except PusherUnavailable:
            logger.warning(f"Pusher unavailable, queuing message for user {user_id}")
            await self._queue_message_for_retry("user_message", message, user_id)
        except Exception as e:
            logger.error(f"Error sending message to user {user_id}: {e}")

    async def _send_to_conversation(
        self,
        conversation_id: str,
        message: Dict[str, Any]
    ) -> None:
        """Send message to conversation channel through Pusher"""
        try:
            channel = f"private-conversation-{conversation_id}"
            pusher_trigger_event(
                channel,
                "message",
                message
            )
        except PusherUnavailable:
            logger.warning(f"Pusher unavailable for conversation {conversation_id}")
        except Exception as e:
            logger.error(f"Error sending to conversation {conversation_id}: {e}")

    async def _send_to_channel(
        self,
        channel: str,
        event: str,
        data: Dict[str, Any]
    ) -> None:
        """Send event to specific channel through Pusher"""
        try:
            pusher_trigger_event(channel, event, data)
        except PusherUnavailable:
            logger.warning(f"Pusher unavailable for channel {channel}")
        except Exception as e:
            logger.error(f"Error sending to channel {channel}: {e}")

    async def _send_error_message(
        self,
        user_id: str,
        error_message: str,
        channel: str = None
    ) -> None:
        """Send error message to user"""
        try:
            error_data = {
                'type': 'error',
                'error': error_message,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            if user_id:
                await self._send_to_user(user_id, error_data, channel)
            elif channel:
                await self._send_to_channel(channel, 'error', error_data)

        except Exception as e:
            logger.error(f"Error sending error message: {e}")

    async def _queue_message_for_retry(
        self,
        message_type: str,
        payload: Dict[str, Any],
        user_id: str
    ) -> None:
        """Queue message for retry when Pusher becomes available"""
        # In production, this would use a persistent queue (Redis, RabbitMQ, etc.)
        logger.info(f"Queuing message for retry: {message_type} for user {user_id}")

    async def broadcast_content_update(
        self,
        content_data: Dict[str, Any]
    ) -> None:
        """Broadcast content update to all subscribers"""
        try:
            await self._send_to_channel(
                self.channels['content'],
                'content_update',
                content_data
            )
        except Exception as e:
            logger.error(f"Failed to broadcast content update: {e}")

    def add_user(
        self,
        user_id: str,
        user_info: Dict[str, Any]
    ) -> None:
        """Track active user"""
        self.active_users[user_id] = {
            'info': user_info,
            'connected_at': datetime.now(timezone.utc).isoformat(),
            'channels': set()
        }
        logger.info(f"Added user: {user_id}")

    def remove_user(self, user_id: str) -> None:
        """Remove user from tracking"""
        if user_id in self.active_users:
            # Remove from all channel subscriptions
            for channel in self.active_users[user_id].get('channels', set()):
                if channel in self.channel_subscriptions:
                    self.channel_subscriptions[channel].discard(user_id)

            del self.active_users[user_id]
            logger.info(f"Removed user: {user_id}")

    def subscribe_user_to_channel(
        self,
        user_id: str,
        channel: str
    ) -> bool:
        """Subscribe user to a channel"""
        if user_id not in self.active_users:
            return False

        if channel not in self.channel_subscriptions:
            self.channel_subscriptions[channel] = set()

        self.channel_subscriptions[channel].add(user_id)
        self.active_users[user_id]['channels'].add(channel)

        logger.info(f"User {user_id} subscribed to channel {channel}")
        return True

    def unsubscribe_user_from_channel(
        self,
        user_id: str,
        channel: str
    ) -> bool:
        """Unsubscribe user from a channel"""
        if user_id not in self.active_users:
            return False

        if channel in self.channel_subscriptions:
            self.channel_subscriptions[channel].discard(user_id)

        if 'channels' in self.active_users[user_id]:
            self.active_users[user_id]['channels'].discard(channel)

        logger.info(f"User {user_id} unsubscribed from channel {channel}")
        return True

    def get_user_count(self) -> int:
        """Get number of active users"""
        return len(self.active_users)

    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information"""
        return self.active_users.get(user_id)

    async def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics"""
        return {
            'active_users': len(self.active_users),
            'active_channels': len(self.channel_subscriptions),
            'channel_details': {
                channel: len(users)
                for channel, users in self.channel_subscriptions.items()
            },
            'pusher_enabled': settings.PUSHER_ENABLED,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    async def shutdown(self) -> None:
        """Gracefully shutdown the handler"""
        logger.info(f"Shutting down Pusher handler with {len(self.active_users)} active users")

        # Notify all users about shutdown
        for user_id in list(self.active_users.keys()):
            try:
                await self._send_to_user(
                    user_id,
                    {
                        'type': 'server_shutdown',
                        'message': 'Server is shutting down for maintenance',
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"Error notifying user {user_id} about shutdown: {e}")

        # Clear tracking
        self.active_users.clear()
        self.channel_subscriptions.clear()

        logger.info("Pusher handler shutdown complete")


# Global Pusher handler instance
pusher_handler = PusherHandler()


# Convenience functions for backward compatibility
async def handle_pusher_message(
    message_type: str,
    payload: Dict[str, Any],
    user_id: str = None,
    channel: str = None
) -> None:
    """Handle message through Pusher"""
    await pusher_handler.handle_message(message_type, payload, user_id, channel)


async def broadcast_message(
    channel: str,
    event: str,
    data: Dict[str, Any]
) -> None:
    """Broadcast message to channel"""
    await pusher_handler._send_to_channel(channel, event, data)


async def broadcast_content_update(content_data: Dict[str, Any]) -> None:
    """Broadcast content update to all subscribers"""
    await pusher_handler.broadcast_content_update(content_data)


def add_user(user_id: str, user_info: Dict[str, Any]) -> None:
    """Add user to tracking"""
    pusher_handler.add_user(user_id, user_info)


def remove_user(user_id: str) -> None:
    """Remove user from tracking"""
    pusher_handler.remove_user(user_id)