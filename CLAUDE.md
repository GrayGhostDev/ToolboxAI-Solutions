# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ToolBoxAI-Solutions is a comprehensive educational technology platform that integrates Roblox game-based learning with AI-powered content generation, Learning Management System (LMS) integrations, and real-time analytics.

## Repository Structure

```
./
├── ToolboxAI-Roblox-Environment/    # Main Roblox educational platform (95% complete)
│   ├── mcp/                         # Model Context Protocol (WebSocket :9876)
│   ├── agents/                      # LangChain/LangGraph AI agents
│   ├── sparc/                       # State-Policy-Action-Reward-Context framework
│   ├── swarm/                       # Swarm intelligence coordination
│   ├── coordinators/                # High-level workflow management
│   ├── server/                      # FastAPI (:8008) & Flask (:5001) servers
│   ├── toolboxai_utils/             # Shared utility modules
│   ├── Roblox/                      # Roblox Studio components & Lua scripts
│   ├── API/                         # Dashboard & Ghost backend integration
│   ├── tests/                       # Comprehensive test suite
│   │   ├── unit/                    # Unit tests for individual components
│   │   ├── integration/             # Integration tests for workflows
│   │   ├── e2e/                     # End-to-end tests
│   │   └── performance/             # Performance and load tests
│   ├── venv_clean/                  # Clean Python virtual environment
│   └── .env.example                 # Environment variables template
├── src/                              # Source code organization
│   ├── api/                         # API implementations
│   ├── dashboard/                   # Dashboard components
│   └── shared/                      # Shared utilities and types
├── scripts/                          # Management and deployment scripts
│   ├── integration/                 # Integration verification scripts
│   ├── testing/                     # Comprehensive testing scripts
│   ├── deploy/                      # Production deployment scripts
│   ├── setup/                       # Environment setup scripts
│   ├── maintenance/                 # Maintenance and cleanup scripts
│   ├── database/                    # Database management scripts
│   ├── terminal_sync/               # Terminal synchronization scripts
│   ├── cleanup/                     # Project cleanup scripts
│   └── pids/                        # Process ID files
├── config/                           # Configuration files
│   ├── production/                  # Production configurations
│   │   ├── docker-compose.prod.yml  # Production Docker Compose
│   │   ├── production.env           # Production environment variables
│   │   └── nginx.conf               # Nginx configuration
│   ├── development/                 # Development configurations
│   └── templates/                   # Configuration templates
├── database/                         # Database setup and migrations
│   ├── schemas/                     # Database schema files
│   ├── migrations/                  # Alembic migrations
│   └── repositories.py              # Database repositories
├── logs/                             # Application logs
├── test-results/                     # Test execution results
├── backups/                          # Database and configuration backups
└── Documentation/                    # Project documentation
    ├── 01-overview/                 # Getting started guides
    ├── 02-architecture/             # System design & data models
    ├── 03-api/                      # API documentation
    ├── 04-implementation/           # Implementation details & fixes
    ├── 05-features/                 # Feature documentation
    ├── 06-user-guides/              # User guides and tutorials
    ├── 07-operations/               # Operations and deployment
    ├── 08-reference/                # Reference documentation
    ├── 09-meta/                     # Meta documentation & assessments
    ├── 10-reports/                  # Various technical reports
    ├── 11-sdks/                     # SDK documentation
    ├── 12-status/                   # Project status and TODO
    ├── 13-terminals/                # Terminal-specific documentation
    └── 14-testing/                  # Testing documentation
```

## Development Commands

### ToolboxAI-Roblox-Environment (Main Project)

