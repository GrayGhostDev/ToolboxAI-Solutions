# Supabase Integration Troubleshooting Guide

## Overview

This guide helps diagnose and resolve issues with the Supabase integration in the ToolBoxAI platform, including LangChain 0.3.26+ LCEL compatibility, React 19 frontend integration, and real-time features.

## Quick Diagnostics

### System Health Check

Run this comprehensive diagnostic script:

```bash
cd /path/to/ToolBoxAI-Solutions

python -c "
print('🔍 SUPABASE INTEGRATION DIAGNOSTICS')
print('='*50)

# Test 1: Environment Configuration
try:
    from toolboxai_settings.settings import settings
    config = settings.get_supabase_config()
    configured = settings.is_supabase_configured()
    print(f'✅ Configuration: Configured={configured}')
    if configured:
        print(f'   URL: {config[\"url\"][:30]}...')
        print(f'   Has Anon Key: {bool(config[\"anon_key\"])}')
        print(f'   Has Service Key: {bool(config[\"service_role_key\"])}')
except Exception as e:
    print(f'❌ Configuration Error: {e}')

# Test 2: Service Availability
try:
    from apps.backend.services.supabase_service import get_supabase_service
    service = get_supabase_service()
    available = service.is_available()
    print(f'✅ Service: Available={available}')
except Exception as e:
    print(f'❌ Service Error: {e}')

# Test 3: LangChain LCEL Compatibility
try:
    from core.langchain_lcel_compat import LANGCHAIN_CORE_AVAILABLE, get_compatible_llm
    llm = get_compatible_llm('gpt-4', temperature=0.7)
    print(f'✅ LangChain LCEL: Core={LANGCHAIN_CORE_AVAILABLE}, LLM Created=True')
except Exception as e:
    print(f'❌ LangChain Error: {e}')

# Test 4: Agent System
try:
    from apps.backend.services.agent_service import AgentService
    agent_service = AgentService()
    print(f'✅ Agents: {len(agent_service.agents)} agents initialized')
except Exception as e:
    print(f'❌ Agent Error: {e}')

print('='*50)
"
```

## Common Issues and Solutions

### 1. LangChain 0.3.26+ Compatibility Issues

#### Problem: LLMChain Import Errors
```
Error: LLMChain.__init_subclass__() takes no keyword arguments
```

**Solution**: Use LCEL compatibility layer
```python
# ❌ Old approach (causes errors)
from langchain.chains import LLMChain

# ✅ New approach (LCEL compatible)
from core.langchain_lcel_compat import LLMChain, get_compatible_llm

# Create compatible LLM
llm = get_compatible_llm("gpt-4", temperature=0.7)
chain = LLMChain(llm=llm, prompt=prompt)
```

#### Problem: Agent Import Failures
```
Error: cannot import name 'AgentExecutor' from 'langchain.agents'
```

**Solution**: Use LCEL agent executor
```python
# ❌ Old approach
from langchain.agents import AgentExecutor

# ✅ New approach
from core.langchain_lcel_compat import AgentExecutor
```

### 2. Supabase Connection Issues

#### Problem: Supabase Not Available
```
Error: Supabase is not available or configured
```

**Diagnosis Steps:**
```bash
# 1. Check environment variables
echo "SUPABASE_URL: $SUPABASE_URL"
echo "SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY:0:20}..."

# 2. Test connection
curl -H "apikey: $SUPABASE_ANON_KEY" "$SUPABASE_URL/rest/v1/"

# 3. Check Python client
python -c "
try:
    from supabase import create_client
    client = create_client('$SUPABASE_URL', '$SUPABASE_ANON_KEY')
    print('✅ Supabase client created')
except Exception as e:
    print(f'❌ Client error: {e}')
"
```

**Solutions:**
1. **Missing Environment Variables**:
   ```bash
   # Add to .env file
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_service_key
   ```

2. **Invalid Credentials**:
   - Verify keys in Supabase dashboard: Settings → API
   - Ensure keys are not expired
   - Check project URL is correct

