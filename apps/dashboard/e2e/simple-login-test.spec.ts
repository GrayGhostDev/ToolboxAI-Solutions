import { test, expect } from '@playwright/test';

test('login page has email field', async ({ page }) => {
  // Disable timeout for debugging
  test.setTimeout(60000);

  // Go to login with explicit wait
  await page.goto('http://localhost:5179/login', {
    waitUntil: 'networkidle',
    timeout: 30000
  });

  // Debug: Log the page title
  const title = await page.title();
  console.log('Page title:', title);

  // Debug: Log the URL
  const url = page.url();
  console.log('Current URL:', url);

  // Debug: Take a screenshot
  await page.screenshot({ path: 'login-page-debug.png' });

  // Look for email field with different selectors
  const emailField = await page.locator('input[name="email"], input[type="email"], [data-testid="email-input"]').first();

  // Check if the field exists
  const fieldExists = await emailField.count() > 0;
  console.log('Email field exists:', fieldExists);

  if (fieldExists) {
    // Verify the field is visible
    await expect(emailField).toBeVisible();
    console.log('Email field is visible');

    // Get field attributes
    const name = await emailField.getAttribute('name');
    const type = await emailField.getAttribute('type');
    console.log('Field name:', name, 'Field type:', type);
  } else {
    // Log all input fields found
    const allInputs = await page.locator('input').all();
    console.log('Total input fields found:', allInputs.length);

    for (let i = 0; i < allInputs.length; i++) {
      const input = allInputs[i];
      const inputName = await input.getAttribute('name');
      const inputType = await input.getAttribute('type');
      const inputId = await input.getAttribute('id');
      console.log(`Input ${i}: name="${inputName}" type="${inputType}" id="${inputId}"`);
    }
  }

  // Expect email field to exist
  expect(fieldExists).toBeTruthy();
});