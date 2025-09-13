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
ENV_NAME = os.getenv("ENV_NAME", "development")

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

# Service URLs Configuration
SERVICE_URLS = {
    "backend": f"http://{API_HOST}:{API_PORT}",
    "flask": f"http://{API_HOST}:{FLASK_PORT}",
    "mcp": f"http://{API_HOST}:{MCP_PORT}",
    "roblox_plugin": f"http://localhost:{ROBLOX_PLUGIN_PORT}",
}

def should_use_real_data() -> bool:
    """Check if real data should be used (vs mock data)."""
    return ENABLE_REAL_DATA

# Additional attributes for compatibility
class LLMConfig:
    """LLM configuration."""
    def __init__(self):
        self.default_model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "4000"))

class EducationalConfig:
    """Educational settings configuration."""
    def __init__(self):
        self.supported_subjects = DEFAULT_SUBJECTS
        self.supported_grade_levels = DEFAULT_GRADE_LEVELS
        self.learning_objectives_enabled = True
        self.assessment_mode_enabled = True

class ServiceURLsConfig:
    """Service URLs configuration."""
    def __init__(self):
        self.backend = f"http://{API_HOST}:{API_PORT}"
        self.flask = f"http://{API_HOST}:{FLASK_PORT}"
        self.mcp = f"http://{API_HOST}:{MCP_PORT}"
        self.roblox_plugin = f"http://localhost:{ROBLOX_PLUGIN_PORT}"
        self.sentry_dsn = os.getenv("SENTRY_DSN", "")

class Settings:
    """Settings class with attributes for compatibility."""
    def __init__(self):
        # Copy all module-level variables as attributes
        self.app_name = APP_NAME
        self.version = VERSION
        self.debug = DEBUG
        self.env_name = ENV_NAME
        self.api_host = API_HOST
        self.api_port = API_PORT
        self.flask_port = FLASK_PORT
        self.mcp_port = MCP_PORT
        self.database_url = DATABASE_URL
        self.redis_url = REDIS_URL
        self.openai_api_key = OPENAI_API_KEY
        self.jwt_secret_key = JWT_SECRET_KEY
        self.jwt_algorithm = JWT_ALGORITHM
        self.jwt_expiration_hours = JWT_EXPIRATION_HOURS
        self.log_level = LOG_LEVEL
        self.log_format = LOG_FORMAT
        self.max_agent_retries = MAX_AGENT_RETRIES
        self.agent_timeout_seconds = AGENT_TIMEOUT_SECONDS
        self.roblox_plugin_port = ROBLOX_PLUGIN_PORT
        self.roblox_api_base = ROBLOX_API_BASE
        self.mcp_max_tokens = MCP_MAX_TOKENS
        self.mcp_context_window = MCP_CONTEXT_WINDOW
        self.default_grade_levels = DEFAULT_GRADE_LEVELS
        self.default_subjects = DEFAULT_SUBJECTS
        self.testing = TESTING
        self.test_database_url = TEST_DATABASE_URL
        self.enable_real_data = ENABLE_REAL_DATA
        self.enable_ai_generation = ENABLE_AI_GENERATION
        self.enable_roblox_integration = ENABLE_ROBLOX_INTEGRATION
        self.allowed_origins = ALLOWED_ORIGINS
        self.cors_origins = ALLOWED_ORIGINS  # Alias for compatibility
        self.rate_limit_per_minute = RATE_LIMIT_PER_MINUTE
        self.cache_ttl_seconds = CACHE_TTL_SECONDS
        
        # Nested configurations
        self.llm = LLMConfig()
        self.educational = EducationalConfig()
        self.service_urls = ServiceURLsConfig()
        
        # Additional compatibility attributes
        self.ENV_NAME = ENV_NAME
        self.DEBUG = DEBUG
        self.API_HOST = API_HOST
        self.API_PORT = API_PORT
        self.FLASK_PORT = FLASK_PORT
        self.ROBLOX_PLUGIN_PORT = ROBLOX_PLUGIN_PORT
        self.DATABASE_URL = DATABASE_URL
        self.REDIS_URL = REDIS_URL
        self.OPENAI_API_KEY = OPENAI_API_KEY
        self.CORS_ORIGINS = ALLOWED_ORIGINS
        self.JWT_SECRET_KEY = JWT_SECRET_KEY
        self.JWT_ALGORITHM = JWT_ALGORITHM
        
        # Additional compatibility attributes
        self.use_mock_database = os.getenv("USE_MOCK_DATABASE", "false").lower() in ("true", "1", "yes", "on")
        self.use_mock_llm = os.getenv("USE_MOCK_LLM", "true").lower() in ("true", "1", "yes", "on")
        
    def is_development(self) -> bool:
        """Check if environment is development."""
        return self.env_name.lower() in ("development", "dev", "local")
    
    def get_api_key(self, service: str) -> str:
        """Get API key for a service."""
        if service == "openai":
            return self.openai_api_key
        elif service == "schoology":
            return os.getenv("SCHOOLOGY_KEY", "")
        elif service == "canvas":
            return os.getenv("CANVAS_TOKEN", "")
        return ""
    
    def get_redis_url(self) -> str:
        """Get Redis URL."""
        return self.redis_url
    
    def get_service_url(self, service: str) -> str:
        """Get URL for a service."""
        if service == "backend":
            return self.service_urls.backend
        elif service == "flask":
            return self.service_urls.flask
        elif service == "mcp":
            return self.service_urls.mcp
        elif service == "roblox_plugin":
            return self.service_urls.roblox_plugin
        return ""
        
    def get_database_config(self) -> Dict[str, Any]:
        return get_database_config()
    
    def get_redis_config(self) -> Dict[str, Any]:
        return get_redis_config()
    
    def get_api_config(self) -> Dict[str, Any]:
        return get_api_config()

# Create a singleton settings instance
settings = Settings()