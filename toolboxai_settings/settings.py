"""
ToolboxAI Settings Module

Configuration settings for the ToolboxAI Educational Platform.
These settings can be overridden via environment variables.

SECURITY NOTE: This module now includes secure JWT secret management
with automatic validation and generation of cryptographically secure secrets.
"""

import logging
import os
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

# Application Settings
APP_NAME = os.getenv("APP_NAME", "ToolboxAI-Roblox-Environment")
VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes", "on")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
ENV_NAME = os.getenv("ENV_NAME", "development")

# Server Configuration
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8009"))
FLASK_PORT = int(os.getenv("FLASK_PORT", "5001"))
MCP_PORT = int(os.getenv("MCP_PORT", "9876"))

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://eduplatform:eduplatform2024@localhost/educational_platform_dev")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
SUPABASE_DB_HOST = os.getenv("SUPABASE_DB_HOST", "localhost")
SUPABASE_DB_PORT = int(os.getenv("SUPABASE_DB_PORT", "54322"))
SUPABASE_DB_NAME = os.getenv("SUPABASE_DB_NAME", "postgres")
SUPABASE_DB_USER = os.getenv("SUPABASE_DB_USER", "postgres")
SUPABASE_DB_PASS = os.getenv("SUPABASE_DB_PASS", "postgres")
SUPABASE_AGENT_SCHEMA = os.getenv("SUPABASE_AGENT_SCHEMA", "public")
SUPABASE_ENABLE_REALTIME = os.getenv("SUPABASE_ENABLE_REALTIME", "true").lower() == "true"
SUPABASE_ENABLE_RLS = os.getenv("SUPABASE_ENABLE_RLS", "true").lower() == "true"
SUPABASE_CONNECTION_TIMEOUT = int(os.getenv("SUPABASE_CONNECTION_TIMEOUT", "30"))
SUPABASE_MAX_RETRIES = int(os.getenv("SUPABASE_MAX_RETRIES", "3"))
SUPABASE_RETRY_DELAY = int(os.getenv("SUPABASE_RETRY_DELAY", "5"))

# External API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SCHOOLOGY_KEY = os.getenv("SCHOOLOGY_KEY", "")
SCHOOLOGY_SECRET = os.getenv("SCHOOLOGY_SECRET", "")
CANVAS_TOKEN = os.getenv("CANVAS_TOKEN", "")

# JWT Security Configuration with Enhanced Security
def _initialize_jwt_security():
    """
    Initialize secure JWT secret management with validation and auto-generation

    This function provides multiple layers of security:
    1. Validates environment variables for security
    2. Generates secure secrets for development
    3. Prevents weak secrets in production

    Returns:
        str: Validated, secure JWT secret

    Raises:
        ValueError: If no secure secret can be established
    """
    logger = logging.getLogger(__name__)

    # Always use environment validation to avoid circular imports
    # The JWT security modules can validate independently when they're imported
    return _validate_environment_jwt_secret()

def _validate_environment_jwt_secret():
    """
    Validate and secure JWT secret from environment variables

    Returns:
        str: Validated JWT secret

    Raises:
        ValueError: If secret is invalid or insecure
    """
    logger = logging.getLogger(__name__)

    # Get environment secret
    env_secret = os.getenv("JWT_SECRET_KEY", "")

    # Check for missing or default secret
    if not env_secret or env_secret in [
        "dev-secret-key-change-in-production",
        "your-secret-key-change-in-production",
        "change-me",
        "default",
        "secret",
        "key"
    ]:
        logger.error("CRITICAL SECURITY ISSUE: No secure JWT secret configured!")

        if ENV_NAME.lower() in ('development', 'dev', 'local'):
            # Generate secure development secret
            logger.warning("Generating secure development JWT secret...")
            dev_secret = _generate_development_secret()
            logger.warning("DEVELOPMENT MODE: Auto-generated secure JWT secret")
            logger.warning(f"Add to your .env file: JWT_SECRET_KEY={dev_secret}")
            logger.warning("DO NOT use this auto-generated secret in production!")
            return dev_secret
        else:
            raise ValueError(
                "PRODUCTION SECURITY ERROR: No secure JWT secret configured! "
                "Set JWT_SECRET_KEY environment variable with a cryptographically secure secret "
                "(minimum 32 characters, high entropy, no predictable patterns)"
            )

    # Validate secret strength
    validation_errors = []

    # Length check
    if len(env_secret) < 32:
        validation_errors.append(f"Secret too short: {len(env_secret)} characters (minimum: 32)")

    # Weak pattern check
    weak_patterns = [
        'password', 'secret', 'key', 'token', '12345', 'admin',
        'test', 'demo', 'dev', 'prod', 'staging', 'change',
        'your-secret', 'default', 'example', 'sample'
    ]
    found_patterns = [pattern for pattern in weak_patterns if pattern in env_secret.lower()]
    if found_patterns:
        validation_errors.append(f"Contains weak patterns: {', '.join(found_patterns)}")

    # Character diversity check
    unique_chars = len(set(env_secret))
    if unique_chars < 10:
        validation_errors.append(f"Low character diversity: {unique_chars} unique characters (minimum: 10)")

    # Entropy check (basic)
    if len(env_secret) == len(set(env_secret)) and len(env_secret) < 40:
        # All unique characters but short - might be weak
        logger.warning("JWT secret has unusual pattern - verify it's cryptographically secure")

    if validation_errors:
        error_msg = "JWT secret validation failed: " + "; ".join(validation_errors)

        if ENV_NAME.lower() in ('development', 'dev', 'local'):
            logger.error(error_msg)
            logger.warning("Development mode: Generating secure replacement...")
            dev_secret = _generate_development_secret()
            logger.warning(f"Replace your JWT_SECRET_KEY with: {dev_secret}")
            return dev_secret
        else:
            logger.error(error_msg)
            raise ValueError(f"PRODUCTION SECURITY ERROR: {error_msg}")

    logger.info("JWT secret validation passed")
    return env_secret

