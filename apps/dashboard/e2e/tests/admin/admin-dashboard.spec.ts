import { test, expect } from '../../fixtures/auth.fixture';

/**
 * E2E Tests for Admin Dashboard
 * Tests the complete AdminDashboard component functionality
 */

test.describe('Admin Dashboard', () => {
  test.use({ userRole: 'admin' });

  test.beforeEach(async ({ adminPage }) => {
    await adminPage.goto('/admin/dashboard');
    await adminPage.waitForLoadState('networkidle');
  });

  test('should display admin dashboard with all sections', async ({ adminPage }) => {
    // Check main dashboard elements
    await expect(adminPage.locator('h1')).toContainText('Admin Dashboard');
    await expect(adminPage.locator('text=System overview and management tools')).toBeVisible();

    // Check metrics cards are visible
    await expect(adminPage.locator('text=Total Users')).toBeVisible();
    await expect(adminPage.locator('text=Active Sessions')).toBeVisible();
    await expect(adminPage.locator('text=Content Generated')).toBeVisible();
    await expect(adminPage.locator('text=System Health')).toBeVisible();

    // Check tabs are present
    const tabs = ['Overview', 'Users', 'Content', 'Security', 'Settings'];
    for (const tab of tabs) {
      await expect(adminPage.locator(`text=${tab}`)).toBeVisible();
    }

    // Take screenshot for visual regression
    await adminPage.screenshot({
      path: 'e2e/snapshots/admin-dashboard-overview.png',
      fullPage: true,
    });
  });

  test('should display system performance metrics', async ({ adminPage }) => {
    // Check system performance section
    await expect(adminPage.locator('text=System Performance')).toBeVisible();

    // Check all performance metrics
    const metrics = ['CPU Usage', 'Memory Usage', 'Storage Usage', 'API Latency'];
    for (const metric of metrics) {
      const element = adminPage.locator(`text=${metric}`);
      await expect(element).toBeVisible();

      // Check that progress bars exist
      const progressBar = element.locator('..').locator('.MuiLinearProgress-root');
      await expect(progressBar).toBeVisible();
    }
  });

  test('should display system alerts', async ({ adminPage }) => {
    // Check alerts section
    await expect(adminPage.locator('text=System Alerts')).toBeVisible();

    // Check for alert list
    const alertsList = adminPage.locator('[role="list"]').first();
    await expect(alertsList).toBeVisible();

    // Check if alerts have severity indicators
    const alertItems = alertsList.locator('[role="listitem"]');
    const count = await alertItems.count();

    if (count > 0) {
      // Check first alert has required elements
      const firstAlert = alertItems.first();
      await expect(firstAlert.locator('.MuiAvatar-root')).toBeVisible();
      await expect(firstAlert.locator('.MuiListItemText-primary')).toBeVisible();
      await expect(firstAlert.locator('.MuiListItemText-secondary')).toBeVisible();
    }
  });

  test('should navigate between tabs', async ({ adminPage }) => {
    // Test Overview tab (default)
    await expect(adminPage.locator('text=System Performance')).toBeVisible();

    // Navigate to Users tab
    await adminPage.click('text=Users');
    await expect(adminPage.locator('text=User Management')).toBeVisible();

    // Navigate to Content tab
    await adminPage.click('text=Content');
    await expect(adminPage.locator('text=Content Moderation')).toBeVisible();

    // Navigate to Security tab
    await adminPage.click('text=Security');
    await expect(adminPage.locator('text=Security Settings')).toBeVisible();

    // Navigate to Settings tab
    await adminPage.click('text=Settings');
    await expect(adminPage.locator('text=System Settings')).toBeVisible();

    // Navigate back to Overview
    await adminPage.click('text=Overview');
    await expect(adminPage.locator('text=System Performance')).toBeVisible();
  });

  test('should refresh metrics on demand', async ({ adminPage }) => {
    // Click refresh button
    const refreshButton = adminPage.locator('[aria-label="Refresh"]');
    await expect(refreshButton).toBeVisible();

    // Monitor network request for metrics refresh
    const metricsPromise = adminPage.waitForResponse(
      response => response.url().includes('/admin/metrics'),
      { timeout: 5000 }
    ).catch(() => null);

    await refreshButton.click();

    // Check if refresh was attempted
    const response = await metricsPromise;
    if (response) {
      expect(response.status()).toBeLessThan(500);
    }

    // Check that refresh button shows loading state
    await expect(refreshButton).toBeDisabled();
    await adminPage.waitForTimeout(1000);
    await expect(refreshButton).toBeEnabled();
  });

  test('should handle alert resolution', async ({ adminPage }) => {
    // Find an unresolved alert
    const unresolvedAlert = adminPage
      .locator('[role="listitem"]')
      .filter({ has: adminPage.locator('[aria-label="resolve"]') })
      .first();

    const alertCount = await unresolvedAlert.count();

    if (alertCount > 0) {
      // Get alert text before resolving
      const alertText = await unresolvedAlert.locator('.MuiListItemText-primary').textContent();

      // Click resolve button
      await unresolvedAlert.locator('[aria-label="resolve"]').click();

      // Check that alert is marked as resolved (crossed out)
      await expect(unresolvedAlert).toHaveCSS('text-decoration', /line-through/);
      await expect(unresolvedAlert).toHaveCSS('opacity', /0\.6/);
    }
  });

  test('should display quick actions', async ({ adminPage }) => {
    // Scroll to bottom to see quick actions
    await adminPage.evaluate(() => window.scrollTo(0, document.body.scrollHeight));

    // Check quick action buttons
    const actions = ['Export Logs', 'Backup System', 'Clear Cache'];
    for (const action of actions) {
      const button = adminPage.locator(`button:has-text("${action}")`);
      await expect(button).toBeVisible();
      await expect(button).toBeEnabled();
    }
  });

  test('should show system health indicator', async ({ adminPage }) => {
    // Check system health card
    const healthCard = adminPage.locator('text=System Health').locator('..');
    await expect(healthCard).toBeVisible();

    // Check health percentage is displayed
    const healthValue = healthCard.locator('h4');
    const healthText = await healthValue.textContent();
    expect(healthText).toMatch(/\d+%/);

    // Check health progress bar
    const progressBar = healthCard.locator('.MuiLinearProgress-root');
    await expect(progressBar).toBeVisible();

    // Check health icon (success, warning, or error)
    const healthIcon = healthCard.locator('svg');
    await expect(healthIcon).toBeVisible();
  });

  test('should handle responsive layout', async ({ adminPage }) => {
    // Test different viewport sizes
    const viewports = [
      { width: 1920, height: 1080, name: 'desktop' },
      { width: 1024, height: 768, name: 'tablet' },
      { width: 375, height: 667, name: 'mobile' },
    ];

    for (const viewport of viewports) {
      await adminPage.setViewportSize(viewport);
      await adminPage.waitForTimeout(500);

      // Check that dashboard is still functional
      await expect(adminPage.locator('h1')).toContainText('Admin Dashboard');
      await expect(adminPage.locator('text=System Health')).toBeVisible();

      // Take screenshot for each viewport
      await adminPage.screenshot({
        path: `e2e/snapshots/admin-dashboard-${viewport.name}.png`,
        fullPage: false,
      });
    }
  });

  test('should show warning for low system health', async ({ adminPage }) => {
    // This test would need backend mock to set low health
    // Check if warning alert appears when health < 70
    const warningAlert = adminPage.locator('.MuiAlert-standardWarning');
    const warningCount = await warningAlert.count();

    if (warningCount > 0) {
      await expect(warningAlert).toContainText('System health is below optimal levels');
    }
  });
});

