/**
 * Visual Regression Tests - Dashboard/Home Page
 *
 * Tests visual consistency of the main dashboard including
 * widgets, charts, stats, and various user roles.
 */

import { test, expect } from '@playwright/test';
import {
  captureFullPageSnapshot,
  captureComponentSnapshot,
  preparePageForVisualTesting,
  maskDynamicElements,
  testColorSchemeSnapshots,
  STANDARD_VIEWPORTS,
  testResponsiveSnapshots,
} from '../utils/visual-testing';

test.describe('Dashboard - Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    await preparePageForVisualTesting(page);

    // Login if needed (assuming bypass mode for tests)
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('Dashboard - initial load', async ({ page }) => {
    const masks = await maskDynamicElements(page);

    await captureFullPageSnapshot(page, 'dashboard-home-initial', {
      mask: masks,
      waitForTimeout: 1500,
    });
  });

  test('Dashboard - stats cards', async ({ page }) => {
    const statsCard = page.locator('[data-testid="stats-card"], .stats-card').first();

    if (await statsCard.isVisible()) {
      await captureComponentSnapshot(statsCard, 'dashboard-stats-card');
    }
  });

  test('Dashboard - charts section', async ({ page }) => {
    const chartsSection = page.locator('[data-testid="charts-section"], .charts').first();

    if (await chartsSection.isVisible()) {
      await captureComponentSnapshot(chartsSection, 'dashboard-charts-section');
    }
  });

  test('Dashboard - recent activity widget', async ({ page }) => {
    const activityWidget = page.locator(
      '[data-testid="recent-activity"], .recent-activity'
    ).first();

    if (await activityWidget.isVisible()) {
      await captureComponentSnapshot(activityWidget, 'dashboard-recent-activity');
    }
  });

  test('Dashboard - responsive views', async ({ page }) => {
    const masks = await maskDynamicElements(page);

    await testResponsiveSnapshots(page, 'dashboard-responsive', [
      STANDARD_VIEWPORTS.mobile,
      STANDARD_VIEWPORTS.tablet,
      STANDARD_VIEWPORTS.desktop,
      STANDARD_VIEWPORTS.desktopWide,
    ]);
  });

  test('Dashboard - dark mode', async ({ page }) => {
    // Toggle dark mode if available
    const darkModeToggle = page.locator(
      '[data-testid="dark-mode-toggle"], [aria-label*="dark mode" i]'
    ).first();

    if (await darkModeToggle.isVisible()) {
      await darkModeToggle.click();
      await page.waitForTimeout(500);

      const masks = await maskDynamicElements(page);
      await captureFullPageSnapshot(page, 'dashboard-dark-mode', {
        mask: masks,
      });
    } else {
      // Use color scheme emulation
      await testColorSchemeSnapshots(page, 'dashboard-color-scheme', ['light', 'dark']);
    }
  });

  test('Dashboard - navigation sidebar', async ({ page }) => {
    const sidebar = page.locator('[data-testid="sidebar"], nav, .sidebar').first();

    if (await sidebar.isVisible()) {
      await captureComponentSnapshot(sidebar, 'dashboard-sidebar');
    }
  });

  test('Dashboard - top navigation bar', async ({ page }) => {
    const topNav = page.locator('[data-testid="top-nav"], header, .top-nav').first();

    if (await topNav.isVisible()) {
      await captureComponentSnapshot(topNav, 'dashboard-top-nav');
    }
  });

  test('Dashboard - mobile menu', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize(STANDARD_VIEWPORTS.mobile);
    await page.waitForTimeout(500);

    // Try to open mobile menu
    const menuButton = page.locator(
      '[data-testid="mobile-menu"], [aria-label*="menu" i]'
    ).first();

    if (await menuButton.isVisible()) {
      await menuButton.click();
      await page.waitForTimeout(300);

      await captureViewportSnapshot(page, 'dashboard-mobile-menu-open');
    }
  });

  test('Dashboard - user profile dropdown', async ({ page }) => {
    const profileButton = page.locator(
      '[data-testid="user-profile"], [aria-label*="profile" i], [aria-label*="account" i]'
    ).first();

    if (await profileButton.isVisible()) {
      await profileButton.click();
      await page.waitForTimeout(300);

      await captureViewportSnapshot(page, 'dashboard-profile-dropdown');
    }
  });
});
