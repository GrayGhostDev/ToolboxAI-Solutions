"""LLM Integration for NLU Agent

Provides real LLM capabilities to make the NLU agent interactive and context-aware,
addressing the core issue of "robotic flow" and "repeating questions".
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import LLM libraries
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    AsyncAnthropic = None


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"


@dataclass
class LLMConfig:
    """Configuration for LLM integration."""
    provider: LLMProvider = LLMProvider.MOCK
    model: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1500


class LLMIntegration:
    """Handles LLM integration for intelligent NLU processing."""

    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize LLM integration."""
        self.config = config or LLMConfig()
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the LLM client based on configuration."""
        if self.config.provider == LLMProvider.OPENAI and OPENAI_AVAILABLE:
            api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = AsyncOpenAI(api_key=api_key)
                self.config.model = self.config.model or "gpt-4-turbo-preview"
                logger.info(f"Initialized OpenAI client with model: {self.config.model}")
            else:
                logger.warning("OpenAI API key not found, falling back to mock")
                self.config.provider = LLMProvider.MOCK

        elif self.config.provider == LLMProvider.ANTHROPIC and ANTHROPIC_AVAILABLE:
            api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                self.client = AsyncAnthropic(api_key=api_key)
                self.config.model = self.config.model or "claude-sonnet-4-20250514"
                logger.info(f"Initialized Anthropic client with model: {self.config.model}")
            else:
                logger.warning("Anthropic API key not found, falling back to mock")
                self.config.provider = LLMProvider.MOCK
        else:
            self.config.provider = LLMProvider.MOCK
            logger.info("Using mock LLM for development")

    async def understand_intent(
        self,
        user_input: str,
        conversation_history: List[Dict[str, str]],
        accumulated_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use LLM to understand user intent with full context awareness.

        This addresses the core issue by:
        1. Considering conversation history to avoid repeating questions
        2. Using accumulated context to understand what's already known
        3. Providing intelligent, context-aware responses
        """
        if self.config.provider == LLMProvider.MOCK:
            return await self._mock_understand_intent(user_input, conversation_history, accumulated_context)

        # Build context-aware prompt
        system_prompt = self._build_system_prompt(accumulated_context)
        user_prompt = self._build_user_prompt(user_input, conversation_history)

        try:
            if self.config.provider == LLMProvider.OPENAI:
                response = await self._call_openai(system_prompt, user_prompt)
            elif self.config.provider == LLMProvider.ANTHROPIC:
                response = await self._call_anthropic(system_prompt, user_prompt)
            else:
                response = await self._mock_understand_intent(user_input, conversation_history, accumulated_context)

            # Parse the JSON response
            return self._parse_llm_response(response)

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            # Fallback to mock on error
            return await self._mock_understand_intent(user_input, conversation_history, accumulated_context)

    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build system prompt with context awareness."""
        return f"""You are an intelligent educational content assistant that helps create Roblox educational experiences.

CRITICAL: You must be context-aware and conversational:
- Never repeat questions that have already been answered
- Use information from previous messages to build understanding
- Remember and reference what the user has already told you
- Be proactive in suggesting next steps based on accumulated context

Current Context:
{json.dumps(context, indent=2) if context else "No prior context"}

Your task is to understand the user's intent and extract key information.
Respond with a JSON object containing:
- intent: The primary intent (e.g., "create_lesson", "modify_content", "get_help")
- entities: Key entities mentioned (subject, grade_level, topics, etc.)
- confidence: Your confidence level (0.0 to 1.0)
- clarifications_needed: Only ask for truly missing critical information
- suggestions: Proactive suggestions based on what you understand
- understood_context: Summary of what you understand so far

