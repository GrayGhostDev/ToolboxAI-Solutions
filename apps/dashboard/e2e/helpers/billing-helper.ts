import { Page, expect } from '@playwright/test';

/**
 * Billing E2E Test Helpers
 *
 * Reusable utility functions for billing-related E2E tests.
 * These helpers reduce code duplication and improve test maintainability.
 */

// Test user credentials
export const TEST_USERS = {
  teacher: {
    email: 'teacher@example.com',
    password: 'password123',
    role: 'teacher',
  },
  admin: {
    email: 'admin@example.com',
    password: 'admin123',
    role: 'admin',
  },
  student: {
    email: 'student@example.com',
    password: 'student123',
    role: 'student',
  },
};

// Billing plan types
export const BILLING_PLANS = {
  starter: {
    id: 'starter',
    name: 'Starter',
    monthlyPrice: '$29',
    annualPrice: '$290',
  },
  professional: {
    id: 'professional',
    name: 'Professional',
    monthlyPrice: '$79',
    annualPrice: '$790',
  },
  enterprise: {
    id: 'enterprise',
    name: 'Enterprise',
    monthlyPrice: '$199',
    annualPrice: '$1990',
  },
};

// Test card details (test mode Stripe cards)
export const TEST_CARDS = {
  valid: {
    number: '4242424242424242',
    expiry: '12/26',
    cvc: '123',
    zip: '12345',
  },
  declined: {
    number: '4000000000000002',
    expiry: '12/26',
    cvc: '123',
    zip: '12345',
  },
  insufficientFunds: {
    number: '4000000000009995',
    expiry: '12/26',
    cvc: '123',
    zip: '12345',
  },
};

/**
 * Authentication Helpers
 */

/**
 * Login as a specific user role
 * @param page Playwright page object
 * @param role User role (teacher, admin, student)
 */
export async function loginAsUser(page: Page, role: keyof typeof TEST_USERS = 'teacher'): Promise<void> {
  const user = TEST_USERS[role];

  // Navigate to login page
  await page.goto('/login');

  // Wait for login form
  await page.waitForSelector('input[name="identifier"]', { timeout: 10000 });

  // Fill credentials
  await page.locator('input[name="identifier"]').first().fill(user.email);
  await page.locator('input[name="password"]').first().fill(user.password);

  // Submit form
  await page.locator('button[type="submit"]').first().click();

  // Wait for navigation
  await page.waitForTimeout(2000);
}

/**
 * Login as teacher (default test user)
 * @param page Playwright page object
 */
export async function loginAsTeacher(page: Page): Promise<void> {
  await loginAsUser(page, 'teacher');
}

/**
 * Navigation Helpers
 */

/**
 * Navigate to billing page
 * @param page Playwright page object
 */
export async function navigateToBilling(page: Page): Promise<void> {
  await page.goto('/billing');
  await page.waitForLoadState('networkidle');
}

/**
 * Navigate to specific billing tab
 * @param page Playwright page object
 * @param tab Tab name (plans, subscription, checkout)
 */
export async function navigateToBillingTab(page: Page, tab: 'plans' | 'subscription' | 'checkout'): Promise<void> {
  await navigateToBilling(page);

  const tabPatterns = {
    plans: /plans.*pricing/i,
    subscription: /subscription|manage/i,
    checkout: /checkout|payment/i,
  };

  const tabLocator = page.getByRole('tab', { name: tabPatterns[tab] });

  if (await tabLocator.isVisible().catch(() => false)) {
    await tabLocator.click();
    await page.waitForTimeout(1000);
  }
}

/**
 * Pricing Plans Helpers
 */

/**
 * Select a billing plan
 * @param page Playwright page object
 * @param planName Plan name (Starter, Professional, Enterprise)
 */
