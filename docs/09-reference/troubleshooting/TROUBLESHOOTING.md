# Troubleshooting Guide

This comprehensive guide covers common issues and solutions for the ToolBoxAI Solutions platform after the September 2025 Docker modernization and system refactoring.

## Table of Contents

1. [Docker-Specific Issues](#docker-specific-issues)
2. [Development Environment Issues](#development-environment-issues)
3. [API and Backend Issues](#api-and-backend-issues)
4. [Frontend and Dashboard Issues](#frontend-and-dashboard-issues)
5. [Security and Secrets Issues](#security-and-secrets-issues)
6. [Production Deployment Issues](#production-deployment-issues)
7. [Quick Diagnostic Commands](#quick-diagnostic-commands)

---

## Docker-Specific Issues

### Container Startup Failures

#### Issue: Services fail to start with exit code 125 or 126
**Symptoms:**
```
ERROR: for toolboxai-fastapi  Cannot start service fastapi-main:
OCI runtime create failed: container_linux.go:380: starting container process caused
```

**Root Causes & Solutions:**

1. **Permission Issues**
```bash
# Check file permissions on Docker context
ls -la /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/

# Fix permissions
chmod -R 755 infrastructure/docker/
chmod +x infrastructure/docker/*.sh
```

2. **Missing Docker Context Files**
```bash
# Verify all required Dockerfiles exist
./infrastructure/docker/check-setup.sh

# If missing, ensure you're in the correct directory
pwd
# Should be: /Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions
```

#### Issue: Container exits immediately after start
**Symptoms:**
```
toolboxai-fastapi exited with code 1
```

**Diagnostic Steps:**
```bash
# Check container logs
docker logs toolboxai-fastapi

# Check service health
docker-compose -f infrastructure/docker/docker-compose.dev.yml ps

# Inspect container configuration
docker inspect toolboxai-fastapi
```

**Common Fixes:**
```bash
# 1. Environment variables missing
cp .env.example .env
# Edit .env with required values

# 2. Database not ready
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d postgres redis
# Wait for health checks, then start other services

# 3. Port conflicts
sudo lsof -i :8009
sudo kill -9 <PID>
```

### Image Build Errors

#### Issue: BuildKit failures with "failed to solve"
**Symptoms:**
```
ERROR: failed to solve: failed to read dockerfile: open /var/lib/docker/tmp/buildkit-mount123/Dockerfile.backend: no such file or directory
```

**Solutions:**

1. **Clear Docker BuildKit Cache**
```bash
# Clear all build cache
docker builder prune -a -f

# Reset BuildKit
export DOCKER_BUILDKIT=0
docker-compose -f infrastructure/docker/docker-compose.dev.yml build --no-cache
```

2. **Check Docker Context Path**
```bash
# Ensure build context is correct
docker-compose -f infrastructure/docker/docker-compose.dev.yml config

# Verify Dockerfile paths
ls infrastructure/docker/Dockerfile.backend
ls infrastructure/docker/Dockerfile.dashboard
```

#### Issue: Node.js build failures in dashboard container
**Symptoms:**
```
#8 [stage-0 4/8] RUN npm install
#8 ERROR: npm WARN deprecated ...
#8 npm ERR! code ERESOLVE
```

**Solutions:**
```bash
# 1. Clear npm cache in container
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec dashboard-frontend npm cache clean --force

# 2. Rebuild with clean node_modules
docker-compose -f infrastructure/docker/docker-compose.dev.yml down dashboard-frontend
docker volume rm $(docker volume ls -q | grep node_modules)
docker-compose -f infrastructure/docker/docker-compose.dev.yml build --no-cache dashboard-frontend

# 3. Use legacy peer deps (if needed)
# Add to dashboard Dockerfile:
# RUN npm install --legacy-peer-deps
```

### Network Connectivity Between Containers

#### Issue: Service cannot reach other containers
**Symptoms:**
```
requests.exceptions.ConnectionError: HTTPConnectionPool(host='postgres', port=5432)
```

**Diagnostic Steps:**
```bash
# Check network configuration
docker network ls
docker network inspect toolboxai_network

# Test connectivity between containers
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec fastapi-main ping postgres
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec dashboard-frontend curl http://fastapi-main:8009/health
```

**Solutions:**
```bash
# 1. Recreate network
docker-compose -f infrastructure/docker/docker-compose.dev.yml down
docker network prune -f
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d

# 2. Check service names in environment variables
# Ensure DATABASE_URL uses 'postgres' not 'localhost'
DATABASE_URL=postgresql://eduplatform:eduplatform2024@postgres:5432/educational_platform_dev

# 3. Verify all services are on same network
docker-compose -f infrastructure/docker/docker-compose.dev.yml ps --services
```

### Volume Mount Issues on macOS with VirtioFS

#### Issue: File changes not reflected in containers
**Symptoms:**
- Hot reload not working
- File modifications don't trigger updates

**Solutions:**
```bash
# 1. Enable VirtioFS in Docker Desktop
# Docker Desktop > Settings > General > "Use the new Virtualization framework" > "VirtioFS"

# 2. Check volume mount syntax
docker-compose -f infrastructure/docker/docker-compose.dev.yml config | grep -A5 volumes:

# 3. Use cached/delegated flags for better performance
volumes:
  - ../../apps/dashboard/src:/app/src:cached
  - ../../apps/dashboard/public:/app/public:delegated

# 4. Restart Docker Desktop if issues persist
```

#### Issue: Permission denied when accessing mounted volumes
**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/app/src/components'
```

**Solutions:**
```bash
# 1. Fix host permissions
chmod -R 755 apps/dashboard/src/
chown -R $(whoami) apps/dashboard/

# 2. Use proper user context in Dockerfile
# Add to Dockerfile:
USER node
WORKDIR /app
RUN chown -R node:node /app

# 3. Override user at runtime
docker-compose -f infrastructure/docker/docker-compose.dev.yml run --user="$(id -u):$(id -g)" dashboard-frontend npm run dev
```

### Docker Compose Configuration Problems

#### Issue: Invalid YAML syntax errors
**Symptoms:**
```
ERROR: Invalid interpolation format for "environment" option
```

**Diagnostic:**
```bash
# Validate YAML syntax
docker-compose -f infrastructure/docker/docker-compose.dev.yml config

# Check for common issues
grep -n '${' infrastructure/docker/docker-compose.dev.yml | head -10
```

**Solutions:**
```bash
# 1. Ensure environment variables are properly defined
source .env
env | grep -E "(POSTGRES|REDIS|JWT|PUSHER)"

# 2. Escape special characters in YAML
# Wrong: password: p@ssw0rd!
# Right: password: "p@ssw0rd!"

# 3. Use proper variable substitution
# Wrong: ${VAR:-default value}
# Right: ${VAR:-default_value}
```

### Health Check Failures

#### Issue: Services marked as unhealthy
**Symptoms:**
```
toolboxai-fastapi      Up 2 minutes (unhealthy)
```

**Diagnostic Commands:**
```bash
# Check health check logs
docker inspect toolboxai-fastapi --format='{{.State.Health.Log}}'

# Test health endpoint manually
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec fastapi-main curl -f http://localhost:8009/health

# Check service logs
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs fastapi-main
```

**Common Fixes:**
```bash
# 1. Service not fully started
# Increase start_period in docker-compose.yml
healthcheck:
  start_period: 120s  # Increase from 60s

# 2. Health endpoint not available
# Check FastAPI routes
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec fastapi-main python -c "from apps.backend.main import app; print(list(app.routes))"

# 3. Curl not available in container
# Add to Dockerfile:
RUN apt-get update && apt-get install -y curl

# Or use python for health check:
test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8009/health')"]
```

### Resource Limit Errors

#### Issue: Container killed due to OOM (Out of Memory)
**Symptoms:**
```
Killed
Container exited with code 137
```

**Solutions:**
```bash
# 1. Check current resource limits
docker stats

# 2. Increase memory limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G  # Increase from 2G
    reservations:
      memory: 1G

# 3. Monitor resource usage
docker-compose -f infrastructure/docker/docker-compose.dev.yml top
```

#### Issue: CPU throttling causing slow performance
**Symptoms:**
- Slow API responses
- Build timeouts

**Solutions:**
```bash
# 1. Increase CPU limits
deploy:
  resources:
    limits:
      cpus: '2.0'  # Add CPU limit

# 2. Reduce concurrent processes
WORKERS: 1  # Reduce from 2 in environment

# 3. Use build optimization
# Add to Dockerfile:
ENV NODE_OPTIONS="--max_old_space_size=4096"
```

### Security Context Issues

#### Issue: Non-root user cannot access files
**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/app/data'
```

**Solutions:**
```bash
# 1. Create proper user in Dockerfile
RUN groupadd -r appuser && useradd -r -g appuser -s /bin/bash appuser
RUN chown -R appuser:appuser /app
USER appuser

# 2. Use init system for proper signal handling
# Add to docker-compose.yml:
init: true

# 3. Set proper security options
security_opt:
  - no-new-privileges:true
```

#### Issue: Read-only filesystem restrictions
**Symptoms:**
```
OSError: [Errno 30] Read-only file system
```

**Solutions:**
```bash
# 1. Create writable temporary volumes
tmpfs:
  - /tmp
  - /var/tmp

# 2. Use specific writable paths
volumes:
  - temp_data:/app/temp
  - logs:/app/logs

# 3. Adjust read-only root filesystem
read_only: false  # Temporarily disable for debugging
```

---

## Development Environment Issues

### Port Conflicts

#### Issue: Port 8009 already in use
**Symptoms:**
```
Error starting userland proxy: listen tcp4 0.0.0.0:8009: bind: address already in use
```

**Diagnostic Commands:**
```bash
# Find process using port
sudo lsof -i :8009
sudo netstat -tulpn | grep :8009

# Check all potential conflicting ports
for port in 8009 5179 5434 6381 8888 9877 5001 8000; do
    echo "Port $port:"
    sudo lsof -i :$port
done
```

**Solutions:**
```bash
# 1. Kill conflicting process
sudo kill -9 <PID>

# 2. Use alternative ports
# Edit .env file:
FASTAPI_PORT=8010
DASHBOARD_PORT=5180

# 3. Stop all Docker containers
docker stop $(docker ps -aq)
docker-compose -f infrastructure/docker/docker-compose.dev.yml down
```

#### Issue: Port 5179 (Dashboard) conflicts with other Vite servers
**Solutions:**
```bash
# 1. Change dashboard port
PORT=5180 npm run dev

# 2. Kill all Node processes
pkill -f "vite|node"

# 3. Use Docker with different port mapping
# Edit docker-compose.dev.yml:
ports:
  - '5180:5179'
```

### Python Virtual Environment Problems

#### Issue: Wrong Python version or missing packages
**Symptoms:**
```
ModuleNotFoundError: No module named 'fastapi'
ImportError: This package requires Python 3.12+
```

**Solutions:**
```bash
# 1. Check Python version
python3 --version
which python3

# 2. Recreate virtual environment
rm -rf venv/
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Update VS Code Python interpreter
# Command Palette > Python: Select Interpreter
# Select: /Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/venv/bin/python
```

#### Issue: Package installation failures
**Symptoms:**
```
ERROR: Could not install packages due to an EnvironmentError
pip is being invoked by an old script wrapper
```

**Solutions:**
```bash
# 1. Upgrade pip
python -m pip install --upgrade pip

# 2. Clear pip cache
pip cache purge

# 3. Install with specific flags
pip install -r requirements.txt --no-cache-dir --force-reinstall

# 4. Use conda if pip fails
conda create -n toolboxai python=3.12
conda activate toolboxai
pip install -r requirements.txt
```

### Node.js Version Mismatches

#### Issue: Node version conflicts between system and project
**Symptoms:**
```
error toolboxai@1.1.0: The engine "node" is incompatible with this module
```

**Solutions:**
```bash
# 1. Check required version
cat .nvmrc
# Should show: 22

# 2. Install and use correct Node version
nvm install 22
nvm use 22
nvm alias default 22

# 3. Verify version
node --version
npm --version

# 4. Clear npm cache if needed
npm cache clean --force
rm -rf node_modules
npm install
```

### Database Connection Errors

#### Issue: PostgreSQL connection refused
**Symptoms:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server on socket
```

**Diagnostic Steps:**
```bash
# 1. Check PostgreSQL status
brew services list | grep postgresql
# Or for Docker:
docker-compose -f infrastructure/docker/docker-compose.dev.yml ps postgres

# 2. Test connection
psql postgresql://eduplatform:eduplatform2024@localhost:5434/educational_platform_dev

# 3. Check database exists
psql -U eduplatform -h localhost -p 5434 -l
```

**Solutions:**
```bash
# 1. Start PostgreSQL service
brew services start postgresql@15
# Or Docker:
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d postgres

# 2. Create database if missing
psql -U postgres -h localhost -p 5434 -c "CREATE DATABASE educational_platform_dev;"

# 3. Update connection string in .env
DATABASE_URL=postgresql://eduplatform:eduplatform2024@localhost:5434/educational_platform_dev

# 4. Run migrations
cd apps/backend
alembic upgrade head
```

### Redis Connectivity Issues

#### Issue: Redis connection timeout
**Symptoms:**
```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6381
```

**Solutions:**
```bash
# 1. Start Redis
brew services start redis
# Or Docker:
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d redis

# 2. Test Redis connection
redis-cli -p 6381 ping

# 3. Check Redis configuration
redis-cli -p 6381 CONFIG GET "*"

# 4. Update REDIS_URL in .env
REDIS_URL=redis://localhost:6381/0
```

### Hot-Reload Not Working

#### Issue: File changes don't trigger automatic reloads
**For Backend (FastAPI):**
```bash
# 1. Ensure --reload flag is used
uvicorn main:app --host 127.0.0.1 --port 8009 --reload

# 2. Check file permissions
chmod -R 755 apps/backend/

# 3. Use watchfiles for better monitoring
pip install watchfiles
uvicorn main:app --host 127.0.0.1 --port 8009 --reload --reload-dir apps/backend
```

**For Frontend (Vite):**
```bash
# 1. Check Vite configuration
cat apps/dashboard/vite.config.ts

# 2. Clear Vite cache
rm -rf apps/dashboard/node_modules/.vite
npm -w apps/dashboard run dev

# 3. Use polling for file watching
# Add to vite.config.ts:
server: {
  watch: {
    usePolling: true
  }
}
```

---

## API and Backend Issues

### JWT Authentication Failures

#### Issue: Invalid JWT token errors
**Symptoms:**
```
HTTP 401: {"detail": "Invalid authentication credentials"}
```

**Diagnostic Steps:**
```bash
# 1. Check JWT secret configuration
echo $JWT_SECRET_KEY
grep JWT_SECRET .env

# 2. Test token generation
curl -X POST http://localhost:8009/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test"}'

# 3. Verify token format
# Use jwt.io to decode token
```

**Solutions:**
```bash
# 1. Generate proper JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Add to .env: JWT_SECRET_KEY=<generated_key>

# 2. Check token expiration
# Add to FastAPI config:
JWT_EXPIRE_MINUTES=60

# 3. Verify user authentication flow
curl -X GET http://localhost:8009/api/v1/users/me \
  -H "Authorization: Bearer <your_token>"
```

### CORS Errors

#### Issue: CORS policy blocking frontend requests
**Symptoms:**
```
Access to fetch at 'http://localhost:8009/api/v1/...' from origin 'http://localhost:5179'
has been blocked by CORS policy
```

**Solutions:**
```bash
# 1. Check CORS configuration in backend
# Verify in apps/backend/core/middleware/cors.py:
ALLOWED_ORIGINS = [
    "http://localhost:5179",
    "http://127.0.0.1:5179",
    "http://localhost:3000",  # Alternative dev port
    "https://your-domain.com"  # Production domain
]

# 2. Add CORS headers for debugging
curl -H "Origin: http://localhost:5179" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS \
     http://localhost:8009/api/v1/health

# 3. Check preflight responses
curl -v -X OPTIONS http://localhost:8009/api/v1/users/me \
  -H "Origin: http://localhost:5179" \
  -H "Access-Control-Request-Headers: authorization"
```

### Import Path Problems

#### Issue: Module import errors after refactoring
**Symptoms:**
```
ModuleNotFoundError: No module named 'apps.backend.core'
ImportError: cannot import name 'settings' from 'toolboxai_settings'
```

**Solutions:**
```bash
# 1. Check PYTHONPATH
echo $PYTHONPATH
export PYTHONPATH="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions:$PYTHONPATH"

# 2. Verify module structure
find . -name "__init__.py" | head -20

# 3. Test imports interactively
python -c "from apps.backend.main import app; print('Import successful')"

# 4. Check for circular imports
python -c "import sys; sys.path.insert(0, '.'); from apps.backend.core.config import settings"
```

### Pydantic Validation Errors

#### Issue: Pydantic v2 validation failures
**Symptoms:**
```
pydantic.ValidationError: 1 validation error for UserCreate
field required (type=value_error.missing)
```

**Solutions:**
```bash
# 1. Check Pydantic version compatibility
pip show pydantic
pip show pydantic-settings

# 2. Update model definitions for v2
# Old v1 syntax:
class Config:
    orm_mode = True

# New v2 syntax:
model_config = ConfigDict(from_attributes=True)

# 3. Test model validation
python -c "
from apps.backend.models import UserCreate
user = UserCreate(username='test', email='test@test.com', password='test123')
print(user.model_dump())
"
```

### Database Migration Failures

#### Issue: Alembic migration errors
**Symptoms:**
```
alembic.util.exc.CommandError: Can't locate revision identified by 'abc123'
sqlalchemy.exc.ProgrammingError: relation "users" already exists
```

**Solutions:**
```bash
# 1. Check migration status
cd apps/backend
alembic current
alembic history --verbose

# 2. Reset migrations (DANGER: Data loss)
alembic downgrade base
alembic upgrade head

# 3. Generate new migration
alembic revision --autogenerate -m "Fix migration"

# 4. Manual migration fix
# Edit migration file to handle existing tables:
def upgrade():
    # Check if table exists before creating
    connection = op.get_bind()
    if not connection.dialect.has_table(connection, 'users'):
        op.create_table('users', ...)
```

### Agent Orchestration Problems

#### Issue: MCP server connection failures
**Symptoms:**
```
ConnectionError: Unable to connect to MCP server at ws://localhost:9877
```

**Solutions:**
```bash
# 1. Check MCP server status
curl http://localhost:9877/health

# 2. Verify WebSocket connectivity
# Install websocat: brew install websocat
websocat ws://localhost:9877/ws

# 3. Check agent coordinator logs
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs agent-coordinator

# 4. Restart agent services
docker-compose -f infrastructure/docker/docker-compose.dev.yml restart mcp-server agent-coordinator
```

---

## Frontend and Dashboard Issues

### Build Failures

#### Issue: TypeScript compilation errors
**Symptoms:**
```
src/components/Dashboard.tsx:45:12 - error TS2345:
Argument of type 'string | undefined' is not assignable to parameter of type 'string'
```

**Solutions:**
```bash
# 1. Check TypeScript configuration
cat apps/dashboard/tsconfig.json

# 2. Fix type errors
# Add null checks:
if (apiKey) {
  useApiCall(apiKey);
}

# 3. Update type definitions
npm -w apps/dashboard run typecheck

# 4. Regenerate type declarations
npm -w apps/dashboard run build:types
```

#### Issue: Vite build memory errors
**Symptoms:**
```
<--- Last few GCs --->
FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory
```

**Solutions:**
```bash
# 1. Increase Node.js heap size
NODE_OPTIONS="--max_old_space_size=4096" npm -w apps/dashboard run build

# 2. Use build optimization
# Add to vite.config.ts:
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        vendor: ['react', 'react-dom'],
        ui: ['@mui/material', '@mui/icons-material']
      }
    }
  }
}

# 3. Clear build cache
rm -rf apps/dashboard/dist
rm -rf apps/dashboard/node_modules/.vite
```

### TypeScript Errors

#### Issue: React 19 compatibility issues
**Symptoms:**
```
Type 'ReactNode' is not assignable to type 'ReactElement<any, any>'
```

**Solutions:**
```bash
# 1. Update React types
npm -w apps/dashboard install --save-dev @types/react@^19.0.0

# 2. Fix component type annotations
// Old:
const Component: React.FC<Props> = () => { ... }

// New:
const Component = (props: Props): React.ReactElement => { ... }

# 3. Update JSX configuration
// In tsconfig.json:
{
  "compilerOptions": {
    "jsx": "react-jsx",
    "types": ["react/canary", "react-dom/canary"]
  }
}
```

### Vite Configuration Problems

#### Issue: Vite proxy not working
**Symptoms:**
```
GET http://localhost:5179/api/v1/health 404 (Not Found)
```

**Solutions:**
```bash
# 1. Check proxy configuration
cat apps/dashboard/vite.config.ts

# 2. Verify proxy setup
server: {
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:8009',
      changeOrigin: true,
      secure: false
    }
  }
}

# 3. Test proxy manually
curl http://localhost:5179/api/v1/health
```

#### Issue: Hot Module Replacement (HMR) not working
**Solutions:**
```bash
# 1. Check HMR configuration
# In vite.config.ts:
server: {
  hmr: {
    overlay: true
  },
  watch: {
    usePolling: true  # For file systems that don't support native watching
  }
}

# 2. Clear Vite cache
rm -rf apps/dashboard/node_modules/.vite

# 3. Restart with clean cache
npm -w apps/dashboard run dev -- --force
```

### Pusher Connection Issues

#### Issue: Pusher authentication failures
**Symptoms:**
```
Pusher: Could not authenticate with auth endpoint /pusher/auth
```

**Solutions:**
```bash
# 1. Check Pusher configuration
echo $PUSHER_KEY
echo $VITE_PUSHER_KEY

# 2. Test auth endpoint
curl -X POST http://localhost:8009/api/v1/pusher/auth \
  -H "Authorization: Bearer <your_jwt_token>" \
  -d "channel_name=private-user-123&socket_id=123.456"

# 3. Verify Pusher credentials in dashboard
# Check browser console for Pusher connection logs
```

#### Issue: Pusher channels not receiving messages
**Solutions:**
```bash
# 1. Check channel subscription
# In browser console:
window.pusher.connection.state  // Should be 'connected'
window.pusher.channels.channels  // Should show subscribed channels

# 2. Test event triggering
curl -X POST http://localhost:8009/api/v1/realtime/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "dashboard-updates",
    "event": "test",
    "data": {"message": "test"}
  }'

