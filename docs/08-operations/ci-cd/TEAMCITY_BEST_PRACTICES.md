# TeamCity Best Practices Guide

**Created**: 2025-11-08
**TeamCity Version**: 2025.07 (build 197242)
**Project**: ToolBoxAI Solutions
**Audience**: Development Team

---

## 📋 Table of Contents

1. [Configuration as Code](#configuration-as-code)
2. [Build Configuration](#build-configuration)
3. [Agent Management](#agent-management)
4. [Security Practices](#security-practices)
5. [Performance Optimization](#performance-optimization)
6. [Testing Practices](#testing-practices)
7. [Deployment Practices](#deployment-practices)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Team Collaboration](#team-collaboration)

---

## 🔧 Configuration as Code

### ✅ DO: Use Kotlin DSL for All Configuration

**Why**: Version control, code review, reproducibility, and IDE support.

```kotlin
// .teamcity/settings.kts
import jetbrains.buildServer.configs.kotlin.*
import jetbrains.buildServer.configs.kotlin.buildSteps.*
import jetbrains.buildServer.configs.kotlin.triggers.*

version = "2025.07"

project {
    buildType(DashboardBuild)
    buildType(BackendBuild)

    vcsRoot(MainRepository)
}
```

**Benefits**:
- All configuration in Git
- Code review for CI/CD changes
- Easy rollback with Git history
- IDE autocomplete and validation
- Team collaboration on build configs

### ✅ DO: Use Extension Functions Instead of Templates

**2025.07 Best Practice**: Replace templates with extension functions for better reusability.

```kotlin
// ❌ OLD: Using Templates (deprecated pattern)
template {
    name = "DockerBuildTemplate"
    // ... steps
}

object MyBuild : BuildType({
    templates(DockerBuildTemplate)
})

// ✅ NEW: Using Extension Functions (2025.07 pattern)
fun BuildType.dockerBuildDefaults() {
    steps {
        dockerCommand {
            name = "Build Docker Image"
            commandType = build {
                source = file {
                    path = "Dockerfile"
                }
                namesAndTags = "%docker.image.name%:%build.number%"
            }
        }
    }
}

object MyBuild : BuildType({
    dockerBuildDefaults()

    // Override or extend as needed
    steps {
        // Additional steps
    }
})
```

### ✅ DO: Define Constants for Reusable Values

```kotlin
// At the top of settings.kts
object ProjectConstants {
    // Docker
    const val DOCKER_REGISTRY = "build-cloud.docker.com:443"
    const val DOCKER_USERNAME = "thegrayghost23"

    // Build parameters
    const val NODE_VERSION = "22"
    const val PYTHON_VERSION = "3.12"

    // Timeouts
    const val DEFAULT_BUILD_TIMEOUT_MIN = 30
    const val DEPLOYMENT_TIMEOUT_MIN = 45

    // Artifact patterns
    const val FRONTEND_ARTIFACTS = "dist/** => dashboard-build-%build.number%.zip"
    const val BACKEND_ARTIFACTS = ".venv/** => backend-build-%build.number%.zip"
}

// Usage
object DashboardBuild : BuildType({
    artifactRules = ProjectConstants.FRONTEND_ARTIFACTS

    params {
        param("env.NODE_VERSION", ProjectConstants.NODE_VERSION)
    }
})
```

### ✅ DO: Use Semantic Versioning for DSL Changes

```kotlin
// Increment version when making changes
version = "2025.07"

// Document changes in Git commit:
// feat(ci): add parallel tests to DashboardBuild
//
// - Enable parallelTests feature
// - Configure 3 test batches
// - Update timeout to 20 minutes
```

### ❌ DON'T: Hardcode Credentials in DSL

```kotlin
// ❌ BAD: Hardcoded credentials
authMethod = password {
    userName = "myusername"
    password = "mypassword123"  // Never do this!
}

// ✅ GOOD: Use parameters
authMethod = password {
    userName = "%env.GITHUB_USERNAME%"
    password = "credentialsJSON:github-token"
}
```

---

## 🏗️ Build Configuration

### ✅ DO: Organize Build Configurations Logically

**Recommended Structure**:
- **Master Build**: Orchestrates all builds
- **Component Builds**: One per major component (Dashboard, Backend, etc.)
- **Test Builds**: Unit, Integration, E2E
- **Security Builds**: SAST, dependency scanning, container scanning
- **Deployment Builds**: Staging, Production

```kotlin
project {
    // Orchestration
    buildType(Build)  // Master coordinator

    // Component builds
    buildType(DashboardBuild)
    buildType(BackendBuild)
    buildType(MCPServerBuild)

    // Testing
    buildType(IntegrationTests)
    buildType(PerformanceTests)

    // Security
    buildType(SecurityScan)

    // Deployment
    buildType(DeploymentPipeline)
    buildType(ProductionDeployment)
}
```

### ✅ DO: Use Descriptive Build Names

```kotlin
// ❌ BAD: Vague names
object Build1 : BuildType({
    name = "Build"
})

// ✅ GOOD: Clear, descriptive names
object DashboardBuild : BuildType({
    name = "Dashboard - Build & Test"
    description = "Build React dashboard, run tests, create Docker image"
})
```

### ✅ DO: Add Build Descriptions

```kotlin
object DashboardBuild : BuildType({
    name = "Dashboard - Build & Test"
    description = """
        Builds the React + Vite dashboard application.

        Steps:
        1. Install dependencies (npm ci)
        2. Type checking (TypeScript)
        3. Linting (ESLint)
        4. Unit tests (Vitest)
        5. Build production bundle
        6. Bundle analysis
        7. Docker image build
        8. Push to registry (on success)

        Agent: Frontend-Builder-01
        Typical duration: 8-12 minutes
    """.trimIndent()
})
```

### ✅ DO: Set Appropriate Timeouts

```kotlin
failureConditions {
    // Fast builds: 15 minutes
    executionTimeoutMin = 15

    // Test builds with integration tests: 30 minutes
    executionTimeoutMin = 30

    // Deployment builds: 45 minutes
    executionTimeoutMin = 45

    // Don't set too high - catch infinite loops
}
```

### ✅ DO: Use Build Dependencies Appropriately

```kotlin
// Snapshot dependencies: Always use latest
dependencies {
    snapshot(BackendBuild) {
        onDependencyFailure = FailureAction.FAIL_TO_START
    }
}

// Artifact dependencies: Reuse build artifacts
dependencies {
    artifacts(BackendBuild) {
        artifactRules = ".venv/** => ."
        cleanDestination = false
    }
}
```

### ✅ DO: Add Checkout Rules to Optimize VCS Operations

```kotlin
vcs {
    root(MainRepository)
    checkoutMode = CheckoutMode.ON_AGENT

    // Exclude unnecessary files
    checkoutRules = """
        -:.teamcity => .
        -:.github => .
        -:docs => .
        -:**/*.md => .
        -:*.md => .
        -:.git => .
    """.trimIndent()
}
```

**Benefits**:
- Faster checkout (less data transfer)
- Reduced disk usage
- Avoid triggering builds on documentation changes

---

## 🤖 Agent Management

### ✅ DO: Use Agent Requirements

```kotlin
requirements {
    // Ensure correct agent
    equals("system.agent.name", "Frontend-Builder-01")

    // Or use contains for flexibility
    contains("system.agent.name", "Frontend", RunnersProvider.RQ_CONTAINS)

    // Ensure required tools
    exists("system.docker.version")
    exists("system.node.version")
}
```

### ✅ DO: Set Agent Pools Appropriately

**Organization**:
- **Default Pool**: General-purpose agents
- **Frontend Pool**: Node.js, npm, TypeScript tools
- **Backend Pool**: Python, pip, pytest tools
- **Integration Pool**: Multi-language support

### ✅ DO: Monitor Agent Health

**Regular Checks**:
```bash
# Weekly: Check agent disk space
docker exec teamcity-agent-frontend df -h

# Weekly: Check agent memory
docker stats teamcity-agent-frontend --no-stream

# Monthly: Clean agent work directory
docker exec teamcity-agent-frontend du -sh /data/teamcity_agent/work/*
# Remove old builds if needed
```

### ✅ DO: Use Agent Properties

```kotlin
// Set properties for reusability
params {
    param("system.custom.node.version", "22")
    param("system.custom.python.version", "3.12")
}

// Use in build steps
script {
    content = """
        node --version  # Should be v%system.custom.node.version%
        npm ci
    """.trimIndent()
}
```

### ❌ DON'T: Run Too Many Builds on One Agent

**Guideline**: Max 2 concurrent builds per agent to prevent resource contention.

```kotlin
// Configure in agent settings
maxRunningBuilds = 2
```

---

## 🔐 Security Practices

### ✅ DO: Use Password Parameters for Secrets

```kotlin
// In TeamCity UI: Administration → Root Project → Parameters
// Add as "Password" type:
// - env.OPENAI_API_KEY
// - env.ANTHROPIC_API_KEY
// - credentialsJSON:github-token
// - credentialsJSON:docker-hub-password

// Use in build configuration
params {
    password("env.OPENAI_API_KEY", "credentialsJSON:openai-api-key")
}
```

### ✅ DO: Scope Parameters Appropriately

**Parameter Hierarchy**:
1. **Root Project**: Shared across all builds (GitHub token, Docker credentials)
2. **Sub-Project**: Specific to project group (API keys for testing)
3. **Build Configuration**: Unique to single build (deployment targets)

### ✅ DO: Use VCS Root Credentials

```kotlin
object MainRepository : GitVcsRoot({
    authMethod = password {
        userName = "%env.GITHUB_USERNAME%"
        password = "credentialsJSON:github-token"
    }
})

// Never:
// password = "ghp_actualtoken123"  // ❌ NO!
```

### ✅ DO: Rotate Credentials Regularly

**Schedule**:
- **GitHub PATs**: Every 6 months
- **Docker registry tokens**: Every 6 months
- **API keys**: Per provider policy
- **Database passwords**: Annually (non-production)

**Process**:
1. Generate new credential
2. Update parameter in TeamCity
3. Test with a build
4. Revoke old credential

### ✅ DO: Review Build Logs for Secret Exposure

TeamCity automatically masks password parameters, but verify:

```bash
# Search build logs for potential leaks
# Look for patterns like:
# - Bearer tokens
# - API keys (sk-*, pk-*)
# - Connection strings with passwords

# If found, rotate credential immediately
```

### ❌ DON'T: Commit Secrets to VCS

```bash
# In .gitignore (already present)
.env
.env.local
*.pem
*.key
secrets/
credentials/
```

---

## ⚡ Performance Optimization

### ✅ DO: Enable Build Cache (2025.07 Feature)

```kotlin
features {
    feature {
        type = "BuildCache"
        id = "build-cache"
        param("enabled", "true")
        param("publish.max.size", "10GB")
        param("rules", """
            +:**/node_modules/** => directory
            +:**/.venv/** => directory
            +:**/__pycache__/** => directory
            +:**/.pytest_cache/** => directory
            +:**/.ruff_cache/** => directory
            +:**/dist/** => directory
        """.trimIndent())
    }
}
```

**Expected Impact**: 30-40% faster builds after first build.

### ✅ DO: Use Parallel Tests

```kotlin
object DashboardBuild : BuildType({
    // ... existing config

    features {
        feature {
            type = "parallelTests"
            param("numberOfBatches", "3")
        }
    }
})
```

**How It Works**:
1. First build: Gathers test statistics
2. Subsequent builds: Distributes tests across batches
3. Each batch runs in parallel (3 agents required)

### ✅ DO: Optimize Docker Builds

```dockerfile
# Use .dockerignore
# .dockerignore
.git
.teamcity
node_modules
.venv
*.md
docs/

# Multi-stage builds
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:22-alpine
COPY --from=builder /app/node_modules ./node_modules
COPY . .
CMD ["npm", "start"]

# Use BuildKit
# In build step:
# export DOCKER_BUILDKIT=1
# docker build --cache-from type=local,src=/cache/docker .
```

### ✅ DO: Minimize Checkout Scope

```kotlin
checkoutRules = """
    # Only checkout what's needed
    +:apps/dashboard/** => apps/dashboard
    +:package.json => .
    +:package-lock.json => .
    -:**/*.md => .
""".trimIndent()
```

### ✅ DO: Use Incremental Compilation

```kotlin
// For Kotlin/Java builds
kotlinOptions {
    incremental = true
}

// TeamCity automatically detects changes and compiles only affected files
```

### ❌ DON'T: Run Unnecessary Steps

```kotlin
// ❌ BAD: Always runs all steps
steps {
    nodeTests()
    integrationTests()
    e2eTests()  // Slow!
    performanceTests()  // Very slow!
}

// ✅ GOOD: Conditional execution
steps {
    nodeTests()  // Always

    integrationTests {
        conditions {
            // Only on main branch or PRs
            not { equals("teamcity.build.branch", "feature/*") }
        }
    }

    performanceTests {
        conditions {
            // Only on main, manually, or nightly
            anyOf {
                equals("teamcity.build.branch", "main")
                equals("teamcity.build.triggeredBy", "user")
                equals("teamcity.build.triggeredBy", "schedule")
            }
        }
    }
}
```

---

## 🧪 Testing Practices

### ✅ DO: Organize Tests by Type

**Test Categories**:
1. **Unit Tests**: Fast, isolated, no external dependencies
2. **Integration Tests**: Database, Redis, API integration
3. **E2E Tests**: Full stack, browser automation
4. **Performance Tests**: Load testing, stress testing

```kotlin
// Separate build configurations
object UnitTests : BuildType({
    steps {
        pytest {
            args = "-m unit --cov=. --cov-report=xml"
        }
    }
})

object IntegrationTests : BuildType({
    steps {
        pytest {
            args = "-m integration --maxfail=3"
        }
    }

    dependencies {
        snapshot(BackendBuild)
    }
})
```

### ✅ DO: Use Test Markers

```python
# In test files
import pytest

@pytest.mark.unit
def test_user_model():
    """Fast unit test"""
    pass

@pytest.mark.integration
def test_database_connection():
    """Requires database"""
    pass

@pytest.mark.slow
@pytest.mark.e2e
def test_full_workflow():
    """End-to-end test"""
    pass
```

```bash
# In build step
pytest -m "unit"           # Only unit tests
pytest -m "not slow"       # Exclude slow tests
pytest -m "unit or integration"  # Multiple markers
```

### ✅ DO: Generate Test Reports

```kotlin
steps {
    pytest {
        args = "--junitxml=test-results.xml --cov=. --cov-report=xml"
    }
}

// TeamCity automatically detects JUnit XML
// Shows test results in UI
```

### ✅ DO: Fail Fast for Critical Tests

```kotlin
steps {
    pytest {
        // Stop on first 3 failures
        args = "-m critical --maxfail=3"
    }
}

failureConditions {
    // Fail build on first test failure
    failOnMetricChange {
        metric = BuildFailureOnMetric.MetricType.TEST_FAILED_COUNT
        threshold = 1
        units = BuildFailureOnMetric.MetricUnit.DEFAULT_UNIT
        comparison = BuildFailureOnMetric.MetricComparison.MORE
    }
}
```

### ✅ DO: Track Test Flakiness

**Monitor in TeamCity**:
- Projects → [Project] → Build Statistics
- Filter: "Flaky Tests"
- Investigate tests that fail intermittently

**Fix Flaky Tests**:
```python
# Common causes:
# 1. Race conditions → Add proper waits
# 2. Shared state → Use fixtures with cleanup
# 3. External dependencies → Mock or use test containers
# 4. Timing-dependent → Use retry decorators

# Example fix:
import pytest

@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_api_call():
    """Retry up to 3 times with 2s delay"""
    response = api.call()
    assert response.status_code == 200
```

---

## 🚀 Deployment Practices

### ✅ DO: Use Deployment Pipelines

```kotlin
object DeploymentPipeline : BuildType({
    name = "🚀 Deploy to Staging"

    dependencies {
        // Only deploy if all tests pass
        snapshot(DashboardBuild)
        snapshot(BackendBuild)
        snapshot(IntegrationTests)
        snapshot(SecurityScan)
    }

    steps {
        // 1. Deploy backend
        // 2. Deploy frontend
        // 3. Run smoke tests
        // 4. Notify team
    }
})
```

### ✅ DO: Require Manual Approval for Production

```kotlin
object ProductionDeployment : BuildType({
    name = "🚀 Deploy to Production"

    // Require manual trigger
    triggers {
        // No automatic triggers
    }

    dependencies {
        snapshot(DeploymentPipeline) {
            // Must have successful staging deployment
            onDependencyFailure = FailureAction.FAIL_TO_START
        }
    }

    // Add approval step
    steps {
        script {
            name = "Manual Approval Required"
            scriptContent = """
                echo "⚠️  PRODUCTION DEPLOYMENT"
                echo "This will deploy to production."
                echo "Ensure staging tests passed."
                echo ""
                read -p "Type 'DEPLOY' to continue: " confirm
                if [ "${'$'}confirm" != "DEPLOY" ]; then
                    echo "❌ Deployment cancelled"
                    exit 1
                fi
            """.trimIndent()
        }
    }
})
```

### ✅ DO: Use Blue-Green Deployment

```kotlin
steps {
    script {
        name = "Blue-Green Deployment"
        scriptContent = """
            # Deploy to green (inactive) environment
            vercel deploy --prod --target=green

            # Run smoke tests on green
            curl https://green.toolboxai.com/health

            # Switch traffic to green
            vercel alias green.toolboxai.com toolboxai.com

            # Keep blue as rollback option
            echo "Blue environment available at: https://blue.toolboxai.com"
        """.trimIndent()
    }
}
```

### ✅ DO: Tag Deployments

```kotlin
steps {
    script {
        name = "Tag Release"
        scriptContent = """
            # Tag with build number
            git tag -a v1.%build.number% -m "Release v1.%build.number%"
            git push origin v1.%build.number%

            # Also tag Docker image
            docker tag %docker.image.name%:latest %docker.image.name%:v1.%build.number%
            docker push %docker.image.name%:v1.%build.number%
        """.trimIndent()
    }
}
```

### ✅ DO: Send Deployment Notifications

```kotlin
features {
    notifications {
        notifierSettings = slackNotifier {
            connection = slackConnection {
                id = "PROJECT_EXT_1"
                connectionId = "slack-connection"
            }
            messageFormat = verboseMessageFormat()

            // Notify on deployment events
            buildStarted = true
            buildSuccessful = true
            buildFailed = true

            channel = "#deployments"
        }
    }
}
```

---

## 📊 Monitoring & Maintenance

### ✅ DO: Monitor Build Performance

**Weekly Review**:
```bash
# Check average build times (from UI)
# Projects → ToolBoxAI Solutions → Statistics → Build Duration

# Look for trends:
# - Builds getting slower? → Optimize
# - Cache hit rate dropping? → Review cache rules
# - Agent idle time high? → Better load balancing
```

### ✅ DO: Set Up Automatic Cleanup

```kotlin
// In TeamCity UI: Administration → Clean-up Rules
// Recommended settings:

// Base rule:
// - Keep builds: 30 days
// - Keep successful builds: 14 days
// - Keep artifacts: 7 days
// - Keep everything for tagged builds

// Additional rules:
// - Keep at least 5 successful builds
// - Keep at least 1 build per branch
// - Clean up failed builds after 7 days
```

### ✅ DO: Monitor Disk Usage

```bash
# Monthly check
docker exec teamcity-server du -sh /data/teamcity_server/datadir/*

# Key directories:
# - system/artifacts → Should be cleaned by cleanup rules
# - system/caches → 10GB limit (Build Cache)
# - lib → JDBC drivers, plugins

# If disk full:
# 1. Run manual cleanup: Administration → Clean-up
# 2. Reduce artifact retention
# 3. Reduce cache size limit
```

### ✅ DO: Backup TeamCity Configuration

```bash
# Weekly automated backup
# Administration → Backup

# What gets backed up:
# - Build configurations (Kotlin DSL in Git)
# - Project settings
# - VCS roots
# - Build history
# - User accounts

# Store backups off-server:
# - S3 bucket
# - Network drive
# - Supabase Storage
```

### ✅ DO: Review Build Logs Regularly

```bash
# Weekly: Check for warnings
docker logs teamcity-server 2>&1 | grep -i "warn" | tail -50

# Monthly: Check for errors
docker logs teamcity-server 2>&1 | grep -i "error" | tail -100

# Address issues proactively
```

---

## 👥 Team Collaboration

### ✅ DO: Document Build Configurations

```kotlin
object DashboardBuild : BuildType({
    description = """
        ## Dashboard Build Configuration

        **Purpose**: Build and test React dashboard

        **Triggers**:
        - VCS: Any commit to main, develop, or feature/*
        - Schedule: Nightly at 2 AM

        **Steps**:
        1. Checkout code
        2. Install dependencies (npm ci)
        3. TypeScript type checking
        4. ESLint linting
        5. Vitest unit tests
        6. Build production bundle
        7. Docker image build & push

        **Artifacts**:
        - dist/ → dashboard-build-%build.number%.zip
        - Docker image → thegrayghost23/toolboxai-dashboard:%build.number%

        **Contact**: @frontend-team
    """.trimIndent()
})
```

### ✅ DO: Use Conventional Commit Messages for DSL Changes

```bash
# When updating .teamcity/settings.kts:

git commit -m "feat(ci): add parallel tests to DashboardBuild

- Enable parallelTests feature with 3 batches
- Update timeout from 15 to 20 minutes
- Expected 30% faster test execution

Closes #123"
```

### ✅ DO: Code Review Build Configuration Changes

**Pull Request Template**:
```markdown
## CI/CD Configuration Change

**Build Configuration**: DashboardBuild
**Change Type**: Performance Optimization

**Changes**:
- Added parallel test execution (3 batches)
- Increased timeout to 20 minutes

**Impact**:
- Expected 30% faster test execution
- Requires 3 available agents during test phase

**Testing**:
- [x] Tested in feature branch
- [x] Verified all tests pass
- [x] Checked build duration improvement

**Rollback Plan**:
Revert commit if test parallelization causes issues

cc: @devops-team
```

### ✅ DO: Share Build Status

**Slack Integration**:
```kotlin
features {
    notifications {
        notifierSettings = slackNotifier {
            channel = "#ci-builds"

            buildStarted = false  // Too noisy
            buildSuccessful = false  // Only failures
            buildFailed = true  // Alert on failures
            buildFailedToStart = true

            // Custom message
            messageFormat = verboseMessageFormat()
        }
    }
}
```

**GitHub Status Checks**:
```kotlin
features {
    commitStatusPublisher {
        vcsRootExtId = "${MainRepository.id}"
        publisher = github {
            githubUrl = "https://api.github.com"
            authType = personalToken {
                token = "credentialsJSON:github-token"
            }
        }
    }
}
```

### ✅ DO: Create Build Status Badges

```markdown
# In README.md
[![Build Status](http://localhost:8111/app/rest/builds/buildType:(id:DashboardBuild)/statusIcon.svg)](http://localhost:8111/viewType.html?buildTypeId=DashboardBuild)
```

---

## 📚 Additional Resources

### Official Documentation
- **TeamCity 2025.07 Docs**: http://localhost:8111/help/teamcity-documentation.html
- **Kotlin DSL Reference**: http://localhost:8111/app/dsl-documentation/
- **REST API**: http://localhost:8111/app/rest/application.wadl

### Project Documentation
- **First-Time Setup**: `docs/08-operations/ci-cd/TEAMCITY_FIRST_TIME_SETUP.md`
- **Troubleshooting**: `docs/08-operations/ci-cd/TEAMCITY_TROUBLESHOOTING.md`
- **Kotlin DSL**: `.teamcity/README.md` (coming soon)

### Quick Reference

```bash
# View server status
docker ps --filter "name=teamcity-server"

# View build logs
docker logs teamcity-server --tail 100

# Restart services
docker-compose -f infrastructure/docker/compose/docker-compose.teamcity.yml restart

# Health check
curl -I http://localhost:8111
```

---

## ✅ Checklist for New Team Members

When joining the team, ensure:

- [ ] Access to TeamCity UI (http://localhost:8111)
- [ ] Understanding of build pipeline
- [ ] Familiarity with `.teamcity/settings.kts`
- [ ] Knowledge of troubleshooting guide
- [ ] Slack notifications configured
- [ ] GitHub account linked for commit status
- [ ] Understanding of deployment process
- [ ] Review of security practices

---

**Best Practices Guide Version**: 1.0.0
**Last Updated**: 2025-11-08
**Prepared By**: Claude Code Automation
**Review Cycle**: Quarterly
