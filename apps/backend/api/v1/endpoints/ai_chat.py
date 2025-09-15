"""AI Chat API Endpoints for Roblox Educational Assistant

Provides a conversational AI interface to help teachers create Roblox educational environments.
Integrates with LangChain/LangGraph for intelligent content generation and guidance.
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, status
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import logging
import json
import uuid
import asyncio
from pydantic import BaseModel, Field, field_validator
from enum import Enum

# Import dependencies
try:
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from langgraph.graph import StateGraph, END
    from langgraph_checkpoint_sqlite import SqliteSaver
except ImportError as e:
    logging.warning(f"LangChain imports failed: {e}. Running in mock mode.")
    ChatAnthropic = None
    StateGraph = None
    SqliteSaver = None

# Authentication imports
try:
    from apps.backend.api.auth.auth import get_current_user
except ImportError:
    try:
        from auth.auth import get_current_user
    except ImportError:
        # Fallback for development
        def get_current_user():
            from pydantic import BaseModel
            class MockUser(BaseModel):
                email: str = "test@example.com"
                role: str = "teacher"
                id: Optional[str] = "test_user_id"
            return MockUser()

# Model imports
try:
    from apps.backend.models.schemas import User, BaseResponse
except ImportError:
    try:
        from apps.backend.models.schemas import User, BaseResponse
    except ImportError:
        # Fallback models
        class User(BaseModel):
            email: str
            role: str
            id: Optional[str] = None

        class BaseResponse(BaseModel):
            success: bool = True
            message: str = ""
            timestamp: datetime = Field(default_factory=datetime.utcnow)
            request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

ANTHROPIC_API_KEY = None  # Will be loaded from environment
MODEL_NAME = "claude-3-5-sonnet-latest"
MAX_CONVERSATION_LENGTH = 100  # Maximum messages in a conversation
CHECKPOINT_DIR = "/tmp/langgraph_checkpoints"  # Directory for conversation persistence

# =============================================================================
# ENUMS & MODELS
# =============================================================================

class MessageRole(str, Enum):
    """Message roles in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ConversationStatus(str, Enum):
    """Conversation status"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    GENERATING = "generating"

class IntentType(str, Enum):
    """User intent classification"""
    CREATE_LESSON = "create_lesson"
    DESIGN_ENVIRONMENT = "design_environment"
    GENERATE_QUIZ = "generate_quiz"
    MODIFY_CONTENT = "modify_content"
    GET_HELP = "get_help"
    PREVIEW = "preview"
    DEPLOY = "deploy"
    UNCLEAR = "unclear"

# Request/Response Models
class CreateConversationRequest(BaseModel):
    """Create new conversation"""
    title: Optional[str] = Field(None, description="Conversation title")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Initial context")

class SendMessageRequest(BaseModel):
    """Send message in conversation"""
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="File attachments")

    @field_validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()

class MessageResponse(BaseModel):
    """Single message in conversation"""
    id: str = Field(..., description="Message ID")
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class ConversationResponse(BaseModel):
    """Conversation with messages"""
    id: str = Field(..., description="Conversation ID")
    title: str = Field(..., description="Conversation title")
    status: ConversationStatus = Field(..., description="Conversation status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    messages: List[MessageResponse] = Field(..., description="Conversation messages")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Conversation metadata")

class StreamingToken(BaseModel):
    """Streaming response token"""
    token: str = Field(..., description="Token text")
    is_final: bool = Field(default=False, description="Is this the final token")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Token metadata")

# =============================================================================
# LANGGRAPH STATE & WORKFLOW
# =============================================================================

class ConversationState(BaseModel):
    """State for LangGraph conversation workflow"""
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    intent: Optional[IntentType] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    current_task: Optional[str] = None
    generated_content: Optional[Dict[str, Any]] = None

class RobloxAssistantGraph:
    """LangGraph workflow for Roblox educational assistant"""

    def __init__(self, api_key: str = None):
        """Initialize the assistant graph"""
        self.api_key = api_key
        self.llm = None
        self.graph = None
        self.checkpointer = None

        if ChatAnthropic and api_key:
            self.llm = ChatAnthropic(
                anthropic_api_key=api_key,
                model=MODEL_NAME,
                streaming=True,
                temperature=0.7
            )
            self._build_graph()

    def _build_graph(self):
        """Build the LangGraph workflow"""
        if not StateGraph:
            return

        # Create workflow
        workflow = StateGraph(ConversationState)

        # Add nodes
        workflow.add_node("classify_intent", self.classify_intent)
        workflow.add_node("plan_content", self.plan_content)
        workflow.add_node("generate_resources", self.generate_resources)
        workflow.add_node("create_preview", self.create_preview)
        workflow.add_node("prepare_response", self.prepare_response)

        # Add edges
        workflow.set_entry_point("classify_intent")
        workflow.add_edge("classify_intent", "plan_content")
        workflow.add_edge("plan_content", "generate_resources")
        workflow.add_edge("generate_resources", "create_preview")
        workflow.add_edge("create_preview", "prepare_response")
        workflow.add_edge("prepare_response", END)

        # Set up checkpointer for persistence
        if SqliteSaver:
            self.checkpointer = SqliteSaver.from_conn_string(f"{CHECKPOINT_DIR}/conversations.db")
            self.graph = workflow.compile(checkpointer=self.checkpointer)
        else:
            self.graph = workflow.compile()

    async def classify_intent(self, state: ConversationState) -> ConversationState:
        """Classify user intent from message"""
        if not self.llm or not state.messages:
            state.intent = IntentType.UNCLEAR
            return state

        last_message = state.messages[-1]["content"]

        # Simple intent classification (expand with better prompting)
        intent_prompt = f"""Classify the user's intent from this message:
        "{last_message}"

        Possible intents:
        - create_lesson: User wants to create educational content
        - design_environment: User wants to design a Roblox environment
        - generate_quiz: User wants to create assessments
        - modify_content: User wants to change existing content
        - preview: User wants to see a preview
        - deploy: User wants to deploy content
        - get_help: User needs assistance
        - unclear: Intent is not clear

        Respond with just the intent type."""

        try:
            response = await self.llm.ainvoke([SystemMessage(content=intent_prompt)])
            intent_str = response.content.strip().lower()

            # Map to IntentType
            intent_map = {
                "create_lesson": IntentType.CREATE_LESSON,
                "design_environment": IntentType.DESIGN_ENVIRONMENT,
                "generate_quiz": IntentType.GENERATE_QUIZ,
                "modify_content": IntentType.MODIFY_CONTENT,
                "preview": IntentType.PREVIEW,
                "deploy": IntentType.DEPLOY,
                "get_help": IntentType.GET_HELP,
            }

            state.intent = intent_map.get(intent_str, IntentType.UNCLEAR)
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            state.intent = IntentType.UNCLEAR

        return state

    async def plan_content(self, state: ConversationState) -> ConversationState:
        """Plan content based on intent"""
        # Generate content plan based on intent (works even without LLM)
        if state.intent == IntentType.CREATE_LESSON:
            state.current_task = "Creating educational lesson plan"
        elif state.intent == IntentType.DESIGN_ENVIRONMENT:
            state.current_task = "Designing Roblox environment"
        elif state.intent == IntentType.GENERATE_QUIZ:
            state.current_task = "Generating assessment quiz"
        else:
            state.current_task = "Processing request"

        state.context["task_started"] = datetime.utcnow().isoformat()
        return state

    async def generate_resources(self, state: ConversationState) -> ConversationState:
        """Generate educational resources by calling Roblox content generation"""
        # Generate appropriate resources based on intent
        state.generated_content = {
            "type": state.intent.value if state.intent else "general",
            "status": "generating",
            "timestamp": datetime.utcnow().isoformat()
        }

        if not self.llm:
            # In mock mode, still generate content structure
            state.generated_content["status"] = "generated"
            return state

        # Call Roblox content generation API if appropriate intent
        if state.intent in [IntentType.CREATE_LESSON, IntentType.DESIGN_ENVIRONMENT, IntentType.GENERATE_QUIZ]:
            try:
                # Import here to avoid circular imports
                from httpx import AsyncClient
                from typing import Literal

                # Map intent to content type
                content_type_map = {
                    IntentType.CREATE_LESSON: "lesson",
                    IntentType.DESIGN_ENVIRONMENT: "environment",
                    IntentType.GENERATE_QUIZ: "quiz"
                }

                # Extract parameters from conversation
                last_message = state.messages[-1]["content"] if state.messages else ""

                # Call Roblox content generation endpoint
                async with AsyncClient() as client:
                    response = await client.post(
                        "http://127.0.0.1:8008/api/v1/roblox/content/generate",
                        json={
                            "content_type": content_type_map.get(state.intent, "lesson"),
                            "subject": state.context.get("subject", "General"),
                            "grade_level": state.context.get("grade_level", 6),
                            "difficulty": state.context.get("difficulty", "intermediate"),
                            "learning_objectives": state.context.get("learning_objectives", []),
                            "description": last_message,
                            "ai_assistance": True,
                            "include_quiz": state.intent == IntentType.GENERATE_QUIZ,
                            "terrain_type": "educational_playground" if state.intent == IntentType.DESIGN_ENVIRONMENT else None
                        },
                        headers={
                            "Authorization": f"Bearer {state.context.get('auth_token', '')}"
                        }
                    )

                    if response.status_code in [200, 201, 202]:
                        content_data = response.json()
                        state.generated_content["content_id"] = content_data.get("content_id")
                        state.generated_content["status"] = "generated"
                        state.generated_content["roblox_data"] = content_data
                    else:
                        logger.warning(f"Roblox content generation failed: {response.status_code}")
                        state.generated_content["status"] = "failed"

            except Exception as e:
                logger.error(f"Failed to generate Roblox content: {e}")
                state.generated_content["status"] = "error"
                state.generated_content["error"] = str(e)

        return state

    async def create_preview(self, state: ConversationState) -> ConversationState:
        """Create preview data for visualization"""
        # Add preview generation logic
        if state.generated_content:
            state.generated_content["preview"] = {
                "available": True,
                "type": "3d_environment",
                "data": {}  # Placeholder for 3D preview data
            }

        return state

    async def prepare_response(self, state: ConversationState) -> ConversationState:
        """Prepare final response"""
        # Format the response for the user
        return state

    async def process_message(self, conversation_id: str, message: str) -> AsyncGenerator[str, None]:
        """Process a message and stream response"""
        try:
            # If we have a real LLM, use it
            if self.llm:
                # Create state with context
                state = ConversationState(
                    messages=[{"role": "user", "content": message}],
                    context={"conversation_id": conversation_id}
                )

                # Run workflow
                if self.graph:
                    config = {"configurable": {"thread_id": conversation_id}}
                    result = await self.graph.ainvoke(state, config)

                    # Generate contextual response based on intent and generated content
                    if result.intent == IntentType.CREATE_LESSON:
                        if result.generated_content and result.generated_content.get("status") == "generated":
                            response_text = f"Great! I've started creating your educational lesson. Content ID: {result.generated_content.get('content_id', 'pending')}. "
                            response_text += "The lesson will include interactive elements, assessments, and age-appropriate content. "
                            response_text += "You can preview it in the Environment Preview tab once it's ready."
                        else:
                            response_text = "Let's create an engaging lesson! What subject and grade level are you targeting?"

                    elif result.intent == IntentType.DESIGN_ENVIRONMENT:
                        if result.generated_content and result.generated_content.get("status") == "generated":
                            response_text = f"Excellent! Your Roblox environment is being generated. Content ID: {result.generated_content.get('content_id', 'pending')}. "
                            response_text += "I'm creating an immersive 3D space with interactive elements. "
                            response_text += "The environment will be optimized for educational gameplay."
                        else:
                            response_text = "I'll help you design an amazing environment! Would you like a space station, medieval castle, or modern classroom?"

                    elif result.intent == IntentType.GENERATE_QUIZ:
                        if result.generated_content and result.generated_content.get("status") == "generated":
                            response_text = f"Perfect! Your interactive quiz is being created. Content ID: {result.generated_content.get('content_id', 'pending')}. "
                            response_text += "It will include multiple choice, true/false, and interactive challenges. "
                            response_text += "Students will earn points and badges for correct answers."
                        else:
                            response_text = "Let's create an engaging quiz! How many questions would you like, and what topics should we cover?"

                    else:
                        response_text = "I'm your Roblox Educational Assistant! I can help you:\n"
                        response_text += "• Create interactive lessons with 3D environments\n"
                        response_text += "• Design immersive educational spaces\n"
                        response_text += "• Generate quizzes and assessments\n"
                        response_text += "• Deploy content to Roblox Studio\n"
                        response_text += "What would you like to create today?"

                    # Stream the response
                    for word in response_text.split():
                        yield word + " "
                        await asyncio.sleep(0.03)  # Faster streaming
                else:
                    yield "Setting up AI assistant... Please try again in a moment."
            else:
                # Mock mode - provide helpful responses
                if "lesson" in message.lower():
                    response = "I'll help you create an educational lesson! To get started, I need to know: What subject are you teaching? What grade level? What are your main learning objectives?"
                elif "environment" in message.lower() or "world" in message.lower():
                    response = "Let's design an amazing Roblox environment! I can create: Space stations for science, Medieval castles for history, Modern cities for social studies, or Custom themed worlds. Which interests you?"
                elif "quiz" in message.lower() or "test" in message.lower():
                    response = "I'll create an interactive quiz for your students! Should we include: Multiple choice questions, True/false challenges, Fill-in-the-blank activities, or Puzzle-based assessments?"
                elif "help" in message.lower():
                    response = "I'm here to help! I can: Create lessons, Design 3D environments, Generate quizzes, Preview content, Deploy to Roblox. Just tell me what you need!"
                else:
                    response = "I'm ready to help you create engaging Roblox educational content! Try asking me to create a lesson, design an environment, or generate a quiz."

                # Stream mock response
                for word in response.split():
                    yield word + " "
                    await asyncio.sleep(0.03)

        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            yield f"I encountered an issue: {str(e)}. Please try rephrasing your request."

# =============================================================================
# IN-MEMORY STORAGE (Replace with database in production)
# =============================================================================

conversations: Dict[str, Dict[str, Any]] = {}
messages: Dict[str, List[Dict[str, Any]]] = {}

# Global assistant instance
assistant_graph = None

# =============================================================================
# WEBSOCKET CONNECTION MANAGER
# =============================================================================

class ChatConnectionManager:
    """Manages WebSocket connections for chat"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str):
        """Connect websocket to conversation"""
        await websocket.accept()
        self.active_connections[conversation_id] = websocket
        logger.info(f"WebSocket connected to conversation {conversation_id}")

    def disconnect(self, conversation_id: str):
        """Disconnect websocket from conversation"""
        if conversation_id in self.active_connections:
            del self.active_connections[conversation_id]
            logger.info(f"WebSocket disconnected from conversation {conversation_id}")

    async def send_message(self, conversation_id: str, message: dict):
        """Send message to specific conversation"""
        if conversation_id in self.active_connections:
            try:
                await self.active_connections[conversation_id].send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                self.disconnect(conversation_id)

    async def broadcast(self, message: dict):
        """Broadcast message to all connections"""
        disconnected = []
        for conv_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except:
                disconnected.append(conv_id)

        # Clean up disconnected
        for conv_id in disconnected:
            self.disconnect(conv_id)

