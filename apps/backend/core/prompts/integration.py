"""
Main integration module for the prompt template organization system
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import asyncio

from .models import (
    ConversationContext, UserProfile, ContentRequirements, PersonalizationData,
    UniquenessEnhancement, PromptResponse, FlowDecision, ValidationResult
)
from .conversation_flow import ConversationFlowManager
from .template_engine import PromptTemplateEngine
from .user_guidance import UserGuidanceSystem
from .content_validation import ContentValidationSystem
from .workflow_orchestrator import WorkflowOrchestrator

logger = logging.getLogger(__name__)


class PromptTemplateIntegration:
    """
    Main integration class that coordinates all components of the prompt template
    organization system for creating unique, personalized educational content.
    """

    def __init__(self):
        self.flow_manager = ConversationFlowManager()
        self.template_engine = PromptTemplateEngine()
        self.guidance_system = UserGuidanceSystem()
        self.validation_system = ContentValidationSystem()
        self.workflow_orchestrator = WorkflowOrchestrator()

        # Integration status
        self.is_initialized = False
        self.active_conversations: Dict[str, ConversationContext] = {}

        logger.info("Prompt Template Integration initialized")

    async def initialize(self) -> bool:
        """Initialize the integration system"""
        try:
            # Initialize all components
            await self._initialize_components()
            self.is_initialized = True
            logger.info("Prompt Template Integration fully initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize integration: {e}")
            return False

    async def _initialize_components(self):
        """Initialize all system components"""
        # Components are already initialized in __init__
        # Additional initialization can be added here
        pass

    async def start_educational_content_creation(
        self,
        user_profile: UserProfile,
        initial_message: Optional[str] = None
    ) -> Tuple[ConversationContext, PromptResponse]:
        """
        Start the educational content creation process with a new conversation
        """

        if not self.is_initialized:
            await self.initialize()

        # Start conversation
        context = await self.flow_manager.start_conversation(user_profile, initial_message)

        # Generate initial prompt
        prompt_response = await self._generate_initial_prompt(context)

        # Store active conversation
        self.active_conversations[context.conversation_id] = context

        logger.info(f"Started educational content creation for user {user_profile.user_id}")

        return context, prompt_response

    async def process_user_input(
        self,
        conversation_id: str,
        user_input: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[PromptResponse, FlowDecision, Dict[str, Any]]:
        """
        Process user input and provide intelligent response with guidance
        """

        if not self.is_initialized:
            await self.initialize()

        # Process input through conversation flow
        prompt_response, flow_decision = await self.flow_manager.process_user_input(
            conversation_id, user_input, additional_context
        )

        # Get context for additional processing
        context = self.active_conversations.get(conversation_id)
        if not context:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Generate guidance
        guidance = await self.guidance_system.provide_guidance(
            context,
            guidance_type="suggestion",
            specific_area=context.current_stage.value
        )

        # Validate current state
        validation_result = await self.validation_system.validate_conversation_context(context)

        # Generate next steps
        next_steps = await self.guidance_system.get_next_steps(context)

        # Prepare response metadata
        response_metadata = {
            "guidance": guidance,
            "validation": validation_result.dict(),
            "next_steps": next_steps,
            "conversation_status": await self.flow_manager.get_conversation_status(conversation_id)
        }

        return prompt_response, flow_decision, response_metadata

    async def enhance_content_uniqueness(
        self,
        conversation_id: str,
        uniqueness_factors: List[str],
        creative_elements: List[str]
    ) -> Dict[str, Any]:
        """
        Enhance content uniqueness based on user preferences
        """

        context = self.active_conversations.get(conversation_id)
        if not context:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Create uniqueness enhancement
        uniqueness_data = UniquenessEnhancement(
            factors=uniqueness_factors,
            creative_twists=creative_elements,
            custom_elements={"enhanced": True, "timestamp": datetime.utcnow().isoformat()}
        )

        # Add to conversation context
        await self.flow_manager.add_uniqueness_enhancement(conversation_id, uniqueness_data)

        # Generate enhanced prompt
        enhanced_prompt = await self._generate_uniqueness_enhancement_prompt(context)

        return {
            "enhanced_prompt": enhanced_prompt,
            "uniqueness_score": await self._calculate_uniqueness_score(context),
            "suggestions": await self._get_uniqueness_suggestions(context)
        }

    async def personalize_content(
        self,
        conversation_id: str,
        personalization_data: PersonalizationData
    ) -> Dict[str, Any]:
        """
        Personalize content based on user-provided data
        """

        context = self.active_conversations.get(conversation_id)
        if not context:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Add personalization to conversation context
        await self.flow_manager.add_personalization_data(conversation_id, personalization_data)

        # Generate personalized prompt
        personalized_prompt = await self._generate_personalized_prompt(context)

        return {
            "personalized_prompt": personalized_prompt,
            "personalization_score": await self._calculate_personalization_score(context),
            "suggestions": await self._get_personalization_suggestions(context)
        }

    async def validate_and_optimize(
        self,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Validate current conversation state and provide optimization suggestions
        """

        context = self.active_conversations.get(conversation_id)
        if not context:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Comprehensive validation
        validation_result = await self.validation_system.validate_conversation_context(context)

        # Get optimization suggestions
        optimization_suggestions = await self._get_optimization_suggestions(context, validation_result)

        # Calculate quality metrics
        quality_metrics = await self._calculate_quality_metrics(context)

        return {
            "validation_result": validation_result.dict(),
            "optimization_suggestions": optimization_suggestions,
            "quality_metrics": quality_metrics,
            "readiness_score": await self._calculate_readiness_score(context, validation_result)
        }

    async def generate_content_workflow(
        self,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        Generate a complete content creation workflow based on conversation context
        """

        context = self.active_conversations.get(conversation_id)
        if not context:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Create workflow plan
        workflow_plan = await self.workflow_orchestrator.create_workflow_plan(context)

        # Execute workflow
        workflow_results = await self.workflow_orchestrator.execute_workflow(
            workflow_plan.plan_id,
            progress_callback=self._workflow_progress_callback
        )

        return {
            "workflow_plan": workflow_plan.dict(),
            "execution_results": workflow_results,
            "content_ready": workflow_results["status"] == "completed"
        }

    async def _generate_initial_prompt(self, context: ConversationContext) -> PromptResponse:
        """Generate the initial prompt for starting the conversation"""

        # Get greeting template
        greeting_template = self.template_engine.get_templates_by_stage(context.current_stage)[0]

        # Generate prompt
        prompt_response = self.template_engine.generate_prompt(
            greeting_template.id,
            context
        )

        return prompt_response

    async def _generate_uniqueness_enhancement_prompt(self, context: ConversationContext) -> str:
        """Generate a prompt for uniqueness enhancement"""

        if not context.uniqueness:
            return "No uniqueness data available for enhancement"

        template = """
🎨 **Let's Make Your Content Truly Unique!**

Based on your preferences, here are some amazing ways to make your {{ content_type }} stand out:

**🌟 Uniqueness Factors You've Chosen:**
{{ uniqueness_factors }}

**🎭 Creative Elements to Include:**
{{ creative_elements }}

**💡 Additional Suggestions:**
- Add unexpected plot twists that reinforce learning
- Include trending elements that your students will love
- Create custom characters based on your students' interests
- Incorporate local references and cultural elements

**🎮 Unique Mechanics to Consider:**
- Interactive storytelling with multiple endings
- Collaborative challenges that require teamwork
- Real-time problem solving with immediate feedback
- Creative expression through art, music, or writing

What specific unique elements would you like to explore further?
"""

        # Render template with context data
        from jinja2 import Template
        jinja_template = Template(template)

        rendered = jinja_template.render(
            content_type=context.requirements.content_type.value if context.requirements else "educational content",
            uniqueness_factors=", ".join([f.value for f in context.uniqueness.factors]),
            creative_elements=", ".join(context.uniqueness.creative_twists)
        )

        return rendered

    async def _generate_personalized_prompt(self, context: ConversationContext) -> str:
        """Generate a personalized prompt based on user data"""

        if not context.personalization:
            return "No personalization data available"

        template = """
👥 **Personalizing Your Content for Your Students!**

I'm customizing your {{ content_type }} to make it perfect for your class:

**👨‍🎓 Student Names to Include:**
{{ student_names }}

**🏫 School & Community Elements:**
{{ school_elements }}

**🌍 Cultural & Local References:**
{{ cultural_elements }}

**🎨 Visual & Thematic Elements:**
{{ visual_elements }}

**📚 Story & Interest Integration:**
{{ story_elements }}

This personalized approach will make your students feel like the content was created specifically for them!
"""

        # Render template with personalization data
        from jinja2 import Template
        jinja_template = Template(template)

        rendered = jinja_template.render(
            content_type=context.requirements.content_type.value if context.requirements else "educational content",
            student_names=", ".join(context.personalization.student_names[:5]),
            school_elements=context.personalization.school_theme or "Your school's unique theme",
            cultural_elements=", ".join(context.personalization.cultural_elements[:3]),
            visual_elements=", ".join(context.personalization.colors[:3]) if context.personalization.colors else "Custom color scheme",
            story_elements=", ".join(context.personalization.story_elements[:3])
        )

        return rendered

    async def _calculate_uniqueness_score(self, context: ConversationContext) -> float:
        """Calculate uniqueness score for the conversation context"""

        if not context.uniqueness:
            return 0.0

        score = 0.0

        # Factor in uniqueness factors
        score += len(context.uniqueness.factors) * 0.1

        # Factor in creative elements
        score += len(context.uniqueness.creative_twists) * 0.15

        # Factor in custom elements
        score += len(context.uniqueness.custom_elements) * 0.1

        # Factor in personal touches
        score += len(context.uniqueness.personal_touches) * 0.1

        # Factor in trending elements
        score += len(context.uniqueness.trending_elements) * 0.05

        return min(1.0, score)

    async def _calculate_personalization_score(self, context: ConversationContext) -> float:
        """Calculate personalization score for the conversation context"""

        if not context.personalization:
            return 0.0

        score = 0.0

        # Factor in student names
        if context.personalization.student_names:
            score += 0.2

        # Factor in cultural elements
        if context.personalization.cultural_elements:
            score += 0.2

        # Factor in local references
        if context.personalization.local_landmarks:
            score += 0.15

        # Factor in school theme
        if context.personalization.school_theme:
            score += 0.15

        # Factor in interests
        if context.personalization.story_elements:
            score += 0.15

        # Factor in visual elements
        if context.personalization.colors:
            score += 0.15

        return min(1.0, score)

    async def _get_uniqueness_suggestions(self, context: ConversationContext) -> List[str]:
        """Get suggestions for enhancing uniqueness"""

        suggestions = []

        if not context.uniqueness or not context.uniqueness.factors:
            suggestions.append("Add uniqueness factors like custom themes or unique mechanics")

        if not context.uniqueness or not context.uniqueness.creative_twists:
            suggestions.append("Include creative storytelling elements or unexpected twists")

        if not context.uniqueness or not context.uniqueness.trending_elements:
            suggestions.append("Incorporate current trends or popular culture references")

        return suggestions

    async def _get_personalization_suggestions(self, context: ConversationContext) -> List[str]:
        """Get suggestions for enhancing personalization"""

        suggestions = []

        if not context.personalization or not context.personalization.student_names:
            suggestions.append("Include student names to make content more personal")

        if not context.personalization or not context.personalization.cultural_elements:
            suggestions.append("Add cultural elements that reflect your students' backgrounds")

        if not context.personalization or not context.personalization.local_landmarks:
            suggestions.append("Include local references to make content more relevant")

        return suggestions

    async def _get_optimization_suggestions(
        self,
        context: ConversationContext,
        validation_result: ValidationResult
    ) -> List[str]:
        """Get optimization suggestions based on validation results"""

        suggestions = []

        if validation_result.completeness_score < 0.7:
            suggestions.append("Complete missing information to improve content quality")

        if validation_result.uniqueness_score < 0.5:
            suggestions.append("Add more unique and creative elements")

        if validation_result.engagement_score < 0.6:
            suggestions.append("Increase engagement level for better student participation")

        if validation_result.educational_value_score < 0.7:
            suggestions.append("Strengthen learning objectives and educational content")

        return suggestions

    async def _calculate_quality_metrics(self, context: ConversationContext) -> Dict[str, float]:
        """Calculate overall quality metrics"""

        validation_result = await self.validation_system.validate_conversation_context(context)

        return {
            "completeness": validation_result.completeness_score,
            "uniqueness": validation_result.uniqueness_score,
            "engagement": validation_result.engagement_score,
            "educational_value": validation_result.educational_value_score,
            "overall_quality": (
                validation_result.completeness_score * 0.2 +
                validation_result.uniqueness_score * 0.2 +
                validation_result.engagement_score * 0.3 +
                validation_result.educational_value_score * 0.3
            )
        }

    async def _calculate_readiness_score(
        self,
        context: ConversationContext,
        validation_result: ValidationResult
    ) -> float:
        """Calculate readiness score for content generation"""

        # Base score from validation
        base_score = (
            validation_result.completeness_score * 0.4 +
            validation_result.educational_value_score * 0.3 +
            validation_result.engagement_score * 0.2 +
            validation_result.uniqueness_score * 0.1
        )

        # Adjust based on conversation progress
        progress_bonus = len(context.completed_stages) * 0.1

        return min(1.0, base_score + progress_bonus)

    async def _workflow_progress_callback(self, progress_data: Dict[str, Any]):
        """Callback for workflow progress updates"""
        logger.info(f"Workflow progress: {progress_data['progress_percentage']:.1f}% - {progress_data.get('current_step', 'Unknown')}")

    async def get_conversation_analytics(self, conversation_id: str) -> Dict[str, Any]:
        """Get analytics for a conversation"""

        context = self.active_conversations.get(conversation_id)
        if not context:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Calculate analytics
        validation_result = await self.validation_system.validate_conversation_context(context)
        quality_metrics = await self._calculate_quality_metrics(context)

        return {
            "conversation_id": conversation_id,
            "duration_minutes": (datetime.utcnow() - context.created_at).total_seconds() / 60,
            "stages_completed": len(context.completed_stages),
            "current_stage": context.current_stage.value,
            "data_points_collected": len(context.collected_data),
            "quality_metrics": quality_metrics,
            "validation_summary": await self.validation_system.get_validation_summary(context),
            "readiness_score": await self._calculate_readiness_score(context, validation_result)
        }

    async def cleanup_conversation(self, conversation_id: str) -> bool:
        """Clean up a completed conversation"""

        if conversation_id in self.active_conversations:
            del self.active_conversations[conversation_id]
            logger.info(f"Cleaned up conversation {conversation_id}")
            return True

        return False

    def get_active_conversations(self) -> List[str]:
        """Get list of active conversation IDs"""
        return list(self.active_conversations.keys())

    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""

        return {
            "is_initialized": self.is_initialized,
            "active_conversations": len(self.active_conversations),
            "components": {
                "flow_manager": "active",
                "template_engine": "active",
                "guidance_system": "active",
                "validation_system": "active",
                "workflow_orchestrator": "active"
            },
            "templates_loaded": len(self.template_engine.get_all_templates()),
            "system_health": "healthy" if self.is_initialized else "initializing"
        }


