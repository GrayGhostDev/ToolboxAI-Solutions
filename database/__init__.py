"""
Database Package for ToolboxAI

Contains database models, utilities, and connection management.
"""

# Import database models and utilities
from .models.models import (
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

# Import core database utilities
try:
    from .core.connection_manager import (
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
except ImportError:
    # Fallback for when core connection manager is not available
    pass

try:
    from .connection import get_db
except ImportError:
    pass

try:
    from .core.roblox_models import *
except ImportError:
    pass

# Import agent models if available
try:
    from .models.agent_models import (
        AgentInstance, AgentExecution, AgentMetrics, AgentTaskQueue,
        SystemHealth, AgentConfiguration, AgentType, AgentStatus,
        TaskStatus, TaskPriority
    )
except ImportError:
    pass

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
    # Connection management (if available)
    "db_manager",
    "get_async_session",
    "get_session",
    "get_db",
    "initialize_databases",
    "cleanup_databases",
    "health_check",
    "get_performance_stats",
    # Redis (if available)
    "redis_manager",
    "get_redis_client",
    "get_redis_client_sync",
    # Agent models (if available)
    "AgentInstance", "AgentExecution", "AgentMetrics", "AgentTaskQueue",
    "SystemHealth", "AgentConfiguration", "AgentType", "AgentStatus",
    "TaskStatus", "TaskPriority"
]