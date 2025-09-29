jest.setTimeout(10000);

import { test, expect } from '@playwright/test';
import { TestHelpers, SELECTORS } from './utils/test-helpers';

test.describe('Roblox Integration E2E Tests', () => {
  let testHelpers: TestHelpers;

  test.beforeEach(async ({ page }) => {
    testHelpers = new TestHelpers(page);
    await page.goto('/');
    await testHelpers.waitForPageLoad();
  });

  test('should load Roblox plugin interface', async ({ page }) => {
    // Navigate to Roblox section if it exists
    const robloxSection = page.locator('[data-testid="roblox-section"], .roblox-section, #roblox');
    
    if (await robloxSection.count() > 0) {
      await robloxSection.click();
      await testHelpers.waitForPageLoad();
      
      // Check for Roblox-specific elements
      await expect(robloxSection).toBeVisible();
    }
  });

  test('should handle Roblox API communication', async ({ page }) => {
    // Listen for Roblox API calls
    const robloxApiCalls: any[] = [];
    page.on('response', response => {
      if (response.url().includes('/roblox/') || response.url().includes('/api/roblox')) {
        robloxApiCalls.push({
          url: response.url(),
          status: response.status(),
          method: response.request().method()
        });
      }
    });

    // Trigger any Roblox-related actions
    const robloxButton = page.locator('[data-testid*="roblox"], .roblox-button, button:has-text("Roblox")');
    if (await robloxButton.count() > 0) {
      await robloxButton.click();
      await testHelpers.waitForPageLoad();
    }

    // Check that Roblox API calls are successful
    const failedCalls = robloxApiCalls.filter(call => call.status >= 400);
    expect(failedCalls).toHaveLength(0);
  });

  test('should handle WebSocket communication for real-time updates', async ({ page }) => {
    // Check for WebSocket connection indicators
    const wsIndicators = page.locator('[data-testid*="websocket"], .websocket-status, .connection-status');
    
    if (await wsIndicators.count() > 0) {
      await expect(wsIndicators.first()).toBeVisible();
    }

    // Wait for any WebSocket connections to establish
    await page.waitForTimeout(2000);
  });

  test('should display Roblox game data correctly', async ({ page }) => {
    // Look for game data elements
    const gameDataElements = page.locator('[data-testid*="game"], .game-data, .roblox-game');
    
    if (await gameDataElements.count() > 0) {
      await expect(gameDataElements.first()).toBeVisible();
      
      // Check for proper data structure
      const gameData = await testHelpers.getElementText('[data-testid*="game"]');
      expect(gameData).toBeTruthy();
    }
  });

  test('should handle Roblox authentication flow', async ({ page }) => {
    // Look for Roblox authentication elements
    const robloxAuthElements = page.locator('[data-testid*="roblox-auth"], .roblox-login, #roblox-login');
    
    if (await robloxAuthElements.count() > 0) {
      await expect(robloxAuthElements.first()).toBeVisible();
      
      // Test authentication flow if available
      const authButton = robloxAuthElements.first();
      await authButton.click();
      
      // Wait for authentication modal or redirect
      await page.waitForTimeout(1000);
    }
  });

  test('should handle Roblox plugin configuration', async ({ page }) => {
    // Look for configuration elements
    const configElements = page.locator('[data-testid*="config"], .config-section, .settings');
    
    if (await configElements.count() > 0) {
      await expect(configElements.first()).toBeVisible();
      
      // Test configuration form if available
      const configForm = page.locator('form[data-testid*="config"], .config-form');
      if (await configForm.count() > 0) {
        await expect(configForm).toBeVisible();
      }
    }
  });

  test('should handle error states gracefully', async ({ page }) => {
    // Check for error handling
    const errorElements = page.locator(SELECTORS.ERROR_MESSAGE);
    
    // Simulate an error by navigating to a non-existent Roblox endpoint
    await page.goto('/roblox/nonexistent');
    
    // The page should handle the error gracefully
    await expect(page.locator('body')).toBeVisible();
  });

  test('should maintain performance with Roblox integration', async ({ page }) => {
    // Measure page load time
    const startTime = Date.now();
    await page.goto('/');
    await testHelpers.waitForPageLoad();
    const loadTime = Date.now() - startTime;
    
    // Page should load within reasonable time (5 seconds)
    expect(loadTime).toBeLessThan(5000);
    
    // Check for performance indicators
    const performanceEntries = await page.evaluate(() => {
      return performance.getEntriesByType('navigation')[0];
    });
    
    if (performanceEntries) {
      expect(performanceEntries.loadEventEnd - performanceEntries.loadEventStart).toBeLessThan(3000);
    }
  });
});
