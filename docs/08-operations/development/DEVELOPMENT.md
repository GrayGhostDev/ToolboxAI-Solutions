# 🚀 Development Workflow Guide

**Last Updated**: September 24, 2025
**Docker Version**: 25.x / Compose v2
**Status**: Production-Ready with Modern Docker Infrastructure

## Overview

This guide provides comprehensive development workflows for ToolBoxAI following the Docker infrastructure modernization of September 24, 2025. It covers local development, Docker-based development, testing, and deployment procedures.

## 📋 Prerequisites

### Required Tools
- **Docker Desktop**: 4.26+ (includes Docker Engine 25.x)
- **Docker Compose**: v2.24+
- **Python**: 3.12+
- **Node.js**: 20+ (use .nvmrc for exact version)
- **Git**: 2.40+
- **VS Code/Cursor**: With recommended extensions

### System Requirements
- **macOS**: Enable VirtioFS in Docker Desktop for 2-3x performance boost
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 50GB available space
- **CPU**: 4+ cores recommended

## 🎯 Development Environments

### 1. Local Development (No Docker)

#### Initial Setup
```bash
# Clone repository
git clone https://github.com/toolboxai/toolboxai-solutions.git
cd toolboxai-solutions

# Create Python virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate    # On Windows

# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-ai.txt  # If using AI features

# Install Node dependencies
npm install  # Root workspace
npm -w apps/dashboard install  # Dashboard specific

# Setup environment
cp .env.example .env
# Edit .env with your local configuration
```

#### Start Services
```bash
# Terminal 1: Backend
source venv/bin/activate
make backend
# Or: uvicorn apps.backend.main:app --host 127.0.0.1 --port 8009 --reload

# Terminal 2: Dashboard
make dashboard
# Or: npm -w apps/dashboard run dev

# Terminal 3: Database (if not using Docker)
brew services start postgresql@15  # macOS
brew services start redis           # macOS
```

### 2. Docker Development (Recommended)

#### Initial Setup
```bash
# Navigate to project
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# Create environment file
cp .env.example .env

# Generate secure keys
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env
echo "DB_PASSWORD=$(openssl rand -base64 32)" >> .env
echo "REDIS_PASSWORD=$(openssl rand -base64 24)" >> .env

# For macOS: Enable VirtioFS
# Docker Desktop → Settings → Resources → File sharing → VirtioFS
```

#### Start Docker Stack
```bash
cd infrastructure/docker/compose

# Start all development services
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Or start specific services
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres redis
docker compose -f docker-compose.yml -f docker-compose.dev.yml up backend dashboard

# View logs
docker compose logs -f backend
docker compose logs -f dashboard

# Stop all services
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
```

#### Access Services
- **Dashboard**: http://localhost:5179
- **Backend API**: http://localhost:8009
- **API Docs**: http://localhost:8009/docs
- **Adminer (DB)**: http://localhost:8080
- **Redis Commander**: http://localhost:8081
- **Mailhog**: http://localhost:8025

### 3. Hybrid Development (Docker + Local Code)

Best of both worlds: Docker for services, local code for editing.

```bash
# Start only infrastructure services
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres redis mailhog

# Run backend locally with Docker services
export DATABASE_URL="postgresql://toolboxai:devpass2024@localhost:5432/toolboxai"
export REDIS_URL="redis://localhost:6379/0"
make backend

# Run dashboard locally
make dashboard
```

## 🔨 Development Workflows

### Feature Development

#### 1. Create Feature Branch
```bash
# Ensure you're on main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
```

#### 2. Development Cycle
```bash
# Start Docker services
cd infrastructure/docker/compose
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Make changes to code
# Backend changes auto-reload via uvicorn
# Frontend changes hot-reload via Vite

# Run tests frequently
make test           # All tests
pytest -xvs         # Python tests with verbose output
npm test            # Frontend tests
```

#### 3. Code Quality Checks
```bash
# Python
black apps/backend  # Format code
ruff check apps/backend  # Lint
mypy apps/backend  # Type checking

# TypeScript/React
npm -w apps/dashboard run lint
npm -w apps/dashboard run typecheck
npm -w apps/dashboard run format

# Security scan (if using Docker)
docker scout cves toolboxai/backend:latest
```

#### 4. Commit Changes
```bash
# Stage changes
git add .

# Commit with conventional message
git commit -m "feat: add new dashboard widget"
# Types: feat, fix, docs, style, refactor, test, chore

# Push to remote
git push origin feature/your-feature-name
```

### API Development

#### 1. Create New Endpoint
```python
# apps/backend/routers/your_feature.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from apps.backend.database import get_async_session
from apps.backend.models import YourModel
from apps.backend.schemas import YourSchema

router = APIRouter(prefix="/api/v1/your-feature", tags=["your-feature"])

@router.get("/", response_model=list[YourSchema])
async def get_items(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    # Implementation
    pass
```

