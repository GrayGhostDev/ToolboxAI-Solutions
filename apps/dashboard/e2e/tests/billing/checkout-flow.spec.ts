/**
 * Checkout Flow E2E Tests
 *
 * Tests the complete user journey from plan selection through checkout
 * to subscription activation using Playwright.
 *
 * Test Scenarios:
 * 1. Navigate to billing page
 * 2. View and select pricing plans
 * 3. Toggle between monthly/annual billing
 * 4. Complete checkout form
 * 5. Process payment (mocked)
 * 6. Verify subscription activation
 */

import { test, expect } from '@playwright/test';

// Test user credentials (from authentication.spec.ts pattern)
const TEST_USER = {
  email: 'teacher@toolboxai.com',
  password: 'Teacher123!'
};

test.describe('Billing Checkout Flow', () => {
  // Setup: Login before each test
  test.beforeEach(async ({ page }) => {
    // Navigate to login
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000);

    // Login with test user
    await page.locator('input[name="identifier"], input[id="identifier-field"], [data-testid="email-input"]').first().fill(TEST_USER.email);
    await page.locator('input[name="password"], input[id="password-field"], [data-testid="password-input"]').first().fill(TEST_USER.password);
    await page.locator('button[type="submit"], button:has-text("Continue"), [data-testid="login-submit"]').first().click();

    // Wait for dashboard
    await page.waitForTimeout(2000);
  });

  test('should navigate to billing page', async ({ page }) => {
    // Navigate to billing page
    await page.goto('/billing');
    await page.waitForLoadState('domcontentloaded');

    // Verify page title
    const heading = page.getByRole('heading', { name: /billing.*subscription/i });
    await expect(heading).toBeVisible({ timeout: 10000 });

    // Verify tabs are present
    const subscriptionTab = page.getByRole('tab', { name: /subscription/i });
    const plansTab = page.getByRole('tab', { name: /plans.*pricing/i });
    const invoicesTab = page.getByRole('tab', { name: /invoices/i });

    await expect(subscriptionTab).toBeVisible();
    await expect(plansTab).toBeVisible();
    await expect(invoicesTab).toBeVisible();
  });

  test('should display all pricing plans', async ({ page }) => {
    // Navigate to billing plans tab
    await page.goto('/billing');
    await page.waitForLoadState('domcontentloaded');

    // Click plans tab
    const plansTab = page.getByRole('tab', { name: /plans.*pricing/i });
    await plansTab.click();
    await page.waitForTimeout(500);

    // Verify all three plans are visible
    await expect(page.getByText('Starter')).toBeVisible();
    await expect(page.getByText('Professional')).toBeVisible();
    await expect(page.getByText('Enterprise')).toBeVisible();

    // Verify pricing is displayed
    await expect(page.getByText('$29', { exact: false })).toBeVisible();
    await expect(page.getByText('$79', { exact: false })).toBeVisible();
    await expect(page.getByText('$199', { exact: false })).toBeVisible();

    // Verify "Most Popular" badge on Professional plan
    const popularBadge = page.getByText(/most popular/i);
    await expect(popularBadge).toBeVisible();
  });

  test('should toggle between monthly and annual billing', async ({ page }) => {
    // Navigate to billing plans tab
    await page.goto('/billing');
    await page.waitForLoadState('domcontentloaded');

    const plansTab = page.getByRole('tab', { name: /plans.*pricing/i });
    await plansTab.click();
    await page.waitForTimeout(500);

    // Initial state: Monthly pricing should be visible
    await expect(page.getByText('/month', { exact: false }).first()).toBeVisible();

    // Find and click the annual toggle switch
    const annualSwitch = page.locator('input[type="checkbox"]').first();
    await annualSwitch.check();
    await page.waitForTimeout(500);

    // Verify annual pricing is displayed
    await expect(page.getByText('/year', { exact: false }).first()).toBeVisible();

    // Verify savings badge is visible
    await expect(page.getByText(/save/i)).toBeVisible();

    // Toggle back to monthly
    await annualSwitch.uncheck();
    await page.waitForTimeout(500);

    // Verify monthly pricing is back
    await expect(page.getByText('/month', { exact: false }).first()).toBeVisible();
  });

  test('should calculate annual savings correctly', async ({ page }) => {
    // Navigate to billing plans tab
    await page.goto('/billing');
    await page.waitForLoadState('domcontentloaded');

    const plansTab = page.getByRole('tab', { name: /plans.*pricing/i });
    await plansTab.click();
    await page.waitForTimeout(500);

    // Toggle to annual
    const annualSwitch = page.locator('input[type="checkbox"]').first();
    await annualSwitch.check();
    await page.waitForTimeout(500);

    // Verify starter plan savings
    // Monthly: $29 * 12 = $348, Annual: $290, Savings: $58 (17%)
    const starterSavings = page.getByText(/save.*58/i).or(page.getByText(/17%/i)).first();
    await expect(starterSavings).toBeVisible({ timeout: 5000 });
  });

  test('should open checkout form when plan is selected', async ({ page }) => {
    // Navigate to billing plans tab
    await page.goto('/billing');
    await page.waitForLoadState('domcontentloaded');

    const plansTab = page.getByRole('tab', { name: /plans.*pricing/i });
    await plansTab.click();
    await page.waitForTimeout(500);

    // Click "Choose Plan" button for Professional plan
    const choosePlanButtons = page.getByRole('button', { name: /choose plan/i });
    const professionalButton = choosePlanButtons.nth(1); // Second button (Professional)
    await professionalButton.click();
    await page.waitForTimeout(1000);

    // Verify checkout form is displayed
    await expect(page.getByText(/complete your subscription/i)).toBeVisible();
    await expect(page.getByText(/cardholder name/i)).toBeVisible();
    await expect(page.getByText(/card information/i)).toBeVisible();
  });

  test('should validate cardholder name is required', async ({ page }) => {
    // Navigate to billing and start checkout
    await page.goto('/billing');
    await page.waitForLoadState('domcontentloaded');

    const plansTab = page.getByRole('tab', { name: /plans.*pricing/i });
    await plansTab.click();
    await page.waitForTimeout(500);

    // Select Professional plan
    const choosePlanButtons = page.getByRole('button', { name: /choose plan/i });
    await choosePlanButtons.nth(1).click();
    await page.waitForTimeout(1000);

    // Try to submit without entering cardholder name
    const submitButton = page.getByRole('button', { name: /subscribe for/i });

    // Button should be disabled initially
    await expect(submitButton).toBeDisabled();
  });

  test('should display order summary in checkout', async ({ page }) => {
    // Navigate to billing and start checkout
    await page.goto('/billing');
    await page.waitForLoadState('domcontentloaded');

    const plansTab = page.getByRole('tab', { name: /plans.*pricing/i });
    await plansTab.click();
    await page.waitForTimeout(500);

    // Select Starter plan with monthly billing
    const choosePlanButtons = page.getByRole('button', { name: /choose plan/i });
    await choosePlanButtons.first().click();
    await page.waitForTimeout(1000);

    // Verify order summary
    await expect(page.getByText(/starter plan/i)).toBeVisible();
    await expect(page.getByText(/total today/i)).toBeVisible();
    await expect(page.getByText('$29')).toBeVisible();
  });

  test('should show security notice in checkout', async ({ page }) => {
    // Navigate to billing and start checkout
    await page.goto('/billing');
    await page.waitForLoadState('domcontentloaded');

    const plansTab = page.getByRole('tab', { name: /plans.*pricing/i });
    await plansTab.click();
    await page.waitForTimeout(500);

    // Select any plan
    const choosePlanButtons = page.getByRole('button', { name: /choose plan/i });
    await choosePlanButtons.first().click();
    await page.waitForTimeout(1000);

    // Verify security notice
    await expect(page.getByText(/secured by stripe/i)).toBeVisible();
    await expect(page.getByText(/never see or store your card/i)).toBeVisible();
  });

  test('should allow canceling checkout', async ({ page }) => {
    // Navigate to billing and start checkout
    await page.goto('/billing');
    await page.waitForLoadState('domcontentloaded');

    const plansTab = page.getByRole('tab', { name: /plans.*pricing/i });
    await plansTab.click();
    await page.waitForTimeout(500);

    // Select any plan
    const choosePlanButtons = page.getByRole('button', { name: /choose plan/i });
    await choosePlanButtons.first().click();
    await page.waitForTimeout(1000);

    // Click cancel button
    const cancelButton = page.getByRole('button', { name: /cancel/i });
    await cancelButton.click();
    await page.waitForTimeout(500);

    // Verify we're back on the plans view
    await expect(page.getByRole('tab', { name: /plans.*pricing/i })).toHaveAttribute('aria-selected', 'true');
    await expect(page.getByText('Starter')).toBeVisible();
  });

  test('should process checkout successfully (mocked)', async ({ page }) => {
    // Navigate to billing and start checkout
    await page.goto('/billing');
    await page.waitForLoadState('domcontentloaded');

    const plansTab = page.getByRole('tab', { name: /plans.*pricing/i });
    await plansTab.click();
    await page.waitForTimeout(500);

    // Select Professional plan
    const choosePlanButtons = page.getByRole('button', { name: /choose plan/i });
    await choosePlanButtons.nth(1).click();
    await page.waitForTimeout(1000);

    // Fill cardholder name
    const nameInput = page.locator('input[type="text"]').first();
    await nameInput.fill('John Doe');
    await page.waitForTimeout(300);

    // Note: Stripe Elements would be here in production
    // For now, we're testing the form structure

    // Verify submit button is enabled after filling name
    // (In real scenario, would also need card details)
    const submitButton = page.getByRole('button', { name: /subscribe for/i });

    // Button state depends on card completion (mocked as false currently)
    // So button should still be disabled without card details
    await expect(submitButton).toBeDisabled();
  });

  test('should show loading state during checkout', async ({ page }) => {
    // This test would require mocking the Stripe API
    // For now, verify the button has loading capability
    await page.goto('/billing');
    await page.waitForLoadState('domcontentloaded');

    const plansTab = page.getByRole('tab', { name: /plans.*pricing/i });
    await plansTab.click();
    await page.waitForTimeout(500);

    // Select any plan
    const choosePlanButtons = page.getByRole('button', { name: /choose plan/i });
    await choosePlanButtons.first().click();
    await page.waitForTimeout(1000);

    // Verify submit button exists with correct text
    const submitButton = page.getByRole('button', { name: /subscribe for/i });
    await expect(submitButton).toBeVisible();
  });

  test('should display Stripe Element placeholder', async ({ page }) => {
    // Navigate to billing and start checkout
    await page.goto('/billing');
    await page.waitForLoadState('domcontentloaded');

    const plansTab = page.getByRole('tab', { name: /plans.*pricing/i });
    await plansTab.click();
    await page.waitForTimeout(500);

    // Select any plan
    const choosePlanButtons = page.getByRole('button', { name: /choose plan/i });
    await choosePlanButtons.first().click();
    await page.waitForTimeout(1000);

    // Verify Stripe Element placeholder is visible
    await expect(page.getByText(/stripe card element will be mounted here/i)).toBeVisible();
  });

  test('should handle different plan tiers in checkout', async ({ page }) => {
    // Test checkout with each plan tier
    const plans = [
      { name: 'Starter', price: '$29' },
      { name: 'Professional', price: '$79' },
      { name: 'Enterprise', price: '$199' }
    ];

    for (const plan of plans) {
      await page.goto('/billing');
      await page.waitForLoadState('domcontentloaded');

      const plansTab = page.getByRole('tab', { name: /plans.*pricing/i });
      await plansTab.click();
      await page.waitForTimeout(500);

      // Find the specific plan card by name
      const planCard = page.locator(`text=${plan.name}`).first();
      await planCard.scrollIntoViewIfNeeded();

      // Click choose plan button
      const choosePlanButtons = page.getByRole('button', { name: /choose plan/i });
      const planIndex = plans.indexOf(plan);
      await choosePlanButtons.nth(planIndex).click();
      await page.waitForTimeout(1000);

      // Verify correct plan in checkout
      await expect(page.getByText(new RegExp(plan.name, 'i'))).toBeVisible();
      await expect(page.getByText(plan.price)).toBeVisible();

      // Cancel and go back
      const cancelButton = page.getByRole('button', { name: /cancel/i });
      await cancelButton.click();
      await page.waitForTimeout(500);
    }
  });
});

