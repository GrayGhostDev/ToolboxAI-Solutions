"""
Configuration Management for ToolboxAI Roblox Environment

Manages environment variables, API keys, service URLs, and educational settings.
Provides centralized configuration for all server components.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Type, Tuple

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (init_settings, env_settings, dotenv_settings, file_secret_settings)

    # Application Info
    APP_NAME: str = "ToolboxAI Roblox Environment"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, alias="DEBUG")
    ENVIRONMENT: str = Field(default="development", alias="ENVIRONMENT")

    # Server Configuration
    FASTAPI_HOST: str = Field(default="127.0.0.1", alias="FASTAPI_HOST")
    FASTAPI_PORT: int = Field(default=8008, alias="FASTAPI_PORT")
    FLASK_HOST: str = Field(default="127.0.0.1", alias="FLASK_HOST")
    FLASK_PORT: int = Field(default=5001, alias="FLASK_PORT")
    ROBLOX_PLUGIN_PORT: int = Field(default=64989, alias="ROBLOX_PLUGIN_PORT")

    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5001",
            "http://localhost:5173",
            "http://localhost:5175",  # Dashboard dev server
            "http://localhost:2368",
            "http://127.0.0.1:5175",  # Dashboard dev server (alternate)
            "https://create.roblox.com",
            "https://www.roblox.com",
        ],
        alias="CORS_ORIGINS",
    )

    # AI/ML Configuration
    OPENAI_API_KEY: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4", alias="OPENAI_MODEL")
    OPENAI_TEMPERATURE: float = Field(default=0.7, alias="OPENAI_TEMPERATURE")
    MAX_TOKENS: int = Field(default=4000, alias="MAX_TOKENS")

    # LangChain Configuration
    LANGCHAIN_TRACING_V2: bool = Field(default=True, alias="LANGCHAIN_TRACING_V2")
    LANGCHAIN_API_KEY: Optional[str] = Field(default=None, alias="LANGCHAIN_API_KEY")
    LANGCHAIN_PROJECT: str = Field(default="ToolboxAI-Roblox", alias="LANGCHAIN_PROJECT")

    # LMS Integration
    SCHOOLOGY_KEY: Optional[str] = Field(default=None, alias="SCHOOLOGY_KEY")
    SCHOOLOGY_SECRET: Optional[str] = Field(default=None, alias="SCHOOLOGY_SECRET")
    CANVAS_TOKEN: Optional[str] = Field(default=None, alias="CANVAS_TOKEN")
    CANVAS_BASE_URL: str = Field(default="https://canvas.instructure.com", alias="CANVAS_BASE_URL")

    # Database Configuration
    DATABASE_URL: Optional[str] = Field(default=None, alias="DATABASE_URL")
    REDIS_URL: str = Field(default="redis://localhost:6379", alias="REDIS_URL")

    # Authentication
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        alias="JWT_SECRET_KEY",
    )
    JWT_ALGORITHM: str = Field(default="HS256", alias="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=1440, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # Demo Credentials (for development only)
    DEMO_USERNAME: Optional[str] = Field(default=None, alias="DEMO_USERNAME")
    DEMO_PASSWORD: Optional[str] = Field(default=None, alias="DEMO_PASSWORD")

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, alias="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_BURST: int = Field(default=200, alias="RATE_LIMIT_BURST")

    # Testing Configuration
    TESTING_MODE: bool = Field(default=False, alias="TESTING_MODE")
    BYPASS_RATE_LIMIT_IN_TESTS: bool = Field(default=True, alias="BYPASS_RATE_LIMIT_IN_TESTS")

    # Educational Settings
    SUPPORTED_SUBJECTS: List[str] = Field(
        default=[
            "Mathematics",
            "Science",
            "History",
            "English",
            "Art",
            "Geography",
            "Computer Science",
            "Physics",
            "Chemistry",
            "Biology",
        ],
        alias="SUPPORTED_SUBJECTS",
    )

    GRADE_LEVELS: List[int] = Field(default=list(range(1, 13)), alias="GRADE_LEVELS")

    MAX_QUIZ_QUESTIONS: int = Field(default=20, alias="MAX_QUIZ_QUESTIONS")
    DEFAULT_QUIZ_QUESTIONS: int = Field(default=5, alias="DEFAULT_QUIZ_QUESTIONS")

    # Roblox Configuration
    ROBLOX_TERRAIN_SIZE_LIMITS: Dict[str, int] = Field(
        default={"small": 200, "medium": 500, "large": 1000, "xlarge": 2000},
        alias="ROBLOX_TERRAIN_SIZE_LIMITS",
    )

    ROBLOX_MAX_PARTS: int = Field(default=10000, alias="ROBLOX_MAX_PARTS")
    ROBLOX_MAX_SCRIPTS: int = Field(default=100, alias="ROBLOX_MAX_SCRIPTS")

    # Content Generation Limits
    MAX_CONTENT_GENERATION_TIME: int = Field(default=300, alias="MAX_CONTENT_GENERATION_TIME")
    MAX_CONCURRENT_GENERATIONS: int = Field(default=10, alias="MAX_CONCURRENT_GENERATIONS")

    # Monitoring and Logging
    LOG_LEVEL: str = Field(default="INFO", alias="LOG_LEVEL")
    ENABLE_METRICS: bool = Field(default=True, alias="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=8009, alias="METRICS_PORT")

    # Sentry Configuration
    SENTRY_DSN: Optional[str] = Field(default=None, alias="SENTRY_DSN")
    SENTRY_ENVIRONMENT: str = Field(default="development", alias="SENTRY_ENVIRONMENT")
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=1.0, alias="SENTRY_TRACES_SAMPLE_RATE")
    SENTRY_PROFILES_SAMPLE_RATE: float = Field(default=1.0, alias="SENTRY_PROFILES_SAMPLE_RATE")
    SENTRY_SEND_DEFAULT_PII: bool = Field(default=False, alias="SENTRY_SEND_DEFAULT_PII")
    SENTRY_ENABLE_LOGS: bool = Field(default=True, alias="SENTRY_ENABLE_LOGS")
    SENTRY_RELEASE: Optional[str] = Field(default=None, alias="SENTRY_RELEASE")
    SENTRY_SERVER_NAME: Optional[str] = Field(default=None, alias="SENTRY_SERVER_NAME")

    # WebSocket Configuration
    WS_MAX_CONNECTIONS: int = Field(default=1000, alias="WS_MAX_CONNECTIONS")
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, alias="WS_HEARTBEAT_INTERVAL")
    WS_RATE_LIMIT_PER_MINUTE: int = Field(default=100, alias="WS_RATE_LIMIT_PER_MINUTE")
    WS_RBAC_REQUIRED_ROLES: Dict[str, str] = Field(
        default={"broadcast": "teacher", "content_request": "teacher", "roblox_event": "teacher"},
        alias="WS_RBAC_REQUIRED_ROLES",
    )
    WS_CHANNEL_ROLE_PREFIXES: Dict[str, str] = Field(
        default={"admin_": "admin", "teacher_": "teacher"}, alias="WS_CHANNEL_ROLE_PREFIXES"
    )

    # Pusher Channels Configuration
    PUSHER_ENABLED: bool = Field(default=False, alias="PUSHER_ENABLED")
    PUSHER_APP_ID: Optional[str] = Field(default=None, alias="PUSHER_APP_ID")
    PUSHER_KEY: Optional[str] = Field(default=None, alias="PUSHER_KEY")
    PUSHER_SECRET: Optional[str] = Field(default=None, alias="PUSHER_SECRET")
    PUSHER_CLUSTER: str = Field(default="us2", alias="PUSHER_CLUSTER")

    # Socket.IO Configuration
    SIO_RATE_LIMIT_PER_MINUTE: int = Field(default=100, alias="SIO_RATE_LIMIT_PER_MINUTE")
    SIO_RBAC_REQUIRED_ROLES: Dict[str, str] = Field(
        default={
            "content_request": "teacher",
            "subscribe": "student",
            "unsubscribe": "student",
            "quiz_response": "student",
            "progress_update": "student",
            "collaboration_message": "student",
            "ping": "student",
        },
        alias="SIO_RBAC_REQUIRED_ROLES",
    )

    # File Storage
    UPLOAD_DIR: str = Field(default="uploads", alias="UPLOAD_DIR")
    MAX_FILE_SIZE: int = Field(default=10485760, alias="MAX_FILE_SIZE")
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=[".lua", ".rbxl", ".rbxlx", ".json", ".txt", ".md"],
        alias="ALLOWED_FILE_TYPES",
    )

    # MCP Server Configuration
    MCP_HOST: str = Field(default="localhost", alias="MCP_HOST")
    MCP_PORT: int = Field(default=9876, alias="MCP_PORT")
    MCP_MAX_CONTEXT_TOKENS: int = Field(default=128000, alias="MCP_MAX_CONTEXT_TOKENS")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        # Handle JSON string or comma-separated values
        if isinstance(v, str):
            # Try to parse as JSON first
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Fall back to comma-separated
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("SUPPORTED_SUBJECTS", mode="before")
    @classmethod
    def parse_subjects(cls, v):
        if isinstance(v, str):
            return [subject.strip() for subject in v.split(",")]
        return v

    @field_validator("GRADE_LEVELS", mode="before")
    @classmethod
    def parse_grade_levels(cls, v):
        if isinstance(v, str):
            return [int(level.strip()) for level in v.split(",")]
        return v

    @field_validator("ROBLOX_TERRAIN_SIZE_LIMITS", mode="before")
    @classmethod
    def parse_terrain_limits(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # If JSON parsing fails, return default value
                return {"small": 200, "medium": 500, "large": 1000, "xlarge": 2000}
        return v

    @field_validator("ALLOWED_FILE_TYPES", mode="before")
    @classmethod
    def parse_file_types(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v

    @field_validator("WS_RBAC_REQUIRED_ROLES", mode="before")
    @classmethod
    def parse_ws_rbac_roles(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, Exception):
                # Return default if JSON parsing fails
                return {
                    "broadcast": "teacher",
                    "content_request": "teacher",
                    "roblox_event": "teacher",
                }
        return v

    @field_validator("WS_CHANNEL_ROLE_PREFIXES", mode="before")
    @classmethod
    def parse_ws_channel_role_prefixes(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, Exception):
                # Return default if JSON parsing fails
                return {"admin_": "admin", "teacher_": "teacher"}
        return v

    @field_validator("SIO_RBAC_REQUIRED_ROLES", mode="before")
    @classmethod
    def parse_sio_rbac_roles(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, Exception):
                # Return default if JSON parsing fails
                return {
                    "content_request": "teacher",
                    "subscribe": "student",
                    "unsubscribe": "student",
                    "quiz_response": "student",
                    "progress_update": "student",
                    "collaboration_message": "student",
                    "ping": "student",
                }
        return v

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        env_parse_none_str="",
    )

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return "sqlite:///./toolboxai_roblox.db"

    def get_api_keys(self) -> Dict[str, Optional[str]]:
        """Get API keys."""
        return {
            "openai": self.OPENAI_API_KEY,
            "langchain": self.LANGCHAIN_API_KEY,
            "schoology_key": self.SCHOOLOGY_KEY,
            "schoology_secret": self.SCHOOLOGY_SECRET,
            "canvas": self.CANVAS_TOKEN,
        }

    def validate_required_keys(self) -> List[str]:
        """Check if required API keys are present."""
        missing = []
        api_keys = self.get_api_keys()
        required_keys = ["openai"]
        for key in required_keys:
            if not api_keys.get(key):
                missing.append(key)
        return missing

    def get_educational_config(self) -> Dict[str, Any]:
        """Get educational configuration."""
        return {
            "subjects": self.SUPPORTED_SUBJECTS,
            "grade_levels": self.GRADE_LEVELS,
            "max_quiz_questions": self.MAX_QUIZ_QUESTIONS,
            "default_quiz_questions": self.DEFAULT_QUIZ_QUESTIONS,
            "terrain_limits": self.ROBLOX_TERRAIN_SIZE_LIMITS,
            "max_parts": self.ROBLOX_MAX_PARTS,
            "max_scripts": self.ROBLOX_MAX_SCRIPTS,
        }

    def get_server_info(self) -> Dict[str, Any]:
        """Get server information."""
        return {
            "app_name": self.APP_NAME,
            "version": self.APP_VERSION,
            "environment": self.ENVIRONMENT,
            "debug": self.DEBUG,
            "fastapi_host": self.FASTAPI_HOST,
            "fastapi_port": self.FASTAPI_PORT,
            "flask_host": self.FLASK_HOST,
            "flask_port": self.FLASK_PORT,
            "roblox_plugin_port": self.ROBLOX_PLUGIN_PORT,
        }

    def get_sentry_config(self) -> Dict[str, Any]:
        """Get Sentry configuration."""
        return {
            "dsn": self.SENTRY_DSN,
            "environment": self.SENTRY_ENVIRONMENT,
            "traces_sample_rate": (
                0.1 if self.ENVIRONMENT == "production" else self.SENTRY_TRACES_SAMPLE_RATE
            ),
            "profiles_sample_rate": (
                0.1 if self.ENVIRONMENT == "production" else self.SENTRY_PROFILES_SAMPLE_RATE
            ),
            "send_default_pii": (
                False if self.ENVIRONMENT == "production" else self.SENTRY_SEND_DEFAULT_PII
            ),
            "enable_logs": self.SENTRY_ENABLE_LOGS,
            "release": self.SENTRY_RELEASE or self.APP_VERSION,
            "server_name": self.SENTRY_SERVER_NAME,
        }


# Global settings instance
settings = Settings()

__all__ = ["settings", "Settings"]
