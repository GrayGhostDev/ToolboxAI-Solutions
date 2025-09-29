

import { test, expect } from '@playwright/test';

test('check login page content', async ({ page }) => {
  // Navigate to login page
  await page.goto('http://localhost:5179/login');
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(2000);

  // Take screenshot
  await page.screenshot({ path: 'login-page.png', fullPage: true });

  // Get all text content
  const pageText = await page.textContent('body');
  console.log('Page text:', pageText);

  // Try different heading selectors
  console.log('\n=== Heading Search ===');

  const h1 = await page.locator('h1').count();
  const h2 = await page.locator('h2').count();
  const h3 = await page.locator('h3').count();
  const h4 = await page.locator('h4').count();

  console.log(`h1 count: ${h1}`);
  console.log(`h2 count: ${h2}`);
  console.log(`h3 count: ${h3}`);
  console.log(`h4 count: ${h4}`);

  if (h4 > 0) {
    const h4Text = await page.locator('h4').first().textContent();
    console.log(`h4 text: "${h4Text}"`);
  }

  // Check for inputs
  console.log('\n=== Input Search ===');
  const emailInputCount = await page.locator('input[name="identifier"]').count();
  const passwordInputCount = await page.locator('input[name="password"]').count();
  const emailTestId = await page.locator('[data-testid="email-input"]').count();
  const passwordTestId = await page.locator('[data-testid="password-input"]').count();

  console.log(`input[name="identifier"]: ${emailInputCount}`);
  console.log(`input[name="password"]: ${passwordInputCount}`);
  console.log(`[data-testid="email-input"]: ${emailTestId}`);
  console.log(`[data-testid="password-input"]: ${passwordTestId}`);

  // Check for buttons
  console.log('\n=== Button Search ===');
  const submitButton = await page.locator('button[type="submit"]').count();
  const loginTestId = await page.locator('[data-testid="login-submit"]').count();

  console.log(`button[type="submit"]: ${submitButton}`);
  console.log(`[data-testid="login-submit"]: ${loginTestId}`);

  // Check if there's any text containing "Welcome"
  const welcomeText = await page.locator('*:has-text("Welcome")').count();
  console.log(`\nElements containing "Welcome": ${welcomeText}`);

  // Basic assertion
  expect(emailInputCount).toBeGreaterThan(0);
  expect(passwordInputCount).toBeGreaterThan(0);
});