# Supabase API Integration - ToolBoxAI Platform

## Overview

The ToolBoxAI platform integrates with Supabase to provide real-time database operations, agent system persistence, and enhanced data management capabilities. This document covers all Supabase-related API endpoints and integration patterns.

## Base Configuration

### Environment Variables
```bash
# Backend
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Frontend
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
```

### Authentication
- **Backend**: Uses Service Role Key for full database access
- **Frontend**: Uses Anon Key with Row Level Security (RLS) restrictions
- **Security**: All operations respect RLS policies and JWT authentication

## Agent System API

### Agent Instance Management

#### Create Agent Instance
```typescript
POST /api/v1/supabase/agents/instances
```

**Request Body:**
```json
{
  "agent_id": "agent_content_abc123",
  "agent_type": "content_generator",
  "configuration": {
    "model": "gpt-4",
    "temperature": 0.7
  },
  "resource_limits": {
    "max_memory_mb": 1024,
    "max_cpu_percent": 80
  }
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_id": "agent_content_abc123",
  "agent_type": "content_generator",
  "status": "initializing",
  "created_at": "2025-09-21T17:15:00Z",
  "updated_at": "2025-09-21T17:15:00Z"
}
```

#### Get Agent Instances
```typescript
GET /api/v1/supabase/agents/instances
GET /api/v1/supabase/agents/instances?agent_type=content_generator
GET /api/v1/supabase/agents/instances?status=idle
```

**Response:**
```json
{
  "agents": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "agent_id": "agent_content_abc123",
      "agent_type": "content_generator",
      "status": "idle",
      "configuration": {},
      "total_tasks_completed": 45,
      "total_tasks_failed": 2,
      "average_execution_time": 2.5,
      "last_activity": "2025-09-21T17:14:30Z",
      "created_at": "2025-09-21T17:00:00Z",
      "updated_at": "2025-09-21T17:14:30Z"
    }
  ],
  "count": 1,
  "timestamp": "2025-09-21T17:15:00Z"
}
```

### Task Execution Tracking

#### Create Task Execution
```typescript
POST /api/v1/supabase/agents/executions
```

**Request Body:**
```json
{
  "task_id": "task_xyz_789",
  "agent_instance_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_type": "content_generator",
  "task_type": "generate_content",
  "input_data": {
    "subject": "Mathematics",
    "grade_level": 5,
    "objectives": ["Understand fractions"]
  },
  "priority": "normal",
  "user_id": "user_123",
  "session_id": "session_456"
}
```

**Response:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "task_id": "task_xyz_789",
  "status": "pending",
  "created_at": "2025-09-21T17:15:00Z"
}
```

#### Update Task Execution
```typescript
PUT /api/v1/supabase/agents/executions/{task_id}
```

**Request Body:**
```json
{
  "status": "completed",
  "output_data": {
    "content": "Generated mathematics content...",
    "quality_score": 0.92
  },
  "execution_time_seconds": 2.5,
  "quality_score": 0.92,
  "completed_at": "2025-09-21T17:15:30Z"
}
```

#### Get Task History
```typescript
GET /api/v1/supabase/agents/executions
GET /api/v1/supabase/agents/executions?agent_id=agent_content_abc123
GET /api/v1/supabase/agents/executions?status=completed&limit=50
```

### Performance Metrics

#### Store Agent Metrics
```typescript
POST /api/v1/supabase/agents/metrics
```

**Request Body:**
```json
{
  "agent_instance_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_type": "content_generator",
  "period_start": "2025-09-21T16:00:00Z",
  "period_end": "2025-09-21T17:00:00Z",
  "period_duration_minutes": 60,
  "tasks_completed": 10,
  "tasks_failed": 1,
  "success_rate": 90.9,
  "average_execution_time": 2.5,
  "average_quality_score": 0.88
}
```

#### Get Agent Metrics
```typescript
GET /api/v1/supabase/agents/metrics
GET /api/v1/supabase/agents/metrics?agent_id=agent_content_abc123
GET /api/v1/supabase/agents/metrics?hours=24
```

**Response:**
```json
{
  "metrics": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440000",
      "agent_type": "content_generator",
      "period_start": "2025-09-21T16:00:00Z",
      "period_end": "2025-09-21T17:00:00Z",
      "tasks_completed": 10,
      "success_rate": 90.9,
      "average_execution_time": 2.5,
      "average_quality_score": 0.88,
      "created_at": "2025-09-21T17:00:00Z"
    }
  ],
  "summary": {
    "total_periods": 1,
    "avg_success_rate": 90.9,
    "avg_quality_score": 0.88
  }
}
```

## Real-time API

### Supabase Realtime Subscriptions

#### Subscribe to Agent Updates
```typescript
import { supabase } from '../lib/supabase';

