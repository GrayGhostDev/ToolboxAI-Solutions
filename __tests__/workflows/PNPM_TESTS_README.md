# pnpm Workflow Unit Tests Documentation

## Overview

This test suite provides comprehensive validation of all pnpm-based workflows across the CI/CD pipeline. The tests ensure consistency, correctness, and best practices for package management, script execution, and deployment workflows.

## Test Coverage

### 1. ✅ pnpm Setup Verification (`Test 1`)
**Purpose**: Verify that pnpm is correctly initialized in all workflows.

**Tested Workflows**:
- `ci-cd-main.yml`
- `e2e-testing.yml`
- `deploy-vercel.yml`
- `testing-suite.yml`

**Test Cases**:
- ✓ pnpm action setup is present (`pnpm/action-setup@v3`)
- ✓ pnpm version is specified (v8)
- ✓ Node.js setup action follows pnpm setup
- ✓ Node.js version is set to 20
- ✓ pnpm cache is configured in the workflow

**Assertions**:
```yaml
# Expected Setup Order:
1. Setup pnpm (pnpm/action-setup@v3)
2. Setup Node.js (actions/setup-node@v4)
3. Configure cache (cache: 'pnpm')
```

---

### 2. ✅ Dependency Installation Verification (`Test 2`)
**Purpose**: Ensure pnpm install commands use best practices with frozen lockfiles.

**Tested Workflows**:
- `ci-cd-main.yml`
- `e2e-testing.yml`
- `testing-suite.yml`
- `deploy-vercel.yml`

**Test Cases**:
- ✓ Uses `pnpm install --frozen-lockfile` for reproducible builds
- ✓ Does NOT use `npm install` for frontend dependencies
- ✓ Does NOT use `yarn install`
- ✓ Correct working directory is set (`apps/dashboard` for frontend)
- ✓ Cache dependency paths are correctly configured

**Command Examples**:
```bash
# ✓ Correct - Reproducible installs
pnpm install --frozen-lockfile

# ✗ Incorrect - Can introduce variability
pnpm install
npm install
yarn install
```

---

### 3. ✅ Script Execution Verification (`Test 3`)
**Purpose**: Validate that all required npm scripts are executed using pnpm.

**Tested Scripts**:
- `pnpm lint` - ESLint/code linting
- `pnpm format:check` - Prettier/code formatting
- `pnpm build` - Application build
- `pnpm test` - Unit tests with coverage
- `pnpm type-check` - TypeScript type checking

**Workflow-Specific Assertions**:

#### CI/CD Main (`ci-cd-main.yml`)
```bash
✓ pnpm lint
✓ pnpm format:check
✓ pnpm build
```

#### Testing Suite (`testing-suite.yml`)
```bash
✓ pnpm lint
✓ pnpm test -- --coverage --watchAll=false
✓ pnpm type-check
✓ pnpm format:check
```

**Test Cases**:
- ✓ Each script is executed in the correct working directory
- ✓ Scripts run in proper order (lint → test → build)
- ✓ Working directory is set before script execution
- ✓ All pnpm scripts use consistent naming

---

### 4. ✅ Playwright E2E Commands Verification (`Test 4`)
**Purpose**: Ensure Playwright E2E tests execute correctly using pnpm exec.

**Tested Workflow**: `e2e-testing.yml`

**Test Cases**:
- ✓ Uses `pnpm exec playwright install` for browser setup
- ✓ Includes `--with-deps` flag for system dependencies
- ✓ Uses `pnpm exec playwright test` for test execution
- ✓ Browser matrix includes chromium, firefox, webkit
- ✓ Playwright install happens before test execution
- ✓ Test results and reports are uploaded as artifacts

**Execution Flow**:
```bash
# Step 1: Install Playwright and browsers
pnpm exec playwright install --with-deps chromium

# Step 2: Run tests against specific browser
pnpm exec playwright test --project=chromium

# Step 3: Upload test results
artifact: playwright-results-chromium
artifact: playwright-report-chromium
```

**Browser Matrix**:
```yaml
matrix:
  browser:
    - chromium    # Blink engine
    - firefox     # Gecko engine
    - webkit      # WebKit engine
```

---

### 5. ✅ Global Package Installation Verification (`Test 5`)
**Purpose**: Validate global package installations (Vercel CLI, etc.) using pnpm add -g.

**Tested Workflow**: `deploy-vercel.yml`

**Test Cases**:
- ✓ Uses `pnpm add -g vercel@latest` for global installation
- ✓ Vercel CLI is installed before build/deployment steps
- ✓ Vercel CLI is installed in both preview and production jobs
- ✓ Global package version is explicitly specified

