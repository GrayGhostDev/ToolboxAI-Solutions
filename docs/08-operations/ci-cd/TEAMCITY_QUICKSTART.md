# TeamCity Quick Start Guide

**Last Updated:** November 10, 2025
**Purpose:** Fast-track TeamCity setup for ToolBoxAI-Solutions
**Audience:** Developers and DevOps engineers

---

## Overview

This guide provides two paths to get started with TeamCity:

1. **5-Minute Local Setup** - Test builds locally without full GitHub integration
2. **30-Minute Full Setup** - Complete GitHub integration with cloud deployment

Choose the path that matches your immediate needs.

---

## Path 1: 5-Minute Local Setup

**Goal:** Run TeamCity builds locally to verify setup

### Prerequisites
- Docker Desktop installed and running
- Repository cloned locally
- 10GB+ free disk space

### Steps

#### 1. Run Prerequisites Check (1 min)

```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions
./scripts/teamcity/check_prerequisites.sh
```

Expected output:
```
✓ Docker is installed
✓ Docker daemon is running
✓ Python 3.12+ is installed
✓ Node.js 22 LTS is installed
✓ All critical prerequisites met!
```

If any checks fail, install the missing tools before continuing.

#### 2. Start Local Services (2 min)

```bash
# Start PostgreSQL and Redis
docker compose up -d postgres redis

# Verify services are running
docker compose ps
```

Expected output:
```
NAME                    STATUS
toolboxai-postgres-1    Up 30 seconds
toolboxai-redis-1       Up 30 seconds
```

#### 3. Run a Local Build (2 min)

```bash
# Activate Python virtual environment
source venv/bin/activate

# Run backend tests locally (simulates TeamCity build)
pytest apps/backend/tests/ -v

# Run frontend tests
pnpm --filter @toolboxai/dashboard test
```

If tests pass, your local environment is ready for TeamCity integration.

### What's Next?

- **Ready for GitHub integration?** Continue to Path 2 below
- **Want to customize builds?** Review `.teamcity/settings.kts`
- **Having issues?** Check the Troubleshooting section at the end

---

## Path 2: 30-Minute Full Setup

**Goal:** Complete TeamCity Cloud integration with GitHub

### Time Breakdown
- GitHub token setup: 5 minutes
- TeamCity configuration: 15 minutes
- Testing and verification: 10 minutes

### Prerequisites
- TeamCity Cloud account (create at jetbrains.com/teamcity/cloud)
- GitHub account with admin access to repository
- Path 1 completed (local environment verified)

### Steps

#### Step 1: Create GitHub Personal Access Token (5 min)

1. **Navigate to GitHub Settings:**
   ```
   https://github.com/settings/tokens
   ```

2. **Generate New Token (Classic):**
   - Token name: `TeamCity Cloud - ToolBoxAI`
   - Expiration: 90 days (recommended)
   - Scopes:
     ```
     ✅ repo (Full control)
     ✅ read:org (Read organization)
     ✅ write:repo_hook (Write webhooks)
     ```

3. **Copy Token Immediately:**
   - Token format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - Save in password manager
   - You won't see it again!

4. **Test Token:**
   ```bash
   export GITHUB_TOKEN="your-token-here"
   ./scripts/teamcity/test_github_connection.sh
   ```

   Expected output:
   ```
   ✓ Token authentication successful
   ✓ All required scopes present
   ✓ Repository is accessible
   ✓ All tests passed!
   ```

#### Step 2: Configure TeamCity Cloud (15 min)

1. **Log in to TeamCity:**
   - URL: Your TeamCity Cloud instance (e.g., `https://grayghost-toolboxai.teamcity.com`)
   - Use JetBrains Account credentials

2. **Enable Versioned Settings:**
   ```
   Navigation: Administration → Root Project → Versioned Settings
   ```

   Configuration:
   ```
   ☑ Enable versioned settings

   Synchronization:      Two-way sync
   VCS type:             Git
   Fetch URL:            https://github.com/[YOUR_ORG]/ToolBoxAI-Solutions.git
   Default branch:       refs/heads/main
   Authentication:       Password
   Username:             [Your GitHub username]
   Password:             [GitHub token from Step 1]
   Settings format:      Kotlin
   Settings path:        .teamcity
   ☑ Use settings from VCS
   ```

   Click **Apply** and wait for import (1-2 minutes).

3. **Add GitHub Token to Parameters:**
   ```
   Navigation: Administration → Root Project → Parameters
   ```

   Add parameter:
   ```
   Name:        credentialsJSON:github-token
   Kind:        Environment variable (env.)
   Type:        Password
   Value:       [GitHub token from Step 1]
   Description: GitHub PAT for VCS operations
   ```

