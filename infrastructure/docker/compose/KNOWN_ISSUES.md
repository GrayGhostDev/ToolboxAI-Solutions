# Known Issues - Docker Development Environment

**Last Updated**: 2025-11-01
**Status**: Active issues being tracked

---

## Critical Issues 🔴

### None Currently

All critical blocking issues have been resolved.

---

## High Priority Issues 🟠

### 1. Agent Coordinator - Pydantic v2.10 Compatibility

**Service**: agent-coordinator
**Status**: ⏸️ Disabled via profile
**Impact**: AI agent coordination features unavailable
**Root Cause**: LangSmith dependency incompatibility

#### Description

The agent-coordinator service fails to start with Pydantic v2.10+ due to a compatibility issue in the LangSmith library. The error occurs in `langsmith._internal/_beta_decorator.py`:

```python
AttributeError: type object 'ForwardRef' has no attribute '_evaluate'
# at langsmith._internal._beta_decorator:120
```

This is caused by LangSmith using Pydantic v1 internal API (`ForwardRef._evaluate()`) which was removed in Pydantic v2.10.

#### Current Status

- **Temporary Solution**: Service disabled via Docker Compose profile `agents`
- **Workaround**: `LANGCHAIN_TRACING_V2: "false"` added to environment to disable tracing
- **Impact**: Agent coordination features not available in development

#### Possible Solutions

**Option A: Downgrade Pydantic (Quick Fix)**
```bash
# In requirements.txt
pydantic==2.9.2  # Change from 2.10.3
```
**Pros**: Immediate fix
**Cons**: May cause compatibility issues with other packages
**Risk**: Medium

**Option B: Wait for LangSmith Update (Recommended)**
```bash
# Monitor LangSmith releases
# https://github.com/langchain-ai/langsmith-sdk/releases
```
**Pros**: No regression risk, proper fix
**Cons**: Timing uncertain
**Risk**: Low

**Option C: Fork and Patch LangSmith (Advanced)**
```bash
# Create local fork with Pydantic v2 compatibility
# Install from git in requirements.txt
```
**Pros**: Full control
**Cons**: Maintenance burden
**Risk**: High

#### Re-enabling the Service

Once fixed, re-enable with:
```bash
docker compose --profile agents up -d
```

#### References

- **Issue Filed**: https://github.com/langchain-ai/langsmith-sdk/issues/XXX (TODO)
- **Pydantic v2 Migration Guide**: https://docs.pydantic.dev/latest/migration/
- **Related**: Celery workers also had openai import issues (now fixed)

---

## Medium Priority Issues 🟡

### 2. Celery Worker - OpenAI Package Missing (RESOLVED ✅)

**Service**: celery-worker
**Status**: ✅ Resolved
**Date Resolved**: 2025-11-01

#### Description

Celery workers failed to import `openai` module because the celery-worker image is built separately from the backend image and didn't include all dependencies.

#### Resolution

1. Rebuilt celery-worker image (includes full `requirements.txt`)
2. Rebuilt celery-beat image (same issue)
3. Both services now have access to openai package via langchain-openai dependency

#### Verification

```bash
docker run --rm toolboxai/celery-worker:latest python -c "import openai; print('✅ OK')"
```

---

### 3. Cleanup Tasks - Database Session Import (RESOLVED ✅)

**Service**: celery-worker
**Status**: ✅ Resolved
**Date Resolved**: 2025-11-01

#### Description

`apps/backend/tasks/cleanup_tasks.py` attempted to import `get_session()` function which doesn't exist in the database module.

#### Resolution

Modified `cleanup_tasks.py`:
- Line 17: Changed from `get_session` to `get_db`
- Line 122: Changed from `with get_session()` to `with next(get_db())`

The `get_db()` function is a generator that yields database sessions, so `next()` is needed to get the actual session.

---

### 4. Log File Permissions in Containers (RESOLVED ✅)

**Service**: celery-worker, celery-beat
**Status**: ✅ Resolved
**Date Resolved**: 2025-11-01

#### Description

Containers running as specific UIDs (1005, 1006) couldn't write to host-mounted log directories owned by different UID on macOS.