3. **Network Issues**:
   ```bash
   # Test network connectivity
   ping your-project.supabase.co
   curl -I https://your-project.supabase.co
   ```

#### Problem: Supabase Tables Not Found
```
Error: relation "agent_instances" does not exist
```

**Solution**: Run migrations
```bash
# Check if tables exist
python -c "
from apps.backend.services.supabase_service import get_supabase_service
import asyncio
service = get_supabase_service()
if service.is_available():
    try:
        result = service.client.table('agent_instances').select('count').execute()
        print('✅ Tables exist')
    except Exception as e:
        print(f'❌ Tables missing: {e}')
        print('Run: python scripts/supabase_migration_automation.py')
"

# Run migrations
python scripts/supabase_migration_automation.py
```

### 3. React 19 Frontend Issues

#### Problem: Hook Compatibility Issues
```
Error: startTransition is not a function
```

**Solution**: Ensure React 19 is properly installed
```bash
# Check React version
cd apps/dashboard
npm list react react-dom

# Should show React 19.x.x
# If not, update:
npm install react@19 react-dom@19 @types/react@19 @types/react-dom@19
```

#### Problem: Supabase Client Issues in Frontend
```
Error: createClient is not a function
```

**Solution**: Check Supabase client installation
```bash
cd apps/dashboard

# Check Supabase client version
npm list @supabase/supabase-js

# Should show 2.39.0+
# If not installed:
npm install @supabase/supabase-js@latest
```

#### Problem: Environment Variables Not Loading
```
Error: import.meta.env.VITE_SUPABASE_URL is undefined
```

**Solution**: Check frontend environment configuration
```bash
# Verify .env.local exists and has correct variables
cat apps/dashboard/.env.local

# Should contain:
# VITE_SUPABASE_URL=https://your-project.supabase.co
# VITE_SUPABASE_ANON_KEY=your_anon_key

# Restart development server after adding variables
cd apps/dashboard && npm run dev
```

### 4. Real-time Integration Issues

#### Problem: Real-time Events Not Working
```
Error: WebSocket connection failed
```

**Diagnosis:**
```typescript
// Test real-time connection
import { supabase } from '../lib/supabase';

const testSubscription = supabase
  .channel('test-channel')
  .on('postgres_changes', { event: '*', schema: 'public', table: 'agent_instances' },
    (payload) => console.log('✅ Real-time working:', payload)
  )
  .subscribe((status) => {
    console.log('Subscription status:', status);
    if (status === 'SUBSCRIBED') {
      console.log('✅ Real-time connection established');
    } else {
      console.log('❌ Real-time connection failed:', status);
    }
  });
```

**Solutions:**
1. **Check Realtime is Enabled**:
   - Go to Supabase Dashboard → Settings → API
   - Ensure "Enable Realtime" is checked for your tables

2. **Verify Network Configuration**:
   ```bash
   # Test WebSocket connection
   wscat -c "wss://your-project.supabase.co/realtime/v1/websocket?apikey=$SUPABASE_ANON_KEY&vsn=1.0.0"
   ```

3. **Check RLS Policies**:
   ```sql
   -- Ensure realtime policies exist
   SELECT * FROM pg_policies WHERE tablename = 'agent_instances';
   ```

### 5. Agent System Issues

#### Problem: Agents Not Persisting to Supabase
```
Warning: Failed to persist agent to Supabase
```

**Diagnosis:**
```python
# Test agent persistence
from apps.backend.services.agent_service import AgentService
import asyncio

async def test_persistence():
    service = AgentService()

    if service.supabase_service:
        print('✅ Supabase service available')
        available = service.supabase_service.is_available()
        print(f'✅ Supabase available: {available}')

        if available:
            health = await service.supabase_service.health_check()
            print(f'✅ Health check: {health}')
    else:
        print('❌ Supabase service not initialized')

asyncio.run(test_persistence())
```

**Solutions:**
1. **Check Service Configuration**:
   ```python
   # Verify service initialization
   from apps.backend.services.supabase_service import get_supabase_service
   service = get_supabase_service()
   print('Client:', service.client)
   print('URL:', service.url)
   print('Available:', service.is_available())
   ```

