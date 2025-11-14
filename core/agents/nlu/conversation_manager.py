"""Conversation Manager for Multi-Turn Educational Dialogue

Manages conversation state, dialogue flow, and context persistence across
multiple interactions in educational content generation workflows.
"""

import hashlib
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from .context_extractor import ContextExtractor, EducationalContext
from .nlu_agent import IntentType, NLUAgent, NLUResult

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """States of a conversation lifecycle."""

    INITIALIZING = "initializing"
    GREETING = "greeting"
    GATHERING_REQUIREMENTS = "gathering_requirements"
    CLARIFYING = "clarifying"
    DESIGNING = "designing"
    REVIEWING = "reviewing"
    IMPLEMENTING = "implementing"
    COMPLETED = "completed"
    PAUSED = "paused"
    ERROR = "error"


class TurnType(Enum):
    """Types of conversation turns."""

    USER_INPUT = "user_input"
    ASSISTANT_RESPONSE = "assistant_response"
    CLARIFICATION_REQUEST = "clarification_request"
    CLARIFICATION_RESPONSE = "clarification_response"
    CONFIRMATION_REQUEST = "confirmation_request"
    CONFIRMATION_RESPONSE = "confirmation_response"
    SYSTEM_MESSAGE = "system_message"
    ERROR_MESSAGE = "error_message"


@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation."""

    turn_id: str
    turn_type: TurnType
    speaker: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime

    # Optional NLU results
    nlu_result: Optional[NLUResult] = None

    # Optional metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    # Context at this turn
    context_snapshot: Optional[EducationalContext] = None

    # Confidence and quality metrics
    confidence: float = 1.0
    quality_score: float = 0.0

    # References to related turns
    references: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert turn to dictionary format."""
        data = {
            "turn_id": self.turn_id,
            "turn_type": self.turn_type.value,
            "speaker": self.speaker,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
            "quality_score": self.quality_score,
            "metadata": self.metadata,
            "references": self.references,
        }

        if self.context_snapshot:
            data["context_snapshot"] = self.context_snapshot.to_dict()

        return data


