# Visual Regression Testing Guide

## Overview

This guide covers visual regression testing in the ToolboxAI Dashboard using Playwright's built-in visual comparison capabilities. Visual regression testing ensures that UI changes don't inadvertently break the visual appearance of the application.

**Last Updated**: 2025-10-10
**Playwright Version**: 1.55.0
**Test Coverage**: 56 visual regression tests

---

## Table of Contents

- [Quick Start](#quick-start)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Utilities](#utilities)
- [Best Practices](#best-practices)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Run Visual Tests

```bash
# Run all visual regression tests
npm run test:e2e:visual

# Run with Playwright UI (recommended for development)
npm run test:e2e:ui

# Run only visual tests in Chromium
npm run test:e2e:visual:chromium

# Debug visual tests
npm run test:e2e:visual:debug
```

### Update Snapshots

When you've made intentional visual changes:

```bash
# Update all visual snapshots
npm run test:e2e:visual:update

# Update snapshots for specific test
npx playwright test auth.visual.spec.ts --update-snapshots
```

---

## Test Structure

### Directory Layout

```
apps/dashboard/
├── e2e/
│   ├── visual/                  # Visual regression tests
│   │   ├── auth.visual.spec.ts           # Authentication pages (7 tests)
│   │   ├── dashboard.visual.spec.ts      # Dashboard/Home (11 tests)
│   │   ├── classes.visual.spec.ts        # Classes pages (10 tests)
│   │   ├── content.visual.spec.ts        # Content pages (10 tests)
│   │   ├── quizzes.visual.spec.ts        # Quiz pages (10 tests)
│   │   └── reports.visual.spec.ts        # Reports/Analytics (8 tests)
│   ├── utils/
│   │   └── visual-testing.ts    # Visual testing utilities
│   └── snapshots/               # Baseline screenshots (auto-generated)
└── playwright.config.ts         # Enhanced with visual regression config
```

### Test File Naming Convention

- Visual regression test files end with `.visual.spec.ts`
- Snapshot files are stored in `e2e/snapshots/`
- Follow naming pattern: `[feature]-[description]-[state].png`

---

## Running Tests

### Development Workflow

**1. First Time Running Tests**

```bash
# Generate baseline snapshots
npm run test:e2e:visual

# Review snapshots in e2e/snapshots/
```

**2. After UI Changes**

```bash
# Run tests to detect visual changes
npm run test:e2e:visual

# If changes are intentional, update snapshots
npm run test:e2e:visual:update
```

**3. Review Test Report**

```bash
# Open HTML report
npx playwright show-report
```

### Command Reference

| Command | Description |
|---------|-------------|
| `npm run test:e2e:visual` | Run all visual regression tests |
| `npm run test:e2e:visual:update` | Update all snapshots (use after intentional changes) |
| `npm run test:e2e:visual:chromium` | Run visual tests in Chromium only |
| `npm run test:e2e:visual:debug` | Run tests in debug mode |
| `npx playwright test --ui` | Open Playwright UI for interactive testing |
| `npx playwright show-report` | Open test report in browser |

---

## Utilities

### Available Helper Functions

Located in `e2e/utils/visual-testing.ts`:

#### Page-Level Snapshots

```typescript
import { captureFullPageSnapshot, preparePageForVisualTesting } from '../utils/visual-testing';

test('Example test', async ({ page }) => {
  await preparePageForVisualTesting(page);
  await page.goto('/some-page');

  await captureFullPageSnapshot(page, 'page-name', {
    maxDiffPixels: 100,
    waitForTimeout: 1000,
  });
});
```

#### Component-Level Snapshots

```typescript
import { captureComponentSnapshot } from '../utils/visual-testing';

test('Component test', async ({ page }) => {
  const component = page.locator('[data-testid="my-component"]');

  await captureComponentSnapshot(component, 'component-name', {
    threshold: 0.2,
  });
});
```

#### Responsive Testing

```typescript
import { testResponsiveSnapshots, STANDARD_VIEWPORTS } from '../utils/visual-testing';

test('Responsive test', async ({ page }) => {
  await page.goto('/page');

  await testResponsiveSnapshots(page, 'page-responsive', [
    STANDARD_VIEWPORTS.mobile,
    STANDARD_VIEWPORTS.tablet,
    STANDARD_VIEWPORTS.desktop,
  ]);
});
```

#### Masking Dynamic Content

```typescript
import { maskDynamicElements } from '../utils/visual-testing';

test('Test with masked content', async ({ page }) => {
  const masks = await maskDynamicElements(page);

  await captureFullPageSnapshot(page, 'page-with-masks', {
    mask: masks,  // Automatically masks timestamps, dates, UUIDs, etc.
  });
});
```

### Standard Viewports

```typescript
STANDARD_VIEWPORTS = {
  mobile: { width: 375, height: 667, name: 'mobile' },
  mobileWide: { width: 428, height: 926, name: 'mobile-wide' },
  tablet: { width: 768, height: 1024, name: 'tablet' },
  tabletWide: { width: 1024, height: 768, name: 'tablet-wide' },
  desktop: { width: 1280, height: 720, name: 'desktop' },
  desktopWide: { width: 1920, height: 1080, name: 'desktop-wide' },
  desktop4K: { width: 3840, height: 2160, name: 'desktop-4k' },
};
```

---

## Best Practices

### 1. Preparation

```typescript
test.beforeEach(async ({ page }) => {
  // Always prepare page for consistent testing
  await preparePageForVisualTesting(page);
});
```

This function:
- Disables CSS animations
- Hides carets/cursors
- Pauses videos
- Waits for fonts and images to load

### 2. Mask Dynamic Content

Always mask content that changes frequently:

```typescript
const masks = await maskDynamicElements(page);

await captureFullPageSnapshot(page, 'snapshot-name', {
  mask: masks,  // Masks timestamps, UUIDs, dates, etc.
});
```

### 3. Wait for Stability

Allow time for content to load and animations to complete:

```typescript
await page.waitForLoadState('networkidle');
await page.waitForTimeout(500);  // Let layout stabilize

await captureFullPageSnapshot(page, 'snapshot-name');
```

### 4. Consistent Naming

Follow a consistent naming pattern:

```typescript
// Good naming
'auth-login-initial'
'dashboard-home-with-data'
'classes-list-empty-state'
'quizzes-take-question-screen'

// Bad naming
'test1'
'screenshot'
'page'
```

### 5. Component Testing

Test components in isolation when possible:

```typescript
test('Specific component', async ({ page }) => {
  const component = page.locator('[data-testid="component-name"]');

  if (await component.isVisible()) {
    await captureComponentSnapshot(component, 'component-name');
  }
});
```

### 6. Responsive Testing

Test critical pages across multiple viewports:

```typescript
test('Responsive layout', async ({ page }) => {
  await testResponsiveSnapshots(page, 'page-name', [
    STANDARD_VIEWPORTS.mobile,
    STANDARD_VIEWPORTS.tablet,
    STANDARD_VIEWPORTS.desktop,
  ]);
});
```

### 7. Color Schemes

Test both light and dark themes:

```typescript
import { testColorSchemeSnapshots } from '../utils/visual-testing';

test('Theme test', async ({ page }) => {
  await testColorSchemeSnapshots(page, 'page-name', ['light', 'dark']);
});
```

---

## Configuration

### Playwright Config

Visual regression settings in `playwright.config.ts`:

```typescript
expect: {
  toHaveScreenshot: {
    maxDiffPixels: 100,           // Max pixel difference
    maxDiffPixelRatio: 0.01,      // Max ratio (0-1)
    threshold: 0.2,               // Pixel comparison threshold
    animations: 'disabled',       // Disable animations
    caret: 'hide',                // Hide text carets
    scale: 'css',                 // CSS scale factor
  },
}
```

### Visual Regression Project

Dedicated project for visual tests:

```typescript
{
  name: 'visual-regression',
  use: {
    ...devices['Desktop Chrome'],
    viewport: { width: 1280, height: 720 },
    deviceScaleFactor: 1,
    colorScheme: 'light',
  },
  testMatch: /.*\.visual\.spec\.ts/,
  retries: 0,  // No retries for visual tests
}
```

---

## CI/CD Integration

### GitHub Actions

Visual tests run automatically in CI:

```yaml
# .github/workflows/e2e-tests.yml
- name: Run Visual Regression Tests
  run: npm run test:e2e:visual

- name: Upload test results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: playwright-report/
    retention-days: 30

- name: Upload visual diffs
  if: failure()
  uses: actions/upload-artifact@v3
  with:
    name: visual-diffs
    path: test-results/
    retention-days: 7
```

### Snapshot Storage

- **Baseline snapshots** are stored in Git at `e2e/snapshots/`
- **Test results** are stored in `test-results/` (gitignored)
- **Failed tests** generate comparison images showing differences

---

## Troubleshooting

### Common Issues

**1. Test Fails with "Screenshot comparison failed"**

```bash
# View the diff in the HTML report
npx playwright show-report

# If change is intentional, update snapshot
npx playwright test <test-name> --update-snapshots
```

**2. Inconsistent Results Between Local and CI**

- Ensure same Playwright version
- Check viewport settings match
- Verify font rendering (install same fonts in CI)
- Use Docker for consistent environment

**3. Too Many Pixel Differences**

Adjust threshold in test:

```typescript
await captureFullPageSnapshot(page, 'name', {
  maxDiffPixels: 200,      // Increase from default 100
  threshold: 0.3,          // Increase from default 0.2
});
```

**4. Dynamic Content Causing Failures**

Mask dynamic elements:

```typescript
const masks = await maskDynamicElements(page);

// Or manually mask specific elements
const masks = [
  page.locator('.timestamp'),
  page.locator('.user-avatar'),
];

await captureFullPageSnapshot(page, 'name', { mask: masks });
```

**5. Fonts Not Loading**

Ensure fonts are loaded before snapshot:

```typescript
await page.evaluate(() => document.fonts.ready);
```

**6. Animations Interfering**

Already handled by `preparePageForVisualTesting()`, but you can also:

```typescript
await page.addStyleTag({
  content: `* { animation: none !important; transition: none !important; }`
});
```

---

## Test Coverage

### Current Coverage

| Feature Area | Tests | Coverage |
|--------------|-------|----------|
| Authentication | 7 | Login, Register, Password Reset, Validation, Responsive |
| Dashboard | 11 | Home, Stats, Charts, Navigation, Mobile Menu, Dark Mode |
| Classes | 10 | List, Details, Students, Assignments, Modals, Responsive |
| Content | 10 | Library, Creation, Editor, AI Assistant, Preview, Filters |
| Quizzes | 10 | Library, Creation, Taking, Results, Progress, Responsive |
| Reports | 8 | Analytics, Charts, Tables, Filters, Export, Responsive |
| **Total** | **56** | Comprehensive coverage across all major features |

### Adding New Tests

**1. Create new test file**

```typescript
// e2e/visual/feature.visual.spec.ts
import { test } from '@playwright/test';
import { captureFullPageSnapshot, preparePageForVisualTesting } from '../utils/visual-testing';

test.describe('Feature - Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    await preparePageForVisualTesting(page);
  });

  test('Feature initial state', async ({ page }) => {
    await page.goto('/feature');
    await captureFullPageSnapshot(page, 'feature-initial');
  });
});
```

**2. Run tests to generate baseline**

```bash
npm run test:e2e:visual
```

**3. Commit snapshots to Git**

```bash
git add e2e/snapshots/
git commit -m "feat(tests): add visual regression tests for feature"
```

---

## Additional Resources

- [Playwright Visual Comparisons Docs](https://playwright.dev/docs/test-snapshots)
- [Best Practices for Visual Testing](https://playwright.dev/docs/test-snapshots#best-practices)
- [CI/CD Integration Guide](https://playwright.dev/docs/ci)

---

## Maintenance

### Updating Baseline Snapshots

When making intentional UI changes:

1. **Run tests to see differences**:
   ```bash
   npm run test:e2e:visual
   ```

2. **Review HTML report**:
   ```bash
   npx playwright show-report
   ```

3. **Update snapshots if changes are correct**:
   ```bash
   npm run test:e2e:visual:update
   ```

4. **Commit updated snapshots**:
   ```bash
   git add e2e/snapshots/
   git commit -m "chore(tests): update visual regression baselines"
   ```

### Snapshot Hygiene

- **Review snapshots regularly**: Remove unused snapshots
- **Keep snapshots small**: Use component tests for specific elements
- **Document major changes**: Add comments in tests explaining visual changes

---

## Conclusion

Visual regression testing is a critical part of maintaining UI quality. By following these guidelines and using the provided utilities, you can ensure that visual changes are intentional and don't break the user experience.

**Questions or Issues?** Refer to the [Playwright documentation](https://playwright.dev/docs/test-snapshots) or create an issue in the repository.
