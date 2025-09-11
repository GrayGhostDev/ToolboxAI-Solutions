# Development Setup Guide

## Prerequisites

### System Requirements

- **Operating System**: macOS 12+, Ubuntu 20.04+, Windows 10+ with WSL2
- **RAM**: Minimum 8GB, Recommended 16GB
- **Storage**: 20GB free space
- **CPU**: 4+ cores recommended

### Required Software

```bash
# Check installed versions
python --version      # Python 3.11+
node --version        # Node.js 18+
npm --version         # npm 9+
docker --version      # Docker 20+
git --version         # Git 2.30+
code --version        # VS Code (latest)
```text
## Local Development Environment

### 1. Clone Repository

```bash
# Clone the repository
git clone https://github.com/toolboxai/toolboxai-solutions.git
cd toolboxai-solutions

# Or if using external drive (macOS)
cd "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"
```text
### 2. Python Environment Setup

```bash
# Create virtual environment
python -m venv venv_clean

# Activate virtual environment
# macOS/Linux:
source venv_clean/bin/activate
# Windows:
venv_clean\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```text
### 3. Node.js Environment Setup

```bash
# Install Node dependencies
npm install

# Install global tools
npm install -g typescript
npm install -g @types/node
npm install -g eslint
npm install -g prettier

# Dashboard setup
cd Dashboard/ToolboxAI-Dashboard
npm install
cd ../..
```text
### 4. Database Setup

#### PostgreSQL with Docker

```bash
# Start PostgreSQL container
docker run -d \
  --name toolboxai-postgres \
  -e POSTGRES_USER=toolboxai \
  -e POSTGRES_PASSWORD=toolboxai123 \
  -e POSTGRES_DB=toolboxai_dev \
  -p 5432:5432 \
  -v toolboxai_pgdata:/var/lib/postgresql/data \
  postgres:15

# Verify connection
psql postgresql://toolboxai:toolboxai123@localhost:5432/toolboxai_dev

# Run migrations
alembic upgrade head
```text
#### Redis with Docker

```bash
# Start Redis container
docker run -d \
  --name toolboxai-redis \
  -p 6379:6379 \
  -v toolboxai_redis:/data \
  redis:7 redis-server --appendonly yes

# Verify connection
redis-cli ping
```text
### 5. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file
nano .env  # or use your preferred editor
```text
Required environment variables:

```env
# Database
DATABASE_URL=postgresql://toolboxai:toolboxai123@localhost:5432/toolboxai_dev
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# API Keys
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key  # Optional

# LMS Integration (Optional)
SCHOOLOGY_KEY=your-schoology-key
SCHOOLOGY_SECRET=your-schoology-secret
CANVAS_TOKEN=your-canvas-token
CANVAS_BASE_URL=https://your-school.instructure.com

# Server Configuration
API_HOST=127.0.0.1
API_PORT=8008
FLASK_PORT=5001
MCP_PORT=9876
DASHBOARD_PORT=3000

# Development
DEBUG=true
LOG_LEVEL=DEBUG
RELOAD=true

# Feature Flags
ENABLE_CACHING=true
ENABLE_RATE_LIMITING=false  # Disable for development
ENABLE_MONITORING=true
```text
## IDE Configuration

### VS Code Setup

#### 1. Install Required Extensions

```bash
# Install via command line
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-python.black-formatter
code --install-extension dbaeumer.vscode-eslint
code --install-extension esbenp.prettier-vscode
code --install-extension dsznajder.es7-react-js-snippets
code --install-extension bradlc.vscode-tailwindcss
code --install-extension ms-vscode.vscode-typescript-next
```text
#### 2. Workspace Settings

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv_clean/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.linting.flake8Args": ["--max-line-length=120"],
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "120"],
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],

  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true,
    "source.fixAll.eslint": true
  },

  "eslint.validate": ["javascript", "javascriptreact", "typescript", "typescriptreact"],

  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/node_modules": true,
    "**/.pytest_cache": true,
    "**/.mypy_cache": true
  },

  "typescript.preferences.importModuleSpecifier": "relative",
  "typescript.updateImportsOnFileMove.enabled": "always",

  "tailwindCSS.includeLanguages": {
    "typescript": "javascript",
    "typescriptreact": "javascript"
  }
}
```text
#### 3. Launch Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Server",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["server.main:app", "--reload", "--host", "127.0.0.1", "--port", "8008"],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "Flask Bridge",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/server/roblox_server.py",
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "MCP Server",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/mcp/server.py",
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "Dashboard Dev",
      "type": "node",
      "request": "launch",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev"],
      "cwd": "${workspaceFolder}/Dashboard/ToolboxAI-Dashboard",
      "console": "integratedTerminal"
    },
    {
      "name": "Debug Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["-v", "${file}"],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  ],
  "compounds": [
    {
      "name": "Full Stack",
      "configurations": ["FastAPI Server", "Flask Bridge", "MCP Server", "Dashboard Dev"],
      "stopAll": true
    }
  ]
}
```text
### PyCharm Setup

#### 1. Project Interpreter

1. Open Settings/Preferences (Cmd+, or Ctrl+Alt+S)
2. Navigate to Project > Python Interpreter
3. Click gear icon > Add
4. Choose "Existing environment"
5. Select `venv_clean/bin/python`

#### 2. Run Configurations

Create run configurations for:

1. **FastAPI Server**:
   - Script: `uvicorn`
   - Parameters: `server.main:app --reload --host 127.0.0.1 --port 8008`
   - Working directory: Project root

2. **Flask Bridge**:
   - Script path: `server/roblox_server.py`
   - Working directory: Project root

3. **MCP Server**:
   - Script path: `mcp/server.py`
   - Working directory: Project root

4. **Tests**:
   - Module name: `pytest`
   - Parameters: `-v tests/`
   - Working directory: Project root

## Development Workflows

### Starting Development Services

```bash
# Terminal 1: Database services
docker-compose up -d postgres redis

