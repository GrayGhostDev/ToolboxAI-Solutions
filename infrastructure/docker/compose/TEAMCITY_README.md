# TeamCity CI/CD Infrastructure

**Last Updated:** November 13, 2025
**Version:** 1.0.0
**Status:** Production-Ready

---

## 📘 Overview

This directory contains the Docker-based TeamCity CI/CD infrastructure for ToolBoxAI-Solutions. The setup includes:

- **TeamCity Server 2025.07.3** - CI/CD orchestration
- **4 Specialized Build Agents** - Custom agents with pre-installed tooling
- **Persistent Storage** - Volumes for data, logs, and caches
- **Management Scripts** - Easy infrastructure management

---

## 🏗️ Architecture

```
TeamCity Infrastructure
├── TeamCity Server (Port 8111)
│   ├── Web UI
│   ├── Build Coordinator
│   └── Artifact Storage
│
└── Build Agents (4 specialized agents)
    ├── Frontend Agent (Node.js 22 + pnpm 9.15.0)
    │   └── Capabilities: React, Vite, TypeScript, Dashboard builds
    │
    ├── Backend Agent (Python 3.12 + pytest + basedpyright)
    │   └── Capabilities: FastAPI, SQLAlchemy, Celery, Backend tests
    │
    ├── Integration Agent (Node.js 22 + Python 3.12 + Playwright)
    │   └── Capabilities: Full-stack tests, E2E tests, Integration tests
    │
    └── Cloud Agent (Minimal - Docker + deployment tools)
        └── Capabilities: Docker builds, Cloud deployments
```

---

## 🚀 Quick Start

### Prerequisites

- Docker 25.x+ with BuildKit enabled
- Docker Compose v2
- 16+ CPU cores (recommended)
- 20GB+ RAM (recommended)
- 50GB+ disk space

### 1. Initial Setup

```bash
# Navigate to project root
cd /path/to/ToolBoxAI-Solutions

# Create environment file from template
cp infrastructure/docker/compose/.env.teamcity.example infrastructure/docker/compose/.env.teamcity

# Review and update configuration
nano infrastructure/docker/compose/.env.teamcity
```

### 2. Start TeamCity

```bash
# Using management script (recommended)
./scripts/teamcity/manage_teamcity.sh start

# Or using docker-compose directly
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml --env-file infrastructure/docker/compose/.env.teamcity up -d
```

### 3. Access TeamCity UI

1. Open browser: **http://localhost:8111**
2. First-time setup wizard will appear
3. Get super user token from logs or saved file:

```bash
# Token saved during startup
cat .teamcity-token

# Or retrieve from logs
docker logs teamcity-server 2>&1 | grep "Super user authentication token" | tail -1
```

4. Login with:
   - **Username:** (leave empty)
   - **Password:** [super user token]

5. Complete setup wizard:
   - Accept license agreement
   - Choose database (default: internal database)
   - Create admin account
   - Authorize agents (all 4 agents should appear)

---

## 🔧 Management

### Using the Management Script

The `manage_teamcity.sh` script provides easy infrastructure management:

```bash
# Start infrastructure
./scripts/teamcity/manage_teamcity.sh start

# Stop infrastructure
./scripts/teamcity/manage_teamcity.sh stop

# Restart infrastructure
./scripts/teamcity/manage_teamcity.sh restart

# Rebuild agent images (after Dockerfile changes)
./scripts/teamcity/manage_teamcity.sh rebuild

# View logs (all services)
./scripts/teamcity/manage_teamcity.sh logs

# View logs (specific service)
./scripts/teamcity/manage_teamcity.sh logs teamcity-agent-frontend

# Check status and health
./scripts/teamcity/manage_teamcity.sh status

# Clean everything (removes all data!)
./scripts/teamcity/manage_teamcity.sh clean

# Show help
./scripts/teamcity/manage_teamcity.sh help
```

### Using Docker Compose Directly

```bash
# Start
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml up -d

# Stop
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml down

# View logs
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml logs -f

# Rebuild images
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml build --no-cache
```

---

## 🤖 Build Agents

### Frontend Agent (`teamcity-agent-frontend`)

**Pre-installed:**
- Node.js 22.21.0 LTS
- npm 10.9.4
- pnpm 9.15.0
- Git

**Use for:**
- Dashboard builds (React 19 + Vite)
- Frontend linting and type-checking
- JavaScript/TypeScript compilation
- Frontend unit tests (Vitest)

**Dockerfile:** `infrastructure/docker/dockerfiles/teamcity-agent-frontend.Dockerfile`

### Backend Agent (`teamcity-agent-backend`)

**Pre-installed:**
- Python 3.12
- pip (latest)
- pytest 8.3.4
- basedpyright 1.23.1 (type checker)
- black, flake8, isort (code quality)
- FastAPI, SQLAlchemy, asyncpg
- Redis client

**Use for:**
- Backend builds (FastAPI)
- Python unit tests
- Type checking (basedpyright, NOT mypy)
- Code quality checks
- Database migrations

**Dockerfile:** `infrastructure/docker/dockerfiles/teamcity-agent-backend.Dockerfile`

