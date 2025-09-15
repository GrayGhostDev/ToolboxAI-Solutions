"""
Configuration wrapper for backend app using centralized config
"""

import sys
import os
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env file from project root
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    env_file = project_root / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded .env file from {env_file}")
except ImportError:
    pass

# Add the project root to Python path to find toolboxai_settings
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from toolboxai_settings import settings

# Get the centralized configuration
_env_config = settings

class Settings:
    """Settings wrapper for backward compatibility"""

    def __init__(self):
        self._config = _env_config

    # Application Info
    @property
    def APP_NAME(self):
        return "ToolboxAI Roblox Environment"

    @property
    def APP_VERSION(self):
        return "1.0.0"

    @property
    def DEBUG(self):
        return self._config.is_development()

    @property
    def ENVIRONMENT(self):
        return self._config.env_name

    @property
    def LOG_LEVEL(self):
        return "INFO"

    # Server Configuration
    @property
    def FASTAPI_HOST(self):
        return "127.0.0.1"

    @property
    def FASTAPI_PORT(self):
        return 8008

    # CORS Configuration
    @property
    def CORS_ORIGINS(self):
        # Use secure CORS origins from settings which handles environment logic
        return self._config.CORS_ORIGINS

    # AI/ML Configuration
    @property
    def OPENAI_API_KEY(self):
        return self._config.get_api_key("openai")

    @property
    def OPENAI_MODEL(self):
        return self._config.llm.default_model

    @property
    def OPENAI_TEMPERATURE(self):
        return self._config.llm.temperature

    @property
    def MAX_TOKENS(self):
        return self._config.llm.max_tokens

    # Database Configuration
    @property
    def DATABASE_URL(self):
        return self._config.DATABASE_URL

    @property
    def REDIS_URL(self):
        return self._config.get_redis_url()

    # Authentication
    @property
    def JWT_SECRET_KEY(self):
        return self._config.JWT_SECRET_KEY

    @property
    def COOKIE_SECURE(self):
        """Use secure cookies in production (HTTPS only)"""
        return not self._config.is_development()

    @property
    def JWT_ALGORITHM(self):
        return self._config.JWT_ALGORITHM

    @property
    def JWT_ACCESS_TOKEN_EXPIRE_MINUTES(self):
        return self._config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

    @property
    def JWT_REFRESH_TOKEN_EXPIRE_DAYS(self):
        return self._config.JWT_REFRESH_TOKEN_EXPIRE_DAYS

    # Demo Authentication
    @property
    def DEMO_USERNAME(self):
        return getattr(self._config, 'DEMO_USERNAME', 'demo@example.com')

    @property
    def DEMO_PASSWORD(self):
        return getattr(self._config, 'DEMO_PASSWORD', 'demo123')

    # Educational Settings
    @property
    def SUPPORTED_SUBJECTS(self):
        return self._config.educational.supported_subjects

    @property
    def SUPPORTED_GRADE_LEVELS(self):
        return self._config.educational.supported_grade_levels

    @property
    def LEARNING_OBJECTIVES_ENABLED(self):
        return self._config.educational.learning_objectives_enabled

    @property
    def ASSESSMENT_MODE_ENABLED(self):
        return self._config.educational.assessment_mode_enabled

    # Sentry Configuration
    @property
    def SENTRY_DSN(self):
        return self._config.service_urls.sentry_dsn

    @property
    def SENTRY_ENVIRONMENT(self):
        return self._config.env_name

    # LMS Integration
    @property
    def SCHOOLOGY_KEY(self):
        return self._config.get_api_key("schoology")

    @property
    def SCHOOLOGY_SECRET(self):
        return os.getenv("SCHOOLOGY_SECRET")

    @property
    def CANVAS_TOKEN(self):
        return self._config.get_api_key("canvas")

    @property
    def CANVAS_BASE_URL(self):
        return os.getenv("CANVAS_BASE_URL", "https://canvas.instructure.com")

    # Content Generation Limits
    @property
    def MAX_CONCURRENT_GENERATIONS(self):
        return int(os.getenv("MAX_CONCURRENT_GENERATIONS", "10"))

    @property
    def MAX_CONTENT_GENERATION_TIME(self):
        return int(os.getenv("MAX_CONTENT_GENERATION_TIME", "300"))

    # WebSocket Configuration
    @property
    def WS_MAX_CONNECTIONS(self):
        return int(os.getenv("WS_MAX_CONNECTIONS", "1000"))

    @property
    def WS_HEARTBEAT_INTERVAL(self):
        return int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))

    @property
    def WS_RATE_LIMIT_PER_MINUTE(self):
        return int(os.getenv("WS_RATE_LIMIT_PER_MINUTE", "100"))

    # Pusher Configuration
    @property
    def PUSHER_ENABLED(self):
        return os.getenv("PUSHER_ENABLED", "false").lower() in ("true", "1", "yes")

    @property
    def PUSHER_APP_ID(self):
        return os.getenv("PUSHER_APP_ID")

    @property
    def PUSHER_KEY(self):
        return os.getenv("PUSHER_KEY")

    @property
    def PUSHER_SECRET(self):
        return os.getenv("PUSHER_SECRET")

    @property
    def PUSHER_CLUSTER(self):
        return os.getenv("PUSHER_CLUSTER", "us2")

    @property
    def PUSHER_SSL(self):
        return os.getenv("PUSHER_SSL", "true").lower() in ("true", "1", "yes")

    # Rojo API Configuration
    @property
    def ROJO_HOST(self):
        return os.getenv("ROJO_HOST", "localhost")

    @property
    def ROJO_PORT(self):
        return int(os.getenv("ROJO_PORT", "34872"))

    @property
    def ROJO_ENABLED(self):
        return os.getenv("ROJO_ENABLED", "true").lower() in ("true", "1", "yes")

    @property
    def ROJO_TIMEOUT(self):
        return int(os.getenv("ROJO_TIMEOUT", "30"))

    @property
    def RATE_LIMIT_PER_MINUTE(self):
        return int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    # Testing Configuration
    @property
    def SKIP_AUTH(self):
        return os.getenv("SKIP_AUTH", "false").lower() in ("true", "1", "yes")

    @property
    def env_name(self):
        """Alias for ENVIRONMENT for compatibility"""
        return self.ENVIRONMENT

    # Add other properties as needed...

    def model_dump(self):
        """For compatibility with pydantic"""
        return {
            "APP_NAME": self.APP_NAME,
            "APP_VERSION": self.APP_VERSION,
            "DEBUG": self.DEBUG,
            "ENVIRONMENT": self.ENVIRONMENT,
            "CORS_ORIGINS": self.CORS_ORIGINS,
            # Add more as needed
        }

# Create singleton instance
settings = Settings()