// Subscribe to agent instance changes
const subscription = supabase
  .channel('agent-updates')
  .on('postgres_changes',
    {
      event: '*',
      schema: 'public',
      table: 'agent_instances'
    },
    (payload) => {
      console.log('Agent update:', payload);
      // Handle agent status changes
    }
  )
  .subscribe();
```

#### Subscribe to Task Execution Updates
```typescript
// Subscribe to task execution changes
const taskSubscription = supabase
  .channel('task-updates')
  .on('postgres_changes',
    {
      event: '*',
      schema: 'public',
      table: 'agent_executions'
    },
    (payload) => {
      console.log('Task update:', payload);
      // Handle task status changes
    }
  )
  .subscribe();
```

#### Subscribe to System Health Updates
```typescript
// Subscribe to system health changes
const healthSubscription = supabase
  .channel('health-updates')
  .on('postgres_changes',
    {
      event: 'INSERT',
      schema: 'public',
      table: 'system_health'
    },
    (payload) => {
      console.log('Health update:', payload);
      // Update system health dashboard
    }
  )
  .subscribe();
```

### Real-time Event Types

#### Agent Events
```json
{
  "eventType": "UPDATE",
  "new": {
    "agent_id": "agent_content_abc123",
    "status": "busy",
    "current_task_id": "task_xyz_789",
    "updated_at": "2025-09-21T17:15:00Z"
  },
  "old": {
    "status": "idle",
    "current_task_id": null
  }
}
```

#### Task Events
```json
{
  "eventType": "UPDATE",
  "new": {
    "task_id": "task_xyz_789",
    "status": "completed",
    "output_data": {"content": "..."},
    "quality_score": 0.92,
    "completed_at": "2025-09-21T17:15:30Z"
  },
  "old": {
    "status": "running",
    "output_data": null
  }
}
```

## Frontend Integration

### React 19 Hooks

#### useSupabaseAgent Hook
```typescript
import { useSupabaseAgent } from '../hooks/useSupabaseAgent';

const {
  agents,
  executions,
  metrics,
  loading,
  error,
  configured,
  actions
} = useSupabaseAgent({
  enableRealtime: true,
  refreshInterval: 30000,
  autoRefresh: true
});

// Access data
console.log('Agents:', agents);
console.log('Recent executions:', executions);

// Perform actions
await actions.fetchAgents();
await actions.refresh();
```

#### useSupabaseAgentById Hook
```typescript
const agentData = useSupabaseAgentById('agent_content_abc123', {
  enableRealtime: true
});

// Agent-specific data
console.log('Agent:', agentData.agent);
console.log('Agent executions:', agentData.executions);
console.log('Agent metrics:', agentData.metrics);
```

#### useSupabaseSystemHealth Hook
```typescript
const {
  systemHealth,
  healthSummary,
  loading,
  error,
  actions
} = useSupabaseSystemHealth({
  enableRealtime: true,
  refreshInterval: 30000
});
```

### Direct Supabase Operations

#### AgentSupabaseService
```typescript
import { AgentSupabaseService } from '../lib/supabase';

// Get all agents
const agents = await AgentSupabaseService.getAgentInstances();

// Get agent executions
const executions = await AgentSupabaseService.getAgentExecutions(
  'agent_content_abc123',
  100
);

// Get agent metrics
const metrics = await AgentSupabaseService.getAgentMetrics(
  'agent_content_abc123',
  24 // hours
);

// Get system health
const health = await AgentSupabaseService.getSystemHealth(24);

// Get health summary
const summary = await AgentSupabaseService.getAgentHealthSummary();
```

## Backend Integration

### Service Layer

#### SupabaseService
```python
from apps.backend.services.supabase_service import get_supabase_service

service = get_supabase_service()

# Agent operations
agent_data = await service.create_agent_instance({
    "agent_id": "agent_content_abc123",
    "agent_type": "content_generator",
    "status": "idle"
})

# Task operations
task_data = await service.create_task_execution({
    "task_id": "task_xyz_789",
    "agent_instance_id": agent_data["id"],
    "task_type": "generate_content"
})

# Metrics operations
await service.store_agent_metrics({
    "agent_instance_id": agent_data["id"],
    "tasks_completed": 10,
    "success_rate": 90.9
})
```

#### Real-time Integration Service
```python
from apps.backend.services.realtime_integration import get_realtime_integration_service

service = get_realtime_integration_service()

# Start real-time integration
await service.start()

# Add custom event handler
async def custom_handler(event):
    print(f"Custom event: {event.table} - {event.event_type}")

service.add_event_handler('agent_instances', custom_handler)

