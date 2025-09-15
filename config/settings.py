"""
Centralized Settings Configuration

Provides unified configuration for all components of the ToolboxAI platform.
Uses Pydantic v2 for validation and environment variable loading.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, computed_field
from pathlib import Path
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Main settings class with all configuration options"""
    
    # === Application Info ===
    APP_NAME: str = "ToolboxAI Educational Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # === Paths ===
    @computed_field
    @property
    def BASE_DIR(self) -> Path:
        """Get base directory of the project"""
        return Path(__file__).parent.parent.absolute()
    
    @computed_field
    @property
    def APPS_DIR(self) -> Path:
        """Get apps directory"""
        return self.BASE_DIR / "apps"
    
    @computed_field
    @property
    def CORE_DIR(self) -> Path:
        """Get core directory"""
        return self.BASE_DIR / "core"
    
    @computed_field
    @property
    def TESTS_DIR(self) -> Path:
        """Get tests directory"""
        return self.BASE_DIR / "tests"
    
    @computed_field
    @property
    def LOGS_DIR(self) -> Path:
        """Get logs directory"""
        return self.BASE_DIR / "logs"
    
    @computed_field
    @property
    def STATIC_DIR(self) -> Path:
        """Get static files directory"""
        return self.APPS_DIR / "dashboard" / "dist"
    
    # === Database Configuration ===
    DATABASE_URL: str = Field(
        default="postgresql://eduplatform:eduplatform2024@localhost:5432/educational_platform_dev",
        env="DATABASE_URL"
    )
    DB_HOST: str = Field(default="localhost", env="DB_HOST")
    DB_PORT: int = Field(default=5432, env="DB_PORT")
    DB_USER: str = Field(default="eduplatform", env="DB_USER")
    DB_PASSWORD: str = Field(default="eduplatform2024", env="DB_PASSWORD")
    DB_NAME: str = Field(default="educational_platform_dev", env="DB_NAME")
    
    # Database Pool Settings
    DB_POOL_MIN_SIZE: int = Field(default=5, env="DB_POOL_MIN_SIZE")
    DB_POOL_MAX_SIZE: int = Field(default=20, env="DB_POOL_MAX_SIZE")
    DB_POOL_MAX_OVERFLOW: int = Field(default=40, env="DB_POOL_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")
    DB_COMMAND_TIMEOUT: int = Field(default=60, env="DB_COMMAND_TIMEOUT")
    
    # === Redis Configuration ===
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_MAX_CONNECTIONS: int = Field(default=50, env="REDIS_MAX_CONNECTIONS")
    
    # === API Configuration ===
    API_HOST: str = Field(default="127.0.0.1", env="API_HOST")
    API_PORT: int = Field(default=8008, env="API_PORT")
    API_PREFIX: str = Field(default="/api/v1", env="API_PREFIX")
    API_RELOAD: bool = Field(default=True, env="API_RELOAD")
    
    # === Dashboard Configuration ===
    DASHBOARD_URL: str = Field(default="http://localhost:5179", env="DASHBOARD_URL")
    DASHBOARD_HOST: str = Field(default="localhost", env="DASHBOARD_HOST")
    DASHBOARD_PORT: int = Field(default=5179, env="DASHBOARD_PORT")
    
    # === CORS Configuration ===
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:5179",
            "http://localhost:5180",
            "http://127.0.0.1:5179",
            "http://127.0.0.1:5180",
            "http://localhost:3000",
            "http://127.0.0.1:3000"
        ],
        env="CORS_ORIGINS"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    CORS_ALLOW_METHODS: List[str] = Field(default=["*"], env="CORS_ALLOW_METHODS")
    CORS_ALLOW_HEADERS: List[str] = Field(default=["*"], env="CORS_ALLOW_HEADERS")
    
    # === Authentication ===
    JWT_SECRET_KEY: str = Field(
        default="V2Q.TU:w#0*ROJ_?A){Q2XkDTW>1TPzc{H-$h6%^7gZ)mTarD)@dx@?8&pTGM^4d",
        env="JWT_SECRET_KEY"
    )
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    # === OpenAI Configuration ===
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4", env="OPENAI_MODEL")
    OPENAI_TEMPERATURE: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    OPENAI_MAX_TOKENS: int = Field(default=1000, env="OPENAI_MAX_TOKENS")
    
    # === Pusher Configuration ===
    PUSHER_ENABLED: bool = Field(default=False, env="PUSHER_ENABLED")
    PUSHER_APP_ID: Optional[str] = Field(default=None, env="PUSHER_APP_ID")
    PUSHER_KEY: Optional[str] = Field(default=None, env="PUSHER_KEY")
    PUSHER_SECRET: Optional[str] = Field(default=None, env="PUSHER_SECRET")
    PUSHER_CLUSTER: str = Field(default="us2", env="PUSHER_CLUSTER")
    PUSHER_SSL: bool = Field(default=True, env="PUSHER_SSL")
    
    # === WebSocket Configuration ===
    WS_ENABLED: bool = Field(default=True, env="WS_ENABLED")
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")
    WS_MAX_CONNECTIONS: int = Field(default=1000, env="WS_MAX_CONNECTIONS")
    
    # === Roblox Integration ===
    ROBLOX_API_KEY: Optional[str] = Field(default=None, env="ROBLOX_API_KEY")
    ROBLOX_WEBHOOK_URL: Optional[str] = Field(default=None, env="ROBLOX_WEBHOOK_URL")
    ROBLOX_STUDIO_PORT: int = Field(default=8765, env="ROBLOX_STUDIO_PORT")
    
    # === Monitoring & Logging ===
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    SENTRY_ENVIRONMENT: str = Field(default="development", env="SENTRY_ENVIRONMENT")
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=0.1, env="SENTRY_TRACES_SAMPLE_RATE")
    
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # === Testing Configuration ===
    TESTING: bool = Field(default=False, env="TESTING")
    TEST_DATABASE_URL: str = Field(
        default="postgresql://eduplatform:eduplatform2024@localhost:5432/educational_platform_test",
        env="TEST_DATABASE_URL"
    )
    RUN_INTEGRATION_TESTS: bool = Field(default=False, env="RUN_INTEGRATION_TESTS")
    RUN_WEBSOCKET_TESTS: bool = Field(default=False, env="RUN_WEBSOCKET_TESTS")
    RUN_ENDPOINT_TESTS: bool = Field(default=False, env="RUN_ENDPOINT_TESTS")
    RUN_ROJO_TESTS: bool = Field(default=False, env="RUN_ROJO_TESTS")
    RUN_SOCKETIO_E2E: bool = Field(default=False, env="RUN_SOCKETIO_E2E")
    RUN_WS_INTEGRATION: bool = Field(default=False, env="RUN_WS_INTEGRATION")
    
    # === Performance Settings ===
    WORKER_CONNECTIONS: int = Field(default=1000, env="WORKER_CONNECTIONS")
    WORKER_TIMEOUT: int = Field(default=30, env="WORKER_TIMEOUT")
    KEEPALIVE: int = Field(default=5, env="KEEPALIVE")
    MAX_REQUESTS: int = Field(default=1000, env="MAX_REQUESTS")
    MAX_REQUESTS_JITTER: int = Field(default=50, env="MAX_REQUESTS_JITTER")
    
    # === Security Settings ===
    SECRET_KEY: str = Field(
        default="change-this-in-production-to-a-secure-random-string",
        env="SECRET_KEY"
    )
    ALLOWED_HOSTS: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")
    SECURE_SSL_REDIRECT: bool = Field(default=False, env="SECURE_SSL_REDIRECT")
    SESSION_COOKIE_SECURE: bool = Field(default=False, env="SESSION_COOKIE_SECURE")
    CSRF_COOKIE_SECURE: bool = Field(default=False, env="CSRF_COOKIE_SECURE")
    
    # === Rate Limiting ===
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_DEFAULT: str = Field(default="100/hour", env="RATE_LIMIT_DEFAULT")
    RATE_LIMIT_STORAGE_URL: Optional[str] = Field(default=None, env="RATE_LIMIT_STORAGE_URL")
    
    # === File Upload Settings ===
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_UPLOAD_SIZE")  # 10MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx"],
        env="ALLOWED_UPLOAD_EXTENSIONS"
    )
    UPLOAD_PATH: str = Field(default="uploads", env="UPLOAD_PATH")
    
    # === Email Settings (Future) ===
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_USE_TLS: bool = Field(default=True, env="SMTP_USE_TLS")
    DEFAULT_FROM_EMAIL: str = Field(default="noreply@toolboxai.com", env="DEFAULT_FROM_EMAIL")
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        
        # Allow extra fields for forward compatibility
        extra = "allow"
    
    def get_database_url(self, test: bool = False) -> str:
        """Get the appropriate database URL"""
        if test or self.TESTING:
            return self.TEST_DATABASE_URL
        return self.DATABASE_URL
    
    def get_redis_url(self) -> str:
        """Construct Redis URL from components"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT.lower() in ["production", "prod"]
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT.lower() in ["development", "dev"]
    
    def is_testing(self) -> bool:
        """Check if running tests"""
        return self.TESTING or self.ENVIRONMENT.lower() in ["test", "testing"]


# Create global settings instance
settings = Settings()

# Export commonly used values
BASE_DIR = settings.BASE_DIR
APPS_DIR = settings.APPS_DIR
CORE_DIR = settings.CORE_DIR
TESTS_DIR = settings.TESTS_DIR

# Ensure required directories exist
for directory in [settings.LOGS_DIR, Path(settings.UPLOAD_PATH)]:
    directory.mkdir(parents=True, exist_ok=True)