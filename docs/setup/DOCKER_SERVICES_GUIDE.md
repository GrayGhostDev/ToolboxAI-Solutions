# Docker Services Startup Guide – 2025 Edition

## Quick Start

### Option 1 – Automated (Recommended)
```bash
cd /Users/grayghostdata/Desktop/Development/ToolboxAI-Solutions
./infrastructure/docker/start-docker-dev.sh
```
This script performs validation, builds images, starts the stack, and shows health summaries.

### Option 2 – Manual Compose Command
```bash
cd /Users/grayghostdata/Desktop/Development/ToolboxAI-Solutions
COMPOSE="docker compose -f infrastructure/docker/compose/docker-compose.yml -f infrastructure/docker/compose/docker-compose.dev.yml"
$COMPOSE up -d
```

## Services Included

The combined configuration launches:

### Core Platform
| Service | Container | Port | Notes |
| --- | --- | --- | --- |
| PostgreSQL | `toolboxai-postgres` | 5434 | Local dev DB (user/db `toolboxai`) |
| Redis | `toolboxai-redis` | 6381 | Cache, Celery broker |
| Backend API | `toolboxai-backend` | 8009 | FastAPI + background tasks |
| Dashboard | `toolboxai-dashboard` | 5179 | Vite dev server |
| MCP Server | `toolboxai-mcp` | 9877 | Model Context Protocol endpoint |
| Agent Coordinator | `toolboxai-coordinator` | 8888 | AI agent orchestration |
| Celery Worker | `toolboxai-celery-worker` | — | Processes async jobs |
| Celery Beat | `toolboxai-celery-beat` | — | Schedules periodic jobs |
| Flower | `toolboxai-flower` | 5555 | Task monitoring |
| Adminer | `toolboxai-adminer` | 8082 | Database UI |
| Redis Commander | `toolboxai-redis-commander` | 8081 | Redis UI |
| Mailhog | `toolboxai-mailhog` | 8025 | Email testing |

## Troubleshooting

### Docker Not Running
```bash
open -a Docker
```
Wait until Docker Desktop reports "Running", then retry.

### Compose Validation Failure
Run the validation script for detailed diagnostics:
```bash
./infrastructure/docker/validate-setup.sh
```

### Port Conflicts
```bash
lsof -i :5434 :6381 :8009 :5179 :9877 :8888
```
Stop conflicting processes or adjust the port mapping in `docker-compose.dev.yml`.

### Containers Healthy but App Offline
Check service logs:
```bash
docker compose -f infrastructure/docker/compose/docker-compose.yml -f infrastructure/docker/compose/docker-compose.dev.yml logs -f backend
docker compose -f infrastructure/docker/compose/docker-compose.yml -f infrastructure/docker/compose/docker-compose.dev.yml logs -f dashboard
```

### Cleaning Up
```bash
# Stop containers but keep volumes
$COMPOSE down

# Remove containers + volumes
$COMPOSE down -v

# Remove build cache (optional)
docker image prune -f
```

## Working with Helper Scripts

| Script | Description |
| --- | --- |
| `check-setup.sh` | Quick preflight check (Docker, compose files, ports) |
| `start-docker-dev.sh` | Full validation + ordered startup |
| `start-services.sh` | Minimal helper for quick restarts |
| `start-services-enhanced.sh` | Interactive startup with health polling |
| `validate-setup.sh` | Comprehensive validation suite + report |

All scripts live in `infrastructure/docker/` and assume you run them from the repository root.

## Environment Variables

Ensure `.env` includes:

- `POSTGRES_PASSWORD`
- `JWT_SECRET_KEY`
- `PUSHER_APP_ID`, `PUSHER_KEY`, `PUSHER_SECRET`, `PUSHER_CLUSTER`
- `OPENAI_API_KEY` (mock key acceptable for dev)

The scripts warn if any critical values are missing or blank.

## Health Check Endpoints

- Backend: `http://localhost:8009/health`
- Dashboard: `http://localhost:5179/`
- MCP: `http://localhost:9877/health`
- Agent Coordinator: `http://localhost:8888/health`

## Stop / Restart Cheat Sheet

```bash
# Stop stack (keep data)
$COMPOSE down

# Restart backend only
$COMPOSE restart backend

# Tail logs for celery worker
$COMPOSE logs -f celery-worker

# View status table
$COMPOSE ps
```

Use this guide as the canonical reference for local service orchestration in 2025.
