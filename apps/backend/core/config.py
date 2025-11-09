"""
Configuration wrapper for backend app using centralized config
Enhanced with HashiCorp Vault integration for secure secret management
"""

import sys
import os
import logging
from pathlib import Path
from functools import lru_cache
from typing import Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    # Load .env file from project root
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

# Add the project root to Python path to find toolboxai_settings
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from toolboxai_settings import settings

# Get the centralized configuration
_env_config = settings

# Initialize Vault integration if enabled
_vault_manager = None
VAULT_ENABLED = os.getenv("VAULT_ENABLED", "false").lower() in ("true", "1", "yes")

if VAULT_ENABLED:
    try:
        from apps.backend.services.vault_manager import get_vault_manager
        _vault_manager = get_vault_manager()
        logger.info("HashiCorp Vault integration enabled")
    except Exception as e:
        logger.warning(f"Vault integration failed, falling back to environment variables: {e}")
        _vault_manager = None


class Settings:
    """Settings wrapper for backward compatibility with Vault integration"""

    def __init__(self):
        self._config = _env_config
        self._vault = _vault_manager
        self._secret_cache = {}  # Cache secrets to reduce Vault calls

    @lru_cache(maxsize=128)
    def _get_secret(self, key: str, vault_path: Optional[str] = None, fallback: Any = None) -> Any:
        """
        Get secret from Vault if available, otherwise from environment

        Args:
            key: Environment variable key
            vault_path: Optional Vault path (defaults to apps/backend/secrets/{key})
            fallback: Fallback value if not found

        Returns:
            Secret value
        """
        # Try Vault first if enabled
        if self._vault and vault_path:
            try:
                return self._vault.get_secret(vault_path)
            except Exception as e:
                logger.debug(f"Vault lookup failed for {vault_path}, using fallback: {e}")

        # Fall back to environment variable
        env_value = os.getenv(key, fallback)

        # If still no value and Vault is available, try default path
        if not env_value and self._vault:
            try:
                default_path = f"apps/backend/secrets/{key.lower()}"
                return self._vault.get_secret(default_path)
            except Exception:
                pass

        return env_value

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
        return 8009

    # CORS Configuration
    @property
    def CORS_ORIGINS(self):
        # Use secure CORS origins from settings which handles environment logic
        return self._config.CORS_ORIGINS

    # AI/ML Configuration
    @property
    def OPENAI_API_KEY(self):
        # Prioritize Vault for API keys
        return self._get_secret(
            "OPENAI_API_KEY",
            vault_path="apps/backend/api_keys/openai",
            fallback=self._config.get_api_key("openai")
        )

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
        # Use dynamic database credentials from Vault if available
        if self._vault:
            try:
                creds = self._vault.get_dynamic_database_credentials("toolboxai", ttl="24h")
                # Build DATABASE_URL from dynamic credentials
                db_host = os.getenv("DB_HOST", "localhost")
                db_name = os.getenv("DB_NAME", "toolboxai")
                return f"postgresql://{creds['username']}:{creds['password']}@{db_host}/{db_name}"
            except Exception as e:
                logger.debug(f"Dynamic DB credentials unavailable: {e}")
        return self._config.DATABASE_URL

    @property
    def REDIS_URL(self):
        # Redis credentials from Vault
        return self._get_secret(
            "REDIS_URL",
            vault_path="apps/backend/cache/redis",
            fallback=self._config.get_redis_url()
        )

    # Authentication
    @property
    def JWT_SECRET_KEY(self):
        """
        Get JWT secret key with bcrypt compatibility validation.

        BCrypt has a 72-byte limit for passwords. To ensure compatibility,
        we validate and truncate the JWT_SECRET_KEY to 64 characters (256 bits)
        which provides strong entropy while staying safely under the limit.
        """
        # JWT secrets should always come from Vault in production
        key = self._get_secret(
            "JWT_SECRET_KEY",
            vault_path="apps/backend/auth/jwt_secret",
            fallback=self._config.JWT_SECRET_KEY
        )

        # Validate length for bcrypt compatibility (72-byte limit)
        if key and len(key) > 64:
            logger.warning(
                f"JWT_SECRET_KEY exceeds recommended 64 characters ({len(key)} chars). "
                f"Truncating to 64 chars to ensure bcrypt compatibility (72-byte limit)."
            )
            return key[:64]

        return key

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
        return getattr(self._config, "DEMO_USERNAME", "demo@example.com")

    @property
    def DEMO_PASSWORD(self):
        return getattr(self._config, "DEMO_PASSWORD", "demo123")

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
        return self._get_secret(
            "SCHOOLOGY_SECRET",
            vault_path="apps/backend/integrations/schoology/secret"
        )

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
        return self._get_secret(
            "PUSHER_SECRET",
            vault_path="apps/backend/integrations/pusher/secret"
        )

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
