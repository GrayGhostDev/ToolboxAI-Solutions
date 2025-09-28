# Docker Quick Start Guide
## ToolBoxAI Solutions - Consolidated Configuration

### 🚀 Quick Commands

#### Development Environment
```bash
# Start with hot reload and debugging
docker compose -f compose/docker-compose.yml -f compose/docker-compose.dev.yml up -d

# View logs
docker compose -f compose/docker-compose.yml -f compose/docker-compose.dev.yml logs -f

# Stop services
docker compose -f compose/docker-compose.yml -f compose/docker-compose.dev.yml down
```

#### Production Environment
```bash
# Start production stack
docker compose -f compose/docker-compose.yml -f compose/docker-compose.prod.yml up -d

# Scale backend
docker compose -f compose/docker-compose.yml -f compose/docker-compose.prod.yml up -d --scale backend=3

# View production logs
docker compose -f compose/docker-compose.yml -f compose/docker-compose.prod.yml logs -f backend
```

#### Base Environment (Testing/Staging)
```bash
# Start basic stack with monitoring
docker compose -f compose/docker-compose.yml up -d

# Health check
curl http://localhost:8009/health
```

### 📊 Service Ports

#### Development (Exposed)
- **Backend**: `8009` (FastAPI + Hot Reload)
- **Dashboard**: `5180` (React + Mantine v8)
- **MCP Server**: `9877` (Model Context Protocol Gateway)
- **Agent Coordinator**: `8888` (AI Agent Orchestration)
- **PostgreSQL**: `5432` (Primary Database)
- **Redis**: `6379` (Cache + Sessions)
- **Roblox Sync**: `34872` (Studio Integration)
- **Adminer**: `8080` (Database UI)
- **Redis Commander**: `8081` (Redis UI)
- **Mailhog**: `8025` (Email Testing)

#### Production (Internal Only)
- **Nginx**: `80`, `443` (Public Access)
- **Prometheus**: Internal monitoring network
- **Grafana**: Access via Nginx reverse proxy
- All other services: Internal networks only

### 🔧 Environment Variables

#### Required for Production
```env
# Database
POSTGRES_DB=toolboxai
POSTGRES_USER=toolboxai

# API Keys (via secrets)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...

# Security
JWT_SECRET_KEY=your-secret-key

# Performance
WORKERS=4
MAX_CONCURRENT_AGENTS=10
```

#### Development Overrides
```env
# Development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Simple passwords (dev only)
POSTGRES_PASSWORD=devpass2024
```

### 🔐 Secrets Management

#### Create Production Secrets
```bash
# Database password
echo "your-secure-db-password" | docker secret create db_password -

# Redis password
echo "your-secure-redis-password" | docker secret create redis_password -

# JWT secret
echo "your-jwt-secret" | docker secret create jwt_secret -

# API keys
echo "sk-your-openai-key" | docker secret create openai_api_key -
echo "sk-your-anthropic-key" | docker secret create anthropic_api_key -

# Grafana credentials (production)
echo "admin" | docker secret create grafana_user -
echo "secure-grafana-password" | docker secret create grafana_password -
```

### 🐛 Debugging

#### Backend Debugging
```bash
# Attach to backend container
docker compose -f compose/docker-compose.yml -f compose/docker-compose.dev.yml exec backend bash

# View backend logs with debug info
docker compose -f compose/docker-compose.yml -f compose/docker-compose.dev.yml logs -f backend

# Python debugger (if using debugpy)
# Connect IDE to localhost:5678
```

#### Database Access
```bash
# Connect to PostgreSQL (development)
docker compose -f compose/docker-compose.yml -f compose/docker-compose.dev.yml exec postgres psql -U toolboxai -d toolboxai

# Or use Adminer at http://localhost:8080
```

#### Redis Access
```bash
# Connect to Redis (development)
docker compose -f compose/docker-compose.yml -f compose/docker-compose.dev.yml exec redis redis-cli

# Or use Redis Commander at http://localhost:8081
```

### 📈 Monitoring Access

#### Development
- **Prometheus**: `http://localhost:9090` (if monitoring enabled)
- **Backend Metrics**: `http://localhost:8009/metrics`
- **Health Checks**: `http://localhost:8009/health`

#### Production
- **Grafana**: Access via Nginx reverse proxy
- **Prometheus**: Internal network only
- **Alerts**: Check Alertmanager

### 🔄 Common Operations

#### Build Specific Services
```bash
# Build only backend
docker compose -f compose/docker-compose.yml build backend

# Build with no cache
docker compose -f compose/docker-compose.yml build --no-cache backend
```

#### Scale Services
```bash
# Scale backend to 3 replicas
docker compose -f compose/docker-compose.yml -f compose/docker-compose.prod.yml up -d --scale backend=3

# Scale agents
docker compose -f compose/docker-compose.yml -f compose/docker-compose.prod.yml up -d --scale agent-coordinator=2
```

#### Update and Deploy
```bash
# Pull latest images
docker compose -f compose/docker-compose.yml -f compose/docker-compose.prod.yml pull

# Rolling update
docker compose -f compose/docker-compose.yml -f compose/docker-compose.prod.yml up -d --force-recreate --no-deps backend
```

### 🛠️ Troubleshooting

#### Common Issues
1. **Port conflicts**: Check if ports are already in use
2. **Secrets not found**: Ensure secrets are created before starting production
3. **Permission denied**: Check file permissions and user mappings
4. **Health check failures**: Check service logs and dependencies

#### Clean Reset
```bash
# Stop all services
docker compose -f compose/docker-compose.yml -f compose/docker-compose.dev.yml down -v

# Remove all containers and volumes
docker system prune -a --volumes

# Rebuild from scratch
docker compose -f compose/docker-compose.yml -f compose/docker-compose.dev.yml up --build
```

### 📁 File Structure Reference
```
infrastructure/docker/
├── compose/
│   ├── docker-compose.yml      # Base + monitoring
│   ├── docker-compose.dev.yml  # Development overrides
│   └── docker-compose.prod.yml # Production overrides
├── dockerfiles/
│   ├── base.Dockerfile         # Shared base
│   ├── backend.Dockerfile      # FastAPI (multi-stage)
│   ├── dashboard.Dockerfile    # React (multi-stage)
│   ├── agents.Dockerfile       # AI agents
│   ├── mcp.Dockerfile          # MCP server
│   └── dev.Dockerfile          # Development
└── config/
    ├── nginx/                  # Web server config
    ├── postgres/               # DB initialization
    └── prometheus/             # Monitoring config
```

---

**For more details, see CONSOLIDATION_SUMMARY.md**
