import { test, expect } from '@playwright/test';
import { TestHelpers, SELECTORS } from './utils/test-helpers';

test.describe('Dashboard E2E Tests', () => {
  let testHelpers: TestHelpers;

  test.beforeEach(async ({ page }) => {
    testHelpers = new TestHelpers(page);
    // Navigate to the dashboard before each test
    await page.goto('/');
    await testHelpers.waitForPageLoad();
  });

  test('should load the dashboard homepage', async ({ page }) => {
    // Check if the page loads successfully
    await expect(page).toHaveTitle(/ToolBoxAI|Dashboard/);
    
    // Check for common dashboard elements
    await expect(page.locator('body')).toBeVisible();
    
    // Check for console errors
    const errors = await testHelpers.checkConsoleErrors();
    expect(errors).toHaveLength(0);
  });

  test('should have responsive design', async ({ page }) => {
    await testHelpers.testResponsiveDesign();
  });

  test('should handle navigation', async ({ page }) => {
    // Wait for the page to be fully loaded
    await page.waitForLoadState('networkidle');
    
    // Look for navigation elements
    const navigation = page.locator(SELECTORS.NAVIGATION);
    if (await navigation.count() > 0) {
      await expect(navigation).toBeVisible();
    }
  });

  test('should be accessible', async ({ page }) => {
    await testHelpers.checkAccessibility();
  });

  test('should handle authentication flow', async ({ page }) => {
    // Look for authentication-related elements
    const authElements = page.locator(SELECTORS.LOGIN_BUTTON);
    
    if (await authElements.count() > 0) {
      await expect(authElements.first()).toBeVisible();
    }
    
    // The page should load without authentication errors
    await expect(page.locator('body')).toBeVisible();
  });

  test('should handle API calls', async ({ page }) => {
    // Listen for API responses
    const apiResponses: any[] = [];
    page.on('response', response => {
      if (response.url().includes('/api/')) {
        apiResponses.push({
          url: response.url(),
          status: response.status()
        });
      }
    });

    await page.reload();
    await testHelpers.waitForPageLoad();

    // Check that API calls are successful
    const failedApiCalls = apiResponses.filter(r => r.status >= 400);
    expect(failedApiCalls).toHaveLength(0);
  });

  test('should handle loading states', async ({ page }) => {
    // Check for loading indicators
    const loadingElements = page.locator(SELECTORS.LOADING_SPINNER);
    if (await loadingElements.count() > 0) {
      // Loading elements should eventually disappear
      await testHelpers.waitForElementHidden(SELECTORS.LOADING_SPINNER);
    }
  });
});
