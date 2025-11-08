# 🚀 CI/CD Architecture

## Overview

The ToolBoxAI CI/CD pipeline has been consolidated from **25+ fragmented workflows** into a **streamlined, maintainable system** with just 2 core workflows and reusable components.

## 🎯 Design Principles

1. **DRY (Don't Repeat Yourself)**: Reusable workflows eliminate code duplication
2. **Parallel Execution**: Independent jobs run simultaneously for faster builds
3. **Smart Filtering**: Path-based triggers skip unnecessary runs
4. **Security First**: Automated scanning at every stage
5. **Fast Feedback**: Matrix builds and caching for quick results

---

## 📊 Workflow Architecture

### Core Workflows

#### 1. Enhanced CI/CD Pipeline (`enhanced-ci-cd.yml`)
**Purpose**: Main deployment pipeline from code to production

**Triggers**:
- Push to `main`, `develop`, `staging`, `feature/*`, `release/*`
- Pull requests to `main`, `develop`, `staging`
- Manual dispatch with environment selection
- Git tags (for production deployment)

**Stages**:
```
Setup → Quality Checks → Security Scan → Testing → Build → Deploy → Validate → Notify
         ↓                ↓                ↓         ↓        ↓       ↓         ↓
      (parallel)      (parallel)       (parallel) (matrix)  (matrix) (env)   (always)
```

**Key Features**:
- 🔀 **Parallel execution**: Quality, security, and testing run simultaneously
- 🎯 **Smart deployment**: Auto-detects target environment from branch/tag
- 🐳 **Matrix builds**: 5 Docker images built in parallel (backend, dashboard, celery, mcp, coordinator)
- ✅ **Multi-environment**: development, staging, production with approval gates
- 📊 **Post-deploy validation**: E2E tests, accessibility, performance checks

#### 2. Testing Pipeline (`testing.yml`)
**Purpose**: Comprehensive testing with coverage enforcement

**Triggers**:
- Push/PR to code paths (`apps/**`, `core/**`, `tests/**`)
- Called by `enhanced-ci-cd.yml`
- Manual dispatch

**Test Matrix**:
```
Backend Tests (Python 3.11, 3.12) × (unit, integration)
Frontend Tests (Vitest + Coverage)
E2E Tests (Playwright)
Code Quality (Black, Ruff, BasedPyright, ESLint)
```

**Coverage Requirements**:
- Backend: 80% minimum
- Frontend: 80% minimum
- Auto-fail if below threshold

### Reusable Workflows

Located in `.github/workflows/reusable/`

#### `test-python.yml`
**Purpose**: Parameterized Python testing

**Inputs**:
- `python-version`: Python version (default: 3.12)
- `test-type`: unit | integration | all
- `coverage-threshold`: Minimum coverage % (default: 80)
- `working-directory`: Test directory

**Outputs**:
- `coverage`: Test coverage percentage
- `status`: success | failure

**Usage Example**:
```yaml
jobs:
  backend-tests:
    uses: ./.github/workflows/reusable/test-python.yml
    with:
      python-version: '3.12'
      test-type: 'all'
      coverage-threshold: 85
```

#### `docker-build.yml`
**Purpose**: Standardized Docker image builds

**Inputs**:
- `service-name`: Image name
- `dockerfile-path`: Path to Dockerfile
- `context-path`: Build context
- `platforms`: Target platforms (amd64, arm64)
- `version`: Image tag
- `push`: Whether to push to registry
- `scan-image`: Enable Trivy scanning

**Outputs**:
- `image-tag`: Full image reference
- `image-digest`: SHA256 digest

**Features**:
- ✅ Multi-platform builds (amd64/arm64)
- ✅ BuildKit caching (GitHub Actions cache)
- ✅ Trivy vulnerability scanning
- ✅ SBOM generation (CycloneDX format)
- ✅ Auto-tagging (latest, stable, SHA, semver)

---

## 🔄 Workflow Execution Flow

### Pull Request Flow
```mermaid
graph LR
    PR[Pull Request] --> Quality[Quality Checks]
    PR --> Security[Security Scan]
    PR --> Tests[Testing Pipeline]

    Quality --> Check{All Pass?}
    Security --> Check
    Tests --> Check

    Check -->|Yes| Approve[✅ Ready to Merge]
    Check -->|No| Fix[❌ Fix Issues]
```

### Deployment Flow (Main Branch)
```mermaid
graph TB
    Main[Push to Main] --> Setup[Setup & Preparation]
    Setup --> Parallel{Parallel Execution}

    Parallel --> Quality[Quality Checks]
    Parallel --> Security[Security Scan]
    Parallel --> Tests[Testing Pipeline]

    Quality --> Build[Docker Matrix Build]
    Security --> Build
    Tests --> Build

    Build --> Staging[Deploy to Staging]
    Staging --> Validate[Post-Deploy Validation]
    Validate --> Notify[Slack Notification]
```

### Production Deployment Flow (Tags)
```mermaid
graph TB
    Tag[Git Tag v*] --> Setup[Setup & Preparation]
    Setup --> Quality[Quality Checks]
    Quality --> Security[Security Scan]
    Security --> Tests[Testing Pipeline]
    Tests --> Build[Docker Matrix Build]
    Build --> Staging[Deploy to Staging]
    Staging --> StagingTests[Staging Validation]
    StagingTests --> Approval{Manual Approval}
    Approval -->|Approved| Prod[Deploy to Production]
    Prod --> BlueGreen[Blue-Green Deployment]
    BlueGreen --> Health[Health Checks]
    Health --> Perf[Performance Tests]
    Perf --> Success{Success?}
    Success -->|Yes| Complete[✅ Deployment Complete]
    Success -->|No| Rollback[⏮️ Automatic Rollback]
```

---

## 🗂️ Consolidated vs Legacy Workflows

### Before Consolidation (25+ Workflows)
| Workflow | Purpose | Status |
|----------|---------|--------|
| `ci-cd-pipeline.yml` | Main CI/CD | ✅ **Merged** |
| `comprehensive-testing.yml` | Testing | ✅ **Merged** |
| `docker-ci-cd.yml` | Docker builds | ✅ **Merged** |
| `test-automation.yml` | Test automation | ⚠️ **ARCHIVED** (exposed API key) |
| `test-automation-fix.yml` | Test fixes | ⚠️ **ARCHIVED** (redundant) |
| `ci.yml` | Basic CI | ⚠️ **ARCHIVED** (redundant) |
| `continuous-testing.yml` | Continuous tests | ✅ **Merged** |
| ... | 18 other workflows | ✅ **Kept** (specialized) |

### After Consolidation (10 Core Workflows)
| Workflow | Purpose | Lines | Trigger |
|----------|---------|-------|---------|
| `enhanced-ci-cd.yml` | Main pipeline | 500+ | Push, PR, Manual, Tags |
| `testing.yml` | Testing | 430+ | Push, PR, workflow_call |
| `reusable/test-python.yml` | Python tests | 180+ | workflow_call |
| `reusable/docker-build.yml` | Docker builds | 200+ | workflow_call |
| `security-pipeline.yml` | Security scanning | 350+ | workflow_call, schedule |
| `render-deploy.yml` | Render.com deploy | 200+ | Push (main) |
| `documentation-*.yml` | Doc generation | Various | Push (docs/**) |
| + specialized workflows | Roblox sync, agent orchestration, etc. | | |

**Reduction**: 25 workflows → 10 core workflows (**60% reduction**)

---

## 🎛️ Configuration

### Environment Variables

#### Global (All workflows)
```yaml
PYTHON_VERSION: '3.12'
NODE_VERSION: '20'
DOCKER_BUILDKIT: 1
AWS_REGION: 'us-east-1'
REGISTRY: toolboxai.azurecr.io
```

#### Test-specific
```yaml
COVERAGE_THRESHOLD: 80
POSTGRES_VERSION: '15'
REDIS_VERSION: '7'
```

### GitHub Secrets Required

| Secret | Purpose | Used By |
|--------|---------|---------|
| `AWS_ROLE_ARN` | ECR authentication | Build, Deploy |
| `AWS_PROD_ROLE_ARN` | Production deploy | Production Deploy |
| `GITHUB_TOKEN` | GitHub API access | All (auto-provided) |
| `SLACK_WEBHOOK` | Notifications | Notifications |
| `OPENAI_API_KEY` | AI/ML features | **NOW USING SECRET** (was hardcoded) |

### Path Filters

**Skip CI on**:
- `docs/**`
- `**.md`
- `LICENSE`
- Documentation workflows

**Run on**:
- `apps/**`
- `core/**`
- `database/**`
- `tests/**`
- `requirements.txt`
- `package*.json`

---

## 🚀 Performance Improvements

### Build Time Comparison

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Average CI time** | 25-30 min | 15-18 min | **40% faster** |
| **Docker builds** | Sequential | Parallel | **5x faster** |
| **Test execution** | Single Python | Matrix 3.11+3.12 | **Better coverage** |
| **Cache hit rate** | ~30% | ~75% | **2.5x improvement** |
| **Redundant runs** | ~40% | ~5% | **Path filtering** |

### Caching Strategy

1. **Python Dependencies**: `pip cache` → `~/.cache/pip`
2. **Node Dependencies**: `npm cache` → `~/.npm`
3. **Docker Layers**: `type=gha` → GitHub Actions cache (10GB limit)
4. **Build Artifacts**: Uploaded with 7-day retention

---

## 🔐 Security Features

### Multi-Layer Security Scanning

1. **Secret Scanning**
   - GitLeaks: Scans for exposed secrets
   - Detect-secrets: Baseline comparison
   - **Result**: Exposed OpenAI API key found and documented

2. **Vulnerability Scanning**
   - Trivy: Filesystem and container scanning
   - Bandit: Python security linting
   - SARIF upload to GitHub Security tab

3. **Dependency Scanning**
   - Dependabot: Automated dependency updates
   - Grouped updates: Related packages in single PRs
   - **Schedule**: Mon-Thu (staggered)

4. **Container Security**
   - Non-root users (UID 1001-1004)
   - Read-only filesystems
   - Capability dropping
   - Resource limits

### Security Response Time

| Issue Type | Detection | Alert | Fix |
|------------|-----------|-------|-----|
| Critical vulnerability | < 1 hour | Immediate | < 24 hours |
| High vulnerability | < 4 hours | < 1 hour | < 48 hours |
| Exposed secret | Real-time | Immediate | < 1 hour |
| Dependency update | Weekly | Weekly | < 1 week |

---

## 📈 Monitoring & Observability

### Workflow Status

View real-time status:
- **GitHub Actions tab**: https://github.com/[org]/[repo]/actions
- **Branch protection**: Required checks must pass
- **Status badges**: See README.md

### Deployment Tracking

1. **GitHub Deployments API**: Tracks all environments
2. **ArgoCD**: Kubernetes deployments (dev)
3. **Terraform State**: Infrastructure tracking (staging/prod)
4. **Slack Notifications**: Real-time alerts

### Metrics Collected

- Build duration
- Test coverage (backend, frontend)
- Deployment frequency
- Mean time to recovery (MTTR)
- Success rate by workflow

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. Test Failures
**Symptom**: Tests pass locally but fail in CI

**Causes**:
- Environment differences
- Missing secrets
- Database state issues
- Timezone issues

**Solutions**:
```bash
# Run tests with CI environment
export TESTING=true
export USE_MOCK_LLM=true
export DATABASE_URL=postgresql://testuser:testpass@localhost/testdb
pytest tests/ -v
```

#### 2. Docker Build Failures
**Symptom**: Docker build fails with "layer not found"

**Causes**:
- Cache corruption
- Network issues
- Build context too large

**Solutions**:
- Clear cache: `docker buildx prune -f`
- Reduce context with `.dockerignore`
- Use `--no-cache` flag

#### 3. Deployment Failures
**Symptom**: Deployment succeeds but service is unhealthy

**Causes**:
- Missing environment variables
- Database migration failures
- Service dependencies not ready

**Solutions**:
- Check health check logs
- Verify environment variables
- Review rollout status
- Check ArgoCD sync status

### Debug Mode

Enable debug logging:
```yaml
env:
  ACTIONS_STEP_DEBUG: true
  ACTIONS_RUNNER_DEBUG: true
```

---

## 📚 Best Practices

### 1. Workflow Development
- ✅ Test workflows in feature branches
- ✅ Use reusable workflows for common tasks
- ✅ Add descriptive step names with emojis
- ✅ Set appropriate timeouts
- ✅ Use matrix builds for parallel execution

### 2. Secrets Management
- ✅ Use GitHub Secrets (never hardcode)
- ✅ Rotate secrets regularly
- ✅ Use environment-specific secrets
- ✅ Audit secret access logs

### 3. Performance
- ✅ Leverage caching aggressively
- ✅ Use path filters to skip unnecessary runs
- ✅ Run independent jobs in parallel
- ✅ Minimize build context size

### 4. Maintenance
- ✅ Review Dependabot PRs weekly
- ✅ Monitor workflow success rates
- ✅ Update actions monthly
- ✅ Archive unused workflows

---

## 🔮 Future Enhancements

### Planned Improvements

1. **Progressive Deployment**
   - Canary deployments (10% → 50% → 100%)
   - Automatic rollback on metrics degradation
   - A/B testing support

2. **Enhanced Observability**
   - OpenTelemetry integration
   - Distributed tracing
   - Custom Grafana dashboards

3. **Cost Optimization**
   - Spot instances for test runs
   - Smart cache eviction
   - Workflow run time analysis

4. **Advanced Testing**
   - Visual regression testing
   - Load testing in CI
   - Chaos engineering tests

---

## 📞 Support

**Documentation**: This file + `WORKFLOW_TROUBLESHOOTING.md`
**Issues**: GitHub Issues with `ci-cd` label
**Slack**: `#devops` channel
**On-call**: See PagerDuty schedule

---

**Last Updated**: 2025-11-08
**Maintained By**: DevOps Team
**Review Cycle**: Monthly

**Version**: 2.0.0 (Post-consolidation)
