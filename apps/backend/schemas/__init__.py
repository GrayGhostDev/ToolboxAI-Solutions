"""
Backend schemas module - Re-exports from models.schemas for compatibility
"""

# Re-export all schemas from models.schemas
from ..models.schemas import *

__all__ = [
    # Enums
    "SubjectType",
    "DifficultyLevel",
    "EnvironmentType",
    "TerrainSize",
    "QuizType",
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
