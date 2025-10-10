/**
 * Visual Regression Tests - Authentication Pages
 *
 * Tests visual consistency of authentication flows including
 * login, registration, password reset, and error states.
 */

import { test, expect } from '@playwright/test';
import {
  captureFullPageSnapshot,
  captureViewportSnapshot,
  preparePageForVisualTesting,
  testResponsiveSnapshots,
  STANDARD_VIEWPORTS,
} from '../utils/visual-testing';

test.describe('Authentication Pages - Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    await preparePageForVisualTesting(page);
  });

  test('Login page - initial state', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    await captureFullPageSnapshot(page, 'auth-login-initial', {
      waitForTimeout: 1000,
    });
  });

  test('Login page - with validation errors', async ({ page }) => {
    await page.goto('/login');

    // Trigger validation errors
    await page.getByRole('button', { name: /sign in|login/i }).click();
    await page.waitForTimeout(500);

    await captureFullPageSnapshot(page, 'auth-login-validation-errors');
  });

  test('Login page - filled form', async ({ page }) => {
    await page.goto('/login');

    // Fill in form fields
    await page.getByLabel(/email|username/i).fill('test@example.com');
    await page.getByLabel(/password/i).fill('password123');

    await captureFullPageSnapshot(page, 'auth-login-filled-form');
  });

  test('Login page - responsive views', async ({ page }) => {
    await page.goto('/login');

    await testResponsiveSnapshots(page, 'auth-login-responsive', [
      STANDARD_VIEWPORTS.mobile,
      STANDARD_VIEWPORTS.tablet,
      STANDARD_VIEWPORTS.desktop,
    ]);
  });

  test('Register page - initial state', async ({ page }) => {
    await page.goto('/register');
    await page.waitForLoadState('networkidle');

    await captureFullPageSnapshot(page, 'auth-register-initial');
  });

  test('Password reset page', async ({ page }) => {
    await page.goto('/forgot-password');
    await page.waitForLoadState('networkidle');

    await captureFullPageSnapshot(page, 'auth-password-reset');
  });

  test('Login page - loading state', async ({ page }) => {
    await page.goto('/login');

    // Fill form
    await page.getByLabel(/email|username/i).fill('test@example.com');
    await page.getByLabel(/password/i).fill('password123');

    // Click login and capture loading state immediately
    const loginButton = page.getByRole('button', { name: /sign in|login/i });
    await loginButton.click();

    // Wait for loading indicator
    await page.waitForSelector('[data-testid="loading"], .loading, [aria-busy="true"]', {
      state: 'visible',
      timeout: 1000,
    }).catch(() => {});

    await captureViewportSnapshot(page, 'auth-login-loading-state');
  });
});
