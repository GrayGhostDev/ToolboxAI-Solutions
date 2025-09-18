"""
Prompt Template Engine for generating dynamic, personalized prompts
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import re
import json
from jinja2 import Template, Environment, BaseLoader
from langchain_core.prompts import PromptTemplate as LangChainPromptTemplate

from .models import (
    PromptTemplate, ConversationContext, PromptResponse,
    UserProfile, ContentRequirements, PersonalizationData,
    UniquenessEnhancement, ConversationStage, ContentType
)

logger = logging.getLogger(__name__)


class PromptTemplateEngine:
    """
    Advanced prompt template engine that generates personalized, context-aware prompts
    for guiding users through educational content creation.
    """

    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self.jinja_env = Environment(loader=BaseLoader())
        self._load_default_templates()

    def _load_default_templates(self):
        """Load default prompt templates for all conversation stages"""

        # Greeting Stage Templates
        self.templates["greeting_welcome"] = PromptTemplate(
            name="Welcome Greeting",
            stage=ConversationStage.GREETING,
            template_text="""
🎮 Welcome to the Roblox Educational Assistant!

I'm here to help you create **unique, engaging, and personalized** educational experiences that your students will love!

Let's start by understanding what you'd like to create. I can help you build:
• Interactive lessons that feel like games
• Immersive simulations and virtual field trips
• Collaborative projects that spark creativity
• Assessments that students actually enjoy taking

**What type of educational experience would you like to create today?**
""",
            next_stages=[ConversationStage.DISCOVERY],
            agent_assignments=["content_agent"],
            priority=1
        )

        # Discovery Stage Templates
        self.templates["discovery_content_type"] = PromptTemplate(
            name="Content Type Discovery",
            stage=ConversationStage.DISCOVERY,
            template_text="""
Great choice! Let's dive deeper into your {{ content_type }} idea.

To make this truly special and unique, I need to understand:

🎯 **What's the main learning goal?**
   (What should students know or be able to do after this experience?)

👥 **Who are your students?**
   - Grade level: {{ grade_level_options }}
   - Class size: How many students will participate?
   - Any special needs or learning styles to consider?

📚 **Subject area focus:**
   {{ subject_areas }}

💡 **What makes your students unique?**
   - Any particular interests, hobbies, or cultural backgrounds?
   - What topics get them most excited?
   - Any current events or trends they're following?

The more I know about your students, the more personalized and engaging I can make this experience!
""",
            variables=["content_type", "grade_level_options", "subject_areas"],
            next_stages=[ConversationStage.REQUIREMENTS],
            agent_assignments=["content_agent", "personalization_agent"],
            priority=2
        )

        # Requirements Stage Templates
        self.templates["requirements_detailed"] = PromptTemplate(
            name="Detailed Requirements Gathering",
            stage=ConversationStage.REQUIREMENTS,
            template_text="""
Perfect! Now let's get specific about your {{ content_type }} requirements:

📋 **Learning Objectives** (Be specific!)
   - What exactly should students learn?
   - What skills should they develop?
   - How will you measure success?

⏰ **Time & Structure**
   - How long should this experience be? (15 min, 45 min, multiple sessions?)
   - Should it be self-paced or teacher-guided?
   - Any specific sequence or flow you want?

🎮 **Engagement Level**
   - How interactive should it be?
   - Should it feel like a game, simulation, or interactive story?
   - Any specific mechanics or activities you want included?

🌍 **Personalization Opportunities**
   - Can we include local landmarks or references?
   - Any school themes, mascots, or traditions?
   - Student names or personal interests to incorporate?
   - Cultural elements that would resonate?

🎨 **Visual & Audio Style**
   - What mood or atmosphere are you going for?
   - Any color schemes, music styles, or visual themes?
   - Should it feel futuristic, historical, fantasy, or realistic?