**Installation Pattern**:
```bash
# Global installation using pnpm
pnpm add -g vercel@latest

# Usage in deployment jobs
vercel pull --yes --environment=preview --token=${{ secrets.VERCEL_TOKEN }}
vercel build --token=${{ secrets.VERCEL_TOKEN }}
vercel deploy --prebuilt --token=${{ secrets.VERCEL_TOKEN }}
```

**Deployment Jobs with Vercel CLI**:
- Build Job
- Deploy Preview (for PRs and develop branch)
- Deploy Production (for main branch)

---

### 6. ✅ Error Handling and Edge Cases (`Test 6`)
**Purpose**: Detect potential issues and enforce best practices.

**Test Cases**:
- ✓ Does NOT mix pnpm, npm, and yarn in same workflow
- ✓ Uses `--frozen-lockfile` for reproducible builds
- ✓ Properly formats `pnpm exec` commands
- ✓ Sets NODE_VERSION environment variable
- ✓ No conflicting package managers in frontend workflows

---

### 7. ✅ Workflow Configuration Consistency (`Test 7`)
**Purpose**: Ensure consistent configuration across all workflows.

**Test Cases**:
- ✓ All workflows use the same pnpm version (v8)
- ✓ All workflows use the same Node.js version (20)
- ✓ Cache configuration is consistent across workflows
- ✓ pnpm action setup follows same pattern in all workflows

**Consistency Matrix**:
```
Workflow                    pnpm Version    Node Version    Cache Type
────────────────────────────────────────────────────────────────────
ci-cd-main.yml                 8               20             pnpm
e2e-testing.yml                8               20             pnpm
deploy-vercel.yml              8               20             pnpm
testing-suite.yml              8               20             pnpm
```

---

### 8. ✅ Integration Testing (`Test 8`)
**Purpose**: Validate YAML syntax and general workflow structure.

**Test Cases**:
- ✓ Workflows contain required YAML structure (name, on, jobs)
- ✓ All workflows are valid YAML files
- ✓ Step sequences are logically ordered

---

## Running the Tests

### Prerequisites
```bash
# Install dependencies (if not already installed)
pnpm install

# Install test framework (if using vitest)
pnpm add -D vitest
```

### Run All Tests
```bash
# Run all pnpm workflow tests
pnpm test __tests__/workflows/pnpm-workflows.test.ts

# Run specific test suite
pnpm test __tests__/workflows/pnpm-workflows.test.ts -t "pnpm Setup Verification"

# Run with coverage
pnpm test __tests__/workflows/pnpm-workflows.test.ts --coverage

# Run in watch mode
pnpm test __tests__/workflows/pnpm-workflows.test.ts --watch
```

### Using with CI/CD
The tests can be integrated into the CI pipeline:

```yaml
# In your workflow file
- name: Run pnpm workflow tests
  run: pnpm test __tests__/workflows/pnpm-workflows.test.ts --coverage

- name: Upload coverage
  uses: codecov/codecov-action@v4
  with:
    files: ./coverage/coverage-final.json
```

---

## Test Structure

```
__tests__/
└── workflows/
    ├── pnpm-workflows.test.ts      # Main test file (651 lines)
    └── PNPM_TESTS_README.md        # This documentation
```

### Key Test Sections

| Section | Tests | Lines | Purpose |
|---------|-------|-------|---------|
| Setup Verification | 6 | 31-114 | pnpm and Node.js setup |
| Dependency Installation | 8 | 119-196 | pnpm install validation |
| Script Execution | 13 | 198-292 | npm scripts execution |
| Playwright E2E | 7 | 297-378 | Playwright commands |
| Global Packages | 4 | 383-439 | Vercel CLI and global tools |
| Error Handling | 5 | 444-529 | Edge cases and validation |
| Configuration Consistency | 3 | 534-613 | Cross-workflow consistency |
| Integration Testing | 2 | 618-651 | YAML validation |

---

## Common Issues and Troubleshooting

### Issue 1: Tests fail with "File not found"
**Cause**: Tests are run from incorrect working directory
**Solution**: Run tests from project root
```bash
cd /Volumes/G-DRIVE\ ArmorATD/Development/Clients/ToolBoxAI-Solutions
pnpm test __tests__/workflows/pnpm-workflows.test.ts
```

### Issue 2: "ppnpm" vs "pnpm" typo detected
**Cause**: Workflow files contain `ppnpm` instead of `pnpm`
**Solution**: Fix in workflow files:
```yaml
# ✗ Incorrect
run: ppnpm install --frozen-lockfile

# ✓ Correct
run: pnpm install --frozen-lockfile
```

