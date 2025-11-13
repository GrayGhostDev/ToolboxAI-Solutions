# ToolBoxAI-Solutions - GitHub Copilot Instructions

**Project:** ToolBoxAI-Solutions - AI-Powered Educational Platform with Roblox Integration  
**Last Updated:** November 13, 2025  
**Version:** 2.0.0  
**Status:** Production-Ready

---

## 🎯 Project Overview

ToolBoxAI-Solutions is a comprehensive AI-powered educational platform designed for K-12 students with seamless Roblox integration, real-time collaboration, and advanced AI tutoring capabilities.

### Key Capabilities
- **AI-Powered Learning:** GPT-4.1 + LangChain v1.0 multi-agent system for intelligent tutoring
- **Roblox Integration:** Bidirectional sync with Roblox games for immersive learning
- **Real-Time Collaboration:** Pusher Channels for live interactions (NOT Socket.IO)
- **Role-Based Access Control:** Student, Educator, Parent, Administrator roles
- **Progress Analytics:** Comprehensive tracking with gamification
- **Enterprise Security:** COPPA, FERPA, GDPR, SOC 2 Type 2 compliant

---

## 🏗️ Technology Stack

### Backend Stack
```yaml
Framework: FastAPI 0.121.1
Runtime: Python 3.12+
Server: Uvicorn (ASGI) / Gunicorn (production)
Database: PostgreSQL 16 (asyncpg driver)
Cache: Redis 7
Task Queue: Celery 5.5.3 + Redis broker
Type Checking: BasedPyright (NOT mypy)
Testing: pytest + pytest-asyncio
API Spec: OpenAPI 3.1 / Swagger UI
```

### Frontend Stack
```yaml
Framework: React 19.1.0
Build Tool: Vite 6
Language: TypeScript 5.9.2
UI Library: Mantine UI v8 (NOT Material-UI)
State: Redux Toolkit + RTK Query
Styling: PostCSS + Tailwind CSS
Testing: Vitest + React Testing Library
E2E: Playwright
```

### AI/ML Stack
```yaml
LLM Provider: OpenAI GPT-4.1
Framework: LangChain 1.0.5 (v1 API)
Orchestration: LangGraph 1.0.3
Agent System: Custom multi-agent architecture
Observability: LangSmith 0.4.42
Tokenization: tiktoken 0.12.0
Vector Store: Supabase pgvector
```

### Infrastructure & DevOps
```yaml
Containerization: Docker 25.x + BuildKit
Orchestration: Docker Compose (dev/prod/monitoring)
CI/CD: TeamCity Cloud (on Docker) + GitHub Actions
Package Manager: pnpm 9.15.0 (frontend), pip (backend)
Monitoring: Docker-based (OpenTelemetry + Prometheus + Grafana + Jaeger)
Logging: Structured logging with Sentry
Secrets: Hashicorp Vault (hvac client)
Real-Time: Pusher Channels 3.3.2
Deployment: 
  - Backend: Render (FastAPI app + Celery workers)
  - Frontend: Vercel (React dashboard)
  - Database: Supabase (PostgreSQL 16 + pgvector + Realtime)
  - Monitoring: Docker Compose (self-hosted)
  - CI/CD: TeamCity Cloud (Docker-based agents)
```

### External Integrations
```yaml
Authentication: Clerk (OAuth/OIDC) - Complete auth solution
Database: Supabase (PostgreSQL 16 + Realtime + Storage + Auth)
Roblox: Custom Lua SDK + Rojo sync
Payments: Stripe 8.0.0
Email: SendGrid 6.11.0
SMS: Twilio 9.4.0
```

---

## 📁 Repository Structure

```
ToolBoxAI-Solutions/
├── .github/                      # GitHub configurations
│   ├── workflows/                # CI/CD pipelines (5 workflows)
│   │   ├── main-ci-cd.yml       # Main CI/CD (lint, test, build, docker)
│   │   ├── deploy.yml           # Deployment (Vercel + Render)
│   │   ├── security.yml         # Security scanning (Trivy, CodeQL)
│   │   ├── e2e-tests.yml        # Playwright E2E tests
│   │   └── infrastructure.yml   # DB migrations, Roblox sync
│   ├── agents/                   # Custom GitHub agents
│   │   └── my-agent.agent.md    # Issue resolution agent
│   ├── ISSUE_TEMPLATE/          # Issue templates
│   ├── PROJECT_TEMPLATES/       # Project board templates
│   ├── CONTRIBUTING.md          # Contribution guidelines
│   ├── PULL_REQUEST_TEMPLATE.md # PR template
│   └── instructions.md          # This file
│
├── apps/                         # Monorepo applications
│   ├── backend/                 # FastAPI backend (port 8009)
│   │   ├── api/                 # API routes
│   │   ├── core/                # Core functionality
│   │   ├── models/              # Pydantic models
│   │   ├── services/            # Business logic
│   │   ├── agents/              # AI agent implementations
│   │   ├── middleware/          # FastAPI middleware
│   │   ├── main.py              # Application entry
│   │   └── startup.py           # Startup logic
│   │
│   └── dashboard/               # React dashboard (port 5179)
│       ├── src/
│       │   ├── components/      # React components (Mantine UI)
│       │   ├── features/        # Feature modules
│       │   ├── store/           # Redux store
│       │   ├── hooks/           # Custom hooks
│       │   ├── api/             # RTK Query API
│       │   └── utils/           # Utilities
│       ├── public/              # Static assets
│       ├── vite.config.ts       # Vite configuration
│       └── package.json         # Dashboard dependencies
│
├── infrastructure/               # Infrastructure as Code
│   ├── docker/
│   │   ├── compose/             # Docker Compose files (4 files)
│   │   │   ├── docker-compose.yml           # Base config
│   │   │   ├── docker-compose.dev.yml       # Dev overrides
│   │   │   ├── docker-compose.prod.yml      # Prod overrides
│   │   │   └── docker-compose.monitoring.yml # Grafana/Prometheus
│   │   ├── dockerfiles/         # Dockerfiles (11 canonical)
│   │   │   ├── backend.Dockerfile           # FastAPI backend
│   │   │   ├── dashboard-2025.Dockerfile    # React dashboard
│   │   │   ├── celery-worker.Dockerfile     # Celery worker
│   │   │   ├── celery-beat.Dockerfile       # Celery scheduler
│   │   │   ├── agents.Dockerfile            # AI agents
│   │   │   ├── mcp.Dockerfile               # MCP server
│   │   │   ├── roblox-sync.Dockerfile       # Roblox sync
│   │   │   └── nginx-production-2025.Dockerfile
│   │   └── scripts/             # Docker helper scripts
│   ├── kubernetes/              # K8s manifests (if needed)
│   ├── terraform/               # Terraform IaC
│   ├── teamcity/                # TeamCity configurations
│   └── vault/                   # Vault configurations
│
├── docs/                         # ✅ ALL DOCUMENTATION HERE
│   ├── 01-getting-started/      # Setup guides
│   ├── 02-architecture/         # System architecture
│   ├── 03-api/                  # API documentation
│   ├── 04-implementation/       # Implementation guides
│   ├── 05-features/             # Feature documentation
│   ├── 06-user-guides/          # Role-specific guides
│   ├── 08-operations/           # DevOps & operations
│   │   ├── docker/              # Docker guides
│   │   ├── deployment/          # Deployment procedures
│   │   ├── ci-cd/               # CI/CD documentation
│   │   ├── monitoring/          # Monitoring setup
│   │   └── github-projects/     # Project management
│   ├── 10-security/             # Security documentation
│   ├── 11-reports/              # Status reports ONLY
│   ├── FILE_RELOCATION_MAP.md   # File movement tracking
│   └── README.md                # Documentation index
│
├── scripts/                      # Utility scripts
│   ├── deployment/              # Deployment scripts
│   ├── database/                # Database utilities
│   ├── testing/                 # Test utilities
│   └── maintenance/             # Maintenance tasks
│
├── tests/                        # Test suites
│   ├── backend/                 # Backend tests
│   ├── api/                     # API tests
│   ├── agents/                  # Agent tests
│   ├── database/                # Database tests
│   ├── diagnostics/             # Diagnostic tests
│   └── workflows/               # E2E workflow tests
│
├── venv/                         # ✅ Python virtual environment (NOT .venv)
├── node_modules/                # Node dependencies
├── .env                         # Active config (NOT tracked)
├── .env.example                 # Config template (tracked)
├── requirements.txt             # Python dependencies
├── requirements-dev.txt         # Dev dependencies
├── requirements-docs.txt        # Docs dependencies
├── pnpm-workspace.yaml          # PNPM workspace config
├── package.json                 # Root package.json
├── CLAUDE.md                    # Claude AI assistant guide
└── README.md                    # Project README
```