export async function selectPlan(page: Page, planName: keyof typeof BILLING_PLANS): Promise<void> {
  const plan = BILLING_PLANS[planName];

  // Find plan card
  const planCard = page.locator('[data-testid*="plan-card"], .plan-card, [class*="PlanCard"]')
    .filter({ hasText: plan.name })
    .first();

  // Click "Choose Plan" button
  const selectButton = planCard.locator(
    'button:has-text("Choose Plan"), button:has-text("Get Started"), button:has-text("Select")'
  ).first();

  await selectButton.click();
  await page.waitForTimeout(1500);
}

/**
 * Toggle billing interval
 * @param page Playwright page object
 * @param interval Billing interval (monthly or annual)
 */
export async function toggleBillingInterval(page: Page, interval: 'monthly' | 'annual'): Promise<void> {
  const toggleLocator = page.getByRole('button', { name: new RegExp(interval, 'i') }).or(
    page.locator(`[data-testid*="${interval}"], [class*="${interval}"]`).first()
  );

  const hasToggle = await toggleLocator.isVisible().catch(() => false);

  if (hasToggle) {
    await toggleLocator.click();
    await page.waitForTimeout(500);
  }
}

/**
 * Verify plan pricing is displayed
 * @param page Playwright page object
 * @param planName Plan name
 * @param interval Billing interval
 */
export async function verifyPlanPricing(
  page: Page,
  planName: keyof typeof BILLING_PLANS,
  interval: 'monthly' | 'annual'
): Promise<void> {
  const plan = BILLING_PLANS[planName];
  const expectedPrice = interval === 'monthly' ? plan.monthlyPrice : plan.annualPrice;

  const priceElement = page.locator(`text=${expectedPrice.replace('$', '\\$')}`).first();
  await expect(priceElement).toBeVisible();
}

/**
 * Checkout Form Helpers
 */

/**
 * Fill checkout form with card details
 * @param page Playwright page object
 * @param cardType Type of test card to use
 */
export async function fillCheckoutForm(page: Page, cardType: keyof typeof TEST_CARDS = 'valid'): Promise<void> {
  const card = TEST_CARDS[cardType];

  // Card number
  const cardNumberInput = page.locator('input[name="cardNumber"], input[placeholder*="card number"]').first();
  if (await cardNumberInput.isVisible().catch(() => false)) {
    await cardNumberInput.fill(card.number);
  }

  // Expiry date
  const expiryInput = page.locator('input[name="expiry"], input[placeholder*="expiry"], input[placeholder*="MM/YY"]').first();
  if (await expiryInput.isVisible().catch(() => false)) {
    await expiryInput.fill(card.expiry);
  }

  // CVC
  const cvcInput = page.locator('input[name="cvc"], input[placeholder*="CVC"], input[placeholder*="CVV"]').first();
  if (await cvcInput.isVisible().catch(() => false)) {
    await cvcInput.fill(card.cvc);
  }

  // Zip code
  const zipInput = page.locator('input[name="zip"], input[name="postalCode"], input[placeholder*="zip"]').first();
  if (await zipInput.isVisible().catch(() => false)) {
    await zipInput.fill(card.zip);
  }
}

/**
 * Submit checkout form
 * @param page Playwright page object
 */
export async function submitCheckoutForm(page: Page): Promise<void> {
  const submitButton = page.locator('button[type="submit"]:has-text("Pay"), button:has-text("Subscribe"), button:has-text("Complete")').first();

  await submitButton.click();
  await page.waitForTimeout(2000);
}

/**
 * Verify checkout form validation errors
 * @param page Playwright page object
 * @param expectedErrors Array of expected error messages
 */
export async function verifyCheckoutFormErrors(page: Page, expectedErrors: string[]): Promise<void> {
  for (const errorText of expectedErrors) {
    const errorElement = page.locator(`text=/${errorText}/i`).first();
    await expect(errorElement).toBeVisible();
  }
}

/**
 * Verify order summary displays selected plan
 * @param page Playwright page object
 * @param planName Expected plan name in order summary
 */
