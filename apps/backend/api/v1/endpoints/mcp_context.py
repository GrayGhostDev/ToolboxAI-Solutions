"""
MCP Context API - Pusher + Redis Hybrid Implementation

Replaces custom WebSocket MCP server with:
- Pusher Channels for real-time messaging
- Redis for context storage
- REST API for context operations

This provides the same MCP functionality without maintaining a separate WebSocket server.
"""

import json
from datetime import datetime
from typing import Any
from uuid import uuid4

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from apps.backend.api.auth.auth import get_current_user
from apps.backend.core.config import settings
from apps.backend.core.logging import logging_manager
from apps.backend.models.schemas import User
from apps.backend.services.pusher import trigger_event

logger = logging_manager.get_logger(__name__)

router = APIRouter(prefix="/mcp", tags=["MCP Context"])


# Pydantic Models
class ContextEntry(BaseModel):
    """Agent context entry"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str
    content: dict[str, Any]
    tokens: int = 0
    priority: int = 1  # 1=low, 2=medium, 3=high
    source: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContextUpdate(BaseModel):
    """Context update request"""

    agent_id: str
    content: dict[str, Any]
    source: str
    priority: int = Field(default=1, ge=1, le=3)
    tokens: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContextQuery(BaseModel):
    """Context query filters"""

    agent_id: str | None = None
    source: str | None = None
    min_priority: int = Field(default=1, ge=1, le=3)
    limit: int = Field(default=100, le=1000)


# Redis client (lazy initialization)
_redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """Get Redis client (singleton)"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    return _redis_client


def _get_context_key(agent_id: str, entry_id: str) -> str:
    """Generate Redis key for context entry"""
    return f"mcp:context:{agent_id}:{entry_id}"


def _get_agent_index_key(agent_id: str) -> str:
    """Generate Redis key for agent's context index"""
    return f"mcp:index:{agent_id}"


def _get_token_count_key(agent_id: str) -> str:
    """Generate Redis key for agent's token count"""
    return f"mcp:tokens:{agent_id}"


@router.post("/context", response_model=ContextEntry)
async def add_context(update: ContextUpdate, current_user: User = Depends(get_current_user)):
    """
    Add context entry for an agent

    Stores in Redis and broadcasts via Pusher.
    """
    try:
        redis_client = await get_redis()

        # Create context entry
        entry = ContextEntry(
            agent_id=update.agent_id,
            content=update.content,
            source=update.source,
            priority=update.priority,
            tokens=update.tokens or len(str(update.content)) // 4,  # Rough estimate
            metadata={
                **update.metadata,
                "user_id": current_user.id,
                "created_at": datetime.utcnow().isoformat(),
            },
        )

        # Store in Redis with 1-hour TTL
        context_key = _get_context_key(entry.agent_id, entry.id)
        await redis_client.setex(context_key, 3600, json.dumps(entry.dict()))  # 1 hour TTL

        # Add to agent's index
        index_key = _get_agent_index_key(entry.agent_id)
        await redis_client.sadd(index_key, entry.id)
        await redis_client.expire(index_key, 3600)

        # Update token count
        token_key = _get_token_count_key(entry.agent_id)
        await redis_client.incrby(token_key, entry.tokens)
        await redis_client.expire(token_key, 3600)

        # Broadcast via Pusher
        trigger_event(
            channel=f"agent-{entry.agent_id}",
            event="context.updated",
            data={
                "entry_id": entry.id,
                "source": entry.source,
                "priority": entry.priority,
                "tokens": entry.tokens,
                "timestamp": entry.timestamp.isoformat(),
            },
        )

        logger.info(f"Added context entry {entry.id} for agent {entry.agent_id}")

        return entry

    except Exception as e:
        logger.error(f"Failed to add context: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add context: {str(e)}")


