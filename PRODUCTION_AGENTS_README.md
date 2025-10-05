# Production Agents Launch Guide

## Overview

This guide explains how to use the production workflow agents system to complete the final 25 days of development work required to reach v2.0.0 production deployment.

## System Architecture

### 6 Specialized Agents

| Agent | Days | Phase | Port | Priority | Status |
|-------|------|-------|------|----------|--------|
| **1. Integration Finalizer** | 1-3 | Integration & Commit | 8032 | 🔴 CRITICAL | ✅ Ready |
| **2. Testing Week 1-2** | 4-11 | Testing & Quality (Part 1) | 8033 | 🔴 CRITICAL | ✅ Ready |
| **3. Testing Week 3** | 12-18 | Testing & Quality (Part 2) | 8034 | 🟡 HIGH | ✅ Ready |
| **4. Performance Optimizer** | 19-21 | Performance & Monitoring | 8035 | 🟡 HIGH | ✅ Ready |
| **5. Monitoring Infrastructure** | 19-21 | Performance & Monitoring | 8036 | 🟡 HIGH | ✅ Ready |
| **6. Production Deployer** | 22-25 | Production Deployment | 8037 | 🔴 CRITICAL | ✅ Ready |

### Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: Integration & Commit (Days 1-3)                   │
│  Agent 1: Integration Finalizer                             │
│  ✓ Fix security vulnerabilities                             │
│  ✓ Merge all feature branches                               │
│  ✓ Tag v2.0.0-alpha release                                 │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 2: Testing & Quality Part 1 (Days 4-11)              │
│  Agent 2: Testing Week 1-2 Executor                         │
│  ✓ Write 500+ unit tests (Days 4-8)                         │
│  ✓ Code quality improvements (Days 9-11)                    │
│  ✓ Multi-tenancy 100% coverage                              │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 3: Testing & Quality Part 2 (Days 12-18)             │
│  Agent 3: Testing Week 3 & Integration                      │
│  ✓ Integration tests (Day 12)                               │
│  ✓ E2E tests with Playwright (Day 13)                       │
│  ✓ Load tests with Locust (Day 14)                          │
│  ✓ Dashboard component tests (Days 16-18)                   │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
         ┌─────────────┴─────────────┐
         ↓                           ↓
┌──────────────────────┐    ┌──────────────────────┐
│ Phase 4a: Performance│    │ Phase 4b: Monitoring │
│ (Days 19-21)         │    │ (Days 19-21)         │
│ Agent 4              │    │ Agent 5              │
│ ✓ Fix N+1 queries   │    │ ✓ Prometheus setup   │
│ ✓ Redis caching     │    │ ✓ Grafana dashboards │
│ ✓ Bundle optimize   │    │ ✓ Jaeger tracing     │
│                      │    │ ✓ 6 runbooks         │
└──────────┬───────────┘    └──────────┬───────────┘
           └────────────┬───────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 5: Production Deployment (Days 22-25)                │
│  Agent 6: Production Deployer                               │
│  ✓ Blue-green deployment                                    │
│  ✓ Gradual traffic shift (10% → 50% → 100%)                │
│  ✓ Tag and release v2.0.0                                   │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

```bash
# Ensure you're in the project root
cd /Users/grayghostdataconsultants/Development/projects/clients/Toolbox014/ToolboxAI-Solutions

# Verify worktrees are initialized
ls -la parallel-worktrees/

# Verify launch scripts exist
ls -la session-*.sh start-production-agents.sh

# All scripts should be executable (already done)
```

### Launch Master Menu

```bash
# Start the master launch system
./start-production-agents.sh
```

The menu provides:
- Agent overview with status
- Execution phase visualization
- Timeline (sequential vs parallel)
- Individual agent launch options
- Parallel launch for Agents 4 & 5
- Agent status checking
- Task file viewing

## Individual Agent Launch

### Agent 1: Integration Finalizer

```bash
./session-integration-finalizer.sh
```

**Mission**: Complete integration and commit work (Days 1-3)

**Daily Breakdown**:
- **Day 1**: Fix security vulnerabilities (12 total: 6 high, 6 moderate)
  - npm vulnerabilities in dashboard
  - Python vulnerabilities in backend
  - Commit security fixes
- **Day 2**: Merge feature branches
  - feature/git-cleanup
  - feature/documentation-2025
  - feature/security-audit-2025
  - feature/comprehensive-testing
  - release/v2.0.0
- **Day 3**: Release preparation
  - Tag v2.0.0-alpha
  - Update CHANGELOG.md
  - Push to origin

**Success Criteria**:
- ✅ All security vulnerabilities fixed
- ✅ All branches merged to main
- ✅ v2.0.0-alpha tagged
- ✅ 20+ worktrees cleaned up

