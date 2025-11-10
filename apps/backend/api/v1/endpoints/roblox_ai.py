"""
Roblox AI Agent API Endpoints

Provides REST API endpoints for the Roblox AI chat agent functionality.
Handles WebSocket message routing and agent communication.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from apps.backend.core.config import settings
from apps.backend.api.auth.auth import get_current_user
from apps.backend.models.schemas import User
from apps.backend.services.roblox.ai_agent import roblox_ai_agent
from apps.backend.services.pusher_realtime import get_pusher_service

pusher_service = get_pusher_service()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/roblox-ai", tags=["roblox-ai"])


# Request/Response Models
class ChatMessageRequest(BaseModel):
    conversation_id: str = Field(..., description="Unique conversation identifier")
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class ChatMessageResponse(BaseModel):
    success: bool
    message: str
    conversation_id: str


class GenerateEnvironmentRequest(BaseModel):
    conversation_id: str = Field(..., description="Conversation identifier")
    spec: Dict[str, Any] = Field(..., description="Environment specification")


class GenerateEnvironmentResponse(BaseModel):
    success: bool
    request_id: str
    message: str


class ConversationStatusResponse(BaseModel):
    conversation_id: str
    spec: Dict[str, Any]
    missing_fields: list[str]
    ready_for_generation: bool


@router.post("/chat", response_model=ChatMessageResponse)
async def send_chat_message(
    request: ChatMessageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Send a message to the Roblox AI agent
    """
    try:
        # Add user context
        context = request.context or {}
        context.update(
            {
                "user_id": current_user.id,
                "user_role": current_user.role,
                "user_name": current_user.display_name,
            }
        )

        # Process message in background
        background_tasks.add_task(
            roblox_ai_agent.handle_user_message, request.conversation_id, request.message, context
        )

        return ChatMessageResponse(
            success=True,
            message="Message received and processing",
            conversation_id=request.conversation_id,
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=GenerateEnvironmentResponse)
async def generate_environment(
    request: GenerateEnvironmentRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    """
    Generate a Roblox environment based on the conversation specification
    """
    try:
        # Validate that spec has required fields
        spec = request.spec
        required_fields = ["environment_name", "theme", "map_type", "learning_objectives"]
        missing_fields = [field for field in required_fields if not spec.get(field)]

        if missing_fields:
            raise HTTPException(
                status_code=400, detail=f"Missing required fields: {', '.join(missing_fields)}"
            )

        # Start generation in background
        background_tasks.add_task(
            roblox_ai_agent.generate_environment, request.conversation_id, spec
        )

        return GenerateEnvironmentResponse(
            success=True,
            request_id=f"req_{request.conversation_id}",
            message="Environment generation started",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation/{conversation_id}/status", response_model=ConversationStatusResponse)
async def get_conversation_status(
    conversation_id: str, current_user: User = Depends(get_current_user)
):
    """
    Get the current status of a conversation
    """
    try:
        spec = roblox_ai_agent.get_conversation_spec(conversation_id)

        # Check for missing required fields
        required_fields = ["environment_name", "theme", "map_type", "learning_objectives"]
        missing_fields = [field for field in required_fields if not spec.get(field)]

        return ConversationStatusResponse(
            conversation_id=conversation_id,
            spec=spec,
            missing_fields=missing_fields,
            ready_for_generation=len(missing_fields) == 0,
        )

    except Exception as e:
        logger.error(f"Error getting conversation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversation/{conversation_id}")
async def clear_conversation(conversation_id: str, current_user: User = Depends(get_current_user)):
    """
    Clear a conversation and its history
    """
    try:
        roblox_ai_agent.clear_conversation(conversation_id)

        return {"success": True, "message": "Conversation cleared"}

    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/pusher")
async def handle_pusher_webhook(request_data: Dict[str, Any]):
    """
    Handle Pusher webhook events for agent chat
    """
    try:
        # Extract event data
        event_type = request_data.get("type")
        payload = request_data.get("payload", {})

        if event_type == "agent_chat_user":
            # Handle user message from WebSocket
            conversation_id = payload.get("conversationId")
            message = payload.get("text")
            context = payload.get("context", {})

            if conversation_id and message:
                await roblox_ai_agent.handle_user_message(conversation_id, message, context)

        elif event_type == "roblox_agent_request":
            # Handle environment generation request
            conversation_id = payload.get("conversationId")
            spec = payload.get("spec", {})

            if conversation_id and spec:
                await roblox_ai_agent.generate_environment(conversation_id, spec)

        return {"success": True}

    except Exception as e:
        logger.error(f"Error in Pusher webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for Roblox AI service"""
    try:
        # Check if AI agent is responsive
        test_spec = roblox_ai_agent.get_conversation_spec("health_check")

        return {
            "status": "healthy",
            "service": "roblox-ai-agent",
            "timestamp": "2024-01-01T00:00:00Z",
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


# Export router
__all__ = ["router"]
