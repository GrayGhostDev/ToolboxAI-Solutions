import { test, expect } from '@playwright/test';

test('simple page load test', async ({ page }) => {
  console.log('Starting simple test...');

  // Try to navigate to the login page
  await page.goto('http://localhost:5179/login', {
    waitUntil: 'domcontentloaded',
    timeout: 10000
  });

  console.log('Page loaded, URL:', page.url());

  // Check if we're on the login page
  expect(page.url()).toContain('login');

  // Wait a bit for React to render
  await page.waitForTimeout(2000);

  // Try to find any input fields
  const inputs = await page.locator('input').count();
  console.log('Number of input fields found:', inputs);

  // Expect at least 2 inputs (email and password)
  expect(inputs).toBeGreaterThanOrEqual(2);

  console.log('Test completed successfully!');
});