**Task File**: `worktree-tasks/integration-finalizer-tasks.md` (734 lines)

---

### Agent 2: Testing Week 1-2

```bash
./session-testing-week1-2.sh
```

**Mission**: Write 500+ unit tests and improve code quality (Days 4-11)

**Weekly Structure**:

**Week 1 (Days 4-8)**: Unit Tests (500+ tests)
- Day 4: Core API tests (users, auth, roles) - 60 tests
- Day 5: Content & analytics - 80 tests
- Day 6: Roblox integration - 100 tests
- Day 7: Admin & workflows - 80 tests
- Day 8: Dashboard components - 180 tests

**Week 2 (Days 9-11)**: Code Quality
- Day 9: Replace 1,811 generic exception handlers
- Day 10: Multi-tenancy middleware (100% coverage)
- Day 11: Review and commit

**Success Criteria**:
- ✅ Backend coverage: 60% → 85%
- ✅ Dashboard coverage: 45% → 78%
- ✅ Custom exception hierarchy implemented
- ✅ Multi-tenancy middleware complete

**Task File**: `worktree-tasks/testing-week1-2-tasks.md` (953 lines)

---

### Agent 3: Testing Week 3

```bash
./session-testing-week3.sh
```

**Mission**: E2E, load, and integration tests (Days 12-18)

**Weekly Structure**:

**Week 3 (Days 12-15)**: Integration & E2E
- Day 12: Integration tests for workflows
- Day 13: E2E tests with Playwright (critical flows)
- Day 14: Load tests with Locust (>1000 RPS)
- Day 15: Dashboard component tests (384 components)

**Days 16-18**: Additional Testing & Documentation
- Day 16-17: Expand component test coverage
- Day 18: Test documentation and review

**Success Criteria**:
- ✅ 80%+ overall test coverage
- ✅ E2E tests for critical user flows
- ✅ Load tests pass (>1000 RPS sustained)
- ✅ Dashboard component tests complete

**Reference**: See Agent 3 specification in `PRODUCTION_AGENTS_PLAN.md`

---

### Agent 4: Performance Optimizer

```bash
./session-performance-optimizer.sh
```

**Mission**: Optimize performance and implement caching (Days 19-21)

**Daily Breakdown**:
- **Day 19**: Fix N+1 query patterns (15-20 instances)
  - Identify with Django Debug Toolbar
  - Implement eager loading with SQLAlchemy
  - Verify with load tests
- **Day 20**: Redis caching implementation
  - Cache 20+ endpoints
  - Implement TTL-based caching
  - Add cache warming scripts
- **Day 21**: Frontend bundle optimization
  - Code splitting
  - Lazy loading
  - Reduce bundle from 2.3MB → <1MB

**Success Criteria**:
- ✅ p50 response time: <100ms
- ✅ p95 response time: <200ms
- ✅ p99 response time: <500ms
- ✅ Sustained load: >1000 RPS
- ✅ Frontend bundle: <1MB
- ✅ Cache hit rate: >80%

**Reference**: See Agent 4 specification in `PRODUCTION_AGENTS_PLAN.md`

---

### Agent 5: Monitoring Infrastructure

```bash
./session-monitoring-infrastructure.sh
```

**Mission**: Setup Prometheus, Grafana, Jaeger, and runbooks (Days 19-21)

**Daily Breakdown**:
- **Day 19**: Prometheus metrics + alerting
  - API metrics (request rate, error rate, duration)
  - Database metrics (connection pool, query time)
  - Redis metrics (hit rate, memory usage)
  - 5 alert rules
- **Day 20**: Grafana dashboards
  - API dashboard (request rate, errors, latency)
  - Database dashboard (connections, slow queries)
  - Redis dashboard (memory, operations)
- **Day 21**: Jaeger tracing + runbooks
  - Distributed tracing setup
  - Service map visualization
  - 6 operational runbooks

**Success Criteria**:
- ✅ Prometheus metrics collecting
- ✅ 3 Grafana dashboards created
- ✅ Jaeger tracing operational
- ✅ 6 runbooks documented
- ✅ Alert rules configured

**Runbooks Required**:
1. Deployment Procedures
2. Incident Response
3. Rollback Procedures
4. Database Migration
5. Performance Issues
6. Security Incidents

**Reference**: See Agent 5 specification in `PRODUCTION_AGENTS_PLAN.md`

---

### Agent 6: Production Deployer

```bash
./session-production-deployer.sh
```

**Mission**: Blue-green deployment to production (Days 22-25)

**Daily Breakdown**:
- **Day 22**: Prepare green deployment
  - Create deployment manifests
  - Setup environment variables
  - Deploy green environment
- **Day 23**: Initial traffic shift
  - Shift 10% traffic to green
  - Monitor for 2 hours
  - Verify metrics
