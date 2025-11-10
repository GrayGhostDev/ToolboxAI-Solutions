# TeamCity-GitHub Integration Setup Checklist

**Last Updated:** November 10, 2025
**Purpose:** Complete guide for setting up TeamCity Cloud with GitHub integration for ToolBoxAI-Solutions
**Estimated Time:** 45-60 minutes

---

## Prerequisites

### System Requirements
- [ ] TeamCity Cloud account (jetbrains.com/teamcity/cloud)
- [ ] GitHub account with admin access to repository
- [ ] Docker Desktop installed and running
- [ ] Network access to TeamCity Cloud and GitHub
- [ ] Terminal/shell access

### Required Credentials
- [ ] GitHub Personal Access Token (will create in Step 1)
- [ ] Docker Hub credentials (if using Docker registry)
- [ ] TeamCity Cloud instance URL and credentials

---

## Phase 1: GitHub Personal Access Token Setup

### Step 1.1: Create GitHub Token

1. Navigate to GitHub Settings:
   ```
   https://github.com/settings/tokens
   ```

2. Click "Generate new token (classic)"

3. Configure token settings:
   - **Token name:** `TeamCity Cloud Integration - ToolBoxAI`
   - **Expiration:** 90 days (recommended) or No expiration
   - **Select scopes:**
     ```
     ✅ repo (Full control of private repositories)
        ✅ repo:status
        ✅ repo_deployment
        ✅ public_repo
        ✅ repo:invite
     ✅ read:org (Read org and team membership)
     ✅ write:repo_hook (Write repository hooks)
     ```

4. Click "Generate token"

5. **IMPORTANT:** Copy token immediately and save securely
   - Token format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - Store in password manager
   - You will NOT be able to see this token again

### Step 1.2: Add Token to TeamCity

1. Log into TeamCity Cloud instance

2. Navigate to:
   ```
   Administration → Root Project → Connections
   ```

3. Click "Add Connection"

4. Select "GitHub.com" as connection type

5. Configure connection:
   - **Display name:** `GitHub - ToolBoxAI Repository`
   - **Repository URL:** `https://github.com/[YOUR_ORG]/ToolBoxAI-Solutions`
   - **Authentication method:** Personal Access Token
   - **Token:** Paste the token from Step 1.1
   - **Test connection:** Click to verify

6. Save connection

### Step 1.3: Create Credentials Parameter

1. Navigate to:
   ```
   Administration → Root Project → Parameters
   ```

2. Click "Add Parameter"

3. Configure parameter:
   - **Name:** `credentialsJSON:github-token`
   - **Kind:** Environment variable (env.)
   - **Type:** Password
   - **Value:** Paste the GitHub token
   - **Spec:** Leave empty
   - **Description:** GitHub PAT for VCS operations

4. Save parameter

**Verification:**
- [ ] Connection test passes
- [ ] Parameter appears in project parameters list
- [ ] Token is masked in UI (shows as •••••)

---

## Phase 2: TeamCity Versioned Settings Import

### Step 2.1: Enable Versioned Settings

1. Navigate to:
   ```
   Administration → Root Project → Versioned Settings
   ```

2. Click "Enable versioned settings"

3. Configure synchronization:
   - **Synchronization:** Two-way sync (allow TeamCity to commit changes)
   - **VCS root:** Create new VCS root
   - **VCS type:** Git
   - **Fetch URL:** `https://github.com/[YOUR_ORG]/ToolBoxAI-Solutions.git`
   - **Default branch:** `refs/heads/main`
   - **Authentication method:** Password (use GitHub token)
   - **Username:** Your GitHub username
   - **Password:** GitHub token from Phase 1
   - **Settings format:** Kotlin DSL
   - **Settings path:** `.teamcity`
   - **Use settings from VCS:** Yes

4. Click "Apply" and wait for import

### Step 2.2: Verify Build Configurations Import

After import completes, verify the following build configurations appear:

**Root Build Configurations:**
- [ ] 1. Test Infrastructure
- [ ] 2. Backend Unit Tests
- [ ] 3. Backend Integration Tests
- [ ] 4. Frontend Tests
- [ ] 5. Security Scan
- [ ] 6. Accessibility Tests
- [ ] 7. Database Migration Test
- [ ] 8. Build Backend Image
- [ ] 9. Build Frontend Image
- [ ] 10. Deploy Staging
- [ ] 11. Deploy Production

**Expected structure:**
```
Root Project
└── ToolBoxAI-Solutions
    ├── Testing
    │   ├── Test Infrastructure
    │   ├── Backend Unit Tests
    │   ├── Backend Integration Tests
    │   ├── Frontend Tests
    │   ├── Security Scan
    │   ├── Accessibility Tests
    │   └── Database Migration Test
    ├── Build
    │   ├── Build Backend Image
    │   └── Build Frontend Image
    └── Deploy
        ├── Deploy Staging
        └── Deploy Production
```