4. **Verify Build Configurations Imported:**
   ```
   Navigation: Projects → ToolBoxAI-Solutions
   ```

   You should see 11 build configurations:
   ```
   Testing/
     ├── Test Infrastructure
     ├── Backend Unit Tests
     ├── Backend Integration Tests
     ├── Frontend Tests
     ├── Security Scan
     ├── Accessibility Tests
     └── Database Migration Test

   Build/
     ├── Build Backend Image
     └── Build Frontend Image

   Deploy/
     ├── Deploy Staging
     └── Deploy Production
   ```

5. **Configure Environment Variables:**
   ```
   Navigation: Administration → Root Project → Parameters
   ```

   Add required parameters (minimum set):
   ```
   DATABASE_URL          (Password)  postgresql://user:pass@host:5432/db
   REDIS_URL             (Text)      redis://localhost:6379/0
   OPENAI_API_KEY        (Password)  sk-...
   JWT_SECRET_KEY        (Password)  [Generate: openssl rand -hex 32]
   DOCKER_REGISTRY       (Text)      toolboxai
   IMAGE_TAG             (Text)      %build.number%
   ```

#### Step 3: Test Integration (10 min)

1. **Run First Build Manually:**
   ```
   Navigation: Build → Test Infrastructure → Run
   ```

   Monitor the build log. Expected:
   ```
   ✓ Repository cloned
   ✓ Dependencies installed
   ✓ Tests executed
   ✓ Build completed successfully
   ```

2. **Test Automatic Trigger:**
   ```bash
   # Create test branch
   git checkout -b test/teamcity-integration

   # Make trivial change
   echo "# TeamCity test" >> README.md

   # Commit and push
   git add README.md
   git commit -m "test: verify TeamCity integration"
   git push origin test/teamcity-integration
   ```

   Verify in TeamCity:
   ```
   ✓ Build triggered automatically
   ✓ GitHub shows build status
   ```

3. **Test Pull Request Integration:**
   - Create PR from test branch to main
   - Verify TeamCity runs builds on PR
   - Check PR shows build status checks

4. **Run Verification Script:**
   ```bash
   export TEAMCITY_URL="https://your-instance.teamcity.com"
   export TEAMCITY_PIPELINE_ACCESS_TOKEN="your-teamcity-token"

   ./scripts/teamcity/verify_integration.sh
   ```

   Expected output:
   ```
   ✓ TeamCity server is accessible
   ✓ Build agents are connected
   ✓ VCS root connection successful
   ✓ GitHub authentication working
   ✓ Build configurations loaded

   Integration Status: READY
   ```

### Congratulations!

Your TeamCity-GitHub integration is complete and ready for production use.

---

## Common Tasks Reference

### Trigger a Build Manually

**Via UI:**
```
Build → [Configuration Name] → Run
```

**Via API:**
```bash
curl -X POST \
  -H "Authorization: Bearer $TEAMCITY_PIPELINE_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"buildType":{"id":"BUILD_TYPE_ID"}}' \
  "$TEAMCITY_URL/app/rest/buildQueue"
```

**Via Git Push:**
```bash
git push origin main  # Triggers on push to main
```

### Check Build Status

**Via UI:**
```
Projects → ToolBoxAI-Solutions → Build Overview
```

**Via API:**
```bash
curl -H "Authorization: Bearer $TEAMCITY_PIPELINE_ACCESS_TOKEN" \
  "$TEAMCITY_URL/app/rest/builds?locator=buildType:(id:BUILD_TYPE_ID)"
```

**Via GitHub:**
- Check commit status indicators
- View PR build checks

### View Build Logs

**Via UI:**
```
Build → [Build Number] → Build Log
```

**Download logs:**
```bash
curl -H "Authorization: Bearer $TEAMCITY_PIPELINE_ACCESS_TOKEN" \
  "$TEAMCITY_URL/app/rest/builds/id:BUILD_ID/log" \
  -o build.log
```

### Update Build Configuration

**Via UI:**
```
Administration → Build Configuration → Edit
```

**Via Kotlin DSL:**
```bash
# 1. Edit .teamcity/settings.kts locally
# 2. Commit and push changes
# 3. TeamCity auto-syncs (if two-way sync enabled)

git add .teamcity/
git commit -m "chore: update build configuration"
git push origin main
```

### Add Environment Variable

**Via UI:**
```
Administration → Project → Parameters → Add Parameter
```

**Via Kotlin DSL:**
```kotlin
// In .teamcity/settings.kts
params {
    password("NEW_VARIABLE", "credentialsJSON:...", display = ParameterDisplay.HIDDEN)
}
```

---

## Troubleshooting Quick Reference

### Issue: Build Not Starting

**Check:**
1. Build agent is connected:
   ```
   Administration → Agents
   ```
2. Build agent meets requirements
3. No conflicting builds running

**Fix:**
```bash
# Check agent status
./scripts/teamcity/check_prerequisites.sh

# Restart agent (if self-hosted)
# TeamCity Cloud agents restart automatically
```

### Issue: VCS Root Connection Failed