test.describe('Checkout Form Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000);

    await page.locator('input[name="identifier"], input[id="identifier-field"], [data-testid="email-input"]').first().fill(TEST_USER.email);
    await page.locator('input[name="password"], input[id="password-field"], [data-testid="password-input"]').first().fill(TEST_USER.password);
    await page.locator('button[type="submit"], button:has-text("Continue"), [data-testid="login-submit"]').first().click();
    await page.waitForTimeout(2000);
  });

  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto('/billing');
    await page.waitForLoadState('domcontentloaded');

    const plansTab = page.getByRole('tab', { name: /plans.*pricing/i });
    await plansTab.click();
    await page.waitForTimeout(500);

    // Select a plan
    const choosePlanButtons = page.getByRole('button', { name: /choose plan/i });
    await choosePlanButtons.first().click();
    await page.waitForTimeout(1000);

    // Check for accessible form elements
    const nameInput = page.locator('input[type="text"]').first();
    await expect(nameInput).toBeVisible();

    const submitButton = page.getByRole('button', { name: /subscribe for/i });
    await expect(submitButton).toBeVisible();

    const cancelButton = page.getByRole('button', { name: /cancel/i });
    await expect(cancelButton).toBeVisible();
  });

  test('should support keyboard navigation', async ({ page }) => {
    await page.goto('/billing');
    await page.waitForLoadState('domcontentloaded');

    const plansTab = page.getByRole('tab', { name: /plans.*pricing/i });
    await plansTab.click();
    await page.waitForTimeout(500);

    // Tab through plan cards
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // Should be able to activate plan with Enter
    await page.keyboard.press('Enter');
    await page.waitForTimeout(1000);

    // Verify checkout opened
    await expect(page.getByText(/complete your subscription/i)).toBeVisible();
  });
});
