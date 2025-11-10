# pnpm Migration Implementation Plan
**Status:** Ready for Execution  
**Created:** 2025-11-09  
**Priority:** High  
**Risk Level:** Medium  

---

## Executive Summary

This plan outlines the complete implementation strategy to finalize the npm → pnpm migration for ToolBoxAI-Solutions. The migration is 95% complete with code changes ready, but requires critical bug fixes (typos in workflows), comprehensive testing, and coordinated deployment.

### Migration Status
- ✅ **Completed:** pnpm installation, workspace configuration, package updates, Dockerfile rewrites
- 🐛 **Critical Issue:** 72 instances of "ppnpm" typo in workflow files (must fix before commit)
- ⏳ **Remaining:** Testing, bug fixes, commit, deployment verification

---

## Phase 1: Critical Bug Fixes (MUST DO FIRST)

### Priority: CRITICAL
**Time Estimate:** 15 minutes  
**Risk:** High - Workflow failures if not fixed

#### 1.1 Fix "ppnpm" Typo in All Workflow Files

**Problem:** Automated find-and-replace created "ppnpm" instead of "pnpm" in 72 locations across 21 workflow files.

**Action:**
```bash
cd "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"

# Find all occurrences (verification)
grep -r "ppnpm" .github/workflows/ | wc -l

# Fix all instances (macOS-compatible sed)
find .github/workflows -name "*.yml" -type f -exec sed -i '' 's/ppnpm/pnpm/g' {} +

# Verify fix
grep -r "ppnpm" .github/workflows/ | wc -l  # Should be 0
```

**Verification:**
```bash
# Check specific files that had the typo
git diff .github/workflows/dashboard-build.yml | grep "pnpm"
git diff .github/workflows/ci-cd-main.yml | grep "pnpm"
git diff .github/workflows/enhanced-ci-cd.yml | grep "pnpm"
```

**Expected Result:** All 72 instances of "ppnpm" replaced with "pnpm"

#### 1.2 Verify Workflow Syntax

```bash
# Check for YAML syntax errors in modified workflows
for file in .github/workflows/*.yml; do
  echo "Checking $file"
  python3 -c "import yaml; yaml.safe_load(open('$file'))" && echo "✓ Valid" || echo "✗ Invalid"
done
```

**Decision Point:** If any syntax errors are found, fix before proceeding.

---

## Phase 2: Local Verification & Testing

### Priority: HIGH
**Time Estimate:** 30-45 minutes  
**Risk:** Medium - May uncover dependency issues

#### 2.1 Clean Install Test

**Objective:** Verify pnpm can install from scratch with the new configuration.

```bash
cd "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"

# Backup current node_modules (just in case)
mv node_modules node_modules.backup

# Clean install
pnpm install --frozen-lockfile

# Verify critical binaries
ls -la node_modules/@rollup/rollup-darwin-arm64
ls -la node_modules/.bin/vite
ls -la node_modules/.bin/tsc
```

**Success Criteria:**
- ✓ Installation completes without errors
- ✓ Rollup Darwin ARM64 binary exists
- ✓ All workspace packages linked correctly
- ✓ No peer dependency warnings (blocked by .npmrc config)

**Failure Handling:**
- If install fails: Review error, restore from backup
- If binaries missing: Check .npmrc hoisting configuration
- If workspace issues: Verify pnpm-workspace.yaml paths

#### 2.2 Type Checking Test

**Objective:** Ensure TypeScript compilation works with pnpm.

```bash
cd apps/dashboard

# Run type checking
pnpm typecheck

# Expected: No type errors (or same errors as before migration)
```

**Success Criteria:**
- ✓ Type checking completes
- ✓ No new type errors introduced by pnpm
- ✓ Build info files created (*.tsbuildinfo)

#### 2.3 Unit Tests

**Objective:** Verify test infrastructure works with pnpm.

```bash
cd apps/dashboard

# Run tests (no coverage for speed)
pnpm test --run

# Check test results
echo $?  # Should be 0
```

**Success Criteria:**
- ✓ Tests execute (even if --passWithNoTests)
- ✓ Vitest loads configuration correctly
- ✓ No module resolution errors

#### 2.4 Build Test

**Objective:** Verify production build works with pnpm and rollup.

```bash
cd apps/dashboard

# Clean previous build
rm -rf dist

# Production build
pnpm build

# Verify output
ls -lh dist/
du -sh dist/

# Check for source maps
ls dist/assets/*.map | wc -l
```

**Success Criteria:**
- ✓ Build completes without errors
- ✓ dist/ directory created with assets
- ✓ Bundle size reasonable (~2-5MB before gzip)
- ✓ No rollup binary errors
- ✓ Source maps generated (for Sentry)

**Critical Checkpoints:**
```bash
# Verify these files exist
ls dist/index.html
ls dist/assets/*.js
ls dist/assets/*.css

# Check for common build issues
grep -r "undefined" dist/assets/*.js | head -5  # Should be minimal
```

#### 2.5 Workspace Commands Test

**Objective:** Verify workspace-level commands work.

```bash
# From project root
cd "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"

# Test workspace commands
pnpm dashboard:build
pnpm dashboard:test --run
pnpm dashboard:lint
```

**Success Criteria:**
- ✓ All workspace commands execute
- ✓ No "workspace not found" errors
- ✓ Commands target correct package

#### 2.6 Dev Server Test (Optional but Recommended)

**Objective:** Ensure dev server starts correctly.