def _generate_development_secret():
    """Generate a cryptographically secure development JWT secret"""
    import secrets
    import string

    # Use a mix of characters for high entropy
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"

    # Generate 64-character secret with high entropy
    return ''.join(secrets.choice(alphabet) for _ in range(64))

def _log_jwt_security_status():
    """Log JWT security status for monitoring"""
    logger = logging.getLogger(__name__)

    secret_length = len(JWT_SECRET_KEY) if JWT_SECRET_KEY else 0
    unique_chars = len(set(JWT_SECRET_KEY)) if JWT_SECRET_KEY else 0

    logger.info(f"JWT Security Status:")
    logger.info(f"  Secret Length: {secret_length} characters")
    logger.info(f"  Character Diversity: {unique_chars} unique characters")
    logger.info(f"  Environment: {ENV_NAME}")

    if ENV_NAME.lower() not in ('development', 'dev', 'local'):
        # Production environment - log security reminder
        logger.info("  Production JWT security active")
        logger.info("  Secret source: Environment variable")
        logger.info("  Next rotation recommended: Within 90 days")

# Initialize JWT secret with enhanced security
try:
    JWT_SECRET_KEY = _initialize_jwt_security()
    _log_jwt_security_status()

except Exception as e:
    # Final emergency fallback
    logger = logging.getLogger(__name__)
    logger.critical(f"CRITICAL: JWT security initialization completely failed: {e}")

    if ENV_NAME.lower() in ('development', 'dev', 'local'):
        logger.warning("Emergency fallback: Using minimal development secret")
        JWT_SECRET_KEY = _generate_development_secret()
        logger.warning("This is an emergency fallback - fix JWT security configuration!")
    else:
        logger.critical("PRODUCTION FAILURE: Cannot establish secure JWT secret")
        raise ValueError(f"PRODUCTION SECURITY FAILURE: {e}")

# JWT Algorithm and Expiration
JWT_ALGORITHM = "HS256"
# Following 2025 OAuth 3.0 best practices: 15-minute access tokens
JWT_EXPIRATION_HOURS = 0.25  # 15 minutes (0.25 hours)

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

# CORS Settings - Secure configuration based on environment
def _get_cors_origins():
    """Get CORS allowed origins based on environment"""
    cors_env = os.getenv("ALLOWED_ORIGINS", "")

    if cors_env:
        # Use environment variable if set
        origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]
    elif ENV_NAME.lower() in ('development', 'dev', 'local', 'testing'):
        # Development: Allow common local development ports
        origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:5175",
            "http://127.0.0.1:5175",
            "http://localhost:5176",
            "http://127.0.0.1:5176",
            "http://localhost:5177",
            "http://127.0.0.1:5177",
            "http://localhost:5178",
            "http://127.0.0.1:5178",
            "http://localhost:5179",
            "http://127.0.0.1:5179",
            "http://localhost:5180",
            "http://127.0.0.1:5180",
            "http://localhost:8009",
            "http://127.0.0.1:8009",
            "http://localhost:8009",
            # Clerk Authentication Domains (2025)
            "https://casual-firefly-39.clerk.accounts.dev",
            "https://casual-firefly-39.accounts.dev",
            "https://clerk.casual-firefly-39.lcl.dev",
            "https://accounts.clerk.dev",
            "http://127.0.0.1:8009",
        ]
    else:
        # Production: Must be explicitly configured
        origins = []
        logger = logging.getLogger(__name__)
        logger.error("CORS: No allowed origins configured for production!")
        logger.error("Set ALLOWED_ORIGINS environment variable with comma-separated list of allowed origins")

    # Validate origins - no wildcards in production
    validated_origins = []
    for origin in origins:
        if origin == "*":
            if ENV_NAME.lower() not in ('development', 'dev', 'local'):
                logger = logging.getLogger(__name__)
                logger.error("CORS: Wildcard (*) not allowed in production!")
                continue
        validated_origins.append(origin)

    return validated_origins

