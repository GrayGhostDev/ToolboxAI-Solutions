"""
Pydantic models for prompt template organization and user guidance
"""

from typing import Dict, List, Optional, Any, Literal, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class ConversationStage(str, Enum):
    """Stages of the educational content creation conversation"""
    GREETING = "greeting"
    DISCOVERY = "discovery"
    REQUIREMENTS = "requirements"
    PERSONALIZATION = "personalization"
    CONTENT_DESIGN = "content_design"
    UNIQUENESS_ENHANCEMENT = "uniqueness_enhancement"
    VALIDATION = "validation"
    GENERATION = "generation"
    REVIEW = "review"
    DEPLOYMENT = "deployment"


class FlowDecision(str, Enum):
    """Decision points in conversation flow"""
    CONTINUE = "continue"
    CLARIFY = "clarify"
    REDIRECT = "redirect"
    ESCALATE = "escalate"
    COMPLETE = "complete"
    RETRY = "retry"
    ABORT = "abort"


class ContentType(str, Enum):
    """Types of educational content that can be created"""
    LESSON = "lesson"
    QUIZ = "quiz"
    SIMULATION = "simulation"
    GAME = "game"
    INTERACTIVE_STORY = "interactive_story"
    VIRTUAL_FIELD_TRIP = "virtual_field_trip"
    LAB_EXPERIMENT = "lab_experiment"
    COLLABORATIVE_PROJECT = "collaborative_project"


class GradeLevel(str, Enum):
    """Educational grade levels"""
    PRE_K = "pre_k"
    KINDERGARTEN = "kindergarten"
    ELEMENTARY_1_2 = "elementary_1_2"
    ELEMENTARY_3_5 = "elementary_3_5"
    MIDDLE_SCHOOL = "middle_school"
    HIGH_SCHOOL = "high_school"
    COLLEGE = "college"
    ADULT_EDUCATION = "adult_education"


class SubjectArea(str, Enum):
    """Subject areas for educational content"""
    SCIENCE = "science"
    MATHEMATICS = "mathematics"
    LANGUAGE_ARTS = "language_arts"
    SOCIAL_STUDIES = "social_studies"
    HISTORY = "history"
    ART = "art"
    MUSIC = "music"
    PHYSICAL_EDUCATION = "physical_education"
    FOREIGN_LANGUAGE = "foreign_language"
    COMPUTER_SCIENCE = "computer_science"
    ENGINEERING = "engineering"
    HEALTH = "health"
    ENVIRONMENTAL_SCIENCE = "environmental_science"


class LearningStyle(str, Enum):
    """Learning styles to accommodate"""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"
    MULTIMODAL = "multimodal"


class EngagementLevel(str, Enum):
    """Levels of engagement and interactivity"""
    PASSIVE = "passive"
    MODERATE = "moderate"
    HIGH = "high"
    IMMERSIVE = "immersive"


class UniquenessFactor(str, Enum):
    """Factors that contribute to content uniqueness"""
    CUSTOM_THEME = "custom_theme"
    PERSONALIZED_CHARACTERS = "personalized_characters"
    UNIQUE_MECHANICS = "unique_mechanics"
    CULTURAL_SPECIFIC = "cultural_specific"
    LOCAL_REFERENCES = "local_references"
    STUDENT_INTERESTS = "student_interests"
    CURRENT_EVENTS = "current_events"
    CREATIVE_STORYTELLING = "creative_storytelling"


class UserProfile(BaseModel):
    """User profile for personalization"""
    user_id: str
    role: str
    experience_level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    preferred_learning_styles: List[LearningStyle] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    cultural_background: Optional[str] = None
    teaching_philosophy: Optional[str] = None
    technology_comfort: Literal["low", "medium", "high"] = "medium"
    time_available: Optional[int] = Field(None, description="Minutes available for content creation")


