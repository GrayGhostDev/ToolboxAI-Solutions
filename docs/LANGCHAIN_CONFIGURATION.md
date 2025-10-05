# LangChain Configuration & Setup Guide

**Last Updated:** September 28, 2025
**Status:** ✅ Fully Configured
**Version:** 1.0.0

## 🔑 Production Credentials

These credentials are currently active in the system:

```bash
# Set these in your .env file (values shown are placeholders)
LANGCHAIN_API_KEY=your-langchain-api-key-here
LANGCHAIN_PROJECT_ID=your-langchain-project-id-here
LANGCHAIN_PROJECT=ToolboxAI-Solutions
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

## 📊 LangSmith Dashboard Access

Monitor your agent operations in real-time:

- **Project Dashboard:** https://smith.langchain.com/project/{your-project-id}
- **View Traces:** https://smith.langchain.com/project/{your-project-id}/runs
- **Settings:** https://smith.langchain.com/project/{your-project-id}/settings

## 🚀 Quick Start

### 1. Verify Configuration

```bash
# Run the simple test to verify setup
python test_langchain_simple.py

# Expected output:
# ✅ LangChain configuration is properly set up!
# ✅ Your API key and project ID are configured correctly
# ✅ Tracing is enabled for all agent operations
```

### 2. Start Services

```bash
# Start the LangGraph services with proper configuration
./scripts/start_langgraph_services.sh

# This will:
# - Start Redis on port 55007
# - Configure LangChain environment variables
# - Start LangGraph API container on port 8123
# - Initialize coordinator services
```

### 3. Test Agent Execution

```python
# Simple test to generate a trace
from langchain.callbacks.tracers import LangChainTracer
from langchain_openai import ChatOpenAI

# Create tracer
tracer = LangChainTracer(project_name="ToolboxAI-Test")

# Create LLM with tracing
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    callbacks=[tracer]
)

# Execute and see trace in dashboard
response = llm.invoke("Hello, LangChain!")
print(f"Response: {response}")
print(f"View trace at: https://smith.langchain.com/project/{os.getenv('LANGCHAIN_PROJECT_ID')}")
```

## 📁 File Locations

### Environment Configuration
- **Main .env file:** `/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/.env`
  - Lines 182-186: LangChain configuration

### Implementation Files
- **Agent Config:** `core/agents/config.py`
- **Coordinator Service:** `apps/backend/services/coordinator_service.py`
- **API Router:** `apps/backend/routers/v1/coordinators.py`
- **Docker Config:** `infrastructure/docker/compose/langgraph-service.yml`
- **Startup Script:** `scripts/start_langgraph_services.sh`

### Test Files
- **Integration Test:** `tests/integration/test_langchain_integration.py`
- **Simple Test:** `test_langchain_simple.py`

## 🔧 Configuration Details

### Agent Types Configured

Each agent type has specific LangChain configuration:

| Agent Type | Model | Temperature | Purpose |
|------------|-------|-------------|---------|
| ContentAgent | gpt-4 | 0.7 | Educational content generation |
| QuizAgent | gpt-3.5-turbo | 0.5 | Assessment creation |
| TerrainAgent | gpt-3.5-turbo | 0.8 | Roblox environment design |
| ScriptAgent | gpt-4 | 0.3 | Lua script generation |
| ReviewAgent | gpt-4 | 0.2 | Quality assurance |
| TestingAgent | gpt-3.5-turbo | 0.1 | Validation and testing |
| SupervisorAgent | gpt-4 | 0.4 | Multi-agent coordination |
| Orchestrator | gpt-4 | 0.5 | System orchestration |

### Tracing Configuration

All agents automatically include LangChain tracing:

```python
from core.agents.config import langchain_config

# Get tracer for specific agent
tracer = langchain_config.get_tracer("content-agent")

# Get callbacks for LangChain operations
callbacks = langchain_config.get_callbacks("content-agent")