# 3. Check Pusher dashboard
# Visit https://dashboard.pusher.com for real-time debugging
```

### API Proxy Not Working

#### Issue: Frontend API calls not reaching backend
**Symptoms:**
```
Network Error: Request failed with status code 404
```

**Solutions:**
```bash
# 1. Verify backend is running
curl http://localhost:8009/health

# 2. Check API client configuration
# In apps/dashboard/src/services/api.ts:
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8009'

# 3. Test API directly vs through proxy
curl http://localhost:8009/api/v1/health
curl http://localhost:5179/api/v1/health

# 4. Check browser network tab for failed requests
```

### White Screen Errors

#### Issue: Dashboard shows blank white screen
**Diagnostic Steps:**
```bash
# 1. Check browser console for errors
# Open DevTools > Console

# 2. Check network tab for failed resource loads
# Open DevTools > Network

# 3. Check React error boundaries
# Look for component crash logs
```

**Solutions:**
```bash
# 1. Add error boundary to catch React errors
# Create ErrorBoundary component

# 2. Check for missing environment variables
# In browser console:
console.log(import.meta.env)

# 3. Verify all dependencies are installed
npm -w apps/dashboard install
npm -w apps/dashboard run build

# 4. Clear browser cache and localStorage
# DevTools > Application > Storage > Clear site data
```

---

## Security and Secrets Issues

### Environment Variables Not Found

#### Issue: Required environment variables missing
**Symptoms:**
```
KeyError: 'JWT_SECRET_KEY'
Configuration validation error: OPENAI_API_KEY is required
```

**Solutions:**
```bash
# 1. Create .env file from template
cp .env.example .env