# Get service status
status = await service.get_status()
```

## Database Schema

### Table Definitions

#### agent_instances
```sql
CREATE TABLE agent_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id TEXT UNIQUE NOT NULL,
    agent_type agent_type NOT NULL,
    status agent_status NOT NULL DEFAULT 'initializing',
    configuration JSONB DEFAULT '{}',
    resource_limits JSONB DEFAULT '{}',
    performance_thresholds JSONB DEFAULT '{}',
    current_task_id TEXT,
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    total_tasks_completed INTEGER DEFAULT 0,
    total_tasks_failed INTEGER DEFAULT 0,
    total_execution_time FLOAT DEFAULT 0.0,
    average_execution_time FLOAT DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### agent_executions
```sql
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id TEXT UNIQUE NOT NULL,
    agent_instance_id UUID REFERENCES agent_instances(id),
    agent_type agent_type NOT NULL,
    task_type TEXT NOT NULL,
    priority task_priority DEFAULT 'normal',
    input_data JSONB NOT NULL DEFAULT '{}',
    output_data JSONB,
    context_data JSONB DEFAULT '{}',
    status task_status NOT NULL DEFAULT 'pending',
    error_message TEXT,
    error_details JSONB,
    execution_time_seconds FLOAT,
    quality_score FLOAT CHECK (quality_score >= 0 AND quality_score <= 1),
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    user_id UUID,
    session_id TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3
);
```

### Custom Functions

#### get_agent_health_summary()
```sql
SELECT * FROM get_agent_health_summary();
```

**Returns:**
```json
{
  "total_agents": 8,
  "healthy_agents": 7,
  "busy_agents": 3,
  "error_agents": 1,
  "success_rate": 95.5,
  "avg_response_time": 2.3
}
```

## Error Handling

### Error Responses

#### Service Unavailable
```json
{
  "error": "SupabaseUnavailable",
  "message": "Supabase is not available or configured",
  "timestamp": "2025-09-21T17:15:00Z",
  "fallback_action": "using_local_storage"
}
```

#### Connection Timeout
```json
{
  "error": "ConnectionTimeout",
  "message": "Supabase connection timed out after 30 seconds",
  "timestamp": "2025-09-21T17:15:00Z",
  "retry_in_seconds": 60
}
```

### Graceful Degradation

The system automatically falls back to local operations when Supabase is unavailable:

```python
# Automatic fallback pattern
if self.supabase_service and self.supabase_service.is_available():
    # Use Supabase for persistence
    await self.supabase_service.create_agent_instance(data)
else:
    # Continue with local storage
    logger.warning("Supabase unavailable, using local storage")
```

## Performance Optimization

### Query Optimization

#### Efficient Queries
```typescript
// Good: Use specific filters
const recentTasks = await supabase
  .from('agent_executions')
  .select('*')
  .eq('agent_type', 'content_generator')
  .gte('created_at', '2025-09-21T00:00:00Z')
  .order('created_at', { ascending: false })
  .limit(50);

// Good: Use pagination
const { data, count } = await supabase
  .from('agent_executions')
  .select('*', { count: 'exact' })
  .range(0, 49);
```

#### Index Usage
```sql
-- Optimized indexes for common queries
CREATE INDEX idx_agent_instances_type_status ON agent_instances(agent_type, status);
CREATE INDEX idx_agent_executions_agent_created ON agent_executions(agent_instance_id, created_at);
CREATE INDEX idx_agent_metrics_period ON agent_metrics(period_start, period_end);
```

### Connection Pooling

```python
# Backend connection configuration
SUPABASE_CONNECTION_TIMEOUT=30
SUPABASE_MAX_RETRIES=3
SUPABASE_RETRY_DELAY=5
```

```typescript
// Frontend connection configuration
const supabase = createClient(url, key, {
  realtime: {
    params: {
      eventsPerSecond: 10
    }
  },
  global: {
    headers: {
      'x-application-name': 'toolboxai-dashboard'
    }
  }
});
```

## Security

### Row Level Security (RLS)

#### Policies
```sql
-- Users can view their own agent executions
CREATE POLICY "Users can view own executions"
ON agent_executions FOR SELECT
USING (auth.uid() = user_id);

-- Service role can manage all data
CREATE POLICY "Service role full access"
ON agent_executions FOR ALL
USING (auth.role() = 'service_role');

-- Authenticated users can view agent instances
CREATE POLICY "Users can view agents"
ON agent_instances FOR SELECT
USING (auth.role() = 'authenticated');
```

### API Security

#### Authentication Headers
```typescript
// Frontend requests (automatic with Supabase client)
headers: {
  'Authorization': `Bearer ${anonKey}`,
  'apikey': anonKey
}

// Backend requests
headers: {
  'Authorization': `Bearer ${serviceRoleKey}`,
  'apikey': serviceRoleKey
}
```

## Monitoring and Observability

### Health Monitoring

#### Supabase Health Check
```http
GET /api/v1/health/supabase
```