export async function verifyOrderSummary(page: Page, planName: keyof typeof BILLING_PLANS): Promise<void> {
  const plan = BILLING_PLANS[planName];

  // Find order summary section
  const orderSummary = page.locator('[data-testid*="order-summary"], [class*="order-summary"], [class*="summary"]').first();

  // Verify plan name in summary
  const planNameInSummary = orderSummary.locator(`text=/${plan.name}/i`).first();
  await expect(planNameInSummary).toBeVisible();
}

/**
 * Subscription Management Helpers
 */

/**
 * Check if user has active subscription
 * @param page Playwright page object
 * @returns True if user has active subscription
 */
export async function hasActiveSubscription(page: Page): Promise<boolean> {
  await navigateToBillingTab(page, 'subscription');

  const noSubscriptionMessage = page.getByText(/no active subscription/i);
  const hasNoSubscription = await noSubscriptionMessage.isVisible().catch(() => false);

  return !hasNoSubscription;
}

/**
 * Verify subscription details are displayed
 * @param page Playwright page object
 * @param expectedPlan Expected plan name
 */
export async function verifySubscriptionDetails(page: Page, expectedPlan: keyof typeof BILLING_PLANS): Promise<void> {
  const plan = BILLING_PLANS[expectedPlan];

  // Verify plan name
  const planName = page.getByText(plan.name).first();
  await expect(planName).toBeVisible();

  // Verify status badge
  const statusBadge = page.locator('text=/active|trial|cancelled/i').first();
  await expect(statusBadge).toBeVisible();
}

/**
 * Cancel subscription
 * @param page Playwright page object
 */
export async function cancelSubscription(page: Page): Promise<void> {
  await navigateToBillingTab(page, 'subscription');

  // Find cancel button
  const cancelButton = page.locator('button:has-text("Cancel"), button:has-text("Cancel Subscription")').first();

  if (await cancelButton.isVisible().catch(() => false)) {
    await cancelButton.click();
    await page.waitForTimeout(500);

    // Confirm cancellation if modal appears
    const confirmButton = page.locator('button:has-text("Confirm"), button:has-text("Yes")').first();
    if (await confirmButton.isVisible().catch(() => false)) {
      await confirmButton.click();
      await page.waitForTimeout(1500);
    }
  }
}

/**
 * Reactivate subscription
 * @param page Playwright page object
 */
export async function reactivateSubscription(page: Page): Promise<void> {
  await navigateToBillingTab(page, 'subscription');

  // Find reactivate button
  const reactivateButton = page.locator('button:has-text("Reactivate"), button:has-text("Resume")').first();

  if (await reactivateButton.isVisible().catch(() => false)) {
    await reactivateButton.click();
    await page.waitForTimeout(1500);
  }
}

/**
 * Payment Methods Helpers
 */

/**
 * Verify payment method is displayed
 * @param page Playwright page object
 * @param last4 Last 4 digits of card
 */
export async function verifyPaymentMethod(page: Page, last4: string): Promise<void> {
  await navigateToBillingTab(page, 'subscription');

  // Scroll to payment methods section
  await page.evaluate(() => {
    const paymentSection = document.querySelector('[data-testid*="payment"], [class*="payment"]');
    paymentSection?.scrollIntoView({ behavior: 'smooth' });
  });

  await page.waitForTimeout(500);

  // Verify last 4 digits
  const cardInfo = page.locator(`text=/${last4}/`).first();
  await expect(cardInfo).toBeVisible();
}

/**
 * Delete payment method
 * @param page Playwright page object
 * @param last4 Last 4 digits of card to delete
 */
export async function deletePaymentMethod(page: Page, last4: string): Promise<void> {
  await navigateToBillingTab(page, 'subscription');

  // Find payment method card
  const paymentCard = page.locator(`[data-testid*="payment-method"], [class*="payment-method"]`)
    .filter({ hasText: last4 })
    .first();

  // Find delete button
  const deleteButton = paymentCard.locator('button:has-text("Delete"), button:has-text("Remove")').first();

  if (await deleteButton.isVisible().catch(() => false)) {
    await deleteButton.click();
    await page.waitForTimeout(500);

    // Confirm deletion if modal appears
    const confirmButton = page.locator('button:has-text("Confirm"), button:has-text("Delete")').first();
    if (await confirmButton.isVisible().catch(() => false)) {
      await confirmButton.click();
      await page.waitForTimeout(1500);
    }
  }
}

