# AI Agent Swarm Integration System

## Overview

The AI Agent Swarm is a sophisticated multi-agent system designed to provide seamless integration between Backend, Frontend/Dashboard, and Roblox/Studio components of the ToolboxAI platform. The swarm architecture enables autonomous agents to collaborate, communicate, and coordinate complex workflows across different platform layers.

## Architecture

### Core Components

#### 1. Integration Agents

**Backend Agents:**
- **APIGatewayAgent** - Manages API endpoints, versioning, and OpenAPI documentation
- **DatabaseSyncAgent** - Synchronizes data between PostgreSQL and Redis with multiple caching strategies

**Frontend Agents:**
- **UISyncAgent** - Real-time UI state synchronization across components
- **RealtimeUpdateAgent** - Pusher channel management with WebSocket fallback

**Roblox Agents:**
- **StudioBridgeAgent** - Communicates with Roblox Studio via HTTP plugin

**Orchestration:**
- **IntegrationCoordinator** - Manages multi-platform workflows and task dependencies

**Data Flow:**
- **SchemaValidatorAgent** - Cross-platform schema validation and data transformation

#### 2. Base Infrastructure

**BaseIntegrationAgent** provides:
- Circuit breaker pattern for fault tolerance
- Exponential backoff retry logic
- Event-driven architecture
- Metrics collection and monitoring
- Platform connection management

#### 3. Integration Manager

Central service (`IntegrationAgentsManager`) that:
- Initializes and manages all agents
- Connects agents to platform services
- Provides workflow execution
- Monitors agent health
- Handles graceful shutdown

## API Endpoints

The integration system exposes REST API endpoints under `/api/v1/integration`:

### Status & Monitoring
- `GET /integration/status` - Get agent health status
- `GET /integration/agents` - List available agents
- `GET /integration/metrics` - Detailed performance metrics
- `POST /integration/health/check` - Perform deep health check

### Workflow Management
- `POST /integration/workflow/create` - Create and execute workflows
- `POST /integration/workflow/templates` - List workflow templates

### Data Operations
- `POST /integration/schema/register` - Register cross-platform schemas
- `POST /integration/sync/trigger` - Trigger data synchronization
- `POST /integration/event/broadcast` - Broadcast events via Pusher

### Maintenance
- `POST /integration/maintenance/cleanup` - Cleanup operations (admin only)

## Usage Examples

### 1. Check System Status

```bash
curl -X GET http://localhost:8009/api/v1/integration/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
{
  "initialized": true,
  "timestamp": "2025-09-16T20:00:00Z",
  "agents": {
    "api_gateway": {"status": "healthy"},
    "database_sync": {"status": "healthy"},
    "ui_sync": {"status": "healthy"},
    "realtime_update": {"status": "healthy"},
    "studio_bridge": {"status": "healthy"},
    "schema_validator": {"status": "healthy"}
  },
  "overall_health": "healthy"
}
```

### 2. Execute a Workflow

```bash
curl -X POST http://localhost:8009/api/v1/integration/workflow/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "content_generation",
    "description": "Generate and sync educational content",
    "parameters": {
      "topic": "Python Basics",
      "grade_level": 9
    }
  }'
```

### 3. Register a Schema

```bash
curl -X POST http://localhost:8009/api/v1/integration/schema/register \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "schema_name": "lesson_content",
    "schema_type": "json_schema",
    "platform": "backend",
    "version": "1.0.0",
    "definition": {
      "type": "object",
      "properties": {
        "lesson_id": {"type": "string"},
        "title": {"type": "string"},
        "content": {"type": "string"}
      },
      "required": ["lesson_id", "title"]
    }
  }'
```

### 4. Trigger Data Sync

```bash
curl -X POST http://localhost:8009/api/v1/integration/sync/trigger \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_platform": "backend",
    "target_platform": "frontend",
    "data": {
      "user_id": "123",
      "preferences": {"theme": "dark"}
    }
  }'
```

## Workflow Templates

### Content Generation Workflow
```json
{
  "name": "content_generation",
  "tasks": [
    "validate_input",
    "generate_content",
    "store_in_database",
    "update_frontend",
    "sync_to_roblox"
  ]
}
```

### User Synchronization Workflow
```json
{
  "name": "user_sync",
  "tasks": [
    "fetch_user_data",
    "validate_data",
    "update_database",
    "broadcast_update"
  ]
}
```

### Roblox Deployment Workflow
```json
{
  "name": "roblox_deployment",
  "tasks": [
    "prepare_scripts",
    "validate_scripts",
    "deploy_to_studio",
    "verify_deployment"
  ]
}
```

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://eduplatform:eduplatform2024@localhost/educational_platform_dev

# Redis
REDIS_URL=redis://localhost:6379

# Pusher (for realtime features)
PUSHER_APP_ID=your-app-id
PUSHER_KEY=your-key
PUSHER_SECRET=your-secret
PUSHER_CLUSTER=your-cluster

