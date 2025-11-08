# TeamCity Configuration (Kotlin DSL)

**Version**: 2025.07
**Last Updated**: 2025-11-08
**Configuration Language**: Kotlin DSL

This directory contains the **Configuration as Code** for the ToolBoxAI Solutions CI/CD pipeline using TeamCity Kotlin DSL.

---

## 📁 Directory Structure

```
.teamcity/
├── README.md              # This file
├── settings.kts           # Main configuration (1399 lines)
├── deployment.kts         # Deployment configurations (358 lines)
├── pom.xml                # Kotlin DSL dependencies
└── .teamcity.vcs.settings # VCS settings (auto-generated)
```

---

## 🔧 Configuration Files

### `settings.kts` - Main Configuration

**Purpose**: Defines all build configurations, VCS roots, and project structure.

**Key Sections**:

1. **Project Configuration** (Lines 29-155)
   - Build Cache (2025.07 feature)
   - Project structure
   - Sub-projects and versioned settings

2. **VCS Roots** (Lines 156-169)
   - `MainRepository`: GitHub repository connection

3. **Build Types** (Lines 170-1298)
   - `Build`: Master orchestrator
   - `DashboardBuild`: React + Vite frontend
   - `BackendBuild`: FastAPI Python backend
   - `MCPServerBuild`: Model Context Protocol server
   - `AgentCoordinatorBuild`: LangChain agent system
   - `RobloxIntegrationBuild`: Roblox plugin
   - `SecurityScan`: Comprehensive security scanning
   - `IntegrationTests`: Full-stack integration tests
   - `PerformanceTests`: Load and stress testing
   - `DeploymentPipeline`: Staging deployment
   - `ProductionDeployment`: Production deployment (manual approval)

4. **Templates** (Lines 1299-1399)
   - `DockerBuildTemplate`
   - `PythonTestTemplate`
   - `NodeTestTemplate`
   - `SecurityScanTemplate`

**Note**: Templates will be refactored to extension functions per 2025.07 best practices.

### `deployment.kts` - Deployment Configuration

**Purpose**: Defines deployment build types for Vercel (frontend) and Render (backend).

**Key Build Types**:
- `VercelDeployment`: React dashboard → Vercel
- `RenderDeployment`: FastAPI backend → Render
- `FullProductionDeploy`: Orchestrates both deployments

**Features**:
- Sentry sourcemap upload
- Health check verification
- Deployment notifications

---

## 🏗️ Build Pipeline Architecture

### Build Flow

```
┌─────────────────────────────────────────────────────────────┐
│                       Master Build                          │
│                    (Orchestrator)                           │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
    ┌──────────▼──────────┐        ┌─────────▼──────────┐
    │  Dashboard Build    │        │   Backend Build    │
    │  (React + Vite)     │        │   (FastAPI)        │
    │                     │        │                    │
    │ 1. npm install      │        │ 1. pip install     │
    │ 2. Type check       │        │ 2. Type check      │
    │ 3. Lint             │        │ 3. Lint            │
    │ 4. Unit tests       │        │ 4. Unit tests      │
    │ 5. Build            │        │ 5. Build           │
    │ 6. Docker image     │        │ 6. Docker image    │
    └──────────┬──────────┘        └─────────┬──────────┘
               │                              │
               └──────────────┬───────────────┘
                              │
                   ┌──────────▼──────────┐
                   │  Integration Tests  │
                   │  (Full Stack)       │
                   └──────────┬──────────┘
                              │
                   ┌──────────▼──────────┐
                   │   Security Scan     │
                   │   (SAST + Deps)     │
                   └──────────┬──────────┘
                              │
                   ┌──────────▼──────────┐
                   │ Deployment Pipeline │
                   │   (Staging)         │
                   └──────────┬──────────┘
                              │
                   ┌──────────▼──────────┐
                   │ Production Deploy   │
                   │ (Manual Approval)   │
                   └─────────────────────┘
```

### Build Dependencies

