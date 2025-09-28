# 🔐 Environment Variables Documentation

**Last Updated**: September 24, 2025
**Security Status**: All secrets removed from repository
**Template Location**: `.env.example`

## Overview

This document provides comprehensive documentation for all environment variables used in ToolBoxAI. Following the security audit of September 24, 2025, all exposed secrets have been removed and replaced with secure management practices.

## 🚨 Security Notice

**CRITICAL**: Never commit actual secrets to version control
- Use `.env.example` as a template
- Keep `.env` files in `.gitignore`
- Use Docker Secrets for production
- Rotate keys regularly

## 📋 Quick Setup

### Development Environment
```bash
# Copy template
cp .env.example .env

# Generate secure keys
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env
echo "DB_PASSWORD=$(openssl rand -base64 32)" >> .env
echo "REDIS_PASSWORD=$(openssl rand -base64 24)" >> .env

# Edit with your API keys
nano .env
```

### Docker Development
```bash
# Docker reads .env automatically
cd infrastructure/docker/compose
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Production Setup
```bash
# Use Docker Secrets
echo "your-secret" | docker secret create jwt_secret -
echo "your-db-pass" | docker secret create db_password -
echo "your-redis-pass" | docker secret create redis_password -
```

## 🔧 Core Configuration

### Application Settings

#### ENVIRONMENT
- **Type**: String
- **Required**: Yes
- **Default**: `development`
- **Options**: `development`, `staging`, `production`
- **Description**: Application environment mode
- **Example**: `ENVIRONMENT=development`

#### DEBUG
- **Type**: Boolean
- **Required**: No
- **Default**: `true` (development), `false` (production)
- **Description**: Enable debug mode with verbose logging
- **Example**: `DEBUG=true`

#### LOG_LEVEL
- **Type**: String
- **Required**: No
- **Default**: `INFO`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Description**: Logging verbosity level
- **Example**: `LOG_LEVEL=INFO`

#### APP_NAME
- **Type**: String
- **Required**: No
- **Default**: `ToolBoxAI`
- **Description**: Application display name
- **Example**: `APP_NAME=ToolBoxAI`

#### APP_VERSION
- **Type**: String
- **Required**: No
- **Default**: `1.0.0`
- **Description**: Application version for tracking
- **Example**: `APP_VERSION=1.0.0`

## 🔒 Authentication & Security

### JWT Configuration

#### JWT_SECRET_KEY
- **Type**: String (hex)
- **Required**: Yes
- **Security**: HIGH - Never expose
- **Generation**: `openssl rand -hex 32`
- **Description**: Secret key for JWT token signing
- **Example**: `JWT_SECRET_KEY=your_32_byte_hex_string`

#### JWT_ALGORITHM
- **Type**: String
- **Required**: No
- **Default**: `HS256`
- **Options**: `HS256`, `RS256`
- **Description**: JWT signing algorithm
- **Example**: `JWT_ALGORITHM=HS256`

#### ACCESS_TOKEN_EXPIRE_MINUTES
- **Type**: Integer
- **Required**: No
- **Default**: `30`
- **Description**: Access token expiration time
- **Example**: `ACCESS_TOKEN_EXPIRE_MINUTES=30`

#### REFRESH_TOKEN_EXPIRE_DAYS
- **Type**: Integer
- **Required**: No
- **Default**: `7`
- **Description**: Refresh token expiration time
- **Example**: `REFRESH_TOKEN_EXPIRE_DAYS=7`

### Clerk Authentication (Optional)

#### VITE_ENABLE_CLERK_AUTH
- **Type**: Boolean
- **Required**: No
- **Default**: `false`
- **Description**: Enable Clerk authentication in frontend
- **Example**: `VITE_ENABLE_CLERK_AUTH=false`

#### VITE_CLERK_PUBLISHABLE_KEY
- **Type**: String
- **Required**: If Clerk enabled
- **Security**: MEDIUM - Frontend key
- **Description**: Clerk public key for frontend
- **Example**: `VITE_CLERK_PUBLISHABLE_KEY=pk_test_...`

#### CLERK_SECRET_KEY
- **Type**: String
- **Required**: If Clerk enabled
- **Security**: HIGH - Never expose
- **Description**: Clerk secret key for backend
- **Example**: `CLERK_SECRET_KEY=sk_test_...`

## 💾 Database Configuration

### PostgreSQL

#### DATABASE_URL
- **Type**: Connection String
- **Required**: Yes
- **Security**: HIGH - Contains password
- **Format**: `postgresql://user:password@host:port/database`
- **Docker**: `postgresql://toolboxai:devpass2024@postgres:5432/toolboxai`
- **Local**: `postgresql://toolboxai:devpass2024@localhost:5432/toolboxai`
- **Example**: `DATABASE_URL=postgresql://toolboxai:devpass2024@localhost:5432/toolboxai`

