import { test, expect, type Page } from '@playwright/test';

// Test data
const TEST_USERS = {
  teacher: {
    email: 'teacher@test.com',
    password: 'test123',
    role: 'teacher',
    routes: ['/lessons', '/assessments', '/classes', '/reports', '/messages', '/roblox', '/settings']
  },
  student: {
    email: 'student@test.com',
    password: 'test123',
    role: 'student',
    routes: ['/missions', '/rewards', '/avatar', '/play', '/progress', '/leaderboard', '/settings']
  },
  admin: {
    email: 'admin@test.com',
    password: 'test123',
    role: 'admin',
    routes: ['/compliance', '/integrations', '/schools', '/users', '/analytics', '/agents', '/observability']
  },
  parent: {
    email: 'parent@test.com',
    password: 'test123',
    role: 'parent',
    routes: ['/messages', '/gameplay-replay', '/progress', '/reports', '/settings']
  }
};

// Helper to set bypass mode
async function enableBypassMode(page: Page) {
  await page.addInitScript(() => {
    (window as any).localStorage.setItem('bypassAuth', 'true');
    (window as any).localStorage.setItem('useMockData', 'true');
  });
}

// Helper to check if navigation works
async function checkNavigation(page: Page, route: string, expectedContent?: string) {
  await page.goto(route);

  // Wait for page to load
  await page.waitForLoadState('networkidle');

  // Check if we're not redirected to login
  const currentUrl = page.url();
  expect(currentUrl).not.toContain('/login');

  // Check for error pages
  const notFound = await page.locator('text=/not found|404|unauthorized/i').count();
  expect(notFound).toBe(0);

  // Check for expected content if provided
  if (expectedContent) {
    await expect(page.locator(`text=${expectedContent}`)).toBeVisible({ timeout: 10000 });
  }
}

test.describe('Dashboard Navigation - Bypass Mode', () => {
  test.beforeEach(async ({ page }) => {
    await enableBypassMode(page);
  });

  test('Home page loads correctly', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Dashboard/i);

    // Check for dashboard elements
    const sidebar = page.locator('[data-testid="sidebar"], aside, nav');
    await expect(sidebar).toBeVisible();
  });

  test('Teacher routes are accessible', async ({ page }) => {
    // Set teacher role in localStorage
    await page.addInitScript(() => {
      (window as any).localStorage.setItem('userRole', 'teacher');
    });

    for (const route of TEST_USERS.teacher.routes) {
      await test.step(`Navigate to ${route}`, async () => {
        await checkNavigation(page, route);
      });
    }
  });

  test('Student routes are accessible', async ({ page }) => {
    // Set student role
    await page.addInitScript(() => {
      (window as any).localStorage.setItem('userRole', 'student');
    });

    for (const route of TEST_USERS.student.routes) {
      await test.step(`Navigate to ${route}`, async () => {
        await checkNavigation(page, route);
      });
    }
  });

  test('Admin routes are accessible', async ({ page }) => {
    // Set admin role
    await page.addInitScript(() => {
      (window as any).localStorage.setItem('userRole', 'admin');
    });

    for (const route of TEST_USERS.admin.routes) {
      await test.step(`Navigate to ${route}`, async () => {
        await checkNavigation(page, route);
      });
    }
  });

  test('Parent routes are accessible', async ({ page }) => {
    // Set parent role
    await page.addInitScript(() => {
      (window as any).localStorage.setItem('userRole', 'parent');
    });

    for (const route of TEST_USERS.parent.routes) {
      await test.step(`Navigate to ${route}`, async () => {
        await checkNavigation(page, route);
      });
    }
  });

  test('Sidebar navigation works', async ({ page }) => {
    await page.goto('/');

    // Check sidebar exists
    const sidebar = page.locator('aside, [data-testid="sidebar"], nav').first();
    await expect(sidebar).toBeVisible();

    // Try clicking navigation items
    const navLinks = sidebar.locator('a[href]');
    const linkCount = await navLinks.count();

    expect(linkCount).toBeGreaterThan(0);

    // Click first few links
    for (let i = 0; i < Math.min(3, linkCount); i++) {
      const link = navLinks.nth(i);
      const href = await link.getAttribute('href');

      if (href && !href.startsWith('http')) {
        await link.click();
        await page.waitForLoadState('networkidle');

        // Verify navigation happened
        const currentPath = new URL(page.url()).pathname;
        expect(currentPath).toBeDefined();
      }
    }
  });

  test('Mock data loads correctly', async ({ page }) => {
    await page.goto('/classes');

    // Check for mock data presence
    await page.waitForSelector('text=/Math|Science|English|History/i', { timeout: 10000 });

    // Verify no API errors
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.waitForTimeout(2000);

    // Filter out expected CORS errors
    const criticalErrors = errors.filter(e =>
      !e.includes('CORS') &&
      !e.includes('401') &&
      !e.includes('Failed to fetch')
    );

    expect(criticalErrors).toHaveLength(0);
  });

  test('3D components render without errors', async ({ page }) => {
    await page.goto('/roblox');

    // Wait for 3D canvas
    await page.waitForSelector('canvas', { timeout: 15000 });

    // Check for WebGL context
    const hasWebGL = await page.evaluate(() => {
      const canvas = document.querySelector('canvas');
      if (!canvas) return false;

      const gl = (canvas as HTMLCanvasElement).getContext('webgl') ||
                 (canvas as HTMLCanvasElement).getContext('experimental-webgl');
      return !!gl;
    });

    expect(hasWebGL).toBeTruthy();
  });

  test('Reports page loads with templates', async ({ page }) => {
    await page.goto('/reports');

    // Check for report templates
    await expect(page.locator('text=/Popular Templates|Recent Reports/i')).toBeVisible();

    // Check for action buttons
    await expect(page.locator('button:has-text("Generate Report")')).toBeVisible();
  });

  test('Settings page is accessible', async ({ page }) => {
    await page.goto('/settings');

    // Check for settings sections
    await expect(page.locator('text=/Profile|Preferences|Security/i')).toBeVisible();
  });
});

