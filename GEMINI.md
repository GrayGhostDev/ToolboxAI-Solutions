# Gemini Context File for ToolBoxAI-Solutions

This document provides context to the Gemini AI assistant about the ToolBoxAI-Solutions project.

## 1. Project Overview

- **Project Name:** ToolBoxAI Solutions
- **Description:** An educational technology platform designed to integrate with Roblox, using AI to improve learning outcomes.
- **Repository:** [https://github.com/GrayGhostDev/ToolboxAI-Solutions.git](https://github.com/GrayGhostDev/ToolboxAI-Solutions.git)

## 2. Technology Stack

### Backend
- **Language:** Python 3.11+
- **Framework:** FastAPI
- **Database:** PostgreSQL (managed by Supabase), Redis
- **ORM:** SQLAlchemy 2.0
- **Async Task Queue:** Celery
- **AI/ML:** LangChain, OpenAI
- **Authentication:** Python-JOSE (JWT), Authlib (OAuth)
- **Deployment:** Docker, Render

### Frontend
- **Framework:** React, Next.js
- **Language:** TypeScript
- **UI Library:** Mantine UI
- **Package Manager:** pnpm
- **Node.js:** v22+
- **Deployment:** Vercel

### Testing
- **E2E:** Playwright
- **Unit:** Pytest (backend), Jest (frontend)

### DevOps & Tooling
- **CI/CD:** GitHub Actions, TeamCity
- **Containerization:** Docker
- **Code Quality:** Black, isort, mypy, ESLint, Prettier
- **AI Code Review:** CodeRabbit
- **Monorepo Management:** pnpm workspaces

## 3. Project Structure

This is a monorepo managed with pnpm workspaces.

```
/
├── apps/
│   ├── backend/       # FastAPI backend application
│   └── dashboard/     # React/Next.js frontend application
├── core/              # Core Python modules for agents, security, etc.
├── database/          # Database models, migrations (Alembic), and session management
├── infrastructure/    # Docker configurations
├── packages/          # Shared TypeScript/JavaScript packages
├── scripts/           # Utility and automation scripts
├── services/          # Python services used by the backend
└── tests/             # Backend tests (unit, integration)
```

## 4. Key Configuration Files

- `pnpm-workspace.yaml`: Defines the monorepo structure.
- `package.json`: Root Node.js dependencies and project-wide scripts.
- `apps/dashboard/package.json`: Frontend application dependencies and scripts.
- `requirements.txt`: Python dependencies for the backend.
- `pyproject.toml`: Python tooling configuration (Black, isort, mypy, pytest).
- `Makefile`: Contains a variety of commands for development, testing, and deployment.
- `openapi.yaml`: OpenAPI specification for the backend API.
- `vercel.json`: Vercel deployment configuration for the frontend.
- `.github/workflows/`: GitHub Actions workflows for CI/CD.

## 5. Common Commands

The following commands are frequently used in this project.

### General Development
- `make dev`: Starts both the backend and frontend development servers.
- `pnpm install`: Installs all Node.js dependencies across the monorepo.
- `pip install -r requirements.txt`: Installs Python dependencies.

### Backend
- `make backend`: Runs the FastAPI backend with auto-reload.
- `cd apps/backend && uvicorn main:app --reload`: (Alternative) Starts the backend.

### Frontend
- `make dashboard`: Starts the frontend development server.
- `pnpm --filter apps/dashboard dev`: (Alternative) Starts the frontend.

### Testing
- `make test`: Runs both Python and frontend tests.
- `pnpm run test:e2e`: Runs Playwright end-to-end tests.
- `pytest`: Runs backend Python tests.

### Docker
- `make docker-dev`: Starts all services in development mode using Docker Compose.
- `make docker-dev-down`: Stops and removes the development containers.
- `make stack-up`: Starts the full development and monitoring stack.
- `make stack-down`: Stops the full stack.

### Linting
- `make lint`: Runs linters for both Python and TypeScript code.

### Deployment
- `make deploy-frontend`: Deploys the frontend to Vercel.
- `make deploy-backend`: Deploys the backend to Render.
- `make deploy-all`: Deploys all services.

## 6. API

The backend exposes a RESTful API documented in `openapi.yaml`.

- **Authentication:** Bearer token (JWT).
- **Key Endpoint Groups:**
    - `/agents`: AI agent management and metrics.
    - `/auth`: User authentication and authorization.
    - `/content`: Content generation and management.
    - `/users`: User profile and data management.
- **Specification:** OpenAPI 3.0.0

This context should help in understanding the project's architecture and conventions.