2. **Verify Table Permissions**:
   ```sql
   -- Check if service role can access tables
   SELECT tablename, grantee, privilege_type
   FROM information_schema.role_table_grants
   WHERE table_schema = 'public' AND grantee = 'service_role';
   ```

### 6. Performance Issues

#### Problem: Slow Supabase Queries
```
Warning: Supabase query took 2000ms
```

**Diagnosis:**
```sql
-- Check query performance in Supabase SQL Editor
EXPLAIN ANALYZE SELECT * FROM agent_executions
WHERE agent_type = 'content_generator'
ORDER BY created_at DESC LIMIT 50;
```

**Solutions:**
1. **Add Missing Indexes**:
   ```sql
   -- Common performance indexes
   CREATE INDEX IF NOT EXISTS idx_agent_executions_type_created
   ON agent_executions(agent_type, created_at);

   CREATE INDEX IF NOT EXISTS idx_agent_instances_status
   ON agent_instances(status) WHERE status != 'offline';
   ```

2. **Optimize Queries**:
   ```typescript
   // ❌ Slow: Select all columns
   const data = await supabase.from('agent_executions').select('*');

   // ✅ Fast: Select specific columns
   const data = await supabase
     .from('agent_executions')
     .select('task_id, status, created_at')
     .limit(50);
   ```

3. **Use Connection Pooling**:
   ```bash
   # Backend configuration
   SUPABASE_CONNECTION_TIMEOUT=10
   SUPABASE_MAX_RETRIES=3
   ```

### 7. Docker Issues

#### Problem: Supabase Services Not Starting
```
Error: supabase-kong exited with code 1
```

**Diagnosis:**
```bash
# Check Docker logs
docker-compose logs supabase-kong
docker-compose logs supabase-db
docker-compose logs supabase-auth

# Check service health
docker-compose ps
```

**Solutions:**
1. **Check Kong Configuration**:
   ```bash
   # Verify Kong config file exists
   ls -la infrastructure/supabase/kong.yml

   # Check Kong config syntax
   docker run --rm -v $(pwd)/infrastructure/supabase/kong.yml:/kong.yml kong:2.8.1 kong config -c /kong.yml
   ```

2. **Database Connection Issues**:
   ```bash
   # Check database connectivity
   docker-compose exec supabase-db pg_isready -U postgres

   # Check database logs
   docker-compose logs supabase-db
   ```

3. **Port Conflicts**:
   ```bash
   # Check if ports are already in use
   lsof -i :54321  # Supabase Kong
   lsof -i :54322  # Supabase DB

   # Kill conflicting processes
   sudo lsof -ti:54321 | xargs kill -9
   ```

## Advanced Troubleshooting

### Network Connectivity

#### Test Supabase API Connectivity
```bash
# Test REST API
curl -H "apikey: $SUPABASE_ANON_KEY" \
     -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
     "$SUPABASE_URL/rest/v1/agent_instances?select=count"

# Test Auth API
curl -H "apikey: $SUPABASE_ANON_KEY" \
     "$SUPABASE_URL/auth/v1/settings"

# Test Realtime WebSocket
wscat -c "$SUPABASE_URL/realtime/v1/websocket?apikey=$SUPABASE_ANON_KEY&vsn=1.0.0"
```

#### Test Backend Integration
```python
# Test backend Supabase integration
import asyncio
from apps.backend.services.supabase_service import get_supabase_service

async def test_integration():
    service = get_supabase_service()

    print(f"Service available: {service.is_available()}")

    if service.is_available():
        # Test health check
        health = await service.health_check()
        print(f"Health check: {health}")

        # Test table access
        try:
            agents = await service.get_all_agent_instances()
            print(f"Agent instances: {len(agents)}")
        except Exception as e:
            print(f"Table access error: {e}")

asyncio.run(test_integration())
```

### Database Schema Issues

#### Check Table Existence
```sql
-- Run in Supabase SQL Editor
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name LIKE 'agent_%';
```