```bash
cd ToolboxAI-Roblox-Environment

# Setup Python environment
python -m venv venv_clean
source venv_clean/bin/activate  # On Windows: venv_clean\Scripts\activate
pip install -r requirements.txt

# Install Node dependencies
npm install

# Start all services (recommended)
scripts/start_mcp_servers.sh     # Start all services with proper orchestration

# Alternative manual start
python mcp/server.py &           # MCP server (:9876)
python server/main.py &          # FastAPI server (:8008)
python server/roblox_server.py & # Flask bridge (:5001)

# Service management
scripts/check_mcp_status.sh      # Check all service status
scripts/stop_mcp_servers.sh      # Stop all services

# Comprehensive testing
scripts/testing/run_comprehensive_tests.sh --type=all --verbose --coverage
scripts/testing/run_comprehensive_tests.sh --type=unit        # Unit tests only
scripts/testing/run_comprehensive_tests.sh --type=integration # Integration tests only
scripts/testing/run_comprehensive_tests.sh --type=e2e         # End-to-end tests only
scripts/testing/run_comprehensive_tests.sh --type=performance # Performance tests only

# Integration verification
scripts/integration/verify_integration_paths.sh --verbose --fix-issues

# Legacy pytest commands (still supported)
pytest tests/ -v --cov=server --cov=agents --cov=mcp
pytest tests/unit/               # Unit tests only
pytest tests/integration/        # Integration tests only
pytest tests/e2e/               # End-to-end tests only

# Code quality
black server/ agents/ mcp/ sparc/ swarm/ coordinators/
flake8 server/ agents/ mcp/
mypy server/ agents/ mcp/
```

### Production Deployment

```bash
# From project root directory

# Database setup
scripts/database/setup_database.sh

# Production deployment
scripts/deploy/deploy_production.sh --environment=production
scripts/deploy/deploy_production.sh --skip-tests --force    # Force deploy
scripts/deploy/deploy_production.sh --rollback             # Rollback deployment

# Production management
docker-compose -f config/production/docker-compose.prod.yml up -d
docker-compose -f config/production/docker-compose.prod.yml down
docker-compose -f config/production/docker-compose.prod.yml logs -f

# Health monitoring
scripts/check_mcp_status.sh
scripts/integration/verify_integration_paths.sh --verbose
```

### Dashboard

```bash
cd API/Dashboard

# Backend setup
cd backend
pip install -r requirements.txt
uvicorn backend.api.education_manager:app --reload

# Frontend setup (from API/Dashboard root)
npm install
npm run dev    # Development server (:3000)
npm run build  # Production build
npm test       # Run tests
```

### Ghost Backend (API/GhostBackend)

```bash
cd ToolboxAI-Roblox-Environment/API/GhostBackend

# Setup and run
./bin/setup.sh
./bin/dev_setup.sh
./bin/start_backend.sh    # Full stack (API + DB + Redis)
./bin/run_api.sh          # API only (:8000)

# Database management
make db/start
make db/stop
alembic upgrade head       # Apply migrations

# Testing
pytest
pytest --cov=src/ghost --cov-report=html
```

## Architecture Overview

### Technology Stack

- **Frontend**: React 18, TypeScript, Material-UI, Redux Toolkit, Vite
- **Backend**: FastAPI, SQLAlchemy (async), PostgreSQL, Redis, JWT auth
- **AI/ML**: LangChain, LangGraph, OpenAI GPT-4, SPARC framework
- **Roblox**: Lua scripting, Roblox Studio plugin (:64989)
- **Real-time**: WebSocket connections, Socket.io

### Key Services & Ports

- **FastAPI Server**: 127.0.0.1:8008 (Main API)
- **Flask Bridge**: 127.0.0.1:5001 (Roblox communication)
- **MCP WebSocket**: 127.0.0.1:9876 (Context management)
- **Ghost Backend**: 127.0.0.1:8000 (Alternative API)
- **Dashboard**: 127.0.0.1:3000 (React frontend)
- **Ghost CMS**: 127.0.0.1:2368 (Content management)
- **Roblox Plugin**: 127.0.0.1:64989 (Studio integration)

### Core Components

#### AI Agent System (agents/)
- **Supervisor Agent**: Orchestrates sub-agents using LangGraph
- **Content Agent**: Generates educational materials
- **Quiz Agent**: Creates interactive assessments
- **Terrain Agent**: Builds 3D environments
- **Script Agent**: Generates Lua code
- **Review Agent**: Quality assurance

#### SPARC Framework (sparc/)
- State management for environment tracking
- Policy engine for educational decisions
- Action executor for task implementation
- Reward calculator for learning outcomes
- Context tracker for user sessions

#### Swarm Intelligence (swarm/)
- Parallel agent execution
- Task distribution across workers
- Consensus-based quality control
- Load balancing for optimization

## API Documentation

### Generate Educational Content
```http
POST http://localhost:8008/generate_content
Content-Type: application/json

{
  "subject": "Science",
  "grade_level": 7,
  "learning_objectives": ["Solar System", "Planets"],
  "environment_type": "space_station",
  "include_quiz": true
}
```