**Check:**
```bash
./scripts/teamcity/test_github_connection.sh $GITHUB_TOKEN
```

**Common causes:**
- Token expired
- Insufficient permissions
- Wrong repository URL

**Fix:**
1. Create new GitHub token with correct scopes
2. Update token in TeamCity parameters
3. Test VCS root connection in TeamCity UI

### Issue: Environment Variable Not Found

**Check:**
```
Administration → Root Project → Parameters
```

**Verify:**
- Parameter name matches exactly (case-sensitive)
- Parameter is not empty
- Parameter type is correct (Text vs Password)

**Fix:**
```bash
# Add via UI (see Step 2.5 above)
# Or via Kotlin DSL
```

### Issue: Docker Build Fails

**Check:**
1. Docker credentials configured
2. Docker daemon is running
3. Sufficient disk space

**Fix:**
```bash
# Local testing
docker compose build backend
docker compose build dashboard

# Check Docker status
docker info
```

### Issue: Tests Failing in TeamCity but Pass Locally

**Check:**
1. Environment variables match
2. Dependencies are installed
3. Database/Redis accessible

**Fix:**
```bash
# Compare environments
./scripts/teamcity/check_prerequisites.sh

# Check TeamCity build log for specific errors
# Update build configuration if needed
```

---

## Next Steps

After completing setup, consider:

### 1. Configure Notifications

```
Administration → Notifications
```

Set up:
- Build failure alerts
- First failure notifications
- Build success after failure

### 2. Set Up Deployment Keys

For production deployments:
```
Administration → Deploy → Production → Parameters
```

Add:
- Production database credentials
- API keys for production services
- Deployment target credentials

### 3. Optimize Build Performance

Review:
- Build cache configuration
- Parallel execution settings
- Agent pool assignments

### 4. Set Up Monitoring

Configure:
- Build time tracking
- Test result trends
- Deployment frequency metrics

### 5. Document Custom Configurations

Create runbooks for:
- Emergency rollback procedures
- Manual deployment steps
- Build troubleshooting

---

## Additional Resources

### Documentation
- **Full Setup Checklist:** `docs/08-operations/ci-cd/TEAMCITY_GITHUB_SETUP_CHECKLIST.md`
- **TeamCity Official Docs:** https://www.jetbrains.com/help/teamcity/
- **Kotlin DSL Reference:** https://www.jetbrains.com/help/teamcity/kotlin-dsl.html

### Helper Scripts
```bash
# Check prerequisites
./scripts/teamcity/check_prerequisites.sh

# Test GitHub connection
./scripts/teamcity/test_github_connection.sh [TOKEN]

# Import build configurations
./scripts/teamcity/import_build_configs.sh

# Verify integration
./scripts/teamcity/verify_integration.sh
```

### Support
- **TeamCity Cloud Support:** https://www.jetbrains.com/support/teamcity/
- **GitHub API Docs:** https://docs.github.com/en/rest
- **Internal Docs:** `/docs/08-operations/`

---

## FAQ

### Q: How long does the initial setup take?

**A:**
- Local setup: 5 minutes
- Full GitHub integration: 30 minutes
- First-time users: Allow 45-60 minutes for learning

### Q: Can I use TeamCity without GitHub integration?

**A:** Yes! Follow Path 1 (Local Setup) and trigger builds manually via UI or API.

### Q: What if I don't have a TeamCity Cloud account?

**A:**
1. Visit https://www.jetbrains.com/teamcity/cloud/
2. Sign up with JetBrains Account
3. Choose free tier or appropriate plan
4. Return to this guide

### Q: Can I use self-hosted TeamCity instead of Cloud?

**A:** Yes, but configuration may differ slightly. This guide focuses on TeamCity Cloud.

### Q: How do I add a new build configuration?

**A:**
1. Edit `.teamcity/settings.kts`
2. Add new `buildType` definition
3. Commit and push
4. TeamCity auto-imports (if two-way sync enabled)

### Q: What if builds fail after working locally?

**A:** Common causes:
- Different environment variables
- Missing dependencies on build agent
- Database/service connectivity issues

Run `./scripts/teamcity/check_prerequisites.sh` and compare environments.

### Q: How do I roll back a failed deployment?

**A:**
1. Navigate to previous successful build
2. Click "Run with custom parameters"
3. Deploy to production
4. Or use manual rollback procedures in production runbook

### Q: Can I test builds before pushing to GitHub?

**A:** Yes:
```bash
# Run tests locally
pytest
pnpm test

# Validate Kotlin DSL
./scripts/teamcity/import_build_configs.sh

# Test in Docker (simulates CI environment)
docker compose up --build
```

---

**Ready to start?** Choose your path above and begin setup!

**Questions?** Check the full checklist or reach out to the DevOps team.

---

*Last updated: November 10, 2025*
*Version: 1.0.0*
*Part of ToolBoxAI-Solutions CI/CD documentation*