# Use in agent execution
result = await agent.execute(
    task="Generate content",
    callbacks=callbacks
)
```

## 📊 Monitoring & Observability

### What Gets Traced

Every agent operation is automatically traced with:
- **Input/Output**: Complete request and response
- **Token Usage**: Input tokens, output tokens, total cost
- **Latency**: Time for each step
- **Errors**: Full error traces with stack traces
- **Metadata**: Agent name, task type, user context

### Viewing Traces

1. Go to the [LangSmith dashboard](https://smith.langchain.com) and navigate to your project
2. Click on "Runs" to see all traces
3. Filter by:
   - Agent name
   - Time range
   - Success/failure
   - Token usage
   - Latency

### Cost Monitoring

Monitor LLM costs in real-time:
- View per-run costs
- Daily/weekly/monthly aggregates
- Cost breakdown by agent type
- Optimization opportunities

## 🐳 Docker Integration

### LangGraph Container

The LangGraph container is configured with LangChain credentials:

```yaml
# infrastructure/docker/compose/langgraph-service.yml
environment:
  LANGCHAIN_API_KEY: ${LANGCHAIN_API_KEY}  # Loaded from .env
  LANGCHAIN_PROJECT_ID: ${LANGCHAIN_PROJECT_ID}  # Loaded from .env
  LANGCHAIN_PROJECT: ToolboxAI-Solutions
  LANGCHAIN_TRACING_V2: true
```

### Starting the Container

```bash
# Using docker-compose
docker compose -f infrastructure/docker/compose/langgraph-service.yml up -d

# Or using the startup script
./scripts/start_langgraph_services.sh
```

## 🔍 Troubleshooting

### Common Issues

1. **"API key not found" error**
   - Ensure .env file has correct LANGCHAIN_API_KEY
   - Source the .env file: `source .env`

2. **Traces not appearing in dashboard**
   - Check LANGCHAIN_TRACING_V2=true
   - Verify project ID matches your LangSmith project
   - Check network connectivity to smith.langchain.com

3. **Import errors**
   - Use `langchain.callbacks.tracers.LangChainTracer`
   - Not `langchain_core.callbacks.LangChainTracer` (old import)

### Debug Commands

```bash
# Verify environment variables
env | grep LANGCHAIN

# Test API key validity
python -c "import os; from langsmith import Client; Client(api_key=os.getenv('LANGCHAIN_API_KEY')); print('Valid!')"

# Check if tracing is enabled
python -c "import os; print(f'Tracing: {os.getenv(\"LANGCHAIN_TRACING_V2\")}')"
```

## 🛡️ Security Best Practices

1. **Never commit API keys** - Always use .env files
2. **Use project-specific keys** - Don't share across projects
3. **Rotate keys regularly** - Update every 90 days
4. **Monitor usage** - Check for unusual activity in dashboard
5. **Set spending limits** - Configure alerts for cost overruns

## 📈 Performance Optimization

### Token Usage Optimization
- Use appropriate models for each task
- Implement caching for repeated queries
- Batch similar requests
- Use streaming for long responses

### Latency Optimization
- Use faster models for time-sensitive operations
- Implement timeouts for long-running tasks
- Cache frequently accessed data
- Use parallel execution where possible

## 🔄 Updating Configuration

To update LangChain credentials:

1. **Update .env file**:
   ```bash
   # Edit the .env file
   LANGCHAIN_API_KEY=new_key_here
   LANGCHAIN_PROJECT_ID=new_project_id_here
   ```

2. **Restart services**:
   ```bash
   # Restart backend
   docker restart toolboxai-backend

   # Restart LangGraph
   docker restart langgraph-api
   ```

3. **Verify update**:
   ```bash
   python test_langchain_simple.py
   ```

## 📚 Additional Resources

- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [LangGraph Concepts](https://langchain-ai.github.io/langgraph/concepts/)
- [MCP Integration Guide](https://langchain-ai.github.io/langgraph/agents/mcp/)
- [Pusher Real-time Events](docs/PUSHER_REALTIME.md)

## 🆘 Support

For issues with LangChain integration:

1. Check the [troubleshooting section](#-troubleshooting) above
2. Review traces in [LangSmith dashboard](https://smith.langchain.com)
3. Check container logs: `docker logs langgraph-api`
4. Review agent logs: `docker logs toolboxai-backend | grep -i langchain`

---

**Note:** This configuration is currently active in production. Any changes should be tested in development first.