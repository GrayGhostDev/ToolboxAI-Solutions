---
title: Development Setup
description: Complete development environment setup for ToolboxAI Solutions
audience: developers
difficulty: intermediate
estimated_time: 45 minutes
last_updated: 2025-09-14
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
python -m venv .venv

# Activate environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

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
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
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
# Start all services
make dev

# Individual services
make start-backend
make start-frontend
make start-database
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
source .venv/bin/activate
```

## 📚 Additional Resources

- [API Documentation](../03-api/)
- [Architecture Overview](../02-architecture/)
- [Contributing Guide](../09-meta/contributing.md)
- [Troubleshooting Guide](../07-operations/troubleshooting.md)

---

**Need help?** Join our [Discord community](https://discord.gg/toolboxai) or [open an issue](https://github.com/toolboxai/solutions/issues).