# 2. Set required variables
cat >> .env << EOF
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
OPENAI_API_KEY=your-openai-key
PUSHER_KEY=your-pusher-key
PUSHER_SECRET=your-pusher-secret
EOF

# 3. Source environment file
source .env

# 4. Verify variables are loaded
env | grep -E "(JWT|OPENAI|PUSHER)"
```

### Docker Secrets Configuration

#### Issue: Secrets not properly mounted in containers
**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory: '/run/secrets/jwt_secret'
```

**Solutions:**
```bash
# 1. Create secrets directory
mkdir -p secrets/
echo "your-jwt-secret" > secrets/jwt_secret.txt

# 2. Add secrets to docker-compose.yml
secrets:
  jwt_secret:
    file: ./secrets/jwt_secret.txt

services:
  fastapi-main:
    secrets:
      - jwt_secret

# 3. Read secrets in application
# In Python:
with open('/run/secrets/jwt_secret', 'r') as f:
    JWT_SECRET = f.read().strip()
```

### Permission Denied Errors

#### Issue: Application cannot access files or directories
**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/app/logs/application.log'
```

**Solutions:**
```bash
# 1. Fix file permissions
chmod -R 755 /path/to/app/
chown -R $(whoami):$(whoami) /path/to/app/

# 2. Create directories with proper permissions
mkdir -p logs/ tmp/ data/
chmod 755 logs/ tmp/ data/