---

## 🚀 Development Environment Setup

### Prerequisites
```bash
# Required
Python 3.12+                # Backend runtime
Node.js 22 LTS              # Frontend runtime
pnpm 9.15.0                 # Frontend package manager
PostgreSQL 16               # Primary database
Redis 7                     # Cache & broker
Docker 25.x                 # Containerization
Git 2.40+                   # Version control

# Optional
Hashicorp Vault             # Secrets management
TeamCity                    # CI/CD (alternative to GitHub Actions)
```

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/GrayGhostDev/ToolboxAI-Solutions.git
cd ToolBoxAI-Solutions

# 2. Python environment setup
python3 -m venv venv        # ✅ Use 'venv' NOT '.venv'
source venv/bin/activate    # macOS/Linux
# OR
venv\Scripts\activate       # Windows

pip install -r requirements.txt
pip install -r requirements-dev.txt

# 3. Frontend dependencies
pnpm install                # Install all workspaces

# 4. Environment configuration
cp .env.example .env
# Edit .env with your configuration
# See docs/10-security/ENV_FILES_DOCUMENTATION.md

# 5. Database setup
# Option A: Use Supabase (recommended - matches production)
# 1. Create free Supabase project at supabase.com
# 2. Get connection string from Supabase dashboard
# 3. Add to .env: DATABASE_URL=postgresql://...

# Option B: Docker PostgreSQL (for offline dev)
docker-compose -f infrastructure/docker/compose/docker-compose.yml \
               -f infrastructure/docker/compose/docker-compose.dev.yml up -d postgres redis

# Option C: Local installation
# Install PostgreSQL 16 and Redis 7
# Create database: toolboxai_dev
# Install pgvector extension: CREATE EXTENSION vector;

# 6. Run migrations (if needed)
cd apps/backend
alembic upgrade head

# 7. Start development servers

# Terminal 1 - Backend
cd apps/backend
uvicorn main:app --reload --port 8009
# Backend runs on http://localhost:8009
# Swagger UI: http://localhost:8009/docs

# Terminal 2 - Dashboard
pnpm --filter @toolboxai/dashboard dev
# Dashboard runs on http://localhost:5179
```

---

## 🔧 Common Development Tasks

### Backend Development

```bash
# Activate virtual environment
source venv/bin/activate

# Run backend server
cd apps/backend
uvicorn main:app --reload --port 8009

# Run tests
pytest                              # All tests
pytest -m unit                      # Unit tests only
pytest -m integration               # Integration tests
pytest --cov                        # With coverage
pytest tests/api/test_auth.py       # Specific file

# Type checking (USE BASEDPYRIGHT, NOT MYPY)
basedpyright .                      # ✅ Correct
# mypy .                            # ❌ Don't use this

# Code quality
black apps/backend --check          # Format check
black apps/backend                  # Auto-format
flake8 apps/backend                 # Linting
ruff check apps/backend             # Fast linter

# Database migrations
alembic revision -m "description"   # Create migration
alembic upgrade head                # Apply migrations
alembic downgrade -1                # Rollback one
alembic current                     # Show current version

# Celery worker
celery -A apps.backend.celery_app worker -l info

# Celery beat scheduler
celery -A apps.backend.celery_app beat -l info

# Flower monitoring
celery -A apps.backend.celery_app flower --port=5555
```

### Frontend Development

```bash
# Dashboard development
pnpm --filter @toolboxai/dashboard dev

# Build dashboard
pnpm --filter @toolboxai/dashboard build

# Preview production build
pnpm --filter @toolboxai/dashboard preview

# Tests
pnpm --filter @toolboxai/dashboard test              # Run tests
pnpm --filter @toolboxai/dashboard run test:coverage # With coverage
pnpm --filter @toolboxai/dashboard run test:ui       # UI mode

# Linting
pnpm --filter @toolboxai/dashboard lint              # Check
pnpm --filter @toolboxai/dashboard run lint:fix      # Auto-fix

# Type checking
pnpm --filter @toolboxai/dashboard run typecheck

