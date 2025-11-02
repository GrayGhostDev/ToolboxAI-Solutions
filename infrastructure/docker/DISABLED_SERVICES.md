# Disabled Services - Development Environment

**Date**: 2025-11-01
**Status**: Temporarily disabled for development
**Last Updated**: Session continuation after context limit

## Summary

Four services have been temporarily disabled in the development environment due to technical issues that require deeper investigation or dependency updates. The core platform functionality remains operational.

## Core Services Status ✅

### Healthy Services (6/13 running)
- **PostgreSQL** - Database fully operational on port 5434
- **Redis** - Cache fully operational on port 6381
- **Backend API** - FastAPI running on port 8009 (status: degraded but functional)
- **Dashboard** - React UI serving on port 5179
- **MCP Server** - Model Context Protocol running on port 9876
- **Redis Commander** - Redis admin UI on port 8081
- **Adminer** - Database admin UI on port 8080
- **MailHog** - Email testing on ports 1025 (SMTP) / 8025 (UI)

### Operational But Unhealthy (5)
Services that are running and functional but failing health checks:
- **dashboard** - Vite dev server running correctly, health check timeout
- **mcp-server** - MCP server listening correctly, health check config issue
- **celery-worker** (2 instances) - Logs permission prevents full startup
- **redis-cloud** - Running but health check failing

## Disabled Services ❌

### 1. agent-coordinator
**Status**: Disabled
**Port**: 8888
**Issue**: **Pydantic v1/v2 Compatibility**

#### Root Cause
- Python 3.12's `ForwardRef._evaluate()` signature changed
- langsmith 0.4.39 still uses Pydantic v1 compatibility layer
- Pydantic 2.10.3 broke backward compatibility
- Error occurs at module import time (before env vars are checked)

#### Error Message
```python
TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'
  File "/opt/venv/lib/python3.12/site-packages/pydantic/v1/typing.py", line 66, in evaluate_forwardref
```

