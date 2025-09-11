# Comprehensive Troubleshooting Guide

This guide provides solutions for common issues encountered in the ToolboxAI platform.

## Quick Diagnostics

Run this diagnostic script to collect system information:

```bash
#!/bin/bash
# diagnostic.sh - Quick system check

echo "=== ToolboxAI System Diagnostics ==="
echo "Date: $(date)"
echo ""

echo "Python Version:"
python --version

echo "Node Version:"
node --version

echo "PostgreSQL Status:"
pg_isready -h localhost -p 5432

echo "Redis Status:"
redis-cli ping

echo "Services Status:"
lsof -i :8008 > /dev/null 2>&1 && echo "FastAPI: ✓ Running" || echo "FastAPI: ✗ Not running"
lsof -i :5001 > /dev/null 2>&1 && echo "Flask Bridge: ✓ Running" || echo "Flask Bridge: ✗ Not running"
lsof -i :9876 > /dev/null 2>&1 && echo "MCP WebSocket: ✓ Running" || echo "MCP WebSocket: ✗ Not running"
lsof -i :3000 > /dev/null 2>&1 && echo "Dashboard: ✓ Running" || echo "Dashboard: ✗ Not running"

echo ""
echo "Environment Variables:"
env | grep -E "DATABASE_URL|REDIS_URL|OPENAI_API_KEY" | sed 's/=.*/=<set>/'
```text
## Common Issues and Solutions

### 1. Installation Problems

#### Python Virtual Environment Issues

**Problem:** Virtual environment won't activate

```bash
# Solution 1: Recreate virtual environment
rm -rf venv_clean
python3.11 -m venv venv_clean
source venv_clean/bin/activate

# Solution 2: Use absolute path
source /path/to/project/venv_clean/bin/activate

# Solution 3: Check Python version
python3.11 --version || echo "Python 3.11 not installed"
```text
#### Node Module Installation Failures

**Problem:** npm install hangs or fails

```bash
# Solution: Clean install
rm -rf node_modules package-lock.json
npm cache clean --force
npm install --legacy-peer-deps

# Alternative: Use yarn
yarn install
```text
### 2. Service Startup Issues

#### FastAPI Server Won't Start

**Problem:** Port 8008 already in use

```bash
# Find and kill process using port
lsof -i :8008
kill -9 <PID>

# Or use different port
uvicorn server.main:app --port 8009
```text
**Problem:** Module import errors

```bash
# Fix Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```text
#### Database Connection Failures

**Problem:** PostgreSQL connection refused

```bash
# Start PostgreSQL
docker run -d \
  --name toolboxai-postgres \
  -e POSTGRES_PASSWORD=[REDACTED] \
  -e POSTGRES_USER=toolboxai \
  -e POSTGRES_DB=toolboxai_dev \
  -p 5432:5432 \
  postgres:15

# Or using system PostgreSQL
sudo systemctl start postgresql
```text
**Problem:** Redis connection error

```bash
# Start Redis
docker run -d \
  --name toolboxai-redis \
  -p 6379:6379 \
  redis:7

# Test connection
redis-cli ping
```text
### 3. Authentication Issues

#### JWT Token Problems

**Problem:** "Invalid token" errors

```python
# regenerate_secret.py
import secrets
import base64

# Generate new secret key
secret_key = secrets.token_urlsafe(32)
print(f"New JWT_SECRET_KEY: {secret_key}")

# Update .env file
# JWT_SECRET_KEY=<new_secret_key>
```text
#### Login Failures

**Problem:** Can't login with correct credentials

```sql
-- Check user exists
SELECT email, role, is_active FROM users WHERE email = 'user@example.com';

-- Reset password (run in Python)
```text
```python
from server.auth import hash_password
from database.connection import get_db

async def reset_user_password(email: str, new_password: str):
    async with get_db() as session:
        user = await session.query(User).filter_by(email=email).first()
        if user:
            user.password_hash = hash_password(new_password)
            await session.commit()
            print(f"Password reset for {email}")
```text
### 4. API Errors

#### 500 Internal Server Error

**Debug Steps:**

```python
# Add detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with debug mode
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server.main:app",
        host="127.0.0.1",
        port=8008,
        reload=True,
        log_level="debug"
    )
```text
#### Rate Limiting Issues

**Problem:** 429 Too Many Requests

```python
# Implement retry logic
import time
from typing import Optional

class RateLimitHandler:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    async def request_with_retry(self, func, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                response = await func(*args, **kwargs)
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    print(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                return response
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
```text
### 5. WebSocket Connection Issues

#### Connection Drops Frequently

**Problem:** WebSocket disconnects after short time

```javascript
// Implement reconnection logic
class ReconnectingWebSocket {
  constructor(url) {
    this.url = url
    this.reconnectInterval = 5000
    this.shouldReconnect = true
    this.connect()
  }

  connect() {
    this.ws = new WebSocket(this.url)

    this.ws.onopen = () => {
      console.log('WebSocket connected')
      this.reconnectInterval = 5000
    }

    this.ws.onclose = () => {
      if (this.shouldReconnect) {
        console.log(`Reconnecting in ${this.reconnectInterval}ms...`)
        setTimeout(() => this.connect(), this.reconnectInterval)
        this.reconnectInterval = Math.min(30000, this.reconnectInterval * 2)
      }
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }

  disconnect() {
    this.shouldReconnect = false
    this.ws.close()
  }
}
```text
### 6. Roblox Integration Problems

#### Plugin Can't Connect to Server

**Solution 1:** Enable HTTP requests in Roblox Studio

