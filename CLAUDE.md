# ToolBoxAI-Solutions - Claude Code Guide

**Last Updated:** November 13, 2025  
**Project Type:** Full-Stack AI-Powered Educational Platform  
**Status:** Production-Ready  
**Claude Code Version:** Compatible with Claude 3.7+ (Sonnet, Opus)

---

## 📘 About This File

This file provides context to **Claude AI assistants** (including Claude Code, Claude API, and Claude in various IDEs) when working with the ToolBoxAI-Solutions codebase.

**Purpose**: Help Claude understand:
- Project architecture and technology stack
- Coding standards and best practices
- File organization and naming conventions
- Development workflows and tools
- GitHub Copilot agent integration
- Security and compliance requirements

**For Anthropic Claude Users**: This guide is optimized for Claude 3.7 Sonnet and Opus models with extended context windows (200K+ tokens).

**For Claude Code IDE**: This file is automatically loaded as workspace context. Claude Code will reference it when providing assistance.

---

## 🎯 Project Overview

**ToolBoxAI-Solutions** is an AI-powered educational platform with Roblox integration, designed to provide interactive learning experiences for K-12 students.

### Key Features
- **AI-Powered Learning:** Integrated with GPT-4.1 and LangChain v1.0 for intelligent tutoring
- **Roblox Integration:** Seamless connection with Roblox games for educational experiences
- **Real-Time Collaboration:** Pusher Channels (NOT Socket.IO) for live interactions
- **Role-Based Access:** Student, Educator, Parent, and Administrator roles
- **Progress Tracking:** Comprehensive analytics and gamification
- **Secure & Compliant:** COPPA, FERPA, GDPR, and SOC 2 Type 2 compliant

### Target Users
- **Students**: K-12 students using the platform for learning
- **Educators**: Teachers creating content and tracking progress
- **Parents**: Monitoring student activity and progress
- **Administrators**: Managing the platform and users

---

## 🤖 GitHub Copilot & Claude Integration

### GitHub Copilot Agents

**Location:** `.github/agents/`

ToolBoxAI has **6 specialized GitHub Copilot agents** for development tasks. Claude Code can reference these agents when providing assistance:

1. **Issue Resolution Agent** (`my-agent.agent.md`)
   - **Triggers**: Issues, PRs, bug labels
   - **Use for**: Bug fixes, issue resolution, code review

2. **Backend Development Specialist** (`backend-specialist.agent.md`)
   - **Triggers**: `apps/backend/**/*.py`, labels: `backend`, `api`
   - **Use for**: FastAPI, SQLAlchemy, Celery, LangChain development
   - **Technologies**: Python 3.12, FastAPI, Pydantic v2, BasedPyright

3. **Frontend Development Specialist** (`frontend-specialist.agent.md`)
   - **Triggers**: `apps/dashboard/**/*.{tsx,ts}`, labels: `frontend`, `ui`
   - **Use for**: React 19, Mantine UI v8, TypeScript, Redux development
   - **Technologies**: React 19, TypeScript 5.9, Mantine UI v8, RTK Query

4. **AI Agent Development Specialist** (`ai-agent-specialist.agent.md`)
   - **Triggers**: `apps/backend/agents/**/*.py`, labels: `ai`, `agents`
   - **Use for**: LangChain v1.0, LangGraph, OpenAI agent development
   - **Technologies**: LangChain 1.0.5, LangGraph 1.0.3, OpenAI GPT-4.1

5. **DevOps & Infrastructure Specialist** (`devops-specialist.agent.md`)
   - **Triggers**: `infrastructure/**/*`, labels: `deployment`, `docker`
   - **Use for**: Docker, TeamCity, Render, Vercel deployment
   - **Technologies**: Docker 25.x, TeamCity Cloud, Render, Vercel

6. **Documentation Specialist** (`documentation-specialist.agent.md`)
   - **Triggers**: `docs/**/*.md`, labels: `documentation`
   - **Use for**: Technical writing, API docs, user guides
   - **Technologies**: Markdown, OpenAPI, MkDocs

### When to Reference Copilot Agents

When Claude Code is asked to help with a task, reference the appropriate Copilot agent's knowledge:

```
User: "Create a FastAPI endpoint for user authentication"
Claude: [References backend-specialist.agent.md]
        [Provides FastAPI code using Clerk, async/await, Pydantic v2]
        [Suggests: "@copilot using backend-specialist for more help"]
```

