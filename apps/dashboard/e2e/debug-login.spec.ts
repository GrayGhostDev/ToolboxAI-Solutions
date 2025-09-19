import { test } from '@playwright/test';

test('debug login page', async ({ page }) => {
  // Navigate to login
  await page.goto('http://localhost:5179/login');

  // Wait for page to load
  await page.waitForLoadState('networkidle');

  // Take screenshot
  await page.screenshot({ path: 'login-page-debug.png' });

  // Log all visible text
  const allText = await page.locator('body').innerText();
  console.log('=== Page Text ===');
  console.log(allText);

  // Log all headings
  const headings = await page.locator('h1, h2, h3, h4').allTextContents();
  console.log('\n=== Headings ===');
  console.log(headings);

  // Log all labels
  const labels = await page.locator('label').allTextContents();
  console.log('\n=== Labels ===');
  console.log(labels);

  // Log all buttons
  const buttons = await page.locator('button').allTextContents();
  console.log('\n=== Buttons ===');
  console.log(buttons);

  // Check for email inputs with various selectors
  console.log('\n=== Email Input Search ===');
  console.log('By label:', await page.getByLabel(/username or email/i).count());
  console.log('By label (exact):', await page.getByLabel('Username or Email').count());
  console.log('By type=email:', await page.locator('input[type="email"]').count());
  console.log('By name=email:', await page.locator('input[name="email"]').count());
  console.log('By data-testid:', await page.locator('[data-testid="email-input"]').count());
  console.log('All inputs:', await page.locator('input').count());

  // Check input attributes
  const inputs = await page.locator('input').all();
  console.log('\n=== Input Details ===');
  for (let i = 0; i < inputs.length; i++) {
    const input = inputs[i];
    const type = await input.getAttribute('type');
    const name = await input.getAttribute('name');
    const id = await input.getAttribute('id');
    const placeholder = await input.getAttribute('placeholder');
    const testId = await input.getAttribute('data-testid');
    console.log(`Input ${i}: type=${type}, name=${name}, id=${id}, placeholder=${placeholder}, data-testid=${testId}`);
  }

  // Check if we're actually on login page or redirected
  const currentUrl = page.url();
  console.log('\n=== Current URL ===');
  console.log(currentUrl);
});