```kotlin
// Master Build depends on all component builds
object Build : BuildType({
    dependencies {
        snapshot(DashboardBuild)
        snapshot(BackendBuild)
        snapshot(MCPServerBuild)
        snapshot(AgentCoordinatorBuild)
        snapshot(RobloxIntegrationBuild)
    }
})

// Integration Tests depend on component builds
object IntegrationTests : BuildType({
    dependencies {
        snapshot(DashboardBuild)
        snapshot(BackendBuild)
    }
})

// Deployment depends on successful tests
object DeploymentPipeline : BuildType({
    dependencies {
        snapshot(Build)
        snapshot(IntegrationTests)
        snapshot(SecurityScan)
    }
})
```

---

## 🚀 Key Features

### 1. Build Cache (New in 2025.07)

**Configuration**:
```kotlin
features {
    feature {
        type = "BuildCache"
        param("publish.max.size", "10GB")
        param("rules", """
            +:**/node_modules/** => directory
            +:**/.venv/** => directory
            +:**/__pycache__/** => directory
        """.trimIndent())
    }
}
```

**Impact**: 30-40% faster builds after first build completes.

**Cache Location**: `/Volumes/G-DRIVE ArmorATD/.../TeamCity/cache`

### 2. Parallel Tests (Available, Not Yet Enabled)

**Usage**:
```kotlin
features {
    feature {
        type = "parallelTests"
        param("numberOfBatches", "3")
    }
}
```

**How It Works**:
- First build: Gathers test execution statistics
- Subsequent builds: Distributes tests across N batches
- Each batch runs in parallel on separate agents

**Status**: Planned for Phase 3 implementation

### 3. Agent Requirements

**Specialized Agents**:
- **Frontend-Builder-01**: Node.js 22, npm, Docker-in-Docker
- **Backend-Builder-01**: Python 3.12, pip, Docker-in-Docker
- **Integration-Builder-01**: Multi-language (Node.js + Python)

**Configuration**:
```kotlin
requirements {
    equals("system.agent.name", "Frontend-Builder-01")
}
```

### 4. VCS Configuration

**Branch Specification**:
```kotlin
branchSpec = """
    +:refs/heads/*          # All branches
    +:refs/tags/*           # All tags
    +:refs/pull/*/merge     # All pull requests
""".trimIndent()
```

**Authentication**: GitHub Personal Access Token (parameter: `credentialsJSON:github-token`)

### 5. Docker-in-Docker Support

All build agents run with Docker-in-Docker capability:
- Build Docker images
- Push to TeamCity Cloud Registry
- Push to Docker Hub (optional)

**Configuration**:
```yaml
# docker-compose.teamcity.yml
privileged: true
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

---

## 📝 How to Modify Configuration

### Prerequisites

1. **Local Kotlin IDE** (IntelliJ IDEA recommended)
2. **TeamCity Kotlin DSL plugin** (auto-detects .teamcity directory)
3. **Git access** to repository
4. **TeamCity credentials** for testing

### Making Changes

#### 1. Edit Locally with IDE Support

```bash
# Open project in IntelliJ IDEA
# .teamcity directory will be detected automatically
# IDE provides autocomplete, syntax checking, and inline documentation
```

#### 2. Validate Configuration

```kotlin
// Syntax validation happens automatically in IDE

// To test without committing:
// 1. Push to feature branch
// 2. TeamCity will detect changes
// 3. Verify in UI: Administration → Versioned Settings
```

#### 3. Common Modifications

**Add New Build Step**:
```kotlin
object MyBuild : BuildType({
    steps {
        // Add new step
        script {
            name = "My New Step"
            scriptContent = """
                echo "Hello from new step"
            """.trimIndent()
        }
    }
})
```

**Add Parameter**:
```kotlin
params {
    param("env.MY_VARIABLE", "my_value")
    password("env.MY_SECRET", "credentialsJSON:my-secret")
}
```

**Add Trigger**:
```kotlin
triggers {
    vcs {
        branchFilter = "+:refs/heads/main"
    }

    schedule {
        schedulingPolicy = daily {
            hour = 2
            minute = 0
        }
        triggerBuild = always()
    }
}
```

**Add Failure Condition**:
```kotlin
failureConditions {
    executionTimeoutMin = 30

    failOnMetricChange {
        metric = BuildFailureOnMetric.MetricType.TEST_FAILED_COUNT
        threshold = 1
        comparison = BuildFailureOnMetric.MetricComparison.MORE
    }
}
```

#### 4. Commit Changes

```bash
# Follow conventional commits
git add .teamcity/settings.kts
git commit -m "feat(ci): add new build step to DashboardBuild

