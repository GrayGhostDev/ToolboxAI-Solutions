# ToolBoxAI-Solutions - Claude Code Guide

**Last Updated:** November 13, 2025
**Project Type:** Full-Stack AI-Powered Educational Platform
**Status:** Production-Ready

---

## 🎯 Project Overview

**ToolBoxAI-Solutions** is an AI-powered educational platform with Roblox integration, designed to provide interactive learning experiences for K-12 students.

### Key Features
- **AI-Powered Learning:** Integrated with GPT-4.1 and LangChain for intelligent tutoring
- **Roblox Integration:** Seamless connection with Roblox games for educational experiences
- **Real-Time Collaboration:** Pusher Channels for live interactions
- **Role-Based Access:** Student, Educator, Parent, and Administrator roles
- **Progress Tracking:** Comprehensive analytics and gamification
- **Secure & Compliant:** COPPA, FERPA, GDPR, and SOC 2 Type 2 compliant

---

## 🤖 GitHub Copilot Agents & Triggers

### Available Specialized Agents

**Location:** `.github/agents/`

ToolBoxAI has **6 specialized GitHub Copilot agents** for different development tasks:

1. **Issue Resolution Agent** (`my-agent.agent.md`)
   - **Triggers**: Issues, PRs, bug labels
   - **Use for**: Bug fixes, issue resolution, code review

2. **Backend Development Specialist** (`backend-specialist.agent.md`)
   - **Triggers**: `apps/backend/**/*.py`, labels: `backend`, `api`
   - **Use for**: FastAPI, SQLAlchemy, Celery, LangChain development

3. **Frontend Development Specialist** (`frontend-specialist.agent.md`)
   - **Triggers**: `apps/dashboard/**/*.{tsx,ts}`, labels: `frontend`, `ui`
   - **Use for**: React 19, Mantine UI, TypeScript, Redux development

4. **AI Agent Development Specialist** (`ai-agent-specialist.agent.md`)
   - **Triggers**: `apps/backend/agents/**/*.py`, labels: `ai`, `agents`
   - **Use for**: LangChain, LangGraph, OpenAI agent development

5. **DevOps & Infrastructure Specialist** (`devops-specialist.agent.md`)
   - **Triggers**: `infrastructure/**/*`, labels: `deployment`, `docker`
   - **Use for**: Docker, TeamCity, Render, Vercel deployment

6. **Documentation Specialist** (`documentation-specialist.agent.md`)
   - **Triggers**: `docs/**/*.md`, labels: `documentation`
   - **Use for**: Technical writing, API docs, user guides

### How to Invoke Agents

**In code comments:**
```python
# @copilot using backend-specialist
# Create async FastAPI endpoint for user creation with Pydantic validation
```

**In PRs/Issues:**
```markdown
@copilot using frontend-specialist
Create a Mantine Card component for displaying quiz results
```

**In terminal:**
```bash
gh copilot suggest "using ai-agent-specialist create LangGraph workflow"
```

---

## 📚 Documentation Location Rules

### IMPORTANT: Documentation Guidelines

**Claude Code Memory:**
- ✅ **All documentation in Markdown files** must be placed in the correct `/docs` location
- ❌ **NO documentation files in root directory** (except CLAUDE.md and README.md)
- ✅ **Only create status and summary documents** upon successful completion of a complete Phase or Task
- ❌ **Stop creating summary documents** unless they go in `/docs/11-reports/` folder

### Documentation Structure
All documentation is centralized in `/docs/` with the following structure:
- `/docs/01-getting-started/` - Setup and onboarding
- `/docs/06-features/` - Feature-specific documentation
- `/docs/08-operations/` - DevOps, deployment, CI/CD
- `/docs/10-security/` - Security policies and guides
- `/docs/11-reports/` - Status reports and summaries
- `/docs/FILE_RELOCATION_MAP.md` - Track moved files
- `/docs/README.md` - Documentation index

**Reference:** See `/docs/README.md` for complete documentation structure.

---