- **Day 24**: Complete traffic shift
  - Shift to 50%, monitor
  - Shift to 100%, monitor
  - Decommission blue environment
- **Day 25**: Release and cleanup
  - Tag v2.0.0
  - Update documentation
  - Post-deployment verification

**Success Criteria**:
- ✅ Zero-downtime deployment
- ✅ Gradual traffic shift (10% → 50% → 100%)
- ✅ v2.0.0 live in production
- ✅ All monitoring dashboards operational
- ✅ Post-deployment verification passed

**Safety Checks** (CRITICAL):
1. ✅ All tests passing (500+ tests)
2. ✅ Test coverage >80%
3. ✅ Load tests passed (>1000 RPS)
4. ✅ Monitoring dashboards ready
5. ✅ Rollback procedures documented

**Reference**: See Agent 6 specification in `PRODUCTION_AGENTS_PLAN.md`

## Parallel Execution

### Agents 4 & 5 (Days 19-21)

These agents can run in parallel for efficiency:

```bash
# Option 1: Use master script (recommended)
./start-production-agents.sh
# Select option 7: "Launch Agents 4 & 5 (Parallel)"

# Option 2: Manual launch in separate terminals
# Terminal 1:
./session-performance-optimizer.sh

# Terminal 2:
./session-monitoring-infrastructure.sh
```

**Benefits of Parallel Execution**:
- Reduces timeline from 25 to 21 developer days
- Both agents work on independent systems
- No blocking dependencies

## Worktree Structure

Each agent has its own isolated worktree:

```
parallel-worktrees/
├── integration-finalizer/        # feature/integration-final
├── testing-week1-2/              # feature/testing-unit-quality
├── testing-week3/                # feature/testing-e2e-integration
├── performance-optimizer/        # feature/performance-optimization
├── monitoring-infrastructure/    # feature/monitoring-setup
└── production-deployer/          # feature/production-deployment
```

**Benefits**:
- Isolated development environments
- Separate branches for each agent
- No interference between agents
- Easy to switch contexts

## Port Assignments

Each agent runs its development server on a unique port:

| Agent | Port | Service |
|-------|------|---------|
| Agent 1 | 8032 | Backend API |
| Agent 2 | 8033 | Backend API |
| Agent 3 | 8034 | Backend API |
| Agent 4 | 8035 | Backend API + Redis |
| Agent 5 | 8036 | Backend API + Monitoring Stack |
| Agent 6 | 8037 | Backend API + Kubernetes |

**Additional Ports** (Agent 5):
- Prometheus: 9090
- Grafana: 3001
- Jaeger: 16686

## Documentation Reference

### Task Files
- `worktree-tasks/integration-finalizer-tasks.md` - Agent 1 (734 lines)
- `worktree-tasks/testing-week1-2-tasks.md` - Agent 2 (953 lines)
- `PRODUCTION_AGENTS_PLAN.md` - Agents 3-6 specifications (600+ lines)

### Summary Documents
- `PRODUCTION_WORKFLOW_SUMMARY.md` - Executive summary
- `PRODUCTION_READINESS_ASSESSMENT.md` - Current state analysis
- `TODO.md` - Complete production roadmap

## Timeline & Milestones

### Sequential Execution (25 days)
```
Days 1-3   → Agent 1: Integration Finalizer
Days 4-11  → Agent 2: Testing Week 1-2
Days 12-18 → Agent 3: Testing Week 3
Days 19-21 → Agent 4: Performance Optimizer
Days 19-21 → Agent 5: Monitoring Infrastructure
Days 22-25 → Agent 6: Production Deployer
```

### Parallel Execution (21 days)
```
Days 1-3   → Agent 1: Integration Finalizer
Days 4-11  → Agent 2: Testing Week 1-2
Days 12-18 → Agent 3: Testing Week 3
Days 19-21 → Agents 4 & 5 (Parallel)
Days 22-25 → Agent 6: Production Deployer
```

### Key Milestones

| Date | Milestone | Agent | Deliverable |
|------|-----------|-------|-------------|
| Oct 3-5 | Integration Complete | 1 | v2.0.0-alpha, all code merged |
| Oct 6-13 | Testing Week 1-2 Complete | 2 | 500+ tests, 85% coverage |
| Oct 14-20 | Testing Week 3 Complete | 3 | E2E/load tests, 80%+ coverage |
| Oct 21-23 | Performance & Monitoring | 4 & 5 | Optimized, monitored system |
| Oct 24-28 | Production Deployment | 6 | v2.0.0 live in production |

## Success Metrics

### Test Coverage Targets
- Backend: 60% → 85%
- Dashboard: 45% → 78%
- API Endpoints: 70% → 92%
- Critical Paths: 80% → 96%

