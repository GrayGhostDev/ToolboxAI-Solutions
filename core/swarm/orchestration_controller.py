"""Orchestration Controller for Educational Agent Swarm

This controller orchestrates the newly created educational agents,
handling complex workflows and ensuring intelligent, interactive responses.
"""

import asyncio
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from ..agents.base_agent import TaskResult
from ..agents.educational import (
    AdaptiveLearningAgent,
    AssessmentDesignAgent,
    CurriculumAlignmentAgent,
    EducationalValidationAgent,
    LearningAnalyticsAgent,
)
from ..agents.nlu.context_extractor import ContextExtractor
from ..agents.nlu.conversation_manager import ConversationManager, ConversationState
from ..agents.nlu.nlu_agent import IntentType, NLUAgent
from .message_bus import MessageBus, MessageBusConfig


class OrchestrationMode(Enum):
    """Orchestration modes for different interaction patterns."""

    CONVERSATIONAL = "conversational"  # Natural dialogue
    WORKFLOW = "workflow"  # Multi-step process
    COLLABORATIVE = "collaborative"  # Multiple agents working together
    ADAPTIVE = "adaptive"  # Adjusts based on user needs
    GUIDED = "guided"  # Step-by-step assistance


@dataclass
class SessionContext:
    """Context for a user session."""

    session_id: str
    user_id: Optional[str]
    started_at: datetime

    # Conversation state
    conversation_history: list[dict[str, Any]] = field(default_factory=list)
    current_state: ConversationState = ConversationState.GREETING
    accumulated_context: dict[str, Any] = field(default_factory=dict)

    # Educational context
    grade_level: Optional[str] = None
    subject: Optional[str] = None
    topics: list[str] = field(default_factory=list)
    learning_objectives: list[str] = field(default_factory=list)

    # Personalization
    learning_style: Optional[str] = None
    preferences: dict[str, Any] = field(default_factory=dict)
    performance_history: list[dict[str, Any]] = field(default_factory=list)

    # Workflow state
    active_workflows: list[str] = field(default_factory=list)
    completed_tasks: list[str] = field(default_factory=list)
    pending_questions: list[str] = field(default_factory=list)

    def update_from_nlu(self, nlu_result: dict[str, Any]):
        """Update context from NLU results."""
        entities = nlu_result.get("entities", {})

        if "grade_level" in entities and not self.grade_level:
            self.grade_level = entities["grade_level"]

        if "subject" in entities and not self.subject:
            self.subject = entities["subject"]

        if "topic" in entities:
            topic = entities["topic"]
            if topic not in self.topics:
                self.topics.append(topic)

    def add_to_history(self, role: str, content: str, metadata: Optional[dict] = None):
        """Add entry to conversation history."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
        }
        if metadata:
            entry["metadata"] = metadata

        self.conversation_history.append(entry)

        # Keep history manageable
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-40:]


@dataclass
class OrchestrationPlan:
    """Execution plan for orchestrating agents."""

    plan_id: str
    session_id: str
    intent: IntentType

    # Agent execution plan
    primary_agent: str
    supporting_agents: list[str]
    execution_order: str  # "sequential", "parallel", "adaptive"

    # Data flow
    data_dependencies: dict[str, list[str]]  # agent -> [required data]
    output_mapping: dict[str, str]  # agent output -> next agent input

    # Conditions and rules
    conditions: list[dict[str, Any]]
    fallback_agents: list[str]

    # Expected outcomes
    expected_outputs: list[str]
    success_criteria: dict[str, Any]


class OrchestrationController:
    """
    Advanced orchestration controller for educational agent swarm.

    This controller manages intelligent, context-aware interactions
    between agents to provide natural, helpful responses.
    """

    def __init__(self):
        """Initialize the Orchestration Controller."""
        self.logger = logging.getLogger(__name__)

        # Core components
        self.sessions: dict[str, SessionContext] = {}
        self.message_bus = MessageBus(MessageBusConfig())

        # NLU and conversation management
        self.nlu_agent = NLUAgent()
        self.context_extractor = ContextExtractor()
        self.conversation_manager = ConversationManager()

        # Educational agents
        self.agents = {
            "curriculum": CurriculumAlignmentAgent(),
            "analytics": LearningAnalyticsAgent(),
            "assessment": AssessmentDesignAgent(),
            "validation": EducationalValidationAgent(),
            "adaptive": AdaptiveLearningAgent(),
        }

        # Intent routing configuration
        self.intent_routing = self._configure_intent_routing()

        # Response templates for natural language
        self.response_templates = self._load_response_templates()

        # Performance tracking
        self.metrics = defaultdict(int)

    def _configure_intent_routing(self) -> dict[IntentType, dict[str, Any]]:
        """Configure how intents map to agent orchestration."""
        return {
            IntentType.CREATE_LESSON: {
                "primary": "curriculum",
                "supporting": ["adaptive", "validation"],
                "mode": OrchestrationMode.WORKFLOW,
            },
            IntentType.CREATE_QUIZ: {
                "primary": "assessment",
                "supporting": ["validation"],
                "mode": OrchestrationMode.WORKFLOW,
            },
            IntentType.CREATE_GAME: {
                "primary": "assessment",
                "supporting": ["adaptive", "validation"],
                "mode": OrchestrationMode.COLLABORATIVE,
            },
            IntentType.ANALYZE_PERFORMANCE: {
                "primary": "analytics",
                "supporting": ["adaptive"],
                "mode": OrchestrationMode.CONVERSATIONAL,
            },
            IntentType.PROVIDE_FEEDBACK: {
                "primary": "adaptive",
                "supporting": ["analytics"],
                "mode": OrchestrationMode.ADAPTIVE,
            },
            IntentType.EXPLAIN_CONCEPT: {
                "primary": "adaptive",
                "supporting": ["curriculum"],
                "mode": OrchestrationMode.GUIDED,
            },
            IntentType.DELEGATE_CONTROL: {
                "primary": "adaptive",
                "supporting": ["curriculum", "assessment"],
                "mode": OrchestrationMode.CONVERSATIONAL,
            },
        }

    def _load_response_templates(self) -> dict[str, list[str]]:
        """Load natural language response templates."""
        return {
            "greeting": [
                "Hello! I'm here to help you create engaging educational content for Roblox.",
                "Welcome! Let's create some amazing educational experiences together.",
                "Hi there! I'm ready to assist with your educational content needs.",
            ],
            "clarification": [
                "Could you tell me more about {topic}?",
                "I'd like to understand better - what {aspect} are you looking for?",
                "To help you best, could you specify {detail}?",
            ],
            "confirmation": [
                "Got it! I understand you want to {action}.",
                "Perfect! Let me {action} for you.",
                "Excellent! I'll {action} right away.",
            ],
            "progress": [
                "I'm working on {task}...",
                "Creating {item} based on your requirements...",
                "Analyzing {data} to provide the best solution...",
            ],
            "completion": [
                "I've completed {task} successfully!",
                "Here's {result} as requested.",
                "All done! {summary}",
            ],
            "error_recovery": [
                "I encountered a small issue, but I can help you another way.",
                "Let me try a different approach.",
                "I need a bit more information to proceed.",
            ],
        }

    async def process_interaction(
        self,
        user_input: str,
        session_id: Optional[str] = None,
        user_context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Process user interaction through intelligent orchestration.

        This is the main entry point for handling user requests with
        context accumulation and intelligent agent coordination.
        """
        # Create or retrieve session
        if not session_id:
            session_id = str(uuid.uuid4())

        session = self._get_or_create_session(session_id)

        # Add user input to history
        session.add_to_history("user", user_input)

        # Update session with provided context
        if user_context:
            session.accumulated_context.update(user_context)

        try:
            # Phase 1: Understanding
            understanding = await self._understand_input(user_input, session)

            # Phase 2: Planning
            plan = await self._create_orchestration_plan(understanding, session)

            # Phase 3: Execution
            results = await self._execute_plan(plan, session)

            # Phase 4: Response Generation
            response = await self._generate_response(results, session)

            # Update session state
            await self._update_session_state(session, understanding, results)

            # Add response to history
            session.add_to_history("assistant", response["message"])

            self.metrics["successful_interactions"] += 1

            return {
                "success": True,
                "session_id": session_id,
                "response": response,
                "context": {
                    "accumulated": session.accumulated_context,
                    "state": session.current_state.value,
                    "completed_tasks": session.completed_tasks,
                },
            }

        except Exception as e:
            self.logger.error(f"Orchestration error: {str(e)}")
            self.metrics["failed_interactions"] += 1

            # Generate helpful error response
            error_response = self._generate_error_response(str(e), session)

            return {
                "success": False,
                "session_id": session_id,
                "response": error_response,
                "error": str(e),
            }

    async def _understand_input(self, user_input: str, session: SessionContext) -> dict[str, Any]:
        """Understand user input through NLU and context extraction."""
        # Get full conversation context
        full_context = self._build_full_context(session)

        # NLU processing
        nlu_result = await self.nlu_agent.process(user_input, full_context)

        # Extract educational context
        edu_context = await self.context_extractor.extract_educational_context(
            user_input, full_context
        )

        # Update conversation state
        conv_state = await self.conversation_manager.process_turn(
            user_input, nlu_result.data, full_context
        )

        # Update session from NLU
        session.update_from_nlu(nlu_result.data)
        session.current_state = conv_state.state

        # Accumulate context
        if edu_context.get("grade_level") and not session.grade_level:
            session.grade_level = edu_context["grade_level"]

        if edu_context.get("subject") and not session.subject:
            session.subject = edu_context["subject"]

        session.learning_objectives.extend(edu_context.get("learning_objectives", []))

        return {
            "intent": nlu_result.data.get("primary_intent"),
            "entities": nlu_result.data.get("entities", {}),
            "sentiment": nlu_result.data.get("sentiment"),
            "educational_context": edu_context,
            "conversation_state": conv_state,
            "confidence": nlu_result.data.get("confidence", 0.0),
        }

    async def _create_orchestration_plan(
        self, understanding: dict[str, Any], session: SessionContext
    ) -> OrchestrationPlan:
        """Create execution plan based on understanding."""
        intent = understanding["intent"]

        # Get routing configuration
        routing = self.intent_routing.get(
            intent,
            {
                "primary": "adaptive",
                "supporting": [],
                "mode": OrchestrationMode.CONVERSATIONAL,
            },
        )

        # Determine execution order based on mode
        if routing["mode"] == OrchestrationMode.WORKFLOW:
            execution_order = "sequential"
        elif routing["mode"] == OrchestrationMode.COLLABORATIVE:
            execution_order = "parallel"
        else:
            execution_order = "adaptive"

        # Build data dependencies
        data_deps = self._build_data_dependencies(
            routing["primary"], routing["supporting"], session
        )

        plan = OrchestrationPlan(
            plan_id=str(uuid.uuid4()),
            session_id=session.session_id,
            intent=intent,
            primary_agent=routing["primary"],
            supporting_agents=routing["supporting"],
            execution_order=execution_order,
            data_dependencies=data_deps,
            output_mapping=self._build_output_mapping(routing),
            conditions=[],
            fallback_agents=["adaptive"],
            expected_outputs=self._determine_expected_outputs(intent),
            success_criteria={"completion": True},
        )

        return plan

    async def _execute_plan(
        self, plan: OrchestrationPlan, session: SessionContext
    ) -> dict[str, Any]:
        """Execute orchestration plan."""
        results = {}

        # Prepare base task data
        base_data = {
            "session_id": session.session_id,
            "grade_level": session.grade_level,
            "subject": session.subject,
            "topics": session.topics,
            "learning_objectives": session.learning_objectives,
            "accumulated_context": session.accumulated_context,
        }

        # Execute primary agent
        primary_result = await self._execute_agent(plan.primary_agent, base_data)
        results[plan.primary_agent] = primary_result

        # Execute supporting agents
        if plan.execution_order == "parallel":
            # Parallel execution
            tasks = []
            for agent_name in plan.supporting_agents:
                task_data = {**base_data, "primary_result": primary_result.data}
                tasks.append(self._execute_agent(agent_name, task_data))

            support_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, agent_name in enumerate(plan.supporting_agents):
                if not isinstance(support_results[i], Exception):
                    results[agent_name] = support_results[i]

        else:
            # Sequential execution
            previous_data = primary_result.data
            for agent_name in plan.supporting_agents:
                task_data = {**base_data, "previous_result": previous_data}
                result = await self._execute_agent(agent_name, task_data)
                results[agent_name] = result
                previous_data = result.data

        return results

    async def _execute_agent(self, agent_name: str, task_data: dict[str, Any]) -> TaskResult:
        """Execute task on specific agent."""
        if agent_name not in self.agents:
            return TaskResult(success=False, data={}, error=f"Agent {agent_name} not found")

        agent = self.agents[agent_name]

        # Prepare agent-specific data
        if agent_name == "curriculum":
            task_data["alignment_type"] = "comprehensive"
        elif agent_name == "analytics":
            task_data["type"] = "student_progress"
        elif agent_name == "assessment":
            task_data["design_type"] = "complete_assessment"
        elif agent_name == "validation":
            task_data["validation_type"] = "comprehensive"
        elif agent_name == "adaptive":
            task_data["task_type"] = "adapt_content"

        return await agent.process(task_data)

    async def _generate_response(
        self, results: dict[str, Any], session: SessionContext
    ) -> dict[str, str]:
        """Generate natural language response from results."""
        # Build response based on conversation state
        if session.current_state == ConversationState.GREETING:
            message = self._select_template("greeting")

        elif session.current_state == ConversationState.GATHERING_REQUIREMENTS:
            # Check what's still needed
            missing = self._identify_missing_requirements(session)
            if missing:
                message = f"I see you want to create educational content. "
                message += self._select_template("clarification").format(topic=missing[0])
            else:
                message = "Great! I have all the information I need. "
                message += "Let me create that for you."

        elif session.current_state == ConversationState.DESIGNING:
            message = self._build_design_response(results)

        elif session.current_state == ConversationState.IMPLEMENTING:
            message = self._build_implementation_response(results)

        elif session.current_state == ConversationState.REVIEWING:
            message = self._build_review_response(results)

        elif session.current_state == ConversationState.COMPLETED:
            message = self._build_completion_response(results)

        else:
            message = self._build_general_response(results)

        return {
            "message": message,
            "data": self._extract_key_data(results),
            "suggestions": self._generate_suggestions(session, results),
        }

    def _build_design_response(self, results: dict[str, Any]) -> str:
        """Build response for design phase."""
        response = "I'm designing your educational content with the following features:\n\n"

        if "curriculum" in results:
            curr_result = results["curriculum"]
            if curr_result.success and curr_result.data.get("aligned_standards"):
                standards = curr_result.data["aligned_standards"][:3]
                response += f"✓ Aligned with: {', '.join(standards)}\n"

        if "assessment" in results:
            assess_result = results["assessment"]
            if assess_result.success:
                response += f"✓ Includes interactive assessments\n"

        if "adaptive" in results:
            adapt_result = results["adaptive"]
            if adapt_result.success:
                response += f"✓ Personalized for different learning styles\n"

        response += "\nShall I proceed with creating this content?"

        return response

    def _build_implementation_response(self, results: dict[str, Any]) -> str:
        """Build response for implementation phase."""
        response = "I've successfully created your educational content:\n\n"

        for agent_name, result in results.items():
            if result.success:
                if agent_name == "assessment" and "assessment" in result.data:
                    assessment = result.data["assessment"]
                    response += f"📝 Assessment: {assessment.get('title', 'Created')}\n"
                    response += f"   - {assessment.get('total_questions', 0)} questions\n"
                    response += (
                        f"   - Estimated time: {assessment.get('time_limit', 30)} minutes\n\n"
                    )

                elif agent_name == "validation" and "validation_result" in result.data:
                    validation = result.data["validation_result"]
                    response += f"✅ Content validated: {validation.get('status', 'approved')}\n"
                    response += (
                        f"   - Quality score: {validation.get('overall_score', 0):.0f}/100\n\n"
                    )

        return response

    def _build_general_response(self, results: dict[str, Any]) -> str:
        """Build general response from results."""
        successful = sum(1 for r in results.values() if r.success)
        total = len(results)

        if successful == total:
            return (
                "I've successfully processed your request. "
                + "The educational content has been prepared according to your specifications."
            )
        elif successful > 0:
            return (
                "I've completed most of your request. "
                + "Some components may need additional refinement."
            )
        else:
            return (
                "I encountered some challenges with your request. "
                + "Let me try a different approach."
            )

    def _get_or_create_session(self, session_id: str) -> SessionContext:
        """Get existing session or create new one."""
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionContext(
                session_id=session_id, user_id=None, started_at=datetime.now()
            )

        return self.sessions[session_id]

    def _build_full_context(self, session: SessionContext) -> dict[str, Any]:
        """Build complete context from session."""
        # Extract conversation text
        conversation_text = "\n".join(
            [
                f"{entry['role']}: {entry['content']}"
                for entry in session.conversation_history[-10:]  # Last 10 turns
            ]
        )

        return {
            "conversation_history": conversation_text,
            "accumulated_context": session.accumulated_context,
            "grade_level": session.grade_level,
            "subject": session.subject,
            "topics": session.topics,
            "learning_objectives": session.learning_objectives,
            "current_state": session.current_state.value,
        }

    def _build_data_dependencies(
        self, primary: str, supporting: list[str], session: SessionContext
    ) -> dict[str, list[str]]:
        """Build data dependencies for agents."""
        deps = {}

        # Primary agent needs session context
        deps[primary] = ["session_context", "educational_context"]

        # Supporting agents need primary results
        for agent in supporting:
            deps[agent] = ["primary_result", "session_context"]

        return deps

    def _build_output_mapping(self, routing: dict[str, Any]) -> dict[str, str]:
        """Build output mapping between agents."""
        mapping = {}

        primary = routing["primary"]
        for support in routing["supporting"]:
            mapping[f"{primary}_output"] = f"{support}_input"

        return mapping

    def _determine_expected_outputs(self, intent: IntentType) -> list[str]:
        """Determine expected outputs based on intent."""
        if intent == IntentType.CREATE_LESSON:
            return ["lesson_content", "assessments", "validation_report"]
        elif intent == IntentType.CREATE_QUIZ:
            return ["quiz", "answer_key", "validation_report"]
        elif intent == IntentType.ANALYZE_PERFORMANCE:
            return ["performance_report", "recommendations"]
        else:
            return ["response", "data"]

    async def _update_session_state(
        self,
        session: SessionContext,
        understanding: dict[str, Any],
        results: dict[str, Any],
    ):
        """Update session state based on results."""
        # Update completed tasks
        intent = understanding["intent"]
        if intent:
            task_id = f"{intent.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            session.completed_tasks.append(task_id)

        # Update accumulated context with key results
        for agent_name, result in results.items():
            if result.success and result.data:
                key_data = self._extract_agent_key_data(agent_name, result.data)
                session.accumulated_context.update(key_data)

    def _extract_agent_key_data(self, agent_name: str, data: dict[str, Any]) -> dict[str, Any]:
        """Extract key data from agent results."""
        key_data = {}

        if agent_name == "curriculum":
            if "aligned_standards" in data:
                key_data["curriculum_standards"] = data["aligned_standards"]

        elif agent_name == "assessment":
            if "assessment" in data:
                key_data["assessment_created"] = True
                key_data["assessment_type"] = data["assessment"].get("type")

        elif agent_name == "adaptive":
            if "learning_style" in data:
                key_data["identified_learning_style"] = data["learning_style"]

        return key_data

    def _identify_missing_requirements(self, session: SessionContext) -> list[str]:
        """Identify what information is still needed."""
        missing = []

        if not session.grade_level:
            missing.append("grade level")

        if not session.subject:
            missing.append("subject")

        if not session.topics:
            missing.append("topic or concept")

        return missing

    def _extract_key_data(self, results: dict[str, Any]) -> dict[str, Any]:
        """Extract key data from all results."""
        key_data = {}

        for agent_name, result in results.items():
            if result.success and result.data:
                agent_data = self._extract_agent_key_data(agent_name, result.data)
                key_data.update(agent_data)

        return key_data

    def _generate_suggestions(self, session: SessionContext, results: dict[str, Any]) -> list[str]:
        """Generate helpful suggestions for next steps."""
        suggestions = []

        # Based on completed tasks
        if "assessment_created" in session.accumulated_context:
            suggestions.append("Would you like to preview the assessment?")
            suggestions.append("Should I create practice materials?")

        # Based on conversation state
        if session.current_state == ConversationState.COMPLETED:
            suggestions.append("Create another lesson")
            suggestions.append("Analyze student performance")
            suggestions.append("Generate progress report")

        elif session.current_state == ConversationState.GATHERING_REQUIREMENTS:
            if not session.grade_level:
                suggestions.append("Specify the grade level (e.g., 'Grade 5')")
            if not session.subject:
                suggestions.append("Tell me the subject area")

        return suggestions[:3]  # Limit to 3 suggestions

    def _select_template(self, category: str) -> str:
        """Select a response template."""
        import random

        templates = self.response_templates.get(category, [""])
        return random.choice(templates)

    def _generate_error_response(self, error: str, session: SessionContext) -> dict[str, str]:
        """Generate helpful error response."""
        message = "I encountered an issue, but I can still help you. "

        # Provide context-aware recovery
        if "grade_level" in error.lower():
            message += "Please specify the grade level (e.g., K-12)."
        elif "subject" in error.lower():
            message += "What subject would you like to focus on?"
        else:
            message += "Let me try a different approach. Could you rephrase your request?"

        return {
            "message": message,
            "data": {},
            "suggestions": [
                "Try providing more details",
                "Break down your request into smaller parts",
                "Ask for specific help",
            ],
        }
