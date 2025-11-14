"""Educational Intelligence Agents Suite

Specialized agents for educational content generation, curriculum alignment,
assessment design, and learning analytics in the Roblox educational platform.
"""

from .adaptive_learning_agent import AdaptiveLearningAgent, PersonalizationProfile
from .assessment_design_agent import (
    AssessmentDesignAgent,
    AssessmentItem,
    AssessmentType,
)
from .curriculum_alignment_agent import (
    AlignmentResult,
    CurriculumAlignmentAgent,
    CurriculumStandard,
)
from .educational_validation_agent import EducationalValidationAgent, ValidationResult
from .learning_analytics_agent import (
    LearningAnalyticsAgent,
    LearningPattern,
    StudentProgress,
)

__all__ = [
    # Curriculum Alignment
    "CurriculumAlignmentAgent",
    "CurriculumStandard",
    "AlignmentResult",
    # Learning Analytics
    "LearningAnalyticsAgent",
    "StudentProgress",
    "LearningPattern",
    # Assessment Design
    "AssessmentDesignAgent",
    "AssessmentType",
    "AssessmentItem",
    # Educational Validation
    "EducationalValidationAgent",
    "ValidationResult",
    # Adaptive Learning
    "AdaptiveLearningAgent",
    "PersonalizationProfile",
]
