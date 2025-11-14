"""
Pydantic Data Models for ToolboxAI Roblox Environment

Defines all data structures used throughout the application including:
- Content generation requests and responses
- Quiz and assessment models
- Terrain configuration models
- Educational context models
- API response models
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

try:
    # Prefer the canonical enum definition from the Roblox schemas module
    from apps.backend.schemas.roblox import ConversationStage as _ConversationStage

    ConversationStage = _ConversationStage
except Exception:  # pragma: no cover - fallback for bootstrap/import cycles

    class ConversationStage(str, Enum):
        """Conversation flow stages (fallback definition)."""

        GREETING = "greeting"
        DISCOVERY = "discovery"
        REQUIREMENTS = "requirements"
        PERSONALIZATION = "personalization"
        DESIGN = "design"
        UNIQUENESS = "uniqueness"
        VALIDATION = "validation"
        GENERATION = "generation"
        COMPLETE = "complete"


# Enums for type safety
class SubjectType(str, Enum):
    """Supported educational subjects"""

    MATHEMATICS = "Mathematics"
    SCIENCE = "Science"
    HISTORY = "History"
    ENGLISH = "English"
    ART = "Art"
    GEOGRAPHY = "Geography"
    COMPUTER_SCIENCE = "Computer Science"
    PHYSICS = "Physics"
    CHEMISTRY = "Chemistry"
    BIOLOGY = "Biology"


class DifficultyLevel(str, Enum):
    """Quiz and content difficulty levels"""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class EnvironmentType(str, Enum):
    """Types of Roblox environments"""

    CLASSROOM = "classroom"
    LABORATORY = "laboratory"
    OUTDOOR = "outdoor"
    HISTORICAL = "historical"
    FUTURISTIC = "futuristic"
    UNDERWATER = "underwater"
    SPACE_STATION = "space_station"
    FANTASY = "fantasy"
    CUSTOM = "custom"


class TerrainSize(str, Enum):
    """Terrain size options"""

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    XLARGE = "xlarge"


class QuizType(str, Enum):
    """Types of quiz questions"""

    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    FILL_BLANK = "fill_blank"
    MATCHING = "matching"
    ORDERING = "ordering"


class ActivityType(str, Enum):
    """Types of educational activities"""

    LESSON = "lesson"
    QUIZ = "quiz"
    EXPERIMENT = "experiment"
    EXPLORATION = "exploration"
    INTERACTIVE = "interactive"
    GAME = "game"
    SIMULATION = "simulation"
    ASSESSMENT = "assessment"


# Base Models
class BaseResponse(BaseModel):
    """Base response model for all API endpoints"""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable message")
    data: dict[str, Any] | None = Field(default=None, description="Optional response data")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response timestamp",
    )
    request_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique request identifier",
    )

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat() if v else None})


class PaginationModel(BaseModel):
    """Pagination information for list responses"""

    page: int = Field(1, ge=1, description="Current page number")
    per_page: int = Field(10, ge=1, le=100, description="Items per page")
    total: int = Field(0, ge=0, description="Total number of items")
    pages: int = Field(0, ge=0, description="Total number of pages")


# Educational Content Models
class LearningObjective(BaseModel):
    """Individual learning objective"""

    id: str | None = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique identifier"
    )
    title: str = Field(..., min_length=1, max_length=200, description="Objective title")
    description: str | None = Field(None, max_length=1000, description="Detailed description")
    bloom_level: str | None = Field(None, description="Bloom's taxonomy level")
    measurable: bool = Field(True, description="Whether the objective is measurable")


class ContentRequest(BaseModel):
    """Request model for generating educational content"""

    subject: SubjectType = Field(..., description="Educational subject")
    grade_level: int = Field(..., ge=1, le=12, description="Grade level (K-12)")
    learning_objectives: list[LearningObjective] = Field(
        ..., min_items=1, max_items=10, description="Learning objectives"
    )
    environment_type: EnvironmentType = Field(
        default=EnvironmentType.CLASSROOM, description="Type of Roblox environment"
    )
    terrain_size: TerrainSize = Field(default=TerrainSize.MEDIUM, description="Size of the terrain")
    include_quiz: bool = Field(default=True, description="Whether to include a quiz")
    difficulty_level: DifficultyLevel = Field(
        default=DifficultyLevel.MEDIUM, description="Content difficulty"
    )
    duration_minutes: int = Field(
        30, ge=5, le=180, description="Expected activity duration in minutes"
    )
    max_students: int = Field(30, ge=1, le=100, description="Maximum number of students")
    accessibility_features: bool = Field(False, description="Include accessibility features")
    multilingual: bool = Field(False, description="Support multiple languages")
    custom_requirements: str | None = Field(
        None, max_length=1000, description="Additional custom requirements"
    )

    @field_validator("learning_objectives")
    def validate_objectives(cls, v):
        if not v:
            raise ValueError("At least one learning objective is required")
        return v


class GeneratedScript(BaseModel):
    """Generated Lua script for Roblox"""

    name: str = Field(..., description="Script name")
    content: str = Field(..., description="Lua script content")
    script_type: Literal["server", "client", "module"] = Field(..., description="Type of script")
    dependencies: list[str] = Field(default_factory=list, description="Required dependencies")
    description: str | None = Field(None, description="Script description")


class TerrainConfiguration(BaseModel):
    """Terrain generation configuration"""

    material: str = Field("Grass", description="Primary terrain material")
    size: TerrainSize = Field(TerrainSize.MEDIUM, description="Terrain size")
    features: list[str] = Field(
        default_factory=list, description="Terrain features (hills, water, etc.)"
    )
    biome: str = Field("temperate", description="Terrain biome")
    elevation_map: dict[str, Any] | None = Field(None, description="Custom elevation data")


class GameMechanics(BaseModel):
    """Game mechanics configuration"""

    movement_enabled: bool = Field(True, description="Allow player movement")
    chat_enabled: bool = Field(True, description="Enable chat system")
    collision_detection: bool = Field(True, description="Enable collision detection")
    gravity_enabled: bool = Field(True, description="Enable gravity")
    respawn_enabled: bool = Field(True, description="Enable player respawning")
    team_mode: bool = Field(False, description="Enable team-based activities")


class ContentResponse(BaseResponse):
    """Response model for content generation"""

    content: dict[str, Any] = Field(..., description="Generated content data")
    scripts: list[GeneratedScript] = Field(
        default_factory=list, description="Generated Lua scripts"
    )
    terrain: TerrainConfiguration | None = Field(None, description="Terrain configuration")
    game_mechanics: GameMechanics | None = Field(None, description="Game mechanics settings")
    estimated_build_time: int = Field(0, description="Estimated build time in minutes")
    resource_requirements: dict[str, int] = Field(
        default_factory=dict, description="Resource requirements"
    )
    content_id: str | None = Field(None, description="Unique identifier for the generated content")


# Quiz Models
class QuizOption(BaseModel):
    """Quiz question option"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Option ID")
    text: str = Field(..., min_length=1, max_length=500, description="Option text")
    is_correct: bool = Field(False, description="Whether this option is correct")
    explanation: str | None = Field(
        None, max_length=1000, description="Explanation for this option"
    )