## 🧹 Recent Infrastructure Cleanup (November 9, 2025)

**MAJOR CONSOLIDATION COMPLETED**

### Summary
- **57 files deleted** + all Python cache cleaned
- **16,073 lines removed** from codebase
- **Significantly improved IDE performance** (reduced file scanning overhead)

### What Changed

#### GitHub Workflows: 40 → 5 (87.5% reduction)
**New consolidated workflows with modern versions (Node 22, pnpm 9, basedpyright):**
- `main-ci-cd.yml` - Complete CI/CD pipeline (lint, type-check, test, build, docker)
- `deploy.yml` - Deployment to Vercel (frontend) and Render (backend)
- `security.yml` - Security scanning (Trivy, CodeQL, dependency audits)
- `e2e-tests.yml` - End-to-end testing with Playwright
- `infrastructure.yml` - Database migrations, Roblox sync, TeamCity triggers

**Deleted:** 35 old/redundant workflow files

#### Docker Compose: 15 → 4 (73% reduction)
**Essential files kept:**
- `docker-compose.yml` - Base production configuration
- `docker-compose.dev.yml` - Development overrides
- `docker-compose.prod.yml` - Production overrides
- `docker-compose.monitoring.yml` - Grafana/Prometheus/Jaeger stack

**Deleted:** celery, collab, complete, core, fast-dev, phase2, redis-ha, secrets-dev, secure, swarm, teamcity

#### Dockerfiles: 21 → 11 (48% reduction)
**Canonical files documented in** `infrastructure/docker/dockerfiles/CURRENT_DOCKERFILES.md`

**Deleted:** backend-optimized, backend-production-2025, backend-simple, celery-optimized, celery-production-2025, dashboard-fixed, dashboard-production-2025, dashboard.Dockerfile (old), dev.Dockerfile, test-dashboard-simple

#### Python Cache Cleanup
- Removed all `__pycache__` directories
- Removed all `.pyc` and `.pyo` files
- Removed all `.DS_Store` files (macOS metadata)

### Benefits
- ✅ **IDE Performance:** Dramatically faster indexing and file search
- ✅ **Developer Experience:** Clear which files to use, no confusion
- ✅ **CI/CD Reliability:** Modern versions prevent build failures
- ✅ **Maintenance:** Reduced from managing 70+ config files to ~20

### Where to Find Things Now
- **Workflows:** `.github/workflows/` (5 files - see above)
- **Docker Compose:** `infrastructure/docker/compose/` (4 files - see above)
- **Dockerfiles:** `infrastructure/docker/dockerfiles/` (11 files - see CURRENT_DOCKERFILES.md)
- **File Moves:** See `/docs/FILE_RELOCATION_MAP.md` for documentation relocations

---

## 🏗️ Technology Stack

### Backend
- **Framework:** FastAPI (Python 3.12)
- **Database:** PostgreSQL 16 with asyncpg
- **Cache:** Redis 7
- **Type Checking:** BasedPyright (NOT mypy)
- **Testing:** pytest
- **API Documentation:** OpenAPI/Swagger

### Frontend
- **Framework:** React 19.1.0
- **Build Tool:** Vite 6
- **Language:** TypeScript 5.9.2
- **UI Library:** Mantine UI v8 (NOT Material-UI)
- **State Management:** Redux Toolkit
- **Testing:** Vitest

### AI/ML Stack
- **LLM:** OpenAI GPT-4.1
- **Framework:** LangChain v1.0
- **Agent System:** Custom multi-agent system

### Infrastructure
- **Containerization:** Docker 25.x with BuildKit
- **Orchestration:** Docker Compose
- **CI/CD:** TeamCity Cloud + GitHub Actions
- **Monitoring:** OpenTelemetry + Prometheus
- **Secrets:** Hashicorp Vault (hvac client)
- **Real-Time:** Pusher Channels (NOT Socket.IO)

---

## 📁 Directory Structure

