# ToolBoxAI Docker Quick Reference

## 🚀 Quick Start
```bash
./infrastructure/docker/start-docker-dev.sh
```

## 📋 Service URLs
- Dashboard: http://localhost:5179
- Backend API: http://localhost:8009
- API Docs: http://localhost:8009/docs
- MCP Server: http://localhost:9877
- Agent Coordinator: http://localhost:8888
- Flask Bridge: http://localhost:5001
- Ghost CMS: http://localhost:8000

## 🗄️ Database Connections
- PostgreSQL: `localhost:5434` (eduplatform/password from .env)
- Redis: `localhost:6381`

## ⚡ Common Commands
```bash
# Check setup
./infrastructure/docker/check-setup.sh

# Start all services
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d

# Stop all services
docker-compose -f infrastructure/docker/docker-compose.dev.yml down

# View logs (all)
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f

# View logs (specific service)
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f dashboard-frontend
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f fastapi-main

# Restart service
docker-compose -f infrastructure/docker/docker-compose.dev.yml restart fastapi-main

# Check service status
docker-compose -f infrastructure/docker/docker-compose.dev.yml ps

# Rebuild service
docker-compose -f infrastructure/docker/docker-compose.dev.yml build dashboard-frontend
```

## 🔧 Required Environment Variables
```bash
POSTGRES_PASSWORD=your_password
JWT_SECRET_KEY=your_jwt_secret
PUSHER_APP_ID=your_pusher_app_id
PUSHER_KEY=your_pusher_key
PUSHER_SECRET=your_pusher_secret
```

## 🏥 Health Checks
```bash
curl http://localhost:8009/health        # Backend
curl http://localhost:5179/              # Dashboard
curl http://localhost:9877/health        # MCP Server
curl http://localhost:8888/health        # Agent Coordinator
```

## 🆘 Troubleshooting
```bash
# Port conflicts
lsof -i :8009

# Docker not running
# Start Docker Desktop first

# Reset everything
docker-compose -f infrastructure/docker/docker-compose.dev.yml down --volumes --remove-orphans
```