/**
 * Billing History Helpers
 */

/**
 * Verify invoice appears in billing history
 * @param page Playwright page object
 * @param invoiceNumber Invoice number to verify
 */
export async function verifyInvoiceExists(page: Page, invoiceNumber: string): Promise<void> {
  await navigateToBillingTab(page, 'subscription');

  // Scroll to billing history section
  await page.evaluate(() => {
    const historySection = document.querySelector('[data-testid*="billing-history"], [class*="billing-history"]');
    historySection?.scrollIntoView({ behavior: 'smooth' });
  });

  await page.waitForTimeout(500);

  // Verify invoice number
  const invoice = page.locator(`text=/${invoiceNumber}/`).first();
  await expect(invoice).toBeVisible();
}

/**
 * Download invoice PDF
 * @param page Playwright page object
 * @param invoiceNumber Invoice number to download
 */
export async function downloadInvoice(page: Page, invoiceNumber: string): Promise<void> {
  await navigateToBillingTab(page, 'subscription');

  // Find invoice row
  const invoiceRow = page.locator('[data-testid*="invoice"], [class*="invoice"]')
    .filter({ hasText: invoiceNumber })
    .first();

  // Find download button
  const downloadButton = invoiceRow.locator('button:has-text("Download"), a:has-text("Download")').first();

  if (await downloadButton.isVisible().catch(() => false)) {
    await downloadButton.click();
    await page.waitForTimeout(1000);
  }
}

/**
 * Assertion Helpers
 */

/**
 * Assert subscription is active
 * @param page Playwright page object
 */
export async function assertSubscriptionActive(page: Page): Promise<void> {
  await navigateToBillingTab(page, 'subscription');

  const activeStatus = page.locator('text=/active/i').first();
  await expect(activeStatus).toBeVisible();
}

/**
 * Assert subscription is cancelled
 * @param page Playwright page object
 */
export async function assertSubscriptionCancelled(page: Page): Promise<void> {
  await navigateToBillingTab(page, 'subscription');

  const cancelledStatus = page.locator('text=/cancelled|canceled/i').first();
  await expect(cancelledStatus).toBeVisible();
}

/**
 * Assert checkout success message
 * @param page Playwright page object
 */
export async function assertCheckoutSuccess(page: Page): Promise<void> {
  const successMessage = page.locator('text=/success|subscribed|thank you|welcome/i').first();
  await expect(successMessage).toBeVisible({ timeout: 10000 });
}

/**
 * Assert checkout error message
 * @param page Playwright page object
 * @param errorText Expected error message pattern
 */
export async function assertCheckoutError(page: Page, errorText: string): Promise<void> {
  const errorMessage = page.locator(`text=/${errorText}/i`).first();
  await expect(errorMessage).toBeVisible();
}

/**
 * Wait Helpers
 */

/**
 * Wait for page load and stabilization
 * @param page Playwright page object
 */
export async function waitForPageLoad(page: Page): Promise<void> {
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(500);
}

/**
 * Wait for modal to appear
 * @param page Playwright page object
 */
export async function waitForModal(page: Page): Promise<void> {
  await page.waitForSelector('[role="dialog"], [class*="modal"]', { timeout: 5000 });
  await page.waitForTimeout(300);
}

/**
 * Debug Helpers
 */

/**
 * Take screenshot for debugging
 * @param page Playwright page object
 * @param name Screenshot name
 */
export async function debugScreenshot(page: Page, name: string): Promise<void> {
  await page.screenshot({ path: `e2e/screenshots/${name}.png`, fullPage: true });
}

/**
 * Log page console messages
 * @param page Playwright page object
 */
export function enableConsoleLogging(page: Page): void {
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
}
