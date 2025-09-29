# Backend Migration Guide

## Table of Contents
- [Migration Overview](#migration-overview)
- [Breaking Changes](#breaking-changes)
- [Step-by-Step Migration](#step-by-step-migration)
- [Configuration Changes](#configuration-changes)
- [API Changes](#api-changes)
- [Database Migrations](#database-migrations)
- [Deployment Updates](#deployment-updates)
- [Rollback Procedures](#rollback-procedures)
- [Testing Migration](#testing-migration)
- [Troubleshooting](#troubleshooting)

## Migration Overview

This guide covers the migration from the legacy FastAPI architecture to the refactored modular system. The refactoring introduces:

### Key Improvements
- **Modular Router Architecture**: Separated endpoints into logical modules
- **Enhanced Security**: Circuit breakers, rate limiting, improved CORS
- **Real-time Migration**: Pusher Channels replacing WebSockets
- **Resilience Features**: Fault tolerance and retry mechanisms
- **Centralized Configuration**: Unified settings management
- **Improved Monitoring**: Enhanced logging and error tracking

### Migration Timeline
- **Preparation**: 1-2 days
- **Migration Execution**: 4-6 hours
- **Testing & Validation**: 1-2 days
- **Go-Live**: 1 hour

## Breaking Changes

### 1. WebSocket to Pusher Migration
**Impact**: High - affects real-time features

**Before**:
```javascript
// Legacy WebSocket connection
const ws = new WebSocket('ws://localhost:8009/ws/content');
```

**After**:
```javascript
// Pusher Channels connection
const pusher = new Pusher(process.env.VITE_PUSHER_KEY, {
  cluster: process.env.VITE_PUSHER_CLUSTER,
  authEndpoint: '/pusher/auth'
});
const channel = pusher.subscribe('content-generation');
```

### 2. Authentication Header Changes
**Impact**: Medium - affects API clients

**Before**:
```http
Authorization: Bearer <token>
```

**After**:
```http
Authorization: Bearer <token>
X-Request-ID: <correlation-id>
```

### 3. Error Response Format
**Impact**: Medium - affects error handling

**Before**:
```json
{
  "error": "Error message"
}
```

**After**:
```json
{
  "status": "error",
  "message": "Error message",
  "data": null,
  "metadata": {
    "timestamp": "2025-09-23T...",
    "request_id": "uuid",
    "error_code": "VALIDATION_ERROR"
  }
}
```

### 4. Environment Variable Changes
**Impact**: High - affects deployment

**New Required Variables**:
```bash
# Pusher Configuration
PUSHER_APP_ID=your-app-id
PUSHER_KEY=your-key
PUSHER_SECRET=your-secret
PUSHER_CLUSTER=us2

# Circuit Breaker Configuration
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT_SECONDS=60

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST_SIZE=20
```

## Step-by-Step Migration

### Phase 1: Preparation (1-2 days)

#### 1.1 Environment Setup
```bash
# Backup current environment
cp .env .env.backup

# Update environment variables
cat >> .env << EOF
# Pusher Configuration
PUSHER_APP_ID=your-app-id
PUSHER_KEY=your-key
PUSHER_SECRET=your-secret
PUSHER_CLUSTER=us2

# Circuit Breaker Settings
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT_SECONDS=60

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST_SIZE=20
EOF
```

#### 1.2 Database Backup
```bash
# Backup PostgreSQL database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup Redis data
redis-cli --rdb backup_redis_$(date +%Y%m%d_%H%M%S).rdb
```

#### 1.3 Dependency Updates
```bash
# Update Python dependencies
pip install -r requirements.txt

# Install new dependencies
pip install pusher==3.3.2
```

### Phase 2: Configuration Migration (2-4 hours)

#### 2.1 Update main.py Configuration
```python
# Update imports for new middleware
from apps.backend.api.middleware.resilience import (
    ResilienceMiddleware,
    RetryMiddleware,
    BulkheadMiddleware
)
from apps.backend.core.rate_limiter import RateLimitMiddleware

# Add new middleware to app
if RESILIENCE_AVAILABLE:
    app.add_middleware(ResilienceMiddleware)
    app.add_middleware(RetryMiddleware)
    app.add_middleware(BulkheadMiddleware)
    app.add_middleware(RateLimitMiddleware)
```

#### 2.2 Router Registration
```python
# Update router imports
from apps.backend.api.v1.endpoints.pusher_auth import router as pusher_auth_router

# Register new routers
app.include_router(pusher_auth_router, prefix="/api/v1")
```

### Phase 3: Database Migration (1-2 hours)

#### 3.1 Run Alembic Migrations
```bash
# Generate migration for new features
alembic revision --autogenerate -m "Add circuit breaker and rate limit tables"

# Review migration file
# Edit migration file if needed

# Apply migration
alembic upgrade head
```

#### 3.2 Create Required Tables
```sql
-- Circuit breaker state table (if not auto-generated)
CREATE TABLE IF NOT EXISTS circuit_breaker_state (
    name VARCHAR(255) PRIMARY KEY,
    state VARCHAR(50) NOT NULL,
    failure_count INTEGER DEFAULT 0,
    last_failure_time TIMESTAMP,
    next_attempt_time TIMESTAMP
);

-- Rate limit tracking table
CREATE TABLE IF NOT EXISTS rate_limit_state (
    identifier VARCHAR(255) PRIMARY KEY,
    tokens FLOAT DEFAULT 0,
    last_refill TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Phase 4: API Client Updates (2-3 hours)

#### 4.1 Update Dashboard Frontend
```javascript
// Install Pusher client
npm install pusher-js

// Update API client to handle new response format
const handleApiResponse = (response) => {
  if (response.status === 'error') {
    throw new Error(response.message);
  }
  return response.data;
};

// Initialize Pusher
import Pusher from 'pusher-js';

const pusher = new Pusher(process.env.VITE_PUSHER_KEY, {
  cluster: process.env.VITE_PUSHER_CLUSTER,
  authEndpoint: '/pusher/auth'
});
```

#### 4.2 Update WebSocket Clients
```javascript
// Replace WebSocket connections
// Old WebSocket code:
// const ws = new WebSocket('ws://localhost:8009/ws/content');

// New Pusher code:
const channel = pusher.subscribe('content-generation');
channel.bind('content_progress', (data) => {
  updateProgressBar(data.progress);
});
```

### Phase 5: Testing Phase (1-2 days)

#### 5.1 Unit Testing
```bash
# Run backend tests
pytest apps/backend/tests/ -v

# Run frontend tests
cd apps/dashboard && npm test
```

#### 5.2 Integration Testing
```bash
# Test API endpoints
python scripts/test_api_endpoints.py

# Test real-time features
python scripts/test_pusher_integration.py

# Test circuit breaker functionality
python scripts/test_circuit_breakers.py
```

#### 5.3 Load Testing
```bash
# Install load testing tools
pip install locust

# Run load tests
locust -f scripts/load_test.py --host=http://localhost:8009
```

### Phase 6: Deployment (1 hour)

#### 6.1 Production Deployment
```bash
# Update production environment
scp .env production-server:/app/.env

# Restart services
systemctl restart toolboxai-backend
systemctl restart toolboxai-dashboard

# Monitor logs
tail -f /var/log/toolboxai/backend.log
```

#### 6.2 Health Check Verification
```bash
# Verify all health endpoints
curl http://localhost:8009/health
curl http://localhost:8009/resilience/status
curl http://localhost:8009/circuit-breakers/status
curl http://localhost:8009/pusher/status
```

## Configuration Changes

### Environment Variables

#### New Required Variables
```bash
# Pusher Real-time Communication
PUSHER_APP_ID=123456
PUSHER_KEY=your-pusher-key
PUSHER_SECRET=your-pusher-secret
PUSHER_CLUSTER=us2
PUSHER_ENABLED=true

# Circuit Breaker Configuration
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT_SECONDS=60
CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS=3

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST_SIZE=20
RATE_LIMIT_ENABLED=true

# Resilience Features
RETRY_MAX_ATTEMPTS=3
RETRY_BACKOFF_FACTOR=2
BULKHEAD_MAX_CONCURRENT=10
```

#### Updated Variables
```bash
# Enhanced CORS configuration
CORS_ALLOWED_ORIGINS=["http://localhost:3000","https://app.toolboxai.com"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOWED_METHODS=["GET","POST","PUT","DELETE","OPTIONS"]

# Enhanced logging
LOG_LEVEL=INFO
LOG_FORMAT=json
CORRELATION_ID_HEADER=X-Request-ID

# Monitoring enhancements
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
METRICS_ENABLED=true
```

### Settings Migration

#### Old Configuration (settings.py)
```python
class Settings:
    database_url: str
    redis_url: str
    jwt_secret: str
```

#### New Configuration (toolboxai_settings)
```python
class Settings(BaseSettings):
    # Database
    database_url: str
    redis_url: str

    # Authentication
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30

    # Pusher
    pusher_app_id: str
    pusher_key: str
    pusher_secret: str
    pusher_cluster: str = "us2"

    # Circuit Breaker
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout_seconds: int = 60

    # Rate Limiting
    rate_limit_requests_per_minute: int = 100
    rate_limit_burst_size: int = 20
```

## API Changes

### New Endpoints

#### Circuit Breaker Management
```
GET    /circuit-breakers/status           # Get all circuit breaker states
POST   /circuit-breakers/{name}/reset     # Reset specific circuit breaker
GET    /circuit-breakers/{name}/status    # Get specific circuit breaker status
```

#### Rate Limiting
```
GET    /rate-limit/usage/{identifier}     # Get rate limit usage for identifier
POST   /rate-limit/reset/{identifier}     # Reset rate limit for identifier
GET    /rate-limit/config                 # Get rate limiting configuration
```

#### Pusher Integration
```
POST   /pusher/auth                       # Authenticate private channels
POST   /pusher/trigger                    # Trigger events programmatically
POST   /pusher/webhook                    # Handle Pusher webhooks
GET    /pusher/status                     # Check Pusher connection status
```

#### Resilience Monitoring
```
GET    /resilience/status                 # Overall resilience system status
GET    /resilience/metrics                # Resilience metrics and statistics
POST   /resilience/config                 # Update resilience configuration
```

### Modified Endpoints

#### Enhanced Error Responses
All endpoints now return standardized error format:
```json
{
  "status": "error",
  "message": "Human readable error message",
  "data": null,
  "metadata": {
    "timestamp": "2025-09-23T10:30:00Z",
    "request_id": "uuid-string",
    "error_code": "VALIDATION_ERROR",
    "execution_time": 0.123
  }
}
```

#### Authentication Enhancement
All protected endpoints now support:
- Correlation ID tracking via `X-Request-ID` header
- Enhanced JWT validation
- Rate limiting per user/endpoint

## Database Migrations

### New Tables

#### Circuit Breaker State
```sql
CREATE TABLE circuit_breaker_state (
    name VARCHAR(255) PRIMARY KEY,
    state VARCHAR(50) NOT NULL CHECK (state IN ('CLOSED', 'OPEN', 'HALF_OPEN')),
    failure_count INTEGER DEFAULT 0,
    last_failure_time TIMESTAMP,
    next_attempt_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Rate Limit Tracking
```sql
CREATE TABLE rate_limit_state (
    identifier VARCHAR(255) PRIMARY KEY,
    tokens FLOAT DEFAULT 0,
    last_refill TIMESTAMP,
    window_start TIMESTAMP,
    request_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Agent Metrics (Enhanced)
```sql
ALTER TABLE agent_metrics ADD COLUMN circuit_breaker_trips INTEGER DEFAULT 0;
ALTER TABLE agent_metrics ADD COLUMN rate_limit_hits INTEGER DEFAULT 0;
ALTER TABLE agent_metrics ADD COLUMN avg_response_time FLOAT;
```

### Migration Scripts

#### Alembic Migration
```python
# migrations/versions/xxx_add_resilience_features.py
def upgrade():
    # Create circuit breaker state table
    op.create_table(
        'circuit_breaker_state',
        sa.Column('name', sa.String(255), primary_key=True),
        sa.Column('state', sa.String(50), nullable=False),
        sa.Column('failure_count', sa.Integer, default=0),
        sa.Column('last_failure_time', sa.TIMESTAMP),
        sa.Column('next_attempt_time', sa.TIMESTAMP),
        sa.Column('created_at', sa.TIMESTAMP, default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.TIMESTAMP, default=sa.func.current_timestamp())
    )

    # Create rate limit tracking table
    op.create_table(
        'rate_limit_state',
        sa.Column('identifier', sa.String(255), primary_key=True),
        sa.Column('tokens', sa.Float, default=0),
        sa.Column('last_refill', sa.TIMESTAMP),
        sa.Column('window_start', sa.TIMESTAMP),
        sa.Column('request_count', sa.Integer, default=0),
        sa.Column('created_at', sa.TIMESTAMP, default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.TIMESTAMP, default=sa.func.current_timestamp())
    )

def downgrade():
    op.drop_table('rate_limit_state')
    op.drop_table('circuit_breaker_state')
```

## Deployment Updates

### Docker Configuration

#### Updated Dockerfile
```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app
WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8009/health || exit 1

CMD ["uvicorn", "apps.backend.main:app", "--host", "0.0.0.0", "--port", "8009"]
```

#### Updated docker-compose.yml
```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8009:8009"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/db
      - REDIS_URL=redis://redis:6379
      - PUSHER_APP_ID=${PUSHER_APP_ID}
      - PUSHER_KEY=${PUSHER_KEY}
      - PUSHER_SECRET=${PUSHER_SECRET}
      - PUSHER_CLUSTER=${PUSHER_CLUSTER}
    depends_on:
      - postgres
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8009/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: toolboxai
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Kubernetes Configuration

#### Updated Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: toolboxai-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: toolboxai-backend
  template:
    metadata:
      labels:
        app: toolboxai-backend
    spec:
      containers:
      - name: backend
        image: toolboxai/backend:latest
        ports:
        - containerPort: 8009
        env:
        - name: PUSHER_APP_ID
          valueFrom:
            secretKeyRef:
              name: pusher-secret
              key: app-id
        livenessProbe:
          httpGet:
            path: /health
            port: 8009
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8009
          initialDelaySeconds: 5
          periodSeconds: 5
```

## Rollback Procedures

### Emergency Rollback (15 minutes)

#### 1. Stop New Version
```bash
# Stop current services
systemctl stop toolboxai-backend
docker-compose down

# Switch to backup version
cp .env.backup .env
git checkout previous-stable-tag
```

#### 2. Restore Database
```bash
# Restore database from backup
psql $DATABASE_URL < backup_YYYYMMDD_HHMMSS.sql

# Restore Redis data
redis-cli --rdb backup_redis_YYYYMMDD_HHMMSS.rdb
```

#### 3. Restart Services
```bash
# Start previous version
systemctl start toolboxai-backend
docker-compose up -d

# Verify rollback
curl http://localhost:8009/health
```

### Partial Rollback Options

#### Disable New Features
```bash
# Disable circuit breakers
export CIRCUIT_BREAKER_ENABLED=false

# Disable rate limiting
export RATE_LIMIT_ENABLED=false

# Disable Pusher (fallback to WebSocket)
export PUSHER_ENABLED=false

# Restart with old features disabled
systemctl restart toolboxai-backend
```

#### Database Rollback
```bash
# Rollback specific migrations
alembic downgrade -1  # Rollback one migration
alembic downgrade base  # Rollback all migrations
```

## Testing Migration

### Pre-Migration Testing
```bash
# Test current system
python scripts/test_current_system.py

# Backup validation
python scripts/validate_backup.py

# Dependency check
python scripts/check_dependencies.py
```

### Post-Migration Testing
```bash
# API endpoint tests
python scripts/test_api_endpoints.py

# Real-time feature tests
python scripts/test_pusher_integration.py

# Circuit breaker tests
python scripts/test_circuit_breakers.py

# Rate limiting tests
python scripts/test_rate_limiting.py

# Load testing
python scripts/load_test.py
```

### Automated Test Suite
```python
# tests/migration/test_migration.py
import pytest
import requests

def test_health_endpoint():
    response = requests.get("http://localhost:8009/health")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_pusher_auth():
    response = requests.post("http://localhost:8009/pusher/auth")
    assert response.status_code in [200, 401]  # Should not error

def test_circuit_breaker_status():
    response = requests.get("http://localhost:8009/circuit-breakers/status")
    assert response.status_code == 200

def test_rate_limit_functionality():
    # Make multiple requests to test rate limiting
    for i in range(5):
        response = requests.get("http://localhost:8009/health")
        assert response.status_code == 200
```

## Troubleshooting

### Common Issues

#### 1. Pusher Connection Failed
**Symptom**: Real-time features not working
**Solution**:
```bash
# Check Pusher configuration
curl http://localhost:8009/pusher/status

# Verify environment variables
echo $PUSHER_KEY
echo $PUSHER_CLUSTER

# Test Pusher authentication
curl -X POST http://localhost:8009/pusher/auth
```

#### 2. Circuit Breaker Not Working
**Symptom**: Services not protected from failures
**Solution**:
```bash
# Check circuit breaker status
curl http://localhost:8009/circuit-breakers/status

# Reset circuit breaker if stuck
curl -X POST http://localhost:8009/circuit-breakers/ai-service/reset

# Check logs for circuit breaker events
grep "circuit.breaker" /var/log/toolboxai/backend.log
```

#### 3. Rate Limiting Too Aggressive
**Symptom**: Legitimate requests being blocked
**Solution**:
```bash
# Check rate limit usage
curl http://localhost:8009/rate-limit/usage/user-123

# Adjust rate limits
export RATE_LIMIT_REQUESTS_PER_MINUTE=200
systemctl restart toolboxai-backend

# Reset rate limits for user
curl -X POST http://localhost:8009/rate-limit/reset/user-123
```

#### 4. Database Migration Failed
**Symptom**: App won't start due to schema mismatch
**Solution**:
```bash
# Check migration status
alembic current

# Manually fix migration
alembic stamp head
alembic revision --autogenerate -m "Fix schema"

# Or rollback and retry
alembic downgrade -1
alembic upgrade head
```

### Performance Issues

#### 1. High Response Times
**Diagnosis**:
```bash
# Check resilience metrics
curl http://localhost:8009/resilience/metrics

# Monitor circuit breaker trips
grep "circuit.breaker.open" /var/log/toolboxai/backend.log

# Check database performance
psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity;"
```

#### 2. Memory Usage Increase
**Diagnosis**:
```bash
# Monitor memory usage
top -p $(pgrep -f "uvicorn.*main:app")

# Check for memory leaks in circuit breakers
curl http://localhost:8009/circuit-breakers/status | jq '.memory_usage'

# Restart if necessary
systemctl restart toolboxai-backend
```

### Monitoring Commands

#### Health Check Script
```bash
#!/bin/bash
# scripts/health_check.sh

echo "Checking backend health..."
curl -f http://localhost:8009/health || exit 1

echo "Checking Pusher status..."
curl -f http://localhost:8009/pusher/status || exit 1

echo "Checking circuit breakers..."
curl -f http://localhost:8009/circuit-breakers/status || exit 1

echo "All systems operational!"
```

#### Log Monitoring
```bash
# Monitor real-time logs
tail -f /var/log/toolboxai/backend.log | grep -E "(ERROR|circuit.breaker|rate.limit|pusher)"

# Check for errors in last hour
grep -E "(ERROR|CRITICAL)" /var/log/toolboxai/backend.log | tail -100

# Monitor specific features
grep "pusher" /var/log/toolboxai/backend.log | tail -50
```

This migration guide ensures a smooth transition to the new architecture while providing comprehensive rollback and troubleshooting procedures.