# Format
pnpm --filter @toolboxai/dashboard run format        # Check
pnpm --filter @toolboxai/dashboard run format:write  # Auto-fix
```

### E2E Testing

```bash
# Install Playwright browsers
pnpm run test:e2e:install

# Run E2E tests
pnpm run test:e2e                   # Headless
pnpm run test:e2e:headed            # Headed mode
pnpm run test:e2e:ui                # Interactive UI mode
pnpm run test:e2e:debug             # Debug mode

# View report
pnpm run test:e2e:report
```

### Docker Operations

```bash
# Full stack development
docker-compose -f infrastructure/docker/compose/docker-compose.yml \
               -f infrastructure/docker/compose/docker-compose.dev.yml up -d

# Production build
docker-compose -f infrastructure/docker/compose/docker-compose.yml \
               -f infrastructure/docker/compose/docker-compose.prod.yml up -d

# With monitoring stack
docker-compose -f infrastructure/docker/compose/docker-compose.yml \
               -f infrastructure/docker/compose/docker-compose.monitoring.yml up -d

# View logs
docker-compose -f infrastructure/docker/compose/docker-compose.yml logs -f backend
docker-compose -f infrastructure/docker/compose/docker-compose.yml logs -f dashboard

# Rebuild specific service
docker-compose -f infrastructure/docker/compose/docker-compose.yml build backend

# Stop all services
docker-compose -f infrastructure/docker/compose/docker-compose.yml down

# Clean up (remove volumes)
docker-compose -f infrastructure/docker/compose/docker-compose.yml down -v

# Build individual Dockerfile
docker build -f infrastructure/docker/dockerfiles/backend.Dockerfile -t toolboxai-backend:latest .
docker build -f infrastructure/docker/dockerfiles/dashboard-2025.Dockerfile -t toolboxai-dashboard:latest .
```

---

## 🤖 AI Agent System

### Platform Agents (Backend - LangChain/LangGraph)

The platform uses a **multi-agent system** built with LangChain v1.0 and LangGraph:

```python
# Agent Types (apps/backend/agents/)
ContentGenerationAgent      # Creates educational content
AssessmentAgent             # Generates quizzes and assessments
TutoringAgent               # Provides personalized tutoring
ProgressAnalysisAgent       # Analyzes student progress
RobloxIntegrationAgent      # Manages Roblox sync
FeedbackAgent               # Provides feedback on submissions
```

### Agent Implementation Location
```
apps/backend/agents/
├── __init__.py
├── base.py                 # Base agent class
├── content_generator.py    # Content generation
├── assessment.py           # Assessment creation
├── tutoring.py             # Tutoring interactions
├── progress.py             # Progress analysis
├── roblox.py               # Roblox integration
└── feedback.py             # Feedback generation
```

### Agent Configuration

```python
# apps/backend/agents/base.py
from langchain.agents import AgentExecutor
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph

class BaseAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4-1106-preview",
            temperature=0.7
        )
        self.graph = StateGraph()
        
    async def execute(self, input_data):
        # Agent execution logic
        pass
```

### Custom Tools for Agents

```
apps/backend/tools.py              # Shared agent tools
apps/backend/agents/tools/         # Agent-specific tools
```

Example tools:
- Content database query tool
- Roblox API integration tool
- Student progress retrieval tool
- Quiz generation tool
- Feedback formatting tool

---

## 🤖 GitHub Copilot Agents

### Available Copilot Agents

ToolBoxAI-Solutions has **specialized GitHub Copilot agents** to assist with development tasks. These agents have deep knowledge of the codebase and can help with specific areas.

**Location:** `.github/agents/`

#### 1. **Issue Resolution Agent** (`my-agent.agent.md`)
**Triggers**: 
- Issue comments: `@copilot resolve this issue`
- PR comments: `@copilot review this PR`
- Commit messages: Issues with `bug`, `fix`, or `enhancement` labels

**Capabilities**:
- Analyzes issues and provides fixes
- Creates PR with fixes
- Runs tests and validates
- Updates documentation
- Follows conventional commits

**When to use**:
- Bug fixes needed
- Feature implementation
- Code improvements
- Issue resolution

#### 2. **Backend Development Specialist** (`backend-specialist.agent.md`)
**Triggers**:
- File paths: `apps/backend/**/*.py`
- PR labels: `backend`, `api`, `database`
- Keywords: `fastapi`, `sqlalchemy`, `celery`, `langchain`

**Capabilities**:
- FastAPI endpoint creation
- Database migrations with Alembic
- Celery task development
- LangChain agent implementation
- API documentation (OpenAPI)
- Async/await patterns
- Pydantic v2 validation

**When to use**:
- Creating new API endpoints
- Database schema changes
- Background task implementation
- AI agent development
- Backend bug fixes

**Example**:
```
@copilot using backend-specialist create a new FastAPI endpoint 
for creating quiz questions with Pydantic validation
```

#### 3. **Frontend Development Specialist** (`frontend-specialist.agent.md`)
**Triggers**:
- File paths: `apps/dashboard/**/*.{tsx,ts,jsx,js}`
- PR labels: `frontend`, `ui`, `dashboard`
- Keywords: `react`, `mantine`, `typescript`, `redux`

**Capabilities**:
- React 19 component development
- Mantine UI v8 integration (NOT Material-UI)
- TypeScript strict mode
- Redux Toolkit + RTK Query
- Clerk authentication
- Pusher real-time integration
- Vitest testing

**When to use**:
- Creating UI components
- State management setup
- API integration
- Authentication flows
- Real-time features

**Example**:
```
@copilot using frontend-specialist create a Mantine Card component 
for displaying student progress with TypeScript
```

#### 4. **AI Agent Development Specialist** (`ai-agent-specialist.agent.md`)
**Triggers**:
- File paths: `apps/backend/agents/**/*.py`
- PR labels: `ai`, `agents`, `langchain`
- Keywords: `langchain`, `langgraph`, `openai`, `llm`

**Capabilities**:
- LangChain v1.0 agent development
- LangGraph workflow design
- Custom tool creation
- Prompt engineering
- Vector store integration (Supabase pgvector)
- LangSmith tracing
- Token optimization

**When to use**:
- Creating new AI agents
- Designing agent workflows
- Building custom tools
- Optimizing prompts
- Debugging agents

**Example**:
```
@copilot using ai-agent-specialist create a new LangGraph workflow 
for content review with multiple agents
```

#### 5. **DevOps & Infrastructure Specialist** (`devops-specialist.agent.md`)
**Triggers**:
- File paths: `infrastructure/**/*`, `.github/workflows/**/*`
- PR labels: `infrastructure`, `deployment`, `docker`
- Keywords: `docker`, `teamcity`, `render`, `vercel`

**Capabilities**:
- Docker Compose configuration
- Dockerfile optimization
- TeamCity pipeline setup
- Render deployment
- Vercel configuration
- Monitoring stack (Prometheus, Grafana)
- Database migrations

**When to use**:
- Deployment issues
- Docker configuration
- CI/CD pipeline changes
- Monitoring setup
- Infrastructure changes

**Example**:
```
@copilot using devops-specialist optimize the backend Dockerfile 
for faster builds
```

#### 6. **Documentation Specialist** (`documentation-specialist.agent.md`)
**Triggers**:
- File paths: `docs/**/*.md`, `*.md`
- PR labels: `documentation`
- Keywords: `docs`, `documentation`, `readme`

**Capabilities**:
- Technical documentation
- API documentation (OpenAPI)
- User guides
- Code examples
- Troubleshooting guides
- Maintaining docs structure

**When to use**:
- Writing documentation
- Updating API specs
- Creating user guides
- Fixing broken links
- Organizing docs

**Example**:
```
@copilot using documentation-specialist create a user guide for 
educators on creating quiz content
```

### How to Use GitHub Copilot Agents

#### In Code Comments
```python
# @copilot using backend-specialist
# Create an async FastAPI endpoint for uploading student assignments
# with file validation and Supabase storage integration
```

#### In Pull Requests
```markdown
@copilot using frontend-specialist review this PR and check for:
- Proper TypeScript types
- Mantine UI best practices
- Accessibility compliance
```

#### In Issues
```markdown
@copilot using ai-agent-specialist 