```bash
cd apps/dashboard

# Start dev server (will run in background)
pnpm dev &
DEV_PID=$!

# Wait for server to start
sleep 10

# Check if server is running
curl -f http://localhost:5179/ > /dev/null 2>&1 && echo "✓ Dev server running" || echo "✗ Dev server failed"

# Kill dev server
kill $DEV_PID
```

**Success Criteria:**
- ✓ Vite dev server starts on port 5179
- ✓ No module resolution errors
- ✓ Hot reload works (manual verification)

---

## Phase 3: Git Workflow & Commit

### Priority: HIGH
**Time Estimate:** 20 minutes  
**Risk:** Low - Straightforward git operations

#### 3.1 Review All Changes

**Objective:** Understand what will be committed.

```bash
cd "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"

# See summary of changes
git status

# Review modified files (organized by type)
echo "=== Workflow Changes ==="
git diff --stat .github/workflows/

echo "=== Docker Changes ==="
git diff --stat apps/dashboard/Dockerfile infrastructure/docker/Dockerfile.dashboard

echo "=== Build Configuration ==="
git diff --stat Makefile vercel.json apps/dashboard/vercel.json

echo "=== Package Management ==="
git diff --stat package.json apps/dashboard/package.json
```

**Review Checklist:**
- [ ] All workflow files changed consistently (pnpm, not ppnpm)
- [ ] Dockerfiles use Corepack correctly
- [ ] vercel.json has ENABLE_EXPERIMENTAL_COREPACK=1
- [ ] package.json has packageManager field
- [ ] Makefile uses pnpm commands
- [ ] No accidental changes to unrelated files

#### 3.2 Review Specific Changes (Line by Line)

```bash
# Critical files to review carefully
git diff .github/workflows/dashboard-build.yml
git diff .github/workflows/deploy.yml
git diff apps/dashboard/Dockerfile
git diff vercel.json
git diff package.json
```

**What to Look For:**
- ✓ Correct cache keys: `pnpm-lock.yaml` not `package-lock.json`
- ✓ Correct install command: `pnpm install --frozen-lockfile`
- ✓ Corepack enable commands in Dockerfiles
- ✓ No remnants of npm ci or npm install
- ✓ packageManager field present

#### 3.3 Stage Files for Commit

**Strategy:** Stage incrementally by category for better organization.

```bash
# Stage core package management files
git add package.json
git add package-lock.json  # Deletion
git add pnpm-lock.yaml
git add pnpm-workspace.yaml
git add .npmrc

# Stage workflow files
git add .github/workflows/

# Stage Docker files
git add apps/dashboard/Dockerfile
git add infrastructure/docker/Dockerfile.dashboard

# Stage build configuration
git add Makefile
git add vercel.json
git add apps/dashboard/vercel.json
git add apps/dashboard/package.json

# Stage scripts
git add scripts/deployment/deploy_pipeline.sh
# (Add any other modified scripts)

# Stage documentation
git add docs/pnpm-migration-2025-11-09.md
git add docs/pnpm-migration-implementation-plan.md  # This file
```

**Verification:**
```bash
# Check staged files
git status

# Should show:
# - Modified: 29 files
# - Deleted: 1 file (package-lock.json)
# - Added: 4 files (pnpm-lock.yaml, pnpm-workspace.yaml, .npmrc, docs)
```

#### 3.4 Create Conventional Commit

**Commit Message Format:**
```
refactor(deps)!: migrate from npm to pnpm for improved performance

BREAKING CHANGE: Package manager changed from npm to pnpm v9.15.0

This migration improves installation speed, reduces disk usage, and provides
better monorepo support for the ToolBoxAI-Solutions workspace.

Changes:
- Add pnpm v9.15.0 with Corepack (package.json packageManager field)
- Create pnpm-workspace.yaml for monorepo configuration
- Add .npmrc with hoisted node_modules for compatibility
- Generate pnpm-lock.yaml (replaces package-lock.json)
- Update all 21 GitHub Actions workflows:
  - Replace npm ci with pnpm install --frozen-lockfile
  - Update cache keys to use pnpm-lock.yaml
  - Add Corepack enablement steps
- Rewrite Dockerfiles with Corepack:
  - apps/dashboard/Dockerfile
  - infrastructure/docker/Dockerfile.dashboard
- Update deployment configurations:
  - vercel.json: Add ENABLE_EXPERIMENTAL_COREPACK=1
  - Makefile: Replace npm with pnpm commands
- Update shell scripts in scripts/deployment/

Migration benefits:
- Faster installation (parallelized fetching)
- Reduced disk usage (content-addressable store)
- Better workspace support (pnpm workspaces)
- Stricter dependency resolution
- Compatible with existing Node.js tooling

Developer migration guide:
1. Pull latest changes
2. Remove node_modules and package-lock.json
3. Run: pnpm install
4. Use pnpm instead of npm for all commands

Closes #<issue-number-if-exists>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Create Commit:**
```bash
# Commit with message
git commit -m "$(cat <<'EOF'
refactor(deps)!: migrate from npm to pnpm for improved performance

BREAKING CHANGE: Package manager changed from npm to pnpm v9.15.0

This migration improves installation speed, reduces disk usage, and provides
better monorepo support for the ToolBoxAI-Solutions workspace.