### Performance Targets
- p50 Response Time: <100ms
- p95 Response Time: <200ms
- p99 Response Time: <500ms
- Sustained Load: >1000 RPS
- Frontend Bundle: 2.3MB → <1MB
- Cache Hit Rate: >80%

### Quality Targets
- Security Vulnerabilities: 12 → 0
- Generic Exception Handlers: 1,811 → 0
- TODO/FIXME Comments: 70 → 0
- Code Duplication: Eliminate identified instances
- Multi-tenancy: 100% tenant isolation

## Risk Management

### High-Risk Areas

1. **Testing Coverage Gap** (CRITICAL)
   - Risk: Insufficient test coverage (0.59 test/endpoint ratio)
   - Mitigation: Agents 2 & 3 focus entirely on testing
   - Timeline: 15 days dedicated to testing

2. **Performance Issues** (HIGH)
   - Risk: N+1 queries causing slowdowns
   - Mitigation: Agent 4 systematic optimization
   - Timeline: 3 days for performance work

3. **Production Deployment** (CRITICAL)
   - Risk: Downtime during deployment
   - Mitigation: Blue-green deployment with gradual shift
   - Timeline: 4 days for careful deployment

4. **Monitoring Gaps** (HIGH)
   - Risk: No production observability
   - Mitigation: Agent 5 comprehensive monitoring setup
   - Timeline: 3 days for monitoring infrastructure

5. **Integration Conflicts** (MEDIUM)
   - Risk: 20+ worktrees may have merge conflicts
   - Mitigation: Agent 1 careful branch merging
   - Timeline: 3 days for integration work

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Check what's using the port
lsof -i :8032

# Kill the process
kill $(lsof -t -i:8032)

# Or let the script handle it (automatic)
```

#### Worktree Not Found
```bash
# Re-initialize worktrees
cd parallel-worktrees
git worktree add integration-finalizer -b feature/integration-final
git worktree add testing-week1-2 -b feature/testing-unit-quality
# ... (see initialization commands in documentation)
```

#### Server Won't Start
```bash
# Check logs
tail -f /tmp/integration-finalizer-server.log

# Verify virtual environment
cd parallel-worktrees/integration-finalizer/apps/backend
source venv/bin/activate

# Reinstall dependencies if needed
pip install -r requirements.txt
```

#### Permission Denied on Scripts
```bash
# Make scripts executable
chmod +x session-*.sh start-production-agents.sh
```

## Best Practices

### Before Starting Each Agent
1. Review the task file or PRODUCTION_AGENTS_PLAN.md
2. Understand the daily breakdown
3. Check dependencies (e.g., Redis for Agent 4)
4. Verify port availability
5. Read success criteria

### During Agent Work
1. Follow the daily checklist in task files
2. Run tests after each module completion
3. Update TODO.md as you complete tasks
4. Commit frequently with descriptive messages
5. Monitor server logs for errors

### After Completing Each Agent
1. Run full test suite
2. Verify success criteria met
3. Update PRODUCTION_WORKFLOW_SUMMARY.md
4. Push all changes to origin
5. Review and handoff to next agent

### Quality Gates
- **Agent 1**: All branches merged, v2.0.0-alpha tagged
- **Agent 2**: 500+ tests written, 85% backend coverage
- **Agent 3**: 80%+ overall coverage, E2E tests passing
- **Agent 4**: Performance targets met (p95 <200ms)
- **Agent 5**: Monitoring operational, 6 runbooks complete
- **Agent 6**: v2.0.0 in production, zero downtime

## Getting Help

### Documentation
- Task files: `worktree-tasks/*.md`
- Master plan: `PRODUCTION_AGENTS_PLAN.md`
- Summary: `PRODUCTION_WORKFLOW_SUMMARY.md`
- TODO: `TODO.md`

### Logs
- Server logs: `/tmp/<session-name>-server.log`
- Test output: `pytest -v` or `npm test`
- Build output: `npm run build`

### Commands
- View agent status: `./start-production-agents.sh` (option 8)
- View task files: `./start-production-agents.sh` (option 9)
- Check worktrees: `git worktree list`
- Monitor ports: `lsof -i :<port>`

## Next Steps

1. **Review the master plan**: Read `PRODUCTION_AGENTS_PLAN.md`
2. **Start with Agent 1**: `./session-integration-finalizer.sh`
3. **Follow the daily checklist**: In `worktree-tasks/integration-finalizer-tasks.md`
4. **Complete all phases**: Days 1-25
5. **Deploy to production**: v2.0.0 live

---

**Last Updated**: 2025-10-02
**Status**: ✅ All agents ready for launch
**Timeline**: 25 days sequential, 21 days parallel
**Target**: v2.0.0 production deployment