#### Attempted Fixes
1. ✅ Upgraded langsmith from 0.4.31 → 0.4.39 (didn't resolve)
2. ❌ Disabled LangSmith tracing via env vars (import happens before env check)
3. ❌ Environment variable override (too late in execution)

#### Resolution Options
1. **Downgrade Pydantic** to 2.9.x (risky - may break other dependencies)
2. **Wait for langsmith** to complete Pydantic v2 migration
3. **Use alternative** - Switch to langfuse or other tracing library
4. **Disable service** in development (current approach)

#### Files Modified
- `requirements.txt` - langsmith==0.4.39
- `docker-compose.dev.yml` - Added LANGCHAIN_TRACING_V2=false (ineffective)
- `infrastructure/docker/dockerfiles/agents.Dockerfile` - Rebuilt with updated deps

#### Impact
- No AI agent orchestration in development
- Agent-related endpoints will return errors
- Core platform functionality unaffected

---

### 2. celery-beat
**Status**: Disabled
**Port**: N/A (scheduler service)
**Issue**: **File Permission Error**

#### Root Cause
- Container runs as `toolboxai` user (UID 1001)
- Host `logs/` directory owned by different UID
- Backend initialization tries to create `/app/logs/server.log`
- Permission denied on container startup

#### Error Message
```python
PermissionError: [Errno 13] Permission denied: '/app/logs/server.log'
  File "/usr/local/lib/python3.12/logging/__init__.py", line 1263, in _open
```

#### Attempted Fixes
1. ❌ `chmod 777 logs/` - Permission issue persists inside container
2. ❌ `touch logs/server.log && chmod 666` - Ownership mismatch
3. ❌ Tmpfs mount for logs - Named volume conflict in dev config

#### Resolution Options
1. **Fix ownership** - `chown -R 1001:1001 logs/` (requires sudo)
2. **Use tmpfs** - Remove named volume, use tmpfs consistently
3. **Disable file logging** - Use stdout/stderr only in development
4. **Run as root** - Already configured but volume mounts override

#### Files Modified
- `logs/server.log` - Created with wrong permissions

#### Impact
- No scheduled Celery tasks in development
- Periodic jobs (cleanup, reports, etc.) won't run
- On-demand tasks via Celery workers still functional

---

### 3. backup-coordinator
**Status**: Disabled
**Port**: N/A (background service)
**Issue**: **Python Module Path**

#### Root Cause
- `backup_manager.py` exists at correct path
- Missing `__init__.py` files prevented Python module recognition
- Docker command: `python -m infrastructure.backups.scripts.backup_manager status`
- Module could not be imported despite file existence

#### Error Message
```
/opt/venv/bin/python: No module named infrastructure.backups.scripts.backup_manager
```

#### Attempted Fixes
1. ✅ Created `infrastructure/__init__.py`
2. ✅ Created `infrastructure/backups/__init__.py`
3. ✅ Created `infrastructure/backups/scripts/__init__.py`
4. ❌ Files not visible in container - need volume mount or rebuild

#### Resolution Options
1. **Add volume mount** - Mount `infrastructure/` directory in dev config
2. **Rebuild image** - Bake `__init__.py` files into backend image
3. **Disable in dev** - Backups already disabled via `BACKUP_ENABLED=false`

#### Files Created
- `/Volumes/.../infrastructure/__init__.py`
- `/Volumes/.../infrastructure/backups/__init__.py`
- `/Volumes/.../infrastructure/backups/scripts/__init__.py`

#### Impact
- No automated backups in development (already disabled by default)
- Production backups unaffected
- Manual backup scripts still work

---

### 4. celery-flower
**Status**: Disabled
**Port**: 5555
**Issue**: **Entrypoint Permission**

#### Root Cause
- Entrypoint script `/app/entrypoint.sh` lacks execute permissions
- Image build process didn't set executable bit
- Docker compose override uses different command format

#### Error Message
```
failed to create task for container: exec: "/app/entrypoint.sh": permission denied
```

#### Attempted Fixes
1. ❌ Service failed to start multiple times
2. ✅ Added command override in docker-compose.dev.yml

#### Resolution Options
1. **Fix Dockerfile** - Add `RUN chmod +x /app/entrypoint.sh`
2. **Use direct command** - Already configured in dev override
3. **Rebuild image** - Rebuild celery-flower with proper permissions

#### Files Modified
- `docker-compose.dev.yml` - Added command override for celery-flower

#### Impact
- No Flower web UI for monitoring Celery tasks
- Celery workers still functional
- Can use `docker logs` for monitoring instead

---

## Workarounds

### For Agent Orchestration
Use backend API endpoints directly:
```bash
curl http://localhost:8009/api/v1/agents/status
```

### For Scheduled Tasks
Manually trigger tasks via Celery CLI:
```bash
docker exec compose-celery-worker-1 celery -A apps.backend.celery_app call tasks.cleanup
```

### For Backups
Run manual backup scripts:
```bash
docker exec toolboxai-postgres pg_dump -U toolboxai toolboxai > backup.sql
```

### For Flower Monitoring
Use Celery inspect commands:
```bash
docker exec compose-celery-worker-1 celery -A apps.backend.celery_app inspect active
docker exec compose-celery-worker-1 celery -A apps.backend.celery_app inspect stats
```

## Next Steps

### Immediate (Next Session)
1. **Verify Pydantic compatibility** - Test with pydantic==2.9.2
2. **Fix logs permissions** - `sudo chown -R 1001:1001 logs/` on host
3. **Rebuild backend** - Include `__init__.py` files for backup module
4. **Fix Flower entrypoint** - Update Dockerfile with proper permissions

### Short-term (This Week)
1. Monitor langsmith releases for Pydantic v2 support
2. Review all health checks - some may need timeout adjustments
3. Test celery-worker with tmpfs logs instead of volumes
4. Update documentation with service dependencies

### Long-term (This Month)
1. Consider migration to pydantic v2-compatible tracing (langfuse)
2. Implement centralized logging to eliminate file permission issues
3. Review all Dockerfiles for permission best practices
4. Add automated health check validation in CI/CD

## Testing Commands

Verify core services:
```bash
# Backend health
curl http://localhost:8009/health

# Dashboard accessibility
curl -I http://localhost:5179

# Redis connectivity
redis-cli -h localhost -p 6381 ping

# Database connectivity
PGPASSWORD=devpass2024 psql -h localhost -p 5434 -U toolboxai -d toolboxai -c "SELECT 1;"

# MCP server (websocket)
websocat ws://localhost:9877
```

Check service status:
```bash
cd infrastructure/docker/compose
docker compose -f docker-compose.yml -f docker-compose.dev.yml ps
```

View logs:
```bash
# All services
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

# Specific service
docker logs -f toolboxai-backend
```

## References

- Main compose file: `infrastructure/docker/compose/docker-compose.yml`
- Dev overrides: `infrastructure/docker/compose/docker-compose.dev.yml`
- Dockerfiles: `infrastructure/docker/dockerfiles/`
- Requirements: `requirements.txt` (langsmith==0.4.39, pydantic==2.10.3)

---

**Note**: This document should be updated when services are re-enabled or when workarounds become permanent solutions.