# 3. Use proper user in Docker
# In Dockerfile:
RUN adduser --disabled-password --gecos '' appuser
USER appuser
```

### SSL/TLS Certificate Problems

#### Issue: SSL verification errors in production
**Symptoms:**
```
ssl.SSLCertVerificationError: certificate verify failed
requests.exceptions.SSLError: HTTPSConnectionPool
```

**Solutions:**
```bash
# 1. Update certificates
# On Ubuntu/Debian:
sudo apt-get update && sudo apt-get install ca-certificates

# On Alpine (Docker):
apk add --no-cache ca-certificates

# 2. Disable SSL verification for development only
# In Python:
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# 3. Use proper certificate bundle
export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
```

---

## Production Deployment Issues

### Container Registry Authentication

#### Issue: Cannot push/pull images from registry
**Symptoms:**
```
Error response from daemon: unauthorized: authentication required
```

**Solutions:**
```bash
# 1. Login to Docker registry
docker login registry.your-domain.com
# Or for Docker Hub:
docker login -u your-username

# 2. Tag images properly
docker tag toolboxai-fastapi:latest registry.your-domain.com/toolboxai-fastapi:latest

# 3. Use authentication token
echo $DOCKER_REGISTRY_TOKEN | docker login --username your-username --password-stdin registry.your-domain.com
```

### Docker Swarm Mode Problems

#### Issue: Service deployment failures in Swarm
**Symptoms:**
```
service converged but does not have available replicas
```

**Solutions:**
```bash
# 1. Check Swarm status
docker node ls
docker service ls
docker service ps toolboxai_fastapi --no-trunc