#### Verify Indexes
```sql
-- Check indexes
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename LIKE 'agent_%';
```

#### Check RLS Policies
```sql
-- Verify RLS policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd
FROM pg_policies
WHERE schemaname = 'public';
```

### Real-time Debugging

#### Frontend Real-time Issues
```typescript
// Debug real-time subscriptions
import { supabase } from '../lib/supabase';

// Enable debug mode
const debugSubscription = supabase
  .channel('debug-channel', {
    config: {
      broadcast: { self: true },
      presence: { key: 'debug-key' }
    }
  })
  .on('postgres_changes',
    { event: '*', schema: 'public', table: 'agent_instances' },
    (payload) => {
      console.log('📡 Realtime event received:', payload);
      console.log('Event type:', payload.eventType);
      console.log('Table:', payload.table);
      console.log('New data:', payload.new);
      console.log('Old data:', payload.old);
    }
  )
  .subscribe((status, err) => {
    console.log('🔌 Subscription status:', status);
    if (err) {
      console.error('❌ Subscription error:', err);
    }
  });

// Test subscription after 5 seconds
setTimeout(() => {
  console.log('📊 Subscription state:', debugSubscription);
}, 5000);
```

#### Backend Real-time Issues
```python
# Test backend real-time integration
from apps.backend.services.realtime_integration import get_realtime_integration_service
import asyncio

async def test_realtime():
    service = get_realtime_integration_service()

    # Check service status
    status = await service.get_status()
    print(f"Real-time service status: {status}")

    # Start service if not running
    if not status.get('running'):
        await service.start()
        print("Started real-time service")

    # Check subscriptions
    print(f"Active subscriptions: {status.get('active_subscriptions', [])}")

asyncio.run(test_realtime())
```

## Performance Troubleshooting

### Slow Query Diagnosis

#### Identify Slow Queries
```sql
-- Enable query statistics (run once)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find slow queries
SELECT
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
WHERE query LIKE '%agent_%'
ORDER BY mean_exec_time DESC
LIMIT 10;
```

#### Optimize Query Performance
```typescript
// ❌ Slow: Unfiltered queries
const allData = await supabase
  .from('agent_executions')
  .select('*');

// ✅ Fast: Filtered and limited
const recentData = await supabase
  .from('agent_executions')
  .select('task_id, status, created_at')
  .gte('created_at', yesterday)
  .order('created_at', { ascending: false })
  .limit(50);
```

### Memory Usage Issues

#### Monitor Memory Usage
```python
# Backend memory monitoring
import psutil
import asyncio
from apps.backend.services.supabase_service import get_supabase_service

async def monitor_memory():
    process = psutil.Process()
    print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB")

    # Test memory usage with Supabase operations
    service = get_supabase_service()
    if service.is_available():
        for i in range(100):
            await service.health_check()
            if i % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                print(f"After {i} operations: {current_memory:.1f} MB")

asyncio.run(monitor_memory())
```

#### Frontend Memory Monitoring
```typescript
// Monitor frontend memory usage
const monitorMemory = () => {
  if ('memory' in performance) {
    const memory = (performance as any).memory;
    console.log('Memory usage:', {
      used: `${(memory.usedJSHeapSize / 1024 / 1024).toFixed(1)} MB`,
      total: `${(memory.totalJSHeapSize / 1024 / 1024).toFixed(1)} MB`,
      limit: `${(memory.jsHeapSizeLimit / 1024 / 1024).toFixed(1)} MB`
    });
  }
};

// Monitor memory every 30 seconds
setInterval(monitorMemory, 30000);
```

## Error Code Reference

### Supabase Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| `PGRST116` | Table not found | Run migrations |
| `PGRST301` | RLS policy violation | Check authentication |
| `42P01` | Relation does not exist | Create missing table |
| `42501` | Insufficient privilege | Check service role permissions |
| `08006` | Connection failure | Check network/credentials |

### Application Error Codes

