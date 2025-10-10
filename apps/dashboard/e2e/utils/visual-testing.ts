/**
 * Visual Testing Utilities for Playwright
 *
 * Provides helper functions for consistent visual regression testing
 * across the ToolboxAI Dashboard application.
 *
 * @module visual-testing
 */

import { Page, Locator, expect } from '@playwright/test';

/**
 * Visual testing configuration options
 */
export interface VisualTestOptions {
  /** Name of the snapshot */
  name?: string;
  /** Maximum number of different pixels allowed */
  maxDiffPixels?: number;
  /** Maximum ratio of different pixels (0-1) */
  maxDiffPixelRatio?: number;
  /** Threshold for pixel comparison (0-1) */
  threshold?: number;
  /** Full page screenshot */
  fullPage?: boolean;
  /** Mask elements before screenshot */
  mask?: Locator[];
  /** CSS animations setting */
  animations?: 'allow' | 'disabled';
  /** Wait for specific timeout before screenshot */
  waitForTimeout?: number;
  /** Wait for specific selector */
  waitForSelector?: string;
}

/**
 * Take a full page visual snapshot
 */
export async function captureFullPageSnapshot(
  page: Page,
  name: string,
  options: Omit<VisualTestOptions, 'name' | 'fullPage'> = {}
): Promise<void> {
  // Wait for page to be fully loaded
  await page.waitForLoadState('networkidle');

  // Wait for animations to complete
  await page.waitForTimeout(options.waitForTimeout || 500);

  // If specific selector needed, wait for it
  if (options.waitForSelector) {
    await page.waitForSelector(options.waitForSelector, { state: 'visible' });
  }

  await expect(page).toHaveScreenshot(`${name}.png`, {
    fullPage: true,
    maxDiffPixels: options.maxDiffPixels,
    maxDiffPixelRatio: options.maxDiffPixelRatio,
    threshold: options.threshold,
    mask: options.mask,
    animations: options.animations || 'disabled',
  });
}

/**
 * Take a viewport-only visual snapshot
 */
export async function captureViewportSnapshot(
  page: Page,
  name: string,
  options: Omit<VisualTestOptions, 'name' | 'fullPage'> = {}
): Promise<void> {
  // Wait for page to be stable
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(options.waitForTimeout || 300);

  if (options.waitForSelector) {
    await page.waitForSelector(options.waitForSelector, { state: 'visible' });
  }

  await expect(page).toHaveScreenshot(`${name}-viewport.png`, {
    fullPage: false,
    maxDiffPixels: options.maxDiffPixels,
    maxDiffPixelRatio: options.maxDiffPixelRatio,
    threshold: options.threshold,
    mask: options.mask,
    animations: options.animations || 'disabled',
  });
}

/**
 * Take a component-level visual snapshot
 */
export async function captureComponentSnapshot(
  locator: Locator,
  name: string,
  options: Omit<VisualTestOptions, 'name' | 'fullPage'> = {}
): Promise<void> {
  // Wait for component to be visible and stable
  await locator.waitFor({ state: 'visible' });
  await locator.evaluate((el) => {
    // Force synchronous layout
    el.getBoundingClientRect();
  });

  await expect(locator).toHaveScreenshot(`${name}-component.png`, {
    maxDiffPixels: options.maxDiffPixels,
    maxDiffPixelRatio: options.maxDiffPixelRatio,
    threshold: options.threshold,
    mask: options.mask,
    animations: options.animations || 'disabled',
  });
}

/**
 * Prepare page for consistent visual testing
 */
