# Manual Startup Instructions (Developer Mode)

Follow these steps when you need to bring the ToolboxAI development stack up by hand.

## 1. Start Docker Desktop
```bash
open -a Docker
```
Wait until the Docker whale icon in the macOS menu bar stops animating.

## 2. Confirm Docker Is Ready
```bash
docker ps
```
Seeing the container table (even if empty) means Docker is ready.

## 3. Navigate to the Repository
```bash
cd /Users/grayghostdata/Desktop/Development/ToolboxAI-Solutions
```

## 4. (Optional) Run the Preflight Check
```bash
./infrastructure/docker/check-setup.sh
```
This highlights missing Dockerfiles, port conflicts, and required env vars.

## 5. Stop Any Existing Stack
```bash
docker compose -f infrastructure/docker/compose/docker-compose.yml \
              -f infrastructure/docker/compose/docker-compose.dev.yml down
```
This clears out stale containers while keeping volumes intact.

## 6. Start All Services
```bash
COMPOSE="docker compose -f infrastructure/docker/compose/docker-compose.yml -f infrastructure/docker/compose/docker-compose.dev.yml"
$COMPOSE up -d
```
On first run Docker downloads images and builds containers; expect a few minutes of setup.

## 7. Verify Containers
```bash
docker compose -f infrastructure/docker/compose/docker-compose.yml \
              -f infrastructure/docker/compose/docker-compose.dev.yml ps
```
You should see `postgres`, `redis`, `backend`, `dashboard`, `mcp-server`, `agent-coordinator`, `celery-worker`, `celery-beat`, `flower`, `adminer`, `redis-commander`, and `mailhog` listed as running/healthy.

## 8. Tail Logs (if needed)
```bash
$COMPOSE logs -f backend
$COMPOSE logs -f dashboard
```
Press `Ctrl+C` to stop streaming.

## 9. Access the Running Services

| Service | URL | Notes |
| --- | --- | --- |
| Dashboard | http://localhost:5179 | Vite dev server |
| Backend API | http://localhost:8009 | FastAPI |
| API Docs | http://localhost:8009/docs | Swagger UI |
| MCP Server | http://localhost:9877 | Model Context Protocol |
| Agent Coordinator | http://localhost:8888 | Orchestration API |
| Celery Flower | http://localhost:5555 | Task dashboard (admin/admin) |
| Adminer | http://localhost:8080 | Postgres UI |
| Redis Commander | http://localhost:8081 | Redis browser (admin/admin) |
| Mailhog | http://localhost:8025 | Test inbox |

## Helper Scripts

All scripts live in `infrastructure/docker/` and assume you are in the repo root.

| Script | When to Use |
| --- | --- |
| `check-setup.sh` | Quick readiness check (Docker, ports, env vars) |
| `start-docker-dev.sh` | Full validation and startup sequence |
| `start-services.sh` | Lightweight helper when you just need the stack |
| `start-services-enhanced.sh` | Guided startup with health polling |
| `validate-setup.sh` | Comprehensive validation + reporting |

## Common Issues

### Port Already in Use
```bash
lsof -i :5434 :6381 :8009 :5179
```
Stop the conflicting process or update the port mapping in the dev compose override.

### Docker Compose Errors
Run the validation suite for actionable diagnostics:
```bash
./infrastructure/docker/validate-setup.sh
```

### Backend or Dashboard Unreachable
Inspect logs:
```bash
$COMPOSE logs -f backend
$COMPOSE logs -f dashboard
```
Most failures trace back to missing environment variables or database migrations.

## Clean Up
```bash
# Stop stack, keep volumes
$COMPOSE down

# Stop stack and remove volumes (irreversible)
$COMPOSE down -v
```

## Development Database Defaults
- Host: `localhost` (maps to container `postgres`)
- Port: `5434`
- Database: `toolboxai`
- User: `toolboxai`
- Password: `devpass2024`

Redis listens on `localhost:6381` with no password in development.

With services running you can apply migrations or seed data:
```bash
source venv/bin/activate
alembic upgrade head
python scripts/development/seed_database.py
```

That’s it—your ToolboxAI development environment is live.