class QuizQuestion(BaseModel):
    """Individual quiz question"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Question ID")
    question_type: QuizType = Field(..., description="Type of question")
    question_text: str = Field(..., min_length=1, max_length=1000, description="Question text")
    options: list[QuizOption] = Field(default_factory=list, description="Answer options")
    correct_answer: str | None = Field(None, description="Correct answer for non-multiple choice")
    difficulty: DifficultyLevel = Field(DifficultyLevel.MEDIUM, description="Question difficulty")
    points: int = Field(1, ge=1, le=10, description="Points for correct answer")
    time_limit: int | None = Field(None, ge=10, le=600, description="Time limit in seconds")
    hint: str | None = Field(None, max_length=500, description="Hint for the question")
    explanation: str | None = Field(
        None, max_length=1000, description="Explanation of correct answer"
    )

    @field_validator("options")
    def validate_options(cls, v, info):
        question_type = info.data.get("question_type")
        if question_type == QuizType.MULTIPLE_CHOICE and len(v) < 2:
            raise ValueError("Multiple choice questions need at least 2 options")
        return v


class Quiz(BaseModel):
    """Complete quiz model"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Quiz ID")
    title: str = Field(..., min_length=1, max_length=200, description="Quiz title")
    description: str | None = Field(None, max_length=1000, description="Quiz description")
    subject: SubjectType = Field(..., description="Quiz subject")
    grade_level: int = Field(..., ge=1, le=12, description="Target grade level")
    questions: list[QuizQuestion] = Field(
        ..., min_items=1, max_items=50, description="Quiz questions"
    )
    time_limit: int | None = Field(
        None, ge=60, le=3600, description="Total quiz time limit in seconds"
    )
    passing_score: int = Field(70, ge=0, le=100, description="Passing score percentage")
    max_attempts: int = Field(3, ge=1, le=10, description="Maximum attempts allowed")
    shuffle_questions: bool = Field(True, description="Randomize question order")
    shuffle_options: bool = Field(True, description="Randomize option order")
    show_results: bool = Field(True, description="Show results immediately")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp",
    )


class QuizResponse(BaseResponse):
    """Response model for quiz generation"""

    quiz: Quiz = Field(..., description="Generated quiz")
    lua_script: str | None = Field(None, description="Lua script for Roblox implementation")
    ui_elements: list[dict[str, Any]] = Field(
        default_factory=list, description="UI element configurations"
    )


# User and Session Models
class User(BaseModel):
    """User model"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="User ID")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: str = Field(..., description="Email address")
    role: Literal["student", "teacher", "admin", "parent"] = Field(
        "student", description="User role"
    )
    grade_level: int | None = Field(None, ge=1, le=12, description="Grade level (for students)")
    subjects: list[SubjectType] = Field(
        default_factory=list, description="Subjects of interest/teaching"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Account creation timestamp",
    )
    last_active: datetime | None = Field(None, description="Last activity timestamp")

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat() if v else None})


class Session(BaseModel):
    """User session model"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Session ID")
    user_id: str = Field(..., description="User ID")
    roblox_user_id: str | None = Field(None, description="Roblox user ID")
    studio_id: str | None = Field(None, description="Roblox Studio ID")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Session creation timestamp",
    )
    expires_at: datetime = Field(..., description="Session expiration timestamp")
    active: bool = Field(True, description="Whether session is active")