| Error | Cause | Solution |
|-------|-------|---------|
| `SupabaseUnavailable` | Service not configured | Set environment variables |
| `ConnectionTimeout` | Network issues | Check connectivity |
| `LangChainCompatibilityError` | LCEL issues | Use compatibility layer |
| `AgentInitializationError` | Agent startup failure | Check dependencies |

## Debugging Tools

### Backend Debugging

#### Enable Debug Logging
```bash
# Set debug environment
export DEBUG=true
export LOG_LEVEL=DEBUG
export SUPABASE_DEBUG=true

# Run with debug logging
python apps/backend/main.py
```

#### Database Query Logging
```python
# Enable SQLAlchemy query logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Enable Supabase client logging
import os
os.environ['SUPABASE_DEBUG'] = 'true'
```

### Frontend Debugging

#### Enable Debug Mode
```bash
# Frontend debug environment
export VITE_DEBUG=true
export VITE_SUPABASE_DEBUG=true
export VITE_LOG_LEVEL=debug

# Start with debug logging
cd apps/dashboard && npm run dev
```

#### Browser Console Debugging
```typescript
// Enable debug logging in browser
localStorage.setItem('supabase.debug', 'true');

// Monitor Supabase operations
window.supabase = supabase;  // Make available in console

// Test operations in console
await window.supabase.from('agent_instances').select('count');
```

## Recovery Procedures

### Service Recovery

#### Restart Services
```bash
# Restart specific services
docker-compose restart backend dashboard

# Restart Supabase stack
docker-compose restart supabase-db supabase-kong supabase-auth

# Full system restart
docker-compose down && docker-compose up -d
```

#### Clear Caches
```bash
# Clear Redis cache
redis-cli FLUSHALL

# Clear browser cache
# In browser: DevTools → Application → Storage → Clear storage
```

### Data Recovery

#### Restore from Backup
```bash
# Restore Supabase data from backup
psql \
  --host=db.your-project.supabase.co \
  --port=5432 \
  --username=postgres \
  --dbname=postgres \
  --file=backup.sql
```

#### Rebuild Agent State
```python
# Rebuild agent state from execution history
from apps.backend.services.agent_service import AgentService
from apps.backend.services.supabase_service import get_supabase_service
import asyncio

async def rebuild_agent_state():
    agent_service = AgentService()
    supabase_service = get_supabase_service()

    if not supabase_service.is_available():
        print("❌ Supabase not available")
        return

    # Get all agent executions
    for agent_id in agent_service.agents.keys():
        executions = await supabase_service.get_agent_task_history(agent_id)

        # Rebuild metrics from execution history
        total_completed = len([e for e in executions if e['status'] == 'completed'])
        total_failed = len([e for e in executions if e['status'] == 'failed'])

        # Update agent instance
        await supabase_service.update_agent_instance(agent_id, {
            'total_tasks_completed': total_completed,
            'total_tasks_failed': total_failed
        })

        print(f"Rebuilt state for {agent_id}: {total_completed} completed, {total_failed} failed")

asyncio.run(rebuild_agent_state())
```

## Contact and Support

### Internal Support
- **Documentation**: [docs/](../README.md)
- **Health Status**: http://localhost:8009/api/v1/health
- **Logs**: `logs/` directory or `docker-compose logs`

### External Support
- **Supabase Support**: [supabase.com/support](https://supabase.com/support)
- **LangChain Documentation**: [python.langchain.com](https://python.langchain.com)
- **React 19 Documentation**: [react.dev](https://react.dev)

### Emergency Procedures

#### Critical System Failure
1. **Check Health Endpoints**: Identify failed components
2. **Review Logs**: Check recent error messages
3. **Restart Services**: Use Docker restart procedures
4. **Verify Configuration**: Check environment variables
5. **Contact Support**: If issues persist

#### Data Loss Recovery
1. **Stop Write Operations**: Prevent further data corruption
2. **Assess Damage**: Check data integrity
3. **Restore from Backup**: Use latest known good backup
4. **Verify Recovery**: Run comprehensive health checks
5. **Resume Operations**: Gradually restore service

---

**Last Updated**: 2025-09-21
**Version**: 1.0.0
**Status**: Complete
