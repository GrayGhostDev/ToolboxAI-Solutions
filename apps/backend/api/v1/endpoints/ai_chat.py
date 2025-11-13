"""AI Chat API Endpoints for Roblox Educational Assistant

Provides a conversational AI interface to help teachers create Roblox educational environments.
Integrates with LangChain/LangGraph for intelligent content generation and guidance.
"""

import asyncio
import json
import logging
import time
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

# Import dependencies
try:
    # Skip LangChain imports temporarily due to Pydantic v2 compatibility issues
    # from langchain_openai import ChatOpenAI
    # from langchain_anthropic import ChatAnthropic
    # from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    # from langchain.memory import ConversationBufferMemory
    # from langgraph.graph import StateGraph, END
    # from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    # from langgraph.checkpoint.sqlite import SqliteSaver
    LANGCHAIN_AVAILABLE = False
    logging.warning(
        "LangChain temporarily disabled due to Pydantic v2 compatibility. Using direct OpenAI API."
    )
except ImportError as e:
    logging.warning(f"LangChain imports failed: {e}. Will use direct API.")
    LANGCHAIN_AVAILABLE = False
    ChatOpenAI = None
    ChatAnthropic = None
    StateGraph = None

# Direct API imports for scalable async operations
try:
    import anthropic
    from anthropic import Anthropic, AsyncAnthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    logging.warning("Anthropic library not available")
    ANTHROPIC_AVAILABLE = False
    Anthropic = None
    AsyncAnthropic = None

try:
    import openai
    from openai import AsyncOpenAI, OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    logging.warning("OpenAI library not available")
    OPENAI_AVAILABLE = False
    OpenAI = None
    AsyncOpenAI = None

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
                id: str | None = "test_user_id"

            return MockUser()


# Model imports
try:
    from apps.backend.models.schemas import BaseResponse, User
except ImportError:
    try:
        from apps.backend.models.schemas import BaseResponse, User
    except ImportError:
        # Fallback models
        class User(BaseModel):
            email: str
            role: str
            id: str | None = None

        class BaseResponse(BaseModel):
            success: bool = True
            message: str = ""
            timestamp: datetime = Field(default_factory=datetime.utcnow)
            request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

import os

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Latest models as of 2025
# Anthropic Claude Models
ANTHROPIC_MODEL_OPUS = (
    "claude-opus-4-1-20250805"  # Most capable Claude model ($15/$75 per M tokens)
)
ANTHROPIC_MODEL_SONNET = (
    "claude-sonnet-4-20250514"  # Balanced performance/cost ($3/$15 per M tokens)
)
# Allow environment variable override
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", ANTHROPIC_MODEL_OPUS)  # Default to Opus

# OpenAI GPT Models
OPENAI_MODEL_4O = "gpt-4o"  # GPT-4 Omni - 2x faster, 50% cheaper than Turbo
OPENAI_MODEL_4O_MINI = "gpt-4o-mini"  # Smaller, faster version of GPT-4o
OPENAI_MODEL_TURBO = "gpt-4-turbo"  # Latest GPT-4 Turbo (stable)
OPENAI_MODEL_41 = "gpt-4-1-preview"  # GPT-4.1 if available
# Allow environment variable override
OPENAI_MODEL = os.getenv("OPENAI_MODEL", OPENAI_MODEL_4O)  # Default to GPT-4o

MAX_CONVERSATION_LENGTH = 100  # Maximum messages in a conversation
CHECKPOINT_DIR = "/tmp/langgraph_checkpoints"  # Directory for conversation persistence


# Educational content stages
class ContentStage(str, Enum):
    """8-stage educational content creation flow"""

    INTENT = "intent_understanding"
    REQUIREMENTS = "requirements_gathering"
    PLANNING = "content_planning"
    DESIGN = "interactive_design"
    ASSESSMENT = "assessment_creation"
    REVIEW = "review_refinement"
    DEPLOYMENT = "deployment_preparation"
    DELIVERY = "final_delivery"


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

    title: str | None = Field(None, description="Conversation title")
    context: dict[str, Any] | None = Field(default_factory=dict, description="Initial context")


class SendMessageRequest(BaseModel):
    """Send message in conversation"""

    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    attachments: list[dict[str, Any]] | None = Field(None, description="File attachments")

    @field_validator("message")
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


class MessageResponse(BaseModel):
    """Single message in conversation"""

    id: str = Field(..., description="Message ID")
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")