```
ToolBoxAI-Solutions/
├── apps/
│   ├── backend/           # FastAPI backend (port 8009)
│   │   ├── api/          # API routes
│   │   ├── core/         # Core functionality
│   │   ├── models/       # Pydantic models
│   │   ├── services/     # Business logic
│   │   └── main.py       # Application entry
│   └── dashboard/        # React dashboard (port 5179)
│       ├── src/          # Source code
│       ├── public/       # Static assets
│       └── package.json  # Dependencies
├── docs/                 # ✅ ALL DOCUMENTATION HERE
│   ├── 01-getting-started/
│   ├── 06-features/
│   ├── 08-operations/
│   ├── 10-security/
│   ├── 11-reports/      # Status reports ONLY
│   ├── FILE_RELOCATION_MAP.md
│   └── README.md        # Documentation index
├── infrastructure/
│   ├── docker/
│   │   └── compose/     # Docker Compose configurations
│   ├── kubernetes/      # K8s manifests (if used)
│   └── teamcity/        # TeamCity configurations
├── scripts/             # Utility scripts
│   ├── deployment/      # Deployment scripts
│   ├── maintenance/     # Maintenance tasks
│   ├── testing/         # Test utilities
│   └── database/        # Database scripts
├── tests/               # Test suites
│   ├── backend/         # Backend tests
│   ├── api/             # API tests
│   ├── diagnostics/     # Diagnostic tests
│   └── workflows/       # Workflow tests
├── venv/                # ✅ Python virtual environment (NOT .venv or venv_clean)
├── .env                 # Active config (not tracked)
├── .env.example         # Config template (tracked)
├── requirements.txt     # Python dependencies
├── requirements-dev.txt # Development dependencies
├── requirements-docs.txt# Documentation dependencies
├── pnpm-workspace.yaml  # PNPM workspace config
├── package.json         # Root package.json
├── CLAUDE.md            # This file
└── README.md            # Project README
```

---

## ⚙️ Development Setup

### Prerequisites
```bash
# Required
Python 3.12+
Node.js 22 LTS
pnpm 9.15.0
PostgreSQL 16
Redis 7
Docker 25.x

# Optional
Hashicorp Vault (for secrets management)
TeamCity (for CI/CD)
```

### Quick Start

```bash
# 1. Clone and navigate
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions

# 2. Python environment
python3 -m venv venv          # Use 'venv' NOT '.venv'
source venv/bin/activate      # On macOS/Linux
pip install -r requirements.txt

# 3. Frontend dependencies
pnpm install                  # Install all workspaces

# 4. Environment configuration
cp .env.example .env
# Edit .env with your configuration
# See docs/10-security/ENV_FILES_DOCUMENTATION.md

# 5. Database setup
# Start PostgreSQL and Redis (via Docker or local)
# Run migrations if needed

# 6. Start development servers

# Backend (Terminal 1):
cd apps/backend
uvicorn main:app --reload --port 8009

# Dashboard (Terminal 2):
pnpm --filter @toolboxai/dashboard dev
# Runs on http://localhost:5179
```

---

## 🔧 Common Development Tasks

### Running Tests

```bash
# Python/Backend tests
pytest                        # All tests
pytest -m unit               # Unit tests only
pytest -m integration        # Integration tests only
pytest --cov                 # With coverage

# Type checking (USE BASEDPYRIGHT, NOT MYPY!)
basedpyright .               # Python type checking

# Frontend tests
pnpm -w dashboard test       # Dashboard tests
pnpm -w dashboard run test:coverage  # With coverage

# Frontend type checking
pnpm -w dashboard run typecheck
```

### Code Quality

```bash
# Python linting
flake8 apps/backend
black apps/backend --check   # Format check
black apps/backend           # Auto-format

# Frontend linting
pnpm -w dashboard run lint
pnpm -w dashboard run lint:fix
```

### Database Operations

```bash
# Create migration
cd apps/backend
alembic revision -m "description"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Docker Operations

```bash
# Full stack with Docker
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f dashboard

# Rebuild
docker-compose up -d --build

