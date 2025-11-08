# TeamCity First-Time Setup Guide

**Created**: 2025-11-08
**TeamCity Version**: 2025.07 (build 197242)
**Database**: Supabase PostgreSQL 17.6
**Status**: Ready for initialization

---

## 🎯 Pre-Setup Checklist

Before starting the setup wizard, ensure:

- [x] TeamCity server is running (http://localhost:8111)
- [x] Docker Desktop is responsive
- [x] Supabase PostgreSQL 17 is running and accessible
- [x] `teamcity` database exists in Supabase PostgreSQL
- [x] All 3 build agents are running
- [x] Super user token available: `6313972982264473303`

---

## 📋 Step-by-Step Setup

### Step 1: Initial Access

1. Open your web browser
2. Navigate to **http://localhost:8111**
3. You should see the TeamCity initialization screen showing:
   ```
   The database is empty.

   TeamCity database is configured by database.properties file
   Database type: PostgreSQL

   If you proceed, a new database will be created.
   ```

### Step 2: Database Initialization

**Current Configuration** (auto-detected):
```
Database type: POSTGRESQL
Connection URL: jdbc:postgresql://db.supabase.internal:5432/teamcity
JDBC driver version: 42.7 (PostgreSQL JDBC Driver)
Database system version: 17.6 (PostgreSQL)
```

**Action**:
1. **Click "Proceed"** to initialize the database
2. Wait 2-3 minutes while TeamCity creates schema (~152 tables)
3. Monitor progress bar until completion

**What Happens**:
- TeamCity creates database schema (version 1023)
- Initializes server configuration
- Sets up project structure
- Prepares agent communication

### Step 3: Accept License Agreement

1. Read the JetBrains TeamCity license agreement
2. Check **"I have read and accept the License Agreement"**
3. Click **"Continue"**

### Step 4: Administrator Account Creation

**Important**: Create a strong administrator account (this replaces super user access)

**Recommended Settings**:
```
Username: admin
Full name: ToolBoxAI Admin
Email: admin@toolboxaisolutions.com
Password: [Use strong password with 16+ characters]
```

**Password Requirements**:
- Minimum 8 characters (recommend 16+)
- Mix of uppercase, lowercase, numbers, symbols
- Store in password manager

**Click**: "Create Account"

### Step 5: Disable Super User Token

**Important Security Step**:

Once logged in with admin account:

1. Navigate to **Administration → Authentication**
2. Find **"Super User"** section
3. Click **"Disable super user access"**
4. Confirm the action

**Why**: Super user tokens bypass all security and should only be used for emergency recovery

---

## 🔧 Post-Setup Configuration

### Step 6: Configure Server Settings

Navigate to **Administration → Global Settings**

#### **Server URL**
```
External URL: https://ci.toolboxaisolutions.com
Internal URL: http://localhost:8111
```

#### **Artifacts**
```
Artifacts directory: /data/teamcity_server/datadir/system/artifacts
Max artifact size: 2GB
Artifact cleaning: Enabled (14 days retention)
```

#### **Build Cache**
```
Status: ✅ Enabled (configured via Kotlin DSL)
Max size: 10GB
Location: /Volumes/G-DRIVE ArmorATD/.../TeamCity/cache
```

### Step 7: Authorize Build Agents

Navigate to **Agents → Unauthorized**

You should see 3 agents waiting for authorization:

#### **Agent 1: Frontend-Builder-01**
```
Purpose: React + Vite + TypeScript builds
Environment: Node.js 22, npm, Docker-in-Docker
Resources: 4GB RAM, 2GB reserved
```
**Action**: Click **"Authorize"**

#### **Agent 2: Backend-Builder-01**
```
Purpose: FastAPI + Python builds
Environment: Python 3.12, pip, Docker-in-Docker
Resources: 4GB RAM, 2GB reserved
```
**Action**: Click **"Authorize"**

#### **Agent 3: Integration-Builder-01**
```
Purpose: Integration tests, E2E tests
Environment: Multi-language (Node.js 22 + Python 3.12)
Resources: 4GB RAM, 2GB reserved
```
**Action**: Click **"Authorize"**

**Verification**:
- Navigate to **Agents → Connected**
- All 3 agents should show status: **Idle**
- Agent pools should show: **Default Pool (3 agents)**

### Step 8: Configure VCS Root

Navigate to **Administration → <Root Project> → VCS Roots**

#### **GitHub Repository Connection**

The VCS root `MainRepository` is already configured in Kotlin DSL, but needs credentials:

```kotlin
Name: ToolBoxAI Main Repository
Type: Git
URL: https://github.com/GrayGhostDev/ToolboxAI-Solutions.git
Default branch: refs/heads/main
Branch specification:
  +:refs/heads/*
  +:refs/tags/*
  +:refs/pull/*/merge
```

**Configure Credentials**:

1. Click **"Create new password parameter"**
2. Name: `credentialsJSON:github-token`
3. Value: [Your GitHub Personal Access Token]
4. **Save**

**GitHub PAT Scopes Required**:
- `repo` (full repository access)
- `workflow` (workflow permissions)
- `read:packages` (if using GitHub Packages)

### Step 9: Configure Docker Registry

Navigate to **Administration → <Root Project> → Docker Registry**

#### **TeamCity Cloud Registry**
```
Name: TeamCity Cloud Registry
URL: https://build-cloud.docker.com:443
Username: thegrayghost23
Password: [Create parameter: credentialsJSON:teamcity-cloud-docker]
```

#### **Docker Hub Registry** (Optional)
```
Name: Docker Hub Registry
URL: https://registry-1.docker.io
Username: thegrayghost23
Password: [Create parameter: credentialsJSON:docker-hub-password]
```

**Test Connection**: Click **"Test Connection"** for each registry

### Step 10: Configure Project Parameters

Navigate to **Administration → <Root Project> → Parameters**

#### **Required Parameters** (Create these):

**API Keys**:
```
env.OPENAI_API_KEY (password): [Your OpenAI API key]
env.ANTHROPIC_API_KEY (password): [Your Anthropic API key]
env.LANGCHAIN_API_KEY (password): [Your LangChain API key]
env.REPLICATE_API_TOKEN (password): [Your Replicate API token]
```

**Deployment Credentials**:
```
env.VERCEL_TOKEN (password): [Your Vercel deployment token]
env.VERCEL_ORG_ID (text): [Your Vercel org ID]
env.VERCEL_PROJECT_ID (text): [Your Vercel project ID]
env.RENDER_API_KEY (password): [Your Render API key]
env.RENDER_SERVICE_ID (text): [Your Render service ID]
```

**Monitoring & Notifications**:
```
env.SENTRY_AUTH_TOKEN (password): [Your Sentry auth token]
env.SLACK_WEBHOOK_URL (password): [Your Slack webhook URL]
env.GITHUB_CLIENT_ID (text): [GitHub OAuth client ID]
env.GITHUB_CLIENT_SECRET (password): [GitHub OAuth client secret]
```

**Note**: Parameters marked as `(password)` should use "Password" type for security

---

## 🔍 Verification Steps

### Verify Database Connection

Navigate to **Administration → Diagnostics → Database**

**Expected**:
```
Database type: PostgreSQL 17.6
Connection: Active
Tables: ~152 tables
Data format version: 1023
```

**Test Query**:
```bash
# From host machine
psql "postgresql://supabase_admin:postgres@localhost:54322/teamcity" -c "\dt" | wc -l
```
Expected output: `~152` (number of tables)

### Verify Build Agents

Navigate to **Agents → Connected**

**For each agent, verify**:
- Status: **Idle** (green)
- Compatibility: **Compatible** with all builds
- Properties detected:
  - `teamcity.agent.name` = [agent name]
  - `system.agent.work.dir` = /data/teamcity_agent/work
  - Docker support: **Enabled**

**Test Agent Communication**:
```bash
# Check agent logs
docker logs teamcity-agent-frontend --tail 50
docker logs teamcity-agent-backend --tail 50
docker logs teamcity-agent-integration --tail 50
```

Expected: No errors, "Agent is running and connected" messages

### Verify VCS Connection

Navigate to **Administration → <Root Project> → VCS Roots → MainRepository**

**Click**: "Test Connection"

**Expected Result**:
```
✅ Connection successful
Latest commit: [commit SHA]
Branch: main
Author: [latest commit author]
```

### Verify Build Cache

Navigate to **Administration → <Root Project> → Build Features**

**Expected**:
```
Feature: Build Cache
Status: ✅ Enabled
Max size: 10GB
Published caches: 0 (increases after first builds)
```

**Verify Cache Directory**:
```bash
ls -lh /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/TeamCity/cache
```

Expected: Directory exists and is writable by UID 1000

---

## 🧪 Run Test Build

### Trigger First Build

Navigate to **Projects → ToolBoxAI Solutions → DashboardBuild**

**Click**: "Run"

**What to Expect**:
1. Build queued (appears in build queue)
2. Agent assigned (Frontend-Builder-01)
3. VCS checkout (clones repository)
4. Build steps execute:
   - Setup Node.js
   - Install Dependencies
   - TypeScript Check
   - ESLint Check
   - Unit Tests
   - Build Production
   - Bundle Analysis
   - Build Docker Image
   - Push Docker Image (on success)

**First Build Notes**:
- Will be slower (no cache yet)
- Will download all dependencies
- Will build Docker base images
- Expected time: 15-20 minutes

**Success Criteria**:
- Build status: **Success** (green)
- Artifacts created: `dashboard-build-*.zip`
- Docker image pushed to registry
- Build cache published

**If Build Fails**:
1. Check build logs for errors
2. Verify all credentials are configured
3. Check agent logs for issues
4. Consult troubleshooting guide below

---

## 🔧 Troubleshooting

### Issue: "Database connection failed"

**Symptoms**: Cannot connect to PostgreSQL during initialization

**Solution**:
```bash
# 1. Verify Supabase PostgreSQL is running
docker ps | grep supabase_db_supabase

# 2. Check network connectivity
docker network inspect supabase_network_supabase | grep teamcity-server

# 3. Test database connection
psql "postgresql://supabase_admin:postgres@localhost:54322/teamcity" -c "SELECT 1"

# 4. Restart TeamCity if needed
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml restart teamcity-server
```

### Issue: "Agents not connecting"

**Symptoms**: Agents remain in "Connecting..." state

**Solution**:
```bash
# 1. Check agent logs
docker logs teamcity-agent-frontend --tail 100

# 2. Verify server URL is accessible from agent
docker exec teamcity-agent-frontend curl -I http://teamcity-server:8111

# 3. Restart agents
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml restart \
  teamcity-agent-frontend teamcity-agent-backend teamcity-agent-integration
```

### Issue: "Build fails with 'VCS root not found'"

**Symptoms**: Build cannot clone repository

**Solution**:
1. Navigate to **Administration → VCS Roots → MainRepository**
2. Click **"Test Connection"**
3. If fails, verify GitHub token has correct permissions
4. Regenerate GitHub PAT if needed
5. Update `credentialsJSON:github-token` parameter

### Issue: "Docker image push fails"

**Symptoms**: Build succeeds but Docker push step fails

**Solution**:
1. Verify Docker registry credentials
2. Test connection:
   ```bash
   docker login https://build-cloud.docker.com:443 -u thegrayghost23
   ```
3. Update `credentialsJSON:teamcity-cloud-docker` if needed

### Issue: "Build cache not working"

**Symptoms**: All builds re-download dependencies

**Solution**:
```bash
# 1. Verify cache directory exists and is writable
ls -la /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions/TeamCity/cache

# 2. Check TeamCity cache configuration
# Navigate to: Administration → Build Features → Build Cache

# 3. Verify build cache is enabled in settings.kts
grep -A10 "BuildCache" .teamcity/settings.kts

# 4. Check first build completed (cache published after first build)
```

---

## 📚 Next Steps

After completing first-time setup:

1. **Phase 2**: Apply Kotlin DSL best practices
   - Refactor config parameters to constants
   - Convert templates to extension functions
   - Add checkout rules optimization

2. **Phase 3**: Implement parallel tests
   - Configure `parallelTests` for DashboardBuild
   - Configure `parallelTests` for BackendBuild
   - Monitor test execution time improvements

3. **Phase 4**: Enhance build cache
   - Add more cache rules for `.ruff_cache`, `.pytest_cache`
   - Monitor cache hit rates
   - Optimize cache size limits

4. **Phase 5**: Configure notifications
   - Set up Slack notifications
   - Configure Pusher for real-time updates
   - Add email notifications for critical builds

5. **Phase 6**: Test deployment pipelines
   - Deploy to development environment
   - Test staging deployment
   - Verify production deployment (with approvals)

---

## 📞 Support Resources

### Documentation
- This guide: `docs/08-operations/ci-cd/TEAMCITY_FIRST_TIME_SETUP.md`
- TeamCity docs: http://localhost:8111/help/teamcity-documentation.html
- Kotlin DSL reference: http://localhost:8111/app/dsl-documentation/

### Configuration Files
- Docker Compose: `infrastructure/docker/compose/docker-compose.teamcity.yml`
- Kotlin DSL: `.teamcity/settings.kts`
- Deployment config: `.teamcity/deployment.kts`

### Useful Commands
```bash
# View TeamCity logs
docker logs teamcity-server --tail 100 --follow

# View agent logs
docker logs teamcity-agent-frontend --tail 100 --follow

# Restart all services
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml restart

# Check service status
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml ps
```

---

## ✅ Setup Completion Checklist

- [ ] TeamCity server initialized with PostgreSQL
- [ ] Administrator account created
- [ ] Super user token disabled
- [ ] All 3 build agents authorized
- [ ] VCS root configured and tested
- [ ] Docker registries configured
- [ ] All required parameters added
- [ ] First test build successful
- [ ] Build cache enabled and working
- [ ] Notifications configured

**Once all items are checked, you're ready to proceed with the implementation plan!**

---

**Setup Guide Version**: 1.0.0
**Last Updated**: 2025-11-08
**Prepared By**: Claude Code Automation