### Automated Workflows

The repository has **4 automated workflows** that Claude should be aware of:

1. **copilot-agent-triggers.yml**: Auto-activates agents on label events
2. **auto-resolve-issues.yml**: Automated issue analysis and fixing
3. **pr-auto-review.yml**: Automated PR review with quality checks
4. **auto-label.yml**: Automatic labeling of issues/PRs

**For Claude**: When suggesting fixes, mention relevant automated workflows.

---

## 🏗️ Technology Stack & Constraints

### Required Technologies (✅ Use These)

#### Backend
- **Framework**: FastAPI 0.121.1 (NOT Flask or Django)
- **Runtime**: Python 3.12+ (NOT Python 3.11 or earlier)
- **Type Checking**: BasedPyright (NOT mypy)
- **Validation**: Pydantic v2 (NOT v1)
- **Database Driver**: asyncpg (async PostgreSQL)
- **ORM**: SQLAlchemy 2.0 with async
- **Task Queue**: Celery 5.5.3 + Redis
- **Testing**: pytest + pytest-asyncio
- **Port**: 8009 (NOT 8000)

#### Frontend
- **Framework**: React 19.1.0 (NOT React 18 or earlier)
- **Build Tool**: Vite 6 (NOT webpack or Create React App)
- **Language**: TypeScript 5.9.2 with strict mode
- **UI Library**: Mantine UI v8 (NOT Material-UI/MUI)
- **State**: Redux Toolkit + RTK Query
- **Real-time**: Pusher Channels 3.3.2 (NOT Socket.IO)
- **Testing**: Vitest + React Testing Library
- **Port**: 5179 (NOT 3000 or 5173)

#### AI/ML
- **LLM**: OpenAI GPT-4.1 (gpt-4-1106-preview)
- **Framework**: LangChain 1.0.5 (v1 API, NOT v0.x)
- **Orchestration**: LangGraph 1.0.3
- **Observability**: LangSmith 0.4.42
- **Vector Store**: Supabase pgvector

#### Infrastructure
- **Container**: Docker 25.x with BuildKit
- **Orchestration**: Docker Compose
- **CI/CD**: TeamCity Cloud (Docker-based) + GitHub Actions
- **Package Manager**: pnpm 9.15.0 (frontend), pip (backend)
- **Virtual Env**: `venv/` directory (NOT `.venv`)

#### External Services
- **Authentication**: Clerk (OAuth/OIDC)
- **Database**: Supabase (PostgreSQL 16 + pgvector + Realtime)
- **Deployment**: Render (backend), Vercel (frontend)

### Forbidden Technologies (❌ Do NOT Use)

- **Backend**: Flask, Django, mypy, synchronous SQLAlchemy
- **Frontend**: Material-UI (MUI), Socket.IO, npm, yarn, Create React App
- **Ports**: 3000 (use 5179), 8000 (use 8009), 5173 (use 5179)
- **Virtual Env**: `.venv` (use `venv/`)
- **LangChain**: v0.x API (use v1.0+)
- **React**: Class components (use functional components)
- **Python**: Type hints without BasedPyright checking

---

## 📚 Documentation Location Rules

### CRITICAL: Documentation Guidelines for Claude

**Claude Code Memory:**
- ✅ **All documentation in Markdown files** must be placed in the correct `/docs` location
- ❌ **NO documentation files in root directory** (except CLAUDE.md and README.md)
- ✅ **Only create status and summary documents** upon successful completion of a complete Phase or Task
- ❌ **Stop creating summary documents** unless they go in `/docs/11-reports/` folder
- ✅ **Always check FILE_RELOCATION_MAP.md** before creating or moving files

### Documentation Structure

All documentation is centralized in `/docs/` with the following structure:

```
docs/
├── 01-getting-started/      # Setup and onboarding
├── 02-architecture/         # System architecture
├── 03-api/                  # API documentation
├── 04-implementation/       # Implementation guides
├── 05-features/             # Feature documentation
├── 06-user-guides/          # Role-specific guides
├── 08-operations/           # DevOps, deployment, CI/CD
│   ├── docker/              # Docker guides
│   ├── deployment/          # Deployment procedures
│   ├── ci-cd/               # CI/CD documentation
│   ├── monitoring/          # Monitoring setup
│   └── github-projects/     # Project management
├── 10-security/             # Security documentation
├── 11-reports/              # Status reports ONLY
├── FILE_RELOCATION_MAP.md   # Track moved files
└── README.md                # Documentation index
```

