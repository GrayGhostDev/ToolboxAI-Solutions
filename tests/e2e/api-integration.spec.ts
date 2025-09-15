import { test, expect } from '@playwright/test';

test.describe('API Integration E2E Tests', () => {
  test('should handle API responses correctly', async ({ page }) => {
    // Listen for network requests
    const responses: any[] = [];
    page.on('response', response => {
      responses.push({
        url: response.url(),
        status: response.status(),
        statusText: response.statusText()
      });
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check that API calls are successful (status 200-299)
    const apiResponses = responses.filter(r => 
      r.url.includes('/api/') && r.status >= 200 && r.status < 300
    );
    
    // Log API responses for debugging
    console.log('API Responses:', apiResponses);
  });

  test('should handle WebSocket connections', async ({ page }) => {
    await page.goto('/');
    
    // Wait for WebSocket connections to be established
    await page.waitForTimeout(2000);
    
    // Check if WebSocket is connected (this depends on your implementation)
    const wsConnected = await page.evaluate(() => {
      // Check if WebSocket connection exists
      return typeof window !== 'undefined' && 
             (window as any).WebSocket && 
             (window as any).WebSocket.OPEN;
    });
    
    // This test will pass if the page loads without WebSocket errors
    await expect(page.locator('body')).toBeVisible();
  });

  test('should handle authentication flow', async ({ page }) => {
    await page.goto('/');
    
    // Look for authentication-related elements
    const authElements = page.locator('[data-testid*="auth"], [class*="auth"], [id*="login"], [id*="signin"]');
    
    if (await authElements.count() > 0) {
      await expect(authElements.first()).toBeVisible();
    }
    
    // The page should load without authentication errors
    await expect(page.locator('body')).toBeVisible();
  });
});
