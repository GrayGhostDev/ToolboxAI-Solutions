# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Quick Start
```bash
# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Docker (recommended for external drive development)
make docker-dev           # Start all services
make docker-dev-logs      # View logs
make docker-dev-down      # Stop services

# Native development
make dev                  # Start backend + frontend
make backend             # FastAPI on port 8009
make dashboard           # React on port 5179
```

### External Drive Development
```bash
# Native binaries fail on external drives with error -88
# Use Docker or these workarounds:
cd apps/dashboard && npm install --no-bin-links --legacy-peer-deps

# vite.config.js must be JavaScript (not TypeScript) on external drives
```

### Testing
```bash
# All tests
make test

# Python tests
pytest                                      # Run all
pytest tests/unit/core/test_settings.py    # Specific file
pytest -m unit                              # Unit tests only
pytest -k "test_function_name"              # Specific test

# Frontend tests
npm -w apps/dashboard test                 # Run tests
npm -w apps/dashboard run test:coverage    # With coverage
npm -w apps/dashboard run test:watch       # Watch mode

# Integration test flags (optional)
RUN_ENDPOINT_TESTS=1 pytest               # Enable endpoint tests
RUN_ROJO_TESTS=1 pytest                   # Enable Rojo tests
```

### Building & Linting
```bash
# Build
make build                               # Production build
npm -w apps/dashboard run build         # Dashboard only

# Linting
make lint                                # All linting
black apps/backend                       # Python formatting
npm -w apps/dashboard run lint:fix      # JS/TS fix

# Type checking
basedpyright .                           # Python types
npm -w apps/dashboard run typecheck     # TypeScript
```

### Celery & Background Tasks
```bash
make celery-up          # Start worker, beat, flower
make celery-flower      # Monitoring UI (port 5555)
make celery-logs        # View worker logs
make celery-status      # Check worker status
make celery-purge       # Clear task queue
```

### Docker Services
```bash
# Service management
make docker-monitoring   # Start Grafana, Loki, Jaeger
make roblox-sync        # Roblox sync service
make urls               # Show all service URLs
make health             # Check service health

# Database access
make db-shell           # PostgreSQL CLI
make redis-cli          # Redis CLI
```

## Architecture

### Project Structure
```
apps/
├── backend/          # FastAPI server (port 8009)
│   ├── routers/     # API endpoints
│   ├── services/    # Business logic
│   └── main.py      # Application factory
├── dashboard/        # React 19 frontend (port 5179)
│   ├── src/         # Source code
│   └── vite.config.js # Build config (JS for external drive)

core/                # AI agent system
├── agents/          # Agent implementations
├── mcp/            # Model Context Protocol
└── sparc/          # SPARC framework

database/           # Data layer
├── models.py       # SQLAlchemy models
└── migrations/     # Alembic migrations

roblox/             # Roblox integration
├── src/           # Luau scripts
└── plugins/       # Studio plugins

infrastructure/
└── docker/
    └── compose/   # Docker compose files
```

### Key Systems

**Backend Stack**
- FastAPI with Pydantic v2 (`@field_validator`, `model_config = ConfigDict()`)
- PostgreSQL + Redis
- Pusher for realtime (channels: `dashboard-updates`, `content-generation`)
- JWT authentication with role-based access
- Celery 5.4 for async tasks

**Frontend Stack**
- React 19.1.0 + TypeScript 5.9.2
- Vite 6.0.1 (use vite.config.js on external drives)
- Mantine UI v8 (replaced Material-UI)
- Redux Toolkit for state
- Pusher.js for realtime

**Testing Stack**
- pytest with markers (`unit`, `integration`)
- Vitest 3.2.4 for React components
- Test database shims in `database/` for compatibility

### Environment Configuration

```bash
# Backend (.env)
DATABASE_URL=postgresql://eduplatform:eduplatform2024@localhost/educational_platform_dev
REDIS_URL=redis://localhost:6379
PUSHER_APP_ID=your-id
PUSHER_KEY=your-key
PUSHER_SECRET=your-secret
JWT_SECRET_KEY=generate-with-openssl-rand-hex-32

# Frontend (apps/dashboard/.env.local)
VITE_API_BASE_URL=http://127.0.0.1:8009
VITE_PUSHER_KEY=your-key
VITE_PUSHER_CLUSTER=your-cluster
```

### Common Patterns

**API Response Format**
```python
{
    "status": "success|error",
    "data": {...},
    "message": "...",
    "metadata": {...}
}
```

**Pusher Integration**
```typescript
// Frontend
import { usePusherChannel, usePusherEvent } from '@/hooks/pusher';
usePusherEvent('content-progress', (data) => updateProgress(data));

// Backend
POST /pusher/auth         # Channel authentication
POST /realtime/trigger    # Trigger events
```

**Mantine UI Migration**
```typescript
// MUI → Mantine mappings
Typography → Text
TextField → TextInput
IconButton → ActionIcon
Dialog → Modal
CircularProgress → Loader
```

### Development Workflow

**Adding New API Endpoint**
1. Create router in `apps/backend/routers/`
2. Add Pydantic models for request/response
3. Register router in `main.py`
4. Update frontend API client in `apps/dashboard/src/services/api.ts`
5. Add tests for both backend and frontend

**Database Changes**
1. Modify models in `database/models.py`
2. `alembic revision --autogenerate -m "description"`
3. `alembic upgrade head`
4. Test rollback: `alembic downgrade -1`

### Debugging

**Port Conflicts**
```bash
lsof -i :8009 | grep LISTEN    # Check backend
lsof -i :5179 | grep LISTEN    # Check frontend
```

**Docker Issues**
```bash
# Check logs
docker compose -f infrastructure/docker/compose/docker-compose.yml logs service-name

# Fix permissions (non-root containers)
sudo chown -R 1001:1001 ./data/postgres/
```

**External Drive Issues**
- Error -88: Use Docker or vite.config.js (not .ts)
- npm install: Always add `--no-bin-links --legacy-peer-deps`
- Native binaries (esbuild, Rollup) won't work

### Critical Context

- **Current Branch**: `chore/remove-render-worker-2025-09-20`
- **Main Branch**: `main` (use for PRs)
- **Virtual Environment**: Always use `venv/` in project root
- **External Drive Path**: `/Volumes/G-DRIVE ArmorATD/`
- **Production Gaps**: Missing Stripe, email service, background jobs
- **Security**: Use Docker Secrets in production, never commit credentials