**Reference:** See `/docs/README.md` for complete documentation structure.

### File Creation Rules for Claude

When Claude creates or suggests creating files:

1. **Check Location First**: Always verify the correct directory
2. **Update FILE_RELOCATION_MAP.md**: If moving a file
3. **Follow Naming Conventions**: Use kebab-case for files
4. **Include Headers**: Add title, date, and metadata
5. **No Root Docs**: Except CLAUDE.md, README.md

**Example**:
```markdown
# ❌ Bad (creates doc in root)
/new-feature-doc.md

# ✅ Good (creates doc in correct location)
/docs/05-features/quiz-system.md
```

---


6. **Documentation Specialist** (`documentation-specialist.agent.md`)
   - **Triggers**: `docs/**/*.md`, labels: `documentation`
   - **Use for**: Technical writing, API docs, user guides

### How Claude Should Work With Copilot Agents

When providing assistance, Claude Code should:

1. **Reference Relevant Agents**: Mention which Copilot agent specializes in the task
2. **Follow Agent Patterns**: Use the same patterns and standards as the agents
3. **Suggest Agent Usage**: Recommend using `@copilot using <agent>` for follow-up
4. **Complement Agents**: Provide deeper explanation and context beyond agents

**Example**:
```
User: "Help me create a FastAPI endpoint"

Claude: I'll help you create a FastAPI endpoint following the backend-specialist patterns.
[Provides detailed implementation with async/await, Pydantic v2, Clerk auth]

For automated assistance, you can also use:
@copilot using backend-specialist create <endpoint description>

The backend specialist agent can help with:
- Type checking (BasedPyright)
- Testing (pytest)
- OpenAPI documentation
- Best practices validation
```

---

## 💻 Claude Code IDE Integration

### Using Claude Code with ToolBoxAI

**Claude Code** is Anthropic's AI-powered IDE assistant. This section helps Claude Code understand how to work optimally with ToolBoxAI-Solutions.

### Context Loading

Claude Code automatically loads:
1. **This file** (CLAUDE.md) - As primary context
2. **.github/instructions.md** - For GitHub Copilot integration
3. **README.md** - For project overview
4. **Recent files** - Files you're actively editing

### Workspace Commands

Claude Code users can use these commands:

```
/explain - Explain code or architecture
/fix - Suggest fixes for bugs or errors
/refactor - Improve code structure
/test - Generate tests
/doc - Add documentation
/review - Review code for issues
```

**ToolBoxAI-specific commands**:
```
@workspace /explain auth flow - Explain Clerk authentication
@workspace /explain agent system - Explain LangChain agent architecture
@workspace /explain deployment - Explain Render + Vercel deployment
@workspace /fix backend - Fix backend issues with correct patterns
@workspace /test component - Generate Vitest tests for React components
```

### Claude Code Best Practices for ToolBoxAI

#### 1. Always Check Technology Stack

Before suggesting code, verify the tech stack:

**❌ Bad**:
```python
# Suggests Material-UI for frontend
from @mui/material import Button
```

**✅ Good**:
```typescript
// Uses Mantine UI v8 as required
import { Button } from '@mantine/core';
```

#### 2. Follow Async Patterns

**❌ Bad** (sync code):
```python
def get_user(user_id: int):
    return db.query(User).filter(User.id == user_id).first()
```

**✅ Good** (async code):
```python
async def get_user(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()
```

#### 3. Use Correct Type Checking

**❌ Bad** (mypy hints):
```python
from typing import Optional
def func(x: Optional[str]) -> Optional[int]:
    pass
```

**✅ Good** (BasedPyright with modern syntax):
```python
def func(x: str | None) -> int | None:
    """BasedPyright will check this."""
    pass
```

#### 4. Reference Documentation

When explaining concepts, reference ToolBoxAI docs:

**✅ Good**:
```
The authentication flow uses Clerk. See:
- Architecture: docs/02-architecture/authentication.md
- Implementation: docs/04-implementation/clerk-integration.md
- Security: docs/10-security/authentication-security.md
```

### Claude's Role vs Copilot Agents