We need a new agent that can analyze student writing and provide
personalized feedback. It should:
1. Use GPT-4 for analysis
2. Store feedback in database
3. Send notifications via Pusher
```

#### In Terminal (GitHub CLI)
```bash
# Get help from agent
gh copilot suggest "using backend-specialist create Celery task for email sending"

# Generate code
gh copilot generate "using frontend-specialist create TypeScript interface for User"
```

### Agent Selection Guide

| Task Type | Use This Agent |
|-----------|----------------|
| FastAPI endpoints | Backend Development Specialist |
| React components | Frontend Development Specialist |
| LangChain agents | AI Agent Development Specialist |
| Docker/deployment | DevOps & Infrastructure Specialist |
| Writing docs | Documentation Specialist |
| Bug fixes | Issue Resolution Agent |
| Code review | Issue Resolution Agent |

### Best Practices

1. **Be Specific**: Provide context and requirements
2. **Use Constraints**: Mention tech stack, patterns to follow
3. **Include Examples**: Reference existing code when helpful
4. **Test Suggestions**: Always verify agent-generated code
5. **Iterate**: Refine requests based on results

### Agent Limitations

- Agents have knowledge up to their training cutoff
- Always review generated code for security
- Test thoroughly before merging
- Agents follow repository standards but may need corrections
- Complex tasks may need breaking down into steps

---

## 🔐 Security & Authentication

### Authentication Architecture

**ToolBoxAI-Solutions uses Clerk as the complete authentication solution.**

```yaml
Provider: Clerk (SaaS - clerk.com)
Protocol: OAuth 2.0 / OIDC
Features:
  - Social OAuth: Google, GitHub, Microsoft
  - Email/Password: With email verification
  - Magic Links: Passwordless authentication
  - Multi-Factor Auth: TOTP, SMS via Twilio
  - Session Management: JWT-based
  - User Management: Admin dashboard
  - Webhooks: User lifecycle events

Integration:
  Frontend: @clerk/clerk-react
  Backend: clerk-sdk-python
  JWT Validation: Automatic via Clerk middleware
  Token Storage: HTTP-only cookies (secure)
  Session Duration: Configurable (default 7 days)
```

### Authentication Flow

```
1. User visits dashboard → Clerk component loads
2. User signs in → Clerk handles authentication
3. Clerk issues JWT → Stored in HTTP-only cookie
4. Frontend includes JWT → In Authorization header
5. Backend validates JWT → Via Clerk middleware
6. Backend checks Clerk → Verifies user session
7. Backend checks database → Loads user profile
8. Request processed → Returns data to frontend
```

### Role-Based Access Control (RBAC)

```yaml
Roles Managed in: Clerk Dashboard + Database
Available Roles:
  - student: Default role for learners
  - educator: Teachers and content creators
  - parent: Parent/guardian accounts
  - admin: Platform administrators

Role Mapping:
  - Clerk: Stores role as metadata
  - Backend: Syncs role to database
  - Frontend: Shows UI based on role
  - API: Enforces role-based permissions
```

### Environment Variables Security

**CRITICAL RULES:**
1. ✅ **NEVER commit `.env` files** - Only `.env.example`
2. ✅ **Use environment-specific configs** - `.env.local` for dev, `.env.production` for prod
3. ✅ **Rotate credentials regularly** - Especially for production
4. ✅ **Use Vault for sensitive secrets** - In production environments

**Configuration Files:**
```
.env                    # ❌ NOT tracked (active config)
.env.local              # ❌ NOT tracked (local overrides)
.env.production         # ❌ NOT tracked (production config)
.env.example            # ✅ Tracked (template)
.env.local.example      # ✅ Tracked (template)
```

**Reference:** See `/docs/10-security/ENV_FILES_DOCUMENTATION.md`

### Security Compliance

```yaml
Standards:
  - COPPA: Children's Online Privacy Protection Act
  - FERPA: Family Educational Rights and Privacy Act
  - GDPR: General Data Protection Regulation
  - SOC 2 Type 2: Security compliance

Implementation:
  - OWASP Top 10 protection
  - Dependency scanning (Dependabot + Trivy)
  - Code scanning (CodeQL)
  - Secret scanning (GitHub native)
  - Container scanning (Trivy)
  - Security headers (FastAPI middleware)
  - Rate limiting (Redis-backed)
  - Input validation (Pydantic v2)
