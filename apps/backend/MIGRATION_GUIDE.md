# Backend Migration Guide

## Overview

This guide provides step-by-step instructions for migrating to the new ToolboxAI backend architecture, including breaking changes, environment updates, and database migrations.

## Migration Timeline

### Current Version: 2.0.0 (Post-Refactoring)
### Previous Version: 1.x.x (Legacy Architecture)

**Migration Period**: September 2025
**Estimated Downtime**: 2-4 hours for production migration

## Pre-Migration Checklist

### 1. **Environment Preparation**
- [ ] Backup current database
- [ ] Export Redis data
- [ ] Document current environment variables
- [ ] Test new configuration in staging
- [ ] Verify external service integrations

### 2. **Dependency Verification**
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ for dashboard
- [ ] PostgreSQL 15+ accessible
- [ ] Redis 7+ available
- [ ] Docker (optional but recommended)

### 3. **Service Account Setup**
- [ ] OpenAI API key with sufficient credits
- [ ] Pusher account and app credentials
- [ ] Sentry project for error tracking
- [ ] Supabase project (optional)

## Step-by-Step Migration

### Step 1: Database Schema Migration

#### 1.1 Backup Current Database
```bash
# PostgreSQL backup
pg_dump -h localhost -U your_user -d your_database > backup_pre_migration.sql

# Redis backup (if applicable)
redis-cli --rdb backup_redis_pre_migration.rdb
```

#### 1.2 Update Database Connection
```bash
# Update DATABASE_URL format
# Old format
DATABASE_URL=postgresql://user:pass@host:port/db

# New format (same, but verify connection)
DATABASE_URL=postgresql://eduplatform:eduplatform2024@localhost/educational_platform_dev
```

#### 1.3 Run Alembic Migrations
```bash
# Navigate to backend directory
cd apps/backend

# Initialize Alembic (if not already done)
alembic init alembic

# Create migration for schema changes
alembic revision --autogenerate -m "Migration to v2.0 architecture"

# Review the generated migration file before applying
# Check: alembic/versions/xxx_migration_to_v2_architecture.py

# Apply migration
alembic upgrade head
```

### Step 2: Environment Variable Updates

#### 2.1 Update Root .env File
```bash
# Core Configuration
DATABASE_URL=postgresql://eduplatform:eduplatform2024@localhost/educational_platform_dev
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=your-new-super-secure-jwt-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# AI Services
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
MAX_TOKENS=2048

# Real-time Services (NEW - Required for v2.0)
PUSHER_ENABLED=true
PUSHER_APP_ID=your-pusher-app-id
PUSHER_KEY=your-pusher-key
PUSHER_SECRET=your-pusher-secret
PUSHER_CLUSTER=us2
PUSHER_SSL=true

# Monitoring (NEW - Recommended)
SENTRY_DSN=your-sentry-dsn
SENTRY_ENVIRONMENT=production

# Feature Flags
SKIP_AUTH=false
ROJO_ENABLED=true
ROJO_HOST=localhost
ROJO_PORT=34872

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
WS_RATE_LIMIT_PER_MINUTE=100

# Agent Configuration (NEW)
MAX_CONCURRENT_GENERATIONS=10
MAX_CONTENT_GENERATION_TIME=300

# Legacy WebSocket (Maintained for compatibility)
WS_MAX_CONNECTIONS=1000
WS_HEARTBEAT_INTERVAL=30
```

#### 2.2 Update Dashboard Environment
```bash
# Create apps/dashboard/.env.local
VITE_API_BASE_URL=http://127.0.0.1:8009
VITE_WS_URL=http://127.0.0.1:8009
VITE_ENABLE_WEBSOCKET=true

# Pusher Configuration (NEW - Required)
VITE_PUSHER_KEY=your-pusher-key
VITE_PUSHER_CLUSTER=us2
VITE_PUSHER_AUTH_ENDPOINT=/pusher/auth

# Feature Flags
VITE_ENABLE_AGENTS=true
VITE_ENABLE_ROBLOX_INTEGRATION=true
```

### Step 3: Application Code Updates

#### 3.1 Import Path Changes
```python
# OLD IMPORTS (Update these)
from src.config import settings
from backend.agents import agent_manager

# NEW IMPORTS
from apps.backend.core.config import settings
from apps.backend.services.agent_service import get_agent_service
```

