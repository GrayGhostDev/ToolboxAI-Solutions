# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ToolBoxAI-Solutions is a comprehensive educational technology platform that integrates Roblox game-based learning with AI-powered content generation, Learning Management System (LMS) integrations, and real-time analytics.

## Repository Structure

```
/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/
├── ToolboxAI-Roblox-Environment/    # Main Roblox educational platform (90% complete)
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
│   ├── venv_clean/                  # Clean Python virtual environment
│   └── .env.example                 # Environment variables template
├── API/                              # API integrations
│   └── Dashboard/                    # React-based teacher/admin dashboard
└── Documentation/                    # Project documentation
    ├── 01-overview/                 # Getting started guides
    ├── 02-architecture/             # System design & data models
    ├── 03-api/                      # API documentation
    └── 11-sdks/                     # SDK documentation
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

# Start all services
python mcp/server.py &           # MCP server (:9876)
python server/main.py &          # FastAPI server (:8008)
python server/roblox_server.py & # Flask bridge (:5001)

# Run tests
pytest tests/ -v --cov=server --cov=agents --cov=mcp
pytest tests/unit/               # Unit tests only
pytest tests/integration/        # Integration tests only
pytest tests/e2e/               # End-to-end tests only

# Code quality
black server/ agents/ mcp/ sparc/ swarm/ coordinators/
flake8 server/ agents/ mcp/
mypy server/ agents/ mcp/
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

## Deployment

### Docker Deployment
```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

### Production Configuration
```bash
export ENVIRONMENT=production
export DEBUG=false
export LOG_LEVEL=INFO
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