### Integration Agent (`teamcity-agent-integration`)

**Pre-installed:**
- **Node.js 22.21.0** + pnpm 9.15.0
- **Python 3.12** + pytest
- **Playwright 1.51.1** (with Chrome, Firefox, WebKit)
- All backend + frontend tools

**Use for:**
- Full-stack integration tests
- End-to-end (E2E) tests
- API integration tests
- Multi-service testing
- Performance tests

**Dockerfile:** `infrastructure/docker/dockerfiles/teamcity-agent-integration.Dockerfile`

### Cloud Agent (`teamcity-agent-cloud`)

**Pre-installed:**
- Docker CLI
- Standard TeamCity agent tools

**Use for:**
- Docker image builds
- Cloud deployments (Render, Vercel, AWS)
- Artifact publishing
- Release orchestration

**Image:** Official `jetbrains/teamcity-agent:2025.07.3-linux-sudo`

---

## 📦 Volumes

### Persistent Volumes

```
teamcity_data             - TeamCity server data and configuration
teamcity_logs             - TeamCity server logs
teamcity_temp             - TeamCity server temporary files

teamcity_agent_*_conf     - Agent configurations
teamcity_agent_*_work     - Agent working directories
teamcity_agent_*_temp     - Agent temporary files
```

### Cache Volumes (Shared)

```
pnpm_store                - Shared pnpm package store (faster installs)
pnpm_cache                - pnpm cache directory
pip_cache                 - Shared Python pip cache
venv_cache                - Python virtual environments cache
test_results              - Integration test results storage
```

**Note:** Cache volumes significantly speed up builds by caching dependencies.

---

## 🔐 Security

### Agent Isolation

- Each agent runs in its own container
- Agents communicate with server via internal network
- Docker socket mounted read-only (for Docker-in-Docker builds)

### Secrets Management

**DO NOT** hardcode secrets in:
- Dockerfiles
- docker-compose.yml
- .env files (commit .example only)

**Recommended:**
1. Use TeamCity's built-in secret storage
2. Use environment variables in build configurations
3. Mount secrets via Docker secrets (production)

### Network Security

- TeamCity network is isolated (bridge network)
- Only port 8111 exposed to host
- Agents connect internally (not exposed)

---

## 📊 Resource Management

### Recommended System Resources

```
Minimum:
  - 8 CPU cores
  - 12GB RAM
  - 30GB disk

Recommended:
  - 16+ CPU cores
  - 20GB+ RAM
  - 50GB+ disk (for artifacts and caches)

Optimal:
  - 32 CPU cores
  - 32GB RAM
  - 100GB+ disk
```

### Per-Service Resource Limits

```yaml
TeamCity Server:
  CPU: 4 cores limit, 2 cores reserved
  RAM: 4GB limit, 2GB reserved

Frontend Agent:
  CPU: 4 cores limit, 1 core reserved
  RAM: 4GB limit, 2GB reserved

Backend Agent:
  CPU: 4 cores limit, 1 core reserved
  RAM: 4GB limit, 2GB reserved

Integration Agent:
  CPU: 4 cores limit, 2 cores reserved
  RAM: 6GB limit, 3GB reserved

Cloud Agent:
  CPU: 2 cores limit, 0.5 cores reserved
  RAM: 2GB limit, 1GB reserved
```

**Adjust in:** `docker-compose.teamcity.yml` → `deploy.resources`

---

## 🧪 Testing

### Verify Agent Installation

```bash
# Check Node.js on frontend agent
docker exec teamcity-agent-frontend node --version
docker exec teamcity-agent-frontend pnpm --version

# Check Python on backend agent
docker exec teamcity-agent-backend python --version
docker exec teamcity-agent-backend pytest --version

# Check both on integration agent
docker exec teamcity-agent-integration node --version
docker exec teamcity-agent-integration python --version
docker exec teamcity-agent-integration playwright --version
```

### Trigger Test Build

1. Open TeamCity UI: http://localhost:8111
2. Navigate to: **Projects → ToolboxAI-Solutions → Dashboard Build**
3. Click: **Run**
4. Monitor build progress

**Expected:**
- ✅ Step 1: Install Dependencies (pnpm install) - SUCCESS
- ✅ Step 2: Run Tests (pnpm test) - SUCCESS
- ✅ Step 3: Build Production (pnpm build) - SUCCESS

---

## 🐛 Troubleshooting

### Agents Not Connecting

**Symptom:** Agents show as "Disconnected" or don't appear in UI

**Solutions:**
1. Check server is running: `docker ps | grep teamcity-server`
2. Check agent logs: `docker logs teamcity-agent-frontend`
3. Verify SERVER_URL in .env.teamcity: `http://teamcity-server:8111`
4. Restart agents: `./scripts/teamcity/manage_teamcity.sh restart`

### Build Fails: "Command Not Found"

**Symptom:** Build step fails with "pnpm: not found" or "python: not found"

**Solutions:**
1. Verify correct agent is selected for build
2. Check agent capabilities in TeamCity UI
3. Rebuild agent images: `./scripts/teamcity/manage_teamcity.sh rebuild`
4. Verify tool installation: `docker exec teamcity-agent-frontend pnpm --version`

