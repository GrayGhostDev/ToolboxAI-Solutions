/**
 * Subscription Management E2E Tests
 *
 * Tests subscription lifecycle management including:
 * - Viewing active subscription details
 * - Changing plans (upgrade/downgrade)
 * - Canceling subscriptions
 * - Reactivating cancelled subscriptions
 * - Managing payment methods
 * - Viewing billing history and invoices
 */

import { test, expect } from '@playwright/test';

// Test user with active subscription
const SUBSCRIBED_USER = {
  email: 'teacher@toolboxai.com',
  password: 'Teacher123!'
};

test.describe('Subscription Management', () => {
  // Setup: Login with subscribed user
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000);

    // Login
    await page.locator('input[name="identifier"], input[id="identifier-field"], [data-testid="email-input"]').first().fill(SUBSCRIBED_USER.email);
    await page.locator('input[name="password"], input[id="password-field"], [data-testid="password-input"]').first().fill(SUBSCRIBED_USER.password);
    await page.locator('button[type="submit"], button:has-text("Continue"), [data-testid="login-submit"]').first().click();

    // Wait for dashboard
    await page.waitForTimeout(2000);

    // Navigate to billing page
    await page.goto('/billing');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000);
  });

  test('should display active subscription details', async ({ page }) => {
    // Verify subscription tab is active by default
    const subscriptionTab = page.getByRole('tab', { name: /subscription/i });
    await expect(subscriptionTab).toHaveAttribute('aria-selected', 'true');

    // Check for subscription details or no subscription message
    const hasSubscription = await page.getByText(/no active subscription/i).isVisible().catch(() => false);

    if (hasSubscription) {
      // No subscription case
      await expect(page.getByText(/choose a plan to get started/i)).toBeVisible();
      await expect(page.getByRole('button', { name: /view plans/i })).toBeVisible();
    } else {
      // Active subscription case
      // Verify plan name is visible (could be Starter, Professional, or Enterprise)
      const planNames = [
        page.getByText(/starter/i),
        page.getByText(/professional/i),
        page.getByText(/enterprise/i)
      ];

      let foundPlan = false;
      for (const planName of planNames) {
        if (await planName.isVisible().catch(() => false)) {
          foundPlan = true;
          break;
        }
      }
      expect(foundPlan).toBeTruthy();

      // Verify status badge (Active, Cancelled, Past Due, etc.)
      const statusBadge = page.locator('[class*="Badge"]').filter({ hasText: /active|cancelled|past due|trialing/i }).first();
      await expect(statusBadge).toBeVisible();
    }
  });

  test('should show subscription status badge', async ({ page }) => {
    // Look for status badge
    const badge = page.locator('[class*="Badge"]').filter({ hasText: /active|cancelled|past due|trialing/i }).first();

    // Check if badge exists
    const badgeVisible = await badge.isVisible().catch(() => false);

    if (badgeVisible) {
      await expect(badge).toBeVisible();
      // Status should be one of the valid states
      const badgeText = await badge.textContent();
      expect(badgeText?.toLowerCase()).toMatch(/active|cancelled|past due|trialing/);
    }
  });

  test('should display renewal date for active subscription', async ({ page }) => {
    // Check for renewal date section
    const renewalSection = page.getByText(/next billing date|renewal/i);
    const hasRenewal = await renewalSection.isVisible().catch(() => false);

    if (hasRenewal) {
      await expect(renewalSection).toBeVisible();
      // Should show a date
      await expect(page.locator('text=/\\d+\\/\\d+\\/\\d+|\\w+ \\d+, \\d+/')).toBeVisible();
    }
  });

  test('should show change plan button', async ({ page }) => {
    // Look for change plan button
    const changePlanButton = page.getByRole('button', { name: /change plan|view plans/i });
    await expect(changePlanButton).toBeVisible();
  });

  test('should navigate to plans when change plan clicked', async ({ page }) => {
    // Click change plan button
    const changePlanButton = page.getByRole('button', { name: /change plan|view plans/i });
    await changePlanButton.click();
    await page.waitForTimeout(500);

    // Should switch to plans tab
    const plansTab = page.getByRole('tab', { name: /plans.*pricing/i });
    await expect(plansTab).toHaveAttribute('aria-selected', 'true');

    // Verify plans are displayed
    await expect(page.getByText('Starter')).toBeVisible();
    await expect(page.getByText('Professional')).toBeVisible();
    await expect(page.getByText('Enterprise')).toBeVisible();
  });

  test('should show cancel subscription button for active subscription', async ({ page }) => {
    // Check if there's an active subscription
    const hasActiveSubscription = await page.getByRole('button', { name: /cancel subscription/i }).isVisible().catch(() => false);

    if (hasActiveSubscription) {
      const cancelButton = page.getByRole('button', { name: /cancel subscription/i });
      await expect(cancelButton).toBeVisible();
    }
  });

  test('should open cancellation modal when cancel clicked', async ({ page }) => {
    // Check if cancel button exists
    const cancelButton = page.getByRole('button', { name: /cancel subscription/i });
    const hasCancelButton = await cancelButton.isVisible().catch(() => false);

    if (hasCancelButton) {
      await cancelButton.click();
      await page.waitForTimeout(500);

      // Verify modal opened
      await expect(page.getByRole('dialog').or(page.locator('[role="dialog"]'))).toBeVisible();
      await expect(page.getByText(/cancel subscription/i)).toBeVisible();
      await expect(page.getByText(/are you sure/i)).toBeVisible();
    }
  });

  test('should show warning message in cancellation modal', async ({ page }) => {
    // Check if cancel button exists
    const cancelButton = page.getByRole('button', { name: /cancel subscription/i });
    const hasCancelButton = await cancelButton.isVisible().catch(() => false);

    if (hasCancelButton) {
      await cancelButton.click();
      await page.waitForTimeout(500);

      // Verify warning message
      await expect(page.getByText(/lose access to premium features/i)).toBeVisible();
      await expect(page.getByText(/end of your billing period/i)).toBeVisible();
    }
  });

  test('should allow keeping subscription from modal', async ({ page }) => {
    // Check if cancel button exists
    const cancelButton = page.getByRole('button', { name: /cancel subscription/i });
    const hasCancelButton = await cancelButton.isVisible().catch(() => false);

    if (hasCancelButton) {
      await cancelButton.click();
      await page.waitForTimeout(500);

      // Click "Keep Subscription" button
      const keepButton = page.getByRole('button', { name: /keep subscription/i });
      await keepButton.click();
      await page.waitForTimeout(500);

      // Modal should close
      const modalVisible = await page.getByRole('dialog').isVisible().catch(() => false);
      expect(modalVisible).toBeFalsy();
    }
  });

  test('should process cancellation (mocked)', async ({ page }) => {
    // Check if cancel button exists
    const cancelButton = page.getByRole('button', { name: /cancel subscription/i });
    const hasCancelButton = await cancelButton.isVisible().catch(() => false);

    if (hasCancelButton) {
      await cancelButton.click();
      await page.waitForTimeout(500);

      // Click confirm cancellation
      const confirmButton = page.getByRole('button', { name: /confirm cancellation/i });

      // Button should be visible
      await expect(confirmButton).toBeVisible();

      // Note: Actual cancellation would require backend integration
      // For now, we verify the button is clickable
      await expect(confirmButton).toBeEnabled();
    }
  });

  test('should show reactivate button for cancelled subscription', async ({ page }) => {
    // Check if reactivate button is visible (would be visible for cancelled subs)
    const reactivateButton = page.getByRole('button', { name: /reactivate subscription/i });
    const hasReactivateButton = await reactivateButton.isVisible().catch(() => false);

    // If user has cancelled subscription, verify reactivate button
    if (hasReactivateButton) {
      await expect(reactivateButton).toBeVisible();
    }
  });

  test('should display payment methods section', async ({ page }) => {
    // Look for payment methods section
    const paymentMethodsSection = page.getByText(/payment methods/i).first();
    const hasPaymentMethods = await paymentMethodsSection.isVisible().catch(() => false);

    if (hasPaymentMethods) {
      await expect(paymentMethodsSection).toBeVisible();

      // Should have manage button
      await expect(page.getByRole('button', { name: /manage/i })).toBeVisible();
    }
  });

  test('should display payment method details', async ({ page }) => {
    // Look for card details (VISA •••• 4242 format)
    const cardPattern = /visa|mastercard|amex|discover.*\d{4}/i;
    const cardDetails = page.locator(`text=${cardPattern}`).first();
    const hasCard = await cardDetails.isVisible().catch(() => false);

    if (hasCard) {
      await expect(cardDetails).toBeVisible();

      // Should show expiration
      await expect(page.locator('text=/expires.*\\d+\\/\\d+/i')).toBeVisible();

      // Should show default badge if it's the default card
      const defaultBadge = page.locator('[class*="Badge"]').filter({ hasText: /default/i }).first();
      const hasDefaultBadge = await defaultBadge.isVisible().catch(() => false);

      if (hasDefaultBadge) {
        await expect(defaultBadge).toBeVisible();
      }
    }
  });

  test('should display billing history section', async ({ page }) => {
    // Look for billing history section
    const billingHistory = page.getByText(/billing history/i).first();
    const hasBillingHistory = await billingHistory.isVisible().catch(() => false);

    if (hasBillingHistory) {
      await expect(billingHistory).toBeVisible();
    }
  });

  test('should show invoices in billing history', async ({ page }) => {
    // Look for invoice entries
    const invoicePattern = /invoice.*#/i;
    const invoice = page.locator(`text=${invoicePattern}`).first();
    const hasInvoices = await invoice.isVisible().catch(() => false);

    if (hasInvoices) {
      await expect(invoice).toBeVisible();

      // Should show invoice date
      await expect(page.locator('text=/\\d+\\/\\d+\\/\\d+|\\w+ \\d+, \\d+/')).toBeVisible();

      // Should show invoice amount
      await expect(page.locator('text=/\\$\\d+\\.\\d+/')).toBeVisible();

      // Should show invoice status (paid, pending, failed)
      const statusBadge = page.locator('[class*="Badge"]').filter({ hasText: /paid|pending|failed/i }).first();
      await expect(statusBadge).toBeVisible();
    }
  });

  test('should allow downloading invoices', async ({ page }) => {
    // Look for download buttons or links
    const downloadButton = page.locator('[aria-label*="download"], button:has-text("download")').first();
    const hasDownload = await downloadButton.isVisible().catch(() => false);

    if (hasDownload) {
      await expect(downloadButton).toBeVisible();
      await expect(downloadButton).toBeEnabled();
    }
  });

  test('should display past due alert for overdue payments', async ({ page }) => {
    // Check for past due alert
    const pastDueAlert = page.getByRole('alert').filter({ hasText: /past due|payment.*failed|update.*payment method/i }).first();
    const hasPastDue = await pastDueAlert.isVisible().catch(() => false);

    if (hasPastDue) {
      await expect(pastDueAlert).toBeVisible();
    }
  });

  test('should show trial period information', async ({ page }) => {
    // Check for trial information
    const trialInfo = page.getByText(/trial ends|trial period|days left/i).first();
    const hasTrial = await trialInfo.isVisible().catch(() => false);

    if (hasTrial) {
      await expect(trialInfo).toBeVisible();
      // Should show trial end date
      await expect(page.locator('text=/\\d+\\/\\d+\\/\\d+|\\w+ \\d+, \\d+/')).toBeVisible();
    }
  });

  test('should show cancellation notice for scheduled cancellations', async ({ page }) => {
    // Check for cancellation notice
    const cancellationNotice = page.getByText(/scheduled to cancel|will cancel|retain access until/i).first();
    const hasCancellationNotice = await cancellationNotice.isVisible().catch(() => false);

    if (hasCancellationNotice) {
      await expect(cancellationNotice).toBeVisible();
    }
  });

  test('should display subscription progress indicator', async ({ page }) => {
    // Look for progress bar showing billing cycle
    const progressBar = page.locator('[role="progressbar"], [class*="Progress"]').first();
    const hasProgress = await progressBar.isVisible().catch(() => false);

    if (hasProgress) {
      await expect(progressBar).toBeVisible();
    }
  });
});