### Health Check Endpoints
- FastAPI: `http://localhost:8008/health`
- Flask Bridge: `http://localhost:5001/health`
- Ghost Backend: `http://localhost:8000/health`

### API Documentation URLs
- FastAPI Swagger: `http://localhost:8008/docs`
- Ghost Backend Swagger: `http://localhost:8000/docs`

## Testing Strategy

### Test Coverage Requirements
- Unit tests: Cover all business logic
- Integration tests: API endpoints & database
- E2E tests: Full user workflows
- Performance tests: Load & response time benchmarks

### Running Tests
```bash
# All tests with coverage
pytest --cov=server --cov=agents --cov=mcp --cov-report=html

# Specific test marks
pytest -m "unit"
pytest -m "integration"
pytest -m "not slow"
```

## Security Configuration

- **All services bound to 127.0.0.1** (not 0.0.0.0) for security
- **JWT authentication** with role-based access control
- **Input validation** using Pydantic models
- **Rate limiting**: 100 requests/minute per IP
- **CORS configured** per frontend application

## Environment Variables

Create `.env` files in respective directories:

```bash
# Core settings
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-key

# LMS Integration
SCHOOLOGY_KEY=your-schoology-key
SCHOOLOGY_SECRET=your-schoology-secret
CANVAS_TOKEN=your-canvas-token

# Server configuration
API_HOST=127.0.0.1
API_PORT=8008
LOG_LEVEL=INFO
```

## Database Management

```bash
# PostgreSQL via Alembic
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# Check database status
make db/status
psql $DATABASE_URL
```

## Integration Points & Communication

### Service Communication Matrix
```
┌─────────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│ Service         │ FastAPI      │ Dashboard    │ Flask Bridge │ MCP Server   │
│                 │ (:8008)      │ (:8001)      │ (:5001)      │ (:9876)      │
├─────────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ FastAPI         │ -            │ HTTP/JSON    │ HTTP/JSON    │ WebSocket    │
│ Dashboard       │ HTTP/JSON    │ -            │ HTTP/JSON    │ WebSocket    │
│ Flask Bridge    │ HTTP/JSON    │ HTTP/JSON    │ -            │ WebSocket    │
│ MCP Server      │ WebSocket    │ WebSocket    │ WebSocket    │ -            │
│ Roblox Plugin   │ -            │ -            │ HTTP/JSON    │ -            │
│ Ghost Backend   │ HTTP/JSON    │ HTTP/JSON    │ -            │ -            │
└─────────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

### Database Integration
- **Educational Platform DB**: Main application data (users, courses, lessons)
- **Ghost Backend DB**: Content management and blog functionality
- **Roblox Data DB**: Game-specific data and player progress
- **MCP Memory DB**: AI agent context and memory storage
- **Redis Cache**: Session management and real-time data

### File Structure Updates
The project now includes comprehensive production-ready infrastructure:

- **`scripts/integration/`**: Integration verification and testing scripts
- **`scripts/testing/`**: Comprehensive test execution and reporting
- **`scripts/deploy/`**: Production deployment automation
- **`config/production/`**: Production configurations and Docker Compose
- **`test-results/`**: Test execution reports and coverage data
- **`backups/`**: Database and configuration backups

## Deployment

### Development Deployment
```bash
# Start all services
scripts/start_mcp_servers.sh

# Verify integration
scripts/integration/verify_integration_paths.sh --verbose

# Run comprehensive tests
scripts/testing/run_comprehensive_tests.sh --type=all --coverage
```

### Production Deployment
```bash
# Full production deployment
scripts/deploy/deploy_production.sh --environment=production

# Docker-based deployment
docker-compose -f config/production/docker-compose.prod.yml up -d

# Health monitoring
scripts/check_mcp_status.sh
```

### Production Configuration
```bash
# Environment variables
cp config/production/production.env .env
# Edit .env with your production values

# Database setup
scripts/database/setup_database.sh