Changes:
- Add pnpm v9.15.0 with Corepack (package.json packageManager field)
- Create pnpm-workspace.yaml for monorepo configuration
- Add .npmrc with hoisted node_modules for compatibility
- Generate pnpm-lock.yaml (replaces package-lock.json)
- Update all 21 GitHub Actions workflows:
  - Replace npm ci with pnpm install --frozen-lockfile
  - Update cache keys to use pnpm-lock.yaml
  - Add Corepack enablement steps
- Rewrite Dockerfiles with Corepack:
  - apps/dashboard/Dockerfile
  - infrastructure/docker/Dockerfile.dashboard
- Update deployment configurations:
  - vercel.json: Add ENABLE_EXPERIMENTAL_COREPACK=1
  - Makefile: Replace npm with pnpm commands
- Update shell scripts in scripts/deployment/

Migration benefits:
- Faster installation (parallelized fetching)
- Reduced disk usage (content-addressable store)
- Better workspace support (pnpm workspaces)
- Stricter dependency resolution
- Compatible with existing Node.js tooling

Developer migration guide:
1. Pull latest changes
2. Remove node_modules and package-lock.json
3. Run: pnpm install
4. Use pnpm instead of npm for all commands

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# Verify commit
git log -1 --stat
```

#### 3.5 Branching Strategy Decision

**Option A: Direct to Main (Recommended for this project)**
- **Pros:** Already on main, changes are infrastructure-only, team is aware
- **Cons:** Skips PR review (but changes are well-tested)
- **When to use:** Small team, infrastructure changes, time-sensitive

**Option B: Feature Branch + PR**
- **Pros:** Code review, CI testing before merge, safer
- **Cons:** Delays deployment, may duplicate work
- **When to use:** Large team, breaking changes, regulatory requirements

**Decision Matrix:**
| Factor | Direct to Main | Feature Branch |
|--------|---------------|----------------|
| Team Size | Small (1-3) | Large (4+) |
| Urgency | High | Low |
| Risk | Low (well-tested) | High (untested) |
| CI Readiness | Workflows already updated | Workflows need testing |
| Rollback Plan | Git revert | Close PR |

**Recommended:** Direct to Main (since you're already on main branch, changes are infrastructure-only, and rollback is straightforward)

**If Direct to Main:**
```bash
# Push to main
git push origin main
```

**If Feature Branch:**
```bash
# Create feature branch
git checkout -b feat/pnpm-migration

# Push feature branch
git push origin feat/pnpm-migration

# Create PR via gh CLI
gh pr create \
  --title "refactor(deps)!: Migrate from npm to pnpm" \
  --body "$(cat <<'EOF'
## Summary
Migrates package manager from npm to pnpm v9.15.0 for improved performance and better monorepo support.

## Changes
- ✅ pnpm v9.15.0 installed via Corepack
- ✅ Workspace configuration (pnpm-workspace.yaml)
- ✅ All 21 GitHub Actions workflows updated
- ✅ Dockerfiles rewritten with Corepack
- ✅ Deployment configs updated (Vercel, Makefile)
- ✅ Migration documentation created

## Testing
- ✅ Clean install tested
- ✅ Type checking passes
- ✅ Unit tests pass
- ✅ Production build succeeds
- ✅ Workspace commands work
- ✅ Dev server starts correctly

## Migration Guide for Team
1. Pull latest changes
2. Remove `node_modules` and `package-lock.json`
3. Run: `pnpm install`
4. Use `pnpm` instead of `npm` for all commands

## Rollback Plan
If issues occur:
```bash
git revert <commit-sha>
npm install
```

## Risk Assessment
- **Risk Level:** Medium
- **Impact:** All developers must switch to pnpm
- **Rollback Time:** < 5 minutes
- **CI/CD Impact:** Workflows will use pnpm (tested locally)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)" \
  --base main \
  --draft  # Remove --draft when ready to merge
```

---

## Phase 4: CI/CD Validation

### Priority: HIGH
**Time Estimate:** 20-40 minutes (depending on CI queue)  
**Risk:** Medium - CI may fail on first run

#### 4.1 Monitor Initial CI Run

**After Push:**
```bash
# Watch CI status via gh CLI
gh run watch

# Or view in browser
gh run view --web
```

**Critical Workflows to Watch:**
1. **dashboard-build.yml** - Tests pnpm install and build
2. **ci.yml** - Comprehensive CI checks
3. **comprehensive-testing.yml** - Full test suite
4. **deploy.yml** - Deployment preview (if auto-triggered)

#### 4.2 Expected CI Outcomes

**Likely Success:**
- ✓ Dependency installation (pnpm install --frozen-lockfile)
- ✓ Type checking
- ✓ Linting
- ✓ Unit tests

**Potential Failures (and fixes):**

**Issue 1: Cache Miss on First Run**
- **Symptom:** Slower CI times on first run
- **Cause:** New cache key format (pnpm-lock.yaml)
- **Fix:** No action needed, will cache on subsequent runs
- **Impact:** Low (one-time slowdown)

**Issue 2: Corepack Not Enabled in CI**
- **Symptom:** "corepack: command not found"
- **Cause:** Workflow missing Corepack setup
- **Fix:** Add to workflow:
  ```yaml
  - name: Enable Corepack
    run: corepack enable
  ```
- **Impact:** Medium (workflow fails)

**Issue 3: pnpm Version Mismatch**
- **Symptom:** "pnpm version 8.x.x does not match packageManager"
- **Cause:** GitHub Actions using wrong pnpm version
- **Fix:** Corepack should handle this (from packageManager field)
- **Impact:** Low (should not occur with Corepack)

**Issue 4: Workspace Resolution Errors**
- **Symptom:** "No workspace package found for apps/dashboard"
- **Cause:** Incorrect pnpm-workspace.yaml paths
- **Fix:** Verify workspace paths match directory structure
- **Impact:** High (blocks all CI)

#### 4.3 CI Failure Response Plan

**Decision Tree:**

```
CI Failed?
├─ Yes
│  ├─ Is it pnpm-related?
│  │  ├─ Yes → Fix workflow, push new commit
│  │  └─ No → Unrelated issue, separate fix
│  └─ Critical?
│     ├─ Yes (blocks deployment)
│     │  └─ Hotfix immediately
│     └─ No (minor test failure)
│        └─ Create issue, fix later
└─ No
   └─ Proceed to Phase 5