# Terminal 2: FastAPI server
source venv_clean/bin/activate
uvicorn server.main:app --reload --host 127.0.0.1 --port 8008

# Terminal 3: Flask bridge
source venv_clean/bin/activate
python server/roblox_server.py

# Terminal 4: MCP server
source venv_clean/bin/activate
python mcp/server.py

# Terminal 5: Dashboard
cd Dashboard/ToolboxAI-Dashboard
npm run dev
```text
### Using Make Commands

```bash
# Start all services
make dev

# Run tests
make test

# Format code
make format

# Lint code
make lint

# Clean build artifacts
make clean

# Database operations
make db-migrate
make db-upgrade
make db-downgrade
```text
### Using Docker Compose

```bash
# Start all services with Docker
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Reset everything
docker-compose down -v
```text
## Debugging

### Python Debugging

#### Using VS Code

1. Set breakpoints by clicking left of line numbers
2. Select "FastAPI Server" from debug dropdown
3. Press F5 to start debugging
4. Use Debug Console for interactive debugging

#### Using pdb

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or using Python 3.7+
breakpoint()
```text
#### Using ipdb (enhanced debugger)

```bash
# Install ipdb
pip install ipdb

# In code
import ipdb; ipdb.set_trace()
```text
### JavaScript/TypeScript Debugging

#### Browser DevTools

1. Open Chrome DevTools (F12)
2. Go to Sources tab
3. Set breakpoints in source files
4. Use Console for interactive debugging

#### VS Code Debugging

```json
// Add to launch.json
{
  "type": "chrome",
  "request": "launch",
  "name": "Debug Dashboard",
  "url": "http://localhost:3000",
  "webRoot": "${workspaceFolder}/Dashboard/ToolboxAI-Dashboard"
}
```text
### Database Debugging

```bash
# Connect to PostgreSQL
psql $DATABASE_URL

# Common queries for debugging
\dt                          # List tables
\d+ table_name              # Describe table
SELECT * FROM users LIMIT 10;  # Query data
```text
### API Debugging

#### Using curl

```bash
# Health check
curl http://localhost:8008/health

# API request with authentication
curl -X POST http://localhost:8008/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# Authenticated request
TOKEN="your-jwt-token"
curl http://localhost:8008/api/user/profile \
  -H "Authorization: Bearer $TOKEN"
```text
#### Using HTTPie

```bash
# Install HTTPie
pip install httpie

# Health check
http :8008/health

# Login
http POST :8008/api/auth/login email=test@example.com password=password123

# Authenticated request
http :8008/api/user/profile "Authorization: Bearer $TOKEN"
```text
## Testing

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=server --cov=agents --cov=mcp --cov-report=html

# Specific test file
pytest tests/unit/test_agents.py

# Specific test function
pytest tests/unit/test_agents.py::test_supervisor_agent

# With verbose output
pytest -v

# Stop on first failure
pytest -x

# Run only marked tests
pytest -m "not slow"
```text
### Writing Tests

#### Unit Test Example

```python
# tests/unit/test_example.py
import pytest
from unittest.mock import Mock, patch