export async function preparePageForVisualTesting(page: Page): Promise<void> {
  // Disable animations via CSS
  await page.addStyleTag({
    content: `
      *, *::before, *::after {
        animation-duration: 0s !important;
        animation-delay: 0s !important;
        transition-duration: 0s !important;
        transition-delay: 0s !important;
      }
    `,
  });

  // Hide dynamic content that changes frequently
  await page.evaluate(() => {
    // Hide cursors/carets
    document.querySelectorAll('[contenteditable]').forEach((el) => {
      (el as HTMLElement).style.caretColor = 'transparent';
    });

    // Hide video elements
    document.querySelectorAll('video').forEach((el) => {
      (el as HTMLVideoElement).pause();
    });

    // Pause GIFs (set to first frame)
    document.querySelectorAll('img[src$=".gif"]').forEach((el) => {
      const img = el as HTMLImageElement;
      img.src = img.src; // Reset to first frame
    });
  });

  // Wait for fonts to load
  await page.evaluate(() => document.fonts.ready);

  // Wait for images to load
  await page.evaluate(() => {
    return Promise.all(
      Array.from(document.images)
        .filter((img) => !img.complete)
        .map(
          (img) =>
            new Promise((resolve) => {
              img.onload = img.onerror = resolve;
            })
        )
    );
  });
}

/**
 * Mask dynamic elements (timestamps, user IDs, etc.)
 */
export async function maskDynamicElements(page: Page): Promise<Locator[]> {
  const masks: Locator[] = [];

  // Common selectors for dynamic content
  const dynamicSelectors = [
    '[data-testid*="timestamp"]',
    '[data-testid*="date"]',
    '[data-testid*="time"]',
    '[data-testid*="random"]',
    '[data-testid*="uuid"]',
    '.timestamp',
    '.date',
    '.time-ago',
    '.user-avatar', // User avatars may change
  ];

  for (const selector of dynamicSelectors) {
    const elements = page.locator(selector);
    const count = await elements.count();
    if (count > 0) {
      masks.push(elements);
    }
  }

  return masks;
}

/**
 * Test visual consistency across multiple viewports
 */
export async function testResponsiveSnapshots(
  page: Page,
  name: string,
  viewports: Array<{ width: number; height: number; name: string }>
): Promise<void> {
  for (const viewport of viewports) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.waitForTimeout(500); // Let layout stabilize

    await expect(page).toHaveScreenshot(`${name}-${viewport.name}.png`, {
      fullPage: false,
      animations: 'disabled',
    });
  }
}

/**
 * Test visual consistency across color schemes
 */
export async function testColorSchemeSnapshots(
  page: Page,
  name: string,
  schemes: Array<'light' | 'dark' | 'no-preference'>
): Promise<void> {
  for (const scheme of schemes) {
    await page.emulateMedia({ colorScheme: scheme });
    await page.waitForTimeout(300); // Let theme transition complete

    await expect(page).toHaveScreenshot(`${name}-${scheme}.png`, {
      fullPage: true,
      animations: 'disabled',
    });
  }
}

/**
 * Capture state snapshots (before/after interactions)
 */
export async function captureStateSnapshots(
  page: Page,
  name: string,
  interaction: () => Promise<void>
): Promise<void> {
  // Before state
  await expect(page).toHaveScreenshot(`${name}-before.png`, {
    animations: 'disabled',
  });

  // Perform interaction
  await interaction();
  await page.waitForTimeout(500);

  // After state
  await expect(page).toHaveScreenshot(`${name}-after.png`, {
    animations: 'disabled',
  });
}

/**
 * Standard viewports for responsive testing
 */
export const STANDARD_VIEWPORTS = {
  mobile: { width: 375, height: 667, name: 'mobile' },
  mobileWide: { width: 428, height: 926, name: 'mobile-wide' },
  tablet: { width: 768, height: 1024, name: 'tablet' },
  tabletWide: { width: 1024, height: 768, name: 'tablet-wide' },
  desktop: { width: 1280, height: 720, name: 'desktop' },
  desktopWide: { width: 1920, height: 1080, name: 'desktop-wide' },
  desktop4K: { width: 3840, height: 2160, name: 'desktop-4k' },
};

/**
 * Retry visual test with updated baseline
 * Useful for intentional design changes
 */
export async function updateVisualBaseline(
  testFn: () => Promise<void>,
  updateMode: boolean = process.env.UPDATE_SNAPSHOTS === 'true'
): Promise<void> {
  if (updateMode) {
    console.log('🔄 Updating visual baseline...');
  }
  await testFn();
}