#### POSTGRES_USER
- **Type**: String
- **Required**: For Docker Compose
- **Default**: `toolboxai`
- **Description**: PostgreSQL username
- **Example**: `POSTGRES_USER=toolboxai`

#### POSTGRES_PASSWORD
- **Type**: String
- **Required**: For Docker Compose
- **Security**: HIGH - Never expose
- **Generation**: `openssl rand -base64 32`
- **Description**: PostgreSQL password
- **Example**: `POSTGRES_PASSWORD=secure_password_here`

#### POSTGRES_DB
- **Type**: String
- **Required**: For Docker Compose
- **Default**: `toolboxai`
- **Description**: Database name
- **Example**: `POSTGRES_DB=toolboxai`

#### DB_POOL_SIZE
- **Type**: Integer
- **Required**: No
- **Default**: `10`
- **Description**: Database connection pool size
- **Example**: `DB_POOL_SIZE=10`

#### DB_MAX_OVERFLOW
- **Type**: Integer
- **Required**: No
- **Default**: `20`
- **Description**: Maximum overflow connections
- **Example**: `DB_MAX_OVERFLOW=20`

### Redis

#### REDIS_URL
- **Type**: Connection String
- **Required**: Yes
- **Format**: `redis://[:password]@host:port/db`
- **Docker**: `redis://redis:6379/0`
- **Local**: `redis://localhost:6379/0`
- **Example**: `REDIS_URL=redis://localhost:6379/0`

#### REDIS_PASSWORD
- **Type**: String
- **Required**: For production
- **Security**: HIGH - Never expose
- **Generation**: `openssl rand -base64 24`
- **Description**: Redis authentication password
- **Example**: `REDIS_PASSWORD=secure_redis_password`

#### REDIS_MAX_CONNECTIONS
- **Type**: Integer
- **Required**: No
- **Default**: `50`
- **Description**: Maximum Redis connections
- **Example**: `REDIS_MAX_CONNECTIONS=50`

## 🤖 AI Services

### OpenAI

#### OPENAI_API_KEY
- **Type**: String
- **Required**: For AI features
- **Security**: CRITICAL - Never expose
- **Source**: https://platform.openai.com/api-keys
- **Description**: OpenAI API authentication key
- **Example**: `OPENAI_API_KEY=sk-...`

#### OPENAI_MODEL
- **Type**: String
- **Required**: No
- **Default**: `gpt-4-turbo-preview`
- **Options**: `gpt-4`, `gpt-4-turbo-preview`, `gpt-3.5-turbo`
- **Description**: Default OpenAI model
- **Example**: `OPENAI_MODEL=gpt-4-turbo-preview`

#### OPENAI_MAX_TOKENS
- **Type**: Integer
- **Required**: No
- **Default**: `2000`
- **Description**: Maximum tokens per request
- **Example**: `OPENAI_MAX_TOKENS=2000`

### Anthropic

#### ANTHROPIC_API_KEY
- **Type**: String
- **Required**: For Claude features
- **Security**: CRITICAL - Never expose
- **Source**: https://console.anthropic.com
- **Description**: Anthropic API key for Claude
- **Example**: `ANTHROPIC_API_KEY=sk-ant-...`

#### ANTHROPIC_MODEL
- **Type**: String
- **Required**: No
- **Default**: `claude-3-opus-20240229`
- **Description**: Default Claude model
- **Example**: `ANTHROPIC_MODEL=claude-3-opus-20240229`