### Out of Memory Errors

**Symptom:** Builds fail with OOM (out of memory) errors

**Solutions:**
1. Increase agent memory limits in `docker-compose.teamcity.yml`
2. Reduce concurrent builds in TeamCity settings
3. Clear caches: `./scripts/teamcity/manage_teamcity.sh clean`
4. Add more system RAM

### Slow Builds

**Symptom:** Builds taking much longer than expected

**Solutions:**
1. Enable BuildKit: `export DOCKER_BUILDKIT=1`
2. Check cache volumes are mounted correctly
3. Increase CPU limits for agents
4. Use parallel build steps where possible
5. Cache npm/pnpm/pip dependencies

### Port Conflict (8111)

**Symptom:** Cannot start server - port 8111 already in use

**Solutions:**
1. Check what's using port: `lsof -i :8111`
2. Stop conflicting service
3. Or change TEAMCITY_PORT in .env.teamcity

---

## 🔄 Maintenance

### Regular Maintenance Tasks

**Weekly:**
- Check disk space: `df -h`
- Review build logs for errors
- Clear old artifacts (TeamCity UI → Administration → Clean-Up)

**Monthly:**
- Update agent images to latest tool versions
- Review and optimize build configurations
- Backup TeamCity data (see below)

**Quarterly:**
- Upgrade TeamCity server version
- Review agent resource allocation
- Security audit

### Backup & Restore

**Backup TeamCity Data:**

```bash
# Stop TeamCity
./scripts/teamcity/manage_teamcity.sh stop

# Backup volumes
docker run --rm -v teamcity_data:/source -v $(pwd)/backups:/backup alpine tar czf /backup/teamcity-data-$(date +%Y%m%d).tar.gz -C /source .

# Restart TeamCity
./scripts/teamcity/manage_teamcity.sh start
```

**Restore TeamCity Data:**

```bash
# Stop TeamCity
./scripts/teamcity/manage_teamcity.sh stop

# Restore volumes
docker run --rm -v teamcity_data:/target -v $(pwd)/backups:/backup alpine tar xzf /backup/teamcity-data-YYYYMMDD.tar.gz -C /target

# Restart TeamCity
./scripts/teamcity/manage_teamcity.sh start
```

### Upgrading TeamCity

1. Backup current data (see above)
2. Update version in `docker-compose.teamcity.yml`:
   ```yaml
   image: jetbrains/teamcity-server:2025.XX.X
   ```
3. Rebuild: `./scripts/teamcity/manage_teamcity.sh rebuild`
4. Follow TeamCity upgrade wizard in UI

---

## 📚 Additional Resources

### TeamCity Documentation
- [TeamCity Official Docs](https://www.jetbrains.com/help/teamcity/)
- [Docker Integration](https://www.jetbrains.com/help/teamcity/docker-wrapper.html)
- [Build Agent Configuration](https://www.jetbrains.com/help/teamcity/build-agent-configuration.html)

### Project Documentation
- Main CLAUDE.md: Project overview and guidelines
- Docker Guide: `docs/08-operations/docker/`
- CI/CD Strategy: `docs/08-operations/ci-cd/`

### Related Files
- Docker Compose: `infrastructure/docker/compose/docker-compose.teamcity.yml`
- Dockerfiles: `infrastructure/docker/dockerfiles/teamcity-agent-*.Dockerfile`
- Management Script: `scripts/teamcity/manage_teamcity.sh`
- Environment Template: `infrastructure/docker/compose/.env.teamcity.example`

---

## 🎓 Build Configuration Examples

### Example: Dashboard Build

```kotlin
// .teamcity/settings.kts
object DashboardBuild : BuildType({
    name = "Dashboard Build"

    vcs {
        root(GitVcsRoot)
    }

    steps {
        script {
            name = "Install Dependencies"
            scriptContent = "pnpm install"
        }

        script {
            name = "Run Tests"
            scriptContent = "pnpm -w dashboard test"
        }

        script {
            name = "Build Production"
            scriptContent = "pnpm -w dashboard build"
        }
    }

    requirements {
        contains("system.agent.name", "Frontend-Builder")
    }
})
```

### Example: Backend Tests

```kotlin
object BackendTests : BuildType({
    name = "Backend Tests"

    steps {
        script {
            name = "Setup Virtual Environment"
            scriptContent = """
                python -m venv venv
                source venv/bin/activate
                pip install -r requirements.txt
            """.trimIndent()
        }

        script {
            name = "Run Tests"
            scriptContent = """
                source venv/bin/activate
                pytest -v --cov
            """.trimIndent()
        }

        script {
            name = "Type Check"
            scriptContent = """
                source venv/bin/activate
                basedpyright .
            """.trimIndent()
        }
    }

    requirements {
        contains("system.agent.name", "Backend-Builder")
    }
})
```

---

**ToolBoxAI-Solutions DevOps Team**
*Building reliable CI/CD infrastructure for the future of education*

**Questions?** Check `/docs/08-operations/ci-cd/` or open an issue.
