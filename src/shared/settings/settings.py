"""Shared Settings module (pydantic v2 / pydantic-settings).

This module centralizes application settings for both Roblox and the
environment server copies. It uses pydantic v2 `pydantic-settings`.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Anchor .env to this package directory by default
DOTENV = os.path.join(os.path.dirname(__file__), ".env")


class Settings(BaseSettings):
    """Application settings for ToolboxAI (pydantic v2)."""

    model_config = SettingsConfigDict(
        env_file=DOTENV,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application Info
    APP_NAME: str = "ToolboxAI Roblox Environment"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")

    # Server Configuration
    FASTAPI_HOST: str = Field(default="127.0.0.1")
    FASTAPI_PORT: int = Field(default=8008)
    FLASK_HOST: str = Field(default="127.0.0.1")
    FLASK_PORT: int = Field(default=5001)
    ROBLOX_PLUGIN_PORT: int = Field(default=64989)

    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5001",
            "http://localhost:2368",
            "https://create.roblox.com",
            "https://www.roblox.com",
        ]
    )

    # AI/ML Configuration
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_MODEL: str = Field(default="gpt-4")
    OPENAI_TEMPERATURE: float = Field(default=0.7)
    MAX_TOKENS: int = Field(default=4000)

    # LangChain Configuration
    LANGCHAIN_TRACING_V2: bool = Field(default=True)
    LANGCHAIN_API_KEY: Optional[str] = Field(default=None)
    LANGCHAIN_PROJECT: str = Field(default="ToolboxAI-Roblox")

    # LMS Integration
    SCHOOLOGY_KEY: Optional[str] = Field(default=None)
    SCHOOLOGY_SECRET: Optional[str] = Field(default=None)
    CANVAS_TOKEN: Optional[str] = Field(default=None)
    CANVAS_BASE_URL: str = Field(default="https://canvas.instructure.com")

    # Database Configuration
    DATABASE_URL: Optional[str] = Field(default=None)
    REDIS_URL: str = Field(default="redis://localhost:6379")

    # Authentication
    JWT_SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440)

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=100)
    RATE_LIMIT_BURST: int = Field(default=200)

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
        ]
    )

    GRADE_LEVELS: List[int] = Field(default=list(range(1, 13)))

    MAX_QUIZ_QUESTIONS: int = Field(default=20)
    DEFAULT_QUIZ_QUESTIONS: int = Field(default=5)

    # Roblox Configuration
    ROBLOX_TERRAIN_SIZE_LIMITS: Dict[str, int] = Field(
        default={"small": 200, "medium": 500, "large": 1000, "xlarge": 2000}
    )

    ROBLOX_MAX_PARTS: int = Field(default=10000)
    ROBLOX_MAX_SCRIPTS: int = Field(default=100)

    # Content Generation Limits
    MAX_CONTENT_GENERATION_TIME: int = Field(default=300)
    MAX_CONCURRENT_GENERATIONS: int = Field(default=10)

    # Monitoring and Logging
    LOG_LEVEL: str = Field(default="INFO")
    ENABLE_METRICS: bool = Field(default=True)
    METRICS_PORT: int = Field(default=8009)

    # WebSocket Configuration
    WS_MAX_CONNECTIONS: int = Field(default=1000)
    WS_HEARTBEAT_INTERVAL: int = Field(default=30)

    # File Storage
    UPLOAD_DIR: str = Field(default="uploads")
    MAX_FILE_SIZE: int = Field(default=10485760)
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=[".lua", ".rbxl", ".rbxlx", ".json", ".txt", ".md"]
    )

    # MCP Server Configuration
    MCP_HOST: str = Field(default="localhost")
    MCP_PORT: int = Field(default=9876)
    MCP_MAX_CONTEXT_TOKENS: int = Field(default=128000)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or return as-is."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("SUPPORTED_SUBJECTS", mode="before")
    @classmethod
    def parse_subjects(cls, v):
        """Parse subjects from string or return as-is."""
        if isinstance(v, str):
            return [subject.strip() for subject in v.split(",")]
        return v

    @field_validator("GRADE_LEVELS", mode="before")
    @classmethod
    def parse_grade_levels(cls, v):
        """Parse grade levels from string or return as-is."""
        if isinstance(v, str):
            return [int(level.strip()) for level in v.split(",")]
        return v

    @field_validator("ROBLOX_TERRAIN_SIZE_LIMITS", mode="before")
    @classmethod
    def parse_terrain_limits(cls, v):
        """Parse terrain limits from string or return as-is."""
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("ALLOWED_FILE_TYPES", mode="before")
    @classmethod
    def parse_file_types(cls, v):
        """Parse file types from string or return as-is."""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v

    def get_database_url(self) -> str:
        """Get database URL."""
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
        """Validate required API keys."""
        missing: List[str] = []
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
            "fastapi_port": self.FASTAPI_PORT,
            "flask_port": self.FLASK_PORT,
            "roblox_plugin_port": self.ROBLOX_PLUGIN_PORT,
        }


# Singleton settings instance for convenience imports
settings = Settings()

__all__ = ["Settings", "settings"]