**Response:**
```json
{
  "status": "healthy",
  "response_time_ms": 45.2,
  "tables_accessible": {
    "agent_instances": true,
    "agent_executions": true,
    "agent_metrics": true,
    "system_health": true
  },
  "realtime_enabled": true,
  "database_size_mb": 125.5,
  "errors": [],
  "timestamp": "2025-09-21T17:15:00Z"
}
```

### Performance Metrics

#### Response Times
- **Simple Queries**: <50ms
- **Complex Queries**: <200ms
- **Real-time Events**: <100ms
- **Health Checks**: <100ms

#### Throughput
- **Concurrent Connections**: 10-50
- **Queries per Second**: 100+
- **Real-time Events**: 1000+ per minute

## Best Practices

### Query Patterns

#### Efficient Data Fetching
```typescript
// ✅ Good: Specific columns
const agents = await supabase
  .from('agent_instances')
  .select('agent_id, agent_type, status, last_activity');

// ✅ Good: Filtered queries
const recentTasks = await supabase
  .from('agent_executions')
  .select('*')
  .gte('created_at', yesterday)
  .eq('status', 'completed');

// ❌ Avoid: Select all without filters
const allData = await supabase
  .from('agent_executions')
  .select('*'); // Can be very large
```

#### Real-time Subscriptions
```typescript
// ✅ Good: Specific table subscriptions
const subscription = supabase
  .channel('agent-updates')
  .on('postgres_changes', {
    event: 'UPDATE',
    schema: 'public',
    table: 'agent_instances',
    filter: 'status=eq.busy'
  }, callback)
  .subscribe();

// ✅ Good: Cleanup subscriptions
useEffect(() => {
  return () => {
    subscription.unsubscribe();
  };
}, []);
```

### Error Handling
```typescript
// ✅ Good: Comprehensive error handling
try {
  const { data, error } = await supabase
    .from('agent_instances')
    .select('*');

  if (error) {
    console.error('Supabase error:', error);
    // Handle specific error types
    if (error.code === 'PGRST116') {
      // Table not found
    }
    return [];
  }

  return data || [];
} catch (error) {
  console.error('Network error:', error);
  return [];
}
```

## Migration and Deployment

### Migration Scripts

#### Automated Migration
```bash
# Run Supabase migrations
python scripts/supabase_migration_automation.py

# Check migration status
python -c "
from apps.backend.services.migration_service import get_migration_service
import asyncio
service = get_migration_service()
status = asyncio.run(service.get_migration_status())
print(status)
"
```

#### Manual Migration
```sql
-- Example migration script
-- File: database/supabase/migrations/002_add_agent_configurations.sql

CREATE TABLE agent_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    agent_type agent_type NOT NULL,
    configuration JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE agent_configurations ENABLE ROW LEVEL SECURITY;

-- Create policy
CREATE POLICY "Service role can manage configs"
ON agent_configurations FOR ALL
USING (auth.role() = 'service_role');
```

### Deployment Configuration

#### Docker Environment
```yaml
# docker-compose.yml
services:
  backend:
    environment:
      SUPABASE_URL: ${SUPABASE_URL}
      SUPABASE_SERVICE_ROLE_KEY: ${SUPABASE_SERVICE_ROLE_KEY}

  dashboard:
    environment:
      VITE_SUPABASE_URL: ${SUPABASE_URL}
      VITE_SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY}
```

#### Production Configuration
```bash
# Production environment variables
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_production_service_key
SUPABASE_ENABLE_REALTIME=true
SUPABASE_ENABLE_RLS=true
```

## Troubleshooting

### Common Issues

#### Connection Issues
```bash
# Test Supabase connection
python -c "
from apps.backend.services.supabase_service import get_supabase_service
import asyncio
service = get_supabase_service()
print('Available:', service.is_available())
health = asyncio.run(service.health_check())
print('Health:', health)
"
```

#### Real-time Issues
```typescript
// Debug real-time subscriptions
const subscription = supabase
  .channel('debug-channel')
  .on('postgres_changes', { event: '*', schema: 'public', table: 'agent_instances' },
    (payload) => console.log('Event received:', payload)
  )
  .subscribe((status) => {
    console.log('Subscription status:', status);
  });
```

#### Performance Issues
```bash
# Check Supabase performance
curl -w "@curl-format.txt" \
  -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
  -H "apikey: $SUPABASE_ANON_KEY" \
  "$SUPABASE_URL/rest/v1/agent_instances?select=count"
```

## Conclusion

The Supabase API integration provides comprehensive database services, real-time capabilities, and enhanced monitoring for the ToolBoxAI platform. The integration maintains backward compatibility while adding powerful new features for agent system management and real-time collaboration.

---

**Last Updated**: 2025-09-21
**Version**: 1.0.0
**Status**: Production Ready
