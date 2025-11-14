"""
Roblox AI Agent Service

Handles AI-powered chat interactions for Roblox environment creation.
Processes user messages, extracts structured specifications, and guides
users through the creation process with intelligent follow-up questions.
"""

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    from langchain_community.chat_models import ChatOpenAI

from apps.backend.agents.agent import get_agent_manager
from apps.backend.core.config import settings
from apps.backend.services.pusher import trigger_event as pusher_trigger_event

logger = logging.getLogger(__name__)


class RobloxAIAgent:
    """AI Agent for interactive Roblox environment creation"""

    def __init__(self):
        # Try to initialize LLM, fall back to mock mode if it fails
        try:
            self.llm = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=0.7, max_tokens=1000, http_client=None, http_async_client=None)
            self.mock_mode = False
            logger.info("RobloxAIAgent initialized with OpenAI")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI LLM: {e}. Running in mock mode.")
            self.llm = None
            self.mock_mode = True

        self.conversations: dict[str, InMemoryChatMessageHistory] = {}
        self.conversation_specs: dict[str, dict[str, Any]] = {}

        # Required fields for complete specification
        self.required_fields = {
            "environment_name": "What should we name this Roblox environment?",
            "theme": "What is the theme or style (e.g., space station, medieval castle, jungle)?",
            "map_type": "Which map type fits best (obby, open_world, dungeon, lab, classroom, puzzle)?",
            "learning_objectives": "What are the key learning objectives or topics to cover?",
        }

        # Optional fields with questions
        self.optional_fields = {
            "terrain": "What type of terrain would you like (mountains, plains, water, etc.)?",
            "npc_count": "How many NPCs or characters should be in the environment?",
            "difficulty": "What difficulty level (easy, medium, hard)?",
            "age_range": "What age group is this for?",
            "assets": "Any specific assets or objects you want included?",
            "scripting": "Any special interactive features or scripts needed?",
            "lighting": "What lighting mood (bright, dark, colorful, etc.)?",
            "weather": "Any weather effects (sunny, rainy, snowy, etc.)?",
        }

        # Pattern matching for extracting information
        self.extraction_patterns = {
            "environment_name": [
                r'(?:call it|named?|title(?:d)?)\s+["\']?([^"\'.\n]{3,40})["\']?',
                r'environment\s+["\']?([^"\'.\n]{3,40})["\']?',
                r'world\s+["\']?([^"\'.\n]{3,40})["\']?',
            ],
            "theme": [
                r"(?:theme|style|setting)\s*:?\s*([^.\n]{3,50})",
                r"(?:space|medieval|jungle|forest|ocean|desert|city|school|lab)",
                r"(?:futuristic|ancient|modern|fantasy|sci-fi)",
            ],
            "map_type": [
                r"\b(obby|obstacle\s+course)\b",
                r"\b(open\s+world|sandbox)\b",
                r"\b(dungeon|maze)\b",
                r"\b(lab|laboratory)\b",
                r"\b(classroom|school)\b",
                r"\b(puzzle|brain\s+teaser)\b",
                r"\b(arena|battle\s+ground)\b",
            ],
            "learning_objectives": [
                r"(?:learn|teach|objective|goal|topic)s?\s*:?\s*([^.\n]+)",
                r"(?:math|science|history|english|art|geography|physics|chemistry|biology)",
                r"(?:addition|subtraction|multiplication|division|fractions|geometry)",
            ],
            "difficulty": [
                r"\b(easy|beginner|simple)\b",
                r"\b(medium|intermediate|moderate)\b",
                r"\b(hard|difficult|advanced|challenging)\b",
            ],
            "age_range": [
                r"(?:age|grade)\s*(?:group|level)?\s*:?\s*(\d+(?:-\d+)?)",
                r"(?:kindergarten|elementary|middle\s+school|high\s+school)",
                r"(?:preschool|primary|secondary)",
            ],
            "terrain": [
                r"(?:terrain|landscape|ground)\s*:?\s*([^.\n]{3,30})",
                r"\b(mountains?|hills?|plains?|valleys?|water|ocean|lake|river|desert|forest|jungle)\b",
            ],
            "npc_count": [
                r"(?:npc|character|people|student)s?\s*:?\s*(\d{1,3})",
                r"(\d{1,3})\s+(?:npc|character|people|student)s?",
            ],
        }

    async def handle_user_message(
        self, conversation_id: str, message: str, context: dict[str, Any] = None
    ) -> None:
        """Process user message and respond with AI guidance"""
        try:
            # Initialize conversation if new
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = InMemoryChatMessageHistory()
                self.conversation_specs[conversation_id] = {}

            # Add user message to history
            self.conversations[conversation_id].add_user_message(message)

            # Extract information from message
            extracted_info = self._extract_information(message)

            # Update conversation spec
            current_spec = self.conversation_specs[conversation_id]
            current_spec.update(extracted_info)

            # Generate AI response
            ai_response = await self._generate_response(
                conversation_id, message, current_spec, context
            )

            # Add AI response to history
            self.conversations[conversation_id].add_ai_message(ai_response)

            # Stream response to user
            await self._stream_response(conversation_id, ai_response)

            # Check if we need follow-up questions
            missing_fields = self._get_missing_required_fields(current_spec)
            if missing_fields:
                await self._send_followup_questions(conversation_id, missing_fields, current_spec)
            else:
                # Spec is complete, ready to generate
                await self._notify_ready_for_generation(conversation_id, current_spec)

        except Exception as e:
            logger.error(f"Error handling user message: {e}")
            await self._send_error_message(
                conversation_id,
                "I encountered an error processing your message. Please try again.",
            )

    def _extract_information(self, message: str) -> dict[str, Any]:
        """Extract structured information from user message"""
        extracted = {}
        message_lower = message.lower()

        for field, patterns in self.extraction_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, message_lower, re.IGNORECASE)
                if matches:
                    if field == "learning_objectives":
                        # Handle multiple objectives
                        objectives = []
                        for match in matches:
                            if isinstance(match, str):
                                objectives.extend(
                                    [obj.strip() for obj in match.split(",") if obj.strip()]
                                )
                        if objectives:
                            extracted[field] = objectives
                    elif field == "npc_count":
                        # Convert to integer
                        try:
                            extracted[field] = int(matches[0])
                        except (ValueError, IndexError):
                            pass
                    elif field in ["theme", "terrain", "lighting", "weather"]:
                        # Take first match for descriptive fields
                        extracted[field] = matches[0].strip()
                    elif field == "map_type":
                        # Normalize map type
                        map_type = matches[0].lower().strip()
                        if "obby" in map_type or "obstacle" in map_type:
                            extracted[field] = "obby"
                        elif "open" in map_type or "sandbox" in map_type:
                            extracted[field] = "open_world"
                        elif "dungeon" in map_type or "maze" in map_type:
                            extracted[field] = "dungeon"
                        elif "lab" in map_type:
                            extracted[field] = "lab"
                        elif "classroom" in map_type or "school" in map_type:
                            extracted[field] = "classroom"
                        elif "puzzle" in map_type:
                            extracted[field] = "puzzle"
                        elif "arena" in map_type or "battle" in map_type:
                            extracted[field] = "arena"
                    else:
                        extracted[field] = matches[0].strip()
                    break

        # Special handling for environment name
        if "environment_name" not in extracted:
            # Look for quoted strings or capitalized phrases
            name_patterns = [
                r'"([^"]{3,40})"',
                r"'([^']{3,40})'",
                r"\b([A-Z][a-zA-Z\s]{2,39})\b(?:\s+(?:world|environment|place|room|area))?",
            ]
            for pattern in name_patterns:
                matches = re.findall(pattern, message)
                if matches:
                    extracted["environment_name"] = matches[0].strip()
                    break

        return extracted

    async def _generate_response(
        self,
        conversation_id: str,
        message: str,
        current_spec: dict[str, Any],
        context: dict[str, Any] = None,
    ) -> str:
        """Generate AI response based on conversation context"""

        # Build context for the AI
        spec_summary = self._format_spec_summary(current_spec)
        missing_fields = self._get_missing_required_fields(current_spec)

        system_prompt = f"""You are an AI assistant helping users create educational Roblox environments.

Current specification:
{spec_summary}

Missing required information: {', '.join(missing_fields) if missing_fields else 'None - ready to generate!'}

Guidelines:
- Be enthusiastic and encouraging
- Ask clarifying questions naturally in conversation
- Provide educational context when relevant
- Keep responses concise but helpful
- Use emojis sparingly but effectively
- If the spec is complete, congratulate them and mention they can generate the environment

Respond to the user's message in a helpful, conversational way."""

        try:
            # Get conversation history
            history = self.conversations[conversation_id]
            messages = [{"role": "system", "content": system_prompt}]

            # Add recent conversation history (last 10 messages)
            for msg in history.messages[-10:]:
                if isinstance(msg, HumanMessage):
                    messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    messages.append({"role": "assistant", "content": msg.content})

            # Generate response
            if self.mock_mode:
                # Mock response for development
                return self._generate_mock_response(message, current_spec, missing_fields)
            else:
                response = await self.llm.ainvoke(messages)
                return response.content

        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "I understand you want to create a Roblox environment. Could you tell me more about what you have in mind?"

    def _generate_mock_response(
        self, message: str, current_spec: dict[str, Any], missing_fields: list
    ) -> str:
        """Generate a mock AI response for development"""
        message_lower = message.lower()

        # Check if it's about chemistry
        if any(
            word in message_lower
            for word in [
                "chemistry",
                "chemical",
                "lab",
                "experiment",
                "molecule",
                "atom",
            ]
        ):
            if "environment_name" not in current_spec:
                return "Great! A chemistry lab sounds exciting! 🧪 What would you like to name this environment? Something like 'Chemistry Lab' or 'Science Station'?"
            elif "theme" not in current_spec:
                return "Perfect! Now, what theme would you like for your chemistry lab? We could make it look like a modern laboratory, a space station lab, or even a medieval alchemy workshop!"
            elif "map_type" not in current_spec:
                return "Excellent! For a chemistry lab, I'd recommend either a 'lab' or 'classroom' map type. Which would work better for your students?"
            elif "learning_objectives" not in current_spec:
                return "Almost there! What specific chemistry concepts do you want students to learn? For example: chemical reactions, periodic table, molecular structure, or lab safety?"
            else:
                return "Fantastic! Your chemistry lab specification is complete! 🎉 You can now generate the environment. Would you like me to create it for you?"

        # Check if it's about math
        elif any(
            word in message_lower
            for word in [
                "math",
                "mathematics",
                "algebra",
                "geometry",
                "calculus",
                "fraction",
            ]
        ):
            if "environment_name" not in current_spec:
                return "Math environments are great for learning! 📐 What should we call this math world? Something like 'Math Adventure' or 'Number Land'?"
            elif "theme" not in current_spec:
                return "Nice! What theme would make math more engaging? We could create a space station, medieval castle, or underwater city where students solve math problems!"
            elif "map_type" not in current_spec:
                return "Great choice! For math learning, I'd suggest either 'puzzle' or 'classroom' map type. Which would work better for your math activities?"
            elif "learning_objectives" not in current_spec:
                return "Almost ready! What math topics should students practice? For example: multiplication tables, geometry shapes, word problems, or fractions?"
            else:
                return "Perfect! Your math environment is ready to create! 🎯 Would you like me to generate it now?"

        # General response
        else:
            if "environment_name" not in current_spec:
                return f"Interesting! I'd love to help you create a Roblox environment about: '{message}'. What would you like to name this environment?"
            elif "theme" not in current_spec:
                return "Great name! What theme or style would you like? We could make it look like a space station, medieval castle, jungle, or modern city!"
            elif "map_type" not in current_spec:
                return "Nice theme! What type of map would work best? We have obby (obstacle course), open world, dungeon, lab, classroom, or puzzle maps!"
            elif "learning_objectives" not in current_spec:
                return "Almost there! What should students learn in this environment? What are the key learning objectives or topics to cover?"
            else:
                return "Excellent! Your environment specification is complete! 🚀 Ready to create your Roblox world?"

    def _format_spec_summary(self, spec: dict[str, Any]) -> str:
        """Format current specification as readable summary"""
        if not spec:
            return "No information collected yet."

        summary_parts = []
        for field, value in spec.items():
            if value:
                if field == "learning_objectives" and isinstance(value, list):
                    summary_parts.append(f"Learning objectives: {', '.join(value)}")
                else:
                    field_name = field.replace("_", " ").title()
                    summary_parts.append(f"{field_name}: {value}")

        return "\n".join(summary_parts) if summary_parts else "No information collected yet."

    def _get_missing_required_fields(self, spec: dict[str, Any]) -> list[str]:
        """Get list of missing required fields"""
        missing = []
        for field in self.required_fields:
            if field not in spec or not spec[field]:
                missing.append(field)
        return missing

    async def _stream_response(self, conversation_id: str, response: str) -> None:
        """Stream AI response token by token"""
        try:
            message_id = f"msg_{datetime.now(timezone.utc).timestamp()}"

            # Try to stream via Pusher, fall back to direct message if unavailable
            try:
                # Simulate streaming by sending tokens
                words = response.split()
                for i, word in enumerate(words):
                    token = word + (" " if i < len(words) - 1 else "")

                    await pusher_trigger_event(
                        f"agent-chat-{conversation_id}",
                        "message",
                        {
                            "type": "agent_chat_token",
                            "payload": {
                                "conversationId": conversation_id,
                                "messageId": message_id,
                                "token": token,
                            },
                        },
                    )

                    # Small delay for realistic streaming
                    await asyncio.sleep(0.05)

                # Send completion message
                await pusher_trigger_event(
                    f"agent-chat-{conversation_id}",
                    "message",
                    {
                        "type": "agent_chat_complete",
                        "payload": {
                            "conversationId": conversation_id,
                            "messageId": message_id,
                            "content": response,
                        },
                    },
                )

            except Exception as pusher_error:
                # Pusher unavailable, send direct message via WebSocket handler
                logger.warning(
                    f"Pusher unavailable for streaming, sending direct message: {pusher_error}"
                )
                await self._send_direct_message(conversation_id, response)

        except Exception as e:
            logger.error(f"Error streaming response: {e}")

    async def _send_direct_message(self, conversation_id: str, response: str) -> None:
        """Send direct message when Pusher is unavailable"""
        try:
            # Send via the realtime trigger endpoint to simulate Pusher
            import httpx

            message_data = {
                "type": "ai_message",
                "payload": {
                    "conversation_id": conversation_id,
                    "message": {
                        "id": f"msg_{datetime.now(timezone.utc).timestamp()}",
                        "role": "assistant",
                        "content": response,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "metadata": {"generated": True},
                    },
                },
            }

            # Trigger the realtime endpoint directly
            async with httpx.AsyncClient() as client:
                await client.post(
                    "http://127.0.0.1:8009/realtime/trigger",
                    json={
                        "channel": f"ai-chat-{conversation_id}",
                        "event": "message",
                        "type": "ai_message",
                        "payload": message_data["payload"],
                    },
                )

        except Exception as e:
            logger.error(f"Error sending direct message: {e}")

    async def _send_followup_questions(
        self,
        conversation_id: str,
        missing_fields: list[str],
        current_spec: dict[str, Any],
    ) -> None:
        """Send follow-up questions for missing information"""
        try:
            questions = []
            for field in missing_fields[:3]:  # Limit to 3 questions at a time
                if field in self.required_fields:
                    questions.append(self.required_fields[field])

            if questions:
                await pusher_trigger_event(
                    f"agent-chat-{conversation_id}",
                    "message",
                    {
                        "type": "agent_followup",
                        "payload": {
                            "conversationId": conversation_id,
                            "missingFields": missing_fields,
                            "questions": questions,
                            "collected": current_spec,
                        },
                    },
                )

        except Exception as e:
            logger.error(f"Error sending followup questions: {e}")

    async def _notify_ready_for_generation(
        self, conversation_id: str, spec: dict[str, Any]
    ) -> None:
        """Notify that specification is complete and ready for generation"""
        try:
            await pusher_trigger_event(
                f"agent-chat-{conversation_id}",
                "message",
                {
                    "type": "ai_message",
                    "payload": {
                        "message": {
                            "content": "🎉 Perfect! I have all the information needed to create your Roblox environment. Click 'Generate Environment' when you're ready to start building!"
                        }
                    },
                },
            )

        except Exception as e:
            logger.error(f"Error notifying ready for generation: {e}")

    async def _send_error_message(self, conversation_id: str, error_message: str) -> None:
        """Send error message to user"""
        try:
            await pusher_trigger_event(
                f"agent-chat-{conversation_id}",
                "message",
                {
                    "type": "ai_message",
                    "payload": {"message": {"content": f"❌ {error_message}"}},
                },
            )

        except Exception as e:
            logger.error(f"Error sending error message: {e}")

    async def generate_environment(self, conversation_id: str, spec: dict[str, Any]) -> str:
        """Generate Roblox environment based on specification"""
        try:
            request_id = f"req_{datetime.now(timezone.utc).timestamp()}"

            # Send progress updates
            stages = [
                ("parsing", "Analyzing your requirements..."),
                ("planning", "Planning the environment layout..."),
                ("fetching_assets", "Gathering assets and resources..."),
                ("generating_scripts", "Creating interactive scripts..."),
                ("assembling_world", "Building the world..."),
                ("baking_lighting", "Setting up lighting and atmosphere..."),
                ("finalizing", "Adding final touches..."),
            ]

            for i, (stage, message) in enumerate(stages):
                progress = int((i + 1) / len(stages) * 100)

                await pusher_trigger_event(
                    f"agent-chat-{conversation_id}",
                    "message",
                    {
                        "type": "roblox_env_progress",
                        "payload": {
                            "requestId": request_id,
                            "stage": stage,
                            "percentage": progress,
                            "message": message,
                        },
                    },
                )

                # Simulate processing time
                await asyncio.sleep(2)

            # Use agent manager to generate content
            from apps.backend.models.schemas import ContentRequest

            content_request = ContentRequest(
                subject=(
                    spec.get("learning_objectives", ["General"])[0]
                    if spec.get("learning_objectives")
                    else "General"
                ),
                grade_level=self._extract_grade_level(spec.get("age_range", "5")),
                learning_objectives=[
                    {"title": obj, "description": ""}
                    for obj in spec.get("learning_objectives", ["Interactive Learning"])
                ],
                environment_type=spec.get("map_type", "classroom"),
                include_quiz=True,
                difficulty_level=spec.get("difficulty", "medium"),
            )

            # Generate content using agent manager
            response = await get_agent_manager().generate_content(content_request)

            if response.success:
                # Send success message
                await pusher_trigger_event(
                    f"agent-chat-{conversation_id}",
                    "message",
                    {
                        "type": "roblox_env_ready",
                        "payload": {
                            "requestId": request_id,
                            "environmentId": response.content_id,
                            "previewUrl": f"/roblox/preview/{response.content_id}",
                            "downloadUrl": f"/roblox/download/{response.content_id}",
                        },
                    },
                )
            else:
                # Send error message
                await pusher_trigger_event(
                    f"agent-chat-{conversation_id}",
                    "message",
                    {
                        "type": "roblox_env_error",
                        "payload": {
                            "requestId": request_id,
                            "error": response.message or "Generation failed",
                        },
                    },
                )

            return request_id

        except Exception as e:
            logger.error(f"Error generating environment: {e}")
            await pusher_trigger_event(
                f"agent-chat-{conversation_id}",
                "message",
                {
                    "type": "roblox_env_error",
                    "payload": {
                        "requestId": request_id,
                        "error": f"Generation failed: {str(e)}",
                    },
                },
            )
            raise

    def _extract_grade_level(self, age_range: str) -> int:
        """Extract grade level from age range string"""
        try:
            # Look for numbers in the age range
            numbers = re.findall(r"\d+", str(age_range))
            if numbers:
                age = int(numbers[0])
                # Convert age to approximate grade level
                if age <= 5:
                    return 1
                elif age <= 18:
                    return min(age - 4, 12)
                else:
                    return 12
            return 5  # Default to grade 5
        except Exception:
            return 5

    def get_conversation_spec(self, conversation_id: str) -> dict[str, Any]:
        """Get current specification for a conversation"""
        return self.conversation_specs.get(conversation_id, {})

    def clear_conversation(self, conversation_id: str) -> None:
        """Clear conversation history and spec"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
        if conversation_id in self.conversation_specs:
            del self.conversation_specs[conversation_id]


# Global instance
roblox_ai_agent = RobloxAIAgent()
