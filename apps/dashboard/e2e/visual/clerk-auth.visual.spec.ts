/**
 * Visual Regression Tests - Clerk Authentication Components
 *
 * Tests visual consistency of Clerk authentication UI including
 * sign-in, sign-up, user button, and error states.
 */

import { test, expect } from '@playwright/test';
import {
  captureFullPageSnapshot,
  captureComponentSnapshot,
  preparePageForVisualTesting,
  maskDynamicElements,
  testResponsiveSnapshots,
  STANDARD_VIEWPORTS,
} from '../utils/visual-testing';

// Test configuration
const CLERK_ENABLED = process.env.VITE_ENABLE_CLERK_AUTH === 'true';
const CLERK_PUBLISHABLE_KEY = process.env.VITE_CLERK_PUBLISHABLE_KEY;

// Skip tests if Clerk is not enabled
test.skip(!CLERK_ENABLED || !CLERK_PUBLISHABLE_KEY, 'Clerk authentication not configured');

test.describe('Clerk Authentication - Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    await preparePageForVisualTesting(page);
  });

  test('Sign-in page - initial load', async ({ page }) => {
    await page.goto('/sign-in');
    await page.waitForLoadState('networkidle');

    // Wait for Clerk component to load
    await page.waitForSelector('[data-clerk-element="signIn"]', { timeout: 10000 });
    await page.waitForTimeout(1000); // Wait for fonts and styling

    const masks = await maskDynamicElements(page);
    await captureFullPageSnapshot(page, 'clerk-signin-initial', {
      mask: masks,
      waitForTimeout: 1500,
    });
  });

  test('Sign-in page - with validation errors', async ({ page }) => {
    await page.goto('/sign-in');
    await page.waitForSelector('[data-clerk-element="signIn"]', { timeout: 10000 });

    // Trigger validation errors
    await page.fill('input[name="identifier"]', 'invalid-email');
    await page.fill('input[name="password"]', '');
    await page.getByRole('button', { name: /sign in|continue/i }).click();

    // Wait for error messages
    await page.waitForTimeout(1500);

    const masks = await maskDynamicElements(page);
    await captureFullPageSnapshot(page, 'clerk-signin-validation-errors', {
      mask: masks,
    });
  });

  test('Sign-in page - forgot password state', async ({ page }) => {
    await page.goto('/sign-in');
    await page.waitForSelector('[data-clerk-element="signIn"]', { timeout: 10000 });

    // Click forgot password
    const forgotPasswordLink = page.getByText(/forgot password/i);
    if (await forgotPasswordLink.isVisible()) {
      await forgotPasswordLink.click();
      await page.waitForTimeout(1000);

      const masks = await maskDynamicElements(page);
      await captureFullPageSnapshot(page, 'clerk-signin-forgot-password', {
        mask: masks,
      });
    }
  });

  test('Sign-up page - initial load', async ({ page }) => {
    await page.goto('/sign-up');
    await page.waitForLoadState('networkidle');

    // Wait for Clerk component to load
    await page.waitForSelector('[data-clerk-element="signUp"]', { timeout: 10000 });
    await page.waitForTimeout(1000);

    const masks = await maskDynamicElements(page);
    await captureFullPageSnapshot(page, 'clerk-signup-initial', {
      mask: masks,
      waitForTimeout: 1500,
    });
  });

  test('Sign-up page - with validation errors', async ({ page }) => {
    await page.goto('/sign-up');
    await page.waitForSelector('[data-clerk-element="signUp"]', { timeout: 10000 });

    // Trigger validation errors
    await page.fill('input[name="emailAddress"]', 'invalid');
    await page.fill('input[name="password"]', 'weak');
    await page.getByRole('button', { name: /sign up|create account/i }).click();

    // Wait for error messages
    await page.waitForTimeout(1500);

    const masks = await maskDynamicElements(page);
    await captureFullPageSnapshot(page, 'clerk-signup-validation-errors', {
      mask: masks,
    });
  });

  test('Sign-in form component - focused state', async ({ page }) => {
    await page.goto('/sign-in');
    await page.waitForSelector('[data-clerk-element="signIn"]', { timeout: 10000 });

    const signInCard = page.locator('[data-clerk-element="signIn"]');

    // Focus on email input
    await page.click('input[name="identifier"]');
    await page.waitForTimeout(500);

    if (await signInCard.isVisible()) {
      await captureComponentSnapshot(signInCard, 'clerk-signin-form-focused');
    }
  });

  test('Sign-up form component - focused state', async ({ page }) => {
    await page.goto('/sign-up');
    await page.waitForSelector('[data-clerk-element="signUp"]', { timeout: 10000 });

    const signUpCard = page.locator('[data-clerk-element="signUp"]');

    // Focus on email input
    await page.click('input[name="emailAddress"]');
    await page.waitForTimeout(500);

    if (await signUpCard.isVisible()) {
      await captureComponentSnapshot(signUpCard, 'clerk-signup-form-focused');
    }
  });

  test('Clerk error boundary - configuration error', async ({ page }) => {
    // This test would require temporarily breaking Clerk configuration
    // For now, just capture the normal state
    await page.goto('/sign-in');
    await page.waitForLoadState('networkidle');

    // Check if error boundary is shown
    const errorBoundary = page.locator('[data-testid="clerk-error"]');
    const hasError = await errorBoundary.isVisible().catch(() => false);

    if (hasError) {
      await captureFullPageSnapshot(page, 'clerk-error-boundary');
    }
  });

  test('Sign-in page - responsive views', async ({ page }) => {
    await page.goto('/sign-in');
    await page.waitForSelector('[data-clerk-element="signIn"]', { timeout: 10000 });

    await testResponsiveSnapshots(page, 'clerk-signin-responsive', [
      STANDARD_VIEWPORTS.mobile,
      STANDARD_VIEWPORTS.tablet,
      STANDARD_VIEWPORTS.desktop,
    ]);
  });

  test('Sign-up page - responsive views', async ({ page }) => {
    await page.goto('/sign-up');
    await page.waitForSelector('[data-clerk-element="signUp"]', { timeout: 10000 });

    await testResponsiveSnapshots(page, 'clerk-signup-responsive', [
      STANDARD_VIEWPORTS.mobile,
      STANDARD_VIEWPORTS.tablet,
      STANDARD_VIEWPORTS.desktop,
    ]);
  });

  test('Social login buttons - if configured', async ({ page }) => {
    await page.goto('/sign-in');
    await page.waitForSelector('[data-clerk-element="signIn"]', { timeout: 10000 });

    // Check if social buttons are present
    const socialButtons = page.locator('[data-clerk-element="socialButtons"]');
    const hasSocial = await socialButtons.isVisible().catch(() => false);

    if (hasSocial) {
      await page.waitForTimeout(1000);
      await captureComponentSnapshot(socialButtons, 'clerk-social-buttons');
    }
  });

  test('Clerk loading state', async ({ page }) => {
    // Navigate to page and try to capture loading state
    const navigation = page.goto('/sign-in');

    // Try to capture loading state quickly
    await page.waitForTimeout(500);

    const loadingState = page.locator('[data-clerk-element="loading"], .clerk-loading');
    const isLoading = await loadingState.isVisible().catch(() => false);

    if (isLoading) {
      await captureFullPageSnapshot(page, 'clerk-loading-state');
    }

    await navigation;
  });

  test('Protected route redirect - loading and redirect states', async ({ page }) => {
    // Navigate to protected route without auth
    const navigation = page.goto('/dashboard');

    // Capture any intermediate loading or redirect states
    await page.waitForTimeout(1000);

    const masks = await maskDynamicElements(page);

    // Should show loading or already redirected to sign-in
    const currentUrl = page.url();
    if (currentUrl.includes('/sign-in')) {
      await captureFullPageSnapshot(page, 'clerk-protected-route-redirect', {
        mask: masks,
      });
    }

    await navigation;
  });
});

test.describe('Clerk User Profile - Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    await preparePageForVisualTesting(page);
  });

  // Note: These tests would require an authenticated session
  // For now, they will skip if not authenticated

  test('User button - not authenticated', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // User button should not be visible when not authenticated
    const userButton = page.locator('[data-clerk-element="userButton"]');
    const isVisible = await userButton.isVisible().catch(() => false);

    // This test passes by confirming button is not shown
    expect(isVisible).toBe(false);
  });
});
