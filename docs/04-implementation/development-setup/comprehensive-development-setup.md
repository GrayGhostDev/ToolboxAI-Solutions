---
title: Development Setup
description: Complete development environment setup for ToolboxAI Solutions
audience: developers
difficulty: intermediate
estimated_time: 45 minutes
last_updated: 2025-09-16
prerequisites:
  - Python 3.11+
  - Node.js 20+
  - Docker 24+
  - Git 2.40+
---

# Development Setup Guide

This guide will help you set up a complete development environment for ToolboxAI Solutions.

## 🛠️ Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | macOS 12+, Ubuntu 20.04+, Windows 11 | macOS 14+, Ubuntu 22.04+ |
| RAM | 8GB | 16GB+ |
| Storage | 20GB | 50GB+ |
| CPU | 4 cores | 8+ cores |

### Required Software

```bash
# Check your versions
python --version    # Python 3.11+
node --version      # Node.js 20+
docker --version    # Docker 24+
git --version       # Git 2.40+
```

## 🚀 Quick Setup

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/toolboxai/solutions.git
cd solutions

# Run the setup script
./scripts/setup-dev.sh

# Start development environment
make dev
```

### Option 2: Manual Setup

#### 1. Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

#### 2. Node.js Environment

```bash
# Install dependencies
npm install

# Install global tools
npm install -g @types/node typescript eslint prettier

# Setup dashboard
cd apps/dashboard
npm install
cd ../..
```

#### 3. Database Setup

```bash
# Start PostgreSQL with Docker
docker run -d \
  --name toolboxai-postgres \
  -e POSTGRES_USER=toolboxai \
  -e POSTGRES_PASSWORD=dev_password \
  -e POSTGRES_DB=toolboxai_dev \
  -p 5432:5432 \
  -v toolboxai_pgdata:/var/lib/postgresql/data \
  postgres:15

# Start Redis
docker run -d \
  --name toolboxai-redis \
  -p 6379:6379 \
  -v toolboxai_redis:/data \
  redis:7

# Run migrations
alembic upgrade head
```

#### 4. Docker Development Environment

For a complete containerized development environment:

```bash
# Start all services with Docker Compose
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d

# Or start services individually
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d postgres redis
docker-compose -f infrastructure/docker/docker-compose.dev.yml up fastapi-main
docker-compose -f infrastructure/docker/docker-compose.dev.yml up dashboard-frontend

# View logs for debugging
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs -f dashboard-frontend
```

**Environment Variables for Docker (.env):**
```bash
# Database Configuration
POSTGRES_DB=toolboxai_dev
POSTGRES_USER=toolboxai
POSTGRES_PASSWORD=dev_password
DATABASE_URL=postgresql://toolboxai:dev_password@postgres:5432/toolboxai_dev

# Redis Configuration
REDIS_PASSWORD=dev_redis_pass
REDIS_URL=redis://:dev_redis_pass@redis:6379

# API Keys
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Pusher Configuration (for realtime features)
PUSHER_ENABLED=true
PUSHER_APP_ID=your-pusher-app-id
PUSHER_KEY=your-pusher-key
PUSHER_SECRET=your-pusher-secret
PUSHER_CLUSTER=us2

# Development Flags
DEBUG=true
ENVIRONMENT=development
ENABLE_GAMIFICATION=true
ENABLE_ANALYTICS=true
```

**Dashboard Docker Configuration:**

The dashboard runs in a containerized Vite development server with hot-reload:

- **Port**: 5179 (mapped from container)
- **Base Image**: node:22-alpine
- **Hot Reload**: Enabled via volume mounts
- **Environment**: Uses Docker service names for backend communication

**Key Environment Variables:**
```bash
VITE_API_BASE_URL=http://fastapi-main:8009    # Inter-container communication
VITE_PUSHER_KEY=${PUSHER_KEY}
VITE_PUSHER_CLUSTER=${PUSHER_CLUSTER}
VITE_PUSHER_AUTH_ENDPOINT=http://fastapi-main:8009/api/v1/pusher/auth
```

## 🔧 IDE Configuration

### VS Code (Recommended)

#### Extensions

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "ms-python.isort",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "bradlc.vscode-tailwindcss",
    "ms-vscode.vscode-json"
  ]
}
```

