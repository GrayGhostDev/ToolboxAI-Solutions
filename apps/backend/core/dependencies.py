"""
Centralized dependency injection for the FastAPI application
"""

import asyncio
from functools import lru_cache
from typing import Optional, AsyncGenerator

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.core.config import settings
from apps.backend.core.logging import logging_manager
from apps.backend.services.database import db_service
from apps.backend.core.auth import get_current_user  # Use unified auth
from apps.backend.models.schemas import User

# Initialize logger
logger = logging_manager.get_logger(__name__)


# Database dependencies
async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async with db_service.get_session() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


# Settings dependency
@lru_cache()
def get_settings():
    """Get application settings (cached)"""
    return settings


# Authentication dependencies
async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if hasattr(current_user, "is_active") and not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    return current_user


async def get_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current user with admin privileges"""
    if not hasattr(current_user, "role") or current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )
    return current_user


# Service dependencies
@lru_cache()
def get_agent_service():
    """Get agent service instance"""
    try:
        from apps.backend.services.agent_service import get_agent_service

        return get_agent_service()
    except ImportError as e:
        logger.warning(f"Agent service not available: {e}")
        return None


@lru_cache()
def get_pusher_service():
    """Get Pusher service instance"""
    try:
        from apps.backend.services.pusher_realtime import get_pusher_service

        return get_pusher_service()
    except ImportError as e:
        logger.warning(f"Pusher service not available: {e}")
        return None


@lru_cache()
def get_mcp_service():
    """Get MCP service instance"""
    try:
        from core.mcp.server import MCPServer

        return MCPServer()
    except ImportError as e:
        logger.warning(f"MCP service not available: {e}")
        return None


# Health check dependencies
async def check_database_health() -> bool:
    """Check database connectivity"""
    try:
        async with db_service.get_session() as session:
            # Simple query to check connectivity
            result = await session.execute("SELECT 1")
            return bool(result.scalar())
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def check_redis_health() -> bool:
    """Check Redis connectivity"""
    try:
        # Import Redis service if available
        from apps.backend.core.redis.connection import redis_service

        return await redis_service.ping()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False


# Rate limiting dependencies
def get_rate_limit_key(request) -> str:
    """Generate rate limit key from request"""
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "unknown")
    return f"rate_limit:{client_ip}:{hash(user_agent)}"


# Validation dependencies
def validate_content_id(content_id: str) -> str:
    """Validate content ID format"""
    if not content_id or len(content_id) < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid content ID")
    return content_id


def validate_agent_id(agent_id: str) -> str:
    """Validate agent ID format"""
    if not agent_id or len(agent_id) < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid agent ID")
    return agent_id


# WebSocket dependencies
class WebSocketConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: dict = {}
        self.connection_count = 0

    async def connect(self, websocket, client_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_count += 1
        logger.info(f"WebSocket connected: {client_id} (total: {self.connection_count})")

    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            self.connection_count -= 1
            logger.info(f"WebSocket disconnected: {client_id} (total: {self.connection_count})")

    async def send_personal_message(self, message: str, client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast(self, message: str):
        """Broadcast message to all connected clients"""
        disconnected = []
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send broadcast to {client_id}: {e}")
                disconnected.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)


# Global WebSocket manager instance
websocket_manager = WebSocketConnectionManager()


def get_websocket_manager() -> WebSocketConnectionManager:
    """Get WebSocket connection manager"""
    return websocket_manager


# Error handling dependencies
def handle_validation_error(error: Exception) -> HTTPException:
    """Convert validation errors to HTTP exceptions"""
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error))


def handle_database_error(error: Exception) -> HTTPException:
    """Convert database errors to HTTP exceptions"""
    logger.error(f"Database error: {error}")
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database operation failed"
    )


def handle_external_service_error(error: Exception) -> HTTPException:
    """Convert external service errors to HTTP exceptions"""
    logger.error(f"External service error: {error}")
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="External service temporarily unavailable",
    )
