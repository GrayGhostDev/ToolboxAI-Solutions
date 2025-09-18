# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current Repository State (After 2025-09-16 Cleanup)

This is a monorepo that underwent significant restructuring in September 2025. Multiple agents (warp001-warp007) have worked on various improvements. The repository is on branch `chore/repo-structure-cleanup` with main work tracked in `main` branch.

### Major Reorganization (2025-09-16)
- **Directory Cleanup**: Complete reorganization of root directory - see ROOT_DIRECTORY_ORGANIZATION.md
- **Core Components Consolidated**: All AI agents, MCP, coordinators moved to `core/` directory
- **Documentation Centralized**: All docs moved to `docs/` with organized subfolders
- **Virtual Environment**: Cleaned up duplicate environments, use standard `venv/`

### Recent Updates (2025-09-16)
- **BasedPyright Configuration**: Migrated from `[tool.pyright]` to `[tool.basedpyright]` in pyproject.toml
- **Pydantic v2 Migration**: Updated all deprecated Pydantic v1 patterns to v2 (field_validator, model_config)
- **Complete Type Implementations**: Replaced stub files (.pyi) with complete implementations
- **Type Safety**: Enhanced type checking with proper SQLAlchemy and Pydantic type definitions
- **Configuration Fixes**: Resolved path issues, removed stubPath, fixed diagnosticSeverityOverrides
- **All BasedPyright Errors Resolved**: Configuration now works correctly with BasedPyright 1.31.3
- **TOML Validation**: Fixed TOML parsing errors and removed invalid configuration options
- **Comprehensive Testing**: All implementations tested and verified working correctly

### Critical Context (Updated 2025-09-16)
- **Dashboard Structure**: The active dashboard is at `apps/dashboard/` (package.json confirmed)
- **Realtime Migration**: Dashboard migrated from Socket.IO to Pusher Channels (warp007)
- **Path Normalization**: All components now use canonical paths under `core/` directory
- **Archived Content**: Old embedded dashboard backends archived to `Archive/2025-09-16/deprecated/`
- **Documentation Location**: This file now resides in `docs/09-meta/CLAUDE.md`

## Development Environment

### Key Paths (Updated 2025-09-16)
- **Python Environment**: `venv/` - Standard virtual environment (create with `python3 -m venv venv`)
- **Backend API**: `apps/backend/` - FastAPI server on port 8008
- **Dashboard**: `apps/dashboard/` - React + TypeScript frontend on port 5179
- **Core Components**: `core/` - Contains agents, MCP, coordinators, sparc, database
- **Database**: `database/` - Models and migrations
- **Scripts**: `scripts/` - Automation and utility scripts
- **Configuration**: `config/` - All configuration files

### IDE Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Point VS Code/Cursor Python interpreter to:
/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/venv/bin/python

# Reload window after changing interpreter for pyright to pick up packages
```

## Development Commands

### Quick Start
```bash
# Start both backend and frontend
make dev

# Or run separately:
make backend   # FastAPI on localhost:8008
make dashboard # React dashboard on localhost:5179

# Alternative: Run from specific directories
cd apps/backend && uvicorn main:app --host 127.0.0.1 --port 8008 --reload
cd apps/dashboard && npm run dev
```

### Type System & Configuration

The project uses **BasedPyright** for type checking with complete implementations (no stubs):

```bash
# Type checking with BasedPyright
basedpyright .

# Configuration in pyproject.toml
[tool.basedpyright]
typeCheckingMode = "standard"
pythonVersion = "3.12"
# ... see pyproject.toml for full configuration
```

**Key Type Files:**
- `core/types/pydantic/` - Complete Pydantic v2 implementations
- `core/types/pydantic_settings/` - Pydantic Settings implementations
- `core/types/sqlalchemy/` - Complete SQLAlchemy type definitions
- `toolboxai_settings/` - Shared settings module

**Pydantic v2 Patterns Used:**
- `@field_validator` instead of `@validator`
- `model_config = ConfigDict()` instead of `class Config`
- `model_validator` for cross-field validation

### Testing
```bash
# Run all tests
make test