#### 2. Register Router
```python
# apps/backend/main.py
from apps.backend.routers import your_feature

app.include_router(your_feature.router)
```

#### 3. Test Endpoint
```bash
# Using httpie
http GET localhost:8009/api/v1/your-feature \
    Authorization:"Bearer $TOKEN"

# Using curl
curl -H "Authorization: Bearer $TOKEN" \
    http://localhost:8009/api/v1/your-feature

# Interactive API docs
open http://localhost:8009/docs
```

### Database Development

#### 1. Create/Modify Models
```python
# database/models.py
from sqlalchemy import Column, String, Integer
from database.base import Base

class YourModel(Base):
    __tablename__ = "your_table"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
```

#### 2. Create Migration
```bash
# Generate migration
alembic revision --autogenerate -m "add your_table"

# Review generated migration
cat alembic/versions/latest_*.py

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

#### 3. Database Access via Docker
```bash
# PostgreSQL CLI
docker exec -it toolboxai-postgres psql -U toolboxai -d toolboxai

# Adminer web interface
open http://localhost:8080
# Server: postgres
# Username: toolboxai
# Password: devpass2024
# Database: toolboxai
```

### Frontend Development

#### 1. Component Development
```typescript
// apps/dashboard/src/components/YourComponent.tsx
import React from 'react';
import { Box, Typography } from '@mui/material';

interface YourComponentProps {
  title: string;
}

export const YourComponent: React.FC<YourComponentProps> = ({ title }) => {
  return (
    <Box>
      <Typography variant="h4">{title}</Typography>
    </Box>
  );
};
```

#### 2. State Management
```typescript
// apps/dashboard/src/store/slices/yourSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

const yourSlice = createSlice({
  name: 'your-feature',
  initialState: {},
  reducers: {
    setData: (state, action: PayloadAction<any>) => {
      // Update state
    }
  }
});
```

#### 3. API Integration
```typescript
// apps/dashboard/src/services/api.ts
export const yourFeatureApi = {
  getItems: async () => {
    const response = await apiClient.get('/your-feature');
    return response.data;
  }
};
```

## 🧪 Testing Workflows

### Unit Testing

#### Python Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps.backend --cov-report=html

# Run specific test file
pytest tests/unit/test_your_feature.py

# Run with markers
pytest -m unit  # Unit tests only
pytest -m integration  # Integration tests only

# Verbose output with immediate failures
pytest -xvs
```

#### Frontend Tests
```bash
# Run all tests
npm -w apps/dashboard test

# Run with coverage
npm -w apps/dashboard run test:coverage

# Watch mode for development
npm -w apps/dashboard run test:watch

# Run specific test
npm -w apps/dashboard test YourComponent.test.tsx
```

### Integration Testing

#### Docker-Based Testing
```bash
# Start test stack
docker compose -f docker-compose.yml -f docker-compose.test.yml up -d

# Run integration tests
docker compose exec backend pytest tests/integration

# Clean up
docker compose -f docker-compose.yml -f docker-compose.test.yml down -v
```

#### API Testing
```bash
# Start backend in test mode
TEST_MODE=true uvicorn apps.backend.main:app --reload

# Run API tests
pytest tests/api -v

# Or use test client
python -m tests.api.test_client
```

### End-to-End Testing

```bash
# Start full stack
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Run E2E tests
npm -w apps/dashboard run test:e2e

# Or with Playwright
npx playwright test
```

## 🔧 Debugging Workflows

### Backend Debugging

#### VS Code/Cursor Configuration
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "apps.backend.main:app",
        "--reload",
        "--host", "127.0.0.1",
        "--port", "8009"
      ],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

#### Interactive Debugging
```bash
# Install debugpy
pip install debugpy

# Start with debugger
python -m debugpy --listen 5678 --wait-for-client \
    -m uvicorn apps.backend.main:app --reload

# Connect VS Code debugger on port 5678
```

#### Docker Debugging
```bash
# View logs
docker compose logs -f backend

# Execute commands in container
docker compose exec backend bash
docker compose exec backend python -c "from apps.backend.main import app; print(app.routes)"

# Inspect container
docker compose exec backend sh
ls -la
cat /app/.env
```

### Frontend Debugging

#### Browser DevTools
1. Open Chrome DevTools (F12)
2. Use React Developer Tools extension
3. Use Redux DevTools for state inspection
4. Network tab for API calls
5. Console for errors

#### VS Code Debugging
```json
// .vscode/launch.json
{
  "type": "chrome",
  "request": "launch",
  "name": "Dashboard Debug",
  "url": "http://localhost:5179",
  "webRoot": "${workspaceFolder}/apps/dashboard"
}
```

#### Pusher Debugging
```javascript
// Enable Pusher debug mode
Pusher.logToConsole = true;

// Check Pusher dashboard
// https://dashboard.pusher.com
```

## 🚀 Deployment Workflows

### Build for Production