@router.get("/context")
async def get_context(
    agent_id: str | None = Query(None),
    source: str | None = Query(None),
    min_priority: int = Query(1, ge=1, le=3),
    limit: int = Query(100, le=1000),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve context entries

    Filters by agent_id, source, and priority.
    """
    try:
        redis_client = await get_redis()

        # Get all agent IDs if not specified
        if agent_id:
            agent_ids = [agent_id]
        else:
            # Get all agent index keys
            pattern = "mcp:index:*"
            keys = await redis_client.keys(pattern)
            agent_ids = [key.split(":")[-1] for key in keys]

        contexts = []

        for aid in agent_ids:
            # Get entry IDs from index
            index_key = _get_agent_index_key(aid)
            entry_ids = await redis_client.smembers(index_key)

            for entry_id in entry_ids:
                # Get entry data
                context_key = _get_context_key(aid, entry_id)
                data = await redis_client.get(context_key)

                if not data:
                    continue

                entry = json.loads(data)

                # Apply filters
                if source and entry.get("source") != source:
                    continue
                if entry.get("priority", 1) < min_priority:
                    continue

                contexts.append(entry)

        # Sort by priority (high to low) then timestamp (new to old)
        contexts.sort(
            key=lambda x: (
                -x.get("priority", 1),
                -datetime.fromisoformat(x.get("timestamp", "2000-01-01T00:00:00")).timestamp(),
            )
        )

        # Apply limit
        contexts = contexts[:limit]

        return {"status": "success", "count": len(contexts), "contexts": contexts}

    except Exception as e:
        logger.error(f"Failed to get context: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")


@router.delete("/context/{agent_id}")
async def clear_context(agent_id: str, current_user: User = Depends(get_current_user)):
    """
    Clear all context for an agent
    """
    try:
        redis_client = await get_redis()

        # Get all entry IDs
        index_key = _get_agent_index_key(agent_id)
        entry_ids = await redis_client.smembers(index_key)

        # Delete all entries
        deleted_count = 0
        for entry_id in entry_ids:
            context_key = _get_context_key(agent_id, entry_id)
            deleted = await redis_client.delete(context_key)
            deleted_count += deleted

        # Delete index and token count
        await redis_client.delete(index_key)
        token_key = _get_token_count_key(agent_id)
        await redis_client.delete(token_key)

        # Broadcast via Pusher
        trigger_event(
            channel=f"agent-{agent_id}",
            event="context.cleared",
            data={"agent_id": agent_id, "deleted_count": deleted_count},
        )

        logger.info(f"Cleared {deleted_count} context entries for agent {agent_id}")

        return {"status": "success", "agent_id": agent_id, "deleted_count": deleted_count}

    except Exception as e:
        logger.error(f"Failed to clear context: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear context: {str(e)}")


@router.put("/context/{agent_id}/{entry_id}/priority")
async def set_priority(
    agent_id: str,
    entry_id: str,
    priority: int = Query(..., ge=1, le=3),
    current_user: User = Depends(get_current_user),
):
    """
    Update priority of a context entry
    """
    try:
        redis_client = await get_redis()

        # Get entry
        context_key = _get_context_key(agent_id, entry_id)
        data = await redis_client.get(context_key)

        if not data:
            raise HTTPException(status_code=404, detail="Context entry not found")

        entry = json.loads(data)
        old_priority = entry.get("priority", 1)
        entry["priority"] = priority

        # Update in Redis
        await redis_client.setex(context_key, 3600, json.dumps(entry))

        # Broadcast via Pusher
        trigger_event(
            channel=f"agent-{agent_id}",
            event="context.priority_updated",
            data={"entry_id": entry_id, "old_priority": old_priority, "new_priority": priority},
        )

        logger.info(f"Updated priority for {entry_id}: {old_priority} → {priority}")

        return {
            "status": "success",
            "entry_id": entry_id,
            "old_priority": old_priority,
            "new_priority": priority,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set priority: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set priority: {str(e)}")


@router.get("/status")
async def get_mcp_status(current_user: User = Depends(get_current_user)):
    """
    Get MCP system status

    Returns statistics about context storage and active agents.
    """
    try:
        redis_client = await get_redis()

        # Get all agent index keys
        index_keys = await redis_client.keys("mcp:index:*")
        agent_count = len(index_keys)

        # Get total context entries and tokens
        total_contexts = 0
        total_tokens = 0

        for key in index_keys:
            entry_count = await redis_client.scard(key)
            total_contexts += entry_count

            agent_id = key.split(":")[-1]
            token_key = _get_token_count_key(agent_id)
            tokens = await redis_client.get(token_key)
            total_tokens += int(tokens or 0)

        # Redis info
        redis_info = await redis_client.info("memory")

        return {
            "status": "healthy",
            "implementation": "pusher_redis_hybrid",
            "agents": {"count": agent_count, "active": agent_count},  # All with contexts are active
            "context": {
                "total_entries": total_contexts,
                "total_tokens": total_tokens,
                "token_limit": 128000,  # GPT-4 context limit
                "utilization": round(total_tokens / 128000 * 100, 2),
            },
            "redis": {"used_memory": redis_info.get("used_memory_human"), "connected": True},
            "pusher": {
                "enabled": bool(settings.PUSHER_APP_ID),
                "channels_active": agent_count,  # One channel per agent
            },
        }

    except Exception as e:
        logger.error(f"Failed to get MCP status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")
