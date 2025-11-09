# GitHub + TeamCity CI/CD Integration Guide

**Implementation Date:** November 9, 2025  
**Status:** ✅ Configuration Complete - Requires Manual Setup  
**CI/CD Stack:** GitHub Actions + TeamCity + Docker + Supabase + Render + Vercel

---

## 🎯 Overview

Complete integration guide for ToolBoxAI's **hybrid CI/CD architecture** using:
- **GitHub Actions** for automation, security scanning, and deployment orchestration
- **TeamCity** for Docker-based builds, testing, and quality assurance
- **Docker Compose** for local development and TeamCity agent management
- **Supabase** for PostgreSQL database (shared by TeamCity)
- **Render** for backend deployment
- **Vercel** for frontend deployment

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        GITHUB REPOSITORY                         │
│                    GrayGhostDev/ToolboxAI-Solutions             │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                ┌───────┴────────┐
                │                │
        ┌───────▼─────┐   ┌─────▼──────┐
        │   GITHUB    │   │  TEAMCITY  │
        │   ACTIONS   │◄──┤   SERVER   │
        │  Workflows  │   │   (Docker) │
        └──────┬──────┘   └─────┬──────┘
               │                │
     ┌─────────┼────────┐       │
     │         │        │   ┌───▼────┐
┌────▼───┐ ┌──▼───┐ ┌──▼───┤ Build  │
│Security│ │Deploy│ │Docs  │ Agents │
│Scanning│ │ment  │ │Pages │ (3x)   │
└────────┘ └──┬───┘ └──────┘└───┬────┘
              │                  │
         ┌────┴──────┐      ┌───▼────────┐
         │           │      │   Docker   │
    ┌────▼────┐ ┌───▼────┐ │   Images   │
    │ Vercel  │ │ Render │ │ Dashboard  │
    │Frontend │ │Backend │ │  Backend   │
    └─────────┘ └────────┘ │   MCP      │
                            └────────────┘
```

---

## 📋 Current Configuration

### GitHub Actions Workflows (20 active)

**CI/CD & Building:**
1. ✅ `enhanced-ci-cd.yml` - Main CI/CD pipeline (recommended)
2. ✅ `ci-cd-pipeline.yml` - Alternative CI/CD
3. ✅ `docker-ci-cd.yml` - Docker build & deploy
4. ✅ `docker-build-push.yml` - Docker image publishing
5. ✅ `dashboard-build.yml` - Frontend build
6. ✅ `teamcity-trigger.yml` - **TeamCity integration**

**Testing:**
7. ✅ `comprehensive-testing.yml` - Full test suite
8. ✅ `continuous-testing.yml` - Ongoing tests
9. ✅ `e2e-tests.yml` - End-to-end tests
10. ✅ `playwright.yml` - Browser tests

**Security:**
11. ✅ `security-pipeline.yml` - Security scanning
12. ✅ `security-agents.yml` - Agent security scans
13. ✅ `qodana_code_quality.yml` - Code quality

**Deployment:**
14. ✅ `render-deploy.yml` - Backend deployment
15. ✅ `deploy.yml` - Full platform deployment
16. ✅ `database-migrations.yml` - DB migrations

**Documentation:**
17. ✅ `pages-deploy.yml` - GitHub Pages
18. ✅ `documentation-health.yml` - Doc validation
19. ✅ `documentation-updater.yml` - Auto-update docs

**Automation:**
20. ✅ `agent-orchestration.yml` - AI agent workflows
21. ✅ `vault-rotation.yml` - Secret rotation

### TeamCity Configuration

**Location:** `.teamcity/settings.kts`

**Build Configurations:**
- `Build` - Master orchestrator
- `DashboardBuild` - React + Vite frontend
- `BackendBuild` - FastAPI backend
- `MCPServerBuild` - Model Context Protocol
- `AgentCoordinatorBuild` - LangChain agents
- `RobloxIntegrationBuild` - Roblox plugin
- `SecurityScan` - Security analysis
- `IntegrationTests` - Full-stack tests
- `PerformanceTests` - Load testing
- `DeploymentPipeline` - Staging deploy
- `ProductionDeployment` - Production deploy

**Build Agents:** 3 Docker agents with parallel execution

**Features:**
- Build Cache (10GB)
- Docker-in-Docker support
- Supabase PostgreSQL integration
- GitHub webhook triggers

---

## 🔐 Required GitHub Secrets

### Already Configured ✅

Based on your message, these are already set:

```bash
RENDER_API_KEY=rnd_Xv0q1Yz7W2bvWz9kwMbMXb1hAUif
RENDER_BACKEND_SERVICE_ID=srv-d479pmali9vc738itjng
VERCEL_TOKEN=IUeTajUbNwUAvpK8qCfaY2tsI
```

### Required for Full Integration

**TeamCity Integration:**
```bash
TEAMCITY_PIPELINE_ACCESS_TOKEN   # TeamCity API token
TEAMCITY_URL                      # https://ci.toolboxaisolutions.com (or localhost:8111)
TEAMCITY_PROJECT_ID               # ToolBoxAISolutions
```

**Deployment Secrets:**
```bash
# Render (Backend)
RENDER_API_KEY                    # ✅ Already configured
RENDER_BACKEND_SERVICE_ID         # ✅ Already configured
RENDER_SERVICE_ID_STAGING         # Staging service ID
RENDER_SERVICE_ID_PROD            # Production service ID