Remember: Be intelligent and context-aware. Don't ask for information that's already been provided."""

    def _build_user_prompt(self, user_input: str, history: List[Dict[str, str]]) -> str:
        """Build user prompt with conversation history."""
        prompt = "Conversation History:\n"

        # Include recent history for context
        for msg in history[-5:]:  # Last 5 messages for context
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            prompt += f"{role.capitalize()}: {content}\n"

        prompt += f"\nCurrent User Input: {user_input}\n"
        prompt += "\nPlease analyze this input considering the full conversation context."

        return prompt

    async def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI API."""
        if not self.client:
            raise ValueError("OpenAI client not initialized")

        response = await self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            response_format={"type": "json_object"}
        )

        return response.choices[0].message.content

    async def _call_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """Call Anthropic API."""
        if not self.client:
            raise ValueError("Anthropic client not initialized")

        # Combine prompts for Anthropic format
        full_prompt = f"{system_prompt}\n\n{user_prompt}\n\nRespond with valid JSON only."

        response = await self.client.messages.create(
            model=self.config.model,
            messages=[
                {"role": "user", "content": full_prompt}
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )

        return response.content[0].text

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured format."""
        try:
            # Try to parse as JSON
            data = json.loads(response)

            # Ensure required fields
            return {
                "intent": data.get("intent", "unknown"),
                "entities": data.get("entities", {}),
                "confidence": data.get("confidence", 0.5),
                "clarifications_needed": data.get("clarifications_needed", []),
                "suggestions": data.get("suggestions", []),
                "understood_context": data.get("understood_context", ""),
                "raw_response": response
            }
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM response as JSON: {response[:200]}")
            # Return a basic structure
            return {
                "intent": "unknown",
                "entities": {},
                "confidence": 0.3,
                "clarifications_needed": [],
                "suggestions": ["Could you please rephrase your request?"],
                "understood_context": "",
                "raw_response": response
            }

    async def _mock_understand_intent(
        self,
        user_input: str,
        history: List[Dict[str, str]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock implementation for development/testing."""
        # Intelligent mock that demonstrates context awareness
        user_input_lower = user_input.lower()

        # Check if this is a follow-up based on context
        is_followup = bool(context) or len(history) > 0

        # Determine intent based on keywords
        intent = "unknown"
        entities = {}
        suggestions = []

        if "create" in user_input_lower or "make" in user_input_lower:
            if "lesson" in user_input_lower:
                intent = "create_lesson"
            elif "quiz" in user_input_lower or "assessment" in user_input_lower:
                intent = "create_quiz"
            elif "game" in user_input_lower:
                intent = "create_game"
            else:
                intent = "create_content"
        elif "help" in user_input_lower:
            intent = "get_help"
        elif "modify" in user_input_lower or "change" in user_input_lower:
            intent = "modify_content"

        # Extract entities from input
        if "math" in user_input_lower:
            entities["subject"] = "mathematics"
        if "fraction" in user_input_lower:
            entities["topic"] = "fractions"
        if "5th grade" in user_input_lower or "grade 5" in user_input_lower:
            entities["grade_level"] = "5"

        # Be smart about not asking for already provided information
        clarifications = []
        if not entities.get("subject") and not context.get("subject"):
            clarifications.append("What subject would you like to focus on?")
        if not entities.get("grade_level") and not context.get("grade_level"):
            clarifications.append("What grade level are your students?")

        # Provide intelligent suggestions
        if intent == "create_lesson":
            suggestions = [
                "I can help you add interactive elements to make the lesson engaging",
                "Would you like to include assessment questions?",
                "Consider adding visual demonstrations for better understanding"
            ]

        understood = "I understand you want to "
        if intent == "create_lesson":
            understood += f"create a lesson"
            if entities.get("subject"):
                understood += f" about {entities['subject']}"
            if entities.get("grade_level"):
                understood += f" for grade {entities['grade_level']}"

        return {
            "intent": intent,
            "entities": entities,
            "confidence": 0.8 if intent != "unknown" else 0.3,
            "clarifications_needed": clarifications,
            "suggestions": suggestions,
            "understood_context": understood,
            "is_followup": is_followup
        }

    async def generate_response(
        self,
        intent_result: Dict[str, Any],
        task_results: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a natural language response based on understanding and results."""
        if self.config.provider == LLMProvider.MOCK:
            return self._generate_mock_response(intent_result, task_results)

        # Use LLM to generate natural response
        # ... (implementation for real LLM response generation)

        return self._generate_mock_response(intent_result, task_results)

    def _generate_mock_response(
        self,
        intent_result: Dict[str, Any],
        task_results: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a mock natural language response."""
        understood = intent_result.get("understood_context", "")
        clarifications = intent_result.get("clarifications_needed", [])
        suggestions = intent_result.get("suggestions", [])

        response = ""

        if understood:
            response += understood + ". "

        if task_results and task_results.get("success"):
            response += "I've successfully processed your request. "
            if task_results.get("message"):
                response += task_results["message"] + " "

        if clarifications:
            response += "To provide the best assistance, " + " ".join(clarifications) + " "

        if suggestions and not clarifications:
            response += "Here are some suggestions: " + "; ".join(suggestions[:2])

        if not response:
            response = "I'm ready to help you create engaging educational content for Roblox. What would you like to work on?"

        return response.strip()