# 2. Check resource constraints
docker node inspect self --format '{{.Status.State}}'

# 3. Update service with constraints
docker service update --constraint-rm node.hostname==old-node toolboxai_fastapi
```

### Load Balancing Issues

#### Issue: Nginx not distributing traffic properly
**Symptoms:**
- Requests always go to same backend instance
- 502 Bad Gateway errors

**Solutions:**
```bash
# 1. Check Nginx configuration
nginx -t
sudo nginx -s reload

# 2. Verify upstream servers
# In /etc/nginx/sites-available/toolboxai:
upstream fastapi_backend {
    server 127.0.0.1:8009 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8010 max_fails=3 fail_timeout=30s;
}

# 3. Test backend health
for port in 8009 8010; do
    curl -f http://localhost:$port/health || echo "Port $port unhealthy"
done
```

### Monitoring Stack Failures

#### Issue: Prometheus/Grafana not collecting metrics
**Symptoms:**
```
context deadline exceeded
connection refused to prometheus:9090
```

**Solutions:**
```bash
# 1. Check monitoring services
docker-compose -f infrastructure/docker/docker-compose.prod.yml ps | grep -E "(prometheus|grafana)"

# 2. Verify metrics endpoints
curl http://localhost:8009/metrics

# 3. Check Prometheus configuration
# Verify targets are reachable:
curl http://localhost:9090/api/v1/targets