#### Settings

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true,
    "source.fixAll.eslint": true
  }
}
```

## 🧪 Testing

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=core --cov=apps --cov-report=html

# Specific test file
pytest tests/unit/test_agents.py

# Watch mode
pytest-watch

# Frontend tests
cd apps/dashboard && npm test
```

### Writing Tests

```python
# Example test structure
import pytest
from unittest.mock import Mock, patch

class TestAgentSystem:
    @pytest.fixture
    def agent_config(self):
        return AgentConfig(
            name="test_agent",
            agent_type="content",
            llm_model="gpt-3.5-turbo"
        )

    @pytest.mark.asyncio
    async def test_agent_creation(self, agent_config):
        agent = ContentAgent(agent_config)
        assert agent.name == "test_agent"
        assert agent.agent_type == "content"
```

## 🐛 Debugging

### Python Debugging

```python
# Using debugpy (VS Code)
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()

# Using pdb
import pdb; pdb.set_trace()

# Using breakpoint() (Python 3.7+)
breakpoint()
```

### Frontend Debugging

```javascript
// Browser DevTools
console.log('Debug info:', data);

// VS Code debugging
// Set breakpoints and use F5 to start debugging
```

## 📊 Performance Profiling

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
```

### API Performance Testing

```bash
# Using wrk
wrk -t12 -c400 -d30s http://localhost:8008/api/health

# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8008/api/health
```

## 🔄 Development Workflow

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/your-feature-name
```

### Code Quality

```bash
# Format code
black .
isort .

# Lint code
flake8 .
mypy .

# Frontend
npm run lint
npm run format
```

## 🚀 Deployment

### Local Development

```bash
# Start all services (native)
make dev

# Individual services (native)
make start-backend
make start-frontend
make start-database
```

#### Docker Development

```bash
# Start all services with Docker
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d

# Build and restart specific service
docker-compose -f infrastructure/docker/docker-compose.dev.yml up --build dashboard-frontend

# Scale services for load testing
docker-compose -f infrastructure/docker/docker-compose.dev.yml up --scale fastapi-main=2
```

### Production Deployment

```bash
# Build and deploy
make build
make deploy

# Using Docker
docker-compose up -d
```

## 🆘 Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Find process using port
lsof -i :8008

# Kill process
kill -9 <PID>
```

**Database connection failed:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Restart database
docker restart toolboxai-postgres
```

**Module import errors:**
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or activate virtual environment
source venv/bin/activate
```

**Docker Development Issues:**

**Container startup failures:**
```bash
# Check service health and dependencies
docker-compose -f infrastructure/docker/docker-compose.dev.yml ps
docker-compose -f infrastructure/docker/docker-compose.dev.yml logs dashboard-frontend

# Check if ports are available
lsof -i :5179
```

**Hot-reload not working in dashboard container:**
```bash
# Ensure volume mounts are correct
docker-compose -f infrastructure/docker/docker-compose.dev.yml config

# Restart dashboard service
docker-compose -f infrastructure/docker/docker-compose.dev.yml restart dashboard-frontend

# Rebuild with no cache if needed
docker-compose -f infrastructure/docker/docker-compose.dev.yml build --no-cache dashboard-frontend
```

**Inter-container communication failures:**
```bash
# Test connectivity between containers
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec dashboard-frontend ping fastapi-main

# Check network configuration
docker network ls
docker network inspect $(docker network ls -q -f name=toolboxai)
```

**Dashboard test failures (below 85% threshold):**
```bash
# Run tests inside container
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec dashboard-frontend npm test

# Check test coverage
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec dashboard-frontend npm run test:coverage

# Debug failing tests
docker-compose -f infrastructure/docker/docker-compose.dev.yml exec dashboard-frontend npm test -- --verbose
```

## 📚 Additional Resources

- [API Documentation](../../03-api/)
- [Architecture Overview](../../02-architecture/)
- [Contributing Guide](../../09-meta/contributing/contributing.md)
- [Troubleshooting Guide](../../07-operations/troubleshooting/)

---

**Need help?** Join our [Discord community](https://discord.gg/toolboxai) or [open an issue](https://github.com/toolboxai/solutions/issues).

---

*Last Updated: 2025-09-16*
*Version: 2.1.0*
*Compliance: COPPA, FERPA, GDPR, SOC 2 Type 2*
