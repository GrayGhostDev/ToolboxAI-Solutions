# Backend Configuration Guide

## Table of Contents
- [Configuration Overview](#configuration-overview)
- [Environment Variables](#environment-variables)
- [Feature Flags](#feature-flags)
- [Service Settings](#service-settings)
- [Security Configuration](#security-configuration)
- [Performance Tuning](#performance-tuning)
- [Monitoring Configuration](#monitoring-configuration)
- [Development vs Production](#development-vs-production)
- [Configuration Validation](#configuration-validation)
- [Troubleshooting](#troubleshooting)

## Configuration Overview

The ToolboxAI backend uses a centralized configuration system built on Pydantic Settings. Configuration is managed through environment variables, `.env` files, and runtime settings with proper validation and type safety.

### Configuration Architecture
```
toolboxai_settings/
├── settings.py          # Main settings class
├── compat.py           # Compatibility layer
└── __init__.py         # Package initialization

apps/backend/core/
├── config.py           # Backend-specific config wrapper
└── app_factory.py      # App factory with config injection
```

### Configuration Sources (Priority Order)
1. **Environment Variables** (Highest priority)
2. **`.env` files** (Project root and app-specific)
3. **Default values** (Defined in settings classes)
4. **Runtime overrides** (Testing and special cases)

## Environment Variables

### Core Application Settings

#### Basic Application Configuration
```bash
# Application Information
APP_NAME="ToolboxAI Roblox Environment"
APP_VERSION="1.0.0"
ENVIRONMENT=development  # development, staging, production
DEBUG=true              # Enable debug mode (development only)

# Server Configuration
HOST=127.0.0.1
PORT=8009
WORKERS=1               # Number of worker processes (production)
RELOAD=true             # Auto-reload on changes (development)
```

#### Database Configuration
```bash
# Primary Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/database_name
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
DATABASE_ECHO=false     # Set to true for SQL query logging

# Database Connection Examples
# Local Development:
DATABASE_URL=postgresql+asyncpg://toolboxai:dev_password@localhost:5432/toolboxai_dev

# Docker Development:
DATABASE_URL=postgresql+asyncpg://toolboxai:dev_password@postgres:5432/toolboxai_dev

# Production (with connection pooling):
DATABASE_URL=postgresql+asyncpg://prod_user:secure_password@prod-db.example.com:5432/toolboxai_prod
```

#### Redis Configuration
```bash
# Redis Cache and Session Store
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=optional_password
REDIS_MAX_CONNECTIONS=100
REDIS_TIMEOUT=5
REDIS_RETRY_ON_TIMEOUT=true

# Redis Connection Examples
# Local Development:
REDIS_URL=redis://localhost:6379/0

# Docker Development:
REDIS_URL=redis://redis:6379/0

# Production with authentication:
REDIS_URL=redis://:secure_password@redis.example.com:6379/0

# Redis Cluster (Production):
REDIS_URL=redis://redis-cluster.example.com:7000,redis-cluster.example.com:7001,redis-cluster.example.com:7002/0
```

### Authentication & Security

#### JWT Configuration
```bash
# JWT Token Settings
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_ISSUER=toolboxai
JWT_AUDIENCE=toolboxai-users

# JWT Key Generation (use for production)
# python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### CORS Configuration
```bash
# Cross-Origin Resource Sharing
CORS_ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5179","https://app.toolboxai.com"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOWED_METHODS=["GET","POST","PUT","DELETE","OPTIONS","PATCH"]
CORS_ALLOWED_HEADERS=["*"]
CORS_MAX_AGE=86400

# Development (allow all origins)
CORS_ALLOW_ORIGINS=["*"]  # WARNING: Only for development!

# Production (specific origins only)
CORS_ALLOWED_ORIGINS=["https://toolboxai.com","https://app.toolboxai.com","https://dashboard.toolboxai.com"]
```

#### Security Headers
```bash
# Security Header Configuration
SECURITY_HEADERS_ENABLED=true
HSTS_MAX_AGE=31536000
HSTS_INCLUDE_SUBDOMAINS=true
HSTS_PRELOAD=false
CSP_ENABLED=true
CSP_POLICY="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
```

### AI & External Services

#### OpenAI Configuration
```bash
# OpenAI API Settings
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7
OPENAI_TIMEOUT=60
OPENAI_MAX_RETRIES=3

# OpenAI Organization (if applicable)
OPENAI_ORGANIZATION=org-your-organization-id
```

#### Pusher Real-time Configuration
```bash
# Pusher Channels Configuration
PUSHER_ENABLED=true
PUSHER_APP_ID=123456
PUSHER_KEY=your-pusher-key
PUSHER_SECRET=your-pusher-secret
PUSHER_CLUSTER=us2
PUSHER_USE_TLS=true

# Pusher Channel Settings
PUSHER_MAX_CONNECTIONS=1000
PUSHER_ACTIVITY_TIMEOUT=120000
PUSHER_PONG_TIMEOUT=30000
```

#### Roblox Integration
```bash
# Roblox Open Cloud API
ROBLOX_API_KEY=your-roblox-api-key
ROBLOX_UNIVERSE_ID=your-universe-id
ROBLOX_CREATOR_ID=your-creator-id
ROBLOX_GROUP_ID=your-group-id

# Roblox Studio Integration
ROBLOX_STUDIO_ENABLED=true
ROBLOX_AUTO_PUBLISH=false
ROBLOX_TIMEOUT=120
```

### Monitoring & Observability

#### Sentry Configuration
```bash
# Sentry Error Tracking
SENTRY_ENABLED=true
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
SENTRY_ATTACH_STACKTRACE=true
SENTRY_SEND_DEFAULT_PII=false

# Sentry Performance Monitoring
SENTRY_ENABLE_TRACING=true
SENTRY_TRACE_SAMPLE_RATE=0.01  # 1% of transactions
```

#### Logging Configuration
```bash
# Logging Settings
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json         # json, text
LOG_FILE_ENABLED=true
LOG_FILE_PATH=logs/app.log
LOG_ROTATION_SIZE=100MB
LOG_RETENTION_DAYS=30

# Correlation ID Tracking
CORRELATION_ID_HEADER=X-Request-ID
CORRELATION_ID_RESPONSE_HEADER=X-Request-ID
```

## Feature Flags

### Resilience Features
```bash
# Circuit Breaker Configuration
CIRCUIT_BREAKER_ENABLED=true
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT_SECONDS=60
CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS=3
CIRCUIT_BREAKER_EXPECTED_EXCEPTION=Exception

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST_SIZE=20
RATE_LIMIT_STORAGE=redis
RATE_LIMIT_KEY_FUNC=get_remote_address

# Retry Mechanism
RETRY_ENABLED=true
RETRY_MAX_ATTEMPTS=3
RETRY_BACKOFF_FACTOR=2
RETRY_JITTER=true

# Bulkhead Pattern
BULKHEAD_ENABLED=true
BULKHEAD_MAX_CONCURRENT=10
BULKHEAD_TIMEOUT_SECONDS=30
```

### Agent System Configuration
```bash
# AI Agent System
AGENTS_ENABLED=true
AGENT_MAX_WORKERS=5
AGENT_TIMEOUT_SECONDS=300
AGENT_QUEUE_SIZE=100
AGENT_RETRY_ATTEMPTS=3

# Agent Types
CONTENT_AGENT_ENABLED=true
QUIZ_AGENT_ENABLED=true
TERRAIN_AGENT_ENABLED=true
SCRIPT_AGENT_ENABLED=true
ROBLOX_AGENT_ENABLED=true

# Agent Performance
AGENT_CONCURRENT_TASKS=3
AGENT_BATCH_SIZE=10
AGENT_HEALTH_CHECK_INTERVAL=60
```

### Feature Toggles
```bash
# API Features
API_V2_ENABLED=false
GRAPHQL_ENABLED=false
WEBSOCKET_LEGACY_ENABLED=true
PUSHER_MIGRATION_COMPLETE=false

# Development Features
SKIP_AUTH=false         # WARNING: Only for development!
MOCK_EXTERNAL_SERVICES=false
DEBUG_TOOLBAR_ENABLED=false
PROFILING_ENABLED=false

# Experimental Features
EXPERIMENTAL_AI_MODELS=false
BETA_DASHBOARD_FEATURES=false
ADVANCED_ANALYTICS=false
```

## Service Settings

### Agent Service Configuration
```python
# Agent-specific settings
AGENT_SETTINGS = {
    "content_agent": {
        "max_tokens": 2000,
        "temperature": 0.7,
        "timeout": 120,
        "retry_attempts": 3
    },
    "quiz_agent": {
        "max_questions": 50,
        "difficulty_levels": [1, 2, 3, 4, 5],
        "question_types": ["multiple_choice", "true_false", "short_answer"]
    },
    "roblox_agent": {
        "max_script_length": 10000,
        "allowed_services": ["Players", "Workspace", "ReplicatedStorage"],
        "security_level": "strict"
    }
}
```

### Database Service Settings
```bash
# Database Query Optimization
DB_QUERY_TIMEOUT=30
DB_SLOW_QUERY_THRESHOLD=1.0
DB_CONNECTION_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_RECYCLE=3600

# Database Migrations
ALEMBIC_AUTO_UPGRADE=false
ALEMBIC_REVISION_ENVIRONMENT=production
ALEMBIC_COMPARE_TYPE=true
ALEMBIC_COMPARE_SERVER_DEFAULT=true
```

### Cache Configuration
```bash
# Redis Cache Settings
CACHE_DEFAULT_TIMEOUT=300
CACHE_KEY_PREFIX=toolboxai
CACHE_VERSION=1
CACHE_SERIALIZER=json

# Cache Strategies
USER_CACHE_TIMEOUT=600
CONTENT_CACHE_TIMEOUT=1800
ANALYTICS_CACHE_TIMEOUT=3600
AGENT_RESULT_CACHE_TIMEOUT=7200
```

## Security Configuration

### Comprehensive Security Settings
```bash
# Authentication Security
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_SPECIAL_CHARS=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_MAX_AGE_DAYS=90
LOGIN_ATTEMPT_LIMIT=5
LOGIN_LOCKOUT_DURATION=300

# Session Security
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=strict
SESSION_TIMEOUT=3600
SESSION_REGENERATE_ID=true

# API Security
API_KEY_REQUIRED=false
API_RATE_LIMIT_PER_USER=1000
API_RATE_LIMIT_WINDOW=3600
API_REQUEST_SIZE_LIMIT=10MB
API_TIMEOUT=30

# Content Security
CONTENT_VALIDATION_ENABLED=true
CONTENT_SANITIZATION=true
XSS_PROTECTION=true
SQL_INJECTION_PROTECTION=true
```

### Encryption Settings
```bash
# Data Encryption
ENCRYPTION_ENABLED=true
ENCRYPTION_ALGORITHM=AES-256-GCM
ENCRYPTION_KEY_ROTATION_DAYS=90

# Field-level Encryption
ENCRYPT_PII=true
ENCRYPT_API_KEYS=true
ENCRYPT_TOKENS=true

# TLS Configuration
TLS_VERSION=1.2
TLS_CIPHER_SUITES=ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS
```

## Performance Tuning

### Application Performance
```bash
# FastAPI Settings
FASTAPI_WORKERS=4       # Number of worker processes
FASTAPI_WORKER_CLASS=uvicorn.workers.UvicornWorker
FASTAPI_MAX_WORKERS=8
FASTAPI_WORKER_CONNECTIONS=1000
FASTAPI_KEEPALIVE=2

# Request Processing
REQUEST_TIMEOUT=30
MAX_REQUEST_SIZE=100MB
RESPONSE_COMPRESSION=true
GZIP_MINIMUM_SIZE=1000

# Async Settings
ASYNCIO_DEBUG=false
ASYNCIO_LOOP_POLICY=uvloop  # For better performance
MAX_CONCURRENT_REQUESTS=1000
```

### Database Performance
```bash
# Connection Pool Tuning
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=50
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true

# Query Performance
DB_QUERY_CACHE_SIZE=1000
DB_STATEMENT_CACHE_SIZE=1000
DB_PREPARED_STATEMENT_CACHE_SIZE=100
DB_ECHO_POOL=false

# Connection Health
DB_HEALTH_CHECK_INTERVAL=30
DB_MAX_RETRIES=3
DB_RETRY_DELAY=1
```

### Cache Performance
```bash
# Redis Performance
REDIS_CONNECTION_POOL_SIZE=50
REDIS_MAX_CONNECTIONS=100
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
REDIS_SOCKET_KEEPALIVE=true
REDIS_SOCKET_KEEPALIVE_OPTIONS={}

# Cache Optimization
CACHE_COMPRESSION=true
CACHE_SERIALIZATION_FORMAT=msgpack
CACHE_PIPELINE_SIZE=100
```

## Monitoring Configuration

### Health Check Settings
```bash
# Health Check Configuration
HEALTH_CHECK_ENABLED=true
HEALTH_CHECK_INTERVAL=30
HEALTH_CHECK_TIMEOUT=10
HEALTH_CHECK_RETRIES=3

# Component Health Checks
DB_HEALTH_CHECK=true
REDIS_HEALTH_CHECK=true
EXTERNAL_API_HEALTH_CHECK=true
AGENT_HEALTH_CHECK=true

# Health Check Endpoints
HEALTH_CHECK_PATH=/health
HEALTH_CHECK_VERBOSE_PATH=/health/verbose
HEALTH_CHECK_DEPENDENCIES_PATH=/health/dependencies
```

### Metrics Collection
```bash
# Metrics Settings
METRICS_ENABLED=true
METRICS_EXPORT_INTERVAL=60
METRICS_RETENTION_DAYS=30

# Prometheus Metrics
PROMETHEUS_ENABLED=false
PROMETHEUS_PORT=9090
PROMETHEUS_PATH=/metrics

# Custom Metrics
TRACK_REQUEST_DURATION=true
TRACK_DATABASE_QUERIES=true
TRACK_CACHE_HITS=true
TRACK_AGENT_PERFORMANCE=true
```

### Performance Monitoring
```bash
# Performance Tracking
PERFORMANCE_MONITORING=true
SLOW_REQUEST_THRESHOLD=2.0
MEMORY_MONITORING=true
CPU_MONITORING=true

# Profiling
PROFILING_ENABLED=false
PROFILING_SAMPLE_RATE=0.01
PROFILING_MAX_TRACES=1000
```

## Development vs Production

### Development Configuration
```bash
# Development Environment
ENVIRONMENT=development
DEBUG=true
RELOAD=true
LOG_LEVEL=DEBUG
SKIP_AUTH=false  # Even in dev, keep auth enabled

# Development Database
DATABASE_URL=postgresql+asyncpg://dev_user:dev_pass@localhost:5432/toolboxai_dev
DATABASE_ECHO=true

# Development CORS (more permissive)
CORS_ALLOW_ORIGINS=["*"]
CORS_ALLOW_CREDENTIALS=true

# Development Sentry (disabled or separate project)
SENTRY_ENABLED=false
# Or use separate development DSN
SENTRY_DSN=https://dev-dsn@sentry.io/dev-project

# Development External Services (mocked)
MOCK_EXTERNAL_SERVICES=true
OPENAI_API_KEY=mock-key-for-testing
```

### Production Configuration
```bash
# Production Environment
ENVIRONMENT=production
DEBUG=false
RELOAD=false
LOG_LEVEL=INFO
WORKERS=4

# Production Database
DATABASE_URL=postgresql+asyncpg://prod_user:${DB_PASSWORD}@prod-db:5432/toolboxai_prod
DATABASE_ECHO=false
DATABASE_POOL_SIZE=50

# Production CORS (strict)
CORS_ALLOWED_ORIGINS=["https://toolboxai.com","https://app.toolboxai.com"]
CORS_ALLOW_CREDENTIALS=true

# Production Security
HSTS_MAX_AGE=31536000
CSP_ENABLED=true
SECURITY_HEADERS_ENABLED=true

# Production Monitoring
SENTRY_ENABLED=true
SENTRY_ENVIRONMENT=production
METRICS_ENABLED=true
PERFORMANCE_MONITORING=true
```

### Staging Configuration
```bash
# Staging Environment (Production-like)
ENVIRONMENT=staging
DEBUG=false
RELOAD=false
LOG_LEVEL=INFO
WORKERS=2

# Staging Database
DATABASE_URL=postgresql+asyncpg://staging_user:${DB_PASSWORD}@staging-db:5432/toolboxai_staging

# Staging Monitoring
SENTRY_ENABLED=true
SENTRY_ENVIRONMENT=staging
SENTRY_TRACES_SAMPLE_RATE=0.5  # Higher sampling for testing
```

## Configuration Validation

### Pydantic Settings Validation
```python
# apps/backend/core/config.py
from pydantic import BaseSettings, validator, root_validator
from typing import List, Optional

class Settings(BaseSettings):
    """Application settings with validation."""

    # Database URL validation
    DATABASE_URL: str

    @validator('DATABASE_URL')
    def validate_database_url(cls, v):
        if not v.startswith(('postgresql://', 'postgresql+asyncpg://')):
            raise ValueError('DATABASE_URL must use PostgreSQL')
        return v

    # CORS origins validation
    CORS_ALLOWED_ORIGINS: List[str] = []

    @validator('CORS_ALLOWED_ORIGINS', pre=True)
    def validate_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    # JWT secret validation
    JWT_SECRET_KEY: str

    @validator('JWT_SECRET_KEY')
    def validate_jwt_secret(cls, v):
        if len(v) < 32:
            raise ValueError('JWT_SECRET_KEY must be at least 32 characters')
        return v

    # Environment-specific validation
    @root_validator
    def validate_production_settings(cls, values):
        env = values.get('ENVIRONMENT')
        if env == 'production':
            # Ensure debug is disabled in production
            if values.get('DEBUG', False):
                raise ValueError('DEBUG must be False in production')

            # Ensure proper secret in production
            if values.get('JWT_SECRET_KEY') == 'development-secret':
                raise ValueError('Must use secure JWT secret in production')

        return values

    class Config:
        env_file = '.env'
        case_sensitive = True
```

### Runtime Configuration Checks
```python
# apps/backend/core/validation.py
import os
import sys
from typing import List, Dict, Any

def validate_environment() -> List[str]:
    """Validate environment configuration."""
    errors = []

    # Required environment variables
    required_vars = [
        'DATABASE_URL',
        'JWT_SECRET_KEY',
        'OPENAI_API_KEY',
        'PUSHER_KEY'
    ]

    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")

    # Database connectivity
    try:
        from apps.backend.core.database import test_connection
        asyncio.run(test_connection())
    except Exception as e:
        errors.append(f"Database connection failed: {e}")

    # Redis connectivity
    try:
        from apps.backend.core.redis import test_redis_connection
        asyncio.run(test_redis_connection())
    except Exception as e:
        errors.append(f"Redis connection failed: {e}")

    return errors

def startup_validation():
    """Perform startup validation checks."""
    errors = validate_environment()

    if errors:
        print("Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    print("✓ Configuration validation passed")
```

## Troubleshooting

### Common Configuration Issues

#### 1. Database Connection Issues
```bash
# Problem: Database connection failed
# Solution: Check database URL format
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database

# Common issues:
# - Missing +asyncpg driver suffix
# - Wrong port (5432 for PostgreSQL)
# - Network connectivity issues
# - Credentials problems

# Debug command:
python -c "
from sqlalchemy import create_engine
engine = create_engine('$DATABASE_URL')
print('Database connection successful')
"
```

#### 2. Redis Connection Issues
```bash
# Problem: Redis connection failed
# Solution: Check Redis URL and connectivity
REDIS_URL=redis://[:password@]host:port/database

# Debug commands:
redis-cli -h localhost -p 6379 ping
python -c "
import redis
r = redis.from_url('$REDIS_URL')
print(r.ping())
"
```

#### 3. CORS Configuration Issues
```bash
# Problem: CORS errors in browser
# Solution: Check allowed origins
CORS_ALLOWED_ORIGINS=["http://localhost:3000","https://app.example.com"]

# Development (temporary):
CORS_ALLOW_ORIGINS=["*"]  # WARNING: Not for production!

# Check current CORS config:
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     http://localhost:8009/api/v1/content
```

#### 4. JWT Token Issues
```bash
# Problem: JWT authentication failing
# Solution: Check JWT configuration

# Generate secure secret:
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Debug JWT token:
python -c "
import jwt
from apps.backend.core.config import settings
token = 'your-token-here'
payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
print(payload)
"
```

### Configuration Debugging Commands

#### Check Current Configuration
```bash
# View current environment variables
env | grep -E "(DATABASE|REDIS|JWT|PUSHER|OPENAI)" | sort

# Check configuration loading
python -c "
from apps.backend.core.config import settings
print(f'Environment: {settings.ENVIRONMENT}')
print(f'Debug: {settings.DEBUG}')
print(f'Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'hidden'}')
print(f'Redis: {settings.REDIS_URL}')
"
```

#### Validate Services
```bash
# Test all service connections
python scripts/validate_config.py

# Test specific service
python -c "
import asyncio
from apps.backend.services.agent_service import get_agent_service
async def test():
    service = get_agent_service()
    status = await service.health_check()
    print(f'Agent service: {status}')
asyncio.run(test())
"
```

#### Monitor Configuration Changes
```bash
# Watch configuration files
watch -n 2 'env | grep -E "(DATABASE|REDIS|JWT)" | sort'

# Monitor configuration loading
tail -f logs/app.log | grep -i config
```

### Environment-Specific Troubleshooting

#### Development Issues
```bash
# Common development problems:
1. Database not running: docker-compose up -d postgres
2. Redis not running: docker-compose up -d redis
3. Wrong Python interpreter: source venv/bin/activate
4. Missing dependencies: pip install -r requirements.txt
5. Port conflicts: lsof -i :8009
```

#### Production Issues
```bash
# Common production problems:
1. Environment variables not set: Check deployment configuration
2. Secret management: Verify secret injection
3. Network connectivity: Test database/Redis connectivity
4. Resource limits: Check memory/CPU limits
5. SSL/TLS issues: Verify certificate configuration
```

### Configuration Monitoring
```python
# apps/backend/core/config_monitor.py
import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ConfigurationMonitor:
    """Monitor configuration changes and health."""

    def __init__(self):
        self.last_check = None
        self.config_hash = None

    async def monitor_loop(self):
        """Continuous configuration monitoring."""
        while True:
            try:
                await self.check_configuration_health()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Configuration monitoring error: {e}")
                await asyncio.sleep(60)

    async def check_configuration_health(self):
        """Check configuration health."""
        issues = []

        # Check database connectivity
        try:
            from apps.backend.core.database import test_connection
            await test_connection()
        except Exception as e:
            issues.append(f"Database: {e}")

        # Check Redis connectivity
        try:
            from apps.backend.core.redis import test_redis_connection
            await test_redis_connection()
        except Exception as e:
            issues.append(f"Redis: {e}")

        # Check external services
        try:
            from apps.backend.services.external_health import check_all_services
            service_status = await check_all_services()
            for service, status in service_status.items():
                if not status['healthy']:
                    issues.append(f"{service}: {status['error']}")
        except Exception as e:
            issues.append(f"External services: {e}")

        if issues:
            logger.warning(f"Configuration health issues: {issues}")
        else:
            logger.debug("Configuration health check passed")

        return len(issues) == 0
```

This comprehensive configuration guide ensures proper setup, validation, and troubleshooting of the ToolboxAI backend system across all environments.