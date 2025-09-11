"""
Environment Detection and Configuration Module

Controls when to use mock data vs real data based on environment.
Ensures production ALWAYS uses real data.
"""

import os
from enum import Enum
from typing import Dict, Any, Optional


class Environment(Enum):
    """Environment types"""
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TESTING = "testing"
    LOCAL = "local"


class EnvironmentConfig:
    """
    Central environment configuration management.
    
    Key Principle: Production ALWAYS uses real data.
    Development/Testing can opt-in to mock data.
    """
    
    def __init__(self):
        self._env = self._detect_environment()
        self._config = self._load_config()
    
    def _detect_environment(self) -> Environment:
        """
        Detect current environment from various signals.
        
        Priority order:
        1. ENVIRONMENT variable
        2. NODE_ENV variable (for compatibility)
        3. TESTING flag
        4. Default to development if uncertain
        """
        # Explicit environment variable takes precedence
        env_var = os.getenv("ENVIRONMENT", "").lower()
        if env_var:
            env_map = {
                "production": Environment.PRODUCTION,
                "prod": Environment.PRODUCTION,
                "staging": Environment.STAGING,
                "development": Environment.DEVELOPMENT,
                "dev": Environment.DEVELOPMENT,
                "testing": Environment.TESTING,
                "test": Environment.TESTING,
                "local": Environment.LOCAL
            }
            if env_var in env_map:
                return env_map[env_var]
        
        # Check NODE_ENV for compatibility
        node_env = os.getenv("NODE_ENV", "").lower()
        if node_env == "production":
            return Environment.PRODUCTION
        
        # Check if we're in testing mode
        if os.getenv("TESTING") == "true" or os.getenv("PYTEST_CURRENT_TEST"):
            return Environment.TESTING
        
        # Check for CI/CD environment
        if os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS"):
            return Environment.TESTING
        
        # Default to development (safe for local development)
        return Environment.DEVELOPMENT
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration based on environment"""
        base_config = {
            "use_mock_llm": False,
            "use_mock_database": False,
            "use_mock_services": False,
            "bypass_rate_limit": False,
            "debug_mode": False,
            "log_level": "INFO",
            "require_auth": True,
            "validate_ssl": True,
            "cache_enabled": True
        }
        
        # Environment-specific overrides
        env_configs = {
            Environment.PRODUCTION: {
                # Production NEVER uses mocks
                "use_mock_llm": False,
                "use_mock_database": False,
                "use_mock_services": False,
                "bypass_rate_limit": False,
                "debug_mode": False,
                "log_level": "WARNING",
                "require_auth": True,
                "validate_ssl": True,
                "cache_enabled": True
            },
            Environment.STAGING: {
                # Staging is like production but with more logging
                "use_mock_llm": False,
                "use_mock_database": False,
                "use_mock_services": False,
                "bypass_rate_limit": False,
                "debug_mode": False,
                "log_level": "INFO",
                "require_auth": True,
                "validate_ssl": True,
                "cache_enabled": True
            },
            Environment.DEVELOPMENT: {
                # Development can opt-in to mocks via env vars
                "use_mock_llm": os.getenv("USE_MOCK_LLM") == "true",
                "use_mock_database": os.getenv("USE_MOCK_DATABASE") == "true",
                "use_mock_services": os.getenv("USE_MOCK_SERVICES") == "true",
                "bypass_rate_limit": os.getenv("BYPASS_RATE_LIMIT") == "true",
                "debug_mode": True,
                "log_level": "DEBUG",
                "require_auth": os.getenv("REQUIRE_AUTH", "false") == "true",
                "validate_ssl": False,
                "cache_enabled": True
            },
            Environment.TESTING: {
                # Testing defaults to mocks unless explicitly disabled
                "use_mock_llm": os.getenv("USE_MOCK_LLM", "true") == "true",
                "use_mock_database": os.getenv("USE_MOCK_DATABASE", "true") == "true",
                "use_mock_services": os.getenv("USE_MOCK_SERVICES", "true") == "true",
                "bypass_rate_limit": True,
                "debug_mode": True,
                "log_level": "WARNING",
                "require_auth": False,
                "validate_ssl": False,
                "cache_enabled": False
            },
            Environment.LOCAL: {
                # Local is like development but with all mocks by default
                "use_mock_llm": os.getenv("USE_MOCK_LLM", "true") == "true",
                "use_mock_database": os.getenv("USE_MOCK_DATABASE", "false") == "true",
                "use_mock_services": os.getenv("USE_MOCK_SERVICES", "false") == "true",
                "bypass_rate_limit": True,
                "debug_mode": True,
                "log_level": "DEBUG",
                "require_auth": False,
                "validate_ssl": False,
                "cache_enabled": True
            }
        }
        
        # Merge base config with environment-specific config
        config = base_config.copy()
        config.update(env_configs.get(self._env, {}))
        
        # Allow explicit overrides for specific flags
        # BUT NEVER allow mocks in production
        if self._env != Environment.PRODUCTION:
            if os.getenv("FORCE_USE_MOCK_LLM") == "true":
                config["use_mock_llm"] = True
            if os.getenv("FORCE_USE_MOCK_DATABASE") == "true":
                config["use_mock_database"] = True
            if os.getenv("FORCE_USE_MOCK_SERVICES") == "true":
                config["use_mock_services"] = True
        
        return config
    
    @property
    def environment(self) -> Environment:
        """Get current environment"""
        return self._env
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self._env == Environment.PRODUCTION
    
    @property
    def is_staging(self) -> bool:
        """Check if running in staging"""
        return self._env == Environment.STAGING
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self._env in [Environment.DEVELOPMENT, Environment.LOCAL]
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing"""
        return self._env == Environment.TESTING
    
    @property
    def use_mock_llm(self) -> bool:
        """Should use mock LLM?"""
        # NEVER use mock in production, even if env var is set
        if self.is_production:
            return False
        return self._config["use_mock_llm"]
    
    @property
    def use_mock_database(self) -> bool:
        """Should use mock database?"""
        # NEVER use mock in production
        if self.is_production:
            return False
        return self._config["use_mock_database"]
    
    @property
    def use_mock_services(self) -> bool:
        """Should use mock external services?"""
        # NEVER use mock in production
        if self.is_production:
            return False
        return self._config["use_mock_services"]
    
    @property
    def use_real_data(self) -> bool:
        """Should use real data? (inverse of mocks)"""
        return not (self.use_mock_llm or self.use_mock_database or self.use_mock_services)
    
    @property
    def bypass_rate_limit(self) -> bool:
        """Should bypass rate limiting?"""
        # NEVER bypass in production
        if self.is_production:
            return False
        return self._config["bypass_rate_limit"]
    
    @property
    def debug_mode(self) -> bool:
        """Is debug mode enabled?"""
        return self._config["debug_mode"]
    
    @property
    def log_level(self) -> str:
        """Get log level"""
        return self._config["log_level"]
    
    @property
    def require_auth(self) -> bool:
        """Should require authentication?"""
        # ALWAYS require auth in production
        if self.is_production:
            return True
        return self._config["require_auth"]
    
    def get_config(self) -> Dict[str, Any]:
        """Get full configuration dictionary"""
        return self._config.copy()
    
    def validate_for_production(self) -> bool:
        """
        Validate configuration is safe for production.
        Returns True if safe, False otherwise.
        """
        if not self.is_production:
            return True
        
        # Production safety checks
        checks = [
            not self.use_mock_llm,
            not self.use_mock_database,
            not self.use_mock_services,
            not self.bypass_rate_limit,
            self.require_auth,
            self._config["validate_ssl"]
        ]
        
        return all(checks)
    
    def get_database_url(self) -> str:
        """Get appropriate database URL based on environment"""
        if self.use_mock_database:
            return "sqlite+aiosqlite:///:memory:"
        
        # Use real database URLs based on environment
        db_urls = {
            Environment.PRODUCTION: os.getenv("DATABASE_URL", ""),
            Environment.STAGING: os.getenv("STAGING_DATABASE_URL", os.getenv("DATABASE_URL", "")),
            Environment.DEVELOPMENT: os.getenv("DEV_DATABASE_URL", os.getenv("DATABASE_URL", "")),
            Environment.TESTING: os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///test.db"),
            Environment.LOCAL: os.getenv("LOCAL_DATABASE_URL", "sqlite+aiosqlite:///local.db")
        }
        
        return db_urls.get(self._env, "")
    
    def get_service_url(self, service: str) -> str:
        """Get appropriate service URL based on environment"""
        if self.use_mock_services:
            # Return mock service URLs
            mock_urls = {
                "fastapi": "http://mock-api:8008",
                "flask": "http://mock-flask:5001",
                "mcp": "ws://mock-mcp:9876",
                "roblox": "http://mock-roblox:64989"
            }
            return mock_urls.get(service, "http://mock-service")
        
        # Use real service URLs
        service_urls = {
            "fastapi": os.getenv("FASTAPI_URL", "http://127.0.0.1:8008"),
            "flask": os.getenv("FLASK_URL", "http://127.0.0.1:5001"),
            "mcp": os.getenv("MCP_URL", "ws://127.0.0.1:9876"),
            "roblox": os.getenv("ROBLOX_URL", "http://127.0.0.1:64989")
        }
        
        return service_urls.get(service, "")
    
    def __repr__(self) -> str:
        return f"<EnvironmentConfig env={self._env.value} use_real_data={self.use_real_data}>"


# Singleton instance
_env_config: Optional[EnvironmentConfig] = None


def get_environment_config() -> EnvironmentConfig:
    """Get or create the singleton environment configuration"""
    global _env_config
    if _env_config is None:
        _env_config = EnvironmentConfig()
    return _env_config


def is_production() -> bool:
    """Quick check if in production"""
    return get_environment_config().is_production


def is_development() -> bool:
    """Quick check if in development"""
    return get_environment_config().is_development


def is_testing() -> bool:
    """Quick check if in testing"""
    return get_environment_config().is_testing


def should_use_mock_llm() -> bool:
    """Check if should use mock LLM"""
    return get_environment_config().use_mock_llm


def should_use_real_data() -> bool:
    """Check if should use real data"""
    return get_environment_config().use_real_data


# Export main components
__all__ = [
    "Environment",
    "EnvironmentConfig",
    "get_environment_config",
    "is_production",
    "is_development",
    "is_testing",
    "should_use_mock_llm",
    "should_use_real_data"
]