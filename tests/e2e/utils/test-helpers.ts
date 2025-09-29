import { Page, expect } from '@playwright/test';

export class TestHelpers {
  constructor(private page: Page) {}

  /**
   * Wait for the page to be fully loaded
   */
  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
    await this.page.waitForLoadState('domcontentloaded');
  }

  /**
   * Wait for a specific element to be visible
   */
  async waitForElement(selector: string, timeout = 10000) {
    await this.page.waitForSelector(selector, { state: 'visible', timeout });
  }

  /**
   * Wait for an element to be hidden
   */
  async waitForElementHidden(selector: string, timeout = 10000) {
    await this.page.waitForSelector(selector, { state: 'hidden', timeout });
  }

  /**
   * Check if an element exists on the page
   */
  async elementExists(selector: string): Promise<boolean> {
    return (await this.page.locator(selector).count()) > 0;
  }

  /**
   * Get text content of an element
   */
  async getElementText(selector: string): Promise<string> {
    return await this.page.locator(selector).textContent() || '';
  }

  /**
   * Click an element and wait for navigation if needed
   */
  async clickAndWait(selector: string, waitForNavigation = false) {
    if (waitForNavigation) {
      await Promise.all([
        this.page.waitForNavigation(),
        this.page.click(selector)
      ]);
    } else {
      await this.page.click(selector);
    }
  }

  /**
   * Fill a form field
   */
  async fillField(selector: string, value: string) {
    await this.page.fill(selector, value);
  }

  /**
   * Select an option from a dropdown
   */
  async selectOption(selector: string, value: string) {
    await this.page.selectOption(selector, value);
  }

  /**
   * Take a screenshot
   */
  async takeScreenshot(name: string) {
    await this.page.screenshot({ path: `test-results/screenshots/${name}.png` });
  }

  /**
   * Check for console errors
   */
  async checkConsoleErrors(): Promise<string[]> {
    const errors: string[] = [];
    
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    return errors;
  }

  /**
   * Wait for API calls to complete
   */
  async waitForApiCalls(apiPattern: string | RegExp) {
    await this.page.waitForResponse(response => {
      const url = response.url();
      if (typeof apiPattern === 'string') {
        return url.includes(apiPattern);
      }
      return apiPattern.test(url);
    });
  }

  /**
   * Mock API responses
   */
  async mockApiResponse(url: string | RegExp, response: any) {
    await this.page.route(url, route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(response)
      });
    });
  }

  /**
   * Check accessibility basics
   */
  async checkAccessibility() {
    // Check for proper heading structure
    const h1Count = await this.page.locator('h1').count();
    expect(h1Count).toBeGreaterThan(0);

    // Check for alt text on images
    const images = this.page.locator('img');
    const imageCount = await images.count();
    for (let i = 0; i < imageCount; i++) {
      const alt = await images.nth(i).getAttribute('alt');
      expect(alt).toBeTruthy();
    }

    // Check for proper form labels
    const inputs = this.page.locator('input[type="text"], input[type="email"], input[type="password"]');
    const inputCount = await inputs.count();
    for (let i = 0; i < inputCount; i++) {
      const input = inputs.nth(i);
      const id = await input.getAttribute('id');
      if (id) {
        const label = this.page.locator(`label[for="${id}"]`);
        expect(await label.count()).toBeGreaterThan(0);
      }
    }
  }

  /**
   * Test responsive design
   */
  async testResponsiveDesign() {
    const viewports = [
      { width: 1920, height: 1080, name: 'Desktop' },
      { width: 1024, height: 768, name: 'Tablet' },
      { width: 375, height: 667, name: 'Mobile' }
    ];

    for (const viewport of viewports) {
      await this.page.setViewportSize({ width: viewport.width, height: viewport.height });
      await this.page.waitForTimeout(500); // Allow for layout adjustments
      
      // Check that the page is still visible and functional
      await expect(this.page.locator('body')).toBeVisible();
    }
  }
}

/**
 * Common selectors for the ToolBoxAI dashboard
 */
export const SELECTORS = {
  // Navigation
  NAVIGATION: 'nav, [role="navigation"], .navigation',
  MAIN_MENU: '.main-menu, [data-testid="main-menu"]',
  
  // Authentication
  LOGIN_BUTTON: '[data-testid="login-button"], .login-button, #login',
  LOGOUT_BUTTON: '[data-testid="logout-button"], .logout-button, #logout',
  USER_MENU: '[data-testid="user-menu"], .user-menu',
  
  // Dashboard elements
  DASHBOARD_HEADER: '.dashboard-header, [data-testid="dashboard-header"]',
  DASHBOARD_CONTENT: '.dashboard-content, [data-testid="dashboard-content"]',
  SIDEBAR: '.sidebar, [data-testid="sidebar"]',
  
  // Forms
  FORM: 'form',
  INPUT: 'input',
  BUTTON: 'button',
  SELECT: 'select',
  
  // Loading states
  LOADING_SPINNER: '.loading, .spinner, [data-testid="loading"]',
  LOADING_OVERLAY: '.loading-overlay, [data-testid="loading-overlay"]',
  
  // Error states
  ERROR_MESSAGE: '.error, .error-message, [data-testid="error"]',
  SUCCESS_MESSAGE: '.success, .success-message, [data-testid="success"]',
  
  // Common UI elements
  MODAL: '.modal, [role="dialog"]',
  TOAST: '.toast, [role="alert"]',
  DROPDOWN: '.dropdown, [role="listbox"]',
  TAB: '[role="tab"]',
  TAB_PANEL: '[role="tabpanel"]'
} as const;