### Step 2.3: Configure Build Chains

1. Navigate to:
   ```
   Administration → ToolBoxAI-Solutions → Build Chains
   ```

2. Verify build chain dependencies:
   - **Testing Phase:** All test configs run in parallel
   - **Build Phase:** Depends on successful testing phase
   - **Deploy Phase:** Depends on successful build phase

**Verification:**
- [ ] All 11 build configurations visible
- [ ] Build chains configured correctly
- [ ] No import errors in TeamCity log

---

## Phase 3: Docker Registry Credentials

### Step 3.1: Docker Hub Credentials (if using Docker Hub)

1. Navigate to:
   ```
   Administration → Root Project → Connections
   ```

2. Click "Add Connection"

3. Select "Docker Registry" as connection type

4. Configure connection:
   - **Display name:** `Docker Hub - ToolBoxAI`
   - **Registry URL:** `https://index.docker.io/v1/`
   - **Username:** Your Docker Hub username
   - **Password:** Docker Hub access token or password
   - **Test connection:** Click to verify

5. Save connection

### Step 3.2: TeamCity Cloud Docker Credentials

1. Navigate to:
   ```
   Administration → Root Project → Parameters
   ```

2. Add parameter:
   - **Name:** `docker-hub-password`
   - **Kind:** Environment variable (env.)
   - **Type:** Password
   - **Value:** Docker Hub password/token
   - **Description:** Docker Hub authentication

3. Add parameter:
   - **Name:** `teamcity-cloud-docker`
   - **Kind:** Environment variable (env.)
   - **Type:** Password
   - **Value:** TeamCity Cloud Docker registry token
   - **Description:** TeamCity Cloud registry authentication

**Verification:**
- [ ] Docker Hub connection test passes
- [ ] Both password parameters created
- [ ] Passwords are masked in UI

---

## Phase 4: Environment Variables Configuration

### Step 4.1: Required Environment Variables

Navigate to:
```
Administration → Root Project → Parameters
```

Add the following parameters:

#### Database Configuration
```
DATABASE_URL
  Type: Password
  Value: postgresql://user:pass@localhost:5432/toolboxai
  Description: PostgreSQL connection string

REDIS_URL
  Type: Text
  Value: redis://localhost:6379/0
  Description: Redis connection string
```

#### API Keys and Secrets
```
OPENAI_API_KEY
  Type: Password
  Value: sk-...
  Description: OpenAI API key for LLM features

JWT_SECRET_KEY
  Type: Password
  Value: [Generate with: openssl rand -hex 32]
  Description: JWT token signing secret

PUSHER_KEY
  Type: Text
  Value: your_pusher_key
  Description: Pusher Channels key

PUSHER_SECRET
  Type: Password
  Value: your_pusher_secret
  Description: Pusher Channels secret

PUSHER_APP_ID
  Type: Text
  Value: your_app_id
  Description: Pusher application ID
```

#### Roblox Integration
```
ROBLOX_API_KEY
  Type: Password
  Value: your_roblox_api_key
  Description: Roblox API authentication

ROBLOX_UNIVERSE_ID
  Type: Text
  Value: your_universe_id
  Description: Roblox universe identifier
```

#### Application Configuration
```
ENVIRONMENT
  Type: Text
  Value: staging
  Description: Deployment environment (staging/production)

LOG_LEVEL
  Type: Text
  Value: INFO
  Description: Application logging level

CORS_ORIGINS
  Type: Text
  Value: http://localhost:5179,https://toolboxai-staging.com
  Description: Allowed CORS origins (comma-separated)
```

#### Build Configuration
```
DOCKER_REGISTRY
  Type: Text
  Value: toolboxai
  Description: Docker registry/organization name

IMAGE_TAG
  Type: Text
  Value: %build.number%
  Description: Docker image tag (uses TeamCity build number)
```

### Step 4.2: Environment-Specific Parameters

#### Staging Environment

Create parameter group "Staging":
```
BACKEND_URL
  Value: https://api-staging.toolboxai.com

FRONTEND_URL
  Value: https://staging.toolboxai.com

DATABASE_URL
  Value: [Staging database connection]
```

#### Production Environment

Create parameter group "Production":
```
BACKEND_URL
  Value: https://api.toolboxai.com

FRONTEND_URL
  Value: https://toolboxai.com

DATABASE_URL
  Value: [Production database connection]
```

**Verification:**
- [ ] All required parameters created
- [ ] Sensitive values are Password type
- [ ] Parameter descriptions clear
- [ ] Environment-specific groups configured

