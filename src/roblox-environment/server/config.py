"""
Configuration Management for ToolboxAI Roblox Environment

Manages environment variables, API keys, service URLs, and educational settings.
Provides centralized configuration for all server components.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from src.shared.settings.compat import (
    BaseSettings,
    Field,
    SettingsConfigDict,
    field_validator,
)

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application Info
    APP_NAME: str = "ToolboxAI Roblox Environment"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, validation_alias="DEBUG")
    ENVIRONMENT: str = Field(default="development", validation_alias="ENVIRONMENT")

    # Server Configuration
    FASTAPI_HOST: str = Field(default="127.0.0.1", validation_alias="FASTAPI_HOST")
    FASTAPI_PORT: int = Field(default=8008, validation_alias="FASTAPI_PORT")
    FLASK_HOST: str = Field(default="127.0.0.1", validation_alias="FLASK_HOST")
    FLASK_PORT: int = Field(default=5001, validation_alias="FLASK_PORT")
    ROBLOX_PLUGIN_PORT: int = Field(
        default=64989, validation_alias="ROBLOX_PLUGIN_PORT"
    )

    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5001",
            "http://localhost:2368",
            "https://create.roblox.com",
            "https://www.roblox.com",
        ],
        validation_alias="CORS_ORIGINS",
    )

    # AI/ML Configuration
    OPENAI_API_KEY: Optional[str] = Field(
        default=None, validation_alias="OPENAI_API_KEY"
    )
    OPENAI_MODEL: str = Field(default="gpt-4", validation_alias="OPENAI_MODEL")
    OPENAI_TEMPERATURE: float = Field(
        default=0.7, validation_alias="OPENAI_TEMPERATURE"
    )
    MAX_TOKENS: int = Field(default=4000, validation_alias="MAX_TOKENS")

    # LangChain Configuration
    LANGCHAIN_TRACING_V2: bool = Field(
        default=True, validation_alias="LANGCHAIN_TRACING_V2"
    )
    LANGCHAIN_API_KEY: Optional[str] = Field(
        default=None, validation_alias="LANGCHAIN_API_KEY"
    )
    LANGCHAIN_PROJECT: str = Field(
        default="ToolboxAI-Roblox", validation_alias="LANGCHAIN_PROJECT"
    )

    # LMS Integration
    SCHOOLOGY_KEY: Optional[str] = Field(default=None, validation_alias="SCHOOLOGY_KEY")
    SCHOOLOGY_SECRET: Optional[str] = Field(
        default=None, validation_alias="SCHOOLOGY_SECRET"
    )
    CANVAS_TOKEN: Optional[str] = Field(default=None, validation_alias="CANVAS_TOKEN")
    CANVAS_BASE_URL: str = Field(
        default="https://canvas.instructure.com", validation_alias="CANVAS_BASE_URL"
    )

    # Database Configuration
    DATABASE_URL: Optional[str] = Field(default=None, validation_alias="DATABASE_URL")
    REDIS_URL: str = Field(
        default="redis://localhost:6379", validation_alias="REDIS_URL"
    )

    # Authentication
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        validation_alias="JWT_SECRET_KEY",
    )
    JWT_ALGORITHM: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=1440, validation_alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    # Demo Credentials (for development only)
    DEMO_USERNAME: Optional[str] = Field(default=None, validation_alias="DEMO_USERNAME")
    DEMO_PASSWORD: Optional[str] = Field(default=None, validation_alias="DEMO_PASSWORD")

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=100, validation_alias="RATE_LIMIT_PER_MINUTE"
    )
    RATE_LIMIT_BURST: int = Field(default=200, validation_alias="RATE_LIMIT_BURST")

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
        validation_alias="SUPPORTED_SUBJECTS",
    )

    GRADE_LEVELS: List[int] = Field(
        default=list(range(1, 13)), validation_alias="GRADE_LEVELS"
    )

    MAX_QUIZ_QUESTIONS: int = Field(default=20, validation_alias="MAX_QUIZ_QUESTIONS")
    DEFAULT_QUIZ_QUESTIONS: int = Field(
        default=5, validation_alias="DEFAULT_QUIZ_QUESTIONS"
    )

    # Roblox Configuration
    ROBLOX_TERRAIN_SIZE_LIMITS: Dict[str, int] = Field(
        default={"small": 200, "medium": 500, "large": 1000, "xlarge": 2000},
        validation_alias="ROBLOX_TERRAIN_SIZE_LIMITS",
    )

    ROBLOX_MAX_PARTS: int = Field(default=10000, validation_alias="ROBLOX_MAX_PARTS")
    ROBLOX_MAX_SCRIPTS: int = Field(default=100, validation_alias="ROBLOX_MAX_SCRIPTS")

    # Content Generation Limits
    MAX_CONTENT_GENERATION_TIME: int = Field(
        default=300, validation_alias="MAX_CONTENT_GENERATION_TIME"
    )
    MAX_CONCURRENT_GENERATIONS: int = Field(
        default=10, validation_alias="MAX_CONCURRENT_GENERATIONS"
    )

    # Monitoring and Logging
    LOG_LEVEL: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    ENABLE_METRICS: bool = Field(default=True, validation_alias="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=8009, validation_alias="METRICS_PORT")

    # WebSocket Configuration
    WS_MAX_CONNECTIONS: int = Field(default=1000, validation_alias="WS_MAX_CONNECTIONS")
    WS_HEARTBEAT_INTERVAL: int = Field(
        default=30, validation_alias="WS_HEARTBEAT_INTERVAL"
    )

    # File Storage
    UPLOAD_DIR: str = Field(default="uploads", validation_alias="UPLOAD_DIR")
    MAX_FILE_SIZE: int = Field(default=10485760, validation_alias="MAX_FILE_SIZE")
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=[".lua", ".rbxl", ".rbxlx", ".json", ".txt", ".md"],
        validation_alias="ALLOWED_FILE_TYPES",
    )

    # MCP Server Configuration
    MCP_HOST: str = Field(default="localhost", validation_alias="MCP_HOST")
    MCP_PORT: int = Field(default=9876, validation_alias="MCP_PORT")
    MCP_MAX_CONTEXT_TOKENS: int = Field(
        default=128000, validation_alias="MCP_MAX_CONTEXT_TOKENS"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
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
            return json.loads(v)
        return v

    @field_validator("ALLOWED_FILE_TYPES", mode="before")
    @classmethod
    def parse_file_types(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
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


# Global settings instance
settings = Settings()

__all__ = ["settings", "Settings"]