# Python tests (from root)
pytest -q
# Or specific test file
pytest tests/unit/core/test_settings.py
# Run with specific markers
pytest -m unit        # Unit tests only
pytest -m integration # Integration tests only

# Dashboard tests
npm -w apps/dashboard test
# With coverage
npm -w apps/dashboard run test:coverage

# Run single test or test file
pytest tests/test_specific.py::test_function_name -v
```

### Environment Flags for Testing
Some integration tests are gated behind environment variables to prevent heavy operations:
```bash
RUN_ENDPOINT_TESTS=1     # Enable endpoint script tests
RUN_ROJO_TESTS=1         # Enable Rojo integration tests
RUN_SOCKETIO_E2E=1       # Enable Socket.IO E2E tests
RUN_WS_INTEGRATION=1     # Enable WebSocket integration tests
```

### Building & Linting
```bash
# Build dashboard for production
make build
# Or: npm -w apps/dashboard run build

# Lint checks
make lint
# Or separately:
npm -w apps/dashboard run lint      # TypeScript/React
npm -w apps/dashboard run typecheck # Type checking only

# Python linting (if configured)
black apps/backend
mypy apps/backend
```

### Dashboard-specific Commands
```bash
# Development server with hot reload
cd apps/dashboard && npm run dev

# Run on different port to avoid conflicts
PORT=5180 npm run dev

# Check Socket.IO connectivity (legacy, now using Pusher)
npm run socketio:check:env

# Type checking
npm run typecheck
```

## Architecture Overview

### Core Systems

#### 1. **FastAPI Backend** (`apps/backend/`)
- Main API server with WebSocket support for legacy features
- Pusher integration for new realtime features
- Integrates with LangChain, agents, and Roblox content generation
- Uses Pydantic v2 for settings and validation
- Sentry for error tracking (when enabled)
- CORS configured for multi-platform access

#### 2. **React Dashboard** (`apps/dashboard/`)
- Material-UI based interface
- Redux Toolkit for state management
- Pusher.js for realtime updates (migrated from Socket.IO)
- Multi-role authentication (admin, teacher, student)
- Vite for bundling with proxy configuration

#### 3. **AI Agent System** (`core/agents/`)
- Base agent architecture for content generation
- Specialized agents: ContentAgent, CleanupAgent, OrchestrationAgent
- Orchestrator for coordinating multiple agents
- SPARC framework integration for structured reasoning
- Mock LLM for testing

#### 4. **MCP (Model Context Protocol)** (`core/mcp/`)
- Context management for AI interactions
- Server-side tools and resource handling
- Integration with LangChain

#### 5. **Database Layer** (`database/`)
- PostgreSQL for persistent storage
- Redis for caching and sessions
- SQLAlchemy ORM with async support
- Alembic for migrations
- Compatibility shims for legacy test imports

### Configuration Management

#### Shared Settings
- **Location**: `toolboxai_settings/settings.py`
- **Usage**: Both backend servers import the shared `settings` instance
- **Environment**: Uses Pydantic v2 with `pydantic-settings`
- **Compatibility**: `toolboxai_settings/compat.py` provides v1 adapter if needed

#### Key Environment Variables
```bash
# Database
DATABASE_URL=postgresql://eduplatform:eduplatform2024@localhost/educational_platform_dev

# API Keys (set in .env files)
OPENAI_API_KEY=your-key

# Pusher (for realtime features)
PUSHER_APP_ID=your-id
PUSHER_KEY=your-key
PUSHER_SECRET=your-secret
PUSHER_CLUSTER=your-cluster

# Redis
REDIS_URL=redis://localhost:6379