class TestUserService:
    @pytest.fixture
    def user_service(self):
        return UserService()

    @pytest.mark.asyncio
    async def test_create_user(self, user_service):
        # Arrange
        user_data = {"email": "test@example.com", "name": "Test User"}

        # Act
        user = await user_service.create_user(user_data)

        # Assert
        assert user.email == "test@example.com"
        assert user.name == "Test User"
```text
#### Integration Test Example

```python
# tests/integration/test_api.py
import pytest
from httpx import AsyncClient

class TestAPIEndpoints:
    @pytest.mark.asyncio
    async def test_health_endpoint(self, async_client: AsyncClient):
        response = await async_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
```text
## Common Issues and Solutions

### Port Already in Use

```bash
# Find process using port
lsof -i :8008

# Kill process
kill -9 <PID>

# Or use different port
uvicorn server.main:app --port 8009
```text
### Module Import Errors

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or in VS Code, add to settings.json
"terminal.integrated.env.osx": {
  "PYTHONPATH": "${workspaceFolder}"
}
```text
### Database Connection Failed

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Restart PostgreSQL
docker restart toolboxai-postgres

# Check connection string
echo $DATABASE_URL
```text
### Node Modules Issues

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```text
### Virtual Environment Issues

```bash
# Recreate virtual environment
deactivate
rm -rf venv_clean
python -m venv venv_clean
source venv_clean/bin/activate
pip install -r requirements.txt
```text
## Performance Profiling

### Python Profiling

```python
# Using cProfile
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here
result = expensive_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```text
### API Performance Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8008/api/endpoint

# Using wrk
wrk -t12 -c400 -d30s http://localhost:8008/api/endpoint
```text
## Code Quality Tools

### Python Linting

```bash
# Run flake8
flake8 server/ agents/ mcp/

# Run mypy for type checking
mypy server/ agents/ mcp/

# Run black for formatting
black server/ agents/ mcp/

# Run isort for import sorting
isort server/ agents/ mcp/
```text
### JavaScript/TypeScript Linting

```bash
# Run ESLint
npm run lint

# Fix automatically
npm run lint:fix

# Run Prettier
npm run format
```text
## Git Workflow

### Branch Strategy

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Create bugfix branch
git checkout -b bugfix/issue-description

# Create hotfix branch
git checkout -b hotfix/critical-fix
```text
### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```text
### Commit Message Format

```text
type(scope): subject

body

footer
```text
Examples:

- `feat(agents): add new quiz generation agent`
- `fix(auth): resolve JWT token expiration issue`
- `docs(api): update endpoint documentation`
- `test(integration): add workflow tests`
- `refactor(database): optimize query performance`

## Useful Development Scripts

### Auto-reload Development

Create `scripts/dev.sh`:

```bash
#!/bin/bash
# Development script with auto-reload

# Function to cleanup on exit
cleanup() {
    echo "Stopping services..."
    kill $FASTAPI_PID $FLASK_PID $MCP_PID $DASHBOARD_PID 2>/dev/null
    exit 0
}

trap cleanup EXIT INT TERM

# Start services
echo "Starting FastAPI server..."
uvicorn server.main:app --reload --host 127.0.0.1 --port 8008 &
FASTAPI_PID=$!

echo "Starting Flask bridge..."
python server/roblox_server.py &
FLASK_PID=$!

echo "Starting MCP server..."
python mcp/server.py &
MCP_PID=$!

echo "Starting Dashboard..."
cd Dashboard/ToolboxAI-Dashboard && npm run dev &
DASHBOARD_PID=$!

echo "All services started. Press Ctrl+C to stop."
wait
```text
### Database Reset Script

Create `scripts/reset-db.sh`:

```bash
#!/bin/bash
# Reset development database

echo "Dropping existing database..."
docker exec toolboxai-postgres psql -U toolboxai -c "DROP DATABASE IF EXISTS toolboxai_dev;"

echo "Creating new database..."
docker exec toolboxai-postgres psql -U toolboxai -c "CREATE DATABASE toolboxai_dev;"

echo "Running migrations..."
alembic upgrade head

echo "Seeding database..."
python scripts/seed_db.py

echo "Database reset complete!"
```text
## Resources

### Documentation

- [Project README](../../README.md)
- [API Documentation](../03-api/README.md)
- [Architecture Overview](../02-architecture/system-design.md)

### External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Roblox Developer Hub](https://create.roblox.com/docs)

### Community

- GitHub Issues: Report bugs and request features
- Discord: Join development discussions
- Stack Overflow: Tag with `toolboxai`