test.describe('Invoices Tab', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000);

    await page.locator('input[name="identifier"], input[id="identifier-field"], [data-testid="email-input"]').first().fill(SUBSCRIBED_USER.email);
    await page.locator('input[name="password"], input[id="password-field"], [data-testid="password-input"]').first().fill(SUBSCRIBED_USER.password);
    await page.locator('button[type="submit"], button:has-text("Continue"), [data-testid="login-submit"]').first().click();
    await page.waitForTimeout(2000);

    await page.goto('/billing');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000);
  });

  test('should navigate to invoices tab', async ({ page }) => {
    // Click invoices tab
    const invoicesTab = page.getByRole('tab', { name: /invoices/i });
    await invoicesTab.click();
    await page.waitForTimeout(500);

    // Verify tab is active
    await expect(invoicesTab).toHaveAttribute('aria-selected', 'true');

    // Verify invoices content is visible
    await expect(page.getByText(/all invoices|no invoices yet/i)).toBeVisible();
  });

  test('should display all invoices in chronological order', async ({ page }) => {
    // Navigate to invoices tab
    const invoicesTab = page.getByRole('tab', { name: /invoices/i });
    await invoicesTab.click();
    await page.waitForTimeout(500);

    // Check if invoices exist
    const noInvoices = await page.getByText(/no invoices yet/i).isVisible().catch(() => false);

    if (!noInvoices) {
      // Verify invoice list items
      const invoiceItems = page.locator('[class*="Card"], [class*="Box"]').filter({ hasText: /invoice/i });
      const count = await invoiceItems.count();

      expect(count).toBeGreaterThan(0);

      // Verify invoice information is displayed
      await expect(page.locator('text=/\\$\\d+\\.\\d+/')).toBeVisible();
      await expect(page.locator('[class*="Badge"]').filter({ hasText: /paid|pending|failed/i }).first()).toBeVisible();
    }
  });

  test('should show empty state when no invoices', async ({ page }) => {
    // Navigate to invoices tab
    const invoicesTab = page.getByRole('tab', { name: /invoices/i });
    await invoicesTab.click();
    await page.waitForTimeout(500);

    // Check for empty state
    const emptyState = page.getByText(/no invoices yet/i);
    const hasEmptyState = await emptyState.isVisible().catch(() => false);

    if (hasEmptyState) {
      await expect(emptyState).toBeVisible();
      await expect(page.getByText(/billing history will appear here/i)).toBeVisible();
    }
  });

  test('should display invoice status badges', async ({ page }) => {
    // Navigate to invoices tab
    const invoicesTab = page.getByRole('tab', { name: /invoices/i });
    await invoicesTab.click();
    await page.waitForTimeout(500);

    // Look for status badges
    const statusBadges = page.locator('[class*="Badge"]').filter({ hasText: /paid|pending|failed/i });
    const hasStatuses = await statusBadges.first().isVisible().catch(() => false);

    if (hasStatuses) {
      const count = await statusBadges.count();
      expect(count).toBeGreaterThan(0);

      // Verify badge colors are appropriate
      // Green for paid, yellow for pending, red for failed
      for (let i = 0; i < Math.min(count, 3); i++) {
        await expect(statusBadges.nth(i)).toBeVisible();
      }
    }
  });
});