# Global connection manager
chat_manager = ChatConnectionManager()

# =============================================================================
# ROUTER SETUP
# =============================================================================

router = APIRouter(prefix="/ai-chat", tags=["AI Chat"])

# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: CreateConversationRequest,
    current_user: User = Depends(get_current_user)
) -> ConversationResponse:
    """Create a new AI chat conversation"""

    # Generate conversation ID
    conversation_id = f"conv_{uuid.uuid4().hex[:12]}"

    # Create conversation
    conversation = {
        "id": conversation_id,
        "title": request.title or "New Roblox Assistant Chat",
        "status": ConversationStatus.ACTIVE.value,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "user_id": current_user.id if hasattr(current_user, 'id') else current_user.email,
        "metadata": {
            "context": request.context or {},
            "user_role": current_user.role
        }
    }

    # Store conversation
    conversations[conversation_id] = conversation
    messages[conversation_id] = []

    # Add system message
    system_msg = {
        "id": f"msg_{uuid.uuid4().hex[:12]}",
        "role": MessageRole.SYSTEM.value,
        "content": "Hello! I'm your Roblox Educational Assistant. I'll help you create engaging educational environments for your students. What would you like to create today?",
        "timestamp": datetime.utcnow(),
        "metadata": {"type": "greeting"}
    }
    messages[conversation_id].append(system_msg)

    logger.info(f"Created conversation {conversation_id} for user {current_user.email}")

    return ConversationResponse(
        **conversation,
        messages=[MessageResponse(**system_msg)]
    )

