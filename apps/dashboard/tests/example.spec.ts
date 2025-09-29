jest.setTimeout(10000);

import { test, expect } from '@playwright/test';

test('basic test: homepage loads', async ({ page }) => {
  await page.goto('https://playwright.dev');
  await expect(page).toHaveTitle(/Playwright/);
});