#### 3.2 Agent Service Migration
```python
# OLD: Direct agent usage
from backend.agents.content_agent import ContentAgent
agent = ContentAgent()
result = await agent.generate_content(...)

# NEW: Service-based approach
from apps.backend.services.agent_service import get_agent_service
agent_service = get_agent_service()
result = await agent_service.execute_task(
    agent_type="content_generator",
    task_type="generate_content",
    task_data={
        "subject": "Mathematics",
        "grade_level": 5,
        "objectives": ["Learn fractions"]
    }
)
```

#### 3.3 WebSocket to Pusher Migration
```javascript
// OLD: WebSocket usage
const ws = new WebSocket('ws://localhost:8009/ws/content');
ws.send(JSON.stringify({type: 'message', data: 'test'}));

// NEW: Pusher usage
import Pusher from 'pusher-js';
const pusher = new Pusher(process.env.VITE_PUSHER_KEY, {
  cluster: process.env.VITE_PUSHER_CLUSTER,
  authEndpoint: '/pusher/auth'
});

const channel = pusher.subscribe('content-generation');
channel.bind('generation-started', (data) => {
  console.log('Content generation started:', data);
});
```

### Step 4: Service Integration Updates

#### 4.1 Circuit Breaker Integration
```python
# NEW: Add circuit breaker to external API calls
from apps.backend.core.circuit_breaker import circuit_breaker

@circuit_breaker("external_api", failure_threshold=3, timeout=30.0)
async def call_openai_api():
    # Your OpenAI API call here
    pass
```

#### 4.2 Rate Limiting Setup
```python
# NEW: Rate limiting configuration
from apps.backend.core.rate_limiter import RateLimitConfig

rate_limit_config = RateLimitConfig(
    requests_per_minute=60,
    burst_size=10,
    window_size=60
)
```

### Step 5: Testing the Migration

#### 5.1 Backend Health Check
```bash
# Start the backend
cd apps/backend
uvicorn main:app --host 127.0.0.1 --port 8009 --reload

# Test health endpoints
curl http://localhost:8009/health
curl http://localhost:8009/health/agents
curl http://localhost:8009/health/mcp
```

#### 5.2 Dashboard Integration Test
```bash
# Start the dashboard
cd apps/dashboard
npm install
npm run dev

# Test Pusher connection
# Check browser console for Pusher connection messages
```

#### 5.3 Agent Service Test
```bash
# Test agent execution
curl -X POST http://localhost:8009/api/v1/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "content_generator",
    "task_type": "generate_content",
    "task_data": {
      "subject": "Test",
      "grade_level": 5
    }
  }'
```

### Step 6: Production Deployment

#### 6.1 Environment-Specific Configurations
```bash
# Production environment variables
ENVIRONMENT=production
DEBUG=false
SENTRY_ENVIRONMENT=production
CORS_ORIGINS=["https://yourdomain.com"]

# Production database
DATABASE_URL=postgresql://prod_user:prod_pass@prod_host:5432/prod_db

# Production Pusher
PUSHER_SSL=true
PUSHER_CLUSTER=us-east-1  # Choose appropriate cluster
```

#### 6.2 Security Hardening
```bash
# Generate secure JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update CORS origins
CORS_ORIGINS=["https://app.yourdomain.com", "https://admin.yourdomain.com"]

# Enable security headers
SECURITY_HEADERS_ENABLED=true
```

## Breaking Changes

### 1. **API Endpoint Changes**

#### Agent Endpoints (Updated)
```bash
# OLD
POST /agents/generate

# NEW
POST /api/v1/agents/execute
```

#### Authentication Endpoints (Updated)
```bash
# OLD
POST /auth/login

# NEW
POST /api/v1/auth/login
```

### 2. **Configuration Changes**

#### Settings Import (Breaking)
```python
# OLD
from config import settings

# NEW
from apps.backend.core.config import settings
```

#### WebSocket Events (Breaking)
```javascript
// OLD event names
'content_generated'
'agent_status_update'

// NEW event names
'content-generated'
'agent-status-update'
```

### 3. **Database Schema Changes**

#### New Tables Added
- `agent_instances` - Agent lifecycle management
- `task_executions` - Task execution history
- `agent_metrics` - Performance metrics
- `circuit_breaker_state` - Circuit breaker status