# Vercel (Frontend)
VERCEL_TOKEN                      # ✅ Already configured
VERCEL_ORG_ID                     # Vercel organization ID
VERCEL_PROJECT_ID                 # Vercel project ID

# Docker Hub
DOCKER_USERNAME                   # thegrayghost23
DOCKER_PASSWORD                   # Docker Hub token
```

**Database & Services:**
```bash
# Supabase
DATABASE_URL                      # PostgreSQL connection string
SUPABASE_URL                      # Supabase project URL
SUPABASE_ANON_KEY                 # Supabase anonymous key
SUPABASE_SERVICE_ROLE_KEY         # Supabase service role key

# Application
API_KEY                           # Dashboard API key
DASHBOARD_API_KEY                 # Alternative dashboard key
DASHBOARD_URL                     # Dashboard URL
```

**Third-Party Integrations:**
```bash
# AI Services
ANTHROPIC_API_KEY                 # Claude API
OPENAI_API_KEY                    # OpenAI API

# Monitoring & Analytics
SENTRY_DSN                        # Sentry error tracking
SENTRY_AUTH_TOKEN                 # Sentry API token
PUSHER_KEY                        # Pusher real-time
PUSHER_SECRET                     # Pusher secret

# Communication
SLACK_WEBHOOK_URL                 # Slack notifications
DISCORD_WEBHOOK                   # Discord notifications
```

**Security Scanning:**
```bash
# Code Security
FOSSA_API_KEY                     # License scanning
SNYK_TOKEN                        # Dependency scanning

# Optional (AWS removed)
# Note: Not using AWS per requirements
```

---

## 🚀 Setup Instructions

### Step 1: Enable GitHub Pages

Already created in previous implementation. To activate:

1. Go to: https://github.com/GrayGhostDev/ToolboxAI-Solutions/settings/pages
2. Source: **GitHub Actions**
3. Click **Save**

✅ **Result:** Docs at https://grayghostdev.github.io/ToolboxAI-Solutions/

### Step 2: Configure Required Secrets

#### Option A: Via GitHub Web UI

1. Go to: https://github.com/GrayGhostDev/ToolboxAI-Solutions/settings/secrets/actions
2. Click **New repository secret**
3. Add each secret from the list above

#### Option B: Via GitHub CLI

```bash
# TeamCity
gh secret set TEAMCITY_PIPELINE_ACCESS_TOKEN --body "YOUR_TOKEN_HERE"
gh secret set TEAMCITY_URL --body "http://localhost:8111"
gh secret set TEAMCITY_PROJECT_ID --body "ToolBoxAISolutions"

# Docker Hub
gh secret set DOCKER_USERNAME --body "thegrayghost23"
gh secret set DOCKER_PASSWORD --body "YOUR_DOCKER_TOKEN"

# Vercel (additional)
gh secret set VERCEL_ORG_ID --body "YOUR_ORG_ID"
gh secret set VERCEL_PROJECT_ID --body "YOUR_PROJECT_ID"

# Supabase
gh secret set DATABASE_URL --body "postgresql://..."
gh secret set SUPABASE_URL --body "https://YOUR_PROJECT.supabase.co"
gh secret set SUPABASE_ANON_KEY --body "YOUR_ANON_KEY"
gh secret set SUPABASE_SERVICE_ROLE_KEY --body "YOUR_SERVICE_KEY"
```

### Step 3: Start TeamCity Server

```bash
cd infrastructure/docker/compose

# Start TeamCity with Supabase integration
docker-compose -f docker-compose.teamcity.yml up -d

# Check status
docker-compose -f docker-compose.teamcity.yml ps