# Plugin Models
class PluginRegistration(BaseModel):
    """Roblox Studio plugin registration"""

    plugin_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Plugin instance ID"
    )
    studio_id: str = Field(..., description="Roblox Studio user ID")
    port: int = Field(64989, description="Plugin communication port")
    version: str = Field("1.0.0", description="Plugin version")
    registered_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Registration timestamp",
    )
    last_heartbeat: datetime | None = Field(None, description="Last heartbeat timestamp")
    active: bool = Field(True, description="Whether plugin is active")


class PluginMessage(BaseModel):
    """Message between server and plugin"""

    type: Literal["command", "response", "event", "heartbeat"] = Field(
        ..., description="Message type"
    )
    payload: dict[str, Any] = Field(default_factory=dict, description="Message payload")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Message timestamp",
    )
    request_id: str | None = Field(None, description="Request ID for response tracking")


# LMS Integration Models
class LMSCourse(BaseModel):
    """LMS course information"""

    id: str = Field(..., description="Course ID")
    title: str = Field(..., description="Course title")
    description: str | None = Field(None, description="Course description")
    subject: SubjectType | None = Field(None, description="Course subject")
    grade_level: int | None = Field(None, description="Grade level")
    instructor: str = Field(..., description="Instructor name")
    platform: Literal["schoology", "canvas", "blackboard", "moodle"] = Field(
        ..., description="LMS platform"
    )
    enrollment_count: int = Field(0, description="Number of enrolled students")


class LMSAssignment(BaseModel):
    """LMS assignment information"""

    id: str = Field(..., description="Assignment ID")
    course_id: str = Field(..., description="Course ID")
    title: str = Field(..., description="Assignment title")
    description: str | None = Field(None, description="Assignment description")
    due_date: datetime | None = Field(None, description="Due date")
    points_possible: int | None = Field(None, description="Maximum points")
    submission_types: list[str] = Field(
        default_factory=list, description="Allowed submission types"
    )


# Analytics and Monitoring Models
class UsageMetrics(BaseModel):
    """Usage metrics for monitoring"""

    endpoint: str = Field(..., description="API endpoint")
    method: str = Field(..., description="HTTP method")
    response_time: float = Field(..., description="Response time in seconds")
    status_code: int = Field(..., description="HTTP status code")
    user_id: str | None = Field(None, description="User ID if authenticated")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Request timestamp",
    )


class HealthCheck(BaseModel):
    """Health check response model"""

    status: Literal["healthy", "unhealthy", "degraded"] = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Check timestamp",
    )
    checks: dict[str, bool] = Field(default_factory=dict, description="Individual component checks")
    uptime: float = Field(..., description="Uptime in seconds")

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat() if v else None})


# Error Models
class ErrorDetail(BaseModel):
    """Detailed error information"""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: str | None = Field(None, description="Field that caused the error")
    context: dict[str, Any] | None = Field(None, description="Additional error context")


class ErrorResponse(BaseResponse):
    """Error response model"""

    success: bool = Field(False, description="Always false for error responses")
    error_type: str = Field(..., description="Type of error")
    details: list[ErrorDetail] = Field(
        default_factory=list, description="Detailed error information"
    )


# WebSocket Models
class WebSocketMessage(BaseModel):
    """WebSocket message model"""

    type: str = Field(..., description="Message type")
    data: dict[str, Any] = Field(default_factory=dict, description="Message data")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Message timestamp",
    )
    client_id: str | None = Field(None, description="Client identifier")


class WebSocketResponse(BaseModel):
    """WebSocket response model"""

    type: str = Field(..., description="Response type")
    success: bool = Field(..., description="Whether operation was successful")
    data: dict[str, Any] | None = Field(None, description="Response data")
    error: str | None = Field(None, description="Error message if failed")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response timestamp",
    )


# Export all models
__all__ = [
    # Enums
    "SubjectType",
    "DifficultyLevel",
    "EnvironmentType",
    "TerrainSize",
    "QuizType",
    "ActivityType",
    # Base Models
    "BaseResponse",
    "PaginationModel",
    # Content Models
    "LearningObjective",
    "ContentRequest",
    "GeneratedScript",
    "TerrainConfiguration",
    "GameMechanics",
    "ContentResponse",
    # Quiz Models
    "QuizOption",
    "QuizQuestion",
    "Quiz",
    "QuizResponse",
    # User Models
    "User",
    "Session",
    # Plugin Models
    "PluginRegistration",
    "PluginMessage",
    # LMS Models
    "LMSCourse",
    "LMSAssignment",
    # Monitoring Models
    "UsageMetrics",
    "HealthCheck",
    # Error Models
    "ErrorDetail",
    "ErrorResponse",
    # WebSocket Models
    "WebSocketMessage",
    "WebSocketResponse",
]