### Replicate

#### REPLICATE_API_TOKEN
- **Type**: String
- **Required**: For image generation
- **Security**: HIGH - Never expose
- **Source**: https://replicate.com/account
- **Description**: Replicate API token
- **Example**: `REPLICATE_API_TOKEN=r8_...`

## 📡 Realtime & Communication

### Pusher

#### PUSHER_ENABLED
- **Type**: Boolean
- **Required**: No
- **Default**: `true`
- **Description**: Enable Pusher for realtime features
- **Example**: `PUSHER_ENABLED=true`

#### PUSHER_APP_ID
- **Type**: String
- **Required**: If Pusher enabled
- **Security**: LOW - App identifier
- **Description**: Pusher application ID
- **Example**: `PUSHER_APP_ID=1234567`

#### PUSHER_KEY
- **Type**: String
- **Required**: If Pusher enabled
- **Security**: MEDIUM - Public key
- **Description**: Pusher public key
- **Example**: `PUSHER_KEY=abc123def456`

#### PUSHER_SECRET
- **Type**: String
- **Required**: If Pusher enabled
- **Security**: HIGH - Never expose
- **Description**: Pusher secret key
- **Example**: `PUSHER_SECRET=secret123`

#### PUSHER_CLUSTER
- **Type**: String
- **Required**: If Pusher enabled
- **Default**: `us2`
- **Description**: Pusher cluster region
- **Example**: `PUSHER_CLUSTER=us2`

### Email (SMTP)

#### SMTP_HOST
- **Type**: String
- **Required**: For email features
- **Description**: SMTP server hostname
- **Example**: `SMTP_HOST=smtp.gmail.com`

#### SMTP_PORT
- **Type**: Integer
- **Required**: For email features
- **Default**: `587`
- **Description**: SMTP server port
- **Example**: `SMTP_PORT=587`

#### SMTP_USER
- **Type**: String
- **Required**: For email features
- **Security**: MEDIUM
- **Description**: SMTP authentication username
- **Example**: `SMTP_USER=your-email@gmail.com`

#### SMTP_PASSWORD
- **Type**: String
- **Required**: For email features
- **Security**: HIGH - Never expose
- **Description**: SMTP authentication password
- **Example**: `SMTP_PASSWORD=your-app-password`

## 🎮 Platform Integrations

### Supabase

#### SUPABASE_URL
- **Type**: URL
- **Required**: For Supabase features
- **Security**: LOW - Public URL
- **Description**: Supabase project URL
- **Example**: `SUPABASE_URL=https://your-project.supabase.co`

#### SUPABASE_ANON_KEY
- **Type**: String
- **Required**: For Supabase features
- **Security**: MEDIUM - Public anon key
- **Description**: Supabase anonymous key
- **Example**: `SUPABASE_ANON_KEY=eyJ...`

#### SUPABASE_SERVICE_KEY
- **Type**: String
- **Required**: For admin features
- **Security**: CRITICAL - Never expose
- **Description**: Supabase service role key
- **Example**: `SUPABASE_SERVICE_KEY=eyJ...`

### Roblox

#### ROBLOX_API_KEY
- **Type**: String
- **Required**: For Roblox features
- **Security**: HIGH - Never expose
- **Description**: Roblox API authentication
- **Example**: `ROBLOX_API_KEY=...`

#### ROBLOX_WEBHOOK_SECRET
- **Type**: String
- **Required**: For webhooks
- **Security**: HIGH - Never expose
- **Description**: Webhook validation secret
- **Example**: `ROBLOX_WEBHOOK_SECRET=...`

## 🐳 Docker-Specific Variables

### Container Networking

#### BACKEND_HOST
- **Type**: String
- **Required**: No
- **Default**: `backend` (Docker), `localhost` (local)
- **Description**: Backend service hostname
- **Example**: `BACKEND_HOST=backend`

#### BACKEND_PORT
- **Type**: Integer
- **Required**: No
- **Default**: `8009`
- **Description**: Backend service port
- **Example**: `BACKEND_PORT=8009`

