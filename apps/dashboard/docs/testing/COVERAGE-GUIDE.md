# Code Coverage Guide - 2025 Standards

**Target**: >80% coverage for all metrics (lines, branches, functions, statements)

## Quick Start

### Run Coverage

```bash
# Generate coverage report
npm run test:coverage

# Watch mode with coverage
npm run test:coverage:watch

# Interactive UI with coverage
npm run test:coverage:ui

# Generate and open HTML report
npm run test:coverage:report
```

### View Reports

After running coverage, reports are generated in multiple formats:

- **HTML Report**: `coverage/index.html` (interactive, best for exploration)
- **Terminal**: Real-time summary in console
- **JSON**: `coverage/coverage-final.json` (for CI/CD)
- **LCOV**: `coverage/lcov.info` (for Codecov, Coveralls)
- **Cobertura**: `coverage/cobertura-coverage.xml` (for Jenkins, Azure)

## Coverage Metrics

### What Each Metric Means

#### **Lines Coverage (>80% required)**
- Percentage of code lines executed during tests
- **Good**: High line coverage means most code paths are tested
- **Limitation**: Can be misleading if tests don't check results

#### **Branches Coverage (>80% required)**
- Percentage of conditional branches tested (if/else, switch, ternary)
- **Good**: Ensures both true and false paths are tested
- **Critical**: Often the most important metric for quality

**Example**:
```typescript
// 50% branch coverage - only tests true path
if (user.isAdmin) {
  return adminDashboard();
} else {
  return userDashboard(); // ❌ Not tested
}

// 100% branch coverage - tests both paths
it('shows admin dashboard for admins', () => {
  const user = { isAdmin: true };
  expect(getDashboard(user)).toBe('admin');
});

it('shows user dashboard for non-admins', () => {
  const user = { isAdmin: false };
  expect(getDashboard(user)).toBe('user');
});
```

#### **Functions Coverage (>80% required)**
- Percentage of functions called at least once
- **Good**: Identifies unused/dead code
- **Limitation**: Calling a function doesn't mean it's well-tested

#### **Statements Coverage (>80% required)**
- Percentage of statements executed
- **Good**: Fine-grained metric for code execution
- **Similar to**: Line coverage but counts statements

## Configuration

### Coverage Thresholds (vite.config.js)

```javascript
coverage: {
  thresholds: {
    branches: 80,    // 80% minimum
    functions: 80,   // 80% minimum
    lines: 80,       // 80% minimum
    statements: 80,  // 80% minimum
    perFile: true    // Enforce per-file (strict)
  }
}
```

### Files Excluded from Coverage

The following are automatically excluded:

- **Test files**: `*.test.ts`, `*.spec.tsx`, `__tests__/*`
- **Type definitions**: `*.d.ts`, `types/*`
- **Config files**: `*.config.*`, `.eslintrc.*`
- **Mock data**: `**/mockData.*`, `**/fixtures/**`
- **Storybook**: `*.stories.*`, `.storybook/**`
- **Entry points**: `main.tsx`, `App.tsx` (tested via integration)
- **Constants**: Static configuration files

## Understanding Coverage Reports

### HTML Report (Most Useful)

Open `coverage/index.html` for an interactive report showing:

1. **Overall Summary**
   - Total coverage percentages
   - Files below threshold highlighted in red

2. **File Browser**
   - Click any file to see line-by-line coverage
   - Red lines: Not covered
   - Yellow lines: Partially covered (branches)
   - Green lines: Fully covered

3. **Drill Down**
   - Navigate through directories
   - See exactly which branches are missing

### Terminal Report

```
-----------|---------|----------|---------|---------|-------------------
File       | % Stmts | % Branch | % Funcs | % Lines | Uncovered Line #s
-----------|---------|----------|---------|---------|-------------------
All files  |   85.23 |    78.45 |   82.11 |   85.23 |
 hooks     |   92.50 |    87.50 |   90.00 |   92.50 |
  useAuth  |   95.00 |    90.00 |  100.00 |   95.00 | 23,45
 components|   78.20 |    65.30 |   75.00 |   78.20 |
  Button   |   60.00 |    50.00 |   66.67 |   60.00 | 15-20,34-38
-----------|---------|----------|---------|---------|-------------------
```

