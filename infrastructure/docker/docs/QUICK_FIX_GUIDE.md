# Docker Container Quick Fix Guide

## 🚀 Quick Commands

### Apply All Fixes

```bash
cd /Users/grayghostdataconsultants/Development/projects/clients/Toolbox014/ToolboxAI-Solutions

# Stop and remove affected containers
docker stop toolboxai-mcp toolboxai-coordinator
docker rm toolboxai-mcp toolboxai-coordinator

# Restart with updated configuration
docker compose -f infrastructure/docker/compose/docker-compose.fast-dev.yml up -d
```

### Validate Fixes

```bash
# Run validation script
./scripts/docker-validate.sh

# Or manually check logs
docker logs toolboxai-mcp --tail 50
docker logs toolboxai-coordinator --tail 50
docker logs toolboxai-backend --tail 50
```

## 📋 Issues Fixed

### ✅ MCP Server
- **Problem**: Missing `numpy` and `tiktoken` dependencies
- **Fix**: Added to pip install command
- **Verification**: Check logs for "✅ MCP dependencies installed"

### ✅ Agent Coordinator
- **Problem**: Missing `numpy` and `psutil` dependencies, wrong module path
- **Fix**: Added dependencies and changed `coordinator` to `orchestrator`
- **Verification**: Check logs for "✅ Coordinator dependencies installed"

### ℹ️ Dashboard 401 Errors
- **Status**: Expected behavior (not a bug)
- **Reason**: Unauthenticated requests require login
- **Action**: Verify authentication flow if login is broken

## 🔍 Testing Steps

### 1. Check Container Status
```bash
docker ps --filter "name=toolboxai-"
```

Expected: All 6 containers running
- toolboxai-postgres
- toolboxai-redis
- toolboxai-backend
- toolboxai-dashboard
- toolboxai-mcp
- toolboxai-coordinator

### 2. Test Endpoints
```bash
# Backend health
curl http://localhost:8009/health

# MCP Server health
curl http://localhost:9877/health

# Coordinator health
curl http://localhost:8888/health

# Dashboard (should return HTML)
curl http://localhost:5179
```

### 3. Test Authentication
```bash
# Login request
curl -X POST http://localhost:8009/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# Use returned token in subsequent requests
TOKEN="<your-token-here>"
curl http://localhost:8009/api/v1/dashboard/overview \
  -H "Authorization: Bearer $TOKEN"
```

## 🛠️ Troubleshooting

### Container Won't Start
```bash
# View detailed logs
docker logs toolboxai-<service> --tail 100 -f

# Check container status
docker inspect toolboxai-<service>

# Restart specific container
docker restart toolboxai-<service>
```

### Port Conflicts
```bash
# Check what's using ports
lsof -i :8009
lsof -i :9877
lsof -i :8888

# Kill process if needed
kill -9 <PID>
```

### Database Connection Issues
```bash
# Check PostgreSQL health
docker exec toolboxai-postgres pg_isready -U toolboxai

# Check Redis health
docker exec toolboxai-redis redis-cli ping
```

### Full Reset (Nuclear Option)
```bash
# Stop all containers
docker compose -f infrastructure/docker/compose/docker-compose.fast-dev.yml down

# Remove all containers and volumes
docker compose -f infrastructure/docker/compose/docker-compose.fast-dev.yml down -v

# Start fresh
docker compose -f infrastructure/docker/compose/docker-compose.fast-dev.yml up -d
```

## 📊 Expected Results

### Successful Startup Logs

**MCP Server:**
```
🔧 Installing MCP dependencies...
✅ MCP dependencies installed
🚀 Starting MCP server...
INFO:     Uvicorn running on http://0.0.0.0:9877
```

**Coordinator:**
```
🔧 Installing coordinator dependencies...
✅ Coordinator dependencies installed
🚀 Starting coordinator...
INFO:     Uvicorn running on http://0.0.0.0:8888
```

**Backend:**
```
🚀 Starting FastAPI backend...
INFO:     Uvicorn running on http://0.0.0.0:8009
```

## 🔗 Related Files

- **Docker Compose**: `infrastructure/docker/compose/docker-compose.fast-dev.yml`
- **Validation Script**: `scripts/docker-validate.sh`
- **Full Documentation**: `infrastructure/docker/docs/DOCKER_FIXES_2025-09-30.md`
- **Requirements**: `requirements.txt`

## 📞 Need More Help?

1. Check full documentation: `DOCKER_FIXES_2025-09-30.md`
2. Review container logs: `docker logs <container-name>`
3. Run validation script: `./scripts/docker-validate.sh`
4. Check Docker Compose config: `docker compose -f <file> config`

---

**Last Updated**: 2025-09-30
**Status**: ✅ Fixes Applied and Tested
