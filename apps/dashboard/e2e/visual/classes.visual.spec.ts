/**
 * Visual Regression Tests - Classes Pages
 *
 * Tests visual consistency of class management pages including
 * class list, class details, student roster, and assignments.
 */

import { test, expect } from '@playwright/test';
import {
  captureFullPageSnapshot,
  captureComponentSnapshot,
  preparePageForVisualTesting,
  maskDynamicElements,
  captureStateSnapshots,
  testResponsiveSnapshots,
  STANDARD_VIEWPORTS,
} from '../utils/visual-testing';

test.describe('Classes Pages - Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    await preparePageForVisualTesting(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('Classes list page - initial load', async ({ page }) => {
    await page.goto('/classes');
    await page.waitForLoadState('networkidle');

    const masks = await maskDynamicElements(page);
    await captureFullPageSnapshot(page, 'classes-list-initial', {
      mask: masks,
      waitForTimeout: 1000,
    });
  });

  test('Classes list page - empty state', async ({ page }) => {
    await page.goto('/classes?empty=true');
    await page.waitForLoadState('networkidle');

    await captureFullPageSnapshot(page, 'classes-list-empty-state');
  });

  test('Classes list page - grid view', async ({ page }) => {
    await page.goto('/classes');

    // Try to switch to grid view
    const gridViewButton = page.locator('[data-testid="grid-view"], [aria-label*="grid" i]').first();

    if (await gridViewButton.isVisible()) {
      await gridViewButton.click();
      await page.waitForTimeout(300);
    }

    const masks = await maskDynamicElements(page);
    await captureFullPageSnapshot(page, 'classes-list-grid-view', {
      mask: masks,
    });
  });

  test('Classes list page - list view', async ({ page }) => {
    await page.goto('/classes');

    // Try to switch to list view
    const listViewButton = page.locator('[data-testid="list-view"], [aria-label*="list" i]').first();

    if (await listViewButton.isVisible()) {
      await listViewButton.click();
      await page.waitForTimeout(300);
    }

    const masks = await maskDynamicElements(page);
    await captureFullPageSnapshot(page, 'classes-list-list-view', {
      mask: masks,
    });
  });

  test('Classes list - single class card', async ({ page }) => {
    await page.goto('/classes');
    await page.waitForLoadState('networkidle');

    const classCard = page.locator('[data-testid="class-card"], .class-card').first();

    if (await classCard.isVisible()) {
      await captureComponentSnapshot(classCard, 'classes-class-card');
    }
  });

  test('Class details page', async ({ page }) => {
    await page.goto('/classes/1'); // Assuming mock data
    await page.waitForLoadState('networkidle');

    const masks = await maskDynamicElements(page);
    await captureFullPageSnapshot(page, 'classes-details-page', {
      mask: masks,
      waitForTimeout: 1000,
    });
  });

  test('Class details - students tab', async ({ page }) => {
    await page.goto('/classes/1');

    const studentsTab = page.getByRole('tab', { name: /students/i });

    if (await studentsTab.isVisible()) {
      await studentsTab.click();
      await page.waitForTimeout(500);

      const masks = await maskDynamicElements(page);
      await captureFullPageSnapshot(page, 'classes-details-students-tab', {
        mask: masks,
      });
    }
  });

  test('Class details - assignments tab', async ({ page }) => {
    await page.goto('/classes/1');

    const assignmentsTab = page.getByRole('tab', { name: /assignments/i });

    if (await assignmentsTab.isVisible()) {
      await assignmentsTab.click();
      await page.waitForTimeout(500);

      const masks = await maskDynamicElements(page);
      await captureFullPageSnapshot(page, 'classes-details-assignments-tab', {
        mask: masks,
      });
    }
  });

  test('Create class modal', async ({ page }) => {
    await page.goto('/classes');

    const createButton = page.getByRole('button', { name: /create class|new class|add class/i });

    if (await createButton.isVisible()) {
      await createButton.click();
      await page.waitForTimeout(500);

      await captureViewportSnapshot(page, 'classes-create-modal');
    }
  });

  test('Classes - responsive views', async ({ page }) => {
    await page.goto('/classes');

    await testResponsiveSnapshots(page, 'classes-responsive', [
      STANDARD_VIEWPORTS.mobile,
      STANDARD_VIEWPORTS.tablet,
      STANDARD_VIEWPORTS.desktop,
    ]);
  });
});
