"""
ToolboxAI Settings Module

Configuration settings for the ToolboxAI Educational Platform.
These settings can be overridden via environment variables.
"""

import os
from typing import Optional, List, Dict, Any

# Application Settings
APP_NAME = os.getenv("APP_NAME", "ToolboxAI-Roblox-Environment")
VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes", "on")

# Server Configuration
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8008"))
FLASK_PORT = int(os.getenv("FLASK_PORT", "5001"))
MCP_PORT = int(os.getenv("MCP_PORT", "9876"))

# Database Configuration  
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/toolboxai_education")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# External API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SCHOOLOGY_KEY = os.getenv("SCHOOLOGY_KEY", "")
SCHOOLOGY_SECRET = os.getenv("SCHOOLOGY_SECRET", "")
CANVAS_TOKEN = os.getenv("CANVAS_TOKEN", "")

# Security Settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Agent Configuration
MAX_AGENT_RETRIES = int(os.getenv("MAX_AGENT_RETRIES", "3"))
AGENT_TIMEOUT_SECONDS = int(os.getenv("AGENT_TIMEOUT_SECONDS", "300"))

# Roblox Integration
ROBLOX_PLUGIN_PORT = int(os.getenv("ROBLOX_PLUGIN_PORT", "64989"))
ROBLOX_API_BASE = os.getenv("ROBLOX_API_BASE", "https://api.roblox.com")

# MCP Settings
MCP_MAX_TOKENS = int(os.getenv("MCP_MAX_TOKENS", "128000"))
MCP_CONTEXT_WINDOW = int(os.getenv("MCP_CONTEXT_WINDOW", "1000"))

# Educational Settings
DEFAULT_GRADE_LEVELS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
DEFAULT_SUBJECTS = [
    "Mathematics", 
    "Science", 
    "English Language Arts", 
    "Social Studies",
    "Art",
    "Music",
    "Physical Education",
    "Technology"
]

# Test Configuration
TESTING = os.getenv("TESTING", "False").lower() in ("true", "1", "yes", "on")
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")

# Feature Flags
ENABLE_REAL_DATA = os.getenv("ENABLE_REAL_DATA", "True").lower() in ("true", "1", "yes", "on")
ENABLE_AI_GENERATION = os.getenv("ENABLE_AI_GENERATION", "True").lower() in ("true", "1", "yes", "on")
ENABLE_ROBLOX_INTEGRATION = os.getenv("ENABLE_ROBLOX_INTEGRATION", "True").lower() in ("true", "1", "yes", "on")

# CORS Settings
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

# Rate Limiting
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))

# Cache Settings
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

def get_database_config() -> Dict[str, Any]:
    """Get database configuration dictionary."""
    return {
        "url": DATABASE_URL,
        "echo": DEBUG,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_recycle": 3600
    }

def get_redis_config() -> Dict[str, Any]:
    """Get Redis configuration dictionary."""
    return {
        "url": REDIS_URL,
        "decode_responses": True,
        "health_check_interval": 30
    }

def get_api_config() -> Dict[str, Any]:
    """Get API configuration dictionary."""
    return {
        "host": API_HOST,
        "port": API_PORT,
        "debug": DEBUG,
        "cors_origins": ALLOWED_ORIGINS,
        "rate_limit": RATE_LIMIT_PER_MINUTE
    }