# View logs
docker logs teamcity-server --tail 100
```

**First-time Setup:**
1. Access: http://localhost:8111
2. Complete TeamCity first-run wizard
3. Connect to Supabase PostgreSQL (auto-configured)
4. Create admin account
5. Activate license (free for 100 build configurations)

### Step 4: Configure TeamCity GitHub Integration

#### 4.1 Create GitHub App (Recommended)

1. Go to: https://github.com/organizations/YOUR_ORG/settings/apps/new
   - Or: https://github.com/settings/apps/new (personal)

2. **GitHub App Settings:**
   ```
   Name: TeamCity CI for ToolBoxAI
   Homepage URL: http://localhost:8111
   Webhook URL: http://localhost:8111/app/rest/vcs-root-instances/commitHookNotification
   Webhook Secret: Generate secure token
   ```

3. **Permissions:**
   - Repository permissions:
     - Contents: Read & Write
     - Commit statuses: Read & Write
     - Pull requests: Read & Write
     - Webhooks: Read & Write
   - Organization permissions:
     - Members: Read

4. **Events (Subscribe to):**
   - Push
   - Pull request
   - Release
   - Deployment status

5. **Install App** on `ToolboxAI-Solutions` repository

6. **Get Credentials:**
   - App ID
   - Installation ID
   - Private Key (download)

#### 4.2 Configure in TeamCity

1. **TeamCity Server > Administration > GitHub**
2. Add GitHub App connection:
   - App ID: `<from step 4.1>`
   - Private Key: `<paste content>`
   - Installation ID: `<from GitHub>`

3. **Create Access Token** (if using personal token instead):
   - GitHub > Settings > Developer settings > Personal access tokens
   - Generate new token (classic)
   - Scopes: `repo`, `read:org`, `write:repo_hook`
   - Copy token

4. **TeamCity > Project > VCS Roots > MainRepository**
   - Authentication: GitHub App or Token
   - Repository URL: `https://github.com/GrayGhostDev/ToolboxAI-Solutions`

#### 4.3 Configure Build Triggers

Already configured in `.teamcity/settings.kts`:

```kotlin
triggers {
    vcs {
        branchFilter = """
            +:refs/heads/main
            +:refs/heads/develop
            +:refs/heads/feature/*
        """.trimIndent()
    }
}
```

**Webhooks** (automatic with GitHub App):
- Push events → Trigger builds
- PR events → Trigger validation
- Release events → Trigger deployment

### Step 5: Configure GitHub → TeamCity Trigger

The `teamcity-trigger.yml` workflow automatically triggers TeamCity builds.

**To enable:**

1. **Add TeamCity token to GitHub:**
   ```bash
   gh secret set TEAMCITY_PIPELINE_ACCESS_TOKEN --body "YOUR_TEAMCITY_TOKEN"
   ```

2. **Generate TeamCity token:**
   - TeamCity > User Profile > Access Tokens
   - Create new token
   - Permissions: "Start/stop builds", "View project"
   - Copy token value

3. **Test workflow:**
   ```bash
   # Push to main will trigger
   git push origin main
   
   # Or manually trigger
   gh workflow run teamcity-trigger.yml
   ```

### Step 6: Verify Integration

**GitHub Actions → TeamCity:**
```bash
# Make a change and push
echo "Testing integration" >> README.md
git add README.md
git commit -m "test: GitHub-TeamCity integration"
git push origin main

# Check GitHub Actions
gh run list --limit 5

# Check TeamCity
open http://localhost:8111/buildConfiguration/ToolBoxAISolutions_Build
```

**TeamCity → GitHub:**
- TeamCity builds should post status to GitHub PRs
- Commit status checks appear on GitHub
- Build results comment on PRs

---

## 🔄 CI/CD Workflow Examples

### Workflow 1: Feature Development

```bash
# Developer workflow
git checkout -b feature/new-dashboard
# ... make changes ...
git commit -m "feat: Add new dashboard widget"
git push origin feature/new-dashboard
```

**What Happens:**

1. **GitHub Actions** (triggered on push):
   - ✅ `security-pipeline.yml` - Security scan
   - ✅ `comprehensive-testing.yml` - Quick tests
   - ✅ `teamcity-trigger.yml` - Trigger TeamCity

2. **TeamCity** (triggered by webhook):
   - ✅ `DashboardBuild` - Full frontend build
   - ✅ Docker image creation
   - ✅ Integration tests
   - ✅ Results posted to GitHub PR

3. **GitHub PR**:
   - Status checks appear
   - TeamCity build link in comments
   - Ready for review after all checks pass

### Workflow 2: Main Branch Deployment

```bash
# Merge PR to main
git checkout main
git pull origin main
```

**What Happens:**