@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> MessageResponse:
    """Send a message and receive AI response"""

    # Verify conversation exists
    if conversation_id not in conversations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )

    # Verify user owns conversation
    conversation = conversations[conversation_id]
    if conversation["user_id"] != (current_user.id if hasattr(current_user, 'id') else current_user.email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this conversation"
        )

    # Create user message
    user_msg = {
        "id": f"msg_{uuid.uuid4().hex[:12]}",
        "role": MessageRole.USER.value,
        "content": request.message,
        "timestamp": datetime.utcnow(),
        "metadata": {"attachments": request.attachments} if request.attachments else None
    }

    # Add to messages
    messages[conversation_id].append(user_msg)

    # Update conversation
    conversation["updated_at"] = datetime.utcnow()
    conversation["status"] = ConversationStatus.GENERATING.value

    # Schedule AI response generation
    background_tasks.add_task(
        generate_ai_response,
        conversation_id,
        request.message,
        current_user
    )

    logger.info(f"Message sent to conversation {conversation_id}")

    return MessageResponse(**user_msg)

@router.post("/generate", response_model=MessageResponse)
async def generate_ai_response_endpoint(
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user)
) -> MessageResponse:
    """Generate AI response for a single message (convenience endpoint)"""

    # Create a temporary conversation for this single interaction
    conversation_id = f"temp_{uuid.uuid4().hex[:8]}"

    # Create temporary conversation
    conversations[conversation_id] = {
        "id": conversation_id,
        "title": "AI Assistant Chat",
        "status": ConversationStatus.ACTIVE,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "user_id": current_user.id if hasattr(current_user, 'id') else current_user.email,
        "metadata": {"temporary": True}
    }

    # Initialize messages for this conversation
    if conversation_id not in messages:
        messages[conversation_id] = []

    # Add user message
    user_msg = {
        "id": f"msg_{uuid.uuid4().hex[:8]}",
        "role": MessageRole.USER,
        "content": request.message,
        "timestamp": datetime.utcnow(),
        "metadata": {"attachments": request.attachments or []}
    }
    messages[conversation_id].append(user_msg)

    # Generate AI response
    try:
        if assistant_graph:
            # Use the actual LangGraph workflow
            response_text = ""
            async for token in assistant_graph.process_message(conversation_id, request.message):
                # Token is already a string from the async generator
                response_text += token

            ai_msg = {
                "id": f"msg_{uuid.uuid4().hex[:8]}",
                "role": MessageRole.ASSISTANT,
                "content": response_text,
                "timestamp": datetime.utcnow(),
                "metadata": {"generated": True}
            }
        else:
            # Mock response for development
            ai_msg = {
                "id": f"msg_{uuid.uuid4().hex[:8]}",
                "role": MessageRole.ASSISTANT,
                "content": f"I understand you want to: {request.message}\n\nI'm here to help you create educational Roblox environments! Could you tell me more about:\n- What grade level is this for?\n- What subject area?\n- What specific learning objectives?\n- How many students will participate?\n\nOnce I have these details, I can help you design the perfect educational environment!",
                "timestamp": datetime.utcnow(),
                "metadata": {"generated": True, "mock": True}
            }

        messages[conversation_id].append(ai_msg)

        # Clean up temporary conversation after a delay
        asyncio.create_task(cleanup_temp_conversation(conversation_id))

        return MessageResponse(**ai_msg)

    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate AI response: {str(e)}"
        )

