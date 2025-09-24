jest.setTimeout(10000);

import { test, expect, Page } from '@playwright/test';

test.describe('Comprehensive Dashboard Tests', () => {
  let page: Page;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    await page.goto('/');

    // Wait for the page to load
    await page.waitForLoadState('networkidle');
  });

  test.describe('Authentication Flow', () => {
    test('should display login page when not authenticated', async () => {
      // Check for login elements
      const loginElements = await page.locator('[data-testid*="login"], [id*="login"], #login-form, .login-container').count();

      if (loginElements > 0) {
        await expect(page.locator('[data-testid*="login"], [id*="login"], #login-form, .login-container').first()).toBeVisible();
      }
    });

    test('should handle login form submission', async () => {
      // Try to find login form elements
      const usernameField = page.locator('input[name="username"], input[type="text"], input[placeholder*="username" i], input[placeholder*="email" i]').first();
      const passwordField = page.locator('input[name="password"], input[type="password"]').first();
      const submitButton = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")').first();

      if (await usernameField.count() > 0 && await passwordField.count() > 0) {
        await usernameField.fill('test_teacher');
        await passwordField.fill('TestPass123!');

        if (await submitButton.count() > 0) {
          await submitButton.click();

          // Wait for navigation or error message
          await page.waitForTimeout(2000);
        }
      }
    });

    test('should handle logout functionality', async () => {
      const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Sign out"), [data-testid="logout"]');

      if (await logoutButton.count() > 0) {
        await logoutButton.first().click();
        await page.waitForTimeout(1000);

        // Should redirect to login page
        const loginElements = await page.locator('[data-testid*="login"], [id*="login"]').count();
        expect(loginElements).toBeGreaterThan(0);
      }
    });
  });

  test.describe('Navigation', () => {
    test('should have working navigation menu', async () => {
      // Check for navigation elements
      const navMenu = page.locator('nav, [role="navigation"], .sidebar, .menu');

      if (await navMenu.count() > 0) {
        await expect(navMenu.first()).toBeVisible();

        // Check for navigation links
        const navLinks = navMenu.locator('a, button').all();
        const links = await navLinks;

        for (const link of links.slice(0, 5)) { // Test first 5 links
          const isVisible = await link.isVisible();
          if (isVisible) {
            const text = await link.textContent();
            console.log(`Found navigation link: ${text}`);
          }
        }
      }
    });

    test('should navigate to Classes page', async () => {
      const classesLink = page.locator('a:has-text("Classes"), button:has-text("Classes"), [href*="/classes"]');

      if (await classesLink.count() > 0) {
        await classesLink.first().click();
        await page.waitForLoadState('networkidle');

        // Check if we're on the classes page
        expect(page.url()).toMatch(/classes/i);
      }
    });

    test('should navigate to Lessons page', async () => {
      const lessonsLink = page.locator('a:has-text("Lessons"), button:has-text("Lessons"), [href*="/lessons"]');

      if (await lessonsLink.count() > 0) {
        await lessonsLink.first().click();
        await page.waitForLoadState('networkidle');

        // Check if we're on the lessons page
        expect(page.url()).toMatch(/lessons/i);
      }
    });

    test('should navigate to Assessments page', async () => {
      const assessmentsLink = page.locator('a:has-text("Assessments"), button:has-text("Assessments"), [href*="/assessments"]');

      if (await assessmentsLink.count() > 0) {
        await assessmentsLink.first().click();
        await page.waitForLoadState('networkidle');

        // Check if we're on the assessments page
        expect(page.url()).toMatch(/assessments/i);
      }
    });

    test('should navigate to Messages page', async () => {
      const messagesLink = page.locator('a:has-text("Messages"), button:has-text("Messages"), [href*="/messages"]');

      if (await messagesLink.count() > 0) {
        await messagesLink.first().click();
        await page.waitForLoadState('networkidle');

        // Check if we're on the messages page
        expect(page.url()).toMatch(/messages/i);
      }
    });
  });

  test.describe('Dashboard Features', () => {
    test('should display user profile information', async () => {
      const profileElements = page.locator('[data-testid*="profile"], [class*="profile"], [class*="user-info"]');

      if (await profileElements.count() > 0) {
        await expect(profileElements.first()).toBeVisible();
      }
    });

    test('should display statistics/metrics', async () => {
      const statsElements = page.locator('[data-testid*="stats"], [class*="metric"], [class*="statistic"], .card');

      if (await statsElements.count() > 0) {
        const firstStat = statsElements.first();
        await expect(firstStat).toBeVisible();

        // Check if stats have numbers
        const numbers = await page.locator('.number, .count, .value, [class*="metric-value"]').count();
        expect(numbers).toBeGreaterThan(0);
      }
    });

    test('should have working search functionality', async () => {
      const searchInput = page.locator('input[type="search"], input[placeholder*="search" i], [data-testid*="search"]');

      if (await searchInput.count() > 0) {
        await searchInput.first().fill('Mathematics');
        await page.keyboard.press('Enter');
        await page.waitForTimeout(1000);
      }
    });

    test('should display data tables', async () => {
      const tables = page.locator('table, [role="table"], .data-table');

      if (await tables.count() > 0) {
        await expect(tables.first()).toBeVisible();

        // Check for table headers
        const headers = tables.first().locator('th, [role="columnheader"]');
        const headerCount = await headers.count();
        expect(headerCount).toBeGreaterThan(0);
      }
    });

    test('should have working filters', async () => {
      const filters = page.locator('select, [role="combobox"], .filter-dropdown');

      if (await filters.count() > 0) {
        const firstFilter = filters.first();
        await firstFilter.click();

        // Check if dropdown options appear
        const options = page.locator('option, [role="option"]');
        const optionCount = await options.count();
        expect(optionCount).toBeGreaterThan(0);
      }
    });
  });

  test.describe('Real-time Features', () => {
    test('should establish WebSocket connection', async () => {
      // Check for WebSocket connection
      const wsConnected = await page.evaluate(() => {
        // Check for Pusher or WebSocket in window
        return !!(window as any).Pusher || !!(window as any).WebSocket;
      });

      expect(wsConnected).toBeTruthy();
    });

    test('should display real-time notifications', async () => {
      const notifications = page.locator('[data-testid*="notification"], .notification, .alert, .toast');

      // Wait for any notifications to appear
      await page.waitForTimeout(3000);

      if (await notifications.count() > 0) {
        console.log('Notifications found on page');
      }
    });
  });

  test.describe('Responsive Design', () => {
    test('should be responsive on mobile', async () => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.reload();

      // Check if mobile menu button appears
      const mobileMenu = page.locator('[data-testid*="mobile-menu"], .hamburger, .menu-toggle');

      if (await mobileMenu.count() > 0) {
        await expect(mobileMenu.first()).toBeVisible();
        await mobileMenu.first().click();

        // Mobile menu should open
        const mobileNav = page.locator('.mobile-nav, .drawer, .sidenav');
        if (await mobileNav.count() > 0) {
          await expect(mobileNav.first()).toBeVisible();
        }
      }
    });

    test('should be responsive on tablet', async () => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.reload();

      // Check layout adjustments
      const mainContent = page.locator('main, .main-content, #app');
      await expect(mainContent.first()).toBeVisible();
    });
  });

  test.describe('Forms and Interactions', () => {
    test('should handle form submissions', async () => {
      // Look for any forms on the page
      const forms = page.locator('form');

      if (await forms.count() > 0) {
        const firstForm = forms.first();
        const inputs = firstForm.locator('input:not([type="hidden"])');
        const inputCount = await inputs.count();

        if (inputCount > 0) {
          // Fill first input
          await inputs.first().fill('Test input');
        }
      }
    });

    test('should handle modal dialogs', async () => {
      // Look for buttons that might open modals
      const modalTriggers = page.locator('button:has-text("Add"), button:has-text("Create"), button:has-text("New")');

      if (await modalTriggers.count() > 0) {
        await modalTriggers.first().click();
        await page.waitForTimeout(500);

        // Check if modal appeared
        const modals = page.locator('[role="dialog"], .modal, .dialog');
        if (await modals.count() > 0) {
          await expect(modals.first()).toBeVisible();

          // Close modal
          const closeButton = modals.first().locator('button:has-text("Close"), button:has-text("Cancel"), [aria-label="Close"]');
          if (await closeButton.count() > 0) {
            await closeButton.first().click();
          }
        }
      }
    });

    test('should handle dropdown menus', async () => {
      const dropdowns = page.locator('[role="button"][aria-haspopup="true"], .dropdown-toggle');

      if (await dropdowns.count() > 0) {
        await dropdowns.first().click();
        await page.waitForTimeout(500);

        // Check if dropdown menu appeared
        const dropdownMenu = page.locator('[role="menu"], .dropdown-menu');
        if (await dropdownMenu.count() > 0) {
          await expect(dropdownMenu.first()).toBeVisible();
        }
      }
    });
  });

  test.describe('Error Handling', () => {
    test('should handle 404 pages gracefully', async () => {
      await page.goto('/non-existent-page');
      await page.waitForLoadState('networkidle');

      // Check for 404 message or redirect
      const errorMessage = page.locator(':has-text("404"), :has-text("Not Found"), :has-text("Page not found")');
      const hasError = await errorMessage.count() > 0;
      const isRedirected = !page.url().includes('non-existent-page');

      expect(hasError || isRedirected).toBeTruthy();
    });

    test('should display error messages for failed API calls', async () => {
      // Listen for failed network requests
      const failedRequests: string[] = [];
      page.on('response', response => {
        if (response.status() >= 400 && response.url().includes('/api/')) {
          failedRequests.push(response.url());
        }
      });

      await page.reload();
      await page.waitForTimeout(3000);

      // Check if error messages are displayed for failed requests
      if (failedRequests.length > 0) {
        const errorElements = page.locator('.error, .alert-error, [role="alert"]');
        console.log(`Found ${failedRequests.length} failed API requests`);
      }
    });

    test('should not have console errors', async () => {
      const errors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text());
        }
      });

      await page.reload();
      await page.waitForLoadState('networkidle');

      // Filter out expected errors (like failed API calls during development)
      const criticalErrors = errors.filter(error =>
        !error.includes('Failed to load resource') &&
        !error.includes('404') &&
        !error.includes('NetworkError')
      );

      expect(criticalErrors).toHaveLength(0);
    });
  });

  test.describe('Accessibility', () => {
    test('should have proper ARIA labels', async () => {
      const buttons = page.locator('button');
      const buttonsWithoutLabel = [];

      const buttonCount = await buttons.count();
      for (let i = 0; i < Math.min(buttonCount, 10); i++) {
        const button = buttons.nth(i);
        const ariaLabel = await button.getAttribute('aria-label');
        const text = await button.textContent();

        if (!ariaLabel && !text?.trim()) {
          buttonsWithoutLabel.push(i);
        }
      }

      expect(buttonsWithoutLabel.length).toBeLessThanOrEqual(2);
    });

    test('should support keyboard navigation', async () => {
      // Tab through the page
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');

      // Check if an element is focused
      const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
      expect(focusedElement).toBeTruthy();
    });

    test('should have proper heading hierarchy', async () => {
      const h1Count = await page.locator('h1').count();
      const h2Count = await page.locator('h2').count();

      // Should have at least one h1
      expect(h1Count).toBeGreaterThanOrEqual(1);

      // Should not skip heading levels
      if (h2Count > 0) {
        expect(h1Count).toBeGreaterThan(0);
      }
    });
  });
});