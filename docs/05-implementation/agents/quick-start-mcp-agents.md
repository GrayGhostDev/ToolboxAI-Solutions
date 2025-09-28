# Quick Start: MCP-Agent Docker Integration

## Overview

This guide helps you quickly deploy the MCP-Agent integrated platform in Docker or Kubernetes environments.

## Prerequisites

- Docker and Docker Compose
- Kubernetes cluster (for K8s deployment)
- OpenAI API key
- GitHub token (for GitHub agents)

## Docker Compose Deployment (Recommended for Development)

### 1. Set Environment Variables

Create `.env` file in project root:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key
POSTGRES_PASSWORD=secure_postgres_password
REDIS_PASSWORD=secure_redis_password
JWT_SECRET_KEY=your_jwt_secret_key

# Optional
GITHUB_TOKEN=your_github_token
SENTRY_DSN=your_sentry_dsn
LOG_LEVEL=info
```

### 2. Deploy with Docker Compose

```bash
# Start the complete stack
docker-compose -f infrastructure/docker/docker-compose.prod.yml up -d

# Check status
docker-compose -f infrastructure/docker/docker-compose.prod.yml ps

# View logs
docker-compose -f infrastructure/docker/docker-compose.prod.yml logs -f mcp-server
```

### 3. Verify Deployment

```bash
# Check MCP server health
curl http://localhost:9876/health

# Check agent coordinator
curl http://localhost:8888/health

# Check educational agents
curl http://localhost:8080/health  # Port forward if needed
```

## Kubernetes Deployment (Production)

### 1. Prerequisites Setup

```bash
# Install required tools
kubectl version --client
docker version
helm version  # Optional

# Verify cluster access
kubectl cluster-info
```

### 2. Configure Secrets

```bash
# Set environment variables
export OPENAI_API_KEY="your_openai_api_key"
export GITHUB_TOKEN="your_github_token"
export GITHUB_USERNAME="your_github_username"
export POSTGRES_PASSWORD="secure_password"
export REDIS_PASSWORD="secure_password"
export JWT_SECRET_KEY="your_jwt_secret"
```

### 3. Deploy Using Script

```bash
# Make script executable
chmod +x scripts/deploy-mcp-agents.sh

# Full deployment
./scripts/deploy-mcp-agents.sh deploy

# Or step by step
./scripts/deploy-mcp-agents.sh build    # Build images
./scripts/deploy-mcp-agents.sh push     # Push to registry
./scripts/deploy-mcp-agents.sh deploy   # Deploy to K8s
```

### 4. Monitor Deployment

```bash
# Check pod status
kubectl get pods -n mcp-platform -w

# Check services
kubectl get services -n mcp-platform

# View logs
kubectl logs -n mcp-platform -l app=mcp-server -f
```

## Access Points

After successful deployment:

### Docker Compose
- **MCP Server**: `ws://localhost:9876`
- **Agent Coordinator**: `http://localhost:8888`
- **Prometheus**: `http://localhost:9090`
- **Grafana**: `http://localhost:3001`

### Kubernetes
- **MCP Server**: Port-forward with `kubectl port-forward -n mcp-platform service/mcp-server 9876:9876`
- **Agent Coordinator**: Port-forward with `kubectl port-forward -n mcp-platform service/agent-coordinator 8888:8888`
- **Educational Agents**: Port-forward with `kubectl port-forward -n mcp-platform service/educational-agents 8080:8080`

## Testing the Platform

### 1. Basic Health Checks

```bash
# Docker Compose
curl http://localhost:9876/health
curl http://localhost:8888/health

# Kubernetes (after port-forwarding)
curl http://localhost:9876/health
curl http://localhost:8888/health
```

### 2. Agent Pool Status

```bash
# Check educational agents status
curl http://localhost:8080/status

# Expected response:
{
  "pool_id": "educational-pool-12345",
  "pool_status": "running",
  "total_agents": 9,
  "agents": [...]
}
```

### 3. Submit Test Task

```python
import asyncio
import websockets
import json

async def test_mcp_connection():
    uri = "ws://localhost:9876"
    async with websockets.connect(uri) as websocket:
        # Send test message
        test_message = {
            "type": "task_request",
            "task_id": "test-001",
            "task_type": "content-generation",
            "payload": {
                "subject": "Math",
                "grade_level": 5,
                "topic": "Fractions"
            }
        }

        await websocket.send(json.dumps(test_message))
        response = await websocket.recv()
        print(f"Response: {response}")

# Run test
asyncio.run(test_mcp_connection())
```

## Troubleshooting

### Common Issues

1. **MCP Server Won't Start**
   ```bash
   # Check dependencies
   docker-compose logs postgres redis
   kubectl get pods -n default  # Check postgres/redis pods
   ```

2. **Agent Registration Fails**
   ```bash
   # Check Redis connectivity
   docker-compose exec redis redis-cli ping
   kubectl exec -it redis-pod -- redis-cli ping
   ```

3. **High Memory Usage**
   ```bash
   # Check resource usage
   docker stats
   kubectl top pods -n mcp-platform
   ```

4. **WebSocket Connection Issues**
   ```bash
   # Test WebSocket connectivity
   wscat -c ws://localhost:9876/health
   ```

### Getting Help

1. **View comprehensive logs**:
   ```bash
   # Docker Compose
   docker-compose logs --tail=100 -f

   # Kubernetes
   kubectl logs -n mcp-platform --all-containers=true --tail=100 -f
   ```

2. **Check resource usage**:
   ```bash
   # Docker Compose
   docker stats

   # Kubernetes
   kubectl top pods -n mcp-platform
   kubectl describe pod -n mcp-platform <pod-name>
   ```

3. **Verify configuration**:
   ```bash
   # Check environment variables
   docker-compose config

   # Check Kubernetes config
   kubectl get configmap -n mcp-platform -o yaml
   ```

## Development Workflow

### 1. Local Development

```bash
# Start only infrastructure
docker-compose up -d postgres redis

# Run agents locally for development
cd core/agents/educational
python -m agent_pool

# In another terminal
cd core/agents/github_agents
python -m agent_pool
```

### 2. Testing Changes

```bash
# Rebuild specific service
docker-compose build mcp-server

# Restart service
docker-compose restart mcp-server

# View logs
docker-compose logs -f mcp-server
```

### 3. Updating Configuration

```bash
# Update MCP configuration
vim config/mcp-servers.json

# Restart MCP server to pick up changes
docker-compose restart mcp-server
```

## Next Steps

1. **Configure monitoring**: Set up Prometheus and Grafana dashboards
2. **Enable Istio**: Deploy service mesh for advanced traffic management
3. **Scale agents**: Adjust replica counts based on load
4. **Add custom agents**: Implement domain-specific agent types

## Support

For issues or questions:
1. Check the comprehensive documentation: `docs/04-implementation/mcp-agent-docker-integration.md`
2. Review the troubleshooting guide in the full documentation
3. Check container logs for specific error messages
4. Verify all required environment variables are set