import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';

/**
 * Simple test to verify authentication and navigation work
 * Based on actual dashboard implementation analysis
 */

test.describe('Simple Dashboard Tests', () => {
  test('teacher can login and navigate to classes', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');

    // Fill login form with exact name attributes
    await page.locator('input[name="email"]').fill('jane.smith@school.edu');
    await page.locator('input[name="password"]').fill('Teacher123!');

    // Submit form
    await page.locator('button[type="submit"]').click();

    // Wait for navigation away from login
    await page.waitForURL(url => !url.pathname.includes('/login'), {
      timeout: 10000,
      waitUntil: 'networkidle'
    });

    // The sidebar might be collapsed - look for navigation in the page
    // Try to find the Classes link by exact text
    const classesLink = page.getByText('Classes', { exact: true });

    // Check if the link is visible, if not, try to open sidebar
    if (!(await classesLink.isVisible())) {
      // Try clicking menu button to open sidebar if it exists
      const menuButton = page.locator('button[aria-label*="menu"]');
      if (await menuButton.isVisible()) {
        await menuButton.click();
        await page.waitForTimeout(500); // Wait for animation
      }
    }

    // Now click on Classes
    await classesLink.click();

    // Verify we're on the classes page
    await expect(page).toHaveURL(/\/classes/);

    // Look for the Create Class button (exact text)
    const createButton = page.getByRole('button').filter({ hasText: 'Create Class' });
    await expect(createButton).toBeVisible({ timeout: 10000 });
  });

  test('student cannot see classes link', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');

    // Login as student
    await page.locator('input[name="email"]').fill('alex.johnson@student.edu');
    await page.locator('input[name="password"]').fill('Student123!');
    await page.locator('button[type="submit"]').click();

    // Wait for navigation
    await page.waitForURL(url => !url.pathname.includes('/login'), {
      timeout: 10000,
      waitUntil: 'networkidle'
    });

    // Check that Classes link is NOT visible (students don't have access)
    const classesLink = page.getByText('Classes', { exact: true });
    await expect(classesLink).not.toBeVisible();

    // But student should see Missions
    const missionsLink = page.getByText('Missions', { exact: true });

    // Open sidebar if needed
    if (!(await missionsLink.isVisible())) {
      const menuButton = page.locator('button[aria-label*="menu"]');
      if (await menuButton.isVisible()) {
        await menuButton.click();
        await page.waitForTimeout(500);
      }
    }

    await expect(missionsLink).toBeVisible();
  });

  test('admin can login and see admin menu', async ({ page }) => {
    await page.goto('/login');

    // Login as admin
    await page.locator('input[name="email"]').fill('admin@toolboxai.com');
    await page.locator('input[name="password"]').fill('Admin123!');
    await page.locator('button[type="submit"]').click();

    // Wait for navigation
    await page.waitForURL(url => !url.pathname.includes('/login'), {
      timeout: 10000,
      waitUntil: 'networkidle'
    });

    // Admin should see Schools link
    const schoolsLink = page.getByText('Schools', { exact: true });

    // Open sidebar if needed
    if (!(await schoolsLink.isVisible())) {
      const menuButton = page.locator('button[aria-label*="menu"]');
      if (await menuButton.isVisible()) {
        await menuButton.click();
        await page.waitForTimeout(500);
      }
    }

    await expect(schoolsLink).toBeVisible();
  });
});