@dataclass
class ConversationMemory:
    """Memory system for conversation management."""

    # Short-term memory (current conversation)
    current_turns: deque = field(default_factory=lambda: deque(maxlen=50))
    current_context: Optional[EducationalContext] = None
    current_state: ConversationState = ConversationState.INITIALIZING

    # Working memory (key information)
    key_facts: dict[str, Any] = field(default_factory=dict)
    unresolved_questions: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)

    # Long-term memory (persistent information)
    user_preferences: dict[str, Any] = field(default_factory=dict)
    completed_tasks: list[str] = field(default_factory=list)
    learned_patterns: dict[str, Any] = field(default_factory=dict)

    # Meta-information
    conversation_id: str = field(
        default_factory=lambda: f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    total_turns: int = 0

    def add_turn(self, turn: ConversationTurn):
        """Add a turn to memory."""
        self.current_turns.append(turn)
        self.total_turns += 1
        self.last_updated = datetime.now()

        # Extract key facts if this is a user turn with entities
        if turn.nlu_result and turn.speaker == "user":
            for entity in turn.nlu_result.entities:
                self.key_facts[entity.entity_type.value] = entity.value

    def get_recent_turns(self, n: int = 5) -> list[ConversationTurn]:
        """Get the n most recent turns."""
        return list(self.current_turns)[-n:]

    def get_turn_by_id(self, turn_id: str) -> Optional[ConversationTurn]:
        """Get a specific turn by ID."""
        for turn in self.current_turns:
            if turn.turn_id == turn_id:
                return turn
        return None

    def clear_short_term(self):
        """Clear short-term memory while preserving long-term."""
        self.current_turns.clear()
        self.unresolved_questions.clear()
        self.action_items.clear()


@dataclass
class DialoguePolicy:
    """Policy for managing dialogue flow."""

    # Conversation flow settings
    max_clarification_rounds: int = 3
    require_confirmation: bool = True
    auto_complete_threshold: float = 0.8  # Completeness threshold for auto-completion

    # Timing settings
    response_timeout: int = 30  # seconds
    session_timeout: int = 1800  # 30 minutes

    # Quality settings
    min_context_completeness: float = 0.6
    min_confidence_threshold: float = 0.7

    # Behavioral settings
    be_proactive: bool = True
    suggest_alternatives: bool = True
    provide_examples: bool = True
    use_encouraging_tone: bool = True

    # Educational settings
    enforce_learning_objectives: bool = True
    require_curriculum_alignment: bool = False
    validate_age_appropriateness: bool = True


class ConversationManager:
    """
    Manages multi-turn educational conversations with context preservation.

    This manager coordinates between NLU, context extraction, and dialogue flow
    to maintain coherent, goal-oriented conversations for educational content generation.
    """

    def __init__(
        self,
        nlu_agent: Optional[NLUAgent] = None,
        context_extractor: Optional[ContextExtractor] = None,
        policy: Optional[DialoguePolicy] = None,
    ):
        """Initialize the conversation manager."""
        self.nlu_agent = nlu_agent or NLUAgent()
        self.context_extractor = context_extractor or ContextExtractor()
        self.policy = policy or DialoguePolicy()

        # Conversation storage
        self.conversations: dict[str, ConversationMemory] = {}

        # Response templates
        self.response_templates = self._init_response_templates()

        # State transition rules
        self.state_transitions = self._init_state_transitions()

        logger.info("Conversation Manager initialized")

    def _init_response_templates(self) -> dict[str, list[str]]:
        """Initialize response templates for different situations."""
        return {
            "greeting": [
                "Hello! I'm here to help you create engaging educational content for Roblox. What would you like to create today?",
                "Welcome! Let's design an amazing educational experience together. What subject area are we working with?",
                "Hi there! Ready to build something educational and fun? Tell me about your learning goals.",
            ],
            "clarification_grade": [
                "What grade level are your students?",
                "Which grade will this be for?",
                "Can you tell me the grade level of your learners?",
            ],
            "clarification_subject": [
                "What subject area should this cover?",
                "Which subject are we focusing on?",
                "What subject would you like to teach?",
            ],
            "clarification_topic": [
                "What specific topic within {subject} would you like to focus on?",
                "Can you be more specific about the topic?",
                "What particular concept should we explore?",
            ],
            "confirmation": [
                "Got it! So we're creating a {content_type} for {grade_level} {subject} focusing on {topic}. Should I proceed with the design?",
                "Perfect! I'll design a {content_type} about {topic} for your {grade_level} students. Ready to start?",
                "Excellent! Let me create an engaging {content_type} for teaching {topic} to {grade_level} students. Shall we begin?",
            ],
            "completion": [
                "🎉 Your {content_type} is ready! Here's what I've created for you...",
                "✅ All done! I've designed an engaging {content_type} for your {grade_level} {subject} class.",
                "🚀 Success! Your educational {content_type} about {topic} is complete.",
            ],
            "error": [
                "I encountered an issue: {error}. Let me try a different approach.",
                "Something went wrong: {error}. Can you provide more details?",
                "I need help understanding: {error}. Could you clarify?",
            ],
            "suggestion": [
                "Based on what you've told me, I suggest adding {suggestion}. Would you like that?",
                "This would work great with {suggestion}. Should I include it?",
                "I recommend incorporating {suggestion} for better engagement. What do you think?",
            ],
        }

    def _init_state_transitions(
        self,
    ) -> dict[ConversationState, list[ConversationState]]:
        """Initialize valid state transitions."""
        return {
            ConversationState.INITIALIZING: [
                ConversationState.GREETING,
                ConversationState.ERROR,
            ],
            ConversationState.GREETING: [
                ConversationState.GATHERING_REQUIREMENTS,
                ConversationState.CLARIFYING,
                ConversationState.ERROR,
            ],
            ConversationState.GATHERING_REQUIREMENTS: [
                ConversationState.CLARIFYING,
                ConversationState.DESIGNING,
                ConversationState.PAUSED,
                ConversationState.ERROR,
            ],
            ConversationState.CLARIFYING: [
                ConversationState.GATHERING_REQUIREMENTS,
                ConversationState.DESIGNING,
                ConversationState.ERROR,
            ],
            ConversationState.DESIGNING: [
                ConversationState.REVIEWING,
                ConversationState.IMPLEMENTING,
                ConversationState.ERROR,
            ],
            ConversationState.REVIEWING: [
                ConversationState.IMPLEMENTING,
                ConversationState.DESIGNING,  # For revisions
                ConversationState.COMPLETED,
                ConversationState.ERROR,
            ],
            ConversationState.IMPLEMENTING: [
                ConversationState.COMPLETED,
                ConversationState.REVIEWING,
                ConversationState.ERROR,
            ],
            ConversationState.COMPLETED: [
                ConversationState.GREETING,  # For new task
                ConversationState.REVIEWING,  # For modifications
            ],
            ConversationState.PAUSED: [
                ConversationState.GATHERING_REQUIREMENTS,
                ConversationState.GREETING,
            ],
            ConversationState.ERROR: [
                ConversationState.GATHERING_REQUIREMENTS,
                ConversationState.GREETING,
            ],
        }

    async def start_conversation(
        self,
        user_id: Optional[str] = None,
        initial_context: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Start a new conversation.

        Args:
            user_id: Optional user identifier
            initial_context: Optional initial context

        Returns:
            Conversation ID
        """
        memory = ConversationMemory()

        # Set initial context if provided
        if initial_context:
            memory.key_facts.update(initial_context)

        # Store user preferences if we have history
        if user_id and user_id in self.conversations:
            old_memory = self.conversations[user_id]
            memory.user_preferences = old_memory.user_preferences.copy()
            memory.learned_patterns = old_memory.learned_patterns.copy()

        # Initialize state
        memory.current_state = ConversationState.GREETING

        # Store conversation
        self.conversations[memory.conversation_id] = memory

        logger.info(f"Started conversation {memory.conversation_id}")
        return memory.conversation_id

    async def process_turn(
        self,
        conversation_id: str,
        user_input: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Process a user turn in the conversation.

        Args:
            conversation_id: Conversation identifier
            user_input: User's input text
            metadata: Optional metadata

        Returns:
            Response dictionary with assistant's reply and metadata
        """
        # Get conversation memory
        if conversation_id not in self.conversations:
            return {
                "error": "Conversation not found",
                "suggestion": "Please start a new conversation",
            }

        memory = self.conversations[conversation_id]

        # Create user turn
        user_turn = ConversationTurn(
            turn_id=self._generate_turn_id(),
            turn_type=TurnType.USER_INPUT,
            speaker="user",
            content=user_input,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )

        # Process with NLU
        nlu_result = await self.nlu_agent.process(user_input, memory.key_facts)
        user_turn.nlu_result = nlu_result

        # Extract and update context
        memory.current_context = await self.context_extractor.extract_context(
            user_input, memory.current_context, conversation_id
        )

        user_turn.context_snapshot = memory.current_context

        # Add turn to memory
        memory.add_turn(user_turn)

        # Determine response based on state and context
        response = await self._generate_response(memory, nlu_result)

        # Create assistant turn
        assistant_turn = ConversationTurn(
            turn_id=self._generate_turn_id(),
            turn_type=response["turn_type"],
            speaker="assistant",
            content=response["content"],
            timestamp=datetime.now(),
            metadata=response.get("metadata", {}),
            context_snapshot=memory.current_context,
            references=[user_turn.turn_id],
        )

        # Add assistant turn to memory
        memory.add_turn(assistant_turn)

        # Update conversation state
        if "new_state" in response:
            memory.current_state = response["new_state"]

        # Prepare response
        result = {
            "conversation_id": conversation_id,
            "response": response["content"],
            "state": memory.current_state.value,
            "context": memory.current_context.to_dict() if memory.current_context else {},
            "turn_id": assistant_turn.turn_id,
            "suggestions": response.get("suggestions", []),
            "actions": response.get("actions", []),
            "completeness": (
                memory.current_context.completeness_score if memory.current_context else 0.0
            ),
        }

        return result

    async def _generate_response(
        self, memory: ConversationMemory, nlu_result: NLUResult
    ) -> dict[str, Any]:
        """Generate appropriate response based on conversation state and NLU results."""

        state = memory.current_state

        # Handle different states
        if state == ConversationState.GREETING:
            return await self._handle_greeting(memory, nlu_result)

        elif state == ConversationState.GATHERING_REQUIREMENTS:
            return await self._handle_requirements_gathering(memory, nlu_result)

        elif state == ConversationState.CLARIFYING:
            return await self._handle_clarification(memory, nlu_result)

        elif state == ConversationState.DESIGNING:
            return await self._handle_designing(memory, nlu_result)

        elif state == ConversationState.REVIEWING:
            return await self._handle_reviewing(memory, nlu_result)

        elif state == ConversationState.IMPLEMENTING:
            return await self._handle_implementing(memory, nlu_result)

        else:
            return {
                "content": "I'm not sure how to proceed. Can you tell me what you'd like to create?",
                "turn_type": TurnType.CLARIFICATION_REQUEST,
                "new_state": ConversationState.GATHERING_REQUIREMENTS,
            }

    async def _handle_greeting(
        self, memory: ConversationMemory, nlu_result: NLUResult
    ) -> dict[str, Any]:
        """Handle greeting state."""

        # Check if user provided initial requirements
        if nlu_result.intents and nlu_result.educational_context:
            # User jumped straight to requirements
            memory.current_state = ConversationState.GATHERING_REQUIREMENTS
            return await self._handle_requirements_gathering(memory, nlu_result)

        # Standard greeting
        import random

        content = random.choice(self.response_templates["greeting"])

        return {
            "content": content,
            "turn_type": TurnType.ASSISTANT_RESPONSE,
            "new_state": ConversationState.GATHERING_REQUIREMENTS,
            "suggestions": [
                "Create a math quiz for 5th graders",
                "Build a science simulation about the solar system",
                "Design a history game about ancient civilizations",
            ],
        }

    async def _handle_requirements_gathering(
        self, memory: ConversationMemory, nlu_result: NLUResult
    ) -> dict[str, Any]:
        """Handle requirements gathering state."""

        context = memory.current_context

        # Check if we have enough information
        if context and context.completeness_score >= self.policy.auto_complete_threshold:
            # We have enough info, move to design
            return await self._generate_confirmation(memory)

        # Check what's missing
        missing_fields = context.get_missing_critical_fields() if context else []

        if "grade_level" in missing_fields:
            content = random.choice(self.response_templates["clarification_grade"])
            return {
                "content": content,
                "turn_type": TurnType.CLARIFICATION_REQUEST,
                "new_state": ConversationState.CLARIFYING,
            }

        if "subject" in missing_fields:
            content = random.choice(self.response_templates["clarification_subject"])
            return {
                "content": content,
                "turn_type": TurnType.CLARIFICATION_REQUEST,
                "new_state": ConversationState.CLARIFYING,
            }

        if "topic" in missing_fields:
            subject = context.subject if context else "the subject"
            content = random.choice(self.response_templates["clarification_topic"]).format(
                subject=subject
            )
            return {
                "content": content,
                "turn_type": TurnType.CLARIFICATION_REQUEST,
                "new_state": ConversationState.CLARIFYING,
            }

        # Check for delegation intent
        if nlu_result.intents and any(
            intent.intent_type == IntentType.DELEGATE_CONTROL for intent in nlu_result.intents
        ):
            # User wants us to take control
            return {
                "content": "I'll design something engaging for you! Let me create an interactive learning experience...",
                "turn_type": TurnType.ASSISTANT_RESPONSE,
                "new_state": ConversationState.DESIGNING,
                "actions": ["auto_generate"],
            }

        # Default to asking for more info
        return {
            "content": "Can you tell me more about what you'd like to create? For example, the subject, grade level, and learning objectives.",
            "turn_type": TurnType.CLARIFICATION_REQUEST,
            "new_state": ConversationState.CLARIFYING,
        }

    async def _handle_clarification(
        self, memory: ConversationMemory, nlu_result: NLUResult
    ) -> dict[str, Any]:
        """Handle clarification state."""

        # Check if clarification was successful
        if nlu_result.entities or nlu_result.educational_context:
            # Got useful information, go back to gathering
            memory.current_state = ConversationState.GATHERING_REQUIREMENTS
            return await self._handle_requirements_gathering(memory, nlu_result)

        # Check clarification rounds
        clarification_count = sum(
            1 for turn in memory.current_turns if turn.turn_type == TurnType.CLARIFICATION_REQUEST
        )

        if clarification_count >= self.policy.max_clarification_rounds:
            # Too many clarifications, provide default
            return {
                "content": "Let me help you get started. I'll create a basic educational template that you can customize. Here's what I suggest...",
                "turn_type": TurnType.ASSISTANT_RESPONSE,
                "new_state": ConversationState.DESIGNING,
                "actions": ["use_defaults"],
            }

        # Ask for clarification again with examples
        return {
            "content": "I'm not sure I understood that. Could you provide more details? For example: 'Create a 4th grade math quiz about fractions'",
            "turn_type": TurnType.CLARIFICATION_REQUEST,
            "new_state": ConversationState.CLARIFYING,
        }

    async def _generate_confirmation(self, memory: ConversationMemory) -> dict[str, Any]:
        """Generate confirmation before proceeding to design."""

        context = memory.current_context

        # Format confirmation message
        import random

        template = random.choice(self.response_templates["confirmation"])
        content = template.format(
            content_type=context.content_type or "educational experience",
            grade_level=context.grade_level or "your",
            subject=context.subject or "the",
            topic=context.topic or "selected topics",
        )

        if self.policy.require_confirmation:
            return {
                "content": content,
                "turn_type": TurnType.CONFIRMATION_REQUEST,
                "new_state": ConversationState.DESIGNING,
                "suggestions": (
                    context.learning_objectives[:3] if context.learning_objectives else []
                ),
            }
        else:
            # Auto-proceed to design
            return {
                "content": "Great! I have everything I need. Let me design this for you...",
                "turn_type": TurnType.ASSISTANT_RESPONSE,
                "new_state": ConversationState.DESIGNING,
                "actions": ["begin_design"],
            }

    async def _handle_designing(
        self, memory: ConversationMemory, nlu_result: NLUResult
    ) -> dict[str, Any]:
        """Handle designing state."""

        # Check for user confirmation or modification
        if nlu_result.intents:
            primary_intent = nlu_result.intents[0].intent_type

            if primary_intent == IntentType.CONFIRM_ACTION:
                # User confirmed, proceed to implementation
                return {
                    "content": "Excellent! I'm now creating your educational content. This will just take a moment...",
                    "turn_type": TurnType.ASSISTANT_RESPONSE,
                    "new_state": ConversationState.IMPLEMENTING,
                    "actions": ["generate_content"],
                }

            elif primary_intent in [IntentType.MODIFY_CONTENT, IntentType.ADD_FEATURE]:
                # User wants modifications
                return {
                    "content": "I'll adjust the design based on your feedback. What specific changes would you like?",
                    "turn_type": TurnType.CLARIFICATION_REQUEST,
                    "new_state": ConversationState.GATHERING_REQUIREMENTS,
                }

        # Default: Present design
        return {
            "content": "Here's what I've designed: [Design details would go here]. Ready to create this?",
            "turn_type": TurnType.CONFIRMATION_REQUEST,
            "new_state": ConversationState.REVIEWING,
        }

    async def _handle_reviewing(
        self, memory: ConversationMemory, nlu_result: NLUResult
    ) -> dict[str, Any]:
        """Handle reviewing state."""

        return {
            "content": "The design looks great! I'll now implement this for you. Creating the Roblox environment...",
            "turn_type": TurnType.ASSISTANT_RESPONSE,
            "new_state": ConversationState.IMPLEMENTING,
            "actions": ["implement_design"],
        }

    async def _handle_implementing(
        self, memory: ConversationMemory, nlu_result: NLUResult
    ) -> dict[str, Any]:
        """Handle implementing state."""

        context = memory.current_context

        # Format completion message
        import random

        template = random.choice(self.response_templates["completion"])
        content = template.format(
            content_type=context.content_type or "educational experience",
            grade_level=context.grade_level or "the",
            subject=context.subject or "",
            topic=context.topic or "content",
        )

        return {
            "content": content + "\n\n[Generated content would appear here]",
            "turn_type": TurnType.ASSISTANT_RESPONSE,
            "new_state": ConversationState.COMPLETED,
            "actions": ["display_content", "save_content"],
            "suggestions": [
                "Create another activity",
                "Modify this content",
                "Export to Roblox Studio",
            ],
        }

    def _generate_turn_id(self) -> str:
        """Generate unique turn ID."""
        timestamp = datetime.now().isoformat()
        random_str = hashlib.md5(timestamp.encode()).hexdigest()[:8]
        return f"turn_{random_str}"

    def get_conversation_summary(self, conversation_id: str) -> Optional[dict[str, Any]]:
        """Get summary of a conversation."""

        if conversation_id not in self.conversations:
            return None

        memory = self.conversations[conversation_id]

        return {
            "conversation_id": conversation_id,
            "state": memory.current_state.value,
            "total_turns": memory.total_turns,
            "key_facts": memory.key_facts,
            "context_completeness": (
                memory.current_context.completeness_score if memory.current_context else 0.0
            ),
            "unresolved_questions": memory.unresolved_questions,
            "action_items": memory.action_items,
            "created_at": memory.created_at.isoformat(),
            "last_updated": memory.last_updated.isoformat(),
        }

    def end_conversation(self, conversation_id: str) -> bool:
        """End a conversation and clean up resources."""

        if conversation_id in self.conversations:
            self.conversations[conversation_id]

            # Save any important patterns or preferences
            # This would be persisted to a database in production

            # Remove from active conversations
            del self.conversations[conversation_id]

            logger.info(f"Ended conversation {conversation_id}")
            return True

        return False