# Stop
docker-compose down
```

---

## 📦 Dependencies Management

### Python Dependencies

**Main File:** `requirements.txt`
- Contains ALL production dependencies
- Install with: `pip install -r requirements.txt`

**Development:** `requirements-dev.txt`
- Testing, linting, type-checking tools
- Install with: `pip install -r requirements-dev.txt`

**Documentation:** `requirements-docs.txt`
- Sphinx, mkdocs, documentation generators
- Install with: `pip install -r requirements-docs.txt`

**IMPORTANT:**
- ✅ All dependencies consolidated in main requirements.txt
- ❌ Do NOT create requirements-essential.txt, requirements-missing.txt, etc.
- ❌ These temporary files have been removed

### Node/PNPM Dependencies

**Workspace Structure:**
```yaml
# pnpm-workspace.yaml
packages:
  - 'apps/*'
  - 'packages/*'
```

**Commands:**
```bash
pnpm install                  # Install all workspaces
pnpm -w dashboard [command]  # Run in dashboard workspace
pnpm -w backend [command]    # Run in backend workspace (if exists)
```

---

## 🔐 Environment Variables

### Configuration Files

**Active Configurations (NOT tracked in git):**
- `.env` - Main environment configuration
- `.env.local` - Local development overrides
- `.env.production` - Production configuration

**Templates (tracked in git):**
- `.env.example` - Main configuration template
- `.env.local.example` - Local override template
- `.env.supabase.local.example` - Supabase-specific template

### Security Best Practices

1. **Never commit actual .env files** - Only .example files
2. **Use environment-specific configs** - .env.local for dev, .env.production for prod
3. **Document all variables** - Keep .example files updated
4. **Rotate credentials regularly** - Especially for production

**Reference:** See `/docs/10-security/ENV_FILES_DOCUMENTATION.md` for complete guide.

---

## 🚀 Deployment

### Backend Deployment (Render)

```bash
# Deploy to Render
cd scripts/deployment
./deploy-render.sh

# Verify deployment
python3 verify_deployment.sh
```

### Frontend Deployment (Vercel)

```bash
# Deploy to Vercel
cd scripts/deployment
./deploy-to-vercel.sh

# Or use Vercel CLI
vercel --prod
```

### Docker Deployment

```bash
# Build and push images
cd scripts/deployment
./build_and_push_images.py

# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

**Reference:** See `/docs/08-operations/deployment/` for detailed guides.

---

## 🧪 Testing Strategy

### Test Organization

```
tests/
├── backend/           # Backend unit/integration tests
├── api/               # API endpoint tests
├── accessibility/     # A11y tests
├── agents/            # AI agent tests
├── database/          # Database tests
├── diagnostics/       # Diagnostic utilities
└── workflows/         # End-to-end workflow tests
```

### Running Specific Tests

```bash
# Backend API tests
pytest tests/api/

# Database tests
pytest tests/database/

# Agent system tests
pytest tests/agents/

# Specific test file
pytest tests/backend/test_auth.py

# Specific test function
pytest tests/backend/test_auth.py::test_login_success
```

### Test Coverage Goals
- **Unit Tests:** >80% coverage
- **Integration Tests:** Critical paths covered
- **E2E Tests:** Main user workflows

---

## 🐛 Troubleshooting

### Common Issues

#### "Module not found" errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### Port already in use
```bash
# Find process using port
lsof -i :8009          # Backend port
lsof -i :5179          # Dashboard port

# Kill process
kill -9 <PID>
```

#### Database connection errors
```bash
# Check PostgreSQL is running
pg_isready

# Check Redis is running
redis-cli ping

# Verify .env database credentials
cat .env | grep DATABASE_URL
```

#### Type checking issues
```bash
# Use BasedPyright, NOT mypy
basedpyright .

# NOT this:
# mypy .  # ❌ Don't use mypy
```

#### PNPM workspace issues
```bash
# Clear node_modules and reinstall
rm -rf node_modules apps/*/node_modules
pnpm install

# Verify workspace configuration
pnpm list --depth=0
```