#### Resolution

Changed log mounts to use tmpfs (in-memory filesystem):

```yaml
# Before
volumes:
  - celery_logs:/app/logs:Z

# After
tmpfs:
  - /app/logs
```

**Trade-off**: Logs are lost on container restart, but acceptable for development.

**Production**: Host-mounted volumes will work due to proper UID mapping.

---

## Low Priority Issues 🟢

### 5. MCP Server Health Status

**Service**: mcp-server
**Status**: ⚠️ Monitoring
**Impact**: Low - MCP features may be unavailable

#### Description

MCP server may show unhealthy status depending on configuration and dependencies.

#### Current Status

- Not critical for core development workflow
- Model Context Protocol features optional
- Service continues running even if health check fails

#### Action Items

- [ ] Review MCP server logs when needed
- [ ] Verify health endpoint responds
- [ ] May need dependency rebuild similar to celery fix

---

### 6. Redis Cloud Connector

**Service**: redis-cloud-connector
**Status**: ⏸️ Disabled via profile
**Impact**: None for local development

#### Description

Redis Cloud Connector service was failing health checks because it requires cloud-specific certificates and configuration that don't exist in local development.

#### Resolution

Disabled via profile `cloud` - only enable when working with Redis Cloud/LangCache features.

#### Re-enabling

```bash
# Add cloud certificates to infrastructure/config/certificates/
docker compose --profile cloud up -d
```

---

## Informational 📝

### Services Intentionally Disabled

The following services are disabled by default via Docker Compose profiles to optimize the development environment:

1. **backup-coordinator** - Backups not needed in dev
2. **migration-runner** - Migrations run manually when needed
3. **roblox-sync** - Optional Roblox integration
4. **prometheus** - Optional metrics collection
5. **celery-flower** - Optional Celery monitoring (can enable if needed)

These are **not issues** - they're intentional optimizations.

---

## Docker Daemon on macOS

**Issue**: Docker commands fail with "Cannot connect to the Docker daemon"
**Cause**: Docker Desktop not running or socket path issue
**Resolution**:
1. Start Docker Desktop application
2. Wait for "Docker is running" indicator
3. Verify: `docker ps` should work

---

## Monitoring & Tracking

### Issue Lifecycle

1. **Identified**: Issue discovered and documented here
2. **Investigated**: Root cause analysis performed
3. **Workaround Applied**: Temporary solution implemented
4. **Permanent Fix**: Proper resolution deployed
5. **Verified**: Fix tested and confirmed
6. **Resolved**: Issue closed and marked ✅

### How to Report New Issues

1. Check if issue already documented here
2. Gather relevant logs: `docker compose logs service-name`
3. Check service health: `docker compose ps`
4. Document in this file with:
   - Service affected
   - Error message
   - Steps to reproduce
   - Impact assessment
   - Attempted solutions

---

## Future Improvements

### Planned Enhancements

1. **Automated Health Monitoring**
   - Script to check all service health periodically
   - Alert on service failures
   - Auto-restart unhealthy services

2. **Dependency Version Locking**
   - Pin all dependency versions to avoid compatibility issues
   - Regular dependency update schedule
   - Automated testing of dependency upgrades

3. **Service Startup Orchestration**
   - Better dependency ordering
   - Retry logic for transient failures
   - Graceful degradation for optional services

4. **Documentation Improvements**
   - Video walkthroughs for common tasks
   - Troubleshooting decision tree
   - Performance tuning guide

---

## References

- [SERVICE_STATUS.md](./SERVICE_STATUS.md) - Current service configuration
- [docker-compose.yml](./docker-compose.yml) - Base configuration
- [docker-compose.dev.yml](./docker-compose.dev.yml) - Development overrides
- [Pydantic Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [Celery Documentation](https://docs.celeryq.dev/)

---

## Contact & Support

For urgent issues:
1. Check this document first
2. Review SERVICE_STATUS.md for configuration
3. Check service logs for error details
4. Ask team for assistance if needed

**Last Review**: 2025-11-01
**Next Review**: When new issues discovered or existing issues resolved