#### Modified Tables
- `users` - Added role-based fields
- `educational_content` - Added quality_score field
- `sessions` - Enhanced with JWT token tracking

### 4. **Service Dependencies**

#### Required Services (New)
- **Pusher**: Real-time communication (replaces WebSocket)
- **Redis**: Required for rate limiting and caching
- **Sentry**: Recommended for error tracking

#### Optional Services (New)
- **Supabase**: Enhanced agent metrics
- **Docker**: Development environment

## Rollback Procedures

### 1. **Database Rollback**
```bash
# Rollback database migration
alembic downgrade -1

# Restore from backup if needed
psql -h localhost -U your_user -d your_database < backup_pre_migration.sql
```

### 2. **Application Rollback**
```bash
# Switch to previous version
git checkout v1.x.x

# Restore old environment variables
cp .env.backup .env

# Restart services
```

### 3. **Service Rollback**
```bash
# Disable new features
PUSHER_ENABLED=false
AGENT_SERVICE_ENABLED=false

# Use legacy WebSocket
WS_ENABLED=true
```

## Post-Migration Verification

### 1. **Functional Tests**
- [ ] User authentication working
- [ ] Content generation functional
- [ ] Dashboard real-time updates
- [ ] Roblox integration operational
- [ ] Agent system responsive

### 2. **Performance Tests**
- [ ] Response times under 500ms
- [ ] WebSocket/Pusher connections stable
- [ ] Database queries optimized
- [ ] Memory usage within limits

### 3. **Monitoring Setup**
- [ ] Sentry error tracking active
- [ ] Health check endpoints responding
- [ ] Circuit breaker status monitoring
- [ ] Agent performance metrics

## Troubleshooting

### Common Issues

#### 1. **Import Errors**
```bash
# Error: Module not found
ModuleNotFoundError: No module named 'apps.backend.core.config'

# Solution: Update Python path
export PYTHONPATH="/path/to/project:$PYTHONPATH"
```

#### 2. **Pusher Connection Failures**
```bash
# Error: Pusher connection failed
# Solution: Verify credentials
curl -X POST https://api-{cluster}.pusherapp.com/apps/{app_id}/events \
  -H "Authorization: key={key}:{secret}" \
  -H "Content-Type: application/json"
```

#### 3. **Database Connection Issues**
```bash
# Error: Database connection refused
# Solution: Check connection string and permissions
psql $DATABASE_URL -c "SELECT version();"
```

#### 4. **Agent Service Not Starting**
```bash
# Error: Agent service initialization failed
# Solution: Check dependencies and imports
python -c "from apps.backend.services.agent_service import get_agent_service; print('OK')"
```

### Performance Issues

#### 1. **Slow Response Times**
- Check circuit breaker status
- Monitor database connection pool
- Verify Redis connectivity
- Review agent utilization

#### 2. **Memory Usage**
- Monitor agent instance count
- Check for memory leaks in AI models
- Verify garbage collection settings

#### 3. **Real-time Latency**
- Test Pusher channel performance
- Monitor WebSocket fallback usage
- Check network connectivity

## Support and Resources

### Documentation
- [Backend Architecture](./ARCHITECTURE.md)
- [Configuration Guide](./CONFIGURATION.md)
- [API Documentation](../docs/api/)

### Monitoring
- Health Check: `http://your-domain/health`
- Agent Status: `http://your-domain/health/agents`
- Circuit Breaker Status: `http://your-domain/api/v1/system/circuit-breakers`

### Emergency Contacts
- Technical Lead: [Contact Information]
- DevOps Team: [Contact Information]
- Database Admin: [Contact Information]

## Migration Completion Checklist

- [ ] Database migration completed successfully
- [ ] Environment variables updated
- [ ] Application code updated for new imports
- [ ] Pusher integration configured and tested
- [ ] Agent service operational
- [ ] Circuit breakers functioning
- [ ] Rate limiting active
- [ ] Health checks passing
- [ ] Dashboard real-time features working
- [ ] Performance monitoring active
- [ ] Rollback procedure documented and tested
- [ ] Team trained on new architecture
- [ ] Documentation updated
- [ ] Production deployment completed

**Migration Status**: [ ] In Progress [ ] Completed [ ] Rolled Back

**Migration Lead**: _______________
**Date Completed**: _______________
**Post-Migration Review Date**: _______________