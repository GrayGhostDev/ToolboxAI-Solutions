"""
Comprehensive Environment Configuration Module for ToolboxAI Solutions

This module provides all environment-related configuration for the entire application,
including database connections, API keys, service URLs, feature flags, and runtime settings.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

# Configure logger
logger = logging.getLogger(__name__)


class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class DatabaseType(Enum):
    """Database connection types"""
    EDUCATION = "education"
    ROBLOX = "roblox"
    GHOST = "ghost"
    DEVELOPMENT = "development"
    TESTING = "testing"


@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False
    connect_timeout: int = 30
    pool_pre_ping: bool = True
    pool_recycle: int = 3600


@dataclass
class RedisConfig:
    """Redis configuration settings"""
    url: str
    decode_responses: bool = True
    max_connections: int = 50
    socket_connect_timeout: int = 5
    socket_timeout: int = 5
    retry_on_timeout: bool = True


@dataclass
class AgentConfig:
    """Agent configuration settings"""
    max_agents: int = 10
    agent_timeout: int = 300
    max_retries: int = 3
    use_real_data: bool = False
    enable_caching: bool = True
    cache_ttl: int = 3600
    enable_monitoring: bool = True
    log_level: str = "INFO"


@dataclass
class LLMConfig:
    """LLM configuration settings"""
    provider: str = "openai"
    model: str = "gpt-4"
    default_model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 60
    retry_attempts: int = 3


@dataclass
class RobloxConfig:
    """Roblox integration configuration"""
    plugin_port: int = 64989
    max_parts: int = 10000
    max_scripts: int = 100
    terrain_size_limits: Dict[str, int] = field(default_factory=lambda: {
        "small": 200,
        "medium": 500,
        "large": 1000,
        "xlarge": 2000
    })
    api_key: Optional[str] = None
    universe_id: Optional[str] = None
    webhook_secret: Optional[str] = None


@dataclass
class EducationalConfig:
    """Educational content configuration"""
    supported_subjects: List[str] = field(default_factory=lambda: [
        "Mathematics", "Science", "History", "English", "Art",
        "Geography", "Computer Science", "Physics", "Chemistry", "Biology"
    ])
    grade_levels: List[int] = field(default_factory=lambda: list(range(1, 13)))
    max_quiz_questions: int = 20
    default_quiz_questions: int = 5
    bloom_levels: List[str] = field(default_factory=lambda: [
        "Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"
    ])
    difficulty_levels: List[str] = field(default_factory=lambda: [
        "Easy", "Medium", "Hard", "Expert"
    ])


@dataclass
class ServiceURLs:
    """Service URLs configuration"""
    api_base: str = "http://127.0.0.1:8008"
    dashboard_url: str = "http://localhost:5179"
    flask_bridge: str = "http://127.0.0.1:5001"
    mcp_server: str = "ws://localhost:9876"
    websocket_url: str = "ws://127.0.0.1:8008"
    pusher_auth_endpoint: str = "/pusher/auth"
    roblox_plugin_url: str = "http://localhost:64989"
    pusher_url: str = ""
    sentry_dsn: Optional[str] = None
    langchain_hub_url: str = "https://api.smith.langchain.com"
    openai_api_url: str = "https://api.openai.com/v1"


class EnvironmentConfig:
    """Main environment configuration class"""
    
    def __init__(self):
        """Initialize environment configuration"""
        # Load environment from env variable or default to development
        self.env_name = os.getenv("ENVIRONMENT", "development").lower()
        self.environment = Environment(self.env_name)
        
        # Load .env file if exists
        self._load_env_file()
        
        # Initialize configurations
        self._init_database_configs()
        self._init_redis_config()
        self._init_agent_config()
        self._init_llm_config()
        self._init_roblox_config()
        self._init_educational_config()
        self._init_service_urls()
        self._init_api_keys()
        self._init_feature_flags()
        
    def _load_env_file(self):
        """Load .env file if it exists"""
        env_files = [
            Path(".env"),
            Path(".env.local"),
            Path(f".env.{self.env_name}"),
            Path("config") / ".env",
            Path("config") / f".env.{self.env_name}"
        ]
        
        for env_file in env_files:
            if env_file.exists():
                try:
                    from dotenv import load_dotenv
                    load_dotenv(env_file)
                    logger.info(f"Loaded environment from {env_file}")
                    break
                except ImportError:
                    logger.warning("python-dotenv not installed, skipping .env file loading")
                    break
                    
    def _init_database_configs(self):
        """Initialize database configurations"""
        self.databases = {}
        
        # Main database
        self.databases[DatabaseType.EDUCATION] = DatabaseConfig(
            url=os.getenv("DATABASE_URL", "postgresql://eduplatform:eduplatform2024@localhost:5432/educational_platform_dev"),
            pool_size=int(os.getenv("DATABASE_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "20")),
            echo=self.environment == Environment.DEVELOPMENT
        )
        
        # Roblox database
        self.databases[DatabaseType.ROBLOX] = DatabaseConfig(
            url=os.getenv("ROBLOX_DATABASE_URL", os.getenv("DATABASE_URL", "sqlite:///./toolboxai_roblox.db")),
            pool_size=5,
            max_overflow=10
        )
        
        # Ghost CMS database
        self.databases[DatabaseType.GHOST] = DatabaseConfig(
            url=os.getenv("GHOST_DATABASE_URL", "sqlite:///./ghost.db"),
            pool_size=3,
            max_overflow=5
        )
        
        # Development database
        self.databases[DatabaseType.DEVELOPMENT] = DatabaseConfig(
            url=os.getenv("DEV_DATABASE_URL", "sqlite:///./development.db"),
            pool_size=5,
            max_overflow=10,
            echo=True
        )
        
        # Testing database
        self.databases[DatabaseType.TESTING] = DatabaseConfig(
            url=os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:"),
            pool_size=1,
            max_overflow=0
        )
        
    def _init_redis_config(self):
        """Initialize Redis configuration"""
        self.redis = RedisConfig(
            url=os.getenv("REDIS_URL", "redis://localhost:6379"),
            decode_responses=True,
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
        )
        
    def _init_agent_config(self):
        """Initialize agent configuration"""
        self.agents = AgentConfig(
            max_agents=int(os.getenv("MAX_AGENTS", "10")),
            agent_timeout=int(os.getenv("AGENT_TIMEOUT", "300")),
            max_retries=int(os.getenv("AGENT_MAX_RETRIES", "3")),
            use_real_data=os.getenv("USE_REAL_DATA", "false").lower() == "true",
            enable_caching=os.getenv("ENABLE_AGENT_CACHING", "true").lower() == "true",
            cache_ttl=int(os.getenv("AGENT_CACHE_TTL", "3600")),
            enable_monitoring=os.getenv("ENABLE_AGENT_MONITORING", "true").lower() == "true",
            log_level=os.getenv("AGENT_LOG_LEVEL", "INFO")
        )
        
    def _init_llm_config(self):
        """Initialize LLM configuration"""
        self.llm = LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("MAX_TOKENS", "4000")),
            top_p=float(os.getenv("LLM_TOP_P", "1.0")),
            frequency_penalty=float(os.getenv("LLM_FREQUENCY_PENALTY", "0.0")),
            presence_penalty=float(os.getenv("LLM_PRESENCE_PENALTY", "0.0")),
            timeout=int(os.getenv("LLM_TIMEOUT", "60")),
            retry_attempts=int(os.getenv("LLM_RETRY_ATTEMPTS", "3"))
        )
        
    def _init_roblox_config(self):
        """Initialize Roblox configuration"""
        terrain_limits_str = os.getenv("ROBLOX_TERRAIN_SIZE_LIMITS", "{}")
        try:
            terrain_limits = json.loads(terrain_limits_str) if terrain_limits_str else {}
        except json.JSONDecodeError:
            terrain_limits = {}
            
        self.roblox = RobloxConfig(
            plugin_port=int(os.getenv("ROBLOX_PLUGIN_PORT", "64989")),
            max_parts=int(os.getenv("ROBLOX_MAX_PARTS", "10000")),
            max_scripts=int(os.getenv("ROBLOX_MAX_SCRIPTS", "100")),
            terrain_size_limits=terrain_limits or {
                "small": 200, "medium": 500, "large": 1000, "xlarge": 2000
            },
            api_key=os.getenv("ROBLOX_API_KEY"),
            universe_id=os.getenv("ROBLOX_UNIVERSE_ID"),
            webhook_secret=os.getenv("ROBLOX_WEBHOOK_SECRET")
        )
        
    def _init_educational_config(self):
        """Initialize educational configuration"""
        subjects_str = os.getenv("SUPPORTED_SUBJECTS", "")
        subjects = [s.strip() for s in subjects_str.split(",")] if subjects_str else None
        
        grades_str = os.getenv("GRADE_LEVELS", "")
        grades = [int(g.strip()) for g in grades_str.split(",")] if grades_str else None
        
        self.educational = EducationalConfig(
            supported_subjects=subjects or EducationalConfig().supported_subjects,
            grade_levels=grades or EducationalConfig().grade_levels,
            max_quiz_questions=int(os.getenv("MAX_QUIZ_QUESTIONS", "20")),
            default_quiz_questions=int(os.getenv("DEFAULT_QUIZ_QUESTIONS", "5"))
        )
        
    def _init_service_urls(self):
        """Initialize service URLs"""
        self.service_urls = ServiceURLs(
            api_base=os.getenv("API_BASE_URL", "http://127.0.0.1:8008"),
            dashboard_url=os.getenv("DASHBOARD_URL", "http://localhost:5179"),
            flask_bridge=os.getenv("FLASK_BRIDGE_URL", "http://127.0.0.1:5001"),
            mcp_server=os.getenv("MCP_SERVER_URL", "ws://localhost:9876"),
            websocket_url=os.getenv("WEBSOCKET_URL", "ws://127.0.0.1:8008"),
            pusher_auth_endpoint=os.getenv("PUSHER_AUTH_ENDPOINT", "/pusher/auth")
        )
        
    def _init_api_keys(self):
        """Initialize API keys"""
        self.api_keys = {
            "openai": os.getenv("OPENAI_API_KEY"),
            "langchain": os.getenv("LANGCHAIN_API_KEY"),
            "langsmith": os.getenv("LANGSMITH_API_KEY"),
            "pusher_app_id": os.getenv("PUSHER_APP_ID"),
            "pusher_key": os.getenv("PUSHER_KEY"),
            "pusher_secret": os.getenv("PUSHER_SECRET"),
            "pusher_cluster": os.getenv("PUSHER_CLUSTER", "us2"),
            "stripe_public": os.getenv("STRIPE_PUBLIC_KEY"),
            "stripe_secret": os.getenv("STRIPE_SECRET_KEY"),
            "stripe_webhook": os.getenv("STRIPE_WEBHOOK_SECRET"),
            "sentry_dsn": os.getenv("SENTRY_DSN"),
            "ghost_admin": os.getenv("GHOST_ADMIN_API_KEY"),
            "ghost_content": os.getenv("GHOST_CONTENT_API_KEY"),
            "schoology_key": os.getenv("SCHOOLOGY_KEY"),
            "schoology_secret": os.getenv("SCHOOLOGY_SECRET"),
            "canvas_token": os.getenv("CANVAS_TOKEN"),
            "google_classroom_client_id": os.getenv("GOOGLE_CLASSROOM_CLIENT_ID")
        }
        
    def _init_feature_flags(self):
        """Initialize feature flags"""
        self.features = {
            "enable_websocket": os.getenv("ENABLE_WEBSOCKET", "true").lower() == "true",
            "enable_pusher": os.getenv("PUSHER_ENABLED", "true").lower() == "true",
            "enable_gamification": os.getenv("ENABLE_GAMIFICATION", "true").lower() == "true",
            "enable_analytics": os.getenv("ENABLE_ANALYTICS", "true").lower() == "true",
            "enable_monitoring": os.getenv("ENABLE_MONITORING", "true").lower() == "true",
            "enable_sentry": os.getenv("SENTRY_ENABLED", "false").lower() == "true",
            "enable_rate_limiting": os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
            "enable_caching": os.getenv("ENABLE_CACHING", "true").lower() == "true",
            "debug_mode": os.getenv("DEBUG", "false").lower() == "true",
            "testing_mode": os.getenv("TESTING_MODE", "false").lower() == "true",
            "bypass_rate_limit_in_tests": os.getenv("BYPASS_RATE_LIMIT_IN_TESTS", "true").lower() == "true",
            "coppa_compliance": os.getenv("COPPA_COMPLIANCE", "true").lower() == "true",
            "ferpa_compliance": os.getenv("FERPA_COMPLIANCE", "true").lower() == "true",
            "gdpr_compliance": os.getenv("GDPR_COMPLIANCE", "true").lower() == "true"
        }
        
    def get_database_config(self, db_type: Union[DatabaseType, str] = DatabaseType.EDUCATION) -> DatabaseConfig:
        """Get database configuration by type"""
        if isinstance(db_type, str):
            db_type = DatabaseType(db_type.lower())
        return self.databases.get(db_type, self.databases[DatabaseType.EDUCATION])
        
    def get_database_url(self, db_type: Union[DatabaseType, str] = DatabaseType.EDUCATION) -> str:
        """Get database URL by type"""
        config = self.get_database_config(db_type)
        return config.url
    
    @property
    def DATABASE_URL(self) -> str:
        """Get default database URL (backward compatibility)"""
        return self.get_database_url(DatabaseType.EDUCATION)
    
    @property
    def JWT_SECRET_KEY(self) -> str:
        """Get JWT secret key"""
        return self.api_keys.get("jwt_secret", "default-jwt-secret-key-change-in-production")
    
    @property
    def JWT_ALGORITHM(self) -> str:
        """Get JWT algorithm"""
        return "HS256"
    
    @property
    def services(self) -> ServiceURLs:
        """Alias for service_urls for backward compatibility"""
        return self.service_urls
    
    @property
    def REDIS_URL(self) -> str:
        """Get Redis URL (backward compatibility)"""
        return self.redis.url
    
    @property
    def FASTAPI_HOST(self) -> str:
        """Get FastAPI host (backward compatibility)"""
        return "127.0.0.1"
    
    @property
    def FASTAPI_PORT(self) -> int:
        """Get FastAPI port (backward compatibility)"""
        return 8008
    
    @property
    def use_mock_data(self) -> bool:
        """Check if mock data should be used"""
        return self.environment == Environment.TESTING or os.getenv("USE_MOCK_DATA", "false").lower() == "true"
    
    @property
    def use_mock_database(self) -> bool:
        """Check if mock database should be used"""
        return self.environment == Environment.TESTING or os.getenv("USE_MOCK_DATABASE", "false").lower() == "true"
    
    @property
    def use_mock_llm(self) -> bool:
        """Check if mock LLM should be used"""
        return self.environment == Environment.TESTING or os.getenv("USE_MOCK_LLM", "false").lower() == "true"
        
    def get_redis_config(self) -> RedisConfig:
        """Get Redis configuration"""
        return self.redis
        
    def get_redis_url(self) -> str:
        """Get Redis URL"""
        return self.redis.url
        
    def get_agent_config(self) -> AgentConfig:
        """Get agent configuration"""
        return self.agents
        
    def get_llm_config(self) -> LLMConfig:
        """Get LLM configuration"""
        return self.llm
        
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a service"""
        return self.api_keys.get(service)
        
    def get_service_url(self, service: str) -> Optional[str]:
        """Get service URL by name"""
        service_map = {
            "api": self.services.api_base,
            "api_base": self.services.api_base,
            "dashboard": self.services.dashboard_url,
            "flask": self.services.flask_bridge,
            "flask_bridge": self.services.flask_bridge,
            "mcp": self.services.mcp_server,
            "mcp_server": self.services.mcp_server,
            "websocket": self.services.websocket_url,
            "ws": self.services.websocket_url,
            "pusher_auth": self.services.pusher_auth_endpoint
        }
        return service_map.get(service.lower())
        
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        return self.features.get(feature, False)
        
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == Environment.PRODUCTION
        
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == Environment.DEVELOPMENT
        
    def is_testing(self) -> bool:
        """Check if running in testing mode"""
        return self.environment == Environment.TESTING or self.features.get("testing_mode", False)
        
    def should_use_real_data(self) -> bool:
        """Check if real data should be used"""
        return self.agents.use_real_data and not self.is_testing()
        
    def get_log_level(self) -> str:
        """Get log level"""
        return os.getenv("LOG_LEVEL", "INFO" if self.is_production() else "DEBUG")
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "environment": self.env_name,
            "databases": {
                db_type.value: {
                    "url": config.url,
                    "pool_size": config.pool_size,
                    "max_overflow": config.max_overflow
                }
                for db_type, config in self.databases.items()
            },
            "redis": {
                "url": self.redis.url,
                "max_connections": self.redis.max_connections
            },
            "agents": {
                "max_agents": self.agents.max_agents,
                "use_real_data": self.agents.use_real_data,
                "enable_caching": self.agents.enable_caching
            },
            "llm": {
                "provider": self.llm.provider,
                "model": self.llm.model,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens
            },
            "roblox": {
                "plugin_port": self.roblox.plugin_port,
                "max_parts": self.roblox.max_parts,
                "universe_id": self.roblox.universe_id
            },
            "educational": {
                "subjects": self.educational.supported_subjects,
                "grade_levels": self.educational.grade_levels,
                "max_quiz_questions": self.educational.max_quiz_questions
            },
            "services": {
                "api_base": self.services.api_base,
                "dashboard_url": self.services.dashboard_url,
                "flask_bridge": self.services.flask_bridge
            },
            "features": self.features
        }