- Added bundle size analysis
- Set failure threshold at 500KB
- Publishes report as artifact

Closes #123"

git push origin feature/add-bundle-analysis
```

#### 5. Verify in TeamCity

1. Navigate to **Administration → <Root Project> → Versioned Settings**
2. TeamCity will show detected changes
3. Click **"Apply changes"** or wait for auto-sync
4. Verify build configuration updated

### Testing Changes

**Best Practice**: Test in feature branch before merging to main

```bash
# 1. Create feature branch
git checkout -b feature/ci-improvement

# 2. Make changes to .teamcity/settings.kts

# 3. Commit and push
git commit -m "feat(ci): improve build configuration"
git push origin feature/ci-improvement

# 4. Run build manually in TeamCity UI
# Projects → ToolBoxAI Solutions → Run → Custom Build
# Branch: feature/ci-improvement

# 5. If successful, merge to main
git checkout main
git merge feature/ci-improvement
git push origin main
```

---

## 🔍 Configuration Reference

### Build Configuration Structure

```kotlin
object MyBuild : BuildType({
    // Basic properties
    name = "My Build Name"
    description = "Build description"

    // VCS settings
    vcs {
        root(MainRepository)
        checkoutMode = CheckoutMode.ON_AGENT
        checkoutRules = "-:.git => ."
    }

    // Build steps
    steps {
        script {
            name = "Step 1"
            scriptContent = "echo 'Hello'"
        }
    }

    // Triggers
    triggers {
        vcs { }  // On every commit
    }

    // Dependencies
    dependencies {
        snapshot(OtherBuild) {
            onDependencyFailure = FailureAction.FAIL_TO_START
        }
    }

    // Failure conditions
    failureConditions {
        executionTimeoutMin = 15
    }

    // Features
    features {
        commitStatusPublisher {
            // Publish status to GitHub
        }
    }

    // Parameters
    params {
        param("env.MY_VAR", "value")
    }

    // Requirements
    requirements {
        equals("system.agent.name", "MyAgent")
    }

    // Artifact rules
    artifactRules = "dist/** => build.zip"
})
```

### Common Patterns

#### Docker Build

```kotlin
steps {
    dockerCommand {
        name = "Build Docker Image"
        commandType = build {
            source = file {
                path = "Dockerfile"
            }
            namesAndTags = "%docker.image.name%:%build.number%"
            commandArgs = "--pull --no-cache"
        }
    }

    dockerCommand {
        name = "Push Docker Image"
        commandType = push {
            namesAndTags = "%docker.image.name%:%build.number%"
        }
    }
}
```

#### Python Tests

```kotlin
steps {
    script {
        name = "Run Python Tests"
        scriptContent = """
            python -m venv .venv
            source .venv/bin/activate
            pip install -r requirements.txt
            pytest -v --cov=. --cov-report=xml
        """.trimIndent()
    }
}
```

#### Node.js Build

```kotlin
steps {
    script {
        name = "Install Dependencies"
        scriptContent = "npm ci"
    }

    script {
        name = "Type Check"
        scriptContent = "npm run typecheck"
    }

    script {
        name = "Run Tests"
        scriptContent = "npm test -- --coverage"
    }

    script {
        name = "Build Production"
        scriptContent = "npm run build"
    }
}
```

---

## 🔐 Secrets Management

### Parameter Types

1. **Text**: Plain text, visible in UI and logs
2. **Password**: Encrypted, hidden in UI and logs (shown as `******`)

### Adding Secrets

**Via UI** (Recommended):
```
Administration → Root Project → Parameters → Add new parameter

Name: credentialsJSON:my-secret
Type: Password
Value: <paste secret>
```

**Via Kotlin DSL** (Reference only):
```kotlin
params {
    // Reference secret (actual value set in UI)
    password("env.MY_SECRET", "credentialsJSON:my-secret")
}
```

**Never commit actual secrets**:
```kotlin
// ❌ BAD
password("env.API_KEY", "sk-1234567890abcdef")