# Optional: Skip integration agents (for testing)
SKIP_INTEGRATION_AGENTS=false
```

### Service Initialization

The integration agents are automatically initialized during backend startup:

```python
# In apps/backend/main.py lifespan function
if not os.getenv("SKIP_INTEGRATION_AGENTS", "false").lower() == "true":
    from apps.backend.services.integration_agents import integration_manager
    await integration_manager.initialize()
```

## Agent Capabilities

### API Gateway Agent
- Dynamic endpoint creation
- API versioning (v1, v2, v3)
- Rate limiting per endpoint
- OpenAPI/Swagger generation
- Deprecation management
- Request/response transformation

### Database Sync Agent
- PostgreSQL ↔ Redis synchronization
- Multiple sync strategies:
  - Write-through caching
  - Write-behind caching
  - Lazy loading
  - Cache invalidation
- Conflict resolution
- Transaction support

### UI Sync Agent
- Component state management
- Real-time updates
- Optimistic UI updates with rollback
- Partial update strategies
- State reconciliation

### Realtime Update Agent
- Pusher channel management
- WebSocket fallback
- Message queuing
- Delivery guarantees
- Presence tracking

### Studio Bridge Agent
- HTTP communication with Roblox Studio
- Script synchronization
- Asset management
- Debug message routing
- Version control

### Schema Validator Agent
- JSON Schema validation
- Protobuf support
- Avro support
- Cross-platform transformation
- Version migration
- Compatibility checking

## Circuit Breaker Pattern

All agents implement circuit breaker for fault tolerance:

```python
# Circuit breaker states
CLOSED   # Normal operation
OPEN     # Failing, reject requests
HALF_OPEN # Testing recovery

# Configuration
failure_threshold: 5      # Failures before opening
recovery_timeout: 60s     # Time before retry
half_open_requests: 3     # Test requests in half-open
```

## Monitoring & Health

### Health Check Levels

1. **Basic Health** - Agent status check
2. **Deep Health** - Include external service checks
3. **Metrics** - Performance and throughput data

### Key Metrics

- Total requests per agent
- Success/failure rates
- Average latency
- Events processed
- Circuit breaker states
- Cache hit/miss ratios

## Testing

### Unit Tests
```bash
pytest tests/unit/core/agents/integration/
```

### Integration Tests
```bash
pytest tests/integration/test_integration_agents_startup.py
```

### Manual Testing
```bash
# Start backend with agents
uvicorn apps.backend.main:app --reload

# Check status
curl http://localhost:8008/api/v1/integration/status

# View interactive docs
open http://localhost:8008/docs#/integration
```

## Troubleshooting

### Agents Not Initializing

Check environment variables:
```bash
echo $SKIP_INTEGRATION_AGENTS  # Should be empty or "false"
```

Check service connections:
```bash
# PostgreSQL
psql $DATABASE_URL -c "SELECT 1"

# Redis
redis-cli ping

# Pusher
curl https://api.pusherapp.com/apps/YOUR_APP_ID
```

### Circuit Breaker Open

Check metrics to identify failing service:
```bash
curl http://localhost:8008/api/v1/integration/metrics
```

Reset circuit breaker by fixing underlying issue and waiting for recovery timeout.

### Schema Validation Failures

Verify schema registration:
```bash
curl http://localhost:8008/api/v1/integration/agents | jq '.agents.schema_validator'
```

### Performance Issues

Monitor metrics:
- Check average latency per agent
- Identify slow endpoints
- Review circuit breaker states
- Analyze cache hit ratios

## Future Enhancements

1. **GraphQL Support** - Add GraphQL schema generation and federation
2. **Message Queue Integration** - RabbitMQ/Kafka for async processing
3. **Distributed Tracing** - OpenTelemetry integration
4. **Auto-scaling** - Dynamic agent pool sizing
5. **Machine Learning** - Predictive caching and load balancing
6. **Multi-tenancy** - Isolated agent pools per tenant
7. **Event Sourcing** - Complete audit trail of all operations
8. **Workflow Designer** - Visual workflow creation interface

## Development Guidelines

### Adding New Agents

1. Extend `BaseIntegrationAgent`
2. Implement `_process_integration_event`
3. Override `execute_task` for specific tasks
4. Register in `IntegrationAgentsManager`
5. Add API endpoints if needed
6. Write tests

### Creating Workflows

1. Define workflow template
2. Specify task dependencies
3. Implement task handlers in agents
4. Register with coordinator
5. Test end-to-end flow

### Best Practices

- Always use circuit breakers for external calls
- Implement proper retry logic with backoff
- Validate schemas at boundaries
- Monitor metrics and set alerts
- Document workflows and dependencies
- Write comprehensive tests
- Handle graceful degradation

## Conclusion

The AI Agent Swarm provides a robust, scalable integration layer for the ToolboxAI platform. By leveraging autonomous agents with specialized capabilities, the system ensures reliable cross-platform communication while maintaining fault tolerance and performance.