# Sentry (optional)
SENTRY_DSN=your-dsn
```

#### Dashboard Environment (.env.local)
```bash
# Create apps/dashboard/.env.local
VITE_API_BASE_URL=http://127.0.0.1:8008
VITE_WS_URL=http://127.0.0.1:8008
VITE_ENABLE_WEBSOCKET=true
VITE_PUSHER_KEY=your-key
VITE_PUSHER_CLUSTER=your-cluster
VITE_PUSHER_AUTH_ENDPOINT=/pusher/auth
```

### Realtime Features (Pusher Migration)

#### Pusher Channels (Current)
- `dashboard-updates` - General dashboard notifications
- `content-generation` - Content creation progress
- `agent-status` - Agent activity monitoring
- `public` - Public announcements

#### Backend Endpoints
- `POST /pusher/auth` - Channel authentication
- `POST /realtime/trigger` - Trigger events
- `POST /pusher/webhook` - Process Pusher webhooks

#### Legacy WebSocket Support
The backend still maintains WebSocket endpoints for backward compatibility:
- `/ws/content` - Content generation updates
- `/ws/roblox` - Roblox environment sync
- `/ws/agent/{agent_id}` - Individual agent communication
- `/ws/native` - Test echo endpoint

### Testing Strategy

#### Python Tests
- Located in `ToolboxAI-Roblox-Environment/tests/`
- Markers: `@pytest.mark.unit`, `@pytest.mark.integration`
- Coverage reports in `htmlcov/`
- Run with `-v` for verbose output
- Some tests gated behind environment flags (see above)

#### Frontend Tests
- Located in `apps/dashboard/src/__tests__/`
- Uses Vitest with React Testing Library
- Mock API responses with axios-mock-adapter
- Component and integration tests
- jsdom environment with canvas/ResizeObserver mocks needed

#### Test Database Shims
Compatibility layers exist for legacy test imports:
- `database/connection.py` - Re-exports from root
- `database/models.py` - Re-exports from root
- `get_session()` / `get_async_session()` helpers

### Docker & Deployment

#### Docker Compose Files
- `config/production/docker-compose.yml` - Production stack
- `config/production/docker-compose.dev.yml` - Development overrides
- `config/production/Dockerfile.*` - Service-specific Dockerfiles

#### Services
- PostgreSQL database (eduplatform user)
- Redis cache
- FastAPI backend
- React dashboard (served by nginx in production)

### Important Patterns

#### API Response Format
```python
{
    "status": "success|error",
    "data": {...},
    "message": "...",
    "metadata": {...}
}
```

#### Authentication Flow
1. Login via `/api/v1/auth/login`
2. JWT token in Authorization header
3. Role-based access control (admin, teacher, student)
4. Pusher auth via `/pusher/auth` for private channels

#### Agent Communication
1. HTTP POST to `/api/v1/agents/execute`
2. Pusher channels for realtime updates
3. Task queue via Redis for background processing
4. Legacy WebSocket support maintained

### Known Issues & Workarounds

#### 1. Dashboard Structure (RESOLVED)
- **Previous Issue**: Documentation incorrectly stated nested structure
- **Current State**: Dashboard is correctly at `apps/dashboard/`
- **Status**: Fixed in documentation 2025-09-16

#### 2. Import Path Issues
- **Issue**: Some imports reference old `src/roblox-environment` path
- **Status**: Mostly fixed (warp001), check `Archive/` for historical references only

#### 3. Database Model Imports
- **Issue**: `EducationalContent` import errors on startup
- **Workaround**: Shims in place; full alignment pending

#### 4. Port Conflicts
- **Issue**: Multiple services trying to use same ports
- **Workaround**: Use `PORT=5180 npm run dev` for alternate ports

#### 5. Test Environment Setup
- **Issue**: jsdom missing canvas/ResizeObserver for charts
- **Fix**: Add mocks in `src/test/setup.ts`

#### 6. Type Checking Memory Issues
- **Issue**: Full pyright scan causes OOM
- **Fix**: Use `config/pyrightconfig.narrow.json` for targeted checks

### Development Workflow

#### Making Changes
1. Check current branch: `git status` (currently on `chore/repo-structure-cleanup`)
2. Main branch: `main` (use for PRs)
3. Create feature branch from main
4. Run tests before committing
5. Lint and typecheck must pass

#### Database Changes
1. Modify models in `database/models.py`
2. Create migration: `alembic revision --autogenerate -m "description"`
3. Apply migration: `alembic upgrade head`
4. Test rollback: `alembic downgrade -1`

#### Adding New Endpoints
1. Create router in `apps/backend/routers/`
2. Add Pydantic models for request/response
3. Register router in `main.py`
4. Add corresponding frontend API client in `apps/dashboard/src/services/api.ts`
5. Update tests for both backend and frontend

### Debugging Tips

#### Backend Debugging
- Check logs: `uvicorn` outputs to console
- Enable debug mode: `DEBUG=true` in `.env`
- Test endpoints: Use `httpx` or curl
- Pusher debugging: Check Pusher dashboard for event logs

#### Frontend Debugging
- React DevTools for component inspection
- Redux DevTools for state debugging
- Network tab for API calls
- Pusher debug: `Pusher.logToConsole = true` in development

#### Common Issues
- **Port conflicts**: Kill existing processes on 8008/5179
  ```bash
  lsof -i :8008 | grep LISTEN
  lsof -i :5179 | grep LISTEN
  ```
- **Database connection**: Ensure PostgreSQL is running
- **Redis connection**: Start Redis service
- **Module imports**: Check Python path and venv activation
- **CORS errors**: Verify backend CORS configuration matches frontend URL
- **Vite proxy issues**: Check `vite.config.ts` proxy targets match backend

### CI/CD & Quality

#### GitHub Actions Workflows
- `.github/workflows/socketio-smoke.yml` - Socket.IO status tests (legacy)
- Python 3.11/3.12 matrix for compatibility
- Consider adding secret scanning (gitleaks/trufflehog)

#### Pre-commit Hooks
Consider adding for:
- Black (Python formatting)
- ESLint (TypeScript/React)
- Markdownlint (documentation)

### Recent Work Summary (from warp agents)

#### warp001 - Path Normalization
- Replaced `src/roblox-environment` references with `ToolboxAI-Roblox-Environment`
- Fixed dashboard config imports
- Added database compatibility shims
- Added smoke tests

#### warp002 - Socket.IO Standardization
- Unified Socket.IO path to `/socket.io` (no trailing slash)
- Added integration tests
- Hardened CORS configuration
- Created WebSocket/Socket.IO guide

#### warp003 - Documentation Cleanup
- Archived historical docs to `Documentation/Archive/2025-09-16/`
- Added OpenAPI specs (JSON/YAML)
- Added maintenance scripts for docs

#### warp004 - Dashboard Fixes
- Fixed white-screen issues
- Unified config exports
- Standardized WebSocket singleton pattern
- Added connectivity check scripts

#### warp005 - Dashboard Connection
- Aligned ports and Socket.IO paths
- Fixed Vite dependency scanning
- Resolved shared-settings aliases

#### warp006 - Type Checking
- Created narrow Pyright config to avoid OOM
- Fixed agent type errors
- Added TaskResult.create helper
- Hardened Optional type safety

#### warp007 - Pusher Migration
- Migrated dashboard from Socket.IO to Pusher
- Added Pusher backend routes
- Fixed dashboard type errors
- Stabilized unit tests
- Created Pusher documentation

### Maintenance Notes

#### Regular Tasks
- Run `make test` before commits
- Check `npm -w apps/dashboard run typecheck` for frontend
- Use narrow Pyright config for Python type checking
- Monitor Pusher dashboard for realtime issues

#### Cleanup Opportunities
- Remove legacy Socket.IO code after full migration verified
- Remove database shims after test refactoring
- Archive old documentation in `Documentation/Archive/`

### Support Resources

#### Documentation
- Main docs: `Documentation/` directory
- API specs: `Documentation/03-api/openapi-spec.{json,yaml}`
- Pusher guide: `Documentation/05-features/dashboard/realtime-pusher.md`
- WebSocket guide: `Documentation/03-api/WEBSOCKET_SOCKETIO_GUIDE.md`

#### Configuration Files
- Python: `config/pyrightconfig.narrow.json` for type checking
- Database: `config/database.env` for PostgreSQL settings
- Production: `config/production/` for Docker and deployment
- MCP: `config/mcp-servers.json` for Model Context Protocol

### Critical Reminders

1. **Dashboard path is `apps/dashboard/`**: Documentation corrected 2025-09-16
2. **Check venv activation**: Use standard `venv/` virtual environment
3. **Run tests with flags**: Some integration tests need environment variables
4. **Use Pusher for new realtime features**: Socket.IO is legacy
5. **Database uses shims**: Be aware of compatibility layers in tests
6. **Type check with narrow config**: Avoid full pyright scan