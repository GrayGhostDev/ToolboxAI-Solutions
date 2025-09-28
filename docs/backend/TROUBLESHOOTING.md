# Backend Troubleshooting Guide

## Table of Contents
- [Quick Diagnostics](#quick-diagnostics)
- [Common Issues](#common-issues)
- [Debug Techniques](#debug-techniques)
- [Log Interpretation](#log-interpretation)
- [Performance Issues](#performance-issues)
- [Error Resolution](#error-resolution)
- [Service-Specific Issues](#service-specific-issues)
- [Development Issues](#development-issues)
- [Production Issues](#production-issues)
- [Monitoring and Alerts](#monitoring-and-alerts)

## Quick Diagnostics

### Health Check Commands
```bash
# Basic health check
curl http://localhost:8009/health

# Detailed system status
curl http://localhost:8009/health/verbose

# Check specific components
curl http://localhost:8009/circuit-breakers/status
curl http://localhost:8009/resilience/status
curl http://localhost:8009/pusher/status
curl http://localhost:8009/agents/health
```

### Quick Status Script
```bash
#!/bin/bash
# scripts/quick_status.sh

echo "=== ToolboxAI Backend Status Check ==="
echo

# Check if server is running
echo "1. Server Status:"
if curl -s http://localhost:8009/health > /dev/null; then
    echo "✓ Server is running"
else
    echo "✗ Server is not responding"
    exit 1
fi

# Check database
echo "2. Database Status:"
python -c "
import asyncio
from apps.backend.core.database import test_connection
try:
    asyncio.run(test_connection())
    print('✓ Database connected')
except Exception as e:
    print(f'✗ Database error: {e}')
"

# Check Redis
echo "3. Redis Status:"
python -c "
import redis
from apps.backend.core.config import settings
try:
    r = redis.from_url(settings.REDIS_URL)
    r.ping()
    print('✓ Redis connected')
except Exception as e:
    print(f'✗ Redis error: {e}')
"

# Check key services
echo "4. Service Status:"
services=("pusher" "agents" "circuit-breakers")
for service in "${services[@]}"; do
    if curl -s "http://localhost:8009/$service/status" | grep -q "success\|healthy"; then
        echo "✓ $service service operational"
    else
        echo "✗ $service service issues"
    fi
done

echo
echo "Status check complete."
```

### Environment Validation
```bash
# Check environment variables
python -c "
import os
required_vars = ['DATABASE_URL', 'JWT_SECRET_KEY', 'OPENAI_API_KEY', 'PUSHER_KEY']
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    print(f'Missing environment variables: {missing}')
else:
    print('✓ All required environment variables set')
"

# Check Python dependencies
pip check

# Check disk space
df -h

# Check memory usage
free -h

# Check process status
ps aux | grep uvicorn
```

## Common Issues

### 1. Server Won't Start

#### Symptoms
- `uvicorn` command fails
- Port binding errors
- Import errors on startup

#### Diagnosis
```bash
# Check if port is already in use
lsof -i :8009
netstat -tulpn | grep :8009

# Check Python environment
which python
python --version
pip list | grep fastapi

# Check for import errors
python -c "from apps.backend.main import app; print('✓ App imports successfully')"
```

#### Solutions
```bash
# Kill existing process
kill $(lsof -t -i:8009)

# Use different port
uvicorn apps.backend.main:app --port 8010

# Fix Python environment
source venv/bin/activate
pip install -r requirements.txt

# Check for syntax errors
python -m py_compile apps/backend/main.py
```

### 2. Database Connection Issues

#### Symptoms
- `sqlalchemy.exc.OperationalError`
- Connection timeouts
- Pool exhaustion errors

#### Diagnosis
```bash
# Test database connectivity
python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
async def test():
    engine = create_async_engine('$DATABASE_URL')
    async with engine.begin() as conn:
        result = await conn.execute('SELECT 1')
        print(f'Database test: {result.scalar()}')
    await engine.dispose()
asyncio.run(test())
"

# Check database server status
pg_isready -h localhost -p 5432

# Check connection parameters
python -c "
from apps.backend.core.config import settings
print(f'Database URL: {settings.DATABASE_URL}')
print(f'Pool size: {settings.DATABASE_POOL_SIZE}')
"
```

#### Solutions
```bash
# Start PostgreSQL (if local)
sudo systemctl start postgresql
# or with Docker
docker-compose up -d postgres

# Fix connection pool settings
export DATABASE_POOL_SIZE=20
export DATABASE_MAX_OVERFLOW=30

# Check and fix database URL
export DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname

# Run migrations if needed
alembic upgrade head
```

### 3. Authentication Failures

#### Symptoms
- `401 Unauthorized` errors
- JWT decode errors
- Token validation failures

#### Diagnosis
```bash
# Check JWT configuration
python -c "
from apps.backend.core.config import settings
print(f'JWT Secret length: {len(settings.JWT_SECRET_KEY)}')
print(f'JWT Algorithm: {settings.JWT_ALGORITHM}')
"

# Test token generation
python -c "
from apps.backend.api.auth.jwt_handler import create_access_token
token = create_access_token({'user_id': 1, 'role': 'admin'})
print(f'Test token: {token[:50]}...')
"

# Validate existing token
TOKEN='your-token-here'
python -c "
import jwt
from apps.backend.core.config import settings
try:
    payload = jwt.decode('$TOKEN', settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    print(f'Token valid: {payload}')
except Exception as e:
    print(f'Token invalid: {e}')
"
```

#### Solutions
```bash
# Generate new JWT secret
python -c "import secrets; print(f'JWT_SECRET_KEY={secrets.token_urlsafe(32)}')" >> .env

# Check token expiration
# Ensure system clocks are synchronized

# Verify CORS settings for authentication endpoints
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     http://localhost:8009/auth/login
```

### 4. Redis Connection Issues

#### Symptoms
- `redis.exceptions.ConnectionError`
- Cache miss errors
- Session storage failures

#### Diagnosis
```bash
# Test Redis connectivity
redis-cli ping

# Check Redis configuration
python -c "
from apps.backend.core.config import settings
print(f'Redis URL: {settings.REDIS_URL}')
"

# Test Redis from Python
python -c "
import redis
from apps.backend.core.config import settings
r = redis.from_url(settings.REDIS_URL)
r.set('test', 'value')
print(f'Redis test: {r.get('test').decode()}')
r.delete('test')
"
```

#### Solutions
```bash
# Start Redis (if local)
sudo systemctl start redis
# or with Docker
docker-compose up -d redis

# Check Redis memory usage
redis-cli info memory

# Clear Redis if needed (WARNING: clears all data)
redis-cli flushall

# Fix Redis URL
export REDIS_URL=redis://localhost:6379/0
```

### 5. AI Agent Issues

#### Symptoms
- Agent task timeouts
- OpenAI API errors
- Agent status "ERROR"

#### Diagnosis
```bash
# Check agent status
curl http://localhost:8009/agents/health

# Test OpenAI API connectivity
python -c "
import openai
from apps.backend.core.config import settings
openai.api_key = settings.OPENAI_API_KEY
try:
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[{'role': 'user', 'content': 'Hello'}],
        max_tokens=10
    )
    print('✓ OpenAI API working')
except Exception as e:
    print(f'✗ OpenAI API error: {e}')
"

# Check agent queue status
python -c "
from apps.backend.services.agent_service import get_agent_service
service = get_agent_service()
print(f'Active agents: {len(service.agents)}')
print(f'Queue size: {service.queue_size()}')
"
```

#### Solutions
```bash
# Restart agent service
curl -X POST http://localhost:8009/agents/restart

# Check OpenAI API key
echo $OPENAI_API_KEY | wc -c  # Should be > 40 characters

# Clear agent queue if stuck
curl -X POST http://localhost:8009/agents/clear-queue

# Reset circuit breakers for AI services
curl -X POST http://localhost:8009/circuit-breakers/openai-api/reset
```

### 6. Real-time Communication Issues

#### Symptoms
- Pusher connection failures
- WebSocket disconnections
- Missing real-time updates

#### Diagnosis
```bash
# Check Pusher status
curl http://localhost:8009/pusher/status

# Test Pusher authentication
curl -X POST http://localhost:8009/pusher/auth \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"socket_id": "test", "channel_name": "private-test"}'

# Check WebSocket connectivity (legacy)
python -c "
import websocket
try:
    ws = websocket.create_connection('ws://localhost:8009/ws/native')
    ws.send('test')
    result = ws.recv()
    print(f'WebSocket test: {result}')
    ws.close()
except Exception as e:
    print(f'WebSocket error: {e}')
"
```

#### Solutions
```bash
# Check Pusher configuration
python -c "
from apps.backend.core.config import settings
print(f'Pusher enabled: {settings.PUSHER_ENABLED}')
print(f'Pusher cluster: {settings.PUSHER_CLUSTER}')
"

# Test Pusher credentials
python -c "
import pusher
from apps.backend.core.config import settings
pusher_client = pusher.Pusher(
    app_id=settings.PUSHER_APP_ID,
    key=settings.PUSHER_KEY,
    secret=settings.PUSHER_SECRET,
    cluster=settings.PUSHER_CLUSTER
)
pusher_client.trigger('test-channel', 'test-event', {'message': 'test'})
print('✓ Pusher credentials working')
"

# Restart Pusher service
sudo systemctl restart pusher  # If using separate Pusher service
```

## Debug Techniques

### 1. Enabling Debug Mode

#### Environment Configuration
```bash
# Enable debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG

# Enable SQL query logging
export DATABASE_ECHO=true

# Enable detailed error responses
export FASTAPI_DEBUG=true

# Restart server
uvicorn apps.backend.main:app --reload --log-level debug
```

#### Code-Level Debugging
```python
# Add debug breakpoints
import pdb; pdb.set_trace()

# Or use ipdb for better interface
import ipdb; ipdb.set_trace()

# Add debug logging
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Variable value: {variable}")

# Use rich for better debug output
from rich import print as rprint
rprint({"debug_data": data, "timestamp": datetime.now()})
```

### 2. Request Tracing

#### Correlation ID Tracking
```python
# Enable correlation ID middleware
from apps.backend.core.logging import CorrelationIDMiddleware
app.add_middleware(CorrelationIDMiddleware)

# Add correlation ID to logs
logger.info("Processing request", extra={"correlation_id": request.state.correlation_id})

# Track request in Sentry
import sentry_sdk
sentry_sdk.set_tag("correlation_id", request.state.correlation_id)
```

#### Request Debugging
```bash
# Add debug headers to requests
curl -H "X-Debug: true" \
     -H "X-Request-ID: debug-123" \
     http://localhost:8009/api/v1/content

# Monitor request logs
tail -f logs/app.log | grep "debug-123"

# Use httpie for better request debugging
http GET localhost:8009/api/v1/content X-Debug:true
```

### 3. Database Debugging

#### Query Analysis
```python
# Enable query logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Use explain for slow queries
async with db.begin() as conn:
    result = await conn.execute(text("EXPLAIN ANALYZE SELECT * FROM users"))
    print(result.fetchall())

# Profile database operations
from apps.backend.core.logging import log_database_operation
with log_database_operation("complex_query"):
    result = await db.execute(complex_query)
```

#### Connection Pool Monitoring
```python
# Monitor connection pool
from apps.backend.core.database import engine
print(f"Pool size: {engine.pool.size()}")
print(f"Checked out: {engine.pool.checkedout()}")
print(f"Overflow: {engine.pool.overflow()}")
print(f"Invalid: {engine.pool.invalidated()}")
```

### 4. Performance Profiling

#### Application Profiling
```python
# Use cProfile for performance analysis
import cProfile
import pstats

def profile_endpoint():
    profiler = cProfile.Profile()
    profiler.enable()

    # Your code here
    result = expensive_operation()

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)

    return result
```

#### Memory Profiling
```bash
# Install memory profiler
pip install memory-profiler

# Profile memory usage
python -m memory_profiler apps/backend/main.py

# Monitor memory in real-time
python -c "
import psutil
import time
process = psutil.Process()
while True:
    memory = process.memory_info()
    print(f'Memory: {memory.rss / 1024 / 1024:.2f} MB')
    time.sleep(5)
"
```

## Log Interpretation

### Log Format Understanding

#### Structured JSON Logs
```json
{
  "timestamp": "2025-09-23T10:30:00.123Z",
  "level": "INFO",
  "logger": "apps.backend.api.v1.endpoints.content",
  "message": "Content created successfully",
  "correlation_id": "req-123-abc-456",
  "user_id": 42,
  "operation": "create_content",
  "execution_time": 0.234,
  "content_id": 789
}
```

#### Log Level Guidelines
```python
# DEBUG: Detailed information for diagnosing problems
logger.debug("Starting database transaction", extra={"user_id": user.id})

# INFO: General information about application flow
logger.info("User authenticated successfully", extra={"user_id": user.id, "role": user.role})

# WARNING: Something unexpected but not necessarily an error
logger.warning("Rate limit approaching", extra={"user_id": user.id, "remaining_requests": 5})

# ERROR: Error occurred but application continues
logger.error("Failed to send notification", extra={"user_id": user.id, "error": str(e)})

# CRITICAL: Serious error that may cause application to abort
logger.critical("Database connection lost", extra={"error": str(e)})
```

### Common Log Patterns

#### Authentication Issues
```bash
# Failed login attempts
grep "authentication.failed" logs/app.log

# Token validation errors
grep "jwt.decode.error" logs/app.log

# Rate limiting triggers
grep "rate.limit.exceeded" logs/app.log
```

#### Database Issues
```bash
# Connection problems
grep "database.connection" logs/app.log

# Slow queries
grep "database.slow_query" logs/app.log | grep "execution_time"

# Pool exhaustion
grep "database.pool.exhausted" logs/app.log
```

#### Agent System Issues
```bash
# Agent failures
grep "agent.task.failed" logs/app.log

# Circuit breaker triggers
grep "circuit.breaker.open" logs/app.log

# Agent timeout issues
grep "agent.timeout" logs/app.log
```

### Log Analysis Scripts

#### Error Summary Script
```bash
#!/bin/bash
# scripts/log_analysis.sh

echo "=== Error Summary (Last 24 hours) ==="
echo

# Count errors by type
echo "Error counts:"
grep -h "\"level\":\"ERROR\"" logs/app.log* | \
  jq -r '.message' | \
  sort | uniq -c | sort -nr | head -10

echo
echo "Authentication errors:"
grep -h "authentication" logs/app.log* | \
  grep "ERROR" | wc -l

echo
echo "Database errors:"
grep -h "database" logs/app.log* | \
  grep "ERROR" | wc -l

echo
echo "Agent errors:"
grep -h "agent" logs/app.log* | \
  grep "ERROR" | wc -l
```

#### Performance Analysis
```bash
#!/bin/bash
# Analyze slow requests
echo "=== Slow Requests (>2 seconds) ==="
grep -h "execution_time" logs/app.log | \
  jq 'select(.execution_time > 2)' | \
  jq -r '"\(.timestamp) \(.execution_time)s \(.operation) \(.message)"' | \
  sort -k2 -nr | head -20
```

## Performance Issues

### 1. High Response Times

#### Diagnosis
```bash
# Monitor response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8009/api/v1/content

# Create curl-format.txt:
cat > curl-format.txt << EOF
     time_namelookup:  %{time_namelookup}s\n
        time_connect:  %{time_connect}s\n
     time_appconnect:  %{time_appconnect}s\n
    time_pretransfer:  %{time_pretransfer}s\n
       time_redirect:  %{time_redirect}s\n
  time_starttransfer:  %{time_starttransfer}s\n
                     ----------\n
          time_total:  %{time_total}s\n
EOF

# Check database query performance
grep "execution_time" logs/app.log | \
  jq 'select(.operation == "database") | .execution_time' | \
  awk '{sum+=$1; count++} END {print "Avg DB time:", sum/count "s"}'
```

#### Solutions
```bash
# Optimize database queries
# Add database indexes
# Implement query caching
# Use connection pooling

# Scale horizontally
export WORKERS=4

# Optimize async operations
# Use background tasks for heavy operations
# Implement circuit breakers
```

### 2. Memory Issues

#### Diagnosis
```bash
# Monitor memory usage
python -c "
import psutil
process = psutil.Process()
memory_info = process.memory_info()
print(f'RSS: {memory_info.rss / 1024 / 1024:.2f} MB')
print(f'VMS: {memory_info.vms / 1024 / 1024:.2f} MB')
"

# Check for memory leaks
pip install tracemalloc
python -c "
import tracemalloc
tracemalloc.start()
# Run your application
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
"
```

#### Solutions
```bash
# Implement object pooling
# Use generators for large datasets
# Clear caches periodically
# Optimize data structures

# Set memory limits
export MEMORY_LIMIT=2G

# Use memory profiling
pip install memory-profiler
python -m memory_profiler your_script.py
```

### 3. Database Performance

#### Diagnosis
```sql
-- Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check database locks
SELECT pid, usename, query, state
FROM pg_stat_activity
WHERE state = 'active';

-- Check connection usage
SELECT count(*) as active_connections
FROM pg_stat_activity
WHERE state = 'active';
```

#### Solutions
```bash
# Add database indexes
# Optimize queries
# Use read replicas
# Implement connection pooling
# Use database caching

# Monitor database performance
docker exec postgres pg_stat_statements_reset
```

## Error Resolution

### Error Categories and Solutions

#### 1. HTTP 500 Errors
```python
# Add global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception",
        extra={
            "error": str(exc),
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "request_id": request.state.correlation_id}
    )
```

#### 2. HTTP 503 Errors (Service Unavailable)
```bash
# Check circuit breaker status
curl http://localhost:8009/circuit-breakers/status

# Reset circuit breakers if needed
curl -X POST http://localhost:8009/circuit-breakers/database/reset
curl -X POST http://localhost:8009/circuit-breakers/openai-api/reset

# Check service dependencies
docker-compose ps
```

#### 3. Validation Errors
```python
# Enhanced validation error handling
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation failed",
            "details": exc.errors(),
            "request_id": request.state.correlation_id
        }
    )
```

### Automated Error Recovery

#### Circuit Breaker Recovery
```python
# Automatic circuit breaker reset
async def auto_reset_circuit_breakers():
    """Automatically reset circuit breakers after cooldown."""
    while True:
        try:
            breakers = await get_all_circuit_breakers()
            for name, breaker in breakers.items():
                if breaker.should_attempt_reset():
                    await breaker.reset()
                    logger.info(f"Auto-reset circuit breaker: {name}")
        except Exception as e:
            logger.error(f"Circuit breaker auto-reset failed: {e}")

        await asyncio.sleep(60)  # Check every minute
```

#### Service Health Recovery
```python
# Automatic service recovery
async def health_check_and_recover():
    """Monitor service health and attempt recovery."""
    while True:
        try:
            # Check database health
            if not await check_database_health():
                await restart_database_connections()

            # Check Redis health
            if not await check_redis_health():
                await restart_redis_connections()

            # Check agent health
            if not await check_agent_health():
                await restart_agents()

        except Exception as e:
            logger.error(f"Health check failed: {e}")

        await asyncio.sleep(30)  # Check every 30 seconds
```

## Service-Specific Issues

### Agent Service Issues

#### Common Problems
1. **Agent Timeout**: Increase timeout settings
2. **Queue Overflow**: Implement queue size limits
3. **API Rate Limits**: Add rate limiting and retry logic
4. **Memory Leaks**: Implement agent recycling

#### Solutions
```python
# Agent service recovery
async def restart_agent_service():
    """Restart agent service safely."""
    try:
        # Gracefully shutdown current agents
        await agent_service.shutdown()

        # Clear agent queue
        await agent_service.clear_queue()

        # Reinitialize agents
        await agent_service.initialize()

        logger.info("Agent service restarted successfully")
    except Exception as e:
        logger.error(f"Agent service restart failed: {e}")
```

### Pusher Service Issues

#### Common Problems
1. **Connection Limits**: Check Pusher plan limits
2. **Authentication Failures**: Verify credentials
3. **Channel Subscription Issues**: Check channel names and auth

#### Solutions
```bash
# Test Pusher connection
python -c "
import pusher
from apps.backend.core.config import settings

client = pusher.Pusher(
    app_id=settings.PUSHER_APP_ID,
    key=settings.PUSHER_KEY,
    secret=settings.PUSHER_SECRET,
    cluster=settings.PUSHER_CLUSTER
)

# Test trigger
result = client.trigger('test-channel', 'test-event', {'message': 'test'})
print(f'Pusher test result: {result}')
"
```

### Database Service Issues

#### Connection Pool Exhaustion
```python
# Monitor and manage connection pool
async def manage_connection_pool():
    """Monitor and manage database connection pool."""
    while True:
        try:
            pool_status = await get_pool_status()

            if pool_status['checked_out'] > pool_status['size'] * 0.8:
                logger.warning("Connection pool usage high", extra=pool_status)

                # Force connection cleanup
                await cleanup_idle_connections()

        except Exception as e:
            logger.error(f"Pool management error: {e}")

        await asyncio.sleep(10)
```

## Development Issues

### Common Development Problems

#### 1. Hot Reload Issues
```bash
# Fix hot reload
uvicorn apps.backend.main:app --reload --reload-dir apps/backend

# Use watchdog for better file watching
pip install watchdog
uvicorn apps.backend.main:app --reload --reload-delay 0.25
```

#### 2. Import Path Issues
```bash
# Fix Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/project"

# Or add to .env
echo "PYTHONPATH=/path/to/project" >> .env
```

#### 3. Database Migration Issues
```bash
# Reset migrations (WARNING: destroys data)
alembic downgrade base
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Check migration status
alembic current
alembic history
```

## Production Issues

### Production-Specific Problems

#### 1. Environment Configuration
```bash
# Validate production environment
python scripts/validate_production_config.py

# Check secure settings
python -c "
from apps.backend.core.config import settings
if settings.DEBUG:
    print('WARNING: DEBUG is enabled in production!')
if settings.JWT_SECRET_KEY == 'development-secret':
    print('WARNING: Using development JWT secret!')
"
```

#### 2. Resource Monitoring
```bash
# Monitor system resources
top -p $(pgrep -f uvicorn)
iostat -x 1
netstat -an | grep :8009

# Monitor application metrics
curl http://localhost:8009/metrics
```

#### 3. Log Management
```bash
# Rotate logs
logrotate -f /etc/logrotate.d/toolboxai

# Monitor log size
du -sh logs/
find logs/ -name "*.log" -mtime +7 -delete
```

## Monitoring and Alerts

### Health Check Automation
```python
# Comprehensive health monitoring
import asyncio
import aiohttp
from datetime import datetime

class HealthMonitor:
    def __init__(self):
        self.services = {
            'backend': 'http://localhost:8009/health',
            'database': 'postgresql://user:pass@localhost:5432/db',
            'redis': 'redis://localhost:6379',
            'pusher': 'http://localhost:8009/pusher/status'
        }

    async def check_all_services(self):
        """Check health of all services."""
        results = {}

        for service, url in self.services.items():
            try:
                if service == 'backend' or service == 'pusher':
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as response:
                            results[service] = response.status == 200
                elif service == 'database':
                    # Database health check
                    results[service] = await self.check_database()
                elif service == 'redis':
                    # Redis health check
                    results[service] = await self.check_redis()
            except Exception as e:
                results[service] = False
                logger.error(f"Health check failed for {service}: {e}")

        return results

    async def monitor_continuously(self):
        """Continuous health monitoring."""
        while True:
            results = await self.check_all_services()

            # Alert on failures
            for service, healthy in results.items():
                if not healthy:
                    await self.send_alert(f"Service {service} is unhealthy")

            await asyncio.sleep(60)  # Check every minute
```

### Alert System
```python
# Alert notification system
import smtplib
from email.mime.text import MIMEText

class AlertSystem:
    def __init__(self):
        self.alert_channels = ['email', 'slack', 'sentry']

    async def send_alert(self, message: str, severity: str = 'error'):
        """Send alert through configured channels."""
        for channel in self.alert_channels:
            try:
                if channel == 'email':
                    await self.send_email_alert(message, severity)
                elif channel == 'slack':
                    await self.send_slack_alert(message, severity)
                elif channel == 'sentry':
                    await self.send_sentry_alert(message, severity)
            except Exception as e:
                logger.error(f"Failed to send alert via {channel}: {e}")
```

This comprehensive troubleshooting guide provides systematic approaches to diagnosing and resolving issues in the ToolboxAI backend system, from development through production environments.