class ContentRequirements(BaseModel):
    """Detailed requirements for educational content"""
    content_type: ContentType
    subject_area: SubjectArea
    grade_level: GradeLevel
    learning_objectives: List[str] = Field(..., min_items=1)
    duration_minutes: Optional[int] = None
    student_count: Optional[int] = None
    prerequisites: List[str] = Field(default_factory=list)
    assessment_type: Optional[str] = None
    engagement_level: EngagementLevel = EngagementLevel.MODERATE
    accessibility_requirements: List[str] = Field(default_factory=list)
    technology_constraints: List[str] = Field(default_factory=list)


class PersonalizationData(BaseModel):
    """Data for personalizing content"""
    student_names: List[str] = Field(default_factory=list)
    local_landmarks: List[str] = Field(default_factory=list)
    cultural_elements: List[str] = Field(default_factory=list)
    current_trends: List[str] = Field(default_factory=list)
    school_theme: Optional[str] = None
    mascot: Optional[str] = None
    colors: List[str] = Field(default_factory=list)
    music_style: Optional[str] = None
    story_elements: List[str] = Field(default_factory=list)


class UniquenessEnhancement(BaseModel):
    """Enhancements to make content unique"""
    factors: List[UniquenessFactor] = Field(default_factory=list)
    custom_elements: Dict[str, Any] = Field(default_factory=dict)
    creative_twists: List[str] = Field(default_factory=list)
    personal_touches: List[str] = Field(default_factory=list)
    trending_elements: List[str] = Field(default_factory=list)


class PromptTemplate(BaseModel):
    """Individual prompt template"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    stage: ConversationStage
    content_type: Optional[ContentType] = None
    template_text: str
    variables: List[str] = Field(default_factory=list)
    validation_rules: Dict[str, Any] = Field(default_factory=dict)
    next_stages: List[ConversationStage] = Field(default_factory=list)
    agent_assignments: List[str] = Field(default_factory=list)
    priority: int = Field(default=1, ge=1, le=10)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationContext(BaseModel):
    """Context for the entire conversation"""
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_profile: UserProfile
    current_stage: ConversationStage = ConversationStage.GREETING
    completed_stages: List[ConversationStage] = Field(default_factory=list)
    requirements: Optional[ContentRequirements] = None
    personalization: Optional[PersonalizationData] = None
    uniqueness: Optional[UniquenessEnhancement] = None
    collected_data: Dict[str, Any] = Field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    agent_assignments: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PromptResponse(BaseModel):
    """Response from a prompt template"""
    template_id: str
    generated_text: str
    variables_used: Dict[str, Any]
    next_questions: List[str] = Field(default_factory=list)
    suggested_actions: List[str] = Field(default_factory=list)
    agent_triggers: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    validation_results: Dict[str, bool] = Field(default_factory=dict)


class WorkflowStep(BaseModel):
    """Individual step in the content creation workflow"""
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    agent_type: str
    required_data: List[str] = Field(default_factory=list)
    output_data: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    estimated_duration: Optional[int] = Field(None, description="Minutes")
    priority: int = Field(default=1, ge=1, le=10)
    is_parallel: bool = False


class ContentGenerationPlan(BaseModel):
    """Complete plan for content generation"""
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_context: ConversationContext
    workflow_steps: List[WorkflowStep]
    estimated_total_time: int
    required_agents: List[str]
    expected_outputs: List[str]
    quality_metrics: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ValidationResult(BaseModel):
    """Result of content validation"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    completeness_score: float = Field(ge=0.0, le=1.0)
    uniqueness_score: float = Field(ge=0.0, le=1.0)
    educational_value_score: float = Field(ge=0.0, le=1.0)
    engagement_score: float = Field(ge=0.0, le=1.0)


class AgentTrigger(BaseModel):
    """Trigger for agent activation"""
    agent_name: str
    trigger_type: Literal["data_ready", "stage_complete", "user_request", "error"]
    trigger_data: Dict[str, Any]
    priority: int = Field(default=1, ge=1, le=10)
    created_at: datetime = Field(default_factory=datetime.utcnow)