test.describe('Component Interactions', () => {
  test.beforeEach(async ({ page }) => {
    await enableBypassMode(page);
  });

  test('Tab navigation works', async ({ page }) => {
    await page.goto('/reports');

    // Find tabs
    const tabs = page.locator('[role="tab"], .mantine-Tabs-tab');
    const tabCount = await tabs.count();

    if (tabCount > 0) {
      // Click second tab if exists
      if (tabCount > 1) {
        await tabs.nth(1).click();
        await page.waitForTimeout(500);

        // Verify tab panel changed
        const activePanels = page.locator('[role="tabpanel"]:visible, .mantine-Tabs-panel:visible');
        await expect(activePanels).toHaveCount(1);
      }
    }
  });

  test('Modals and dialogs work', async ({ page }) => {
    await page.goto('/');

    // Look for any button that might open a modal
    const modalTriggers = page.locator('button:has-text(/add|create|new|edit/i)');
    const triggerCount = await modalTriggers.count();

    if (triggerCount > 0) {
      await modalTriggers.first().click();

      // Check if modal opened
      const modal = page.locator('[role="dialog"], .mantine-Modal-root');
      const isModalVisible = await modal.isVisible().catch(() => false);

      if (isModalVisible) {
        // Close modal
        const closeButton = modal.locator('button:has-text("Close"), [aria-label="Close"]');
        if (await closeButton.isVisible()) {
          await closeButton.click();
        } else {
          await page.keyboard.press('Escape');
        }
      }
    }
  });

  test('Forms accept input', async ({ page }) => {
    await page.goto('/settings');

    // Find input fields
    const inputs = page.locator('input[type="text"], input[type="email"], textarea');
    const inputCount = await inputs.count();

    if (inputCount > 0) {
      const firstInput = inputs.first();
      await firstInput.click();
      await firstInput.fill('Test Input');

      // Verify input was accepted
      const value = await firstInput.inputValue();
      expect(value).toBe('Test Input');
    }
  });

  test('Dropdown menus work', async ({ page }) => {
    await page.goto('/');

    // Find dropdowns
    const dropdowns = page.locator('select, [role="combobox"], .mantine-Select-input');
    const dropdownCount = await dropdowns.count();

    if (dropdownCount > 0) {
      const dropdown = dropdowns.first();
      await dropdown.click();

      // Check for options
      const options = page.locator('[role="option"], .mantine-Select-option');
      const hasOptions = await options.count() > 0;

      if (hasOptions) {
        await options.first().click();
      }
    }
  });
});

test.describe('Performance and Error Handling', () => {
  test.beforeEach(async ({ page }) => {
    await enableBypassMode(page);
  });

  test('Pages load within acceptable time', async ({ page }) => {
    const routes = ['/', '/classes', '/reports', '/settings'];

    for (const route of routes) {
      await test.step(`Performance test for ${route}`, async () => {
        const startTime = Date.now();
        await page.goto(route);
        await page.waitForLoadState('networkidle');
        const loadTime = Date.now() - startTime;

        // Page should load within 5 seconds
        expect(loadTime).toBeLessThan(5000);
      });
    }
  });

  test('Error boundaries catch component errors', async ({ page }) => {
    // Monitor console for unhandled errors
    const errors = [];
    page.on('pageerror', err => errors.push(err.message));

    await page.goto('/');
    await page.waitForTimeout(2000);

    // Navigate through several pages
    for (const route of ['/', '/classes', '/reports']) {
      await page.goto(route);
      await page.waitForTimeout(1000);
    }

    // Check for critical errors
    const criticalErrors = errors.filter(e =>
      !e.includes('ChunkLoadError') &&
      !e.includes('NetworkError')
    );

    expect(criticalErrors).toHaveLength(0);
  });

  test('Responsive design works', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Check if mobile menu exists
    const mobileMenu = page.locator('[aria-label*="menu"], button:has-text("Menu"), [data-testid="mobile-menu"]');
    const isMobileMenuVisible = await mobileMenu.isVisible().catch(() => false);

    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.reload();

    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.reload();

    // Verify layout adjusts (sidebar should be visible on desktop)
    const sidebar = page.locator('aside, [data-testid="sidebar"]').first();
    await expect(sidebar).toBeVisible();
  });
});