```

**Hotfix Process (if needed):**
```bash
# Make fix
vim .github/workflows/<failing-workflow>.yml

# Commit hotfix
git add .github/workflows/<failing-workflow>.yml
git commit -m "fix(ci): resolve pnpm workflow issue in <workflow>"
git push origin main

# Monitor new CI run
gh run watch
```

---

## Phase 5: Deployment Strategy

### Priority: HIGH
**Time Estimate:** 30-60 minutes (includes monitoring)  
**Risk:** Medium-High - Production deployment

#### 5.1 Vercel Dashboard Deployment

**Pre-Deployment Checklist:**
- [ ] CI passing on main branch
- [ ] Local build tested successfully
- [ ] vercel.json has ENABLE_EXPERIMENTAL_COREPACK=1
- [ ] Vercel project settings allow Corepack (check in dashboard)
- [ ] Build command is `pnpm build` (check Vercel dashboard)
- [ ] Install command is `pnpm install` (check Vercel dashboard)

**Deployment Options:**

**Option A: Auto-Deploy (via Git Push)**
- Vercel detects push to main
- Automatically triggers deployment
- No manual intervention needed

**Option B: Manual Deploy (via CLI)**
```bash
cd apps/dashboard

# Preview deployment (test first)
pnpm exec vercel

# Production deployment
pnpm exec vercel --prod
```

**Option C: Manual Deploy (via Vercel Dashboard)**
1. Go to Vercel dashboard
2. Select ToolBoxAI-Solutions project
3. Click "Deploy" button
4. Select main branch
5. Monitor build logs

**Recommended:** Option A (auto-deploy) if CI is green

#### 5.2 Monitor Vercel Build

**Watch Build Logs:**
```bash
# Via CLI
pnpm exec vercel logs <deployment-url>

# Or in Vercel dashboard
# Navigate to Deployments → Latest → View Logs
```

**Critical Build Stages:**
1. **Install Dependencies** (pnpm install)
   - Should complete in 30-60s (first time may take longer)
   - Watch for: "Lockfile is up to date"

2. **Build** (pnpm build)
   - Should complete in 60-120s
   - Watch for: "vite build completed"

3. **Upload** (Vercel uploads dist/)
   - Should complete in 10-30s
   - Watch for: "Deployment ready"

**Success Criteria:**
- ✓ pnpm install completes without errors
- ✓ Build completes with exit code 0
- ✓ Deployment URL accessible
- ✓ No console errors in browser
- ✓ Critical pages load (login, dashboard, course viewer)

#### 5.3 Vercel Deployment Failure Scenarios

**Scenario 1: Corepack Not Enabled**
- **Symptom:** "pnpm: command not found"
- **Fix:**
  1. Check vercel.json has `ENABLE_EXPERIMENTAL_COREPACK=1`
  2. Ensure Vercel project settings enable Corepack
  3. May need to contact Vercel support (Beta feature)
- **Rollback:** Deploy previous commit

**Scenario 2: Build Fails (Rollup Issue)**
- **Symptom:** "Could not load @rollup/rollup-linux-x64-gnu"
- **Fix:**
  1. Check optionalDependencies include @rollup/rollup-linux-x64-gnu
  2. Verify postinstall script in apps/dashboard/package.json
  3. May need to install rollup binary explicitly
- **Rollback:** Deploy previous commit

**Scenario 3: Out of Memory**
- **Symptom:** "JavaScript heap out of memory"
- **Fix:**
  1. Increase Node memory in vercel.json:
     ```json
     "build": {
       "env": {
         "NODE_OPTIONS": "--max-old-space-size=4096"
       }
     }
     ```
  2. Push fix, redeploy
- **Rollback:** Deploy previous commit

**Scenario 4: Environment Variable Issues**
- **Symptom:** Build succeeds but runtime errors
- **Fix:**
  1. Check Vercel environment variables are still set
  2. Verify .env.example matches required variables
  3. Re-add any missing variables in Vercel dashboard
- **Rollback:** Deploy previous commit

#### 5.4 Render Backend Deployment

**Note:** Backend is Python-only, no changes needed for pnpm migration.

**Verification:**
```bash
# Check backend is still healthy
curl -f https://your-backend.onrender.com/health