The more details you provide, the more unique and tailored this will be!
""",
            variables=["content_type"],
            next_stages=[ConversationStage.PERSONALIZATION],
            agent_assignments=["requirements_agent", "design_agent"],
            priority=3
        )

        # Personalization Stage Templates
        self.templates["personalization_deep_dive"] = PromptTemplate(
            name="Deep Personalization",
            stage=ConversationStage.PERSONALIZATION,
            template_text="""
Excellent! Now let's make this truly **one-of-a-kind** for your students:

🎭 **Character & Story Elements**
   - Should we create custom characters based on your students?
   - Any specific storylines or narratives that would engage them?
   - What kind of hero's journey or adventure should they experience?

🏫 **School & Community Integration**
   - Local landmarks: {{ local_landmarks }}
   - School mascot: {{ school_mascot }}
   - Community events or traditions to reference?
   - Any partnerships with local organizations?

🌟 **Trending & Modern Elements**
   - What are your students currently obsessed with? (Games, shows, music, social media trends)
   - Any viral challenges or memes we could incorporate educationally?
   - Popular culture references that would make them excited?

🎨 **Creative Twists**
   - Any unexpected angles or creative approaches?
   - Humor, mystery, adventure, or fantasy elements?
   - Interactive surprises or Easter eggs?

🌍 **Cultural & Diversity**
   - How can we celebrate your students' diverse backgrounds?
   - Any cultural traditions, languages, or perspectives to include?
   - Ways to make all students feel represented and valued?

This is where we transform a standard lesson into something truly special and memorable!
""",
            variables=["local_landmarks", "school_mascot"],
            next_stages=[ConversationStage.CONTENT_DESIGN],
            agent_assignments=["personalization_agent", "creativity_agent"],
            priority=4
        )

        # Content Design Stage Templates
        self.templates["content_design_blueprint"] = PromptTemplate(
            name="Content Design Blueprint",
            stage=ConversationStage.CONTENT_DESIGN,
            template_text="""
🎨 **Let's Design Your Unique Educational Experience!**

Based on everything you've shared, here's what I'm envisioning:

**🎯 Core Concept:**
{{ content_concept }}

**🏗️ Structure & Flow:**
{{ content_structure }}

**🎮 Interactive Elements:**
{{ interactive_elements }}

**👥 Character Integration:**
{{ character_integration }}

**🌍 Personalization Features:**
{{ personalization_features }}

**🎨 Visual & Audio Style:**
{{ visual_style }}

**📊 Assessment Integration:**
{{ assessment_approach }}

**Does this capture your vision?** Let me know:
- What excites you most about this design?
- What would you like to adjust or enhance?
- Any additional elements you'd like to include?

Once you're happy with the design, I'll start building this amazing experience for your students!
""",
            variables=[
                "content_concept", "content_structure", "interactive_elements",
                "character_integration", "personalization_features",
                "visual_style", "assessment_approach"
            ],
            next_stages=[ConversationStage.UNIQUENESS_ENHANCEMENT, ConversationStage.GENERATION],
            agent_assignments=["design_agent", "content_agent", "creativity_agent"],
            priority=5
        )

        # Uniqueness Enhancement Templates
        self.templates["uniqueness_enhancement"] = PromptTemplate(
            name="Uniqueness Enhancement",
            stage=ConversationStage.UNIQUENESS_ENHANCEMENT,
            template_text="""
✨ **Let's Make This Absolutely Unique!**

I want to ensure your educational experience stands out and creates lasting memories. Let's add some special touches:

**🎭 Creative Storytelling Elements:**
- Custom narrative that connects to your students' interests
- Unexpected plot twists that reinforce learning
- Character development that mirrors student growth

**🎨 Visual Uniqueness:**
- Custom color schemes and visual themes
- Unique architectural or environmental designs
- Special effects and animations that wow students

**🎵 Audio & Atmosphere:**
- Custom sound effects and music
- Voice acting or narration
- Ambient sounds that enhance immersion

**🎮 Unique Mechanics:**
- Innovative interaction methods
- Creative problem-solving challenges
- Collaborative features that encourage teamwork

