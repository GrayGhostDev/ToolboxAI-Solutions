import type { Page, Locator } from '@playwright/test';

/**
 * Semantic Locator Helpers
 * Provides utility functions for finding elements using 2025 Playwright best practices
 */

export class LocatorHelper {
  private page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Get element by semantic role with fallback to data-testid
   */
  async getByRoleWithFallback(
    role: 'button' | 'textbox' | 'checkbox' | 'radio' | 'link' | 'heading' | 'alert' | 'navigation' | 'tab' | 'tablist',
    options?: { name?: string | RegExp; testId?: string }
  ): Promise<Locator> {
    // Try semantic locator first
    const semanticLocator = this.page.getByRole(role, options?.name ? { name: options.name } : undefined);

    if (await semanticLocator.count() > 0) {
      return semanticLocator;
    }

    // Fallback to data-testid if provided
    if (options?.testId) {
      return this.page.locator(`[data-testid="${options.testId}"]`);
    }

    return semanticLocator; // Return the semantic locator even if not found (for error messages)
  }

  /**
   * Get form input by label with fallback strategies
   */
  async getFormInput(labelText: string | RegExp, fallbackSelector?: string): Promise<Locator> {
    // Strategy 1: getByLabel
    const byLabel = this.page.getByLabel(labelText);
    if (await byLabel.count() > 0) {
      return byLabel;
    }

    // Strategy 2: Find label and associated input
    const label = this.page.locator('label', { hasText: labelText });
    if (await label.count() > 0) {
      const forAttribute = await label.getAttribute('for');
      if (forAttribute) {
        return this.page.locator(`#${forAttribute}`);
      }
    }

    // Strategy 3: Fallback selector if provided
    if (fallbackSelector) {
      return this.page.locator(fallbackSelector);
    }

    return byLabel; // Return original for error messages
  }

  /**
   * Get button with multiple fallback strategies
   */
  async getButton(text: string | RegExp, options?: { testId?: string; className?: string }): Promise<Locator> {
    // Strategy 1: Semantic button role
    const byRole = this.page.getByRole('button', { name: text });
    if (await byRole.count() > 0) {
      return byRole;
    }

    // Strategy 2: Button element with text
    const buttonWithText = this.page.locator('button', { hasText: text });
    if (await buttonWithText.count() > 0) {
      return buttonWithText;
    }

    // Strategy 3: data-testid
    if (options?.testId) {
      const byTestId = this.page.locator(`[data-testid="${options.testId}"]`);
      if (await byTestId.count() > 0) {
        return byTestId;
      }
    }

    // Strategy 4: Class name
    if (options?.className) {
      const byClass = this.page.locator(`.${options.className}`, { hasText: text });
      if (await byClass.count() > 0) {
        return byClass;
      }
    }

    return byRole; // Return original for error messages
  }

  /**
   * Get link with fallback strategies
   */
  async getLink(text: string | RegExp, options?: { href?: string }): Promise<Locator> {
    // Strategy 1: Semantic link role
    const byRole = this.page.getByRole('link', { name: text });
    if (await byRole.count() > 0) {
      return byRole;
    }

    // Strategy 2: Anchor element with text
    const anchorWithText = this.page.locator('a', { hasText: text });
    if (await anchorWithText.count() > 0) {
      return anchorWithText;
    }

    // Strategy 3: By href if provided
    if (options?.href) {
      const byHref = this.page.locator(`a[href*="${options.href}"]`, { hasText: text });
      if (await byHref.count() > 0) {
        return byHref;
      }
    }

    return byRole;
  }

  /**
   * Wait for element to be stable (no changes for specified time)
   */
  async waitForElementStable(locator: Locator, timeout: number = 500): Promise<void> {
    // Wait for element to be visible first
    await locator.waitFor({ state: 'visible' });

    // Get initial bounding box
    const initialBox = await locator.boundingBox();
    if (!initialBox) return;

    // Wait for specified time
    await this.page.waitForTimeout(timeout);

    // Check if position/size changed
    const finalBox = await locator.boundingBox();
    if (!finalBox) return;

    // If changed significantly, wait again
    const threshold = 5; // pixels
    if (
      Math.abs(initialBox.x - finalBox.x) > threshold ||
      Math.abs(initialBox.y - finalBox.y) > threshold ||
      Math.abs(initialBox.width - finalBox.width) > threshold ||
      Math.abs(initialBox.height - finalBox.height) > threshold
    ) {
      await this.page.waitForTimeout(timeout);
    }
  }