1. **GitHub Actions**:
   - ✅ `enhanced-ci-cd.yml` - Full CI/CD pipeline
   - ✅ `docker-ci-cd.yml` - Build & push images
   - ✅ `security-pipeline.yml` - Production security scan
   - ✅ `pages-deploy.yml` - Update documentation

2. **TeamCity**:
   - ✅ `Build` - Master build orchestration
   - ✅ `DashboardBuild` + `BackendBuild` - Parallel builds
   - ✅ `SecurityScan` - Comprehensive security
   - ✅ `IntegrationTests` - Full test suite

3. **Deployment**:
   - ✅ `render-deploy.yml` - Deploy backend to Render
   - ✅ `DeploymentPipeline` (TeamCity) - Deploy to staging
   - 🔒 `ProductionDeployment` - Manual approval required

### Workflow 3: Manual Production Deploy

```bash
# Trigger production deployment
gh workflow run deploy.yml --ref main \
  -f environment=production
```

**What Happens:**

1. **GitHub Actions**:
   - ✅ Pre-deployment checks
   - ✅ Database migrations (if needed)
   - ✅ Trigger TeamCity production build

2. **TeamCity**:
   - 🔒 `ProductionDeployment` - Requires approval
   - ✅ Build production Docker images
   - ✅ Deploy to Vercel (frontend)
   - ✅ Deploy to Render (backend)
   - ✅ Health checks
   - ✅ Slack/Discord notification

3. **Post-Deployment**:
   - ✅ Smoke tests
   - ✅ Monitor error rates
   - ✅ Rollback capability

---

## 📊 Integration Points

### GitHub → TeamCity

**Triggers:**
- Push to `main`, `develop`, `feature/*` branches
- Pull request opened/synchronized
- Manual workflow dispatch
- Release created

**Method:**
- GitHub Actions workflow: `teamcity-trigger.yml`
- REST API call to TeamCity
- Authentication: Bearer token

**Example Trigger:**
```bash
curl -X POST \
  -H "Authorization: Bearer ${TEAMCITY_TOKEN}" \
  -H "Content-Type: application/xml" \
  "${TEAMCITY_URL}/app/rest/buildQueue" \
  -d "<build branchName='main'>
      <buildType id='ToolBoxAISolutions_Build'/>
  </build>"
```

### TeamCity → GitHub

**Status Updates:**
- Commit status checks
- PR comments
- Build result badges

**Configuration:**
```kotlin
features {
    commitStatusPublisher {
        vcsRootExtId = "MainRepository"
        publisher = github {
            githubUrl = "https://api.github.com"
            authType = personalToken {
                token = "credentialsJSON:github-token"
            }
        }
    }
}
```

### Docker Integration

**TeamCity Agents:**
- Docker-in-Docker capability
- Build and push to Docker Hub
- Pull images for testing

**GitHub Actions:**
- Build Docker images
- Push to registry
- Deploy to Render/Vercel

**Shared Registry:**
```yaml
# Docker Hub
registry: docker.io
username: thegrayghost23
images:
  - toolboxai-dashboard:latest
  - toolboxai-backend:latest
  - toolboxai-mcp:latest
```

---

## 🐛 Troubleshooting

### TeamCity Not Receiving Webhooks

**Issue:** GitHub webhook failing

**Check:**
```bash
# Verify TeamCity is accessible
curl -I http://localhost:8111/health

# Check webhook URL in GitHub
# Settings > Webhooks > Recent Deliveries
```

**Fix:**
1. If TeamCity is on `localhost`, use **ngrok** for testing:
   ```bash
   ngrok http 8111
   # Update webhook URL to ngrok URL
   ```

2. For production, use proper domain with SSL

### GitHub Actions Can't Reach TeamCity

**Issue:** `teamcity-trigger.yml` fails to connect

**Check:**
```bash
# Verify token is set
gh secret list | grep TEAMCITY

# Test TeamCity API manually
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8111/app/rest/server
```

**Fix:**
1. Verify `TEAMCITY_PIPELINE_ACCESS_TOKEN` is set
2. Check TeamCity URL is correct
3. Ensure token has correct permissions

### Docker Images Not Building

**Issue:** TeamCity agents can't build Docker images

**Check:**
```bash
# Verify Docker-in-Docker
docker exec teamcity-agent-1 docker info

# Check agent logs
docker logs teamcity-agent-1 --tail 100
```

**Fix:**
1. Ensure agents have Docker socket mounted
2. Check Docker daemon is running
3. Verify user permissions (non-root)

### Supabase Connection Issues

**Issue:** TeamCity can't connect to database

**Check:**
```bash
# Verify Supabase is running
docker ps | grep supabase_db

# Test connection
docker exec teamcity-server nc -zv db.supabase.internal 5432
```