# Check backend API
curl -f https://your-backend.onrender.com/api/v1/status
```

**Expected Result:** Backend continues to work normally (no impact from frontend pnpm migration)

#### 5.5 Post-Deployment Smoke Tests

**Manual Testing Checklist:**
- [ ] Dashboard homepage loads
- [ ] Login/authentication works
- [ ] Course browser loads courses
- [ ] 3D course viewer works (Three.js)
- [ ] Real-time features work (Pusher)
- [ ] No console errors in browser DevTools
- [ ] API calls to backend succeed
- [ ] Sentry error tracking active (check Sentry dashboard)

**Automated Smoke Tests (if available):**
```bash
# Run Playwright E2E tests against production
cd apps/dashboard
PLAYWRIGHT_BASE_URL=https://your-production-url.vercel.app pnpm test:e2e --project chromium
```

#### 5.6 Rollback Plan

**If Deployment Fails Catastrophically:**

**Option 1: Instant Rollback via Vercel**
1. Go to Vercel dashboard
2. Find previous successful deployment
3. Click "Promote to Production"
4. Deployment reverts in < 1 minute

**Option 2: Git Revert**
```bash
# Revert pnpm migration commit
git revert HEAD

# Push revert
git push origin main

# Vercel auto-deploys reverted state
# Or manually deploy: cd apps/dashboard && vercel --prod
```

**Option 3: Emergency Hotfix**
```bash
# If specific issue identified, push hotfix
git add <fixed-files>
git commit -m "hotfix: resolve pnpm deployment issue"
git push origin main
```

**Rollback Time Estimate:** 2-5 minutes

---

## Phase 6: Documentation & Communication

### Priority: MEDIUM
**Time Estimate:** 30 minutes  
**Risk:** Low

#### 6.1 Update Project CLAUDE.md

**Location:** `/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/CLAUDE.md`

**Changes to Make:**

```markdown
# CLAUDE.md

## Development Environment

### Package Manager: pnpm v9.15.0

This project uses **pnpm** (not npm) for package management. pnpm provides faster installs, better disk usage, and improved monorepo support.

#### Installation

pnpm is managed via Corepack (included in Node.js 16.9+):

```bash
corepack enable
pnpm --version  # Should show 9.15.0
```

#### Common Commands

```bash
# Install dependencies
pnpm install

# Install with frozen lockfile (CI)
pnpm install --frozen-lockfile

# Add dependency
pnpm add <package>
pnpm add -D <dev-package>

# Update dependency
pnpm update <package>

# Run workspace commands
pnpm dashboard:dev       # Start dashboard dev server
pnpm dashboard:build     # Build dashboard
pnpm dashboard:test      # Run dashboard tests
pnpm dashboard:lint      # Lint dashboard

# Run commands in specific workspace
pnpm --filter apps/dashboard dev
pnpm --filter apps/dashboard build

# Clean install (remove node_modules first)
rm -rf node_modules apps/*/node_modules
pnpm install
```

#### Workspace Structure

This monorepo uses pnpm workspaces:

```
.
├── apps/
│   ├── dashboard/       (React + Vite)
│   └── backend/         (Python - no pnpm)
├── packages/            (Shared packages)
├── pnpm-workspace.yaml  (Workspace config)
├── pnpm-lock.yaml       (Lockfile - commit this)
└── .npmrc               (pnpm config)
```

#### Migration from npm

If you previously used npm:

```bash
# Remove npm artifacts
rm -rf node_modules package-lock.json
rm -rf apps/*/node_modules

# Install with pnpm
pnpm install

# Update muscle memory
alias npm='echo "Use pnpm instead!" && false'
```

#### Troubleshooting

**Issue: "pnpm: command not found"**
```bash
corepack enable
corepack prepare pnpm@9.15.0 --activate
```

**Issue: "Lockfile is up to date, resolution step is skipped"**
This is normal and means pnpm is skipping unnecessary work.

**Issue: Peer dependency warnings**
Check `.npmrc` - `strict-peer-dependencies=false` allows flexibility.

**Issue: Module not found in workspace**
```bash
pnpm install  # Recreates symlinks
```

---

### Technology Stack

(existing content...)

**Build Tools:**
- **Vite 7.0** - Frontend build tool
- **pnpm 9.15.0** - Package manager
- **TypeScript 5.9** - Type safety
- **Rollup** - Bundler (via Vite)

(rest of existing content...)
```

#### 6.2 Create Quick Reference Guide

**Create:** `docs/pnpm-quick-reference.md`

```markdown
# pnpm Quick Reference

## Installation

```bash
corepack enable
```

## Basic Commands

| Task | Command |
|------|---------|
| Install dependencies | `pnpm install` |
| Add package | `pnpm add <pkg>` |
| Add dev package | `pnpm add -D <pkg>` |
| Remove package | `pnpm remove <pkg>` |
| Update package | `pnpm update <pkg>` |
| Run script | `pnpm <script>` |
| Run script in workspace | `pnpm --filter <workspace> <script>` |

## Workspace Commands

| Task | Command |
|------|---------|
| Dev server | `pnpm dashboard:dev` |
| Build | `pnpm dashboard:build` |
| Test | `pnpm dashboard:test` |
| Lint | `pnpm dashboard:lint` |

## Troubleshooting

### pnpm not found
```bash
corepack enable
```

### Module not found
```bash
pnpm install
```

### Clean install
```bash
rm -rf node_modules apps/*/node_modules
pnpm install
```

## Migration from npm

| npm | pnpm |
|-----|------|
| `npm install` | `pnpm install` |
| `npm ci` | `pnpm install --frozen-lockfile` |
| `npm install <pkg>` | `pnpm add <pkg>` |
| `npm uninstall <pkg>` | `pnpm remove <pkg>` |
| `npm run <script>` | `pnpm <script>` |
| `npm run <script> -w <workspace>` | `pnpm --filter <workspace> <script>` |

## Resources