**🌟 Special Features:**
- Easter eggs and hidden surprises
- Dynamic content that changes based on student choices
- Integration with real-world data or current events

**Any specific ideas for making this truly special?** What would make your students say "This is the coolest thing we've ever done in class!"?
""",
            next_stages=[ConversationStage.VALIDATION],
            agent_assignments=["creativity_agent", "uniqueness_agent"],
            priority=6
        )

        # Validation Stage Templates
        self.templates["validation_check"] = PromptTemplate(
            name="Validation Check",
            stage=ConversationStage.VALIDATION,
            template_text="""
🔍 **Final Quality Check & Validation**

Let me verify that your educational experience meets all the best practices:

**✅ Educational Standards:**
- Learning objectives are clear and measurable
- Content aligns with {{ grade_level }} standards
- Assessment methods are appropriate and engaging

**✅ Engagement & Fun Factor:**
- Interactive elements are meaningful and fun
- Content is age-appropriate and culturally sensitive
- Students will be motivated to participate

**✅ Technical Feasibility:**
- All features can be implemented in Roblox
- Performance will be smooth for your class size
- Accessibility requirements are met

**✅ Uniqueness & Personalization:**
- Content is tailored to your specific students
- Includes unique elements that make it special
- Reflects your school's culture and values

**Everything looks great!** Your educational experience is ready to be built.

**🚀 Ready to generate your unique educational experience?**
""",
            variables=["grade_level"],
            next_stages=[ConversationStage.GENERATION],
            agent_assignments=["validation_agent", "quality_agent"],
            priority=7
        )

        # Generation Stage Templates
        self.templates["generation_start"] = PromptTemplate(
            name="Generation Start",
            stage=ConversationStage.GENERATION,
            template_text="""
🚀 **Building Your Unique Educational Experience!**

I'm now creating your personalized {{ content_type }} with all the special elements we discussed:

**🔄 Current Progress:**
{{ progress_status }}

**⏱️ Estimated Time:** {{ estimated_time }} minutes

**🎯 What's Being Created:**
{{ creation_details }}

**📊 Quality Metrics:**
- Uniqueness Score: {{ uniqueness_score }}%
- Engagement Level: {{ engagement_level }}
- Educational Value: {{ educational_value }}%

I'll keep you updated as I build each component. This is going to be amazing! 🎉
""",
            variables=[
                "content_type", "progress_status", "estimated_time",
                "creation_details", "uniqueness_score", "engagement_level", "educational_value"
            ],
            next_stages=[ConversationStage.REVIEW],
            agent_assignments=["generation_agent", "all_agents"],
            priority=8
        )

        # Review Stage Templates
        self.templates["review_presentation"] = PromptTemplate(
            name="Review Presentation",
            stage=ConversationStage.REVIEW,
            template_text="""
🎉 **Your Unique Educational Experience is Ready!**

Here's what I've created for you:

**📋 Overview:**
{{ content_overview }}

**🎮 Key Features:**
{{ key_features }}

**👥 Student Experience:**
{{ student_experience }}

**📊 Learning Outcomes:**
{{ learning_outcomes }}

**🎨 Unique Elements:**
{{ unique_elements }}

**📱 How to Use:**
{{ usage_instructions }}

**Would you like to:**
- Preview the experience?
- Make any adjustments?
- Deploy it to your students?
- Get additional resources or support?

