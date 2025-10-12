# ToolboxAI Services - Quick Start Guide (2025)

## Current Status: Services Not Running

If your local environment is idle, follow the steps below to spin up the entire ToolboxAI development stack with the latest 2025 tooling.

## Step 1: Start Docker Desktop

```bash
open -a Docker
```

Wait until the whale icon in the macOS menu bar stops animating. This usually takes 30–60 seconds.

## Step 2: Run the Environment Check (optional but recommended)

From the repository root:

```bash
./infrastructure/docker/check-setup.sh
```

This script verifies Docker availability, required compose files, Dockerfiles, and common port conflicts.

## Step 3: Start All ToolboxAI Services (Recommended Path)

```bash
cd /Users/grayghostdata/Desktop/Development/ToolboxAI-Solutions
./infrastructure/docker/start-docker-dev.sh
```

This orchestrated script validates prerequisites, builds images, and starts services in the correct sequence.

### Alternative: Manual Compose Command

```bash
cd /Users/grayghostdata/Desktop/Development/ToolboxAI-Solutions
COMPOSE="docker compose -f infrastructure/docker/compose/docker-compose.yml -f infrastructure/docker/compose/docker-compose.dev.yml"
$COMPOSE up -d
```

## Verify Services Are Running

```bash
docker compose -f infrastructure/docker/compose/docker-compose.yml -f infrastructure/docker/compose/docker-compose.dev.yml ps
```

You should see these services reporting `running` or `healthy`:

- ✅ `postgres` (PostgreSQL 16)
- ✅ `redis`
- ✅ `backend`
- ✅ `dashboard`
- ✅ `mcp-server`
- ✅ `agent-coordinator`
- ✅ `celery-worker`
- ✅ `celery-beat`
- ✅ `flower`
- ✅ `adminer`
- ✅ `redis-commander`
- ✅ `mailhog`

## Access Your Services

- **Dashboard (Vite dev server)**: http://localhost:5179
- **Backend API**: http://localhost:8009
- **API Documentation**: http://localhost:8009/docs
- **MCP Server**: http://localhost:9877
- **Agent Coordinator**: http://localhost:8888
- **Celery Flower**: http://localhost:5555
- **Adminer (Postgres UI)**: http://localhost:8082
- **Redis Commander**: http://localhost:8081
- **Mailhog**: http://localhost:8025

## Common Issues & Solutions

### "Cannot connect to Docker daemon"
Docker Desktop is not running. Start it with `open -a Docker` and retry.

### Port already in use (e.g., 5434)
```bash
lsof -i :5434
```
Stop the conflicting process or update the port mapping in the compose overrides.

### Service stuck in `starting`
```bash
docker compose -f infrastructure/docker/compose/docker-compose.yml -f infrastructure/docker/compose/docker-compose.dev.yml logs <service>
```
Look for stack traces or database connection issues.

### "No space left on device"
Clean up Docker resources:
```bash
docker system prune -a
docker volume prune
```

## Useful Commands

### View Logs
```bash
# All services
docker compose -f infrastructure/docker/compose/docker-compose.yml -f infrastructure/docker/compose/docker-compose.dev.yml logs -f

# Specific service
docker compose -f infrastructure/docker/compose/docker-compose.yml -f infrastructure/docker/compose/docker-compose.dev.yml logs -f backend
```

### Restart Services
```bash
# Restart all
docker compose -f infrastructure/docker/compose/docker-compose.yml -f infrastructure/docker/compose/docker-compose.dev.yml restart

# Restart single service
docker compose -f infrastructure/docker/compose/docker-compose.yml -f infrastructure/docker/compose/docker-compose.dev.yml restart dashboard
```

### Stop Services
```bash
# Stop containers, keep data
docker compose -f infrastructure/docker/compose/docker-compose.yml -f infrastructure/docker/compose/docker-compose.dev.yml down

# Stop and remove volumes
docker compose -f infrastructure/docker/compose/docker-compose.yml -f infrastructure/docker/compose/docker-compose.dev.yml down -v
```

### Health Checks
```bash
curl http://localhost:8009/health        # Backend
curl http://localhost:5179/              # Dashboard
curl http://localhost:9877/health        # MCP server
curl http://localhost:8888/health        # Agent coordinator
```

## Available Scripts

1. `./infrastructure/docker/check-setup.sh` – quick validation of Docker prerequisites
2. `./infrastructure/docker/start-docker-dev.sh` – full validation + startup sequence
3. `./infrastructure/docker/start-services.sh` – minimal startup helper (no validation)
4. `./infrastructure/docker/start-services-enhanced.sh` – interactive startup with health monitoring
5. `./infrastructure/docker/validate-setup.sh` – comprehensive validation + reporting

## Postgres & Redis (Development Defaults)

- **Postgres**
  - Host: `localhost`
  - Port: `5434`
  - Database: `toolboxai`
  - User: `toolboxai`
  - Password: `devpass2024`

- **Redis**
  - Host: `localhost`
  - Port: `6381`
  - Password: _none in dev_

## Next Steps

After services are up, run backend migrations and seed data if needed:

```bash
cd /Users/grayghostdata/Desktop/Development/ToolboxAI-Solutions
source venv/bin/activate
alembic upgrade head
python scripts/development/seed_database.py
```

Happy hacking!
