"""
User Guidance System for providing intelligent assistance during content creation
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import re
from enum import Enum

from .models import (
    ConversationContext, UserProfile, ContentRequirements, PersonalizationData,
    UniquenessEnhancement, ContentType, GradeLevel, SubjectArea, LearningStyle,
    EngagementLevel, UniquenessFactor
)

logger = logging.getLogger(__name__)


class GuidanceType(str, Enum):
    """Types of guidance that can be provided"""
    SUGGESTION = "suggestion"
    CLARIFICATION = "clarification"
    EXAMPLES = "examples"
    BEST_PRACTICES = "best_practices"
    WARNING = "warning"
    ENCOURAGEMENT = "encouragement"


class UserGuidanceSystem:
    """
    Provides intelligent guidance and suggestions to users during the
    educational content creation process.
    """

    def __init__(self):
        self.guidance_templates = self._load_guidance_templates()
        self.best_practices = self._load_best_practices()
        self.example_library = self._load_example_library()
        self.validation_rules = self._load_validation_rules()

    def _load_guidance_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load guidance templates for different scenarios"""
        return {
            "discovery_guidance": {
                "suggestions": [
                    "Consider what makes your students unique - their interests, cultural background, and learning styles",
                    "Think about current trends or topics that would excite your students",
                    "Consider how this content could connect to real-world applications"
                ],
                "examples": [
                    "A science lesson about space exploration could include references to current Mars missions",
                    "A history lesson could incorporate local landmarks or community events",
                    "A math lesson could use examples from popular games or sports your students enjoy"
                ],
                "questions": [
                    "What topics do your students get most excited about?",
                    "Are there any current events or trends they're following?",
                    "What makes your school or community unique?"
                ]
            },
            "requirements_guidance": {
                "suggestions": [
                    "Be specific about learning objectives - what exactly should students know or be able to do?",
                    "Consider different learning styles and how to accommodate them",
                    "Think about assessment methods that would be both effective and engaging"
                ],
                "examples": [
                    "Instead of 'learn about photosynthesis', try 'students will be able to explain how plants convert sunlight into energy and demonstrate this process in a virtual lab'",
                    "Consider including visual, auditory, and hands-on elements to reach all learners",
                    "Use interactive quizzes, peer collaboration, or creative projects as assessment methods"
                ],
                "questions": [
                    "How will you know if students have achieved the learning objectives?",
                    "What level of interactivity would work best for your students?",
                    "Are there any accessibility needs to consider?"
                ]
            },
            "personalization_guidance": {
                "suggestions": [
                    "Include elements that reflect your students' cultural backgrounds and interests",
                    "Use local references and landmarks to make content more relevant",
                    "Incorporate student names, school themes, or community traditions"
                ],
                "examples": [
                    "A math lesson about fractions could use examples from a local pizza place your students know",
                    "Include characters that represent the diversity of your classroom",
                    "Reference local sports teams, events, or landmarks in word problems or scenarios"
                ],
                "questions": [
                    "What local places or events are important to your students?",
                    "How can we celebrate the diversity in your classroom?",
                    "What school traditions or themes could we incorporate?"
                ]
            },
            "uniqueness_guidance": {
                "suggestions": [
                    "Add unexpected twists or creative elements that surprise students",
                    "Include trending elements or current pop culture references",
                    "Create custom characters, stories, or mechanics that are unique to your class"
                ],
                "examples": [
                    "Turn a history lesson into a time-travel adventure where students solve historical mysteries",
                    "Create a science simulation where students are astronauts exploring a new planet",
                    "Design a math game where students are treasure hunters solving puzzles to find hidden treasure"
                ],
                "questions": [
                    "What would make this content memorable and exciting for your students?",
                    "Are there any creative twists or unexpected elements we could add?",
                    "How can we make this feel like a game or adventure rather than just a lesson?"
                ]
            },
            "content_design_guidance": {
                "suggestions": [
                    "Create a clear narrative or story that guides students through the content",
                    "Design interactive elements that reinforce learning objectives",
                    "Include multiple pathways or choices to accommodate different learning preferences"
                ],
                "examples": [
                    "Design a virtual museum where students explore different exhibits to learn about ancient civilizations",
                    "Create a space station where students conduct experiments to learn about physics",
                    "Build a medieval castle where students solve puzzles to learn about history and literature"
                ],
                "questions": [
                    "What kind of environment would best support your learning objectives?",
                    "How can we make the content feel immersive and engaging?",
                    "What interactive elements would help students learn most effectively?"
                ]
            }
        }

    def _load_best_practices(self) -> Dict[str, List[str]]:
        """Load best practices for educational content creation"""
        return {
            "engagement": [
                "Use gamification elements like points, badges, and leaderboards",
                "Include immediate feedback and rewards for student actions",
                "Create challenges that are appropriately difficult but achievable",
                "Use storytelling and narrative to make content more compelling",
                "Include social elements like collaboration and competition"
            ],
            "accessibility": [
                "Provide multiple ways to access information (visual, auditory, text)",
                "Use clear, simple language appropriate for the grade level",
                "Include options for different learning speeds and styles",
                "Ensure content works with assistive technologies",
                "Provide alternative formats for different abilities"
            ],
            "educational_effectiveness": [
                "Align content with specific learning standards and objectives",
                "Use research-based instructional strategies",
                "Include formative assessment throughout the experience",
                "Provide opportunities for reflection and metacognition",
                "Connect new learning to prior knowledge and real-world applications"
            ],
            "uniqueness": [
                "Create custom characters, stories, or themes unique to your class",
                "Include local references and cultural elements",
                "Use current trends and pop culture references appropriately",
                "Add unexpected twists or creative elements",
                "Incorporate student interests and hobbies"
            ],
            "technical_quality": [
                "Ensure smooth performance and fast loading times",
                "Test on different devices and browsers",
                "Include error handling and recovery mechanisms",
                "Use high-quality graphics and audio",
                "Implement proper security and privacy measures"
            ]
        }

    def _load_example_library(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load examples of successful educational content"""
        return {
            "science_lessons": [
                {
                    "title": "Virtual Chemistry Lab",
                    "description": "Students conduct virtual experiments to learn about chemical reactions",
                    "grade_level": "high_school",
                    "unique_elements": ["Realistic lab equipment", "Safety protocols", "Real-time data analysis"],
                    "engagement_features": ["Interactive experiments", "Achievement system", "Peer collaboration"]
                },
                {
                    "title": "Space Exploration Mission",
                    "description": "Students become astronauts exploring different planets and moons",
                    "grade_level": "middle_school",
                    "unique_elements": ["Custom spacecraft", "Real NASA data", "Mission planning"],
                    "engagement_features": ["Role-playing", "Problem-solving challenges", "Team missions"]
                }
            ],
            "history_lessons": [
                {
                    "title": "Time Travel Adventure",
                    "description": "Students travel through different historical periods to solve mysteries",
                    "grade_level": "elementary_3_5",
                    "unique_elements": ["Historical characters", "Period-accurate settings", "Mystery solving"],
                    "engagement_features": ["Adventure game mechanics", "Historical artifacts", "Character interactions"]
                }
            ],
            "math_lessons": [
                {
                    "title": "Treasure Hunt Math",
                    "description": "Students solve math problems to find hidden treasure",
                    "grade_level": "elementary_1_2",
                    "unique_elements": ["Pirate theme", "Custom treasure maps", "Student names in puzzles"],
                    "engagement_features": ["Adventure theme", "Progressive difficulty", "Reward system"]
                }
            ]
        }

    def _load_validation_rules(self) -> Dict[str, List[str]]:
        """Load validation rules for content quality"""
        return {
            "learning_objectives": [
                "Must be specific and measurable",
                "Should align with grade-level standards",
                "Must be achievable within the time frame",
                "Should include both knowledge and skills"
            ],
            "engagement_elements": [
                "Must include interactive components",
                "Should provide immediate feedback",
                "Must be age-appropriate",
                "Should encourage active participation"
            ],
            "personalization": [
                "Must include student-specific elements",
                "Should reflect cultural diversity",
                "Must include local or relevant references",
                "Should incorporate student interests"
            ],
            "uniqueness": [
                "Must have custom elements not found in standard content",
                "Should include creative or innovative approaches",
                "Must feel special and memorable",
                "Should stand out from typical educational content"
            ]
        }

    async def provide_guidance(
        self,
        context: ConversationContext,
        guidance_type: GuidanceType,
        specific_area: Optional[str] = None
    ) -> Dict[str, Any]:
        """Provide guidance based on conversation context and type"""

        current_stage = context.current_stage

        # Get guidance template for current stage
        stage_key = f"{current_stage.value}_guidance"
        guidance_data = self.guidance_templates.get(stage_key, {})

        # Generate personalized guidance
        guidance = {
            "type": guidance_type.value,
            "stage": current_stage.value,
            "timestamp": datetime.utcnow().isoformat(),
            "suggestions": [],
            "examples": [],
            "questions": [],
            "best_practices": [],
            "warnings": [],
            "encouragement": []
        }

        # Add suggestions
        if guidance_data.get("suggestions"):
            guidance["suggestions"] = self._personalize_suggestions(
                guidance_data["suggestions"], context
            )

        # Add examples
        if guidance_data.get("examples"):
            guidance["examples"] = self._personalize_examples(
                guidance_data["examples"], context
            )

        # Add questions
        if guidance_data.get("questions"):
            guidance["questions"] = guidance_data["questions"]

        # Add best practices
        if specific_area:
            guidance["best_practices"] = self.best_practices.get(specific_area, [])

        # Add warnings if needed
        warnings = await self._check_for_warnings(context)
        if warnings:
            guidance["warnings"] = warnings

        # Add encouragement
        encouragement = await self._generate_encouragement(context)
        if encouragement:
            guidance["encouragement"] = encouragement

        return guidance

    def _personalize_suggestions(
        self,
        suggestions: List[str],
        context: ConversationContext
    ) -> List[str]:
        """Personalize suggestions based on user context"""

        personalized = []

        for suggestion in suggestions:
            # Replace placeholders with actual data
            personalized_suggestion = suggestion

            if context.user_profile:
                if "{{user_role}}" in suggestion:
                    personalized_suggestion = personalized_suggestion.replace(
                        "{{user_role}}", context.user_profile.role
                    )

                if "{{experience_level}}" in suggestion:
                    personalized_suggestion = personalized_suggestion.replace(
                        "{{experience_level}}", context.user_profile.experience_level
                    )

            if context.requirements:
                if "{{content_type}}" in suggestion:
                    personalized_suggestion = personalized_suggestion.replace(
                        "{{content_type}}", context.requirements.content_type.value
                    )

                if "{{grade_level}}" in suggestion:
                    personalized_suggestion = personalized_suggestion.replace(
                        "{{grade_level}}", context.requirements.grade_level.value
                    )

            personalized.append(personalized_suggestion)

        return personalized

    def _personalize_examples(
        self,
        examples: List[str],
        context: ConversationContext
    ) -> List[str]:
        """Personalize examples based on user context"""

        personalized = []

        for example in examples:
            personalized_example = example

            # Add personalization based on collected data
            if context.personalization:
                if "{{student_names}}" in example and context.personalization.student_names:
                    name = context.personalization.student_names[0]
                    personalized_example = personalized_example.replace(
                        "{{student_names}}", name
                    )

                if "{{local_landmarks}}" in example and context.personalization.local_landmarks:
                    landmark = context.personalization.local_landmarks[0]
                    personalized_example = personalized_example.replace(
                        "{{local_landmarks}}", landmark
                    )

            personalized.append(personalized_example)

        return personalized

    async def _check_for_warnings(self, context: ConversationContext) -> List[str]:
        """Check for potential issues and generate warnings"""

        warnings = []

        # Check for missing required data
        if context.current_stage.value == "requirements" and not context.requirements:
            warnings.append("Learning objectives are required to proceed with content creation")

        if context.current_stage.value == "personalization" and not context.personalization:
            warnings.append("Personalization data will help create more engaging content")

        # Check for potential issues
        if context.requirements:
            if context.requirements.duration_minutes and context.requirements.duration_minutes > 60:
                warnings.append("Longer sessions may require breaks or multiple parts")

            if context.requirements.student_count and context.requirements.student_count > 30:
                warnings.append("Large class sizes may require additional management features")

        # Check for quality concerns
        if context.collected_data:
            if len(context.collected_data) < 3:
                warnings.append("More detailed information will help create better content")

        return warnings

    async def _generate_encouragement(self, context: ConversationContext) -> List[str]:
        """Generate encouraging messages based on progress"""

        encouragement = []

        # Progress-based encouragement
        completed_stages = len(context.completed_stages)
        total_stages = len(context.current_stage.__class__)

        if completed_stages == 0:
            encouragement.append("Great start! You're taking the first step toward creating amazing educational content!")
        elif completed_stages < total_stages / 2:
            encouragement.append("You're making excellent progress! The foundation you're building will make your content truly special.")
        elif completed_stages < total_stages * 0.8:
            encouragement.append("You're almost there! The details you're providing will make this content unforgettable for your students.")
        else:
            encouragement.append("Fantastic work! You've created a comprehensive plan that will result in outstanding educational content!")

        # Quality-based encouragement
        if context.personalization and context.personalization.student_names:
            encouragement.append(f"Your students {', '.join(context.personalization.student_names[:3])} are going to love this personalized experience!")

        if context.uniqueness and context.uniqueness.creative_twists:
            encouragement.append("The creative elements you're adding will make this content truly unique and memorable!")

        return encouragement

    async def get_examples_for_content_type(
        self,
        content_type: ContentType,
        grade_level: Optional[GradeLevel] = None
    ) -> List[Dict[str, Any]]:
        """Get relevant examples for a specific content type and grade level"""

        # Filter examples by content type and grade level
        examples = []

        for category, example_list in self.example_library.items():
            for example in example_list:
                if grade_level and example.get("grade_level") != grade_level.value:
                    continue

                # Add to examples if it matches the content type
                if self._example_matches_content_type(example, content_type):
                    examples.append(example)

        return examples[:5]  # Limit to 5 examples

    def _example_matches_content_type(
        self,
        example: Dict[str, Any],
        content_type: ContentType
    ) -> bool:
        """Check if an example matches the specified content type"""

        # Simple matching based on title keywords
        title = example.get("title", "").lower()

        if content_type == ContentType.LESSON:
            return any(keyword in title for keyword in ["lesson", "learn", "teach", "study"])
        elif content_type == ContentType.QUIZ:
            return any(keyword in title for keyword in ["quiz", "test", "assessment", "challenge"])
        elif content_type == ContentType.SIMULATION:
            return any(keyword in title for keyword in ["simulation", "virtual", "lab", "experiment"])
        elif content_type == ContentType.GAME:
            return any(keyword in title for keyword in ["game", "adventure", "mission", "hunt"])

        return True  # Default to include all examples

    async def validate_content_requirements(
        self,
        requirements: ContentRequirements
    ) -> Dict[str, Any]:
        """Validate content requirements and provide feedback"""

        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "completeness_score": 0.0
        }

        # Check learning objectives
        if not requirements.learning_objectives:
            validation_result["errors"].append("Learning objectives are required")
            validation_result["is_valid"] = False
        else:
            # Check if objectives are specific enough
            for obj in requirements.learning_objectives:
                if len(obj.split()) < 5:  # Simple check for specificity
                    validation_result["warnings"].append(f"Learning objective '{obj}' could be more specific")

        # Check duration
        if requirements.duration_minutes:
            if requirements.duration_minutes < 5:
                validation_result["warnings"].append("Very short duration may limit learning effectiveness")
            elif requirements.duration_minutes > 120:
                validation_result["warnings"].append("Very long duration may require breaks or multiple sessions")

        # Check student count
        if requirements.student_count:
            if requirements.student_count > 50:
                validation_result["warnings"].append("Large class size may require additional management features")

        # Calculate completeness score
        required_fields = ["content_type", "subject_area", "grade_level", "learning_objectives"]
        completed_fields = sum(1 for field in required_fields if getattr(requirements, field, None))
        validation_result["completeness_score"] = completed_fields / len(required_fields)

        return validation_result

    async def suggest_improvements(
        self,
        context: ConversationContext
    ) -> List[str]:
        """Suggest improvements based on current context"""

        suggestions = []

        # Check for missing personalization
        if not context.personalization:
            suggestions.append("Add personalization data to make content more engaging for your students")

        # Check for missing uniqueness elements
        if not context.uniqueness:
            suggestions.append("Consider adding unique elements to make your content stand out")

        # Check for incomplete requirements
        if context.requirements:
            if not context.requirements.duration_minutes:
                suggestions.append("Specify duration to help with content planning")

            if not context.requirements.student_count:
                suggestions.append("Specify class size to optimize for your students")

        # Check for engagement level
        if context.requirements and context.requirements.engagement_level == EngagementLevel.PASSIVE:
            suggestions.append("Consider increasing engagement level for better student participation")

        return suggestions

    async def get_next_steps(
        self,
        context: ConversationContext
    ) -> List[str]:
        """Get suggested next steps based on current context"""

        next_steps = []
        current_stage = context.current_stage

        if current_stage == ConversationStage.GREETING:
            next_steps.append("Choose the type of educational content you want to create")
            next_steps.append("Specify the grade level and subject area")

        elif current_stage == ConversationStage.DISCOVERY:
            next_steps.append("Define specific learning objectives")
            next_steps.append("Specify the duration and class size")

        elif current_stage == ConversationStage.REQUIREMENTS:
            next_steps.append("Add personalization elements for your students")
            next_steps.append("Consider cultural and local references")

        elif current_stage == ConversationStage.PERSONALIZATION:
            next_steps.append("Design the content structure and flow")
            next_steps.append("Add unique and creative elements")

        elif current_stage == ConversationStage.CONTENT_DESIGN:
            next_steps.append("Enhance uniqueness and creativity")
            next_steps.append("Validate content quality")

        elif current_stage == ConversationStage.UNIQUENESS_ENHANCEMENT:
            next_steps.append("Review and validate the design")
            next_steps.append("Start content generation")

        elif current_stage == ConversationStage.VALIDATION:
            next_steps.append("Generate the final content")
            next_steps.append("Review the completed experience")

        elif current_stage == ConversationStage.GENERATION:
            next_steps.append("Review the generated content")
            next_steps.append("Make any final adjustments")

        elif current_stage == ConversationStage.REVIEW:
            next_steps.append("Deploy to your students")
            next_steps.append("Set up monitoring and feedback collection")

        return next_steps
