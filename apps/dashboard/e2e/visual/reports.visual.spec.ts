/**
 * Visual Regression Tests - Reports and Analytics
 *
 * Tests visual consistency of reports, charts, analytics
 * dashboards, and data visualization components.
 */

import { test, expect } from '@playwright/test';
import {
  captureFullPageSnapshot,
  captureComponentSnapshot,
  preparePageForVisualTesting,
  maskDynamicElements,
  testResponsiveSnapshots,
  STANDARD_VIEWPORTS,
} from '../utils/visual-testing';

test.describe('Reports and Analytics - Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    await preparePageForVisualTesting(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('Reports page - initial load', async ({ page }) => {
    await page.goto('/reports');
    await page.waitForLoadState('networkidle');

    const masks = await maskDynamicElements(page);
    await captureFullPageSnapshot(page, 'reports-page-initial', {
      mask: masks,
      waitForTimeout: 1500, // Charts may take time to render
    });
  });

  test('Reports - performance chart', async ({ page }) => {
    await page.goto('/reports');

    const performanceChart = page.locator('[data-testid="performance-chart"], .performance-chart').first();

    if (await performanceChart.isVisible()) {
      await page.waitForTimeout(1000); // Wait for chart animation
      await captureComponentSnapshot(performanceChart, 'reports-performance-chart');
    }
  });

  test('Reports - engagement metrics', async ({ page }) => {
    await page.goto('/reports');

    const engagementSection = page.locator('[data-testid="engagement-metrics"], .engagement').first();

    if (await engagementSection.isVisible()) {
      await captureComponentSnapshot(engagementSection, 'reports-engagement-metrics');
    }
  });

  test('Reports - student progress table', async ({ page }) => {
    await page.goto('/reports/students');
    await page.waitForLoadState('networkidle');

    const progressTable = page.locator('[data-testid="progress-table"], table').first();

    if (await progressTable.isVisible()) {
      await captureComponentSnapshot(progressTable, 'reports-student-progress-table');
    }
  });

  test('Reports - date range filter', async ({ page }) => {
    await page.goto('/reports');

    const dateRangeButton = page.getByRole('button', { name: /date range|filter/i });

    if (await dateRangeButton.isVisible()) {
      await dateRangeButton.click();
      await page.waitForTimeout(300);

      await captureViewportSnapshot(page, 'reports-date-range-filter');
    }
  });

  test('Reports - export options', async ({ page }) => {
    await page.goto('/reports');

    const exportButton = page.getByRole('button', { name: /export/i });

    if (await exportButton.isVisible()) {
      await exportButton.click();
      await page.waitForTimeout(300);

      await captureViewportSnapshot(page, 'reports-export-options');
    }
  });

  test('Analytics dashboard', async ({ page }) => {
    await page.goto('/analytics');
    await page.waitForLoadState('networkidle');

    const masks = await maskDynamicElements(page);
    await captureFullPageSnapshot(page, 'analytics-dashboard', {
      mask: masks,
      waitForTimeout: 1500,
    });
  });

  test('Reports - responsive views', async ({ page }) => {
    await page.goto('/reports');

    await testResponsiveSnapshots(page, 'reports-responsive', [
      STANDARD_VIEWPORTS.mobile,
      STANDARD_VIEWPORTS.tablet,
      STANDARD_VIEWPORTS.desktop,
    ]);
  });
});