This is going to be an unforgettable learning experience for your students! 🌟
""",
            variables=[
                "content_overview", "key_features", "student_experience",
                "learning_outcomes", "unique_elements", "usage_instructions"
            ],
            next_stages=[ConversationStage.DEPLOYMENT],
            agent_assignments=["review_agent", "presentation_agent"],
            priority=9
        )

    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get a specific template by ID"""
        return self.templates.get(template_id)

    def get_templates_by_stage(self, stage: ConversationStage) -> List[PromptTemplate]:
        """Get all templates for a specific conversation stage"""
        return [t for t in self.templates.values() if t.stage == stage and t.is_active]

    def generate_prompt(
        self,
        template_id: str,
        context: ConversationContext,
        additional_vars: Optional[Dict[str, Any]] = None
    ) -> PromptResponse:
        """Generate a personalized prompt using a template"""

        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Prepare variables for template rendering
        variables = self._prepare_variables(template, context, additional_vars)

        # Render the template
        jinja_template = self.jinja_env.from_string(template.template_text)
        generated_text = jinja_template.render(**variables)

        # Validate the generated content
        validation_results = self._validate_generated_content(generated_text, template)

        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(context, template, validation_results)

        return PromptResponse(
            template_id=template_id,
            generated_text=generated_text,
            variables_used=variables,
            next_questions=self._generate_next_questions(template, context),
            suggested_actions=self._generate_suggested_actions(template, context),
            agent_triggers=self._generate_agent_triggers(template, context),
            confidence_score=confidence_score,
            validation_results=validation_results
        )

    def _prepare_variables(
        self,
        template: PromptTemplate,
        context: ConversationContext,
        additional_vars: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Prepare variables for template rendering"""

        variables = {}

        # Add user profile data
        if context.user_profile:
            variables.update({
                "user_role": context.user_profile.role,
                "experience_level": context.user_profile.experience_level,
                "interests": context.user_profile.interests,
                "cultural_background": context.user_profile.cultural_background
            })

        # Add content requirements
        if context.requirements:
            variables.update({
                "content_type": context.requirements.content_type.value,
                "subject_area": context.requirements.subject_area.value,
                "grade_level": context.requirements.grade_level.value,
                "learning_objectives": context.requirements.learning_objectives,
                "engagement_level": context.requirements.engagement_level.value
            })

        # Add personalization data
        if context.personalization:
            variables.update({
                "student_names": context.personalization.student_names,
                "local_landmarks": context.personalization.local_landmarks,
                "cultural_elements": context.personalization.cultural_elements,
                "school_theme": context.personalization.school_theme,
                "mascot": context.personalization.mascot,
                "colors": context.personalization.colors
            })

        # Add uniqueness data
        if context.uniqueness:
            variables.update({
                "uniqueness_factors": [f.value for f in context.uniqueness.factors],
                "custom_elements": context.uniqueness.custom_elements,
                "creative_twists": context.uniqueness.creative_twists
            })

        # Add conversation data
        variables.update({
            "conversation_id": context.conversation_id,
            "current_stage": context.current_stage.value,
            "collected_data": context.collected_data
        })

        # Add any additional variables
        if additional_vars:
            variables.update(additional_vars)

        # Add default values for common variables
        variables.setdefault("grade_level_options", [
            "Pre-K", "K-2", "3-5", "Middle School", "High School", "College"
        ])
        variables.setdefault("subject_areas", [
            "Science", "Math", "Language Arts", "Social Studies",
            "Art", "Music", "Physical Education", "Computer Science"
        ])

        return variables

    def _validate_generated_content(self, content: str, template: PromptTemplate) -> Dict[str, bool]:
        """Validate the generated content against template rules"""
        results = {}

        # Check if all required variables are present
        for var in template.variables:
            results[f"variable_{var}_present"] = f"{{{{ {var} }}}}" not in content

        # Check content length
        results["appropriate_length"] = 50 <= len(content) <= 2000

        # Check for educational elements
        educational_keywords = ["learn", "teach", "understand", "skill", "knowledge", "education"]
        results["educational_focus"] = any(keyword in content.lower() for keyword in educational_keywords)

        # Check for engagement elements
        engagement_keywords = ["fun", "interactive", "game", "exciting", "engaging", "adventure"]
        results["engagement_focus"] = any(keyword in content.lower() for keyword in engagement_keywords)

        return results

    def _calculate_confidence_score(
        self,
        context: ConversationContext,
        template: PromptTemplate,
        validation_results: Dict[str, bool]
    ) -> float:
        """Calculate confidence score for the generated prompt"""

        # Base score from validation results
        validation_score = sum(validation_results.values()) / len(validation_results) if validation_results else 0.5

        # Context completeness score
        context_completeness = 0.0
        if context.user_profile:
            context_completeness += 0.2
        if context.requirements:
            context_completeness += 0.3
        if context.personalization:
            context_completeness += 0.3
        if context.uniqueness:
            context_completeness += 0.2

        # Template priority adjustment
        priority_adjustment = template.priority / 10.0

        # Calculate final confidence score
        confidence = (validation_score * 0.4 + context_completeness * 0.4 + priority_adjustment * 0.2)

        return min(max(confidence, 0.0), 1.0)

    def _generate_next_questions(self, template: PromptTemplate, context: ConversationContext) -> List[str]:
        """Generate follow-up questions based on template and context"""
        questions = []

        if template.stage == ConversationStage.DISCOVERY:
            questions.extend([
                "What grade level are you teaching?",
                "How many students will participate?",
                "What's the main learning objective?",
                "What subjects are you most interested in?"
            ])
        elif template.stage == ConversationStage.REQUIREMENTS:
            questions.extend([
                "How long should this experience be?",
                "What level of interactivity do you want?",
                "Are there any specific activities you'd like included?",
                "Do you have any accessibility requirements?"
            ])
        elif template.stage == ConversationStage.PERSONALIZATION:
            questions.extend([
                "What are your students currently interested in?",
                "Are there any local landmarks or references we could include?",
                "What makes your school or class unique?",
                "Are there any cultural elements to incorporate?"
            ])

        return questions[:3]  # Limit to 3 questions

    def _generate_suggested_actions(self, template: PromptTemplate, context: ConversationContext) -> List[str]:
        """Generate suggested actions based on template and context"""
        actions = []

        if template.stage == ConversationStage.GREETING:
            actions.extend([
                "Choose a content type to get started",
                "Browse example educational experiences",
                "Learn about available features"
            ])
        elif template.stage == ConversationStage.CONTENT_DESIGN:
            actions.extend([
                "Preview the design concept",
                "Adjust specific elements",
                "Add more personalization features"
            ])
        elif template.stage == ConversationStage.REVIEW:
            actions.extend([
                "Preview the complete experience",
                "Make final adjustments",
                "Deploy to your students"
            ])

        return actions[:3]  # Limit to 3 actions

    def _generate_agent_triggers(self, template: PromptTemplate, context: ConversationContext) -> List[str]:
        """Generate agent triggers based on template and context"""
        triggers = []

        for agent in template.agent_assignments:
            triggers.append(f"activate_{agent}")

        # Add stage-specific triggers
        if template.stage == ConversationStage.REQUIREMENTS:
            triggers.append("analyze_requirements")
        elif template.stage == ConversationStage.PERSONALIZATION:
            triggers.append("enhance_personalization")
        elif template.stage == ConversationStage.GENERATION:
            triggers.append("start_content_generation")

        return triggers

    def create_custom_template(
        self,
        name: str,
        stage: ConversationStage,
        template_text: str,
        variables: List[str] = None,
        **kwargs
    ) -> PromptTemplate:
        """Create a custom prompt template"""

        template = PromptTemplate(
            name=name,
            stage=stage,
            template_text=template_text,
            variables=variables or [],
            **kwargs
        )

        self.templates[template.id] = template
        return template

    def update_template(self, template_id: str, **updates) -> bool:
        """Update an existing template"""
        if template_id in self.templates:
            template = self.templates[template_id]
            for key, value in updates.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            template.updated_at = datetime.utcnow()
            return True
        return False

    def deactivate_template(self, template_id: str) -> bool:
        """Deactivate a template"""
        return self.update_template(template_id, is_active=False)

    def get_all_templates(self) -> List[PromptTemplate]:
        """Get all available templates"""
        return list(self.templates.values())

    def get_templates_by_priority(self, min_priority: int = 1) -> List[PromptTemplate]:
        """Get templates with minimum priority"""
        return [t for t in self.templates.values() if t.priority >= min_priority and t.is_active]