# 4. Restart monitoring stack
docker-compose -f infrastructure/docker/docker-compose.prod.yml restart prometheus grafana
```

---

## Quick Diagnostic Commands

### System Health Check
```bash
#!/bin/bash
# Quick system diagnostic script

echo "=== System Health Check ==="

# Check Docker
echo "Docker Status:"
docker --version && docker info --format '{{.ServerVersion}}' && echo "✓ Docker OK" || echo "✗ Docker Issue"

# Check ports
echo -e "\nPort Status:"
for port in 8009 5179 5434 6381; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null; then
        echo "Port $port: OCCUPIED"
    else
        echo "Port $port: FREE"
    fi
done

# Check services
echo -e "\nServices Status:"
curl -s http://localhost:8009/health && echo "✓ Backend OK" || echo "✗ Backend Issue"
curl -s http://localhost:5179/ > /dev/null && echo "✓ Dashboard OK" || echo "✗ Dashboard Issue"

# Check environment
echo -e "\nEnvironment Variables:"
env | grep -E "(JWT_SECRET|DATABASE_URL|REDIS_URL)" | wc -l | xargs echo "Config vars found:"
```

### Docker Environment Diagnostic
```bash
#!/bin/bash
# Docker environment diagnostic

echo "=== Docker Diagnostic ==="

