# Docker Services Startup Guide - Complete Instructions

## 🚀 Quick Start

### Option 1: Automated Startup (Recommended)
```bash
cd /Users/grayghostdataconsultants/GrayGhostDataConsultants/Development/ActiveProjects/Development/Cursor/Customers/ToolboxAI-Solutions

# Check if Docker is ready
./check-docker-ready.sh

# Start all services
./start-all-docker-services.sh
```

### Option 2: Manual Docker Commands
```bash
cd /Users/grayghostdataconsultants/GrayGhostDataConsultants/Development/ActiveProjects/Development/Cursor/Customers/ToolboxAI-Solutions

# Start all services with docker compose
docker compose -f docker-compose.complete.yml up -d

# View logs
docker compose -f docker-compose.complete.yml logs -f
```

## 📋 Services Included# Check specific service logs
docker compose -f docker-compose.complete.yml logs postgres
docker compose -f docker-compose.complete.yml logs redis
docker compose -f docker-compose.complete.yml logs backend
docker compose -f docker-compose.complete.yml logs dashboard
docker compose -f docker-compose.complete.yml logs mcp

# Check for port conflicts
lsof -i :5432 -i :6380 -i :8009 -i :5179 -i :8010

The `docker-compose.complete.yml` configuration starts the following services:

### Core Services
1. **PostgreSQL Database** (port 5432)
   - Container: `toolboxai-postgres`
   - User: eduplatform
   - Database: educational_platform_dev
   - Includes automatic migrations and extensions

2. **Redis Cache** (port 6380)
   - Container: `toolboxai-redis`
   - Used for session management and caching

### Application Services
3. **Backend API** (port 8009)
   - Container: `toolboxai-backend`
   - FastAPI application with auto-reload
   - Includes all integrations (Pusher, OpenAI, Roblox, etc.)
   - API Documentation: http://localhost:8009/docs
   - Health Check: http://localhost:8009/health

4. **Dashboard Frontend** (port 5179)
   - Container: `toolboxai-dashboard`
   - React + Vite application
   - Hot module reload enabled
   - Access: http://localhost:5179

5. **MCP Server** (port 8010)
   - Container: `toolboxai-mcp`
   - Model Context Protocol server for AI agent coordination

## 🔧 Troubleshooting

### Docker Not Running
If you see "Docker is not running" errors:

1. **Start Docker Desktop manually:**
   ```bash
   open -a Docker
   ```
   
2. **Wait for Docker to be ready** (30-60 seconds)
   - Look for the Docker icon in your macOS menu bar
   - It should show "Docker Desktop is running"

3. **Verify Docker is ready:**
   ```bash
   docker info
   docker ps
   ```

### Services Not Starting

If services fail to start:

1. **Check logs for specific service:**
   ```bash
   docker compose -f docker-compose.complete.yml logs backend
   docker compose -f docker-compose.complete.yml logs dashboard
   ```

2. **Restart specific service:**
   ```bash
   docker compose -f docker-compose.complete.yml restart backend
   ```

3. **Full restart with clean rebuild:**
   ```bash
   docker compose -f docker-compose.complete.yml down -v
   docker compose -f docker-compose.complete.yml build --no-cache
   docker compose -f docker-compose.complete.yml up -d
   ```

### Environment Variables

Ensure your `.env` file exists and contains required variables:
```bash
# Check if .env exists
ls -la .env

# Copy from example if needed
cp .env.example .env
```

Required environment variables:
- `JWT_SECRET_KEY`
- `PUSHER_APP_ID`, `PUSHER_KEY`, `PUSHER_SECRET`, `PUSHER_CLUSTER`
- `OPENAI_API_KEY` (optional but recommended)
- `CLERK_SECRET_KEY` (if using Clerk auth)

### Port Conflicts

If you get "port already in use" errors:

1. **Check what's using the ports:**
   ```bash
   lsof -i :5432  # PostgreSQL
   lsof -i :6380  # Redis
   lsof -i :8009  # Backend
   lsof -i :5179  # Dashboard
   lsof -i :8010  # MCP
   ```

2. **Stop conflicting services or change ports in docker-compose.complete.yml**

## 📊 Monitoring Services

### Check Service Status
```bash
docker compose -f docker-compose.complete.yml ps
```

### View Real-time Logs (All Services)
```bash
docker compose -f docker-compose.complete.yml logs -f
```

### View Logs for Specific Service
```bash
docker compose -f docker-compose.complete.yml logs -f backend
docker compose -f docker-compose.complete.yml logs -f dashboard
docker compose -f docker-compose.complete.yml logs -f postgres
```

### Check Service Health
```bash
# Backend health check
curl http://localhost:8009/health

# Dashboard accessibility
curl http://localhost:5179

# PostgreSQL connection
docker exec toolboxai-postgres pg_isready -U eduplatform

# Redis connection
docker exec toolboxai-redis redis-cli ping
```

## 🛑 Stopping Services

### Stop All Services (Keep Data)
```bash
docker compose -f docker-compose.complete.yml stop
```

### Stop and Remove Containers (Keep Data)
```bash
docker compose -f docker-compose.complete.yml down
```

### Stop and Remove Everything (Including Data)
```bash
docker compose -f docker-compose.complete.yml down -v
```

## 🔄 Restarting Services

### Restart All Services
```bash
docker compose -f docker-compose.complete.yml restart
```

### Restart Specific Service
```bash
docker compose -f docker-compose.complete.yml restart backend
docker compose -f docker-compose.complete.yml restart dashboard
```

## 🌐 Access Points

Once all services are running:

| Service | URL | Description |
|---------|-----|-------------|
| Dashboard | http://localhost:5179 | Main application UI |
| Backend API | http://localhost:8009 | REST API endpoints |
| API Docs | http://localhost:8009/docs | Swagger UI documentation |
| API Redoc | http://localhost:8009/redoc | Alternative API docs |
| Health Check | http://localhost:8009/health | Service health status |
| PostgreSQL | localhost:5432 | Database connection |
| Redis | localhost:6380 | Cache/session store |
| MCP Server | localhost:8010 | AI agent coordination |

## 🐛 Common Issues

### Issue: "Cannot connect to the Docker daemon"
**Solution:** Start Docker Desktop: `open -a Docker`

### Issue: Backend shows "Database not ready"
**Solution:** Wait 10-15 seconds for PostgreSQL to fully initialize, then restart backend:
```bash
docker compose -f docker-compose.complete.yml restart backend
```

### Issue: Dashboard shows blank page
**Solution:** Vite dev server takes 20-30 seconds to start. Check logs:
```bash
docker compose -f docker-compose.complete.yml logs -f dashboard
```

### Issue: "Network toolboxai-network not found"
**Solution:** Create the network manually:
```bash
docker network create toolboxai-network
docker compose -f docker-compose.complete.yml up -d
```

### Issue: Build fails with "no space left on device"
**Solution:** Clean up Docker resources:
```bash
docker system prune -a
docker volume prune
```

## 📝 Development Workflow

1. **Start services in the morning:**
   ```bash
   ./start-all-docker-services.sh
   ```

2. **Make code changes** - Changes auto-reload in dev mode

3. **View logs when debugging:**
   ```bash
   docker compose -f docker-compose.complete.yml logs -f backend
   ```

4. **Stop services when done:**
   ```bash
   docker compose -f docker-compose.complete.yml stop
   ```

## 🔐 Security Notes

- Default credentials are for development only
- PostgreSQL password: `eduplatform2024` (change in production)
- Ensure `.env` contains production secrets for production deployments
- Never commit `.env` file to version control

## 📚 Additional Resources

- Docker Compose Documentation: https://docs.docker.com/compose/
- ToolBoxAI Backend API: http://localhost:8009/docs
- Project README: See README.md in project root