**Reading the Report**:
- **Red** (< 80%): Needs more tests
- **Yellow** (80-95%): Acceptable but could improve
- **Green** (> 95%): Well tested
- **Uncovered Line #s**: Exact lines missing coverage

## Improving Coverage

### Strategy 1: Test Happy Path + Error Cases

```typescript
// ✅ Good - tests both success and failure
describe('fetchUserData', () => {
  it('returns user data on success', async () => {
    mockAPI.get.mockResolvedValue({ data: { name: 'John' } });
    const result = await fetchUserData(1);
    expect(result).toEqual({ name: 'John' });
  });

  it('throws error on failure', async () => {
    mockAPI.get.mockRejectedValue(new Error('Network error'));
    await expect(fetchUserData(1)).rejects.toThrow('Network error');
  });
});
```

### Strategy 2: Test All Conditional Branches

```typescript
// Function with multiple branches
function getUserStatus(user) {
  if (!user) return 'guest';
  if (user.isAdmin) return 'admin';
  if (user.isPremium) return 'premium';
  return 'standard';
}

// ✅ Tests all 4 branches
it('returns guest for no user', () => {
  expect(getUserStatus(null)).toBe('guest');
});

it('returns admin for admin user', () => {
  expect(getUserStatus({ isAdmin: true })).toBe('admin');
});

it('returns premium for premium user', () => {
  expect(getUserStatus({ isPremium: true })).toBe('premium');
});

it('returns standard for regular user', () => {
  expect(getUserStatus({})).toBe('standard');
});
```

### Strategy 3: Test Edge Cases

```typescript
describe('calculateDiscount', () => {
  // Happy path
  it('calculates 10% discount for regular items', () => {
    expect(calculateDiscount(100, 'regular')).toBe(90);
  });

  // Edge cases
  it('handles zero price', () => {
    expect(calculateDiscount(0, 'regular')).toBe(0);
  });

  it('handles negative price', () => {
    expect(() => calculateDiscount(-10, 'regular')).toThrow();
  });

  it('handles unknown discount type', () => {
    expect(calculateDiscount(100, 'unknown')).toBe(100);
  });
});
```

## Common Coverage Issues

### Issue 1: Async Code Not Awaited

```typescript
// ❌ Wrong - async code not covered
it('saves user', () => {
  saveUser(userData); // Promise not awaited
  expect(mockAPI.post).toHaveBeenCalled(); // Fails intermittently
});

// ✅ Correct - properly awaited
it('saves user', async () => {
  await saveUser(userData);
  expect(mockAPI.post).toHaveBeenCalled();
});
```

### Issue 2: Component State Not Tested

```typescript
// ❌ Wrong - only tests initial render
it('renders button', () => {
  render(<Counter />);
  expect(screen.getByRole('button')).toBeInTheDocument();
});

// ✅ Correct - tests state changes
it('increments counter on click', async () => {
  const user = userEvent.setup();
  render(<Counter />);
  const button = screen.getByRole('button');

  expect(button).toHaveTextContent('Count: 0');
  await user.click(button);
  expect(button).toHaveTextContent('Count: 1');
});
```

### Issue 3: Error Handling Not Tested

```typescript
function processData(data) {
  try {
    return expensiveOperation(data);
  } catch (error) {
    // ❌ This catch block often not covered
    logError(error);
    return null;
  }
}

// ✅ Test both success and error paths
it('returns processed data on success', () => {
  expect(processData(validData)).toBe(expectedResult);
});

it('handles errors gracefully', () => {
  vi.spyOn(console, 'error').mockImplementation(() => {});
  expect(processData(invalidData)).toBeNull();
});
```

## Coverage Best Practices

### DO ✅

- **Aim for >80% across all metrics** (branches most important)
- **Test behavior, not implementation** (coverage follows)
- **Focus on critical paths first** (auth, payments, data flow)
- **Review HTML report** to find missing branches
- **Write tests before fixing coverage** (TDD approach)
- **Test edge cases** (null, undefined, empty, negative)
- **Test error handling** (try/catch, Promise rejections)