class ConversationResponse(BaseModel):
    """Conversation with messages"""

    id: str = Field(..., description="Conversation ID")
    title: str = Field(..., description="Conversation title")
    status: ConversationStatus = Field(..., description="Conversation status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    messages: list[MessageResponse] = Field(..., description="Conversation messages")
    metadata: dict[str, Any] | None = Field(None, description="Conversation metadata")


class StreamingToken(BaseModel):
    """Streaming response token"""

    token: str = Field(..., description="Token text")
    is_final: bool = Field(default=False, description="Is this the final token")
    metadata: dict[str, Any] | None = Field(None, description="Token metadata")


# =============================================================================
# LANGGRAPH STATE & WORKFLOW
# =============================================================================


class ConversationState(BaseModel):
    """State for LangGraph conversation workflow"""

    messages: list[dict[str, Any]] = Field(default_factory=list)
    intent: IntentType | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    current_task: str | None = None
    generated_content: dict[str, Any] | None = None


class RobloxAssistantGraph:
    """LangGraph workflow for Roblox educational assistant"""

    def __init__(self, anthropic_key: str = None, openai_key: str = None):
        """Initialize the assistant graph with Anthropic or OpenAI for scalable async operations"""
        self.anthropic_key = anthropic_key
        self.openai_key = openai_key
        self.llm = None
        self.graph = None
        self.checkpointer = None
        # Use async clients for scalability
        self.anthropic_client = None
        self.async_anthropic_client = None
        self.openai_client = None
        self.async_openai_client = None
        self.conversation_memory = {}

        # Setup BOTH Anthropic and OpenAI for automatic fallback
        clients_initialized = []

        # Setup Anthropic if key available
        if anthropic_key and ANTHROPIC_AVAILABLE:
            try:
                # Setup both sync and async clients for flexibility
                self.anthropic_client = Anthropic(api_key=anthropic_key)
                self.async_anthropic_client = AsyncAnthropic(api_key=anthropic_key)
                clients_initialized.append(f"Anthropic Claude ({ANTHROPIC_MODEL})")
                logger.info(f"Initialized Anthropic Claude ({ANTHROPIC_MODEL}) for primary LLM")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic: {e}")

        # Setup OpenAI if key available (as fallback or primary)
        if openai_key and OPENAI_AVAILABLE:
            try:
                # Setup both sync and async clients for flexibility
                self.openai_client = OpenAI(api_key=openai_key)
                self.async_openai_client = AsyncOpenAI(api_key=openai_key)
                clients_initialized.append(f"OpenAI ({OPENAI_MODEL})")
                logger.info(
                    f"Initialized OpenAI ({OPENAI_MODEL}) as {'fallback' if self.async_anthropic_client else 'primary'} LLM"
                )
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")

        # Setup LangChain if available (as additional fallback)
        if LANGCHAIN_AVAILABLE:
            if anthropic_key and ChatAnthropic and not self.llm:
                try:
                    self.llm = ChatAnthropic(
                        api_key=anthropic_key,
                        model=ANTHROPIC_MODEL,
                        streaming=True,
                        temperature=0.7,
                        max_tokens=4096,
                    )
                    self._build_graph()
                    clients_initialized.append("LangChain + Anthropic")
                except Exception as e:
                    logger.warning(f"Failed to initialize LangChain with Anthropic: {e}")

            if openai_key and ChatOpenAI and not self.llm:
                try:
                    self.llm = ChatOpenAI(
                        api_key=openai_key, model=OPENAI_MODEL, streaming=True, temperature=0.7
                    )
                    self._build_graph()
                    clients_initialized.append("LangChain + OpenAI")
                except Exception as e:
                    logger.warning(f"Failed to initialize LangChain with OpenAI: {e}")

        # Log initialization status
        if clients_initialized:
            logger.info(f"AI Assistant ready with: {', '.join(clients_initialized)}")
        else:
            logger.warning("No LLM clients initialized, running in mock mode")

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
            "timestamp": datetime.utcnow().isoformat(),
        }

        if not self.llm:
            # In mock mode, still generate content structure
            state.generated_content["status"] = "generated"
            return state

        # Call Roblox content generation API if appropriate intent
        if state.intent in [
            IntentType.CREATE_LESSON,
            IntentType.DESIGN_ENVIRONMENT,
            IntentType.GENERATE_QUIZ,
        ]:
            try:
                # Import here to avoid circular imports

                from httpx import AsyncClient

                # Map intent to content type
                content_type_map = {
                    IntentType.CREATE_LESSON: "lesson",
                    IntentType.DESIGN_ENVIRONMENT: "environment",
                    IntentType.GENERATE_QUIZ: "quiz",
                }

                # Extract parameters from conversation
                last_message = state.messages[-1]["content"] if state.messages else ""

                # Call Roblox content generation endpoint
                async with AsyncClient() as client:
                    response = await client.post(
                        "http://127.0.0.1:8009/api/v1/roblox/content/generate",
                        json={
                            "content_type": content_type_map.get(state.intent, "lesson"),
                            "subject": state.context.get("subject", "General"),
                            "grade_level": state.context.get("grade_level", 6),
                            "difficulty": state.context.get("difficulty", "intermediate"),
                            "learning_objectives": state.context.get("learning_objectives", []),
                            "description": last_message,
                            "ai_assistance": True,
                            "include_quiz": state.intent == IntentType.GENERATE_QUIZ,
                            "terrain_type": (
                                "educational_playground"
                                if state.intent == IntentType.DESIGN_ENVIRONMENT
                                else None
                            ),
                        },
                        headers={"Authorization": f"Bearer {state.context.get('auth_token', '')}"},
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
                "data": {},  # Placeholder for 3D preview data
            }

        return state

    async def prepare_response(self, state: ConversationState) -> ConversationState:
        """Prepare final response"""
        # Format the response for the user
        return state

    async def process_message(
        self, conversation_id: str, message: str
    ) -> AsyncGenerator[str, None]:
        """Process a message and stream response with full context and automatic fallback"""
        try:
            # Get conversation history
            if conversation_id not in self.conversation_memory:
                self.conversation_memory[conversation_id] = {
                    "messages": [],
                    "stage": ContentStage.INTENT,
                    "context": {},
                    "requirements": {},
                }

            memory = self.conversation_memory[conversation_id]
            memory["messages"].append({"role": "user", "content": message})

            # Extract context from ENTIRE conversation history
            import re

            full_conversation = " ".join([msg["content"].lower() for msg in memory["messages"]])
            current_message_lower = message.lower()

            # Enhanced grade extraction (handles "4th grade", "4th grader", "grade 4", etc.)
            grade_patterns = [
                (r"(kindergarten|k-\d|k\d)", "kindergarten"),
                (r"(1st|first|grade 1)\s*(?:grade|grader)?", "1st grade"),
                (r"(2nd|second|grade 2)\s*(?:grade|grader)?", "2nd grade"),
                (r"(3rd|third|grade 3)\s*(?:grade|grader)?", "3rd grade"),
                (r"(4th|fourth|grade 4)\s*(?:grade|grader)?", "4th grade"),
                (r"(5th|fifth|grade 5)\s*(?:grade|grader)?", "5th grade"),
                (r"(6th|sixth|grade 6)\s*(?:grade|grader)?", "6th grade"),
                (r"(7th|seventh|grade 7)\s*(?:grade|grader)?", "7th grade"),
                (r"(8th|eighth|grade 8)\s*(?:grade|grader)?", "8th grade"),
                (r"(9th|ninth|grade 9)\s*(?:grade|grader)?", "9th grade"),
                (r"(10th|tenth|grade 10)\s*(?:grade|grader)?", "10th grade"),
                (r"(11th|eleventh|grade 11)\s*(?:grade|grader)?", "11th grade"),
                (r"(12th|twelfth|grade 12)\s*(?:grade|grader)?", "12th grade"),
            ]

            if "grade" not in memory["context"]:
                for pattern, grade_value in grade_patterns:
                    if re.search(pattern, full_conversation):
                        memory["context"]["grade"] = grade_value
                        break

            # Enhanced subject extraction (consolidated, no conflicts)
            if "subject" not in memory["context"]:
                subjects = {
                    "math": [
                        "math",
                        "mathematics",
                        "fraction",
                        "pizza",
                        "multiplication",
                        "division",
                        "geometry",
                        "algebra",
                        "number",
                        "equation",
                        "calculation",
                    ],
                    "science": [
                        "science",
                        "biology",
                        "chemistry",
                        "physics",
                        "ecosystem",
                        "solar",
                        "planet",
                        "experiment",
                        "lab",
                        "atoms",
                    ],
                    "history": [
                        "history",
                        "historical",
                        "ancient",
                        "civilization",
                        "american",
                        "world war",
                        "timeline",
                        "museum",
                        "past",
                    ],
                    "english": [
                        "english",
                        "reading",
                        "writing",
                        "grammar",
                        "vocabulary",
                        "literature",
                        "story",
                        "poem",
                        "essay",
                    ],
                }

                for subject, keywords in subjects.items():
                    if any(keyword in full_conversation for keyword in keywords):
                        memory["context"]["subject"] = subject
                        break

            # Extract specific topic if mentioned (e.g., "fractions", "solar system")
            if "topic" not in memory["context"]:
                topics = {
                    "fractions": [
                        "fraction",
                        "pizza",
                        "parts",
                        "halves",
                        "thirds",
                        "fourths",
                        "eighths",
                        "pieces",
                    ],
                    "solar system": [
                        "solar",
                        "planet",
                        "space",
                        "mars",
                        "jupiter",
                        "saturn",
                        "orbit",
                    ],
                    "ancient civilizations": [
                        "ancient",
                        "egypt",
                        "rome",
                        "greece",
                        "civilization",
                        "museum",
                    ],
                    "ecosystems": [
                        "ecosystem",
                        "habitat",
                        "animal",
                        "plant",
                        "environment",
                        "food chain",
                    ],
                }

                for topic, keywords in topics.items():
                    if any(keyword in full_conversation for keyword in keywords):
                        memory["context"]["topic"] = topic
                        break

            # Extract class size from full conversation
            if "class_size" not in memory["context"]:
                size_match = re.search(
                    r"(\d+)\s*(?:students?|kids?|children|learners?)", full_conversation
                )
                if size_match:
                    memory["context"]["class_size"] = int(size_match.group(1))

            # Extract game style preference from full conversation
            if "style" not in memory["context"]:
                if any(
                    word in full_conversation
                    for word in [
                        "game",
                        "play",
                        "fun",
                        "interactive",
                        "adventure",
                        "quest",
                        "simulation",
                    ]
                ):
                    memory["context"]["style"] = "game"
                elif any(
                    word in full_conversation
                    for word in ["worksheet", "quiz", "test", "assessment", "questions"]
                ):
                    memory["context"]["style"] = "assessment"

            # Check if user is giving creative control
            if any(
                phrase in current_message_lower
                for phrase in [
                    "you choose",
                    "you decide",
                    "i trust you",
                    "up to you",
                    "your call",
                    "surprise me",
                ]
            ):
                memory["context"]["user_control"] = "delegated"

            # Determine if we have enough information to complete
            has_grade = "grade" in memory["context"]
            has_subject = "subject" in memory["context"] or "topic" in memory["context"]
            has_style = "style" in memory["context"]
            has_class_size = "class_size" in memory["context"]
            message_count = len(memory["messages"])

            # Force completion conditions
            should_complete = False
            if memory["context"].get("user_control") == "delegated":
                should_complete = True
                memory["context"]["force_complete"] = "User delegated control - DESIGN NOW!"
            elif has_grade and has_subject and (has_style or has_class_size):
                should_complete = True
                memory["context"][
                    "force_complete"
                ] = "Have sufficient information - PRESENT DESIGN!"
            elif message_count >= 6:  # 3 user messages + 3 AI messages
                should_complete = True
                memory["context"]["force_complete"] = "Maximum exchanges reached - COMPLETE NOW!"

            if should_complete:
                memory["context"]["MUST_COMPLETE"] = True

            # Try Anthropic first, then fallback to OpenAI, then LangChain
            response_generated = False

            # First try: Anthropic API (direct)
            if self.async_anthropic_client and not response_generated:
                try:
                    # Build messages for Anthropic
                    anthropic_messages = []
                    system_content = f"""You are a friendly educational consultant helping teachers design engaging Roblox learning experiences.

{'🚨 URGENT: ' + memory['context'].get('force_complete', '') if memory['context'].get('MUST_COMPLETE') else ''}

⚠️ CRITICAL RULES:
• NEVER ask for information already provided below
• DO NOT ask "What subject?" or "What grade?" if already known
• Maximum 3-4 total exchanges before presenting complete design
• If user says "you choose", IMMEDIATELY design something specific

📊 KNOWN INFORMATION (DO NOT ASK ABOUT THESE):
{chr(10).join([f"✓ {k.upper()}: {v}" for k, v in memory['context'].items() if k not in ['MUST_COMPLETE', 'force_complete', 'user_control']])}

📈 Conversation Progress: {len(memory['messages'])} messages exchanged

{'''🎯 COMPLETION REQUIRED NOW!
You MUST present a complete design with:
1. "🎯 GOT IT!" header
2. Full environment description
3. All features and mechanics
4. Assessment tools
5. HTML button: <button style="background: linear-gradient(135deg, #00ff88, #00aaff); color: #0a0a0a; padding: 15px 40px; font-size: 18px; font-weight: bold; border-radius: 8px; cursor: pointer;">🌟 View My World</button>
6. Timer: <div>⏱️ Rendering Time: <span id="timer">00:00</span></div>''' if memory['context'].get('MUST_COMPLETE') else '''YOUR NEXT STEP:
• If you have grade + subject + style/size → Present complete design
• If missing critical info → Ask ONE specific question
• Never repeat questions about known information'''}

{f"🔴 USER GAVE YOU CONTROL: {memory['context'].get('user_control')} - CREATE SOMETHING NOW!" if memory['context'].get('user_control') == 'delegated' else ""}"""

                    for msg in memory["messages"]:
                        anthropic_messages.append({"role": msg["role"], "content": msg["content"]})

                    # Generate response with async Anthropic for better scalability
                    stream = await self.async_anthropic_client.messages.create(
                        model=ANTHROPIC_MODEL,
                        messages=anthropic_messages,
                        system=system_content,
                        stream=True,
                        max_tokens=4096,
                        temperature=0.7,
                    )

                    response_text = ""
                    async for chunk in stream:
                        if chunk.type == "content_block_delta":
                            content = chunk.delta.text
                            response_text += content
                            yield content

                    # Save assistant response to memory
                    memory["messages"].append({"role": "assistant", "content": response_text})
                    response_generated = True
                    logger.info(f"Response generated with Anthropic Claude ({ANTHROPIC_MODEL})")

                except Exception as e:
                    logger.warning(f"Anthropic API failed: {e}, trying OpenAI fallback")

            # Second try: OpenAI API (fallback)
            if self.async_openai_client and not response_generated:
                try:
                    # Build messages for OpenAI
                    openai_messages = [
                        {
                            "role": "system",
                            "content": f"""You are a friendly educational consultant helping teachers design engaging Roblox learning experiences.

{'🚨 URGENT: ' + memory['context'].get('force_complete', '') if memory['context'].get('MUST_COMPLETE') else ''}

⚠️ CRITICAL RULES:
• NEVER ask for information already provided below
• DO NOT ask "What subject?" or "What grade?" if already known
• Maximum 3-4 total exchanges before presenting complete design
• If user says "you choose", IMMEDIATELY design something specific

📊 KNOWN INFORMATION (DO NOT ASK ABOUT THESE):
{chr(10).join([f"✓ {k.upper()}: {v}" for k, v in memory['context'].items() if k not in ['MUST_COMPLETE', 'force_complete', 'user_control']])}

📈 Conversation Progress: {len(memory['messages'])} messages exchanged

{'''🎯 COMPLETION REQUIRED NOW!
You MUST present a complete design with:
1. "🎯 GOT IT!" header
2. Full environment description
3. All features and mechanics
4. Assessment tools
5. HTML button: <button style="background: linear-gradient(135deg, #00ff88, #00aaff); color: #0a0a0a; padding: 15px 40px; font-size: 18px; font-weight: bold; border-radius: 8px; cursor: pointer;">🌟 View My World</button>
6. Timer: <div>⏱️ Rendering Time: <span id="timer">00:00</span></div>''' if memory['context'].get('MUST_COMPLETE') else '''YOUR NEXT STEP:
• If you have grade + subject + style/size → Present complete design
• If missing critical info → Ask ONE specific question
• Never repeat questions about known information'''}

{f"🔴 USER GAVE YOU CONTROL: {memory['context'].get('user_control')} - CREATE SOMETHING NOW!" if memory['context'].get('user_control') == 'delegated' else ""}""",
                        }
                    ]
                    openai_messages.extend(memory["messages"])

                    # Generate response with async OpenAI for better scalability
                    stream = await self.async_openai_client.chat.completions.create(
                        model=OPENAI_MODEL, messages=openai_messages, stream=True, temperature=0.7
                    )

                    response_text = ""
                    async for chunk in stream:
                        if chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            response_text += content
                            yield content

                    # Save assistant response to memory
                    memory["messages"].append({"role": "assistant", "content": response_text})
                    response_generated = True
                    logger.info(
                        f"Response generated with OpenAI ({OPENAI_MODEL}) after Anthropic fallback"
                    )

                except Exception as e:
                    logger.warning(f"OpenAI API failed: {e}, trying LangChain fallback")

            # Third try: LangChain if available (Anthropic or OpenAI)
            if self.llm and not response_generated:
                try:
                    # Build conversation context with system prompt
                    system_prompt = """You are a friendly educational consultant helping teachers design engaging Roblox learning experiences.

                    CONVERSATION FLOW RULES:
                    • Track what's been discussed - NEVER repeat questions
                    • Maximum 3-4 total clarifying questions
                    • If user says "you choose" or "I trust you", immediately create specific design
                    • After basic understanding, present "🎯 GOT IT!" with complete design

                    YOUR PROGRESSION:
                    Stage 1: Quick info gathering (1-2 exchanges)
                    Stage 2: Smart assumptions
                    Stage 3: Complete design with "GOT IT!" message and View My World button

                    Current stage: {stage}
                    Context: {context}
                    Messages so far: {len(messages) if 'messages' in locals() else 0}

                    IMPORTANT:
                    • Move conversation FORWARD each message
                    • Include ALL features in final design
                    • End with View My World button and timer display"""

                    # Format messages for the LLM
                    formatted_messages = [
                        SystemMessage(
                            content=system_prompt.format(
                                stage=memory["stage"], context=json.dumps(memory["context"])
                            )
                        )
                    ]

                    for msg in memory["messages"]:
                        if msg["role"] == "user":
                            formatted_messages.append(HumanMessage(content=msg["content"]))
                        elif msg["role"] == "assistant":
                            formatted_messages.append(AIMessage(content=msg["content"]))

                    # Generate response with LangChain
                    response_text = ""
                    async for chunk in self.llm.astream(formatted_messages):
                        if hasattr(chunk, "content"):
                            response_text += chunk.content
                            yield chunk.content

                    # Save assistant response to memory
                    memory["messages"].append({"role": "assistant", "content": response_text})
                    response_generated = True
                    logger.info("Response generated with LangChain after direct API fallback")

                except Exception as e:
                    logger.warning(f"LangChain failed: {e}, using contextual fallback")

            # Final fallback: Context-aware response without LLM
            if not response_generated:
                # Improved fallback without LLM - context-aware responses
                response = self._generate_contextual_fallback(message, memory)

                # Stream response
                for word in response.split():
                    yield word + " "
                    await asyncio.sleep(0.03)

                # Save response to memory
                memory["messages"].append({"role": "assistant", "content": response})
                logger.info("Using contextual fallback response (no LLM available)")

        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            yield f"I encountered an issue: {str(e)}. Let me try to help you with creating Roblox educational content. What would you like to create?"

    def _generate_contextual_fallback(self, message: str, memory: dict) -> str:
        """Generate context-aware fallback responses without LLM"""
        # Check conversation history for context
        last_messages = (
            memory["messages"][-3:] if len(memory["messages"]) >= 3 else memory["messages"]
        )

        # Check if this is a follow-up to a quiz discussion
        discussing_quiz = any("quiz" in msg.get("content", "").lower() for msg in last_messages)

        if discussing_quiz and "puzzle" in message.lower():
            return "Puzzle-based assessments are perfect for making learning about the solar system more engaging! Students love solving challenges while they learn. What specific concepts about the solar system would you like the puzzles to focus on? For example, we could create puzzles about planetary order, identifying moons, or understanding orbital patterns. What aspects are most important for your students to master?"
        elif "solar system" in message.lower() or "5th grade" in message.lower():
            memory["context"]["subject"] = "solar system"
            memory["context"]["grade"] = "5th grade"
            return "A 5th grade solar system simulation sounds fantastic! Students at that age are naturally curious about space. I can help you design an experience where they can explore planets and discover facts through gameplay. What are the main learning objectives you want to achieve? For example, should students learn about planetary characteristics, the scale of the solar system, or how gravity works? And would you like to include any assessments or challenges to check their understanding?"
        elif "quiz" in message.lower():
            return "Interactive quizzes are a great way to check understanding while keeping students engaged! There are many fun ways to assess learning in a game environment. Would you prefer traditional question formats like multiple choice, or something more creative like puzzle challenges, scavenger hunts, or problem-solving missions? What approach would work best for your students' learning style?"
        else:
            return "Hello! I'm here to help you create an amazing educational experience in Roblox for your students. Whether you're teaching math, science, history, or any other subject, we can design something both engaging and educational. To get started, could you tell me what subject you teach and what grade level your students are?"