# Container status
echo "Container Status:"
docker-compose -f infrastructure/docker/docker-compose.dev.yml ps

# Health checks
echo -e "\nHealth Status:"
docker-compose -f infrastructure/docker/docker-compose.dev.yml ps --format "table {{.Name}}\t{{.Status}}"

# Logs (last 50 lines)
echo -e "\nRecent Logs:"
for service in fastapi-main dashboard-frontend postgres redis; do
    echo "--- $service ---"
    docker-compose -f infrastructure/docker/docker-compose.dev.yml logs --tail=5 $service
done

# Network connectivity
echo -e "\nNetwork Test:"
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec fastapi-main ping -c 1 postgres || echo "Network issue detected"
```

### Performance Diagnostic
```bash
#!/bin/bash
# Performance diagnostic script

echo "=== Performance Diagnostic ==="

# Resource usage
echo "Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Disk usage
echo -e "\nDisk Usage:"
df -h | grep -E "(/$|/Volumes)"
docker system df

# Process monitoring
echo -e "\nProcess Status:"
ps aux | grep -E "(python|node|postgres|redis)" | grep -v grep | wc -l | xargs echo "Active processes:"
```

### API Endpoint Testing
```bash
#!/bin/bash
# API endpoint testing script

BASE_URL="http://localhost:8009"
API_URL="$BASE_URL/api/v1"