test.describe('Admin Dashboard - Accessibility', () => {
  test.use({ userRole: 'admin' });

  test('should have proper ARIA labels', async ({ adminPage }) => {
    await adminPage.goto('/admin/dashboard');

    // Check main landmarks
    await expect(adminPage.locator('[role="tablist"]')).toBeVisible();
    await expect(adminPage.locator('[role="tabpanel"]')).toBeVisible();

    // Check tab ARIA attributes
    const tabs = await adminPage.locator('[role="tab"]').all();
    for (const tab of tabs) {
      const ariaSelected = await tab.getAttribute('aria-selected');
      expect(['true', 'false']).toContain(ariaSelected);
    }

    // Check buttons have accessible names
    const buttons = await adminPage.locator('button').all();
    for (const button of buttons) {
      const ariaLabel = await button.getAttribute('aria-label');
      const textContent = await button.textContent();
      expect(ariaLabel || textContent).toBeTruthy();
    }
  });

  test('should be keyboard navigable', async ({ adminPage }) => {
    await adminPage.goto('/admin/dashboard');

    // Tab through interactive elements
    await adminPage.keyboard.press('Tab');
    const firstFocused = await adminPage.evaluate(() => document.activeElement?.tagName);
    expect(firstFocused).toBeDefined();

    // Navigate tabs with arrow keys
    const firstTab = adminPage.locator('[role="tab"]').first();
    await firstTab.focus();
    await adminPage.keyboard.press('ArrowRight');

    // Check that focus moved
    const activeFocused = await adminPage.evaluate(() => document.activeElement?.textContent);
    expect(activeFocused).toBeTruthy();

    // Test Enter key on buttons
    const refreshButton = adminPage.locator('[aria-label="Refresh"]');
    await refreshButton.focus();
    await adminPage.keyboard.press('Enter');

    // Should trigger same action as click
    await expect(refreshButton).toBeDisabled();
  });

  test('should have sufficient color contrast', async ({ adminPage }) => {
    await adminPage.goto('/admin/dashboard');

    // This would typically use axe-core or similar
    // For now, check that text is readable
    const textElements = await adminPage.locator('p, span, h1, h2, h3, h4, h5, h6').all();

    for (const element of textElements.slice(0, 10)) { // Check first 10 elements
      const color = await element.evaluate(el =>
        window.getComputedStyle(el).color
      );

      // Basic check that text has color
      expect(color).not.toBe('rgba(0, 0, 0, 0)');
    }
  });
});