```lua
-- In Roblox Studio:
-- File > Game Settings > Security > Allow HTTP Requests = ON
```text
**Solution 2:** Check Flask bridge is running

```bash
python server/roblox_server.py

# Or with specific host
python server/roblox_server.py --host 127.0.0.1 --port 5001
```text
**Solution 3:** Fix Lua script errors

```lua
-- Test connection from Roblox console
local HttpService = game:GetService("HttpService")
local url = "http://127.0.0.1:5001/health"

local success, response = pcall(function()
    return HttpService:GetAsync(url)
end)

if success then
    print("Connected:", response)
else
    print("Failed:", response)
end
```text
### 7. Database Migration Issues

#### Alembic Migration Failures

**Problem:** "Target database is not up to date"

```bash
# Check current revision
alembic current

# Stamp current version
alembic stamp head

# Create new migration
alembic revision --autogenerate -m "fix migration"

# Apply migrations
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```text
#### Schema Mismatch

**Problem:** Table already exists errors

```sql
-- Drop all tables (CAUTION: Data loss!)
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

-- Then run migrations
```text
```bash
alembic upgrade head
```text
### 8. Performance Issues

#### Slow API Response Times

**Diagnostic Tools:**

```python
# Add performance monitoring
from fastapi import Request
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    if process_time > 1.0:  # Log slow requests
        logger.warning(f"Slow request: {request.url.path} took {process_time:.2f}s")

    return response
```text
**Optimization Solutions:**

```python
# 1. Add caching
from functools import lru_cache
import redis

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

@lru_cache(maxsize=128)
def get_cached_data(key: str):
    return redis_client.get(key)

# 2. Use connection pooling
from sqlalchemy.pool import NullPool, QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600,
    pool_pre_ping=True
)

# 3. Implement pagination
from fastapi import Query

@app.get("/api/items")
async def get_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000)
):
    return await db.query(Item).offset(skip).limit(limit).all()
```text
### 9. Docker/Container Issues

#### Container Crashes on Startup

**Debug Steps:**

```bash
# Check logs
docker logs toolboxai-api

# Run with interactive shell
docker run -it --entrypoint /bin/bash toolboxai-api

# Inside container, test startup
python -c "from server.main import app"
```text
**Common Fixes:**

```dockerfile
# Dockerfile improvements
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install dependencies first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run as non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8008/health')" || exit 1

CMD ["uvicorn", "server.main:app", "--host", "127.0.0.1", "--port", "8008"]
```text
### 10. CI/CD Pipeline Failures

#### GitHub Actions Failing

**Common Issues and Fixes:**

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379
        run: |
          pytest tests/ -v --cov
```text
## Advanced Debugging

### Memory Profiling

```python
# memory_profile.py
from memory_profiler import profile
import tracemalloc

tracemalloc.start()

@profile
def analyze_memory():
    # Your code here
    pass

# Get top memory consumers
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

for stat in top_stats[:10]:
    print(stat)
```text
### SQL Query Analysis

```python
# Enable SQL logging
import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Or use echo in engine
engine = create_async_engine(DATABASE_URL, echo=True)
```text
### Network Debugging

```bash
# Monitor network traffic
tcpdump -i lo -n port 8008

# Check open connections
netstat -tuln | grep LISTEN

# Test API endpoint
curl -v -X POST http://localhost:8008/api/content/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"subject": "Math", "grade_level": 7}'
```text
## Recovery Procedures

### Emergency Database Recovery

```bash
#!/bin/bash
# db_recovery.sh

# Backup current state
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Drop and recreate database
dropdb toolboxai_dev
createdb toolboxai_dev

# Restore from backup
psql $DATABASE_URL < latest_backup.sql

# Run migrations
alembic upgrade head
```text
### Full System Reset

```bash
#!/bin/bash
# reset_system.sh

echo "Full System Reset - This will delete all data!"
read -p "Continue? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Stop all services
    pkill -f "uvicorn"
    pkill -f "python"
    docker-compose down -v

    # Clean everything
    rm -rf venv_clean node_modules __pycache__ .pytest_cache
    rm -rf logs/*.log

    # Rebuild
    python3.11 -m venv venv_clean
    source venv_clean/bin/activate
    pip install -r requirements.txt
    npm install

    # Reset database
    alembic upgrade head
    python scripts/seed_db.py

    echo "Reset complete!"
fi
```text
## Monitoring and Alerts

### Setup Health Monitoring

```python
# health_monitor.py
import asyncio
import httpx
from datetime import datetime

async def check_service_health():
    services = [
        ("FastAPI", "http://localhost:8008/health"),
        ("Flask Bridge", "http://localhost:5001/health"),
        ("Dashboard", "http://localhost:3000"),
    ]

    results = []
    async with httpx.AsyncClient() as client:
        for name, url in services:
            try:
                response = await client.get(url, timeout=5.0)
                status = "✓" if response.status_code == 200 else "✗"
            except:
                status = "✗"

            results.append(f"{name}: {status}")

    print(f"[{datetime.now()}] Health Check")
    for result in results:
        print(f"  {result}")

# Run every 30 seconds
async def monitor_loop():
    while True:
        await check_service_health()
        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(monitor_loop())
```text
## Getting Support

When requesting help, provide:

1. **Error logs** from `logs/` directory
2. **System information** from diagnostic script
3. **Steps to reproduce** the issue
4. **Expected vs actual** behavior
5. **Recent changes** made to the system

### Support Channels

- GitHub Issues: [Report bugs](https://github.com/toolboxai/issues)
- Discord: [Community support](https://discord.gg/toolboxai)
- Email: support@toolboxai.com
- Documentation: [Full docs](https://docs.toolboxai.com)
