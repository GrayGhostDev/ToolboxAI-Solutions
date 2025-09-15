# Playwright E2E Testing

This directory contains end-to-end tests for the ToolBoxAI Solutions platform using Playwright.

## Setup

### Prerequisites

- Node.js 20+ 
- npm 9+
- Python 3.11+ (for backend services)

### Installation

1. Install Playwright and browsers:
```bash
npm install
npx playwright install
```

2. Start the required services:
```bash
# Terminal 1: Start backend
python -m uvicorn apps.backend.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start dashboard
npm run dashboard:dev
```

## Running Tests

### All Tests
```bash
npm run test:e2e
```

### Specific Test Files
```bash
npx playwright test dashboard.spec.ts
npx playwright test roblox-integration.spec.ts
```

### Interactive Mode
```bash
npm run test:e2e:ui
```

### Debug Mode
```bash
npm run test:e2e:debug
```

### Headed Mode (see browser)
```bash
npm run test:e2e:headed
```

## Test Structure

```
tests/e2e/
├── README.md                    # This file
├── global-setup.ts             # Global test setup
├── global-teardown.ts          # Global test cleanup
├── dashboard.spec.ts           # Dashboard E2E tests
├── api-integration.spec.ts     # API integration tests
├── roblox-integration.spec.ts  # Roblox integration tests
└── utils/
    └── test-helpers.ts         # Reusable test utilities
```

## Configuration

The Playwright configuration is in `playwright.config.ts` at the project root. Key settings:

- **Base URL**: `http://localhost:3000` (dashboard)
- **Test Directory**: `./tests/e2e`
- **Browsers**: Chromium, Firefox, WebKit
- **Mobile Testing**: Pixel 5, iPhone 12
- **Screenshots**: On failure
- **Videos**: On failure
- **Traces**: On first retry

## Test Utilities

The `TestHelpers` class provides common testing utilities:

- `waitForPageLoad()` - Wait for page to fully load
- `waitForElement()` - Wait for element to be visible
- `checkConsoleErrors()` - Check for console errors
- `testResponsiveDesign()` - Test multiple viewports
- `checkAccessibility()` - Basic accessibility checks
- `mockApiResponse()` - Mock API responses

## Common Selectors

The `SELECTORS` object provides common CSS selectors:

- Navigation elements
- Authentication components
- Dashboard elements
- Form elements
- Loading states
- Error messages

## Writing Tests

### Basic Test Structure

```typescript
import { test, expect } from '@playwright/test';
import { TestHelpers, SELECTORS } from './utils/test-helpers';

test.describe('Feature Tests', () => {
  let testHelpers: TestHelpers;

  test.beforeEach(async ({ page }) => {
    testHelpers = new TestHelpers(page);
    await page.goto('/');
    await testHelpers.waitForPageLoad();
  });

  test('should do something', async ({ page }) => {
    // Test implementation
    await expect(page.locator('body')).toBeVisible();
  });
});
```

### Best Practices

1. **Use TestHelpers**: Leverage the utility functions for common operations
2. **Wait for Elements**: Always wait for elements to be visible before interacting
3. **Check Console Errors**: Verify no JavaScript errors occur
4. **Test Responsive Design**: Use the responsive design testing utility
5. **Mock API Calls**: Mock external API calls for consistent testing
6. **Clean Up**: Use beforeEach/afterEach for setup and cleanup

## Debugging

### View Test Results
```bash
npm run test:e2e:report
```

### Debug Specific Test
```bash
npx playwright test --debug dashboard.spec.ts
```

### Trace Viewer
```bash
npx playwright show-trace trace.zip
```

## CI/CD Integration

Tests run automatically on:
- Push to main/develop branches
- Pull requests to main/develop branches

Results are uploaded as artifacts:
- `playwright-report/` - HTML test report
- `test-results/` - Screenshots, videos, traces

## Troubleshooting

### Common Issues

1. **Tests timing out**: Increase timeout in `playwright.config.ts`
2. **Elements not found**: Use `waitForElement()` before interacting
3. **Flaky tests**: Add proper waits and retries
4. **Browser not launching**: Run `npx playwright install`

### Debug Commands

```bash
# Check Playwright installation
npx playwright --version

# Install specific browser
npx playwright install chromium

# Run with verbose output
npx playwright test --reporter=list

# Run specific browser
npx playwright test --project=chromium
```

## Contributing

When adding new tests:

1. Follow the existing naming convention (`*.spec.ts`)
2. Use descriptive test names
3. Add appropriate selectors to `SELECTORS` object
4. Update this README if adding new utilities
5. Ensure tests are deterministic and don't rely on external state