#### Docker Build
```bash
# Build production images
cd infrastructure/docker/compose
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# Tag images
docker tag toolboxai/backend:latest toolboxai/backend:v1.0.0
docker tag toolboxai/dashboard:latest toolboxai/dashboard:v1.0.0
```

#### Local Build
```bash
# Backend
cd apps/backend
pip install -r requirements.txt --target ./dist

# Dashboard
cd apps/dashboard
npm run build
# Output in dist/ directory
```

### Staging Deployment
```bash
# Build and push to staging
docker compose -f docker-compose.yml -f docker-compose.staging.yml build
docker push registry.toolboxai.com/backend:staging
docker push registry.toolboxai.com/dashboard:staging

# Deploy to staging server
ssh staging.toolboxai.com
cd /opt/toolboxai
docker compose pull
docker compose up -d
```

### Production Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed production deployment procedures.

## 🔄 Maintenance Workflows

### Daily Maintenance
```bash
# Check system health
docker compose ps
docker compose logs --tail=100

# Monitor resources
docker stats

# Check for security updates
docker scout cves
npm audit
pip-audit
```

### Weekly Maintenance
```bash
# Clean Docker resources
docker system prune -f
docker volume prune -f

# Update dependencies (in development)
npm update
pip list --outdated

# Run full test suite
make test
```

### Database Maintenance
```bash
# Backup database
docker exec toolboxai-postgres pg_dump -U toolboxai toolboxai > backup.sql

# Vacuum and analyze
docker exec toolboxai-postgres psql -U toolboxai -c "VACUUM ANALYZE;"

# Check table sizes
docker exec toolboxai-postgres psql -U toolboxai -c "\dt+"
```

## 📝 Documentation Workflows

### Update Documentation
```bash
# When adding features
1. Update README.md with new feature
2. Update API documentation (OpenAPI)
3. Add to CHANGELOG.md
4. Update CLAUDE.md if AI-relevant

# Generate API docs
python scripts/generate_openapi.py > docs/api/openapi.json
```

### Code Documentation
```python
# Use docstrings for all public functions
def your_function(param: str) -> dict:
    """
    Brief description of function.

    Args:
        param: Description of parameter

    Returns:
        Description of return value

    Raises:
        HTTPException: When something goes wrong
    """
    pass
```

## 🆘 Troubleshooting Common Issues

### Port Conflicts
```bash
# Find process using port
lsof -i :8009
lsof -i :5179

# Kill process
kill -9 <PID>

# Or use different ports
PORT=8010 uvicorn apps.backend.main:app --port 8010
PORT=5180 npm -w apps/dashboard run dev
```

### Docker Issues
```bash
# Reset Docker
docker compose down -v
docker system prune -a --volumes
docker compose up --build

# Check Docker daemon
docker version
docker info

# Restart Docker Desktop (macOS)
killall Docker && open /Applications/Docker.app
```

### Database Connection
```bash
# Check PostgreSQL
docker compose exec postgres pg_isready
docker compose logs postgres

# Reset database
docker compose exec postgres psql -U toolboxai -c "DROP DATABASE toolboxai;"
docker compose exec postgres psql -U toolboxai -c "CREATE DATABASE toolboxai;"
alembic upgrade head
```

### Node/NPM Issues
```bash
# Clear caches
npm cache clean --force
rm -rf node_modules package-lock.json
npm install

# Use correct Node version
nvm use
node --version  # Should match .nvmrc
```

### Python/Pip Issues
```bash
# Recreate virtual environment
deactivate
rm -rf venv
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📚 Resources

### Internal Documentation
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment
- [SECURITY.md](../../09-reference/security/templates/SECURITY_POLICY_TEMPLATE.md) - Security guidelines
- [API Documentation](http://localhost:8009/docs) - Interactive API docs
- [CLAUDE.md](../CLAUDE.md) - AI assistant context

### External Resources
- [Docker Documentation](https://docs.docker.com)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [React Documentation](https://react.dev)
- [PostgreSQL Documentation](https://www.postgresql.org/docs)

### Development Tools
- [VS Code](https://code.visualstudio.com)
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [Postman](https://www.postman.com) - API testing
- [TablePlus](https://tableplus.com) - Database GUI

## 🎯 Best Practices

### Code Quality
1. **Write tests first** (TDD when possible)
2. **Use type hints** in Python
3. **Use TypeScript** for frontend
4. **Follow conventional commits**
5. **Keep PRs small and focused**

### Security
1. **Never commit secrets**
2. **Use environment variables**
3. **Validate all inputs**
4. **Sanitize all outputs**
5. **Keep dependencies updated**

### Performance
1. **Profile before optimizing**
2. **Use caching strategically**
3. **Optimize database queries**
4. **Lazy load frontend components**
5. **Monitor production metrics**

### Collaboration
1. **Document your code**
2. **Review PRs thoroughly**
3. **Communicate blockers early**
4. **Share knowledge in team meetings**
5. **Update documentation as you go**

---

*Development Workflow Guide v1.0.0*
*Updated for Docker Infrastructure Modernization 2025-09-24*