---

## Phase 5: Build Agent Configuration

### Step 5.1: Configure Build Agent

1. Navigate to:
   ```
   Administration → Agents
   ```

2. Verify cloud agent is available and connected

3. Check agent requirements:
   - **Docker:** Installed and running
   - **Python:** 3.12+
   - **Node.js:** 22 LTS
   - **Git:** Latest version
   - **Disk space:** 20GB+ free

### Step 5.2: Agent Pools

1. Navigate to:
   ```
   Administration → Agent Pools
   ```

2. Create pool for ToolBoxAI:
   - **Name:** `ToolBoxAI Cloud Agents`
   - **Max agents:** 5
   - **Assign agents:** Select available cloud agents

**Verification:**
- [ ] At least one agent is connected
- [ ] Agent has required tools installed
- [ ] Agent pool configured

---

## Phase 6: Triggers and Build Features

### Step 6.1: VCS Trigger Configuration

For each build configuration, verify triggers:

1. Navigate to build configuration → Triggers

2. Configure VCS trigger:
   - **Type:** VCS Trigger
   - **Branch filter:**
     ```
     +:refs/heads/main
     +:refs/heads/develop
     +:refs/heads/feature/*
     +:refs/pull/*/merge
     ```
   - **Trigger on:** Push to branches and PR updates
   - **Per-check triggers:** Enabled

### Step 6.2: Build Features

For each build configuration, verify features:

1. Navigate to build configuration → Build Features

2. Add/verify features:
   - **Pull Requests:** GitHub integration enabled
   - **Commit Status Publisher:** Publish build status to GitHub
   - **Docker Support:** Docker registry connections configured
   - **Shared Resources:** Build locks configured (for deploy configs)

**Verification:**
- [ ] VCS triggers configured on all configs
- [ ] Build features enabled
- [ ] GitHub status publishing works

---

## Phase 7: Testing and Verification

### Step 7.1: Test Build Execution

1. Run Test Infrastructure build:
   ```
   Build → Run → Test Infrastructure
   ```

2. Monitor build log for:
   - [ ] Repository clones successfully
   - [ ] Dependencies install
   - [ ] Tests execute
   - [ ] Build completes

### Step 7.2: Test GitHub Integration

1. Create a test branch:
   ```bash
   git checkout -b test/teamcity-integration
   git commit --allow-empty -m "test: verify TeamCity integration"
   git push origin test/teamcity-integration
   ```

2. Verify:
   - [ ] TeamCity detects push
   - [ ] Build starts automatically
   - [ ] GitHub shows build status
   - [ ] Build status updates in PR (if PR created)

### Step 7.3: Test Pull Request Integration

1. Create a test PR from test branch

2. Verify:
   - [ ] TeamCity runs builds on PR
   - [ ] PR shows build status checks
   - [ ] Comments from TeamCity appear (if configured)

### Step 7.4: Run Verification Script

```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions
./scripts/teamcity/verify_integration.sh
```

Expected output:
```
✓ TeamCity server is accessible
✓ Build agents are connected
✓ VCS root connection successful
✓ GitHub authentication working
✓ Build configurations loaded
✓ All prerequisites met

Integration Status: READY
```

**Verification:**
- [ ] All manual tests pass
- [ ] Verification script passes
- [ ] No errors in TeamCity log

---

## Phase 8: Final Configuration

### Step 8.1: Notification Rules

1. Navigate to:
   ```
   Administration → Notifications
   ```

2. Configure notification rules:
   - **Build failed:** Email to team
   - **Build fixed:** Email to team
   - **First failure:** Immediate notification
   - **Hanging build:** After 30 minutes

### Step 8.2: Cleanup Policies

1. Navigate to:
   ```
   Administration → Cleanup
   ```

2. Configure cleanup:
   - **Keep builds:** Last 30 days
   - **Keep artifacts:** Last 10 successful builds
   - **Clean history:** After 90 days

### Step 8.3: Project Permissions

1. Navigate to:
   ```
   Administration → Roles
   ```

2. Configure team permissions:
   - **Developers:** View, run builds, comment
   - **DevOps:** All permissions including configuration
   - **Viewers:** Read-only access

**Verification:**
- [ ] Notifications configured
- [ ] Cleanup policies set
- [ ] Permissions configured

---

## Troubleshooting

### Issue: VCS Root Connection Failed

**Symptoms:**
- "Authentication failed" error
- "Repository not found" error

**Solutions:**
1. Verify GitHub token has correct scopes
2. Check token hasn't expired
3. Verify repository URL is correct
4. Test token with:
   ```bash
   curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
   ```