# SSL/TLS configuration
# Place certificates in config/production/ssl/
```

## Common Development Tasks

### Adding New API Endpoint
1. Create route in `server/main.py` or appropriate module
2. Use dependency injection for database/auth
3. Return standardized APIResponse
4. Add tests in `tests/` directory

### Adding New AI Agent
1. Create agent class in `agents/` directory
2. Inherit from `BaseAgent`
3. Implement required methods
4. Register with supervisor in `agents/supervisor.py`
5. Add tests for agent behavior

### Modifying Roblox Integration
1. Update Lua scripts in `Roblox/Scripts/`
2. Test in Roblox Studio with plugin
3. Update API endpoints if needed
4. Document changes in relevant README

## Changelog (2025-09-10)

- WebSocket Diagnostics and Config
  - Added /ws/status endpoint in FastAPI to expose detailed WebSocket stats and active channels; includes role distribution.
  - Added /socketio/status endpoint exposing Socket.IO connected client counts, auth ratio, and role distribution.
  - Introduced WS_RATE_LIMIT_PER_MINUTE (per-connection WS limit) and WS_RBAC_REQUIRED_ROLES (per-message role overrides).
  - Added runtime RBAC admin endpoints: GET/POST/DELETE /ws/rbac (admin-only) to inspect, update, and reset RBAC mapping safely.
  - Tests: test_ws_status_endpoint.py, test_websocket_config_overrides.py, test_socketio_status_endpoint.py.

- Socket.IO RBAC and Rate Limiting
  - Added SIO_RBAC_REQUIRED_ROLES and SIO_RATE_LIMIT_PER_MINUTE to settings for per-event RBAC and rate limits.
  - Enforced RBAC and rate limiting in Socket.IO event handlers (ping, subscribe, content_request, quiz_response, progress_update, collaboration_message).
  - Tests added: tests/unit/test_socketio_rbac_and_rate_limit.py.

- SPARC StateManager
  - Enhanced initialize_state to inject default metadata (timestamp, source, system_bootstrap) improving initial quality metrics.
  - Implemented calculate_reward(metrics) to normalize reward in [0,1] using objectives met and execution time.
  - Added unit tests: tests/unit/test_state_manager.py for initialization and reward pathways.

- WebSocket Security
  - Added RBAC enforcement per message type (student/teacher/admin) in server/websocket.py MessageHandler.
    - Elevated actions now require teacher role: broadcast, content_request, roblox_event.
  - Added per-connection rate limiting using server.rate_limit_manager with settings.RATE_LIMIT_PER_MINUTE.
  - Enforced per-message JWT expiry in server/websocket_auth.authenticate_websocket_message.
  - Added observability counters for token/auth failures: token_expired and auth_errors incremented at message-auth stage.
  - Made WebSocketAuthSession.send_auth_message tolerant of mocks/missing client_state for reliable tests.
  - Added unit tests:
    - tests/unit/test_websocket_rbac_and_rate_limit.py (RBAC deny for broadcast; rate limit enforcement)
    - tests/unit/test_websocket_message_auth.py (token expiry denial)
    - tests/unit/test_websocket_metrics_token_expired.py (metrics increments for token_expired/auth_errors)

- Notes
  - No changes to external public API routes.
  - All new logic is feature-flag free and defaults to secure behavior.

## Troubleshooting

### Service Not Starting
```bash
# Check if ports are in use
lsof -i :8008
lsof -i :5001
lsof -i :9876

# Check logs
tail -f logs/*.log
```

### Database Connection Issues
```bash
# Check PostgreSQL status
make db/status

# Test connection
psql $DATABASE_URL

# Reset database
alembic downgrade base
alembic upgrade head
```

### AI Agent Errors
- Enable debug logging: `LOG_LEVEL=DEBUG`
- Check LangSmith traces: https://smith.langchain.com
- Verify API keys in `.env` file

## Best Practices

1. **Always use virtual environments** for Python projects
2. **Run tests before committing** code changes
3. **Use type hints** in Python code
4. **Follow existing code patterns** and conventions
5. **Document complex logic** with inline comments
6. **Keep services bound to localhost** for security
7. **Use environment variables** for configuration
8. **Write comprehensive tests** for new features

## Project Status

- **ToolboxAI-Roblox-Environment**: 90% complete (Roblox scripts remaining)
- **Dashboard**: Fully integrated with backend
- **Ghost Backend**: Complete and operational
- **Documentation**: Comprehensive guides available

## Additional Resources

- Main project README: `ToolboxAI-Roblox-Environment/README.md`
- Detailed implementation guide: `ToolboxAI-Roblox-Environment/CLAUDE.md`
- API documentation: `Documentation/03-api/`
- Architecture docs: `Documentation/02-architecture/`
- Add to memory. Real Real implementation integration other than Mock Data wherever possible. Then Continue With Remaining Work. Think Deeply.
- Add to memory. I want to use real Data.