// ✅ GOOD
password("env.API_KEY", "credentialsJSON:openai-api-key")
```

---

## 📊 Build Statistics

### Viewing Build Performance

**TeamCity UI**:
```
Projects → ToolBoxAI Solutions → Statistics

Available metrics:
- Build duration
- Success rate
- Test count
- Code coverage
- Artifact size
- Queue time
- Agent utilization
```

### Monitoring Build Cache

**Cache Hit Rate**:
```
Administration → Build Cache

Shows:
- Total cache size
- Published caches
- Cache hits/misses
- Storage location
```

---

## 🐛 Troubleshooting

### Configuration Not Updating

**Symptom**: Changes to `settings.kts` not reflected in TeamCity

**Solutions**:
1. Check versioned settings sync status:
   ```
   Administration → <Root Project> → Versioned Settings
   ```

2. Manually trigger sync:
   ```
   Administration → <Root Project> → Versioned Settings → "Apply changes"
   ```

3. Check for syntax errors:
   ```bash
   # Kotlin compilation errors prevent sync
   # Check TeamCity logs for details
   docker logs teamcity-server 2>&1 | grep -i "settings.kts"
   ```

### Build Configuration Validation Errors

**Common Errors**:

1. **Missing VCS Root**:
   ```kotlin
   // Ensure VCS root is defined
   object MainRepository : GitVcsRoot({ ... })

   // And referenced in build
   vcs {
       root(MainRepository)
   }
   ```

2. **Invalid Parameter Reference**:
   ```kotlin
   // ❌ BAD: Undefined parameter
   param("my.value", "%undefined.param%")

   // ✅ GOOD: Define parameter first
   params {
       param("my.source", "value")
       param("my.value", "%my.source%")
   }
   ```

3. **Circular Dependencies**:
   ```kotlin
   // ❌ BAD: A depends on B, B depends on A
   object BuildA : BuildType({
       dependencies { snapshot(BuildB) }
   })
   object BuildB : BuildType({
       dependencies { snapshot(BuildA) }
   })

   // ✅ GOOD: Clear dependency chain
   // A → B → C
   ```

---

## 📚 Additional Resources

### Documentation

- **TeamCity Kotlin DSL Reference**: http://localhost:8111/app/dsl-documentation/
- **TeamCity Documentation**: http://localhost:8111/help/teamcity-documentation.html
- **First-Time Setup**: `docs/08-operations/ci-cd/TEAMCITY_FIRST_TIME_SETUP.md`
- **Troubleshooting**: `docs/08-operations/ci-cd/TEAMCITY_TROUBLESHOOTING.md`
- **Best Practices**: `docs/08-operations/ci-cd/TEAMCITY_BEST_PRACTICES.md`

### Examples

- **JetBrains Examples**: https://github.com/JetBrains/teamcity-kotlin-dsl-samples
- **Community Examples**: https://github.com/topics/teamcity-kotlin-dsl

### Support

- **Internal**: #devops channel on Slack
- **TeamCity Community**: https://teamcity-support.jetbrains.com/

---

## 📅 Maintenance Schedule

### Weekly
- [ ] Review failed builds
- [ ] Check build duration trends
- [ ] Verify cache hit rates

### Monthly
- [ ] Update dependencies in pom.xml
- [ ] Review and clean up old build configurations
- [ ] Check agent disk space

### Quarterly
- [ ] Review and update this README
- [ ] Audit security configurations
- [ ] Performance optimization review

---

## 🔄 Version History

### Version 2025.07 (Current)
- TeamCity 2025.07 upgrade
- Build Cache feature enabled
- Supabase PostgreSQL integration
- 3 specialized build agents
- 11 build configurations
- Docker-in-Docker support

### Upcoming Changes (Planned)
- Convert templates to extension functions (Phase 2)
- Enable parallel tests (Phase 3)
- Enhanced build cache rules (Phase 4)
- Implement checkout rules optimization (Phase 5)

---

**Configuration Version**: 2025.07
**Last Updated**: 2025-11-08
**Maintained By**: DevOps Team
**Review Cycle**: Quarterly

For questions or issues, contact the DevOps team or create an issue in the repository.