# =============================================================================
# IN-MEMORY STORAGE (Replace with database in production)
# =============================================================================

conversations: dict[str, dict[str, Any]] = {}
messages: dict[str, list[dict[str, Any]]] = {}

# Global assistant instance
assistant_graph = None

# =============================================================================
# WEBSOCKET CONNECTION MANAGER
# =============================================================================


class ChatConnectionManager:
    """Manages WebSocket connections for chat"""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

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


@router.post(
    "/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED
)
async def create_conversation(
    request: CreateConversationRequest, current_user: User = Depends(get_current_user)
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
        "user_id": current_user.id if hasattr(current_user, "id") else current_user.email,
        "metadata": {"context": request.context or {}, "user_role": current_user.role},
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
        "metadata": {"type": "greeting"},
    }
    messages[conversation_id].append(system_msg)

    logger.info(f"Created conversation {conversation_id} for user {current_user.email}")

    return ConversationResponse(**conversation, messages=[MessageResponse(**system_msg)])


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """Send a message and receive AI response"""

    # Verify conversation exists
    if conversation_id not in conversations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    # Verify user owns conversation
    conversation = conversations[conversation_id]
    if conversation["user_id"] != (
        current_user.id if hasattr(current_user, "id") else current_user.email
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this conversation"
        )

    # Create user message
    user_msg = {
        "id": f"msg_{uuid.uuid4().hex[:12]}",
        "role": MessageRole.USER.value,
        "content": request.message,
        "timestamp": datetime.utcnow(),
        "metadata": {"attachments": request.attachments} if request.attachments else None,
    }

    # Add to messages
    messages[conversation_id].append(user_msg)

    # Update conversation
    conversation["updated_at"] = datetime.utcnow()
    conversation["status"] = ConversationStatus.GENERATING.value

    # Schedule AI response generation
    background_tasks.add_task(generate_ai_response, conversation_id, request.message, current_user)

    logger.info(f"Message sent to conversation {conversation_id}")

    return MessageResponse(**user_msg)