```

---

## 🔄 CI/CD Pipelines

### Primary CI/CD: TeamCity Cloud

**ToolBoxAI-Solutions uses TeamCity Cloud as the primary CI/CD platform**, running on Docker-based build agents.

**Location:** `infrastructure/teamcity/`

**TeamCity Pipelines:**
```yaml
Build Configurations:
  - Main Build Pipeline: Full CI/CD workflow
  - Docker Image Builds: Multi-arch container builds
  - Integration Tests: Comprehensive test suite
  - Security Scanning: Trivy + dependency audits
  - Performance Tests: Load testing and benchmarks
  - Deployment Pipeline: Automated deployments to Render + Vercel

Build Agents:
  - Docker-based agents: Consistent build environments
  - Auto-scaling: Scales based on build queue
  - Cached dependencies: Faster build times

Deployment Targets:
  - Backend → Render (FastAPI + Celery)
  - Frontend → Vercel (React dashboard)
  - Database migrations → Supabase
  - Monitoring → Docker Compose stack
```

**Why TeamCity:**
- Superior Docker integration
- Advanced build artifact management
- Comprehensive test reporting
- Enterprise-grade security
- Build chain dependencies
- Flexible agent scaling

### GitHub Actions Workflows (Secondary)

**Location:** `.github/workflows/`

**GitHub Actions complement TeamCity** for specific tasks:

#### 1. Main CI/CD (`main-ci-cd.yml`) - Pull Request Validation
```yaml
Triggers: pull_request (pre-merge validation)
Node: 22 LTS
pnpm: 9.15.0
Python: 3.12
Type Checker: BasedPyright (NOT mypy)

Jobs:
  - lint-backend          # Flake8, black, ruff
  - lint-frontend         # ESLint, prettier
  - type-check-backend    # BasedPyright
  - type-check-frontend   # TypeScript
  - test-backend          # pytest (unit + integration)
  - test-frontend         # Vitest
  - build-backend         # FastAPI build validation
  - build-frontend        # Vite build validation

Note: Full deployments handled by TeamCity Cloud
```

#### 2. Deployment (`deploy.yml`) - Manual Deployments Only
```yaml
Triggers: workflow_dispatch (manual trigger only)

Jobs:
  - deploy-frontend       # Manual Vercel deployment
  - deploy-backend        # Manual Render deployment
  - notify-sentry         # Release tracking

Note: Automated deployments handled by TeamCity Cloud
      This workflow is for emergency/manual deployments only
```

#### 3. Security Scanning (`security.yml`)
```yaml
Triggers: schedule (daily), pull_request

Jobs:
  - trivy-scan            # Container vulnerabilities
  - codeql-analysis       # Code scanning
  - dependency-review     # Dependency vulnerabilities
  - secret-scan           # Secret detection
```

#### 4. E2E Tests (`e2e-tests.yml`)
```yaml
Triggers: schedule (nightly), workflow_dispatch

Jobs:
  - playwright-tests      # Browser testing
  - visual-regression     # Visual diffs
  - performance-tests     # Lighthouse
```

#### 5. Infrastructure (`infrastructure.yml`)
```yaml
Triggers: workflow_dispatch, schedule

Jobs:
  - database-migrations   # Alembic migrations
  - roblox-sync           # Roblox asset sync
  - teamcity-trigger      # TeamCity jobs
  - vault-rotation        # Secret rotation
```

### TeamCity Cloud Architecture

**Location:** `infrastructure/teamcity/`

**Build Agent Configuration:**
```yaml
Agent Type: Docker-based
Base Images:
  - Python 3.12 agent (backend builds)
  - Node.js 22 agent (frontend builds)
  - Multi-tool agent (full-stack builds)
  
Agent Features:
  - Pre-installed: Docker, pnpm, Python, Node.js, PostgreSQL client
  - Volume mounts: Persistent dependency caches
  - Network access: Render API, Vercel API, Supabase, Clerk
  - Secrets: Vault integration for secure credentials
```

**Build Chains:**
```
1. Code Quality Gate
   ↓ (lint, type-check, security scan)
2. Unit Tests
   ↓ (pytest, vitest)
3. Integration Tests
   ↓ (API tests, database tests, agent tests)
4. Docker Image Build
   ↓ (multi-arch: amd64, arm64)
5. Deploy to Staging
   ↓ (Render staging + Vercel preview)
6. E2E Tests
   ↓ (Playwright on staging)
7. Deploy to Production
   ↓ (Render production + Vercel production)
8. Post-Deployment Tests
   └→ (Health checks, smoke tests)
```

**Deployment Targets from TeamCity:**
- **Backend:** Render Web Services API
  - FastAPI application
  - Celery workers
  - Celery beat scheduler
- **Frontend:** Vercel Deployment API
  - Production deployment
  - Preview deployments (PRs)
- **Database:** Supabase Migrations API
  - Alembic migrations
  - Schema updates
- **Monitoring:** Docker Compose on dedicated server
  - Prometheus, Grafana, Jaeger
  - Auto-deployed on config changes

---

## 📊 Testing Strategy

### Test Organization

```
tests/
├── backend/              # Backend unit/integration tests
│   ├── test_auth.py
│   ├── test_api.py
│   ├── test_models.py
│   └── test_services.py
├── api/                  # API endpoint tests
│   ├── test_content.py
│   ├── test_users.py
│   └── test_roblox.py
├── agents/               # AI agent tests
│   ├── test_content_agent.py
│   ├── test_tutoring_agent.py
│   └── test_assessment_agent.py
├── database/             # Database tests
│   ├── test_migrations.py
│   └── test_models.py
├── accessibility/        # A11y tests (WCAG 2.1 AA)
├── diagnostics/          # Diagnostic utilities
└── workflows/            # E2E workflow tests
```

### Testing Commands

```bash
# Backend Tests
pytest                                    # All tests
pytest -m unit                            # Unit tests only
pytest -m integration                     # Integration tests
pytest -m slow                            # Slow tests
pytest --cov                              # With coverage
pytest --cov-report=html                  # HTML coverage report
pytest -k "test_auth"                     # Pattern matching
pytest tests/backend/test_auth.py::test_login  # Specific test

# Frontend Tests
pnpm --filter @toolboxai/dashboard test                # All tests
pnpm --filter @toolboxai/dashboard run test:coverage   # With coverage
pnpm --filter @toolboxai/dashboard run test:ui         # Interactive UI

# E2E Tests
pnpm run test:e2e                         # All E2E tests
pnpm run test:e2e:ui                      # Interactive mode
pnpm run test:e2e:debug                   # Debug mode

