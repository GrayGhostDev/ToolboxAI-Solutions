# Production Environment Configuration Template

**Created:** October 1, 2025
**Purpose:** Production-ready environment configuration for infrastructure dashboard

## Overview

This document provides production-ready environment variable templates for the infrastructure monitoring dashboard. Use these templates to configure your production, staging, and development environments.

## Environment Files

### 1. Backend Environment (.env)

Create `apps/backend/.env` or root `.env`:

```bash
# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# PostgreSQL Database
DATABASE_URL=postgresql://YOUR_DB_USER:YOUR_DB_PASSWORD@YOUR_DB_HOST:5432/YOUR_DB_NAME

# Individual database credentials (for Docker)
POSTGRES_USER=YOUR_DB_USER
POSTGRES_PASSWORD=YOUR_SECURE_DB_PASSWORD
POSTGRES_DB=YOUR_DB_NAME
POSTGRES_HOST=postgres  # Use "localhost" for local dev, "postgres" for Docker

# ============================================================================
# REDIS CONFIGURATION
# ============================================================================

REDIS_URL=redis://YOUR_REDIS_HOST:6379/0
REDIS_PASSWORD=YOUR_SECURE_REDIS_PASSWORD  # Leave empty if no password

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================

# Environment
ENVIRONMENT=production  # Options: development, staging, production
DEBUG=false  # Set to "true" only for development

# Security
SECRET_KEY=YOUR_SUPER_SECRET_KEY_MINIMUM_32_CHARACTERS_LONG_AND_RANDOM
JWT_SECRET_KEY=YOUR_JWT_SECRET_KEY_MINIMUM_64_CHARACTERS_WITH_HIGH_ENTROPY
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=https://your-frontend-domain.com,https://your-dashboard.com
CORS_ALLOW_CREDENTIALS=true

# ============================================================================
# PUSHER CONFIGURATION (Real-time Features)
# ============================================================================

PUSHER_APP_ID=YOUR_PUSHER_APP_ID
PUSHER_KEY=YOUR_PUSHER_KEY
PUSHER_SECRET=YOUR_PUSHER_SECRET
PUSHER_CLUSTER=YOUR_PUSHER_CLUSTER  # e.g., us2, eu, ap1

# ============================================================================
# OBSERVABILITY & MONITORING
# ============================================================================

# Sentry Error Tracking (Optional)
SENTRY_DSN=https://YOUR_SENTRY_DSN@sentry.io/YOUR_PROJECT_ID
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of transactions

# Infrastructure Metrics
INFRASTRUCTURE_METRICS_ENABLED=true
METRICS_COLLECTION_INTERVAL=5  # seconds
METRICS_RETENTION_DAYS=30

# Health Check Thresholds
HEALTH_CPU_WARNING=70.0
HEALTH_CPU_CRITICAL=90.0
HEALTH_MEMORY_WARNING=75.0
HEALTH_MEMORY_CRITICAL=90.0
HEALTH_DISK_WARNING=80.0
HEALTH_DISK_CRITICAL=95.0

# ============================================================================
# ADMIN CREDENTIALS (For Automated Scripts)
# ============================================================================

ADMIN_EMAIL=admin@your-domain.com
ADMIN_PASSWORD=YOUR_SECURE_ADMIN_PASSWORD

# ============================================================================
# ALERTING CONFIGURATION
# ============================================================================

# Slack Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL=#infrastructure-alerts

# Email Notifications (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=YOUR_EMAIL_APP_PASSWORD
ALERT_EMAIL_TO=devops@your-domain.com
ALERT_EMAIL_FROM=infrastructure@your-domain.com

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=/var/log/toolboxai/backend.log
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=5

# ============================================================================
# PERFORMANCE TUNING
# ============================================================================

# Database Pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Worker Configuration
WORKERS=4  # Number of Uvicorn workers
MAX_CONNECTIONS=1000

# ============================================================================
# FEATURE FLAGS
# ============================================================================

ENABLE_SWAGGER_UI=false  # Disable in production
ENABLE_METRIC_AGGREGATIONS=true
ENABLE_REAL_TIME_STREAMING=true
ENABLE_ALERT_NOTIFICATIONS=true
```

### 2. Frontend Environment (.env.local or .env.production)

Create `apps/dashboard/.env.local` or `.env.production`:

```bash
# ============================================================================
# API CONFIGURATION
# ============================================================================

# Backend API Base URL
VITE_API_BASE_URL=https://api.your-domain.com
VITE_WS_URL=https://api.your-domain.com

# ============================================================================
# PUSHER CONFIGURATION (Must match backend)
# ============================================================================

VITE_PUSHER_KEY=YOUR_PUSHER_KEY
VITE_PUSHER_CLUSTER=YOUR_PUSHER_CLUSTER
VITE_PUSHER_AUTH_ENDPOINT=/pusher/auth

# ============================================================================
# FEATURE FLAGS
# ============================================================================

VITE_ENABLE_WEBSOCKET=false  # Deprecated, using Pusher
VITE_ENABLE_CLERK_AUTH=false  # Set true if using Clerk
VITE_ENABLE_REAL_TIME=true
VITE_ENABLE_DARK_MODE=true

# ============================================================================
# MONITORING & ANALYTICS
# ============================================================================

# Sentry Frontend Monitoring (Optional)
VITE_SENTRY_DSN=https://YOUR_FRONTEND_SENTRY_DSN@sentry.io/YOUR_PROJECT_ID
VITE_SENTRY_ENVIRONMENT=production

# Google Analytics (Optional)
VITE_GA_TRACKING_ID=G-XXXXXXXXXX

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================

VITE_APP_NAME=ToolboxAI Infrastructure Dashboard
VITE_APP_VERSION=1.0.0
VITE_ENVIRONMENT=production

# Refresh Intervals (milliseconds)
VITE_METRICS_REFRESH_INTERVAL=5000  # 5 seconds
VITE_HEALTH_CHECK_INTERVAL=60000  # 1 minute
```

## Security Best Practices

### 1. Generate Secure Secrets

**JWT Secret (64+ characters):**
```bash
# Using OpenSSL
openssl rand -hex 32

# Using Python
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# Expected output format:
# qL5r8mN9pD2vK7nJ4yT6hG3fB1zX0wC8eA5sV2uQ1iO9pM7nK4jR3tY6hU2gF5d
```

**Application Secret Key (32+ characters):**
```bash
# Using OpenSSL
openssl rand -hex 32

# Using uuidgen
uuidgen | tr -d '-' | tr '[:upper:]' '[:lower:]'
```

**Database Passwords:**
```bash
# Generate strong password
python3 -c "import secrets, string; chars=string.ascii_letters+string.digits+string.punctuation; print(''.join(secrets.choice(chars) for _ in range(32)))"
```

### 2. Environment Variable Validation

Before deployment, validate all environment variables:

```bash
# Check required variables
python3 << 'EOF'
import os

required_vars = [
    'DATABASE_URL',
    'REDIS_URL',
    'SECRET_KEY',
    'JWT_SECRET_KEY',
    'PUSHER_APP_ID',
    'PUSHER_KEY',
    'PUSHER_SECRET',
]

missing = [var for var in required_vars if not os.getenv(var)]

if missing:
    print(f"❌ Missing required environment variables:")
    for var in missing:
        print(f"   - {var}")
    exit(1)
else:
    print("✅ All required environment variables are set")
EOF
```

### 3. Secret Management

**Production Recommendations:**

1. **Docker Secrets** (Recommended for Docker deployments)
   ```bash
   # Create secrets
   echo "your_db_password" | docker secret create db_password -
   echo "your_jwt_secret" | docker secret create jwt_secret -

   # Reference in docker-compose.yml
   secrets:
     - db_password
     - jwt_secret
   ```

2. **AWS Secrets Manager**
   ```bash
   # Store secret
   aws secretsmanager create-secret \
     --name production/toolboxai/database \
     --secret-string '{"password":"YOUR_DB_PASSWORD"}'

   # Retrieve in application
   aws secretsmanager get-secret-value \
     --secret-id production/toolboxai/database
   ```

3. **HashiCorp Vault**
   ```bash
   # Store secret
   vault kv put secret/toolboxai/prod \
     database_url="postgresql://..." \
     jwt_secret="..."

   # Retrieve secret
   vault kv get secret/toolboxai/prod
   ```

## Environment-Specific Configurations

### Development Environment

```bash
# .env.development
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=postgresql://eduplatform:eduplatform2024@localhost:5432/educational_platform_dev
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=http://localhost:5179,http://localhost:3000
ENABLE_SWAGGER_UI=true
LOG_LEVEL=DEBUG
```

### Staging Environment

```bash
# .env.staging
ENVIRONMENT=staging
DEBUG=false
DATABASE_URL=postgresql://staging_user:staging_pass@staging-db:5432/toolboxai_staging
REDIS_URL=redis://staging-redis:6379/0
CORS_ORIGINS=https://staging.your-domain.com
ENABLE_SWAGGER_UI=true
LOG_LEVEL=INFO
SENTRY_ENVIRONMENT=staging
```

### Production Environment

