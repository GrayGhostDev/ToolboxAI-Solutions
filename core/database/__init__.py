"""
Database Package for ToolboxAI

Contains database models, utilities, and connection management.
"""

# Import database models and utilities
from .models import (
    Base,
    User, UserRole,
    Course, Lesson, Content, ContentStatus, DifficultyLevel,
    Quiz, QuizQuestion,
    UserProgress, UserAchievement, Achievement, AchievementType,
    Enrollment, QuizAttempt,
    Analytics, Session,
    # Alias for compatibility
    EducationalContent
)
from .connection_manager import (
    db_manager,
    get_async_session,
    get_session,
    initialize_databases,
    cleanup_databases,
    health_check,
    get_performance_stats,
    redis_manager,
    get_redis_client,
    get_redis_client_sync
)
from .roblox_models import *

__all__ = [
    # Base
    "Base",
    # User models
    "User", "UserRole",
    # Course models  
    "Course", "Lesson", "Content", "ContentStatus", "DifficultyLevel",
    # Quiz models
    "Quiz", "QuizQuestion",
    # Progress and achievement models
    "UserProgress", "UserAchievement", "Achievement", "AchievementType",
    # Other models
    "Enrollment", "QuizAttempt", "Analytics", "Session",
    # Alias
    "EducationalContent",
    # Connection management
    "db_manager",
    "get_async_session",
    "get_session", 
    "initialize_databases",
    "cleanup_databases",
    "health_check",
    "get_performance_stats",
    # Redis
    "redis_manager",
    "get_redis_client",
    "get_redis_client_sync",
    # Roblox models
    "roblox_models"
]