# Global singleton instance
_config_instance: Optional[EnvironmentConfig] = None


def get_environment_config() -> EnvironmentConfig:
    """Get the global environment configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = EnvironmentConfig()
    return _config_instance


def should_use_real_data() -> bool:
    """Check if real data should be used"""
    config = get_environment_config()
    return config.should_use_real_data()


def get_database_url(db_type: str = "education") -> str:
    """Get database URL for a specific type"""
    config = get_environment_config()
    return config.get_database_url(db_type)


def get_redis_url() -> str:
    """Get Redis URL"""
    config = get_environment_config()
    return config.redis.url


def get_api_key(service: str) -> Optional[str]:
    """Get API key for a service"""
    config = get_environment_config()
    return config.get_api_key(service)


def is_production() -> bool:
    """Check if running in production"""
    config = get_environment_config()
    return config.is_production()


def is_development() -> bool:
    """Check if running in development"""
    config = get_environment_config()
    return config.is_development()


def is_testing() -> bool:
    """Check if running in testing mode"""
    config = get_environment_config()
    return config.is_testing()


async def get_async_session(database: str = "education"):
    """Get async database session (compatibility method)"""
    # This is a compatibility method - actual implementation should be in database layer
    from core.database.connection_manager import get_async_session as _get_async_session
    async for session in _get_async_session(database):
        yield session


def get_session(database: str = "education"):
    """Get database session (compatibility method)"""
    # This is a compatibility method - actual implementation should be in database layer
    from core.database.connection_manager import get_session as _get_session
    return _get_session(database)


# Export all necessary functions and classes
__all__ = [
    "EnvironmentConfig",
    "Environment",
    "DatabaseType",
    "DatabaseConfig",
    "RedisConfig",
    "AgentConfig",
    "LLMConfig",
    "RobloxConfig",
    "EducationalConfig",
    "ServiceURLs",
    "get_environment_config",
    "should_use_real_data",
    "get_database_url",
    "get_redis_url",
    "get_api_key",
    "is_production",
    "is_development",
    "is_testing"
]