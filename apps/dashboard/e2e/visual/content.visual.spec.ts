/**
 * Visual Regression Tests - Content Pages
 *
 * Tests visual consistency of content creation, editing,
 * and viewing pages including rich text editors and previews.
 */

import { test, expect } from '@playwright/test';
import {
  captureFullPageSnapshot,
  captureComponentSnapshot,
  preparePageForVisualTesting,
  captureStateSnapshots,
  maskDynamicElements,
  testResponsiveSnapshots,
  STANDARD_VIEWPORTS,
} from '../utils/visual-testing';

test.describe('Content Pages - Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    await preparePageForVisualTesting(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('Content library - initial load', async ({ page }) => {
    await page.goto('/content');
    await page.waitForLoadState('networkidle');

    const masks = await maskDynamicElements(page);
    await captureFullPageSnapshot(page, 'content-library-initial', {
      mask: masks,
      waitForTimeout: 1000,
    });
  });

  test('Content library - empty state', async ({ page }) => {
    await page.goto('/content?empty=true');
    await page.waitForLoadState('networkidle');

    await captureFullPageSnapshot(page, 'content-library-empty-state');
  });

  test('Content creation page - initial load', async ({ page }) => {
    await page.goto('/content/create');
    await page.waitForLoadState('networkidle');

    await captureFullPageSnapshot(page, 'content-create-initial', {
      waitForTimeout: 1000,
    });
  });

  test('Content creation - rich text editor', async ({ page }) => {
    await page.goto('/content/create');

    const editor = page.locator('[data-testid="rich-editor"], .tiptap, [contenteditable="true"]').first();

    if (await editor.isVisible()) {
      await captureComponentSnapshot(editor, 'content-rich-text-editor');
    }
  });

  test('Content creation - with content filled', async ({ page }) => {
    await page.goto('/content/create');

    // Fill in title
    const titleInput = page.getByLabel(/title/i);
    if (await titleInput.isVisible()) {
      await titleInput.fill('Sample Educational Content');
    }

    // Fill in description
    const descInput = page.getByLabel(/description/i);
    if (await descInput.isVisible()) {
      await descInput.fill('This is a sample description for visual testing');
    }

    await page.waitForTimeout(500);
    await captureFullPageSnapshot(page, 'content-create-filled');
  });

  test('Content creation - AI assistant panel', async ({ page }) => {
    await page.goto('/content/create');

    const aiButton = page.getByRole('button', { name: /ai assistant|generate|ai/i });

    if (await aiButton.isVisible()) {
      await aiButton.click();
      await page.waitForTimeout(500);

      await captureViewportSnapshot(page, 'content-ai-assistant-panel');
    }
  });

  test('Content preview modal', async ({ page }) => {
    await page.goto('/content/1');

    const previewButton = page.getByRole('button', { name: /preview/i });

    if (await previewButton.isVisible()) {
      await previewButton.click();
      await page.waitForTimeout(500);

      await captureViewportSnapshot(page, 'content-preview-modal');
    }
  });

  test('Content details page', async ({ page }) => {
    await page.goto('/content/1');
    await page.waitForLoadState('networkidle');

    const masks = await maskDynamicElements(page);
    await captureFullPageSnapshot(page, 'content-details-page', {
      mask: masks,
    });
  });

  test('Content - filter and search', async ({ page }) => {
    await page.goto('/content');

    // Open filters
    const filterButton = page.getByRole('button', { name: /filter/i });

    if (await filterButton.isVisible()) {
      await filterButton.click();
      await page.waitForTimeout(300);

      await captureViewportSnapshot(page, 'content-filters-open');
    }
  });

  test('Content - responsive views', async ({ page }) => {
    await page.goto('/content');

    await testResponsiveSnapshots(page, 'content-responsive', [
      STANDARD_VIEWPORTS.mobile,
      STANDARD_VIEWPORTS.tablet,
      STANDARD_VIEWPORTS.desktop,
    ]);
  });
});