### DON'T ❌

- **Don't write tests just for coverage** (test behavior)
- **Don't test trivial code** (getters, constants)
- **Don't aim for 100% everywhere** (diminishing returns)
- **Don't ignore low branch coverage** (most critical metric)
- **Don't test implementation details** (internal state)
- **Don't skip error cases** (often forgotten)

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests with Coverage

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'

      - run: npm ci
      - run: npm run test:coverage

      # Upload to Codecov
      - uses: codecov/codecov-action@v4
        with:
          files: ./coverage/lcov.info
          fail_ci_if_error: true

      # Fail if coverage below 80%
      - run: |
          if ! grep -q "All files.*80" coverage/coverage-summary.json; then
            echo "Coverage below 80%"
            exit 1
          fi
```

### Coverage Badges

Add to README.md:

```markdown
[![Coverage](https://img.shields.io/codecov/c/github/yourusername/yourrepo)](https://codecov.io/gh/yourusername/yourrepo)
```

## Troubleshooting

### Coverage Files Not Generated

**Problem**: Running `npm run test:coverage` doesn't create coverage/

**Solution**: Ensure `COVERAGE=true` environment variable is set

```bash
# Correct
COVERAGE=true npm run test:coverage

# Or use the npm script (already sets COVERAGE=true)
npm run test:coverage
```

### Coverage Thresholds Failing

**Problem**: "Coverage for X (75%) does not meet threshold (80%)"

**Solution**:

1. Check which files are below threshold:
   ```bash
   npm run test:coverage
   # Look for red files in output
   ```

2. Open HTML report:
   ```bash
   npm run test:coverage:report
   ```

3. Click on red files to see uncovered lines

4. Write tests for uncovered branches

### Coverage Higher Than Expected

**Problem**: Coverage shows 90% but you know code isn't well tested

**Solution**: Check branch coverage specifically:

```bash
# Branch coverage is most important
# Check HTML report for yellow lines (partial branch coverage)
npm run test:coverage:report
```

## Advanced Topics

### Per-File Thresholds

Enforce stricter thresholds for critical files:

```javascript
// vite.config.js
coverage: {
  thresholds: {
    // Global 80%
    branches: 80,
    functions: 80,
    lines: 80,
    statements: 80,

    // Critical files require 100%
    'src/services/auth.ts': {
      branches: 100,
      functions: 100,
      lines: 100,
      statements: 100
    }
  }
}
```

### Ignore Specific Lines

```typescript
// Use istanbul ignore comments (sparingly!)
function debugHelper() {
  /* istanbul ignore next */
  if (process.env.NODE_ENV === 'development') {
    console.log('Debug info');
  }
}
```

### Coverage Watermarks

Visual indicators in HTML report:

```javascript
coverage: {
  watermarks: {
    statements: [80, 95], // Red < 80%, Yellow 80-95%, Green > 95%
    branches: [80, 95],
    functions: [80, 95],
    lines: [80, 95]
  }
}
```

## Summary

### Minimum Requirements (2025 Standards)

- ✅ **>80% line coverage**
- ✅ **>80% branch coverage** (most important!)
- ✅ **>80% function coverage**
- ✅ **>80% statement coverage**
- ✅ **HTML reports generated**
- ✅ **LCOV for CI/CD**
- ✅ **Per-file enforcement**

### Quick Commands

```bash
npm run test:coverage          # Generate coverage
npm run test:coverage:watch    # Watch mode
npm run test:coverage:ui       # Interactive UI
npm run test:coverage:report   # Generate + open HTML
```

### Next Steps

1. Run `npm run test:coverage` to see current state
2. Open HTML report to find gaps
3. Write tests for uncovered branches
4. Focus on critical paths first
5. Maintain >80% as you add new code

---

**Last Updated**: 2025-10-01
**Vitest Version**: 3.2.4
**Coverage Provider**: V8
**Target**: >80% all metrics
