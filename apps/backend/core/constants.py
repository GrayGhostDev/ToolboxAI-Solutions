"""
Application constants and enums for ToolBoxAI backend
"""

from enum import Enum, IntEnum
from typing import Final


class APIVersion(str, Enum):
    """API version constants"""

    V1 = "v1"
    V2 = "v2"


class UserRole(str, Enum):
    """User role definitions"""

    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"
    PARENT = "parent"
    GUEST = "guest"


class ContentType(str, Enum):
    """Content type definitions"""

    LESSON = "lesson"
    QUIZ = "quiz"
    SCRIPT = "script"
    TERRAIN = "terrain"
    ASSESSMENT = "assessment"
    TUTORIAL = "tutorial"


class ContentStatus(str, Enum):
    """Content generation status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Status(str, Enum):
    """General status definitions"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ENABLED = "enabled"
    DISABLED = "disabled"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class SessionStatus(str, Enum):
    """Session status definitions"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class OperationStatus(str, Enum):
    """General operation status"""

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Priority(IntEnum):
    """Priority levels for tasks/operations"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    URGENT = 5


class CacheKeys(str, Enum):
    """Redis cache key patterns"""

    USER_SESSION = "user:session:{user_id}"
    CONTENT_CACHE = "content:cache:{content_id}"
    QUIZ_CACHE = "quiz:cache:{quiz_id}"
    PLUGIN_STATUS = "plugin:status:{plugin_id}"
    RATE_LIMIT = "rate_limit:{user_id}:{endpoint}"


class EventTypes(str, Enum):
    """WebSocket/Pusher event types"""

    USER_CONNECTED = "user_connected"
    USER_DISCONNECTED = "user_disconnected"
    CONTENT_GENERATED = "content_generated"
    QUIZ_COMPLETED = "quiz_completed"
    PLUGIN_REGISTERED = "plugin_registered"
    ERROR_OCCURRED = "error_occurred"


class LogLevels(str, Enum):
    """Logging levels"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Permissions(str, Enum):
    """Permission definitions"""

    READ_CONTENT = "read:content"
    WRITE_CONTENT = "write:content"
    DELETE_CONTENT = "delete:content"
    READ_USERS = "read:users"
    WRITE_USERS = "write:users"
    DELETE_USERS = "delete:users"
    ADMIN_ACCESS = "admin:access"
    TEACHER_ACCESS = "teacher:access"


class DatabaseTables(str, Enum):
    """Database table names"""

    USERS = "users"
    SESSIONS = "sessions"
    CONTENT = "content"
    QUIZZES = "quizzes"
    PLUGINS = "plugins"
    AUDIT_LOGS = "audit_logs"


# Application constants
APP_NAME: Final[str] = "ToolBoxAI"
APP_VERSION: Final[str] = "1.0.0"
DEFAULT_PAGE_SIZE: Final[int] = 20
MAX_PAGE_SIZE: Final[int] = 100
DEFAULT_CACHE_TTL: Final[int] = 3600  # 1 hour
MAX_FILE_SIZE: Final[int] = 10 * 1024 * 1024  # 10MB
JWT_ALGORITHM: Final[str] = "HS256"
JWT_EXPIRY_HOURS: Final[int] = 24

# Rate limiting
DEFAULT_RATE_LIMIT: Final[int] = 100  # requests per hour
ADMIN_RATE_LIMIT: Final[int] = 1000  # requests per hour

# Content generation limits
MAX_LEARNING_OBJECTIVES: Final[int] = 10
MAX_QUIZ_QUESTIONS: Final[int] = 50
MAX_SCRIPT_SIZE: Final[int] = 1024 * 1024  # 1MB

# Plugin constants
DEFAULT_PLUGIN_PORT: Final[int] = 64989
PLUGIN_HEARTBEAT_INTERVAL: Final[int] = 30  # seconds
PLUGIN_TIMEOUT: Final[int] = 300  # 5 minutes

# Error codes
ERROR_CODES = {
    "VALIDATION_ERROR": "E001",
    "AUTHENTICATION_ERROR": "E002",
    "AUTHORIZATION_ERROR": "E003",
    "NOT_FOUND": "E004",
    "INTERNAL_ERROR": "E005",
    "RATE_LIMIT_EXCEEDED": "E006",
    "CONTENT_GENERATION_FAILED": "E007",
    "PLUGIN_CONNECTION_FAILED": "E008",
    "DATABASE_ERROR": "E009",
    "CACHE_ERROR": "E010",
}

# HTTP status messages
HTTP_STATUS_MESSAGES = {
    200: "Success",
    201: "Created",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    422: "Validation Error",
    429: "Rate Limit Exceeded",
    500: "Internal Server Error",
    503: "Service Unavailable",
}

__all__ = [
    "APIVersion",
    "UserRole",
    "ContentType",
    "ContentStatus",
    "Status",
    "SessionStatus",
    "OperationStatus",
    "Priority",
    "CacheKeys",
    "EventTypes",
    "LogLevels",
    "Permissions",
    "DatabaseTables",
    "APP_NAME",
    "APP_VERSION",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "DEFAULT_CACHE_TTL",
    "MAX_FILE_SIZE",
    "JWT_ALGORITHM",
    "JWT_EXPIRY_HOURS",
    "DEFAULT_RATE_LIMIT",
    "ADMIN_RATE_LIMIT",
    "MAX_LEARNING_OBJECTIVES",
    "MAX_QUIZ_QUESTIONS",
    "MAX_SCRIPT_SIZE",
    "DEFAULT_PLUGIN_PORT",
    "PLUGIN_HEARTBEAT_INTERVAL",
    "PLUGIN_TIMEOUT",
    "ERROR_CODES",
    "HTTP_STATUS_MESSAGES",
]