---

## 📝 Important Reminders

### For Claude Code AI Assistant

1. **Virtual Environment:**
   - ✅ Use `venv/` directory
   - ❌ NOT `.venv` or `venv_clean`

2. **Type Checking:**
   - ✅ Use `basedpyright`
   - ❌ NOT `mypy`

3. **UI Library:**
   - ✅ Mantine UI v8
   - ❌ NOT Material-UI (MUI)

4. **Real-Time:**
   - ✅ Pusher Channels
   - ❌ NOT Socket.IO

5. **Package Manager:**
   - ✅ Frontend: PNPM v9.15.0
   - ✅ Backend: pip
   - ❌ NOT npm or yarn for frontend

6. **Ports:**
   - Backend: 8009 (NOT 8000)
   - Dashboard: 5179 (NOT 3000 or 5173)

7. **Documentation:**
   - ✅ All docs in `/docs/` directory
   - ❌ No markdown files in root (except CLAUDE.md, README.md)
   - ✅ Status reports in `/docs/11-reports/` only

8. **Requirements Files:**
   - ✅ Use `requirements.txt` (main dependencies)
   - ✅ Use `requirements-dev.txt` (development)
   - ✅ Use `requirements-docs.txt` (documentation)
   - ❌ Do NOT create requirements-essential.txt, requirements-missing.txt

9. **Git Workflow:**
   - Use conventional commits
   - Sign commits if configured
   - Follow branch naming conventions in docs

10. **File Relocation:**
    - Always check `/docs/FILE_RELOCATION_MAP.md` for moved files
    - Update paths in code when files are relocated

---

## 🔗 Quick Links

### Essential Documentation
- **Documentation Index:** `/docs/README.md`
- **File Relocation Map:** `/docs/FILE_RELOCATION_MAP.md`
- **Environment Security:** `/docs/10-security/ENV_FILES_DOCUMENTATION.md`
- **Cleanup Report:** `/docs/11-reports/PROJECT_CLEANUP_COMPLETION_2025-11-09.md`

### Development Guides
- **Getting Started:** `/docs/01-getting-started/`
- **API Documentation:** `/docs/04-api/`
- **Feature Docs:** `/docs/06-features/`
- **Operations:** `/docs/08-operations/`

### External Resources
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **React Docs:** https://react.dev
- **Mantine UI:** https://mantine.dev
- **LangChain:** https://python.langchain.com

---

## 🎓 Best Practices

### Code Organization
- Keep components small and focused
- Use TypeScript strict mode
- Follow SOLID principles
- Write tests for new features

### Security
- Never commit secrets or credentials
- Use environment variables for configuration
- Implement proper input validation
- Follow OWASP security guidelines

### Performance
- Use async/await for I/O operations
- Implement caching where appropriate
- Optimize database queries
- Monitor application metrics

### Documentation
- Document public APIs
- Keep README files updated
- Write clear commit messages
- Update CLAUDE.md when architecture changes

---

## 📊 Project Status

**Last Major Cleanup:** November 9, 2025
- 56 files reorganized
- 22,574 lines of obsolete code removed
- Documentation fully centralized
- Requirements files consolidated
- Environment files properly configured

**Next Steps:**
- Continue development
- Maintain clean organization
- Follow documentation guidelines
- Keep dependencies updated

---

## 📧 Support

**Documentation Issues:**
- Check `/docs/README.md` for index
- Check `/docs/FILE_RELOCATION_MAP.md` for moved files
- See `/docs/08-operations/troubleshooting/`

**Development Questions:**
- Review `/docs/01-getting-started/`
- Check feature-specific docs in `/docs/06-features/`
- Review architecture docs in `/docs/02-architecture/`

---

**ToolBoxAI-Solutions Development Team**
*Building the future of education through AI and technology*

**Last Updated:** November 9, 2025
**Version:** 1.0.0
**Next Review:** December 9, 2025