# Agent Tests
pytest tests/agents/ -v                   # All agent tests
pytest tests/agents/test_tutoring_agent.py  # Specific agent
```

### Coverage Goals
```yaml
Unit Tests: >80% coverage
Integration Tests: Critical paths covered
E2E Tests: Main user workflows
API Tests: All endpoints covered
Agent Tests: All agent types covered
```

---

## 🚢 Deployment Architecture

### Deployment Overview

```yaml
Primary Deployment Method: TeamCity Cloud (automated)
Manual Deployment Method: GitHub Actions + CLI tools (emergency)

Deployment Targets:
  Backend: Render
  Frontend: Vercel  
  Database: Supabase
  Monitoring: Docker Compose (self-hosted)
  Authentication: Clerk (SaaS)
```

### Backend Deployment (Render)

**Primary Method: TeamCity Cloud**
```yaml
TeamCity automatically deploys to Render using:
  - Render API integration
  - Automated on: main branch merges
  - Services deployed:
    * FastAPI web service (apps/backend)
    * Celery worker service
    * Celery beat scheduler service
```

**Manual Deployment (Emergency/Testing):**
```bash
# Via Render CLI
cd apps/backend
render deploy

# Or via script
pnpm run deploy:backend

# Or via API
curl -X POST \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/$RENDER_SERVICE_ID/deploys
```

**Render Configuration:**
```yaml
Environment Variables (set in Render dashboard):
  # Database & Cache
  - DATABASE_URL: <Supabase connection string>
  - REDIS_URL: <Redis connection string>
  
  # AI/ML
  - OPENAI_API_KEY: <OpenAI API key>
  - LANGCHAIN_API_KEY: <LangSmith API key>
  
  # Authentication
  - CLERK_SECRET_KEY: <Clerk backend secret>
  - CLERK_PUBLISHABLE_KEY: <Clerk public key>
  
  # External Services
  - PUSHER_APP_ID: <Pusher app ID>
  - PUSHER_KEY: <Pusher key>
  - PUSHER_SECRET: <Pusher secret>
  - PUSHER_CLUSTER: <Pusher cluster>
  - STRIPE_SECRET_KEY: <Stripe secret key>
  - SENDGRID_API_KEY: <SendGrid API key>
  - TWILIO_ACCOUNT_SID: <Twilio account>
  - TWILIO_AUTH_TOKEN: <Twilio token>
  
  # Monitoring
  - SENTRY_DSN: <Sentry DSN>
  
  # Secrets Management (optional)
  - VAULT_ADDR: <Vault server address>
  - VAULT_TOKEN: <Vault access token>

Render Services:
  1. toolboxai-backend (Web Service)
     - Region: Oregon (us-west)
     - Plan: Standard
     - Auto-deploy: Yes (from main)
     - Health check: /health
     
  2. toolboxai-celery-worker (Background Worker)
     - Region: Oregon (us-west)
     - Plan: Standard
     - Command: celery -A apps.backend.celery_app worker -l info
     
  3. toolboxai-celery-beat (Cron Job)
     - Region: Oregon (us-west)
     - Plan: Starter
     - Command: celery -A apps.backend.celery_app beat -l info
```

### Frontend Deployment (Vercel)

**Primary Method: TeamCity Cloud**
```yaml
TeamCity automatically deploys to Vercel using:
  - Vercel API integration
  - Automated on: main branch merges
  - Preview deployments: All PRs
  - Production URL: toolboxai.vercel.app (or custom domain)
```

**Manual Deployment (Emergency/Testing):**
```bash
# Via Vercel CLI
cd apps/dashboard
vercel --prod

# Or via script
pnpm run deploy:frontend

# Preview deployment
vercel
```

**Vercel Configuration:**
```yaml
Environment Variables (set in Vercel dashboard):
  # API & Backend
  - VITE_API_URL: https://toolboxai-backend.onrender.com
  
  # Authentication (Clerk)
  - VITE_CLERK_PUBLISHABLE_KEY: <Clerk public key>
  
  # Real-Time (Pusher)
  - VITE_PUSHER_KEY: <Pusher public key>
  - VITE_PUSHER_CLUSTER: <Pusher cluster>
  
  # Roblox Integration
  - VITE_ROBLOX_UNIVERSE_ID: <Roblox universe ID>
  - VITE_ROBLOX_API_KEY: <Roblox API key>
  
  # Monitoring
  - VITE_SENTRY_DSN: <Sentry frontend DSN>

Build Settings:
  Framework: Vite
  Build Command: pnpm --filter @toolboxai/dashboard build
  Output Directory: apps/dashboard/dist
  Install Command: pnpm install
  Node Version: 22 LTS
  
Deployment:
  Auto-deploy: Yes (main branch)
  Preview Deployments: Yes (all PRs)
  Production Branch: main
  Custom Domains: Configure in Vercel dashboard
```

### Database Deployment (Supabase)

**Supabase is the managed database provider** - no deployment needed for the database itself.

**Database Migrations:**
```bash
# Automated via TeamCity on main branch merge
# Or manually:
cd apps/backend
alembic upgrade head

# TeamCity executes migrations before backend deployment
```

**Supabase Configuration:**
```yaml
Database:
  Type: PostgreSQL 16
  Extensions: pgvector (for AI embeddings)
  Features:
    - Realtime: WebSocket subscriptions
    - Storage: File uploads
    - Auth: Optional (using Clerk instead)
    - Row Level Security (RLS): Enabled
    
Connection:
  Pooler: Supavisor (connection pooling)
  Max Connections: 500
  Pool Mode: Transaction
  
Access:
  Direct Connection: For migrations
  Pooled Connection: For application
```

### Monitoring Deployment (Docker Compose)

**Monitoring stack runs on dedicated server via Docker Compose:**

```bash
# Deploy monitoring stack
cd infrastructure/docker/compose
docker-compose -f docker-compose.yml \
               -f docker-compose.monitoring.yml up -d

# Services included:
# - Prometheus: Metrics collection
# - Grafana: Visualization dashboards
# - Jaeger: Distributed tracing
# - Node Exporter: System metrics
# - Cadvisor: Container metrics
```

**Monitoring Services:**
```yaml
Prometheus:
  Port: 9090
  Scrape Targets:
    - Render backend (/metrics)
    - Vercel edge functions
    - Supabase Postgres exporter
    - Redis exporter
    
Grafana:
  Port: 3000
  Dashboards:
    - System Overview
    - Application Performance
    - Database Metrics
    - AI Agent Performance
    - Celery Tasks
    - Error Tracking
    