### Issue: Build Configurations Not Imported

**Symptoms:**
- Versioned settings enabled but no builds appear
- "Failed to load settings" error

**Solutions:**
1. Check .teamcity directory exists in repository
2. Verify settings.kts file is valid Kotlin
3. Check TeamCity logs for import errors
4. Try manual re-import from VCS

### Issue: Docker Authentication Failed

**Symptoms:**
- "unauthorized: authentication required" error
- Docker push fails

**Solutions:**
1. Verify Docker Hub credentials are correct
2. Check docker-hub-password parameter exists
3. Test credentials locally:
   ```bash
   docker login -u USERNAME -p PASSWORD
   ```

### Issue: Build Agent Not Available

**Symptoms:**
- "No compatible agents" message
- Builds queue indefinitely

**Solutions:**
1. Check agent is connected (Administration → Agents)
2. Verify agent meets requirements
3. Check agent pool assignments
4. Restart build agent if needed

### Issue: Environment Variables Not Set

**Symptoms:**
- Build fails with "undefined variable" errors
- Services can't connect to database

**Solutions:**
1. Verify parameter names match exactly (case-sensitive)
2. Check parameters are set at correct level (Root Project vs Build Config)
3. Verify password parameters are not empty
4. Check parameter inheritance

---

## Post-Setup Checklist

After completing all phases, verify:

- [ ] GitHub connection working
- [ ] All 11 build configurations visible
- [ ] At least one build agent connected
- [ ] All environment variables configured
- [ ] Docker registry authenticated
- [ ] VCS triggers working
- [ ] Test build executed successfully
- [ ] GitHub status updates working
- [ ] Pull request integration working
- [ ] Notifications configured
- [ ] Cleanup policies set
- [ ] Team permissions configured
- [ ] Verification script passes

---

## Next Steps

1. **Review Build Configurations:**
   - Customize build steps if needed
   - Adjust triggers and schedules
   - Configure branch-specific settings

2. **Set Up Monitoring:**
   - Configure build failure alerts
   - Set up performance monitoring
   - Track build metrics

3. **Documentation:**
   - Share setup guide with team
   - Document custom configurations
   - Create runbooks for common issues

4. **Optimization:**
   - Review build times
   - Optimize Docker layers
   - Configure build caching

---

## Additional Resources

### Documentation
- TeamCity Documentation: https://www.jetbrains.com/help/teamcity/
- GitHub Integration: https://www.jetbrains.com/help/teamcity/integrating-teamcity-with-vcs-hosting-services.html
- Kotlin DSL Reference: https://www.jetbrains.com/help/teamcity/kotlin-dsl.html

### Support
- TeamCity Cloud Support: https://www.jetbrains.com/support/teamcity/
- GitHub API Documentation: https://docs.github.com/en/rest
- ToolBoxAI Team: Internal documentation in /docs/08-operations/

### Helper Scripts
- **Validate Setup:** `./scripts/teamcity/validate_setup.sh` (NEW - validates complete setup)
- **Trigger Cloud Build:** `./infrastructure/teamcity/trigger-cloud-build.sh`
- Check Prerequisites: `./scripts/teamcity/check_prerequisites.sh`
- Test GitHub Connection: `./scripts/teamcity/test_github_connection.sh`
- Verify Integration: `./scripts/teamcity/verify_integration.sh`
- Import Build Configs: `./scripts/teamcity/import_build_configs.sh`

### Security Notes

**IMPORTANT:** As of November 10, 2025, all TeamCity scripts have been updated to require environment variables for authentication. The hardcoded token vulnerability has been resolved.

**Required Environment Variables:**
```bash
# Set TeamCity token (REQUIRED)
export TEAMCITY_PIPELINE_ACCESS_TOKEN='your-token-here'

# Optional: Set GitHub token for validation
export GITHUB_TOKEN='your-github-token'
```

**To get a TeamCity token:**
1. Log in to TeamCity: https://grayghost-toolboxai.teamcity.com
2. Go to Profile → Access Tokens
3. Create a new token with appropriate permissions
4. Export the token as shown above

**Validation:**
Run the validation script before using any TeamCity automation:
```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions
./scripts/teamcity/validate_setup.sh
```

This will verify:
- Environment variables are set correctly
- TeamCity API is accessible
- Project and build configurations exist
- VCS roots are configured
- GitHub repository is accessible

---

**Setup Completion Time:** Record your actual time for future reference
**Issues Encountered:** Document for team knowledge base
**Completed By:** [Your Name]
**Date Completed:** [Date]

---

*This checklist is part of the ToolBoxAI-Solutions TeamCity CI/CD setup.*
*Last updated: November 10, 2025*
*Version: 1.0.0*