#### FRONTEND_HOST
- **Type**: String
- **Required**: No
- **Default**: `dashboard` (Docker), `localhost` (local)
- **Description**: Frontend service hostname
- **Example**: `FRONTEND_HOST=dashboard`

#### FRONTEND_PORT
- **Type**: Integer
- **Required**: No
- **Default**: `5179`
- **Description**: Frontend service port
- **Example**: `FRONTEND_PORT=5179`

### Resource Limits

#### DOCKER_MEMORY_LIMIT
- **Type**: String
- **Required**: No
- **Default**: `512m`
- **Description**: Container memory limit
- **Example**: `DOCKER_MEMORY_LIMIT=1g`

#### DOCKER_CPU_LIMIT
- **Type**: Float
- **Required**: No
- **Default**: `0.5`
- **Description**: CPU cores limit
- **Example**: `DOCKER_CPU_LIMIT=1.0`

## 🚀 Frontend Variables (Vite)

All frontend environment variables must be prefixed with `VITE_`

### API Configuration

#### VITE_API_BASE_URL
- **Type**: URL
- **Required**: Yes
- **Default**: `http://localhost:8009`
- **Description**: Backend API base URL
- **Example**: `VITE_API_BASE_URL=http://localhost:8009`

#### VITE_WS_URL
- **Type**: URL
- **Required**: For WebSocket
- **Default**: `ws://localhost:8009`
- **Description**: WebSocket server URL
- **Example**: `VITE_WS_URL=ws://localhost:8009`

#### VITE_ENABLE_WEBSOCKET
- **Type**: Boolean
- **Required**: No
- **Default**: `true`
- **Description**: Enable WebSocket features
- **Example**: `VITE_ENABLE_WEBSOCKET=true`

### Pusher Frontend

#### VITE_PUSHER_KEY
- **Type**: String
- **Required**: If Pusher enabled
- **Description**: Pusher public key for frontend
- **Example**: `VITE_PUSHER_KEY=abc123def456`

#### VITE_PUSHER_CLUSTER
- **Type**: String
- **Required**: If Pusher enabled
- **Default**: `us2`
- **Description**: Pusher cluster for frontend
- **Example**: `VITE_PUSHER_CLUSTER=us2`

#### VITE_PUSHER_AUTH_ENDPOINT
- **Type**: String
- **Required**: No
- **Default**: `/pusher/auth`
- **Description**: Pusher auth endpoint
- **Example**: `VITE_PUSHER_AUTH_ENDPOINT=/pusher/auth`

## 📊 Monitoring & Analytics

### Sentry

#### SENTRY_DSN
- **Type**: String
- **Required**: For error tracking
- **Security**: MEDIUM
- **Description**: Sentry project DSN
- **Example**: `SENTRY_DSN=https://...@sentry.io/...`

#### SENTRY_ENVIRONMENT
- **Type**: String
- **Required**: No
- **Default**: Value of `ENVIRONMENT`
- **Description**: Sentry environment tag
- **Example**: `SENTRY_ENVIRONMENT=production`

#### SENTRY_TRACES_SAMPLE_RATE
- **Type**: Float
- **Required**: No
- **Default**: `0.1`
- **Range**: `0.0` to `1.0`
- **Description**: Performance monitoring sample rate
- **Example**: `SENTRY_TRACES_SAMPLE_RATE=0.1`

### Monitoring

#### ENABLE_METRICS
- **Type**: Boolean
- **Required**: No
- **Default**: `true`
- **Description**: Enable Prometheus metrics
- **Example**: `ENABLE_METRICS=true`

#### METRICS_PORT
- **Type**: Integer
- **Required**: No
- **Default**: `9090`
- **Description**: Metrics endpoint port
- **Example**: `METRICS_PORT=9090`

## 🔄 Migration from Old Environment

If migrating from the pre-September 2025 setup:

### Old Variables (Deprecated)
```bash
# These are no longer used
REACT_APP_*  # Replaced with VITE_*
NODE_ENV     # Use ENVIRONMENT
MONGO_URL    # Replaced with DATABASE_URL (PostgreSQL)
```