Jaeger:
  Port: 16686
  Features:
    - OpenTelemetry integration
    - Trace all requests
    - Service dependency graph
```

### Local Docker Deployment (Development/Testing)

```bash
# Full development stack
docker-compose -f infrastructure/docker/compose/docker-compose.yml \
               -f infrastructure/docker/compose/docker-compose.dev.yml up -d

# Production-like environment locally
docker-compose -f infrastructure/docker/compose/docker-compose.yml \
               -f infrastructure/docker/compose/docker-compose.prod.yml up -d

# With monitoring stack
docker-compose -f infrastructure/docker/compose/docker-compose.yml \
               -f infrastructure/docker/compose/docker-compose.monitoring.yml up -d

# Health checks
curl http://localhost:8009/health      # Backend
curl http://localhost:5179/            # Dashboard
curl http://localhost:3000/            # Grafana
curl http://localhost:9090/-/healthy   # Prometheus
```

### TeamCity Docker Agents

**TeamCity uses Docker-based build agents for CI/CD:**

```yaml
Agent Configuration:
  Base Image: jetbrains/teamcity-agent
  Tools Installed:
    - Docker Engine
    - Python 3.12
    - Node.js 22
    - pnpm 9.15.0
    - PostgreSQL client
    - Redis client
    
  Volumes:
    - Docker socket: /var/run/docker.sock
    - Build cache: /opt/buildagent/work
    - Dependency cache: /root/.cache
    
  Network:
    - Access to Render API
    - Access to Vercel API
    - Access to Supabase
    - Access to Clerk
    - Access to Docker Hub
    - Access to monitoring stack
```

**Reference:** See `/docs/08-operations/deployment/` for detailed guides.

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "Module not found" errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# For frontend
pnpm install
```

#### 2. Port already in use
```bash
# Find process using port
lsof -i :8009          # Backend
lsof -i :5179          # Dashboard

# Kill process
kill -9 <PID>
```

#### 3. Database connection errors
```bash
# Check PostgreSQL is running
pg_isready

# Check Redis is running
redis-cli ping

# Verify .env credentials
cat .env | grep DATABASE_URL
```

#### 4. Type checking issues
```bash
# ✅ Use BasedPyright
basedpyright .

# ❌ NOT mypy
# mypy .  # Don't use this
```

#### 5. PNPM workspace issues
```bash
# Clear and reinstall
rm -rf node_modules apps/*/node_modules
pnpm install

# Verify workspace
pnpm list --depth=0
```

#### 6. Docker build failures
```bash
# Clear Docker cache
docker builder prune -a

# Rebuild without cache
docker-compose build --no-cache backend

# Check Docker disk space
docker system df
docker system prune -a  # Clean up
```

#### 7. Celery worker not processing tasks
```bash
# Check Redis connection
redis-cli ping

# Check Celery worker logs
celery -A apps.backend.celery_app worker -l debug

# Purge task queue
celery -A apps.backend.celery_app purge

# Check Flower dashboard
open http://localhost:5555
```

---

## 📝 Code Standards & Best Practices

### Python Code Standards

```python
# Use type hints everywhere
from typing import Optional, List, Dict
from pydantic import BaseModel

async def get_user(user_id: int) -> Optional[User]:
    """
    Retrieve user by ID.
    
    Args:
        user_id: The user's unique identifier
        
    Returns:
        User object if found, None otherwise
    """
    return await User.get(id=user_id)

# Use Pydantic for data validation
class CreateUserRequest(BaseModel):
    email: str
    password: str
    role: str = "student"
    
# Prefer async/await for I/O operations
async def fetch_content(content_id: int):
    async with db.session() as session:
        result = await session.execute(
            select(Content).where(Content.id == content_id)
        )
        return result.scalar_one_or_none()

# Use structured logging
import structlog
logger = structlog.get_logger()

logger.info("user_created", user_id=user.id, email=user.email)
```

### TypeScript Code Standards

```typescript
// Use strict TypeScript
// tsconfig.json: "strict": true

// Define interfaces for all data structures
interface User {
  id: number;
  email: string;
  role: 'student' | 'educator' | 'parent' | 'admin';
  createdAt: Date;
}

// Use functional components with hooks
import { FC, useState, useEffect } from 'react';

const UserProfile: FC<{ userId: number }> = ({ userId }) => {
  const [user, setUser] = useState<User | null>(null);
  
  useEffect(() => {
    fetchUser(userId).then(setUser);
  }, [userId]);
  
  return <div>{user?.email}</div>;
};

// Use RTK Query for API calls
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({ baseUrl: '/api' }),
  endpoints: (builder) => ({
    getUser: builder.query<User, number>({
      query: (id) => `/users/${id}`,
    }),
  }),
});
```

### Commit Message Convention

```bash
# Format: <type>(<scope>): <subject>

# Types:
feat: New feature
fix: Bug fix
docs: Documentation changes
style: Code style changes (formatting)
refactor: Code refactoring
test: Adding or updating tests
chore: Maintenance tasks
perf: Performance improvements
ci: CI/CD changes
build: Build system changes

# Examples:
feat(auth): add OAuth2 authentication
fix(api): resolve user creation validation error
docs(readme): update installation instructions
test(agents): add tutoring agent tests
chore(deps): update LangChain to v1.0.5
```

---

## 🎯 Critical Reminders for GitHub Copilot

### 1. Virtual Environment
```bash
✅ Use: venv/
❌ NOT: .venv/ or venv_clean/
```

### 2. Type Checking
```bash
✅ Use: basedpyright
❌ NOT: mypy
```

### 3. UI Library
```bash
✅ Use: Mantine UI v8
❌ NOT: Material-UI (MUI)
```

### 4. Real-Time
```bash
✅ Use: Pusher Channels
❌ NOT: Socket.IO
```

### 5. Package Manager
```bash
✅ Frontend: pnpm 9.15.0
✅ Backend: pip
❌ NOT: npm or yarn for frontend
```

### 6. Ports & Services
```yaml
Local Development:
  Backend: 8009          # NOT 8000
  Dashboard: 5179        # NOT 3000 or 5173
  Celery Flower: 5555
  PostgreSQL: 5432       # (Supabase direct connection)
  Redis: 6379
  MCP Server: 9877
  
Production:
  Backend: Render (https://toolboxai-backend.onrender.com)
  Dashboard: Vercel (https://toolboxai.vercel.app)
  Database: Supabase (managed PostgreSQL)
  Auth: Clerk (managed service)
  
Monitoring (Docker):
  Prometheus: 9090
  Grafana: 3000
  Jaeger: 16686
```