ALLOWED_ORIGINS = _get_cors_origins()

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

def validate_jwt_security() -> Dict[str, Any]:
    """Validate JWT security configuration."""
    validation_result = {
        'secret_configured': bool(JWT_SECRET_KEY),
        'secret_length': len(JWT_SECRET_KEY) if JWT_SECRET_KEY else 0,
        'meets_minimum_length': len(JWT_SECRET_KEY) >= 32 if JWT_SECRET_KEY else False,
        'environment': ENV_NAME,
        'is_secure': False,
        'using_fallback': True  # Since we're using environment validation
    }

    if JWT_SECRET_KEY:
        # Check for weak patterns
        weak_patterns = ['dev-secret', 'change-in-production', 'your-secret', 'default']
        has_weak_pattern = any(pattern in JWT_SECRET_KEY.lower() for pattern in weak_patterns)
        validation_result['has_weak_pattern'] = has_weak_pattern
        validation_result['is_secure'] = (
            validation_result['meets_minimum_length'] and
            not has_weak_pattern
        )

    return validation_result

def rotate_jwt_secret() -> bool:
    """Rotate JWT secret (placeholder for actual implementation)."""
    logger = logging.getLogger(__name__)
    logger.warning("JWT secret rotation requested - manual update required")
    logger.warning("1. Generate new secret using: python apps/backend/core/security/jwt_cli.py generate")
    logger.warning("2. Update environment variable: JWT_SECRET_KEY")
    logger.warning("3. Restart application")
    return False

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

# Security validation functions
def validate_jwt_security() -> Dict[str, Any]:
    """
    Validate current JWT security configuration

    Returns:
        Dict containing validation results
    """
    try:
        from apps.backend.core.security.jwt import get_jwt_security_manager

        manager = get_jwt_security_manager()
        if manager:
            return manager.get_security_status()
    except ImportError:
        pass

    # Fallback validation
    return {
        'secret_configured': bool(JWT_SECRET_KEY),
        'secret_length': len(JWT_SECRET_KEY) if JWT_SECRET_KEY else 0,
        'environment': ENV_NAME,
        'using_fallback': True
    }

def rotate_jwt_secret() -> bool:
    """
    Rotate JWT secret (if advanced security system is available)

    Returns:
        bool: True if rotation succeeded
    """
    try:
        from apps.backend.core.security.jwt import get_jwt_security_manager

        manager = get_jwt_security_manager()
        if manager:
            success, report = manager.rotate_secret(force=True)
            return success
    except ImportError:
        logger = logging.getLogger(__name__)
        logger.warning("Advanced JWT security not available for rotation")

    return False

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

class SupabaseConfig:
    """Supabase configuration."""
    def __init__(self):
        self.url = SUPABASE_URL
        self.anon_key = SUPABASE_ANON_KEY
        self.service_role_key = SUPABASE_SERVICE_ROLE_KEY
        self.jwt_secret = SUPABASE_JWT_SECRET
        self.db_host = SUPABASE_DB_HOST
        self.db_port = SUPABASE_DB_PORT
        self.db_name = SUPABASE_DB_NAME
        self.db_user = SUPABASE_DB_USER
        self.db_pass = SUPABASE_DB_PASS
        self.agent_schema = SUPABASE_AGENT_SCHEMA
        self.enable_realtime = SUPABASE_ENABLE_REALTIME
        self.enable_rls = SUPABASE_ENABLE_RLS
        self.connection_timeout = SUPABASE_CONNECTION_TIMEOUT
        self.max_retries = SUPABASE_MAX_RETRIES
        self.retry_delay = SUPABASE_RETRY_DELAY

    def is_configured(self) -> bool:
        """Check if Supabase is properly configured."""
        return bool(self.url and self.anon_key)

    def get_database_url(self) -> str:
        """Get PostgreSQL connection URL for direct database access."""
        return f"postgresql://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}"

