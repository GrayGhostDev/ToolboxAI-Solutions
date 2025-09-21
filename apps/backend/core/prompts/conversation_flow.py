"""
Conversation Flow Manager for guiding users through educational content creation
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import asyncio
from enum import Enum

from .models import (
    ConversationContext, ConversationStage, PromptTemplate, PromptResponse,
    UserProfile, ContentRequirements, PersonalizationData, UniquenessEnhancement,
    ContentType, GradeLevel, SubjectArea, LearningStyle, EngagementLevel
)
from .template_engine import PromptTemplateEngine
from .user_guidance import UserGuidanceSystem
from .content_validation import ContentValidationSystem

logger = logging.getLogger(__name__)


class FlowDecision(str, Enum):
    """Decisions that can be made during conversation flow"""
    CONTINUE = "continue"
    BRANCH = "branch"
    LOOP_BACK = "loop_back"
    COMPLETE = "complete"
    ESCALATE = "escalate"


class ConversationFlowManager:
    """
    Manages the flow of conversations to guide users through educational content creation
    with focus on uniqueness, personalization, and engagement.
    """

    def __init__(self):
        self.template_engine = PromptTemplateEngine()
        self.guidance_system = UserGuidanceSystem()
        self.validation_system = ContentValidationSystem()
        self.active_conversations: Dict[str, ConversationContext] = {}

        # Define conversation flow rules
        self.flow_rules = self._define_flow_rules()

        # Define stage transitions
        self.stage_transitions = self._define_stage_transitions()

    def _define_flow_rules(self) -> Dict[ConversationStage, Dict[str, Any]]:
        """Define rules for each conversation stage"""
        return {
            ConversationStage.GREETING: {
                "required_data": [],
                "optional_data": ["user_experience_level"],
                "next_stages": [ConversationStage.DISCOVERY],
                "max_duration_minutes": 5,
                "required_confidence": 0.7
            },
            ConversationStage.DISCOVERY: {
                "required_data": ["content_type", "grade_level", "subject_area"],
                "optional_data": ["learning_objectives", "student_count", "duration"],
                "next_stages": [ConversationStage.REQUIREMENTS],
                "max_duration_minutes": 10,
                "required_confidence": 0.8
            },
            ConversationStage.REQUIREMENTS: {
                "required_data": ["learning_objectives", "engagement_level", "duration_minutes"],
                "optional_data": ["prerequisites", "assessment_type", "accessibility_requirements"],
                "next_stages": [ConversationStage.PERSONALIZATION],
                "max_duration_minutes": 15,
                "required_confidence": 0.85
            },
            ConversationStage.PERSONALIZATION: {
                "required_data": ["student_interests", "cultural_elements"],
                "optional_data": ["local_references", "school_theme", "personal_touches"],
                "next_stages": [ConversationStage.CONTENT_DESIGN, ConversationStage.UNIQUENESS_ENHANCEMENT],
                "max_duration_minutes": 20,
                "required_confidence": 0.9
            },
            ConversationStage.CONTENT_DESIGN: {
                "required_data": ["content_structure", "interactive_elements"],
                "optional_data": ["visual_style", "audio_style", "character_elements"],
                "next_stages": [ConversationStage.UNIQUENESS_ENHANCEMENT],
                "max_duration_minutes": 15,
                "required_confidence": 0.85
            },
            ConversationStage.UNIQUENESS_ENHANCEMENT: {
                "required_data": ["uniqueness_factors", "creative_elements"],
                "optional_data": ["trending_elements", "personal_touches", "special_features"],
                "next_stages": [ConversationStage.VALIDATION],
                "max_duration_minutes": 10,
                "required_confidence": 0.8
            },
            ConversationStage.VALIDATION: {
                "required_data": ["quality_metrics", "completeness_check"],
                "optional_data": ["accessibility_check", "performance_check"],
                "next_stages": [ConversationStage.GENERATION, ConversationStage.REVIEW],
                "max_duration_minutes": 5,
                "required_confidence": 0.9
            },
            ConversationStage.GENERATION: {
                "required_data": ["generation_plan", "agent_assignments"],
                "optional_data": ["progress_tracking", "quality_monitoring"],
                "next_stages": [ConversationStage.REVIEW],
                "max_duration_minutes": 30,
                "required_confidence": 0.95
            },
            ConversationStage.REVIEW: {
                "required_data": ["content_preview", "quality_assessment"],
                "optional_data": ["adjustment_requests", "deployment_preferences"],
                "next_stages": [ConversationStage.DEPLOYMENT, ConversationStage.CONTENT_DESIGN],
                "max_duration_minutes": 10,
                "required_confidence": 0.9
            },
            ConversationStage.DEPLOYMENT: {
                "required_data": ["deployment_plan", "student_access"],
                "optional_data": ["monitoring_setup", "feedback_collection"],
                "next_stages": [],
                "max_duration_minutes": 5,
                "required_confidence": 0.95
            }
        }

    def _define_stage_transitions(self) -> Dict[ConversationStage, List[ConversationStage]]:
        """Define valid stage transitions"""
        return {
            ConversationStage.GREETING: [ConversationStage.DISCOVERY],
            ConversationStage.DISCOVERY: [ConversationStage.REQUIREMENTS, ConversationStage.GREETING],
            ConversationStage.REQUIREMENTS: [ConversationStage.PERSONALIZATION, ConversationStage.DISCOVERY],
            ConversationStage.PERSONALIZATION: [ConversationStage.CONTENT_DESIGN, ConversationStage.UNIQUENESS_ENHANCEMENT, ConversationStage.REQUIREMENTS],
            ConversationStage.CONTENT_DESIGN: [ConversationStage.UNIQUENESS_ENHANCEMENT, ConversationStage.PERSONALIZATION],
            ConversationStage.UNIQUENESS_ENHANCEMENT: [ConversationStage.VALIDATION, ConversationStage.CONTENT_DESIGN],
            ConversationStage.VALIDATION: [ConversationStage.GENERATION, ConversationStage.REVIEW, ConversationStage.UNIQUENESS_ENHANCEMENT],
            ConversationStage.GENERATION: [ConversationStage.REVIEW],
            ConversationStage.REVIEW: [ConversationStage.DEPLOYMENT, ConversationStage.CONTENT_DESIGN, ConversationStage.GENERATION],
            ConversationStage.DEPLOYMENT: []
        }

    async def start_conversation(
        self,
        user_profile: UserProfile,
        initial_message: Optional[str] = None
    ) -> ConversationContext:
        """Start a new conversation with a user"""

        context = ConversationContext(
            conversation_id=f"conv_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{user_profile.user_id[:8]}",
            user_profile=user_profile,
            current_stage=ConversationStage.GREETING
        )

        self.active_conversations[context.conversation_id] = context

        logger.info(f"Started conversation {context.conversation_id} for user {user_profile.user_id}")

        return context

    async def process_user_input(
        self,
        conversation_id: str,
        user_input: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[PromptResponse, FlowDecision]:
        """Process user input and determine next steps"""

        context = self.active_conversations.get(conversation_id)
        if not context:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Update conversation history
        context.conversation_history.append({
            "timestamp": datetime.utcnow(),
            "role": "user",
            "content": user_input,
            "stage": context.current_stage.value
        })

        # Extract information from user input
        extracted_data = await self._extract_information(user_input, context)
        context.collected_data.update(extracted_data)

        # Determine if we can progress to next stage
        can_progress, next_stage = await self._evaluate_stage_progression(context)

        if can_progress and next_stage:
            # Move to next stage
            context.completed_stages.append(context.current_stage)
            context.current_stage = next_stage
            context.updated_at = datetime.utcnow()

        # Generate appropriate prompt
        prompt_response = await self._generate_stage_prompt(context, additional_context)

        # Determine flow decision
        flow_decision = await self._determine_flow_decision(context, prompt_response)

        # Update conversation history with AI response
        context.conversation_history.append({
            "timestamp": datetime.utcnow(),
            "role": "assistant",
            "content": prompt_response.generated_text,
            "stage": context.current_stage.value,
            "confidence": prompt_response.confidence_score
        })

        return prompt_response, flow_decision

    async def _extract_information(
        self,
        user_input: str,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Extract relevant information from user input"""

        extracted = {}
        current_stage = context.current_stage

        # Stage-specific information extraction
        if current_stage == ConversationStage.DISCOVERY:
            extracted.update(await self._extract_discovery_info(user_input))
        elif current_stage == ConversationStage.REQUIREMENTS:
            extracted.update(await self._extract_requirements_info(user_input))
        elif current_stage == ConversationStage.PERSONALIZATION:
            extracted.update(await self._extract_personalization_info(user_input))
        elif current_stage == ConversationStage.CONTENT_DESIGN:
            extracted.update(await self._extract_design_info(user_input))
        elif current_stage == ConversationStage.UNIQUENESS_ENHANCEMENT:
            extracted.update(await self._extract_uniqueness_info(user_input))

        return extracted

    async def _extract_discovery_info(self, user_input: str) -> Dict[str, Any]:
        """Extract information during discovery stage"""
        extracted = {}

        # Extract content type
        content_types = {
            "lesson": ContentType.LESSON,
            "quiz": ContentType.QUIZ,
            "simulation": ContentType.SIMULATION,
            "game": ContentType.GAME,
            "story": ContentType.INTERACTIVE_STORY,
            "field trip": ContentType.VIRTUAL_FIELD_TRIP,
            "lab": ContentType.LAB_EXPERIMENT,
            "project": ContentType.COLLABORATIVE_PROJECT
        }

        for keyword, content_type in content_types.items():
            if keyword in user_input.lower():
                extracted["content_type"] = content_type.value
                break

        # Extract grade level
        grade_keywords = {
            "pre-k": GradeLevel.PRE_K,
            "kindergarten": GradeLevel.KINDERGARTEN,
            "k-2": GradeLevel.ELEMENTARY_1_2,
            "elementary": GradeLevel.ELEMENTARY_3_5,
            "middle school": GradeLevel.MIDDLE_SCHOOL,
            "high school": GradeLevel.HIGH_SCHOOL,
            "college": GradeLevel.COLLEGE
        }

        for keyword, grade_level in grade_keywords.items():
            if keyword in user_input.lower():
                extracted["grade_level"] = grade_level.value
                break

        # Extract subject area
        subject_keywords = {
            "science": SubjectArea.SCIENCE,
            "math": SubjectArea.MATHEMATICS,
            "language": SubjectArea.LANGUAGE_ARTS,
            "social studies": SubjectArea.SOCIAL_STUDIES,
            "history": SubjectArea.HISTORY,
            "art": SubjectArea.ART,
            "music": SubjectArea.MUSIC,
            "pe": SubjectArea.PHYSICAL_EDUCATION,
            "computer": SubjectArea.COMPUTER_SCIENCE
        }

        for keyword, subject_area in subject_keywords.items():
            if keyword in user_input.lower():
                extracted["subject_area"] = subject_area.value
                break

        # Extract learning objectives
        if "learn" in user_input.lower() or "teach" in user_input.lower():
            # Simple extraction - in production, use NLP
            extracted["learning_objectives"] = [user_input]

        return extracted

    async def _extract_requirements_info(self, user_input: str) -> Dict[str, Any]:
        """Extract information during requirements stage"""
        extracted = {}

        # Extract duration
        import re
        duration_match = re.search(r'(\d+)\s*(min|minutes|hour|hours)', user_input.lower())
        if duration_match:
            duration = int(duration_match.group(1))
            if duration_match.group(2) in ['hour', 'hours']:
                duration *= 60
            extracted["duration_minutes"] = duration

        # Extract engagement level
        if "high" in user_input.lower() and "engagement" in user_input.lower():
            extracted["engagement_level"] = EngagementLevel.HIGH.value
        elif "interactive" in user_input.lower():
            extracted["engagement_level"] = EngagementLevel.MODERATE.value
        elif "passive" in user_input.lower():
            extracted["engagement_level"] = EngagementLevel.PASSIVE.value

        # Extract student count
        count_match = re.search(r'(\d+)\s*students?', user_input.lower())
        if count_match:
            extracted["student_count"] = int(count_match.group(1))

        return extracted

    async def _extract_personalization_info(self, user_input: str) -> Dict[str, Any]:
        """Extract information during personalization stage"""
        extracted = {}

        # Extract student interests
        interest_keywords = ["interested", "love", "enjoy", "fascinated", "excited"]
        if any(keyword in user_input.lower() for keyword in interest_keywords):
            # Simple extraction - in production, use NLP
            extracted["student_interests"] = [user_input]

        # Extract cultural elements
        cultural_keywords = ["culture", "tradition", "heritage", "background", "community"]
        if any(keyword in user_input.lower() for keyword in cultural_keywords):
            extracted["cultural_elements"] = [user_input]

        # Extract local references
        local_keywords = ["local", "nearby", "city", "town", "landmark", "school"]
        if any(keyword in user_input.lower() for keyword in local_keywords):
            extracted["local_references"] = [user_input]

        return extracted

    async def _extract_design_info(self, user_input: str) -> Dict[str, Any]:
        """Extract information during content design stage"""
        extracted = {}

        # Extract visual style preferences
        visual_keywords = ["color", "theme", "style", "look", "appearance", "design"]
        if any(keyword in user_input.lower() for keyword in visual_keywords):
            extracted["visual_style"] = user_input

        # Extract interactive elements
        interactive_keywords = ["click", "drag", "move", "interact", "play", "explore"]
        if any(keyword in user_input.lower() for keyword in interactive_keywords):
            extracted["interactive_elements"] = [user_input]

        return extracted

    async def _extract_uniqueness_info(self, user_input: str) -> Dict[str, Any]:
        """Extract information during uniqueness enhancement stage"""
        extracted = {}

        # Extract creative elements
        creative_keywords = ["unique", "special", "creative", "different", "original", "custom"]
        if any(keyword in user_input.lower() for keyword in creative_keywords):
            extracted["creative_elements"] = [user_input]

        # Extract trending elements
        trending_keywords = ["trending", "popular", "viral", "current", "modern", "latest"]
        if any(keyword in user_input.lower() for keyword in trending_keywords):
            extracted["trending_elements"] = [user_input]

        return extracted

    async def _evaluate_stage_progression(
        self,
        context: ConversationContext
    ) -> Tuple[bool, Optional[ConversationStage]]:
        """Evaluate if conversation can progress to next stage"""

        current_stage = context.current_stage
        rules = self.flow_rules.get(current_stage, {})

        # Check if required data is present
        required_data = rules.get("required_data", [])
        for data_key in required_data:
            if data_key not in context.collected_data:
                return False, None

        # Check confidence level
        required_confidence = rules.get("required_confidence", 0.7)
        # In production, calculate actual confidence based on data quality
        current_confidence = 0.8  # Placeholder

        if current_confidence < required_confidence:
            return False, None

        # Determine next stage
        next_stages = rules.get("next_stages", [])
        if next_stages:
            # For now, take the first available next stage
            # In production, use more sophisticated logic
            return True, next_stages[0]

        return False, None

    async def _generate_stage_prompt(
        self,
        context: ConversationContext,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> PromptResponse:
        """Generate appropriate prompt for current stage"""

        # Get templates for current stage
        stage_templates = self.template_engine.get_templates_by_stage(context.current_stage)

        if not stage_templates:
            raise ValueError(f"No templates found for stage {context.current_stage}")

        # Select best template based on context
        selected_template = self._select_best_template(stage_templates, context)

        # Generate prompt
        prompt_response = self.template_engine.generate_prompt(
            selected_template.id,
            context,
            additional_context
        )

        return prompt_response

    def _select_best_template(
        self,
        templates: List[PromptTemplate],
        context: ConversationContext
    ) -> PromptTemplate:
        """Select the best template for current context"""

        # For now, select based on priority
        # In production, use more sophisticated selection logic
        best_template = max(templates, key=lambda t: t.priority)

        return best_template

    async def _determine_flow_decision(
        self,
        context: ConversationContext,
        prompt_response: PromptResponse
    ) -> FlowDecision:
        """Determine the next flow decision based on context and response"""

        # Check if conversation is complete
        if context.current_stage == ConversationStage.DEPLOYMENT:
            return FlowDecision.COMPLETE

        # Check if we need to loop back for more information
        if prompt_response.confidence_score < 0.7:
            return FlowDecision.LOOP_BACK

        # Check if we need to branch to a different stage
        if context.current_stage == ConversationStage.PERSONALIZATION:
            # Check if we have enough personalization data
            if not context.personalization:
                return FlowDecision.BRANCH

        # Check if we need to escalate to human support
        if prompt_response.confidence_score < 0.5:
            return FlowDecision.ESCALATE

        # Default to continue
        return FlowDecision.CONTINUE

    async def get_conversation_status(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a conversation"""

        context = self.active_conversations.get(conversation_id)
        if not context:
            return None

        return {
            "conversation_id": context.conversation_id,
            "current_stage": context.current_stage.value,
            "completed_stages": [stage.value for stage in context.completed_stages],
            "progress_percentage": len(context.completed_stages) / len(ConversationStage) * 100,
            "collected_data_keys": list(context.collected_data.keys()),
            "last_updated": context.updated_at.isoformat()
        }

    async def update_user_profile(
        self,
        conversation_id: str,
        profile_updates: Dict[str, Any]
    ) -> bool:
        """Update user profile during conversation"""

        context = self.active_conversations.get(conversation_id)
        if not context:
            return False

        # Update profile fields
        for key, value in profile_updates.items():
            if hasattr(context.user_profile, key):
                setattr(context.user_profile, key, value)

        context.updated_at = datetime.utcnow()
        return True

    async def add_personalization_data(
        self,
        conversation_id: str,
        personalization_data: PersonalizationData
    ) -> bool:
        """Add personalization data to conversation"""

        context = self.active_conversations.get(conversation_id)
        if not context:
            return False

        context.personalization = personalization_data
        context.updated_at = datetime.utcnow()
        return True

    async def add_uniqueness_enhancement(
        self,
        conversation_id: str,
        uniqueness_data: UniquenessEnhancement
    ) -> bool:
        """Add uniqueness enhancement data to conversation"""

        context = self.active_conversations.get(conversation_id)
        if not context:
            return False

        context.uniqueness = uniqueness_data
        context.updated_at = datetime.utcnow()
        return True

    async def complete_conversation(self, conversation_id: str) -> Optional[ConversationContext]:
        """Mark conversation as complete and return final context"""

        context = self.active_conversations.get(conversation_id)
        if not context:
            return None

        context.current_stage = ConversationStage.DEPLOYMENT
        context.updated_at = datetime.utcnow()

        return context

    def get_active_conversations(self) -> List[str]:
        """Get list of active conversation IDs"""
        return list(self.active_conversations.keys())

    async def cleanup_old_conversations(self, max_age_hours: int = 24):
        """Clean up old conversations"""

        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)

        to_remove = []
        for conv_id, context in self.active_conversations.items():
            if context.updated_at.timestamp() < cutoff_time:
                to_remove.append(conv_id)

        for conv_id in to_remove:
            del self.active_conversations[conv_id]

        logger.info(f"Cleaned up {len(to_remove)} old conversations")









