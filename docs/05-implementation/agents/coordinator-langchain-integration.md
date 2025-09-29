# Agent Coordinator LangChain Integration - Complete Implementation Guide

**Last Updated:** September 28, 2025
**Status:** ✅ Fully Implemented
**Version:** 2.0.0

## 🎯 Overview

This document describes the complete Agent Coordinator system integration with LangChain/LangGraph for the ToolBoxAI platform. The system provides full observability through LangSmith, real-time updates via Pusher, and orchestrates multiple AI agents for educational content generation.

## 🏗️ Architecture

### System Components

```mermaid
graph TD
    A[FastAPI Backend] --> B[Coordinator Service]
    B --> C[Main Coordinator]
    C --> D[Workflow Coordinator]
    C --> E[Resource Coordinator]
    C --> F[Sync Coordinator]
    C --> G[Error Coordinator]

    B --> H[LangChain Tracer]
    H --> I[LangSmith Dashboard]

    B --> J[Pusher Service]
    J --> K[Real-time Events]

    C --> L[Redis Cache]
    L --> M[Service Discovery]

    C --> N[Agent System]
    N --> O[Content Agent]
    N --> P[Quiz Agent]
    N --> Q[Script Agent]
    N --> R[Terrain Agent]
```

## 📋 Configuration

### Environment Variables

```bash
# LangChain Configuration (Set in .env file)
LANGCHAIN_API_KEY=your-langchain-api-key-here
LANGCHAIN_PROJECT_ID=your-project-id-here
LANGCHAIN_PROJECT=ToolboxAI-Solutions
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# Redis Configuration (Using running container)
REDIS_HOST=localhost
REDIS_PORT=55007
REDIS_URL=redis://localhost:55007/2  # Database 2 for coordinators

# Pusher Configuration (Real-time events)
PUSHER_APP_ID=${Your_Pusher_App_ID}
PUSHER_KEY=${Your_Pusher_Key}
PUSHER_SECRET=${Your_Pusher_Secret}
PUSHER_CLUSTER=us2
```

### Redis Database Allocation

| Database | Purpose | Service |
|----------|---------|---------|
| 0 | Backend/Celery | FastAPI, Celery Workers |
| 1 | MCP Server | Model Context Protocol |
| 2 | Coordinators | Agent Coordinators |
| 3 | LangGraph | LangGraph API (if used) |
| 4 | Sessions | User Sessions |
| 5 | Cache | General Cache |
| 6 | Pusher Queue | Event Queue |
| 7 | Metrics | Performance Metrics |

## 🚀 Implementation Details

### 1. Coordinator Service (`apps/backend/services/coordinator_service.py`)

The coordinator service is the main interface between FastAPI and the agent system:

```python
class CoordinatorService:
    """
    Manages all coordinator components with LangChain tracing.
    """

    def __init__(self):
        # Configure LangChain
        self._configure_langchain()

        # Initialize coordinators
        self.main_coordinator = MainCoordinator(...)

        # Setup tracing
        self.tracer = LangChainTracer(
            project_name="ToolboxAI-Coordinators",
            client=Client(api_key=LANGCHAIN_API_KEY)
        )
```

**Key Features:**
- Automatic LangChain configuration
- Redis-based service discovery
- Pusher integration for real-time events
- Health monitoring
- Graceful shutdown

### 2. Agent Configuration (`core/agents/config.py`)

Centralized configuration for all agents with LangChain integration:

```python
class LangChainConfiguration:
    """
    Manages LangChain/LangSmith configuration for all agents.
    """

    def __init__(self):
        self.api_key = os.getenv("LANGCHAIN_API_KEY")
        self.project_id = os.getenv("LANGCHAIN_PROJECT_ID")
        self.langsmith_client = Client(api_key=self.api_key)
```

**Agent Types Configured:**
- ContentAgent - Educational content generation
- QuizAgent - Assessment creation
- TerrainAgent - Roblox environment design
- ScriptAgent - Lua script generation
- ReviewAgent - Quality assurance
- TestingAgent - Validation and testing
- SupervisorAgent - Multi-agent coordination

### 3. API Endpoints (`apps/backend/routers/v1/coordinators.py`)

RESTful API for coordinator operations:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/coordinators/generate` | POST | Generate educational content |
| `/api/v1/coordinators/health` | GET | System health status |
| `/api/v1/coordinators/agents` | GET | List active agents |
| `/api/v1/coordinators/agents/{name}/execute` | POST | Execute specific agent task |
| `/api/v1/coordinators/workflows` | GET | Active workflows |
| `/api/v1/coordinators/workflows/{id}` | DELETE | Cancel workflow |

### 4. Docker Configuration

#### LangGraph Service (`infrastructure/docker/compose/langgraph-service.yml`)

```yaml
services:
  langgraph-api:
    image: langchain/langgraph-api:3.12-7cf63c6
    environment:
      DATABASE_URI: postgresql://toolboxai:devpass2024@postgres:5432/toolboxai
      REDIS_URL: redis://host.docker.internal:55007/3
      LANGCHAIN_API_KEY: ${LANGCHAIN_API_KEY}
      LANGCHAIN_PROJECT_ID: ${LANGCHAIN_PROJECT_ID}
      USE_PUSHER: true
      USE_WEBSOCKET: false
    ports:
      - "8123:8000"