class Settings:
    """Settings class with attributes for compatibility."""
    def __init__(self):
        # Copy all module-level variables as attributes
        self.app_name = APP_NAME
        self.version = VERSION
        self.debug = DEBUG
        self.env_name = ENV_NAME
        self.environment = ENVIRONMENT
        self.api_host = API_HOST
        self.api_port = API_PORT
        self.flask_port = FLASK_PORT
        self.mcp_port = MCP_PORT
        self.database_url = DATABASE_URL
        self.redis_url = REDIS_URL

        # Supabase configuration
        self.supabase_url = SUPABASE_URL
        self.supabase_anon_key = SUPABASE_ANON_KEY
        self.supabase_service_role_key = SUPABASE_SERVICE_ROLE_KEY
        self.supabase_jwt_secret = SUPABASE_JWT_SECRET
        self.supabase_db_host = SUPABASE_DB_HOST
        self.supabase_db_port = SUPABASE_DB_PORT
        self.supabase_db_name = SUPABASE_DB_NAME
        self.supabase_db_user = SUPABASE_DB_USER
        self.supabase_db_pass = SUPABASE_DB_PASS
        self.supabase_agent_schema = SUPABASE_AGENT_SCHEMA
        self.supabase_enable_realtime = SUPABASE_ENABLE_REALTIME
        self.supabase_enable_rls = SUPABASE_ENABLE_RLS
        self.supabase_connection_timeout = SUPABASE_CONNECTION_TIMEOUT
        self.supabase_max_retries = SUPABASE_MAX_RETRIES
        self.supabase_retry_delay = SUPABASE_RETRY_DELAY

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
        self.TESTING = TESTING  # Uppercase for compatibility
        self.test_database_url = TEST_DATABASE_URL
        self.enable_real_data = ENABLE_REAL_DATA
        self.enable_ai_generation = ENABLE_AI_GENERATION
        self.enable_roblox_integration = ENABLE_ROBLOX_INTEGRATION
        self.allowed_origins = ALLOWED_ORIGINS
        self.cors_origins = ALLOWED_ORIGINS  # Alias for compatibility
        self.rate_limit_per_minute = RATE_LIMIT_PER_MINUTE
        self.cache_ttl_seconds = CACHE_TTL_SECONDS

        # Demo Authentication
        self.DEMO_USERNAME = os.getenv("DEMO_USERNAME", "demo@example.com")
        self.DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "demo123")
        self.demo_username = self.DEMO_USERNAME  # lowercase alias
        self.demo_password = self.DEMO_PASSWORD  # lowercase alias

        # Nested configurations
        self.llm = LLMConfig()
        self.educational = EducationalConfig()
        self.service_urls = ServiceURLsConfig()
        self.supabase = SupabaseConfig()

        # Additional compatibility attributes
        self.ENV_NAME = ENV_NAME
        self.ENVIRONMENT = ENVIRONMENT
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
        self.JWT_EXPIRATION_HOURS = JWT_EXPIRATION_HOURS
        self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = JWT_EXPIRATION_HOURS * 60  # Convert hours to minutes
        # Following 2025 OAuth 3.0 best practices: shorter refresh tokens with rotation
        self.JWT_REFRESH_TOKEN_EXPIRE_DAYS = 1  # 1 day refresh token expiry with rotation

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

    def get_supabase_config(self) -> Dict[str, Any]:
        """Get Supabase configuration dictionary."""
        return {
            "url": self.supabase_url,
            "anon_key": self.supabase_anon_key,
            "service_role_key": self.supabase_service_role_key,
            "jwt_secret": self.supabase_jwt_secret,
            "db_host": self.supabase_db_host,
            "db_port": self.supabase_db_port,
            "db_name": self.supabase_db_name,
            "db_user": self.supabase_db_user,
            "db_pass": self.supabase_db_pass,
            "agent_schema": self.supabase_agent_schema,
            "enable_realtime": self.supabase_enable_realtime,
            "enable_rls": self.supabase_enable_rls,
            "connection_timeout": self.supabase_connection_timeout,
            "max_retries": self.supabase_max_retries,
            "retry_delay": self.supabase_retry_delay
        }

    def is_supabase_configured(self) -> bool:
        """Check if Supabase is properly configured."""
        return bool(self.supabase_url and self.supabase_anon_key)

    def get_supabase_database_url(self) -> str:
        """Get PostgreSQL connection URL for direct database access to Supabase."""
        return f"postgresql://{self.supabase_db_user}:{self.supabase_db_pass}@{self.supabase_db_host}:{self.supabase_db_port}/{self.supabase_db_name}"

    def validate_jwt_security(self) -> Dict[str, Any]:
        """Validate JWT security configuration"""
        return validate_jwt_security()

    def rotate_jwt_secret(self) -> bool:
        """Rotate JWT secret"""
        return rotate_jwt_secret()

# Create a singleton settings instance
settings = Settings()

# Export module-level attributes for backward compatibility
env_name = ENV_NAME
service_urls = SERVICE_URLS

# Log security status on module import
_logger = logging.getLogger(__name__)
_logger.info("ToolboxAI settings loaded with enhanced JWT security")

# Validate security on import in production
if ENV_NAME.lower() not in ('development', 'dev', 'local', 'testing', 'test'):
    security_status = validate_jwt_security()
    if not security_status.get('secret_configured', False):
        _logger.critical("PRODUCTION ALERT: JWT security validation failed!")