**Claude Code excels at**:
- Deep architectural explanations
- Complex refactoring
- Multi-file changes
- Design discussions
- Debugging complex issues
- Learning and education

**Copilot Agents excel at**:
- Quick code generation
- Pattern-based suggestions
- File-specific help
- Automated quality checks
- Triggered assistance

**Use both**: Claude for understanding, Copilot for quick assistance.

---

## 🔧 Development Workflows for Claude

### Common Development Tasks

When assisting with these tasks, Claude should follow these patterns:

#### Task: Create New API Endpoint

**Steps Claude should guide**:
1. Create endpoint in `apps/backend/api/`
2. Define Pydantic models in `apps/backend/models/`
3. Add business logic in `apps/backend/services/`
4. Write tests in `tests/backend/`
5. Update OpenAPI documentation
6. Test with pytest
7. Verify with BasedPyright

**Code pattern**:
```python
# apps/backend/api/v1/resources.py
from fastapi import APIRouter, Depends, HTTPException, status
from apps.backend.models.resource import ResourceCreate, ResourceResponse
from apps.backend.services.resource_service import ResourceService
from apps.backend.core.auth import get_current_user

router = APIRouter(prefix="/api/v1/resources", tags=["resources"])

@router.post("/", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    resource: ResourceCreate,
    user: dict = Depends(get_current_user),
    service: ResourceService = Depends()
) -> ResourceResponse:
    """
    Create a new resource.
    
    Requires:
    - Clerk authentication
    - Valid resource data
    
    Returns:
    - Created resource with ID
    """
    return await service.create(resource, user_id=user["id"])
```

#### Task: Create React Component

**Steps Claude should guide**:
1. Create component in `apps/dashboard/src/components/`
2. Define TypeScript interfaces
3. Use Mantine UI v8 components
4. Implement with hooks
5. Connect to Redux if needed
6. Add Vitest tests
7. Verify TypeScript compilation

**Code pattern**:
```typescript
// apps/dashboard/src/components/ResourceCard/ResourceCard.tsx
import { FC } from 'react';
import { Card, Text, Button, Group } from '@mantine/core';
import { useResourceMutation } from '@/api/resources';

interface ResourceCardProps {
  id: number;
  title: string;
  description?: string;
}

export const ResourceCard: FC<ResourceCardProps> = ({ 
  id, 
  title, 
  description 
}) => {
  const [deleteResource, { isLoading }] = useResourceMutation();

  const handleDelete = async () => {
    await deleteResource(id);
  };

  return (
    <Card shadow="sm" padding="lg" radius="md" withBorder>
      <Text size="lg" fw={500}>{title}</Text>
      {description && <Text size="sm" c="dimmed" mt="sm">{description}</Text>}
      <Group mt="md">
        <Button onClick={handleDelete} loading={isLoading} color="red">
          Delete
        </Button>
      </Group>
    </Card>
  );
};
```

#### Task: Create LangChain Agent

**Steps Claude should guide**:
1. Create agent in `apps/backend/agents/`
2. Define state with TypedDict
3. Create LangGraph workflow
4. Add custom tools
5. Configure LLM (GPT-4.1)
6. Add LangSmith tracing
7. Test agent behavior

**Code pattern**:
```python
# apps/backend/agents/content_reviewer.py
from typing import TypedDict, List
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langsmith import traceable

class ReviewState(TypedDict):
    content: str
    feedback: List[str]
    approved: bool

llm = ChatOpenAI(model="gpt-4-1106-preview", temperature=0.7)

@traceable(name="content_review_agent")
async def review_content(state: ReviewState) -> ReviewState:
    """Review educational content for quality."""
    # Agent implementation
    pass

# Build workflow
workflow = StateGraph(ReviewState)
workflow.add_node("review", review_content)
workflow.set_entry_point("review")
workflow.add_edge("review", END)

content_reviewer = workflow.compile()
```

---

## 📝 Claude Communication Guidelines

### How Claude Should Respond

When providing assistance in ToolBoxAI-Solutions:

#### 1. Be Explicit About Technology Choices

**❌ Vague**:
```
Use a UI library for the button component.
```

**✅ Explicit**:
```
Use Mantine UI v8 for the button component (NOT Material-UI):

import { Button } from '@mantine/core';
```

#### 2. Provide Context and Rationale