```

## 📊 Monitoring & Observability

### LangSmith Dashboard

Access your project dashboard:
- **Project URL:** https://smith.langchain.com/project/{your-project-id}
- **Traces:** View all agent execution traces
- **Metrics:** Monitor token usage, latency, costs
- **Errors:** Debug failed operations

### Pusher Real-time Events

Event channels and types:

| Channel | Events | Description |
|---------|--------|-------------|
| `private-agent-orchestration` | `generation.started`, `generation.completed`, `generation.error` | Content generation lifecycle |
| `private-agent-{agent_id}` | `progress.update`, `agent.status` | Individual agent updates |
| `private-system` | `coordinator.initialized`, `coordinator.shutdown` | System events |

### Redis Monitoring

```bash
# Check coordinator registration
redis-cli -h localhost -p 55007 -n 2 hgetall "coordinators:registry"

# Monitor service health
redis-cli -h localhost -p 55007 -n 7 hgetall "services:registry"

# View agent progress
redis-cli -h localhost -p 55007 -n 2 keys "agent:progress:*"
```

## 🔧 Startup & Deployment

### Quick Start

1. **Start Redis Container**
```bash
docker start redis-toolboxai || docker run -d \
  --name redis-toolboxai \
  -p 55007:6379 \
  redis:latest
```

2. **Start LangGraph Services**
```bash
./scripts/start_langgraph_services.sh
```

3. **Start Backend with Coordinators**
```bash
cd apps/backend
uvicorn main:app --host 127.0.0.1 --port 8009 --reload
```

### Production Deployment

```bash
# Use Docker Compose
docker compose -f infrastructure/docker/compose/docker-compose.yml \
               -f infrastructure/docker/compose/docker-compose.dev.yml \
               up -d
```

## 🧪 Testing

### Integration Test
```python
# Run the integration test
python tests/integration/test_langchain_integration.py

# Or use the simple test
python test_langchain_simple.py
```

### Manual Testing
```bash
# Test coordinator health
curl http://localhost:8009/api/v1/coordinators/health

# Generate content
curl -X POST http://localhost:8009/api/v1/coordinators/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "subject": "Mathematics",
    "grade_level": 7,
    "learning_objectives": ["Understand fractions"],
    "environment_type": "interactive_classroom",
    "include_quiz": true
  }'
```

## 🔍 Troubleshooting

### Common Issues

1. **LangGraph Container Fails to Start**
   - Check DATABASE_URI is set correctly
   - Verify PostgreSQL is running
   - Check logs: `docker logs langgraph-api`

2. **Redis Connection Issues**
   - Ensure redis-toolboxai is running on port 55007
   - Test connection: `redis-cli -h localhost -p 55007 ping`

3. **LangChain Tracing Not Working**
   - Verify API key is correct
   - Check project ID matches your LangSmith project
   - Ensure LANGCHAIN_TRACING_V2=true

4. **Pusher Events Not Received**
   - Check Pusher credentials in .env
   - Verify channel authentication endpoint
   - Monitor Pusher debug console

### Debug Commands

```bash
# Check coordinator service logs
docker logs backend 2>&1 | grep -i coordinator

# Monitor Redis activity
redis-cli -h localhost -p 55007 monitor

# View LangGraph container status
docker inspect langgraph-api | jq '.State'

# Test LangSmith connectivity
python -c "import os; from langsmith import Client; c = Client(api_key=os.getenv('LANGCHAIN_API_KEY')); print('Connected!')"
```

## 📈 Performance Optimization

### Caching Strategy
- Redis cache for frequent requests (DB 5)
- 10-minute TTL for generated content
- Service discovery cache (60s TTL)

### Resource Management
- Max 10 concurrent coordinator requests
- Agent timeout: 300 seconds
- Health check interval: 30 seconds

### Monitoring Metrics
- Track in LangSmith dashboard
- Average generation time: < 30 seconds target
- Token usage optimization
- Error rate monitoring

## 🔐 Security Considerations

1. **API Keys**: Stored securely in .env, never committed
2. **Redis**: No password in dev, use AUTH in production
3. **Pusher**: Private channels with authentication
4. **LangChain**: Project-specific API keys with limited scope
5. **Docker**: Non-root users, read-only filesystems where possible

## 📝 Maintenance

### Regular Tasks
1. Monitor LangSmith for errors and performance
2. Clear Redis cache if needed: `redis-cli -n 5 FLUSHDB`
3. Update Docker images: `docker pull langchain/langgraph-api:latest`
4. Review agent logs for optimization opportunities

### Backup & Recovery
- Redis persistence: AOF enabled
- Database backups: Regular PostgreSQL dumps
- Configuration: Version controlled in Git

## 🚀 Future Enhancements

1. **Multi-tenant Support**: Agent isolation per tenant
2. **Advanced Workflows**: Complex multi-agent pipelines
3. **Cost Optimization**: Token usage reduction strategies
4. **Auto-scaling**: Dynamic agent pool management
5. **Enhanced Monitoring**: Custom metrics and alerting

## 📚 References

- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
- [LangSmith Guide](https://docs.smith.langchain.com/)
- [Pusher Channels Docs](https://pusher.com/docs/channels)
- [Redis Documentation](https://redis.io/documentation)
- [Docker Compose Reference](https://docs.docker.com/compose/)