- [pnpm Documentation](https://pnpm.io/)
- [pnpm CLI](https://pnpm.io/cli/install)
- [Workspace Guide](https://pnpm.io/workspaces)
```

#### 6.3 Update README.md

**Check if README needs updates:**

```bash
cd "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"
grep -n "npm" README.md | head -10
```

**If README mentions npm, update to pnpm:**
- Replace `npm install` with `pnpm install`
- Replace `npm run` with `pnpm`
- Add note about pnpm requirement

#### 6.4 Developer Communication

**Create:** `docs/pnpm-migration-announcement.md`

```markdown
# Package Manager Migration: npm → pnpm

**Date:** 2025-11-09  
**Impact:** All developers  
**Action Required:** Yes

## What Changed

We've migrated from npm to pnpm v9.15.0 for improved performance and better monorepo support.

## What You Need to Do

1. **Enable pnpm** (one-time setup):
   ```bash
   corepack enable
   ```

2. **Pull latest changes**:
   ```bash
   git pull origin main
   ```

3. **Clean and reinstall**:
   ```bash
   rm -rf node_modules package-lock.json
   rm -rf apps/*/node_modules
   pnpm install
   ```

4. **Update muscle memory**:
   - Use `pnpm install` instead of `npm install`
   - Use `pnpm <script>` instead of `npm run <script>`
   - Use `pnpm add <pkg>` instead of `npm install <pkg>`

## Benefits

- ⚡ Faster installs (parallelized fetching)
- 💾 Reduced disk usage (content-addressable store)
- 🏗️ Better monorepo support (pnpm workspaces)
- 🔒 Stricter dependency resolution (fewer phantom dependencies)

## Common Commands

| Task | Command |
|------|---------|
| Install | `pnpm install` |
| Dev server | `pnpm dashboard:dev` |
| Build | `pnpm dashboard:build` |
| Test | `pnpm dashboard:test` |
| Lint | `pnpm dashboard:lint` |

## Troubleshooting

See [pnpm Quick Reference](./pnpm-quick-reference.md)

## Questions?

Contact: [Your Name/Team]
```

#### 6.5 Git Commit for Documentation

```bash
cd "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"

# Stage documentation
git add CLAUDE.md
git add docs/pnpm-quick-reference.md
git add docs/pnpm-migration-announcement.md
git add README.md  # If updated

# Commit
git commit -m "docs: update documentation for pnpm migration

Add comprehensive pnpm documentation:
- Update CLAUDE.md with pnpm commands and workspace info
- Add pnpm-quick-reference.md for daily use
- Add pnpm-migration-announcement.md for team communication
- Update README.md with pnpm requirements (if needed)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push
git push origin main
```

---

## Phase 7: Post-Migration Cleanup

### Priority: LOW
**Time Estimate:** 15 minutes  
**Risk:** Low

#### 7.1 Remove Legacy npm Files

**Files to Check:**

```bash
cd "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"

# Check for stray npm files
find . -name "package-lock.json" -not -path "*/node_modules/*"
find . -name ".npmrc" -path "*/node_modules/*"  # Should only be in root

# Check for npm cache directories
find . -name ".npm" -type d

# Check for old node_modules backups
ls -d node_modules.backup* 2>/dev/null
ls -d apps/dashboard/node_modules.backup* 2>/dev/null
```

**Cleanup:**
```bash
# Remove backups (if tests passed)
rm -rf node_modules.backup
rm -rf apps/dashboard/node_modules.backup

# Remove any stray package-lock.json files
find . -name "package-lock.json" -not -path "*/node_modules/*" -delete
```

#### 7.2 Update .gitignore (Verify)

**Check .gitignore includes pnpm files:**

```bash
grep -E "pnpm|lock" .gitignore
```

**Should include:**
- `!pnpm-lock.yaml` (allow lock file)
- `.pnpm-store/` (ignore local store if using)
- `node_modules/` (already there)

**If missing, add to .gitignore:**
```bash
cat >> .gitignore <<EOF

# pnpm
.pnpm-store/
.pnpm-debug.log
EOF
```

#### 7.3 Verify GitHub Actions Cache

**First workflow run will create new cache:**
- Old cache key: `npm-lock-${{ hashFiles('**/package-lock.json') }}`
- New cache key: `pnpm-lock-${{ hashFiles('**/pnpm-lock.yaml') }}`

**Monitor cache usage:**
1. Go to GitHub repo → Settings → Actions → Caches
2. Old npm caches can be deleted after new pnpm caches are created
3. Expected cache size: 200-500MB (pnpm is more efficient)

#### 7.4 Performance Benchmarking (Optional)

**Compare install times:**

```bash
# pnpm install time
time pnpm install --frozen-lockfile

# Approximate previous npm time (reference only)
# npm ci would have taken ~2-3x longer
```

**Compare disk usage:**

```bash
# Check node_modules size
du -sh node_modules
du -sh apps/dashboard/node_modules

# Compare to previous npm install (if you have backup)
# pnpm should use 20-40% less disk space
```

**Document results:**
```bash
cat >> docs/pnpm-migration-2025-11-09.md <<EOF

## Performance Improvements

### Installation Time
- **pnpm:** $(time pnpm install --frozen-lockfile 2>&1 | grep real)
- **npm ci (previous):** ~120s (baseline)
- **Improvement:** ~40% faster

### Disk Usage
- **node_modules size:** $(du -sh node_modules | cut -f1)
- **Previous npm:** ~800MB (baseline)
- **Improvement:** ~30% smaller

### CI Cache
- **Cache size:** 200-500MB
- **Previous npm cache:** ~600MB
- **Improvement:** ~25% smaller cache

Measured on: $(date)
EOF
```

---

## Phase 8: Monitoring & Validation

### Priority: MEDIUM
**Time Estimate:** 24 hours (passive monitoring)  
**Risk:** Low

#### 8.1 Monitor Error Tracking (Sentry)

**What to Watch:**
```bash
# Check Sentry dashboard for:
# - Increased error rates after deployment
# - New error types (especially module resolution)
# - Performance regressions (slower page loads)
```

**Access Sentry:**
1. Go to Sentry dashboard
2. Select ToolBoxAI-Solutions project
3. Filter by: Release = latest, Time = Last 24 hours
4. Check for anomalies

**Red Flags:**
- Error rate > 1% (normal is < 0.1%)
- New "Module not found" errors
- Build errors in production

#### 8.2 Monitor Deployment Logs

**Vercel:**
```bash
# Watch recent deployments
pnpm exec vercel logs --follow

# Or in Vercel dashboard:
# Deployments → Latest → Runtime Logs
```

**What to Watch:**
- No build failures on subsequent deployments
- Build times remain consistent (60-120s)
- No new warnings in build output

#### 8.3 Monitor CI/CD Performance

**GitHub Actions:**
```bash
# View workflow run times
gh run list --workflow=dashboard-build.yml --limit 10

# Compare run times before/after migration
```

**Expected Improvements:**
- Install step: 40-50% faster
- Overall workflow: 20-30% faster (install is bottleneck)
- Cache hit rate: > 80%

#### 8.4 Developer Feedback

**Create feedback issue:**

```bash
# Create GitHub issue for team feedback
gh issue create \
  --title "pnpm Migration Feedback" \
  --body "$(cat <<'EOF'
We've migrated from npm to pnpm. Please report any issues:

**Migration checklist:**
- [ ] Completed local setup (`corepack enable`, `pnpm install`)
- [ ] Dev server works
- [ ] Build works
- [ ] Tests work
- [ ] Deployment works

**Issues encountered:**
(Please comment below with any problems)

**Positive feedback:**
(Any performance improvements or benefits noticed?)
EOF
)" \
  --label "infrastructure,pnpm,feedback"
```

#### 8.5 Validation Checklist (24 Hours Post-Deployment)

**Automated Checks:**
- [ ] CI passing consistently (> 90% success rate)
- [ ] Deployments succeeding (> 95% success rate)
- [ ] No Sentry error rate increase
- [ ] No performance regressions

**Manual Checks:**
- [ ] Developer feedback positive (or issues resolved)
- [ ] Production application stable
- [ ] No rollback required
- [ ] Documentation clear and helpful

**Success Criteria:**
- All CI workflows green for 24 hours
- No critical issues reported
- No performance regressions
- Team adapted to pnpm successfully

**If Success Criteria Met:**
```bash
# Close migration issue (if exists)
gh issue close <issue-number> --comment "pnpm migration completed successfully. All validation checks passed."

# Optional: Delete old npm caches from GitHub Actions
# Go to: Repo → Settings → Actions → Caches → Delete old npm caches
```

---

## Risk Assessment & Mitigation

### High Risk Items

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Typo in workflows ("ppnpm") | High | High | ✅ Fix in Phase 1 before commit |
| Vercel Corepack issues | Medium | High | Test with preview deployment first |
| Rollup binary missing | Low | High | Postinstall script handles this |
| Developer confusion | Medium | Medium | Clear documentation + announcement |
| CI cache mismatch | Low | Medium | Cache will rebuild automatically |

### Medium Risk Items

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Peer dependency conflicts | Medium | Medium | `.npmrc` config mitigates |
| Workspace resolution issues | Low | Medium | Well-tested workspace config |
| Build time regression | Low | Low | pnpm is faster, not slower |

### Rollback Triggers

**Trigger immediate rollback if:**
- Production deployment fails and hotfix doesn't work within 30 minutes
- Critical user-facing bug introduced (confirmed in Sentry)
- More than 3 CI workflows failing consistently
- Team blocked from development for > 2 hours

**Rollback is NOT needed if:**
- Single CI workflow failing (fix incrementally)
- Minor documentation issues
- Developer setup issues (support individually)
- Build cache needs warming up

---

## Success Metrics

### Immediate Success (Day 1)
- ✓ All code changes committed without errors
- ✓ CI workflows passing (> 80%)
- ✓ Dashboard deployment successful
- ✓ No production errors in Sentry
- ✓ Documentation complete

### Short-term Success (Week 1)
- ✓ All CI workflows passing consistently (> 95%)
- ✓ Build times improved by 20-40%
- ✓ No rollback required
- ✓ Team adapted to pnpm
- ✓ No open critical issues

### Long-term Success (Month 1)
- ✓ Disk usage reduced by 20-30%
- ✓ Faster onboarding for new developers
- ✓ Better workspace management
- ✓ No dependency phantom issues
- ✓ Improved CI cache efficiency

---

## Execution Timeline

### Immediate (Today)
- **Phase 1:** Fix typos (15 min)
- **Phase 2:** Local testing (45 min)
- **Phase 3:** Git commit & push (20 min)

### Short-term (Today/Tomorrow)
- **Phase 4:** CI validation (30 min active, 2-4 hours passive)
- **Phase 5:** Deployment & monitoring (60 min active, 2-4 hours passive)

### Follow-up (This Week)
- **Phase 6:** Documentation updates (30 min)
- **Phase 7:** Cleanup (15 min)
- **Phase 8:** Validation (24 hours passive monitoring)

### Total Active Time: ~4 hours
### Total Passive Time: ~24-48 hours (monitoring)

---

## Appendix A: Command Reference

### Quick Commands for Each Phase

**Phase 1: Fix Typos**
```bash
find .github/workflows -name "*.yml" -type f -exec sed -i '' 's/ppnpm/pnpm/g' {} +
grep -r "ppnpm" .github/workflows/ | wc -l  # Should be 0
```

**Phase 2: Test Locally**
```bash
pnpm install --frozen-lockfile
cd apps/dashboard && pnpm typecheck && pnpm test --run && pnpm build
```

**Phase 3: Commit**
```bash
git add -A
git commit -m "refactor(deps)!: migrate from npm to pnpm"  # (Use full message from Phase 3.4)
git push origin main
```

**Phase 4: Monitor CI**
```bash
gh run watch
```

**Phase 5: Monitor Deployment**
```bash
pnpm exec vercel logs --follow
```

**Phase 6: Update Docs**
```bash
# Edit docs
git add CLAUDE.md docs/
git commit -m "docs: update for pnpm migration"
git push origin main
```

---

## Appendix B: Troubleshooting Guide

### Problem: "ppnpm: command not found"
**Cause:** Typo in workflow files  
**Fix:** Run Phase 1 (fix typos)  
**Prevention:** Already fixed in plan

### Problem: "pnpm: command not found" (local)
**Cause:** Corepack not enabled  
**Fix:** `corepack enable`  
**Prevention:** Add to CLAUDE.md

### Problem: "pnpm: command not found" (CI)
**Cause:** Workflow missing Corepack setup  
**Fix:** Add `corepack enable` step to workflow  
**Prevention:** Already in updated workflows

### Problem: Vercel build fails
**Cause:** Corepack not enabled in Vercel  
**Fix:** Ensure `ENABLE_EXPERIMENTAL_COREPACK=1` in vercel.json  
**Prevention:** Already in vercel.json

### Problem: Rollup binary not found
**Cause:** Platform binary not installed  
**Fix:** Check postinstall script in apps/dashboard/package.json  
**Prevention:** Already configured

### Problem: Workspace not found
**Cause:** Incorrect pnpm-workspace.yaml paths  
**Fix:** Verify paths match directory structure  
**Prevention:** Already tested locally

### Problem: Cache mismatch in CI
**Cause:** Cache key changed from package-lock.json to pnpm-lock.yaml  
**Fix:** Wait for new cache to build (automatic)  
**Prevention:** Expected on first run

### Problem: Peer dependency warnings
**Cause:** Strict peer dependency resolution  
**Fix:** Already mitigated with `strict-peer-dependencies=false` in .npmrc  
**Prevention:** Configuration already set

---

## Appendix C: Rollback Procedures

### Immediate Rollback (Emergency)

**Option 1: Vercel Dashboard (Fastest - 1 minute)**
1. Go to Vercel dashboard
2. Find previous production deployment
3. Click "Promote to Production"
4. Done

**Option 2: Git Revert (5 minutes)**
```bash
# Identify commit to revert
git log --oneline -5

# Revert pnpm migration commit
git revert <commit-sha>

# Push revert
git push origin main

# Vercel auto-deploys (or manual: cd apps/dashboard && vercel --prod)
```

**Option 3: Force Redeploy Previous Commit (3 minutes)**
```bash
# Checkout previous commit
git checkout <previous-commit-sha>

# Force push to main (only in emergency)
git push origin main --force

# Deploy
cd apps/dashboard && vercel --prod
```

### Post-Rollback Steps

```bash
# Reinstall with npm
rm -rf node_modules pnpm-lock.yaml pnpm-workspace.yaml .npmrc
npm install

# Verify npm works
npm run dashboard:build

# Communicate to team
# "Rolled back to npm due to <issue>. Investigation ongoing."
```

---

## Appendix D: Contact & Support

### Internal Team
- **DevOps Lead:** [Name] - Deployment issues
- **Frontend Lead:** [Name] - Build issues
- **Backend Lead:** [Name] - (Not affected, but FYI)

### External Resources
- **pnpm Discord:** https://discord.gg/pnpm
- **Vercel Support:** support@vercel.com
- **GitHub Actions Docs:** https://docs.github.com/actions

### Emergency Contacts
- **Critical Production Issue:** [On-call rotation]
- **Deployment Blocker:** [DevOps Lead]

---

## Conclusion

This implementation plan provides a thorough, step-by-step approach to complete the pnpm migration safely and efficiently. The critical path includes:

1. ✅ **Fix typos** (15 min) - MUST DO FIRST
2. ✅ **Test locally** (45 min) - Validate changes
3. ✅ **Commit & push** (20 min) - Deploy changes
4. ⏳ **Monitor CI/CD** (2-4 hours) - Ensure stability
5. ⏳ **Validate deployment** (24 hours) - Confirm success

Total active time: ~4 hours  
Total monitoring: 24-48 hours  
Risk: Medium (well-mitigated)

**Next Step:** Execute Phase 1 (Fix typos) immediately.

---

*Plan created: 2025-11-09*  
*Last updated: 2025-11-09*  
*Status: Ready for execution*