### Migration Steps
1. Backup old `.env` file
2. Copy new `.env.example`
3. Map old values to new variables
4. Test in development first
5. Deploy to staging
6. Deploy to production

## 🛡️ Security Best Practices

### Development
```bash
# Use different keys for each environment
JWT_SECRET_KEY=dev_key_only_for_local_development
DATABASE_URL=postgresql://dev_user:dev_pass@localhost/dev_db
```

### Staging
```bash
# Use stronger keys than development
JWT_SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=postgresql://staging_user:$(openssl rand -base64 32)@staging-db/staging
```

### Production
```bash
# Use Docker Secrets or external vault
# Never store production secrets in .env files
docker secret create jwt_secret_key -
docker secret create db_password -
```

### Key Rotation Schedule
- **JWT_SECRET_KEY**: Every 30 days
- **Database passwords**: Every 60 days
- **API keys**: Every 90 days
- **Service tokens**: Every 7 days

## 📝 Environment File Templates

### Minimal Development (.env.development)
```env
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=postgresql://toolboxai:devpass2024@localhost:5432/toolboxai
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=dev_secret_key_do_not_use_in_production
```

### Full Development (.env.development.full)
```env
# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database
DATABASE_URL=postgresql://toolboxai:devpass2024@localhost:5432/toolboxai
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET_KEY=dev_secret_key_do_not_use_in_production

# AI Services (optional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Realtime
PUSHER_ENABLED=true
PUSHER_APP_ID=...
PUSHER_KEY=...
PUSHER_SECRET=...
PUSHER_CLUSTER=us2

# Frontend
VITE_API_BASE_URL=http://localhost:8009
VITE_PUSHER_KEY=...
VITE_PUSHER_CLUSTER=us2
```

### Production (.env.production)
```env
# Never commit this file!
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# Use Docker Secrets instead
# See DEPLOYMENT.md for production setup
```

## 🔧 Validation Script

Use this script to validate your environment:

```python
#!/usr/bin/env python3
# validate_env.py

import os
import sys
from pathlib import Path

required = [
    'DATABASE_URL',
    'REDIS_URL',
    'JWT_SECRET_KEY',
]

optional_with_defaults = {
    'ENVIRONMENT': 'development',
    'DEBUG': 'false',
    'LOG_LEVEL': 'INFO',
}

warnings = []
errors = []

# Check required
for var in required:
    if not os.getenv(var):
        errors.append(f"❌ Missing required: {var}")

# Check optional
for var, default in optional_with_defaults.items():
    if not os.getenv(var):
        warnings.append(f"⚠️  Missing optional: {var} (will use: {default})")

# Security checks
if os.getenv('JWT_SECRET_KEY') == 'dev_secret_key_do_not_use_in_production':
    if os.getenv('ENVIRONMENT') == 'production':
        errors.append("❌ Using development JWT key in production!")

# Print results
if errors:
    print("Environment validation failed:")
    for error in errors:
        print(error)
    sys.exit(1)

if warnings:
    print("Environment warnings:")
    for warning in warnings:
        print(warning)

print("✅ Environment validation passed!")
```

## 🆘 Troubleshooting

### Common Issues

#### "JWT_SECRET_KEY not set"
```bash
# Generate a secure key
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env
```

#### "Cannot connect to database"
```bash
# Check PostgreSQL is running
docker compose ps postgres
# Check connection string
echo $DATABASE_URL
```

#### "Redis connection refused"
```bash
# Check Redis is running
docker compose ps redis
# Test connection
redis-cli ping
```

#### "Pusher not working"
```bash
# Verify all Pusher vars are set
env | grep PUSHER
# Check cluster matches between backend and frontend
```

## 📚 Additional Resources

- [Docker Secrets Documentation](https://docs.docker.com/engine/swarm/secrets/)
- [12-Factor App Environment Config](https://12factor.net/config)
- [OWASP Environment Security](https://owasp.org/www-project-secrets-management-cheat-sheet/)
- [PostgreSQL Connection Strings](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING)

---

*Environment Variables Documentation v1.0.0*
*Security-first configuration following September 2025 audit*