@router.post("/generate")
async def generate_ai_response_endpoint(
    request: SendMessageRequest, current_user: User = Depends(get_current_user)
):
    """
    Generate AI-powered educational content with streaming response.

    Uses Anthropic Claude and OpenAI models to generate contextual educational
    content for Roblox environments. Supports real-time streaming for immediate
    user feedback and conversation memory for context-aware responses.

    Args:
        request (SendMessageRequest): Message request containing:
            - message (str): User's prompt or question
            - attachments (optional): File attachments for context

    Returns:
        StreamingResponse: Server-sent events stream containing:
            - start: Generation initiation
            - token: Incremental response tokens
            - complete: Final response with full message

    Authentication:
        Required: JWT token in Authorization header

    Permissions:
        All authenticated users

    Rate Limit:
        5 requests per minute for content generation

    Features:
        - Context-aware conversation memory
        - Automatic completion after 3-4 exchanges
        - Creative delegation support ("you choose")
        - Multi-model fallback (Anthropic → OpenAI → Mock)
        - Grade level and subject extraction
        - Pusher integration for notifications

    Example:
        ```python
        async with client.stream('POST', '/ai-chat/generate', json={
            "message": "Create a 5th grade solar system lesson"
        }) as response:
            async for line in response.aiter_lines():
                data = json.loads(line)
                if data["type"] == "token":
                    print(data["content"], end="")
        ```
    """

    # Extract conversation_id from request or create temporary one
    conversation_id = getattr(request, "conversation_id", None)
    if not conversation_id:
        conversation_id = f"temp_{uuid.uuid4().hex[:8]}"
        conversations[conversation_id] = {
            "id": conversation_id,
            "title": "AI Assistant Chat",
            "status": ConversationStatus.ACTIVE,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "user_id": current_user.id if hasattr(current_user, "id") else current_user.email,
            "metadata": {"temporary": True},
        }
        messages[conversation_id] = []

    # Add user message
    user_msg = {
        "id": f"msg_{uuid.uuid4().hex[:8]}",
        "role": MessageRole.USER,
        "content": request.message,
        "timestamp": datetime.utcnow(),
        "metadata": {"attachments": request.attachments or []},
    }
    messages[conversation_id].append(user_msg)

    async def stream_response():
        """Stream the AI response with fast initial response"""
        start_time = time.time()
        response_text = ""
        ai_msg_id = f"msg_{uuid.uuid4().hex[:8]}"

        try:
            # Send immediate acknowledgment
            yield json.dumps(
                {"type": "start", "id": ai_msg_id, "timestamp": datetime.utcnow().isoformat()}
            ) + "\n"

            # If using assistant_graph, stream the response
            if assistant_graph:
                # Quick initial response while LLM initializes
                quick_text = "Let me help you with that"
                for char in quick_text:
                    yield json.dumps({"type": "token", "content": char}) + "\n"
                    await asyncio.sleep(0.01)
                yield json.dumps({"type": "token", "content": "... "}) + "\n"

                # Stream actual LLM response
                async for token in assistant_graph.process_message(
                    conversation_id, request.message
                ):
                    response_text += token
                    yield json.dumps({"type": "token", "content": token}) + "\n"

                    # Timeout protection
                    if time.time() - start_time > 55:
                        yield json.dumps(
                            {
                                "type": "token",
                                "content": "\n\n[Response truncated due to time limit. Please continue the conversation.]",
                            }
                        ) + "\n"
                        response_text += "\n\n[Response truncated due to time limit. Please continue the conversation.]"
                        break
            else:
                # Fast mock response for when assistant is not available
                mock_response = f"I understand you want to: {request.message}\n\nI'm here to help you create educational Roblox environments!"
                for word in mock_response.split():
                    response_text += word + " "
                    yield json.dumps({"type": "token", "content": word + " "}) + "\n"
                    await asyncio.sleep(0.02)

            # Save the complete message
            ai_msg = {
                "id": ai_msg_id,
                "role": MessageRole.ASSISTANT.value,
                "content": response_text.strip(),
                "timestamp": datetime.utcnow(),
                "metadata": {"generated": True, "streaming": True},
            }
            messages[conversation_id].append(ai_msg)

            # Send completion signal with full message
            yield json.dumps(
                {
                    "type": "complete",
                    "message": {
                        "id": ai_msg["id"],
                        "role": ai_msg["role"],
                        "content": ai_msg["content"],
                        "timestamp": ai_msg["timestamp"].isoformat(),
                        "metadata": ai_msg["metadata"],
                    },
                }
            ) + "\n"

            # Also send via Pusher for other connected clients
            try:
                from apps.backend.services.pusher import trigger_event

                channel = f"ai-chat-{conversation_id}"
                trigger_event(
                    channel=channel,
                    event="ai_response",
                    data={"conversation_id": conversation_id, "message": ai_msg},
                )
                logger.info(f"Sent AI response via Pusher to channel {channel}")
            except Exception as e:
                logger.warning(f"Pusher notification failed: {e}")

            # Clean up temp conversation later
            asyncio.create_task(cleanup_temp_conversation(conversation_id))

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield json.dumps({"type": "error", "error": str(e)}) + "\n"

    return StreamingResponse(
        stream_response(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},  # Disable nginx buffering
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
    conversation_id: str, current_user: User = Depends(get_current_user)
) -> ConversationResponse:
    """Get conversation with all messages"""

    # Verify conversation exists
    if conversation_id not in conversations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    conversation = conversations[conversation_id]

    # Verify user owns conversation
    if conversation["user_id"] != (
        current_user.id if hasattr(current_user, "id") else current_user.email
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this conversation"
        )

    # Get messages
    conversation_messages = messages.get(conversation_id, [])

    return ConversationResponse(
        **conversation, messages=[MessageResponse(**msg) for msg in conversation_messages]
    )


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user), limit: int = 20, offset: int = 0
) -> list[ConversationResponse]:
    """List user's conversations"""

    user_id = current_user.id if hasattr(current_user, "id") else current_user.email

    # Filter user's conversations
    user_conversations = [conv for conv in conversations.values() if conv["user_id"] == user_id]

    # Sort by updated_at
    user_conversations.sort(key=lambda x: x["updated_at"], reverse=True)

    # Paginate
    paginated = user_conversations[offset : offset + limit]

    # Return with messages
    result = []
    for conv in paginated:
        conv_messages = messages.get(conv["id"], [])
        result.append(
            ConversationResponse(
                **conv,
                messages=[
                    MessageResponse(**msg) for msg in conv_messages[-10:]
                ],  # Last 10 messages
            )
        )

    return result


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: str, current_user: User = Depends(get_current_user)):
    """Archive/delete a conversation"""

    # Verify conversation exists
    if conversation_id not in conversations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    conversation = conversations[conversation_id]

    # Verify user owns conversation
    if conversation["user_id"] != (
        current_user.id if hasattr(current_user, "id") else current_user.email
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this conversation"
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
                await websocket.send_json(
                    {"type": "stream_start", "timestamp": datetime.utcnow().isoformat()}
                )

                # Process with assistant
                if assistant_graph:
                    async for token in assistant_graph.process_message(conversation_id, message):
                        await websocket.send_json(
                            {
                                "type": "stream_token",
                                "content": token,
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )
                else:
                    # Mock response
                    response = "I'll help you create an amazing Roblox educational experience!"
                    for word in response.split():
                        await websocket.send_json(
                            {
                                "type": "stream_token",
                                "content": word + " ",
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )
                        await asyncio.sleep(0.05)

                await websocket.send_json(
                    {"type": "stream_end", "timestamp": datetime.utcnow().isoformat()}
                )

            elif data.get("type") == "ping":
                await websocket.send_json(
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                )

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
            "metadata": {"generated": True},
        }

        # Add to messages
        messages[conversation_id].append(ai_msg)

        # Update conversation status
        conversations[conversation_id]["status"] = ConversationStatus.ACTIVE.value
        conversations[conversation_id]["updated_at"] = datetime.utcnow()

        # Send via WebSocket if connected
        await chat_manager.send_message(
            conversation_id,
            {"type": "ai_message", "message": ai_msg, "timestamp": datetime.utcnow().isoformat()},
        )

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

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if anthropic_key or openai_key:
        assistant_graph = RobloxAssistantGraph(anthropic_key=anthropic_key, openai_key=openai_key)
        if anthropic_key:
            logger.info("Roblox Assistant initialized with Anthropic Claude")
        else:
            logger.info("Roblox Assistant initialized with OpenAI")
    else:
        assistant_graph = RobloxAssistantGraph()  # Mock mode
        logger.warning("Roblox Assistant running in mock mode - no API keys found")


# Initialize on module load
initialize_assistant()

# Export router
__all__ = ["router", "chat_manager", "assistant_graph"]