echo "=== API Endpoint Test ==="

# Health check
curl -s "$BASE_URL/health" | grep -q "ok" && echo "✓ Health endpoint OK" || echo "✗ Health endpoint failed"

# Authentication test (without credentials)
curl -s -o /dev/null -w "%{http_code}" "$API_URL/users/me" | grep -q "401" && echo "✓ Auth protection working" || echo "✗ Auth issue"

# CORS test
curl -s -H "Origin: http://localhost:5179" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS "$API_URL/health" | grep -q "Access-Control" && echo "✓ CORS configured" || echo "✗ CORS issue"
```

### Frontend Build Test
```bash
#!/bin/bash
# Frontend build and test script

echo "=== Frontend Diagnostic ==="

cd apps/dashboard

# Dependencies check
echo "Dependency Status:"
npm outdated --depth=0 | head -10

# Type check
echo -e "\nType Check:"
npm run typecheck && echo "✓ Types OK" || echo "✗ Type errors found"

# Build test
echo -e "\nBuild Test:"
NODE_OPTIONS="--max_old_space_size=2048" npm run build && echo "✓ Build OK" || echo "✗ Build failed"

# Test run
echo -e "\nTest Status:"
npm test -- --run --reporter=basic && echo "✓ Tests OK" || echo "✗ Tests failed"

cd ../..
```

### Database Connection Test
```bash
#!/bin/bash
# Database connection testing

echo "=== Database Diagnostic ==="

# PostgreSQL connection
echo "PostgreSQL Connection:"
psql "postgresql://eduplatform:eduplatform2024@localhost:5434/educational_platform_dev" \
     -c "SELECT version();" > /dev/null 2>&1 && echo "✓ PostgreSQL OK" || echo "✗ PostgreSQL connection failed"

# Redis connection
echo -e "\nRedis Connection:"
redis-cli -p 6381 ping | grep -q "PONG" && echo "✓ Redis OK" || echo "✗ Redis connection failed"

# Migration status
echo -e "\nMigration Status:"
cd apps/backend
alembic current 2>/dev/null && echo "✓ Migrations current" || echo "✗ Migration issues"
cd ../..
```

---

## Additional Resources

### Log Locations
```bash
# Application logs
tail -f logs/application.log

# Docker container logs
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f fastapi-main

# System logs (macOS)
tail -f /var/log/system.log

# Nginx logs (if running)
tail -f /usr/local/var/log/nginx/error.log
```

### Configuration Files
- Main environment: `.env`
- Docker Compose: `infrastructure/docker/docker-compose.dev.yml`
- Backend config: `apps/backend/core/config.py`
- Frontend config: `apps/dashboard/vite.config.ts`
- Database config: `alembic.ini`

### Useful Commands Reference
```bash
# Start everything
make dev

# Start individual services
make backend
make dashboard

# Run tests
make test

# Clean up
docker-compose -f infrastructure/docker/docker-compose.dev.yml down
docker system prune -f

# Reset everything
docker-compose -f infrastructure/docker/docker-compose.dev.yml down -v
rm -rf venv/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Remember to check the most recent documentation in the `docs/` directory and the Docker setup guides in `infrastructure/docker/` for the latest configuration details.