**Fix:**
1. Ensure Supabase is started before TeamCity
2. Verify network connection: `supabase_network_supabase`
3. Check database credentials in `database.properties`

---

## 📚 Configuration Files Reference

### GitHub Actions

```
.github/workflows/
├── enhanced-ci-cd.yml         # Main CI/CD (recommended)
├── teamcity-trigger.yml       # TeamCity integration ⭐
├── docker-ci-cd.yml           # Docker pipeline
├── security-pipeline.yml      # Security scanning
├── render-deploy.yml          # Backend deployment
├── pages-deploy.yml           # Documentation
└── comprehensive-testing.yml  # Test suite
```

### TeamCity

```
.teamcity/
├── settings.kts              # Main configuration (1399 lines)
├── deployment.kts            # Deployment configs (358 lines)
└── README.md                 # TeamCity documentation
```

### Docker

```
infrastructure/docker/compose/
├── docker-compose.teamcity.yml    # TeamCity stack ⭐
├── docker-compose.yml             # Main services
├── docker-compose.dev.yml         # Development
├── docker-compose.prod.yml        # Production
└── SUPABASE_TEAMCITY_INTEGRATION.md
```

---

## ✅ Integration Checklist

### GitHub Setup
- [x] Repository created
- [x] Workflows configured (20+)
- [x] Dependabot enabled
- [ ] Required secrets configured
- [ ] Branch protection rules
- [ ] GitHub App created (optional)

### TeamCity Setup
- [x] Docker Compose config created
- [x] Supabase integration complete
- [x] Kotlin DSL configuration
- [ ] TeamCity server running
- [ ] Admin account created
- [ ] GitHub connection configured
- [ ] Build agents active

### Integration
- [ ] GitHub → TeamCity trigger working
- [ ] TeamCity → GitHub status working
- [ ] Docker Hub authentication
- [ ] Vercel deployment configured
- [ ] Render deployment configured
- [ ] Webhooks functioning

### Testing
- [ ] Push to feature branch triggers builds
- [ ] PR creates build and status check
- [ ] Main branch deploys to staging
- [ ] Production deploy requires approval
- [ ] Notifications working

---

## 🎯 Next Steps

### Immediate (Today)

1. **Configure Missing Secrets:**
   ```bash
   gh secret set TEAMCITY_PIPELINE_ACCESS_TOKEN --body "..."
   gh secret set DOCKER_USERNAME --body "thegrayghost23"
   gh secret set DOCKER_PASSWORD --body "..."
   ```

2. **Start TeamCity:**
   ```bash
   cd infrastructure/docker/compose
   docker-compose -f docker-compose.teamcity.yml up -d
   ```

3. **Complete First-Time Setup:**
   - Access http://localhost:8111
   - Follow wizard
   - Create admin account

### This Week

4. **Configure GitHub Integration:**
   - Create GitHub App or token
   - Add to TeamCity
   - Test webhook delivery

5. **Test Full Pipeline:**
   - Create test PR
   - Verify builds trigger
   - Check status updates

6. **Configure Deployments:**
   - Test staging deployment
   - Set up production approval
   - Configure monitoring

### Ongoing

7. **Monitor & Optimize:**
   - Review build times
   - Optimize Docker cache
   - Tune build agents

8. **Documentation:**
   - Update runbooks
   - Document custom configurations
   - Train team on workflows

---

## 📞 Support Resources

**Documentation:**
- TeamCity: https://www.jetbrains.com/help/teamcity/
- GitHub Actions: https://docs.github.com/en/actions
- Docker Compose: https://docs.docker.com/compose/

**ToolBoxAI Docs:**
- `.teamcity/README.md` - TeamCity configuration
- `infrastructure/docker/compose/SUPABASE_TEAMCITY_INTEGRATION.md`
- `docs/11-reports/GITHUB_PAGES_DEPENDABOT_IMPLEMENTATION.md`

**Quick Commands:**
```bash
# View all workflows
gh workflow list

# Trigger specific workflow
gh workflow run teamcity-trigger.yml

# View recent runs
gh run list --limit 10

# Watch workflow
gh run watch

# View TeamCity logs
docker logs teamcity-server --tail 100 -f

# Restart TeamCity
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml restart
```

---

**Integration Status:** ✅ Configuration Complete  
**Deployment Status:** ⏳ Awaiting Manual Setup (Steps 1-6)  
**Production Ready:** ✅ Yes (after setup)

**Questions?** Check troubleshooting section or create an issue with label `ci-cd`

---

*Last Updated: November 9, 2025*  
*Stack: GitHub Actions + TeamCity 2025.07 + Docker + Supabase + Render + Vercel*