```bash
# .env.production
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://prod_user:prod_pass@prod-db:5432/toolboxai_production
REDIS_URL=redis://prod-redis:6379/0
CORS_ORIGINS=https://your-domain.com
ENABLE_SWAGGER_UI=false
LOG_LEVEL=WARNING
SENTRY_ENVIRONMENT=production
WORKERS=8
```

## Infrastructure Metrics Configuration

### Metric Collection Settings

```bash
# Collection frequency
METRICS_COLLECTION_INTERVAL=5  # seconds between collections

# Data retention
METRICS_RETENTION_DAYS=30  # days to keep raw metrics
AGGREGATION_RETENTION_DAYS=365  # days to keep aggregated metrics

# Storage optimization
ENABLE_HOURLY_AGGREGATIONS=true
ENABLE_DAILY_AGGREGATIONS=true
CLEANUP_SCHEDULE="0 2 * * *"  # Daily at 2 AM
```

### Alert Threshold Tuning

Adjust thresholds based on your infrastructure:

```bash
# High-performance servers
HEALTH_CPU_WARNING=80.0
HEALTH_CPU_CRITICAL=95.0
HEALTH_MEMORY_WARNING=85.0
HEALTH_MEMORY_CRITICAL=95.0

# Low-resource environments
HEALTH_CPU_WARNING=60.0
HEALTH_CPU_CRITICAL=80.0
HEALTH_MEMORY_WARNING=70.0
HEALTH_MEMORY_CRITICAL=85.0
```

## Verification Checklist

Use this checklist before deployment:

- [ ] All required environment variables are set
- [ ] Secrets are strong (32+ characters with high entropy)
- [ ] Database connection string is correct and accessible
- [ ] Redis connection works
- [ ] Pusher credentials are valid
- [ ] CORS origins include all frontend domains
- [ ] Sentry DSN is configured (if using Sentry)
- [ ] Admin credentials are secure
- [ ] Slack webhook is tested (if using alerts)
- [ ] Log directory exists and is writable
- [ ] Health check thresholds are appropriate
- [ ] Debug mode is disabled in production
- [ ] Swagger UI is disabled in production
- [ ] JWT secret has high entropy (64+ characters)
- [ ] Database password is strong
- [ ] No secrets are committed to version control

## Testing Environment Configuration

```bash
# Validate environment
python3 << 'EOF'
import os
from urllib.parse import urlparse

def validate_database_url(url):
    """Validate DATABASE_URL format"""
    try:
        result = urlparse(url)
        assert result.scheme in ['postgresql', 'postgres'], "Must be PostgreSQL"
        assert result.username, "Username required"
        assert result.password, "Password required"
        assert result.hostname, "Hostname required"
        assert result.path and len(result.path) > 1, "Database name required"
        return True
    except Exception as e:
        print(f"❌ DATABASE_URL invalid: {e}")
        return False

def validate_jwt_secret(secret):
    """Validate JWT secret strength"""
    if len(secret) < 64:
        print(f"⚠️  JWT secret too short: {len(secret)} chars (minimum 64)")
        return False

    # Check entropy
    unique_chars = len(set(secret))
    if unique_chars < 40:
        print(f"⚠️  JWT secret low entropy: {unique_chars} unique chars (minimum 40)")
        return False

    return True

# Run validations
database_url = os.getenv('DATABASE_URL', '')
jwt_secret = os.getenv('JWT_SECRET_KEY', '')

if validate_database_url(database_url):
    print("✅ DATABASE_URL format valid")

if validate_jwt_secret(jwt_secret):
    print("✅ JWT_SECRET_KEY strength good")
else:
    print("🔧 Generate new JWT secret:")
    print("   python3 -c \"import secrets; print(secrets.token_urlsafe(64))\"")
EOF
```

## Troubleshooting

### Issue: Environment variables not loading

**Solution:**
```bash
# Check .env file location
ls -la .env

# Load manually
export $(cat .env | grep -v '^#' | xargs)

# Verify loaded
env | grep DATABASE_URL
```

### Issue: Database connection fails

**Solution:**
```bash
# Test connection
psql "$DATABASE_URL" -c "SELECT 1"

# Check if database exists
psql -h localhost -U postgres -l | grep your_db_name

# Create database if missing
createdb -h localhost -U postgres your_db_name
```

### Issue: Pusher connection fails

**Solution:**
```bash
# Test Pusher credentials
curl -X POST "https://api-${VITE_PUSHER_CLUSTER}.pusher.com/apps/${PUSHER_APP_ID}/events" \
  -H "Content-Type: application/json" \
  -d '{"name":"test","channel":"test-channel","data":"{}"}'
```

---

**Last Updated:** October 1, 2025
**Version:** 1.0.0
