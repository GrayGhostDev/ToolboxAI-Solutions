# Bug Fixes Worktree Tasks
**Branch**: fix/ci-cd-test-failures
**Ports**: Backend(8012), Dashboard(5183), MCP(9880), Coordinator(8891)

## 🚨 CRITICAL: 2025 Implementation Standards

**MANDATORY**: Read and follow `2025-IMPLEMENTATION-STANDARDS.md` when fixing bugs!

**Requirements**:
- ✅ Fix using 2025 modern patterns
- ✅ Update tests to Vitest 3.2.4 / Pytest async
- ✅ Replace deprecated code during fixes
- ✅ Auto-accept enabled for corrections
- ❌ NO band-aid fixes with legacy code

## Primary Objectives
1. **CI/CD Pipeline Fixes**
   - Resolve test failures in GitHub Actions
   - Fix TeamCity build issues
   - Stabilize deployment pipeline

2. **Test Suite Improvements**
   - Fix failing unit tests
   - Update integration tests
   - Add missing test coverage

3. **Code Quality**
   - Fix linting errors
   - Resolve TypeScript type errors
   - Address security vulnerabilities

## Current Tasks
- [ ] Analyze GitHub Actions workflow failures
- [ ] Review TeamCity build logs
- [ ] Fix failing unit tests in `__tests__/`
- [ ] Update test configuration files
- [ ] Resolve dependency conflicts
- [ ] Fix ESLint and Prettier errors
- [ ] Address security vulnerabilities (npm audit)
- [ ] Update CI/CD documentation

## Known Issues
1. **GitHub Actions Failures**
   - Test timeout issues
   - Environment variable configuration
   - Docker build failures

2. **TeamCity Build Issues**
   - Build agent compatibility
   - Resource allocation
   - Artifact publishing

3. **Test Failures**
   - Database connection timeouts
   - Mock service failures
   - Async timing issues

## File Locations
- CI/CD: `.github/workflows/`, `.teamcity/`
- Tests: `ToolboxAI-Solutions/__tests__/`
- Config: `jest.config.js`, `.eslintrc.js`

## Commands
```bash
cd ToolboxAI-Solutions
npm run test              # Run all tests
npm run test:ci           # Run CI test suite
npm run lint:fix          # Auto-fix linting issues
npm run type-check        # TypeScript validation
npm audit fix             # Fix security issues
npm run test:debug        # Debug failing tests
```