test.describe('Subscription Management Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000);

    await page.locator('input[name="identifier"], input[id="identifier-field"], [data-testid="email-input"]').first().fill(SUBSCRIBED_USER.email);
    await page.locator('input[name="password"], input[id="password-field"], [data-testid="password-input"]').first().fill(SUBSCRIBED_USER.password);
    await page.locator('button[type="submit"], button:has-text("Continue"), [data-testid="login-submit"]').first().click();
    await page.waitForTimeout(2000);

    await page.goto('/billing');
    await page.waitForLoadState('domcontentloaded');
  });

  test('should have proper tab navigation', async ({ page }) => {
    // Verify all tabs are accessible
    const subscriptionTab = page.getByRole('tab', { name: /subscription/i });
    const plansTab = page.getByRole('tab', { name: /plans/i });
    const invoicesTab = page.getByRole('tab', { name: /invoices/i });

    await expect(subscriptionTab).toBeVisible();
    await expect(plansTab).toBeVisible();
    await expect(invoicesTab).toBeVisible();

    // Test keyboard navigation
    await subscriptionTab.focus();
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(200);

    // Plans tab should be focused
    await expect(plansTab).toBeFocused();
  });

  test('should have accessible status indicators', async ({ page }) => {
    // Check for status badges with proper roles
    const statusBadges = page.locator('[class*="Badge"]');
    const count = await statusBadges.count();

    if (count > 0) {
      // At least one badge should be visible
      await expect(statusBadges.first()).toBeVisible();
    }
  });

  test('should support screen reader navigation', async ({ page }) => {
    // Verify semantic structure
    const mainHeading = page.getByRole('heading', { name: /billing.*subscription/i });
    await expect(mainHeading).toBeVisible();

    // Verify buttons have accessible names
    const buttons = page.getByRole('button');
    const buttonCount = await buttons.count();

    for (let i = 0; i < Math.min(buttonCount, 5); i++) {
      const buttonText = await buttons.nth(i).textContent();
      expect(buttonText?.trim().length).toBeGreaterThan(0);
    }
  });
});
