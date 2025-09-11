# Debugger Terminal: Error Resolution & Monitoring Task List

## 🎯 PRIMARY OBJECTIVE
Monitor all services, fix critical errors in real-time, handle merge conflicts, and ensure system stability.

## 🌳 BRANCH
```bash
git checkout -b fix/test-failures
```

## 📋 CONTINUOUS MONITORING TASKS

### Real-time Service Monitoring

#### Background Process IDs:
- **FastAPI**: PID 545248 (Port 8008)
- **Flask Bridge**: PID 693637 (Port 5001)  
- **Dashboard**: PID 71a6c3 (Port 3000)
- **MCP Server**: PID c6091f (Port 9876)

#### Monitor Commands:
```bash
# Check service health
curl -s http://localhost:8008/health | jq
curl -s http://localhost:5001/health | jq
curl -s http://localhost:3000 # Dashboard
curl -s ws://localhost:9876 # WebSocket

# Monitor logs
tail -f logs/*.log

# Check background processes
./scripts/terminal_sync/sync.sh debugger check
```

## 🔍 ERROR DETECTION & RESOLUTION

### Priority 1: Critical Errors (Immediate)

#### 1.1 Service Crashes
**Tools**: Bash, BashOutput, Task(debugger)

```bash
# Check if service is running
ps aux | grep [process_id]

# Restart if crashed
cd ToolboxAI-Roblox-Environment
venv_clean/bin/uvicorn server.main:app --reload &

# Log the issue
echo "[$(date)] Service restart: [service_name]" >> logs/debugger.log
```

#### 1.2 Database Connection Errors
**Tools**: Bash, Task(database-migrator)

```bash
# Test database connections
psql -h localhost -U grayghostdata -d educational_platform -c "SELECT 1"

# Fix connection pool
# Check max connections
psql -c "SHOW max_connections"
psql -c "SELECT count(*) FROM pg_stat_activity"
```

### Priority 2: Test Failures (Within 1 hour)

#### 2.1 Analyze Failing Tests
**Tools**: Bash, Grep, Task(debugger)

```bash
# Run specific failing test with debug
venv_clean/bin/pytest -xvs [test_file]::[test_name]

# Capture full stack trace
venv_clean/bin/pytest --tb=long [test_file]

# Check test dependencies
venv_clean/bin/pip list | grep -E "pytest|mock|faker"
```

#### 2.2 Common Fixes

**SPARC Initialize State Error**:
```python
# Add to sparc/state_manager.py
def initialize_state(self, initial_context: Dict[str, Any]) -> None:
    self.state = {
        'context': initial_context,
        'timestamp': datetime.now(),
        'version': '1.0.0'
    }
```

**Async Test Hanging**:
```python
# Add timeout to async tests
@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_async_operation():
    # test code
```

### Priority 3: Performance Issues (Within 2 hours)

#### 3.1 Memory Leaks
**Tools**: Bash, Task(debugger)

```bash
# Monitor memory usage
while true; do
    ps aux | grep python | awk '{print $11, $6}'
    sleep 60
done

# Python memory profiling
python -m memory_profiler [script.py]
```

#### 3.2 Slow Queries
```bash
# Enable query logging
psql -c "ALTER SYSTEM SET log_statement = 'all'"
psql -c "ALTER SYSTEM SET log_duration = on"
psql -c "SELECT pg_reload_conf()"

# Check slow queries
psql -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10"
```

## 🔄 INTER-TERMINAL SUPPORT

### Terminal 1 Support (Backend)
Monitor for:
- Agent test failures
- API endpoint errors
- Database deadlocks

Common fixes:
```python
# Fix import errors
try:
    from database.models import DifficultyLevel
except ImportError:
    # Fallback
    from enum import Enum
    class DifficultyLevel(Enum):
        BEGINNER = "beginner"
```

### Terminal 2 Support (Frontend)
Monitor for:
- WebSocket disconnections
- React render errors
- Build failures

Common fixes:
```typescript
// Fix WebSocket reconnection
ws.onclose = () => {
    setTimeout(() => {
        reconnect();
    }, 5000);
};
```

### Terminal 3 Support (Roblox)
Monitor for:
- Lua syntax errors
- HTTP timeout issues
- Plugin crashes

Common fixes:
```lua
-- Add error handling
local success, result = pcall(function()
    return HttpService:GetAsync(url)
end)
if not success then
    warn("HTTP Error: " .. tostring(result))
end
```

## 🛠️ DEBUGGING TOOLS & AGENTS

### Primary Agents:
- **debugger**: Core debugging operations
- **security**: Security issue detection
- **reviewer**: Code quality checks
- **database-migrator**: Database fixes

### Primary Tools:
- **Bash/BashOutput**: Monitor services
- **Grep**: Search for errors
- **Task**: Complex debugging
- **MultiEdit**: Batch fixes

## 📊 HEALTH METRICS TO TRACK

### System Health:
- [ ] All services running (4/4)
- [ ] Response times < 200ms
- [ ] Memory usage < 80%
- [ ] CPU usage < 70%
- [ ] No critical errors in last hour

### Test Health:
- [ ] Unit tests: 95%+ passing
- [ ] Integration tests: 90%+ passing
- [ ] E2E tests: 85%+ passing
- [ ] No hanging tests

## 🚨 EMERGENCY PROCEDURES

### Service Down:
1. Check process status
2. Review logs for errors
3. Restart service
4. Notify affected terminals
5. Document root cause

### Database Lock:
```sql
-- Find blocking queries
SELECT pid, usename, query, state
FROM pg_stat_activity
WHERE state != 'idle' AND query NOT ILIKE '%pg_stat_activity%'
ORDER BY query_start;

-- Kill blocking query
SELECT pg_terminate_backend(pid);
```

### Memory Crisis:
```bash
# Emergency cleanup
sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches

# Kill memory hogs
ps aux | sort -nrk 4 | head -5
kill -9 [pid]
```

## 📝 COMMUNICATION PROTOCOL

### Hourly Health Check:
```bash
./scripts/terminal_sync/sync.sh debugger status "All systems operational - [details]"
```

### Error Detected:
```bash
./scripts/terminal_sync/sync.sh debugger message "CRITICAL: [error] in [service]" all
```

### Fix Deployed:
```bash
./scripts/terminal_sync/sync.sh debugger message "FIXED: [issue] - deployed to [branch]" [terminal]
```

### Daily Report:
```bash
# Generate comprehensive report
./scripts/terminal_sync/sync.sh debugger report

# Include:
# - Service uptime
# - Errors fixed
# - Performance metrics
# - Recommendations
```

## 🔧 DEBUGGING COMMANDS REFERENCE

### Python Debugging:
```bash
# Interactive debugger
python -m pdb [script.py]

# Memory profiling
python -m memory_profiler [script.py]

# Line profiling
kernprof -l -v [script.py]

# Trace calls
python -m trace --trace [script.py]
```

### JavaScript Debugging:
```bash
# Node inspector
node --inspect [script.js]

# Chrome DevTools
chrome://inspect

# Memory leaks
node --expose-gc --inspect [script.js]
```

### Database Debugging:
```sql
-- Connection info
SELECT * FROM pg_stat_activity;

-- Lock info  
SELECT * FROM pg_locks;

-- Table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

## 📝 NOTES

- Keep detailed logs of all fixes
- Prioritize blocking issues
- Communicate fixes immediately
- Update TODO.md with resolved issues
- Create hotfix branches when needed
- Document patterns for future reference