**❌ Just code**:
```python
async def get_users(db: AsyncSession):
    return await db.execute(select(User))
```

**✅ With context**:
```python
# Using async/await as required by ToolBoxAI's asyncpg setup
# BasedPyright will type-check this pattern
async def get_users(db: AsyncSession) -> list[User]:
    """
    Retrieve all users from Supabase.
    
    Uses:
    - AsyncSession for non-blocking database queries
    - Modern Python 3.12 type hints (list[User] not List[User])
    - BasedPyright type checking
    """
    result = await db.execute(select(User))
    return result.scalars().all()
```

#### 3. Reference Documentation

Always point to relevant docs:

**✅ Good**:
```
For more details on authentication:
- See docs/02-architecture/authentication.md
- Implementation: docs/04-implementation/clerk-integration.md
- GitHub Copilot: Use @copilot using backend-specialist for auth help
```

#### 4. Warn About Common Mistakes

**✅ Helpful**:
```
⚠️ Common mistake: Don't use Material-UI (MUI) in this project.
✅ Use Mantine UI v8 instead.

❌ Bad: import Button from '@mui/material/Button'
✅ Good: import { Button } from '@mantine/core'
```

#### 5. Suggest Next Steps

**✅ Complete**:
```
Next steps:
1. ✅ Code implementation provided
2. 📝 Add tests: pytest tests/backend/test_resources.py
3. 🔍 Type check: basedpyright apps/backend
4. 🚀 Run locally: uvicorn main:app --reload --port 8009
5. 📚 Update docs: docs/03-api/resources-endpoint.md
```

---

## 🔒 Security & Compliance for Claude

### CRITICAL: Security Rules

When generating code, Claude MUST ensure:

#### 1. No Secrets in Code

**❌ NEVER**:
```python
OPENAI_API_KEY = "sk-proj-..."
SUPABASE_KEY = "eyJhbGc..."
```

**✅ ALWAYS**:
```python
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable required")
```

#### 2. Input Validation

**✅ ALWAYS use Pydantic v2**:
```python
from pydantic import BaseModel, Field, field_validator

class QuizCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    questions: list[str] = Field(..., min_length=1, max_length=50)
    
    @field_validator('title')
    @classmethod
    def title_must_be_clean(cls, v: str) -> str:
        # Validate and sanitize
        return v.strip()
```

#### 3. Authentication Required

**❌ BAD** (no auth):
```python
@router.get("/sensitive-data")
async def get_sensitive():
    return {"data": "secret"}
```

**✅ GOOD** (Clerk auth):
```python
from apps.backend.core.auth import get_current_user

@router.get("/sensitive-data")
async def get_sensitive(user: dict = Depends(get_current_user)):
    # Clerk authentication verified
    return {"data": "secret", "user_id": user["id"]}
```

#### 4. COPPA Compliance

**For K-12 platform**:
- ❌ NO PII in logs
- ❌ NO tracking without consent
- ✅ Parental consent for students under 13
- ✅ Data minimization
- ✅ Secure data storage

**Example**:
```python
import logging

logger = logging.getLogger(__name__)

# ❌ BAD: Logs PII
logger.info(f"User {email} logged in")

# ✅ GOOD: No PII
logger.info(f"User {user_id} logged in")
```

---

## 🎓 Educational Context for Claude

### Understanding ToolBoxAI's Purpose

ToolBoxAI-Solutions is an **educational platform** for K-12 students. When providing assistance, Claude should:

1. **Consider Educational Use Cases**:
   - Students aged 5-18
   - Various skill levels
   - Accessibility requirements (WCAG 2.1 AA)
   - Parent/teacher oversight

2. **Prioritize Safety**:
   - Content filtering
   - Age-appropriate interactions
   - Moderation capabilities
   - Audit trails

3. **Support Learning Goals**:
   - Progress tracking
   - Gamification
   - Personalized feedback
   - Adaptive difficulty

### Example Educational Features

When implementing features, consider:

**Quiz System**:
- Multiple question types
- Adaptive difficulty
- Immediate feedback
- Progress tracking
- Parent/teacher visibility

**AI Tutor**:
- Age-appropriate language
- Encouraging tone
- Learning-focused responses
- Safe content filtering
- Session limits

**Roblox Integration**:
- Educational game sync
- Progress transfer
- Safe social features
- Moderated chat
- Parent controls

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
