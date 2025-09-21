"""
Content Validation System for ensuring quality and completeness of educational content
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import re
from enum import Enum

from .models import (
    ConversationContext, ContentRequirements, PersonalizationData,
    UniquenessEnhancement, ValidationResult, ContentType, GradeLevel,
    SubjectArea, EngagementLevel, UniquenessFactor
)

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues"""
    CRITICAL = "critical"
    WARNING = "warning"
    SUGGESTION = "suggestion"
    INFO = "info"


class ContentValidationSystem:
    """
    Validates educational content for quality, completeness, and effectiveness
    """

    def __init__(self):
        self.validation_rules = self._load_validation_rules()
        self.quality_metrics = self._load_quality_metrics()
        self.standards = self._load_educational_standards()

    def _load_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load validation rules for different content aspects"""
        return {
            "learning_objectives": {
                "required": True,
                "min_count": 1,
                "max_count": 10,
                "min_length": 10,
                "max_length": 200,
                "keywords": ["learn", "understand", "demonstrate", "apply", "analyze", "create"],
                "severity": ValidationSeverity.CRITICAL
            },
            "personalization": {
                "required": True,
                "min_elements": 2,
                "elements": ["student_names", "cultural_elements", "local_references", "interests"],
                "severity": ValidationSeverity.WARNING
            },
            "uniqueness": {
                "required": True,
                "min_factors": 1,
                "factors": ["custom_theme", "personalized_characters", "unique_mechanics", "creative_storytelling"],
                "severity": ValidationSeverity.WARNING
            },
            "engagement": {
                "required": True,
                "min_level": "moderate",
                "elements": ["interactive", "visual", "auditory", "kinesthetic"],
                "severity": ValidationSeverity.CRITICAL
            },
            "accessibility": {
                "required": True,
                "elements": ["multiple_formats", "clear_language", "appropriate_difficulty"],
                "severity": ValidationSeverity.CRITICAL
            },
            "technical_quality": {
                "required": True,
                "elements": ["performance", "compatibility", "security", "error_handling"],
                "severity": ValidationSeverity.WARNING
            }
        }

    def _load_quality_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Load quality metrics and scoring criteria"""
        return {
            "educational_value": {
                "weight": 0.3,
                "criteria": {
                    "learning_objectives_clarity": 0.25,
                    "curriculum_alignment": 0.25,
                    "pedagogical_effectiveness": 0.25,
                    "assessment_quality": 0.25
                }
            },
            "engagement": {
                "weight": 0.25,
                "criteria": {
                    "interactivity_level": 0.3,
                    "visual_appeal": 0.2,
                    "narrative_quality": 0.2,
                    "gamification_elements": 0.3
                }
            },
            "uniqueness": {
                "weight": 0.2,
                "criteria": {
                    "creative_elements": 0.3,
                    "personalization_depth": 0.3,
                    "innovative_approaches": 0.2,
                    "memorable_features": 0.2
                }
            },
            "technical_quality": {
                "weight": 0.15,
                "criteria": {
                    "performance": 0.3,
                    "usability": 0.3,
                    "accessibility": 0.2,
                    "reliability": 0.2
                }
            },
            "completeness": {
                "weight": 0.1,
                "criteria": {
                    "required_elements": 0.4,
                    "optional_elements": 0.3,
                    "documentation": 0.3
                }
            }
        }

    def _load_educational_standards(self) -> Dict[str, Dict[str, Any]]:
        """Load educational standards for different grade levels and subjects"""
        return {
            "common_core": {
                "elementary": {
                    "math": ["number_operations", "geometry", "measurement", "data_analysis"],
                    "language_arts": ["reading_comprehension", "writing", "speaking", "listening"]
                },
                "middle_school": {
                    "math": ["algebra", "geometry", "statistics", "probability"],
                    "language_arts": ["literature_analysis", "argumentative_writing", "research_skills"]
                },
                "high_school": {
                    "math": ["advanced_algebra", "trigonometry", "calculus", "statistics"],
                    "language_arts": ["literature_analysis", "research_papers", "presentation_skills"]
                }
            },
            "next_gen_science": {
                "elementary": ["physical_science", "life_science", "earth_science", "engineering"],
                "middle_school": ["matter_energy", "motion_stability", "ecosystems", "earth_systems"],
                "high_school": ["physics", "chemistry", "biology", "earth_space_science"]
            }
        }

    async def validate_conversation_context(
        self,
        context: ConversationContext
    ) -> ValidationResult:
        """Validate the entire conversation context"""

        validation_result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            suggestions=[],
            completeness_score=0.0,
            uniqueness_score=0.0,
            educational_value_score=0.0,
            engagement_score=0.0
        )

        # Validate requirements
        if context.requirements:
            req_validation = await self.validate_requirements(context.requirements)
            validation_result.errors.extend(req_validation["errors"])
            validation_result.warnings.extend(req_validation["warnings"])
            validation_result.suggestions.extend(req_validation["suggestions"])
            validation_result.educational_value_score = req_validation["educational_value_score"]

        # Validate personalization
        if context.personalization:
            pers_validation = await self.validate_personalization(context.personalization)
            validation_result.warnings.extend(pers_validation["warnings"])
            validation_result.suggestions.extend(pers_validation["suggestions"])
            validation_result.uniqueness_score = pers_validation["uniqueness_score"]

        # Validate uniqueness
        if context.uniqueness:
            uniq_validation = await self.validate_uniqueness(context.uniqueness)
            validation_result.warnings.extend(uniq_validation["warnings"])
            validation_result.suggestions.extend(uniq_validation["suggestions"])
            validation_result.uniqueness_score = max(validation_result.uniqueness_score, uniq_validation["uniqueness_score"])

        # Calculate overall completeness
        validation_result.completeness_score = await self._calculate_completeness_score(context)

        # Calculate engagement score
        validation_result.engagement_score = await self._calculate_engagement_score(context)

        # Determine overall validity
        validation_result.is_valid = len(validation_result.errors) == 0

        return validation_result

    async def validate_requirements(
        self,
        requirements: ContentRequirements
    ) -> Dict[str, Any]:
        """Validate content requirements"""

        result = {
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "educational_value_score": 0.0
        }

        # Validate learning objectives
        if not requirements.learning_objectives:
            result["errors"].append("Learning objectives are required")
        else:
            obj_validation = await self._validate_learning_objectives(requirements.learning_objectives)
            result["errors"].extend(obj_validation["errors"])
            result["warnings"].extend(obj_validation["warnings"])
            result["suggestions"].extend(obj_validation["suggestions"])
            result["educational_value_score"] += obj_validation["score"] * 0.4

        # Validate grade level appropriateness
        grade_validation = await self._validate_grade_level_appropriateness(requirements)
        result["warnings"].extend(grade_validation["warnings"])
        result["suggestions"].extend(grade_validation["suggestions"])
        result["educational_value_score"] += grade_validation["score"] * 0.3

        # Validate engagement level
        engagement_validation = await self._validate_engagement_level(requirements)
        result["warnings"].extend(engagement_validation["warnings"])
        result["suggestions"].extend(engagement_validation["suggestions"])
        result["educational_value_score"] += engagement_validation["score"] * 0.3

        return result

    async def validate_personalization(
        self,
        personalization: PersonalizationData
    ) -> Dict[str, Any]:
        """Validate personalization data"""

        result = {
            "warnings": [],
            "suggestions": [],
            "uniqueness_score": 0.0
        }

        # Check for student names
        if not personalization.student_names:
            result["warnings"].append("Student names would make content more personal")
        else:
            result["uniqueness_score"] += 0.2

        # Check for cultural elements
        if not personalization.cultural_elements:
            result["warnings"].append("Cultural elements would make content more inclusive")
        else:
            result["uniqueness_score"] += 0.2

        # Check for local references
        if not personalization.local_landmarks:
            result["suggestions"].append("Local references would make content more relevant")
        else:
            result["uniqueness_score"] += 0.2

        # Check for interests
        if not personalization.story_elements:
            result["suggestions"].append("Story elements would make content more engaging")
        else:
            result["uniqueness_score"] += 0.2

        # Check for school theme
        if not personalization.school_theme:
            result["suggestions"].append("School theme would make content more cohesive")
        else:
            result["uniqueness_score"] += 0.2

        return result

    async def validate_uniqueness(
        self,
        uniqueness: UniquenessEnhancement
    ) -> Dict[str, Any]:
        """Validate uniqueness enhancement data"""

        result = {
            "warnings": [],
            "suggestions": [],
            "uniqueness_score": 0.0
        }

        # Check for uniqueness factors
        if not uniqueness.factors:
            result["warnings"].append("No uniqueness factors specified")
        else:
            result["uniqueness_score"] += len(uniqueness.factors) * 0.15

        # Check for custom elements
        if not uniqueness.custom_elements:
            result["suggestions"].append("Custom elements would make content more unique")
        else:
            result["uniqueness_score"] += 0.2

        # Check for creative twists
        if not uniqueness.creative_twists:
            result["suggestions"].append("Creative twists would make content more memorable")
        else:
            result["uniqueness_score"] += 0.2

        # Check for personal touches
        if not uniqueness.personal_touches:
            result["suggestions"].append("Personal touches would make content more special")
        else:
            result["uniqueness_score"] += 0.15

        # Check for trending elements
        if not uniqueness.trending_elements:
            result["suggestions"].append("Trending elements would make content more current")
        else:
            result["uniqueness_score"] += 0.1

        return result

    async def _validate_learning_objectives(
        self,
        objectives: List[str]
    ) -> Dict[str, Any]:
        """Validate learning objectives"""

        result = {
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "score": 0.0
        }

        if not objectives:
            result["errors"].append("At least one learning objective is required")
            return result

        # Check objective quality
        for i, objective in enumerate(objectives):
            if len(objective.strip()) < 10:
                result["warnings"].append(f"Learning objective {i+1} is too short")
            elif len(objective.strip()) > 200:
                result["warnings"].append(f"Learning objective {i+1} is too long")

            # Check for action verbs
            action_verbs = ["learn", "understand", "demonstrate", "apply", "analyze", "create", "evaluate", "synthesize"]
            if not any(verb in objective.lower() for verb in action_verbs):
                result["suggestions"].append(f"Learning objective {i+1} should include an action verb")

            # Check for specificity
            if len(objective.split()) < 5:
                result["suggestions"].append(f"Learning objective {i+1} could be more specific")

        # Calculate score
        result["score"] = min(1.0, len(objectives) / 5.0)  # Normalize to 0-1

        return result

    async def _validate_grade_level_appropriateness(
        self,
        requirements: ContentRequirements
    ) -> Dict[str, Any]:
        """Validate grade level appropriateness"""

        result = {
            "warnings": [],
            "suggestions": [],
            "score": 0.0
        }

        grade_level = requirements.grade_level
        subject_area = requirements.subject_area

        # Check for appropriate complexity
        if grade_level in [GradeLevel.PRE_K, GradeLevel.KINDERGARTEN]:
            if requirements.engagement_level == EngagementLevel.IMMERSIVE:
                result["warnings"].append("Very young students may find immersive content overwhelming")
            result["score"] = 0.8
        elif grade_level in [GradeLevel.ELEMENTARY_1_2, GradeLevel.ELEMENTARY_3_5]:
            if requirements.engagement_level == EngagementLevel.PASSIVE:
                result["suggestions"].append("Elementary students benefit from more interactive content")
            result["score"] = 0.9
        elif grade_level in [GradeLevel.MIDDLE_SCHOOL, GradeLevel.HIGH_SCHOOL]:
            if requirements.engagement_level == EngagementLevel.PASSIVE:
                result["warnings"].append("Older students may find passive content unengaging")
            result["score"] = 0.95
        else:
            result["score"] = 1.0

        return result

    async def _validate_engagement_level(
        self,
        requirements: ContentRequirements
    ) -> Dict[str, Any]:
        """Validate engagement level appropriateness"""

        result = {
            "warnings": [],
            "suggestions": [],
            "score": 0.0
        }

        engagement_level = requirements.engagement_level

        if engagement_level == EngagementLevel.PASSIVE:
            result["warnings"].append("Passive content may not be engaging enough for most students")
            result["score"] = 0.5
        elif engagement_level == EngagementLevel.MODERATE:
            result["score"] = 0.8
        elif engagement_level == EngagementLevel.HIGH:
            result["score"] = 0.9
        elif engagement_level == EngagementLevel.IMMERSIVE:
            result["score"] = 1.0

        return result

    async def _calculate_completeness_score(
        self,
        context: ConversationContext
    ) -> float:
        """Calculate completeness score for the conversation context"""

        score = 0.0
        total_checks = 0

        # Check for basic requirements
        if context.user_profile:
            score += 0.1
        total_checks += 1

        if context.requirements:
            score += 0.3
            # Check requirements completeness
            if context.requirements.learning_objectives:
                score += 0.1
            if context.requirements.duration_minutes:
                score += 0.05
            if context.requirements.student_count:
                score += 0.05
        total_checks += 1

        if context.personalization:
            score += 0.2
            # Check personalization completeness
            if context.personalization.student_names:
                score += 0.05
            if context.personalization.cultural_elements:
                score += 0.05
        total_checks += 1

        if context.uniqueness:
            score += 0.2
            # Check uniqueness completeness
            if context.uniqueness.factors:
                score += 0.05
            if context.uniqueness.custom_elements:
                score += 0.05
        total_checks += 1

        # Check conversation progress
        if len(context.completed_stages) > 0:
            score += 0.2
        total_checks += 1

        return min(1.0, score)

    async def _calculate_engagement_score(
        self,
        context: ConversationContext
    ) -> float:
        """Calculate engagement score based on context"""

        score = 0.0

        # Base engagement from requirements
        if context.requirements:
            if context.requirements.engagement_level == EngagementLevel.PASSIVE:
                score = 0.3
            elif context.requirements.engagement_level == EngagementLevel.MODERATE:
                score = 0.6
            elif context.requirements.engagement_level == EngagementLevel.HIGH:
                score = 0.8
            elif context.requirements.engagement_level == EngagementLevel.IMMERSIVE:
                score = 1.0

        # Boost from personalization
        if context.personalization:
            if context.personalization.student_names:
                score += 0.1
            if context.personalization.story_elements:
                score += 0.1
            if context.personalization.cultural_elements:
                score += 0.05

        # Boost from uniqueness
        if context.uniqueness:
            if context.uniqueness.creative_twists:
                score += 0.1
            if context.uniqueness.custom_elements:
                score += 0.05

        return min(1.0, score)

    async def get_validation_summary(
        self,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Get a summary of validation results"""

        validation_result = await self.validate_conversation_context(context)

        summary = {
            "overall_status": "valid" if validation_result.is_valid else "needs_attention",
            "completeness_percentage": int(validation_result.completeness_score * 100),
            "quality_scores": {
                "educational_value": int(validation_result.educational_value_score * 100),
                "engagement": int(validation_result.engagement_score * 100),
                "uniqueness": int(validation_result.uniqueness_score * 100)
            },
            "critical_issues": len(validation_result.errors),
            "warnings": len(validation_result.warnings),
            "suggestions": len(validation_result.suggestions),
            "next_steps": []
        }

        # Generate next steps based on validation results
        if validation_result.errors:
            summary["next_steps"].append("Address critical issues before proceeding")

        if validation_result.completeness_score < 0.7:
            summary["next_steps"].append("Complete missing information to improve content quality")

        if validation_result.uniqueness_score < 0.5:
            summary["next_steps"].append("Add more unique and creative elements")

        if validation_result.engagement_score < 0.6:
            summary["next_steps"].append("Increase engagement level for better student participation")

        return summary