  /**
   * Get element by accessible name
   */
  async getByAccessibleName(name: string | RegExp): Promise<Locator> {
    // Try multiple strategies to find by accessible name
    const strategies = [
      () => this.page.getByRole('button', { name }),
      () => this.page.getByRole('link', { name }),
      () => this.page.getByRole('textbox', { name }),
      () => this.page.getByRole('checkbox', { name }),
      () => this.page.getByRole('radio', { name }),
      () => this.page.locator(`[aria-label="${name}"]`),
      () => this.page.locator(`[title="${name}"]`)
    ];

    for (const strategy of strategies) {
      const locator = strategy();
      if (await locator.count() > 0) {
        return locator;
      }
    }

    // Return first strategy result for error messages
    return strategies[0]();
  }

  /**
   * Get form field with comprehensive strategies
   */
  async getFormField(identifier: string | RegExp): Promise<Locator> {
    // Try multiple strategies
    const strategies = [
      () => this.page.getByLabel(identifier),
      () => this.page.getByPlaceholder(identifier),
      () => this.page.locator(`input[name="${identifier}"]`),
      () => this.page.locator(`textarea[name="${identifier}"]`),
      () => this.page.locator(`select[name="${identifier}"]`),
      () => this.page.locator(`[data-testid="${identifier}"]`)
    ];

    for (const strategy of strategies) {
      const locator = strategy();
      if (await locator.count() > 0) {
        return locator;
      }
    }

    return strategies[0]();
  }

  /**
   * Check if element is truly interactive
   */
  async isInteractive(locator: Locator): Promise<boolean> {
    try {
      // Check multiple conditions
      const isVisible = await locator.isVisible();
      const isEnabled = await locator.isEnabled();
      const isEditable = await locator.isEditable().catch(() => true); // Not all elements are editable

      // Check if not obscured
      const box = await locator.boundingBox();
      if (!box) return false;

      // Element should have reasonable size
      const hasSize = box.width > 0 && box.height > 0;

      return isVisible && isEnabled && isEditable && hasSize;
    } catch {
      return false;
    }
  }

  /**
   * Smart click with retry and wait for stability
   */
  async smartClick(locator: Locator, options?: { force?: boolean; retries?: number }): Promise<void> {
    const maxRetries = options?.retries || 3;

    for (let i = 0; i < maxRetries; i++) {
      try {
        // Wait for element to be stable
        await this.waitForElementStable(locator);

        // Check if interactive
        if (!options?.force) {
          const interactive = await this.isInteractive(locator);
          if (!interactive) {
            throw new Error('Element is not interactive');
          }
        }

        // Attempt click
        await locator.click({ force: options?.force });
        return; // Success
      } catch (error) {
        if (i === maxRetries - 1) {
          throw error; // Last retry failed
        }
        await this.page.waitForTimeout(500); // Wait before retry
      }
    }
  }

  /**
   * Smart fill with clear and retry
   */
  async smartFill(locator: Locator, value: string, options?: { clear?: boolean }): Promise<void> {
    // Wait for element to be stable
    await this.waitForElementStable(locator);

    // Clear if requested
    if (options?.clear !== false) {
      // Default to true
      await locator.clear();
    }

    // Fill the value
    await locator.fill(value);

    // Verify the value was set
    const actualValue = await locator.inputValue();
    if (actualValue !== value) {
      // Retry with different method
      await locator.clear();
      await locator.type(value, { delay: 50 });
    }
  }

  /**
   * Wait for loading indicators to disappear
   */
  async waitForLoadingComplete(): Promise<void> {
    // Common loading indicators
    const loadingSelectors = [
      '[data-testid="loading-spinner"]',
      '.loading-spinner',
      '.spinner',
      '[aria-label="loading"]',
      '.skeleton',
      '[data-loading="true"]'
    ];

    for (const selector of loadingSelectors) {
      const loadingElement = this.page.locator(selector);
      if (await loadingElement.count() > 0) {
        await loadingElement.waitFor({ state: 'hidden', timeout: 30000 }).catch(() => {
          // Ignore timeout, element might have disappeared already
        });
      }
    }

    // Also wait for network idle
    await this.page.waitForLoadState('networkidle').catch(() => {
      // Ignore timeout
    });
  }
}

/**
 * Create a locator helper instance
 */
export function createLocatorHelper(page: Page): LocatorHelper {
  return new LocatorHelper(page);
}