async def cleanup_temp_conversation(conversation_id: str):
    """Clean up temporary conversation after 5 minutes"""
    await asyncio.sleep(300)  # 5 minutes
    if conversation_id in conversations:
        del conversations[conversation_id]
    if conversation_id in messages:
        del messages[conversation_id]

@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
) -> ConversationResponse:
    """Get conversation with all messages"""

    # Verify conversation exists
    if conversation_id not in conversations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )

    conversation = conversations[conversation_id]

    # Verify user owns conversation
    if conversation["user_id"] != (current_user.id if hasattr(current_user, 'id') else current_user.email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this conversation"
        )

    # Get messages
    conversation_messages = messages.get(conversation_id, [])

    return ConversationResponse(
        **conversation,
        messages=[MessageResponse(**msg) for msg in conversation_messages]
    )

@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0
) -> List[ConversationResponse]:
    """List user's conversations"""

    user_id = current_user.id if hasattr(current_user, 'id') else current_user.email

    # Filter user's conversations
    user_conversations = [
        conv for conv in conversations.values()
        if conv["user_id"] == user_id
    ]

    # Sort by updated_at
    user_conversations.sort(key=lambda x: x["updated_at"], reverse=True)

    # Paginate
    paginated = user_conversations[offset:offset + limit]

    # Return with messages
    result = []
    for conv in paginated:
        conv_messages = messages.get(conv["id"], [])
        result.append(ConversationResponse(
            **conv,
            messages=[MessageResponse(**msg) for msg in conv_messages[-10:]]  # Last 10 messages
        ))

    return result

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Archive/delete a conversation"""

    # Verify conversation exists
    if conversation_id not in conversations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )

    conversation = conversations[conversation_id]

    # Verify user owns conversation
    if conversation["user_id"] != (current_user.id if hasattr(current_user, 'id') else current_user.email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this conversation"
        )

    # Archive instead of delete
    conversation["status"] = ConversationStatus.ARCHIVED.value
    conversation["archived_at"] = datetime.utcnow()

    logger.info(f"Archived conversation {conversation_id}")

# =============================================================================
# WEBSOCKET ENDPOINT
# =============================================================================

@router.websocket("/ws/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str):
    """WebSocket endpoint for real-time chat streaming"""

    await chat_manager.connect(websocket, conversation_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            if data.get("type") == "message":
                message = data.get("content", "")

                # Stream AI response
                await websocket.send_json({
                    "type": "stream_start",
                    "timestamp": datetime.utcnow().isoformat()
                })

                # Process with assistant
                if assistant_graph:
                    async for token in assistant_graph.process_message(conversation_id, message):
                        await websocket.send_json({
                            "type": "stream_token",
                            "content": token,
                            "timestamp": datetime.utcnow().isoformat()
                        })
                else:
                    # Mock response
                    response = "I'll help you create an amazing Roblox educational experience!"
                    for word in response.split():
                        await websocket.send_json({
                            "type": "stream_token",
                            "content": word + " ",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        await asyncio.sleep(0.05)

                await websocket.send_json({
                    "type": "stream_end",
                    "timestamp": datetime.utcnow().isoformat()
                })

            elif data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        chat_manager.disconnect(conversation_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        chat_manager.disconnect(conversation_id)

# =============================================================================
# BACKGROUND TASKS
# =============================================================================

async def generate_ai_response(conversation_id: str, user_message: str, user: User):
    """Generate AI response in background"""

    try:
        # Simulate processing delay
        await asyncio.sleep(1)

        # Generate response (use actual LangGraph in production)
        if assistant_graph:
            response_text = ""
            async for token in assistant_graph.process_message(conversation_id, user_message):
                response_text += token
        else:
            # Mock response based on message content
            if "lesson" in user_message.lower():
                response_text = "I'll help you create an engaging lesson! Let's start by defining the subject and grade level. What subject will this lesson cover?"
            elif "environment" in user_message.lower():
                response_text = "Great! Let's design a Roblox environment. Would you like to start with a template (space station, medieval castle, modern classroom) or create something custom?"
            elif "quiz" in user_message.lower():
                response_text = "Let's create an interactive quiz! How many questions would you like, and should it include multiple choice, true/false, or both?"
            else:
                response_text = "I understand you want to create educational content for Roblox. Could you tell me more about your learning objectives?"

        # Create AI message
        ai_msg = {
            "id": f"msg_{uuid.uuid4().hex[:12]}",
            "role": MessageRole.ASSISTANT.value,
            "content": response_text,
            "timestamp": datetime.utcnow(),
            "metadata": {"generated": True}
        }

        # Add to messages
        messages[conversation_id].append(ai_msg)

        # Update conversation status
        conversations[conversation_id]["status"] = ConversationStatus.ACTIVE.value
        conversations[conversation_id]["updated_at"] = datetime.utcnow()

        # Send via WebSocket if connected
        await chat_manager.send_message(conversation_id, {
            "type": "ai_message",
            "message": ai_msg,
            "timestamp": datetime.utcnow().isoformat()
        })

        logger.info(f"Generated AI response for conversation {conversation_id}")

    except Exception as e:
        logger.error(f"Failed to generate AI response: {e}")
        conversations[conversation_id]["status"] = ConversationStatus.ACTIVE.value

# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_assistant():
    """Initialize the assistant with API key"""
    global assistant_graph

    import os
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if api_key and ChatAnthropic:
        assistant_graph = RobloxAssistantGraph(api_key)
        logger.info("Roblox Assistant initialized with Anthropic")
    else:
        assistant_graph = RobloxAssistantGraph()  # Mock mode
        logger.warning("Roblox Assistant running in mock mode")

# Initialize on module load
initialize_assistant()

# Export router
__all__ = ["router", "chat_manager", "assistant_graph"]