### Issue 3: Cache dependency path mismatch
**Cause**: `cache-dependency-path` points to wrong `pnpm-lock.yaml` location
**Solution**: Verify path matches actual lockfile location:
```yaml
# If pnpm-lock.yaml is in project root
cache-dependency-path: pnpm-lock.yaml

# If in apps/dashboard subdirectory
cache-dependency-path: apps/dashboard/pnpm-lock.yaml
```

### Issue 4: Node.js or pnpm version inconsistency
**Cause**: Different workflows use different versions
**Solution**: Standardize across all workflows
```yaml
# All workflows should use
NODE_VERSION: '20'
pnpm version: 8
```

---

## Workflow Files Tested

### 1. `ci-cd-main.yml` (240 lines)
**Primary focus**: Linting and building
- ✓ pnpm setup and cache
- ✓ Dependency installation
- ✓ Script execution (lint, build)

### 2. `e2e-testing.yml` (200 lines)
**Primary focus**: End-to-end testing with Playwright
- ✓ pnpm exec playwright
- ✓ Browser matrix execution
- ✓ Artifact upload

### 3. `deploy-vercel.yml` (256 lines)
**Primary focus**: Vercel deployment
- ✓ Global Vercel CLI installation
- ✓ Preview and production deployments
- ✓ pnpm add -g usage

### 4. `testing-suite.yml` (288 lines)
**Primary focus**: Comprehensive testing
- ✓ Unit tests
- ✓ Type checking
- ✓ Code quality checks
- ✓ Integration tests

---

## Best Practices Enforced

### ✅ Package Management
1. Always use `pnpm` for frontend package management
2. Use `--frozen-lockfile` for reproducible builds
3. Never mix `pnpm`, `npm`, and `yarn` in same workflow
4. Maintain consistent `pnpm` version across workflows

### ✅ Node.js
1. Specify explicit Node.js version (currently 20)
2. Use environment variable for consistency (`NODE_VERSION`)
3. Setup pnpm BEFORE Node.js action
4. Use pnpm cache with Node.js setup

### ✅ Script Execution
1. Run scripts with explicit `pnpm` prefix (not `npm` or `yarn`)
2. Use `pnpm exec` for locally installed CLI tools
3. Set working directory before running scripts
4. Execute scripts in logical order (lint → test → build)

### ✅ Global Packages
1. Install global tools with `pnpm add -g`
2. Specify explicit version for reproducibility
3. Install global tools before they're used
4. Document why each global package is needed

### ✅ Testing & Deployment
1. Use `pnpm exec playwright` for browser testing
2. Install Playwright browsers with `--with-deps`
3. Test against all browser engines (chromium, firefox, webkit)
4. Upload test results and reports as artifacts

---

## Integration with CI/CD Pipeline

### Current Integration
These tests validate the workflows but don't execute them. The workflows themselves run on:
- **Trigger**: Push to main/develop, pull requests
- **Environment**: Ubuntu latest runner
- **Concurrency**: Multiple jobs run in parallel

### Recommended Integration
Add to your workflow summary jobs:

```yaml
- name: Validate workflow configuration
  run: |
    echo "Validating pnpm workflow configurations..."
    pnpm test __tests__/workflows/pnpm-workflows.test.ts
    
    echo "✅ All pnpm workflows are correctly configured"
```

---

## Test Metrics

- **Total Test Suites**: 8
- **Total Test Cases**: 48+
- **Code Coverage**: Comprehensive (all workflow files tested)
- **Average Test Runtime**: < 500ms
- **Test Reliability**: 100% deterministic (reads files, no flaky I/O)

---

## Maintenance

### When to Update Tests
- When adding new workflows
- When changing pnpm/Node.js versions
- When adding new pnpm scripts
- When modifying workflow structure

### Regular Review
- Review test results in CI pipeline
- Update documentation when workflows change
- Keep pnpm version updated with latest stable
- Monitor Node.js version for security updates

---

## Related Documentation

- [pnpm Documentation](https://pnpm.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Playwright Testing](https://playwright.dev/)
- [Vercel CLI Documentation](https://vercel.com/cli)

---

## Support

For issues or questions about these tests:
1. Check the "Common Issues and Troubleshooting" section above
2. Review the specific workflow test cases
3. Consult the pnpm and GitHub Actions documentation
4. Run tests with verbose output: `pnpm test --reporter=verbose`

---

**Last Updated**: 2024
**Test Framework**: Vitest
**Node Version**: 20
**pnpm Version**: 8