### 7. Documentation
```bash
✅ All docs in: /docs/
✅ Status reports in: /docs/11-reports/
❌ NO markdown files in root (except CLAUDE.md, README.md)
```

### 8. Requirements Files
```bash
✅ Use: requirements.txt (main)
✅ Use: requirements-dev.txt (development)
✅ Use: requirements-docs.txt (documentation)
❌ Do NOT create: requirements-essential.txt, requirements-missing.txt
```

### 9. Docker Compose
```bash
✅ Use: docker-compose.yml (base)
✅ Use: docker-compose.dev.yml (development)
✅ Use: docker-compose.prod.yml (production)
✅ Use: docker-compose.monitoring.yml (observability)
❌ Other compose files are deprecated
```

### 10. Deployment & Services
```bash
✅ Backend Deployment: Render
✅ Frontend Deployment: Vercel
✅ Database: Supabase (PostgreSQL 16)
✅ Authentication: Clerk (OAuth/OIDC)
✅ CI/CD: TeamCity Cloud (Docker-based)
✅ Monitoring: Docker Compose (self-hosted)
❌ NOT: AWS, Azure, or GCP for core services
```

### 11. AI/ML Stack
```bash
✅ Use: LangChain v1.0 API (NOT v0.x)
✅ Use: LangGraph 1.0.3
✅ Use: OpenAI GPT-4.1
✅ Use: LangSmith for observability
✅ Vector Store: Supabase pgvector
```

---

## 🔗 Essential Links & Resources

### Documentation
- **Documentation Index:** `/docs/README.md`
- **File Relocation Map:** `/docs/FILE_RELOCATION_MAP.md`
- **Environment Security:** `/docs/10-security/ENV_FILES_DOCUMENTATION.md`
- **Docker Guide:** `/docs/08-operations/docker/DOCKER_SETUP_GUIDE.md`
- **Getting Started:** `/docs/01-getting-started/QUICK_START.md`

### Development Guides
- **API Documentation:** `/docs/03-api/`
- **Feature Documentation:** `/docs/06-features/`
- **Architecture:** `/docs/02-architecture/`
- **Testing:** `/docs/04-implementation/testing/`

### External Resources
- **FastAPI:** https://fastapi.tiangolo.com
- **React:** https://react.dev
- **Mantine UI:** https://mantine.dev
- **LangChain:** https://python.langchain.com
- **LangGraph:** https://langchain-ai.github.io/langgraph/
- **Supabase:** https://supabase.com/docs
- **Clerk:** https://clerk.com/docs
- **Pusher:** https://pusher.com/docs

### Project Management
- **GitHub Issues:** Track bugs and features
- **GitHub Projects:** Sprint planning and tracking
- **Pull Requests:** Code review process
- **GitHub Discussions:** Technical discussions

---

## 🤝 Contributing

### Contribution Workflow

1. **Check existing issues** - Avoid duplicates
2. **Create/claim an issue** - Discuss before large changes
3. **Fork the repository** - Create your own copy
4. **Create a feature branch** - `git checkout -b feat/your-feature`
5. **Make your changes** - Follow code standards
6. **Write tests** - Maintain coverage
7. **Run tests locally** - Ensure everything passes
8. **Commit with convention** - Use conventional commits
9. **Push to your fork** - `git push origin feat/your-feature`
10. **Create a Pull Request** - Use the PR template
11. **Address review feedback** - Iterate as needed
12. **Celebrate** - Your contribution is merged! 🎉

### Code Review Guidelines

**For Contributors:**
- Keep PRs focused and small
- Write clear descriptions
- Add tests for new features
- Update documentation
- Respond to feedback promptly

**For Reviewers:**
- Be respectful and constructive
- Check for security issues
- Verify tests pass
- Ensure documentation is updated
- Approve when ready

**Reference:** See `.github/CONTRIBUTING.md` for full guidelines.

---

## 📊 Project Health Metrics

### Recent Improvements (November 2025)

**Infrastructure Cleanup:**
- ✅ Reduced GitHub workflows: 40 → 5 (87.5% reduction)
- ✅ Reduced Docker Compose files: 15 → 4 (73% reduction)
- ✅ Reduced Dockerfiles: 21 → 11 (48% reduction)
- ✅ Removed 57 obsolete files
- ✅ Deleted 22,574 lines of dead code
- ✅ Dramatically improved IDE performance

**Documentation:**
- ✅ Centralized all docs in `/docs/`
- ✅ Created comprehensive security guide
- ✅ Updated all file paths and references
- ✅ Added file relocation tracking

**Security:**
- ✅ COPPA, FERPA, GDPR, SOC 2 Type 2 compliant
- ✅ Regular dependency scanning
- ✅ Automated security audits
- ✅ Secret rotation procedures

### Next Steps

**Q4 2025:**
- Enhanced AI agent capabilities
- Expanded Roblox integration
- Performance optimizations
- Additional language support

---

## 📧 Support & Contact

### For Technical Issues
1. Check `/docs/08-operations/troubleshooting/`
2. Search existing GitHub Issues
3. Create a new issue with template
4. Tag with appropriate labels

### For Security Issues
1. **DO NOT** create public issues
2. Email security team (see SECURITY.md)
3. Follow responsible disclosure
4. Allow time for patch before disclosure

### For General Questions
- GitHub Discussions
- Project documentation
- Team communication channels

---

**ToolBoxAI-Solutions Development Team**  
*Building the future of education through AI and technology*

**Last Updated:** November 13, 2025  
**Version:** 2.0.0  
**Next Review:** December 13, 2025  
**License:** MIT

---

## 🏷️ Keywords for Search

AI, Education, EdTech, Roblox, LangChain, LangGraph, FastAPI, React, TypeScript, Python, PostgreSQL, Redis, Docker, Kubernetes, CI/CD, GitHub Actions, TeamCity, Supabase, Clerk, Pusher, OpenAI, GPT-4, Multi-Agent System, COPPA, FERPA, GDPR, SOC 2, Mantine UI, Vite, pnpm, pytest, Playwright, Celery, Microservices, Monorepo, WebSockets, Real-time, OAuth, JWT, Containerization, Infrastructure as Code, Terraform, Vault, Prometheus, Grafana, Sentry, OpenTelemetry
