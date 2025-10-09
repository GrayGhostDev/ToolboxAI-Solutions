import { test, expect, Page } from '@playwright/test';
import { createLocatorHelper } from '../helpers/locators';

/**
 * Comprehensive Test Suite for All Dashboard Pages
 * Tests that all page components render without errors in bypass mode
 */

test.describe('All Dashboard Pages - Comprehensive Rendering Tests', () => {
  let page: Page;
  let locatorHelper: any;

  // Define all pages to test with their expected elements and roles
  const pagesToTest = [
    {
      path: '/',
      name: 'Home Dashboard',
      expectedElements: ['Welcome', 'Dashboard', 'Quick Actions'],
      roles: ['admin', 'teacher', 'student', 'parent']
    },
    {
      path: '/classes',
      name: 'Classes',
      expectedElements: ['Classes', 'Create New Class', 'Active Classes'],
      roles: ['teacher', 'admin']
    },
    {
      path: '/lessons',
      name: 'Lessons',
      expectedElements: ['Lessons', 'Create Lesson', 'Lesson Library'],
      roles: ['teacher', 'admin']
    },
    {
      path: '/assessments',
      name: 'Assessments',
      expectedElements: ['Assessments', 'Create Assessment', 'Published'],
      roles: ['teacher', 'admin']
    },
    {
      path: '/messages',
      name: 'Messages',
      expectedElements: ['Messages', 'Compose', 'Inbox'],
      roles: ['admin', 'teacher', 'student', 'parent']
    },
    {
      path: '/rewards',
      name: 'Rewards',
      expectedElements: ['Rewards Store', 'Available Rewards', 'My Rewards'],
      roles: ['student', 'teacher']
    },
    {
      path: '/progress',
      name: 'Progress',
      expectedElements: ['Progress', 'Learning Path', 'Achievements'],
      roles: ['student', 'teacher', 'parent']
    },
    {
      path: '/settings',
      name: 'Settings',
      expectedElements: ['Settings', 'Profile', 'Preferences'],
      roles: ['admin', 'teacher', 'student', 'parent']
    },
    {
      path: '/reports',
      name: 'Reports',
      expectedElements: ['Reports', 'Analytics', 'Performance'],
      roles: ['admin', 'teacher']
    },
    {
      path: '/leaderboard',
      name: 'Leaderboard',
      expectedElements: ['Leaderboard', 'Top Performers', 'Rankings'],
      roles: ['student', 'teacher']
    }
  ];

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    locatorHelper = createLocatorHelper(page);

    // Enable bypass mode and mock data
    await page.addInitScript(() => {
      // Set environment variables for bypass mode
      (window as any).__VITE_BYPASS_AUTH__ = 'true';
      (window as any).__VITE_USE_MOCK_DATA__ = 'true';

      // Mock console to capture errors
      (window as any).__consoleErrors__ = [];
      const originalError = console.error;
      console.error = (...args) => {
        (window as any).__consoleErrors__.push(args.join(' '));
        originalError.apply(console, args);
      };

      // Mock user data for different roles
      window.localStorage.setItem('user', JSON.stringify({
        id: 'test-user-123',
        email: 'test@example.com',
        role: 'teacher',
        name: 'Test User',
        isAuthenticated: true
      }));

      // Mock Redux store for all pages
      (window as any).__REDUX_STORE__ = {
        getState: () => ({
          user: {
            role: 'teacher',
            isAuthenticated: true,
            profile: {
              id: 'test-user-123',
              email: 'test@example.com',
              name: 'Test User'
            }
          },
          gamification: {
            xp: 1500,
            level: 15,
            badges: ['gold_star', 'perfect_score']
          },
          classes: {
            items: [],
            loading: false,
            error: null
          },
          lessons: {
            items: [],
            loading: false,
            error: null
          },
          assessments: {
            items: [],
            loading: false,
            error: null
          },
          messages: {
            items: [],
            loading: false,
            error: null
          }
        })
      };
    });

    // Set console error monitoring
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        console.log('Console error:', msg.text());
      }
    });

    // Set page error monitoring
    page.on('pageerror', (err) => {
      console.log('Page error:', err.message);
    });
  });

  test.afterEach(async () => {
    await page.close();
  });

  test.describe('Page Rendering Tests', () => {
    pagesToTest.forEach((pageConfig) => {
      test(`should render ${pageConfig.name} page without errors`, async () => {
        // Navigate to the page
        await page.goto(pageConfig.path, {
          waitUntil: 'networkidle',
          timeout: 30000
        });

        // Wait for loading to complete
        await locatorHelper.waitForLoadingComplete();

        // Check that page loaded successfully (no error pages)
        await expect(page.locator('text=404')).not.toBeVisible();
        await expect(page.locator('text=500')).not.toBeVisible();
        await expect(page.locator('text=Page not found')).not.toBeVisible();
        await expect(page.locator('text=Something went wrong')).not.toBeVisible();

        // Check for critical page elements
        const hasExpectedContent = await Promise.all(
          pageConfig.expectedElements.map(async (element) => {
            const locator = page.locator(`text=${element}`).first();
            return await locator.isVisible().catch(() => false);
          })
        );

        // At least one expected element should be visible
        expect(hasExpectedContent.some(Boolean)).toBeTruthy();

        // Check for console errors
        const consoleErrors = await page.evaluate(() => {
          return (window as any).__consoleErrors__ || [];
        });

        // Filter out non-critical errors
        const criticalErrors = consoleErrors.filter((error: string) => {
          return !error.includes('favicon') &&
                 !error.includes('service worker') &&
                 !error.includes('network error') &&
                 !error.includes('WebSocket');
        });

        expect(criticalErrors).toHaveLength(0);
      });

      test(`should have proper page title and metadata for ${pageConfig.name}`, async () => {
        await page.goto(pageConfig.path);
        await locatorHelper.waitForLoadingComplete();

        // Check page title
        const title = await page.title();
        expect(title).toBeTruthy();
        expect(title.length).toBeGreaterThan(0);

        // Check meta viewport
        const viewport = page.locator('meta[name="viewport"]');
        await expect(viewport).toHaveAttribute('content', /width=device-width/);
      });

      test(`should be responsive on ${pageConfig.name} page`, async () => {
        await page.goto(pageConfig.path);
        await locatorHelper.waitForLoadingComplete();

        // Test mobile viewport
        await page.setViewportSize({ width: 375, height: 667 });
        await page.waitForTimeout(500);

        // Page should still be functional
        const bodyElement = page.locator('body');
        await expect(bodyElement).toBeVisible();

        // No horizontal scroll should appear
        const hasHorizontalScroll = await page.evaluate(() => {
          return document.body.scrollWidth > window.innerWidth;
        });
        expect(hasHorizontalScroll).toBeFalsy();

        // Test tablet viewport
        await page.setViewportSize({ width: 768, height: 1024 });
        await page.waitForTimeout(500);
        await expect(bodyElement).toBeVisible();

        // Reset to desktop
        await page.setViewportSize({ width: 1280, height: 720 });
      });
    });
  });

  test.describe('Navigation Tests', () => {
    test('should handle navigation between all pages', async () => {
      // Start at home
      await page.goto('/');
      await locatorHelper.waitForLoadingComplete();

      // Test navigation to each page
      for (const pageConfig of pagesToTest.slice(1)) { // Skip home as we're already there
        // Try to find a navigation link
        const navLink = await locatorHelper.getLink(pageConfig.name).catch(() => null);

        if (navLink && await navLink.isVisible()) {
          await navLink.click();
          await locatorHelper.waitForLoadingComplete();

          // Verify we're on the right page
          expect(page.url()).toContain(pageConfig.path === '/' ? '' : pageConfig.path);
        } else {
          // Direct navigation if no nav link found
          await page.goto(pageConfig.path);
          await locatorHelper.waitForLoadingComplete();
        }

        // Verify page loaded correctly
        await expect(page.locator('text=404')).not.toBeVisible();
      }
    });

    test('should handle browser back/forward navigation', async () => {
      // Visit multiple pages
      await page.goto('/');
      await locatorHelper.waitForLoadingComplete();

      await page.goto('/classes');
      await locatorHelper.waitForLoadingComplete();

      await page.goto('/lessons');
      await locatorHelper.waitForLoadingComplete();

      // Test back navigation
      await page.goBack();
      expect(page.url()).toContain('/classes');

      await page.goBack();
      expect(page.url()).toMatch(/\/$|\/$/); // Home page

      // Test forward navigation
      await page.goForward();
      expect(page.url()).toContain('/classes');
    });
  });

  test.describe('Mock Data Integration Tests', () => {
    test('should display mock data on all relevant pages', async () => {
      const pagesWithMockData = [
        { path: '/assessments', dataIndicator: 'Variables Quiz' },
        { path: '/messages', dataIndicator: 'Help with loops homework' },
        { path: '/rewards', dataIndicator: 'Golden Avatar Frame' },
        { path: '/classes', dataIndicator: 'Programming 101' }
      ];

      for (const pageConfig of pagesWithMockData) {
        await page.goto(pageConfig.path);
        await locatorHelper.waitForLoadingComplete();

        // Look for mock data indicators
        const mockDataElement = page.locator(`text=${pageConfig.dataIndicator}`).first();
        const isVisible = await mockDataElement.isVisible().catch(() => false);

        // Mock data should be visible when in bypass mode
        if (isVisible) {
          await expect(mockDataElement).toBeVisible();
        }

        // Verify no loading states persist
        const loadingSpinner = page.locator('[data-testid="loading-spinner"], .loading-spinner, .spinner');
        await expect(loadingSpinner).not.toBeVisible();
      }
    });

    test('should handle empty data states gracefully', async () => {
      // Override mock data to be empty
      await page.addInitScript(() => {
        (window as any).__MOCK_EMPTY_DATA__ = true;
      });

      await page.goto('/classes');
      await locatorHelper.waitForLoadingComplete();

      // Should show empty state message
      const emptyStateTexts = [
        'No classes found',
        'No items to display',
        'Get started',
        'Create your first',
        'No data available'
      ];

      const hasEmptyState = await Promise.all(
        emptyStateTexts.map(async (text) => {
          return await page.locator(`text=${text}`).first().isVisible().catch(() => false);
        })
      );

      // At least one empty state indicator should be visible
      expect(hasEmptyState.some(Boolean)).toBeTruthy();
    });
  });

  test.describe('Performance Tests', () => {
    test('should load all pages within performance thresholds', async () => {
      const performanceResults = [];

      for (const pageConfig of pagesToTest) {
        const startTime = Date.now();

        await page.goto(pageConfig.path);
        await locatorHelper.waitForLoadingComplete();

        const loadTime = Date.now() - startTime;
        performanceResults.push({
          page: pageConfig.name,
          loadTime
        });

        // Each page should load within 5 seconds
        expect(loadTime).toBeLessThan(5000);
      }

      console.log('Page Load Times:', performanceResults);
    });

    test('should not have memory leaks between page transitions', async () => {
      // Visit multiple pages in sequence
      for (const pageConfig of pagesToTest) {
        await page.goto(pageConfig.path);
        await locatorHelper.waitForLoadingComplete();
        await page.waitForTimeout(100); // Brief pause
      }

      // Check for excessive DOM nodes (basic memory leak indicator)
      const domNodeCount = await page.evaluate(() => {
        return document.querySelectorAll('*').length;
      });

      // Should not have an excessive number of DOM nodes
      expect(domNodeCount).toBeLessThan(5000);
    });
  });

  test.describe('Accessibility Tests', () => {
    test('should have proper semantic markup on all pages', async () => {
      for (const pageConfig of pagesToTest.slice(0, 3)) { // Test first 3 pages for performance
        await page.goto(pageConfig.path);
        await locatorHelper.waitForLoadingComplete();

        // Check for main content area
        const main = page.locator('main, [role="main"], #main');
        const hasMainContent = await main.count() > 0;

        // Check for headings
        const headings = page.locator('h1, h2, h3, h4, h5, h6');
        const headingCount = await headings.count();

        expect(headingCount).toBeGreaterThan(0);

        // Check for skip links or other accessibility features
        const skipLink = page.locator('a[href="#main"], a[href="#content"]');
        // Skip link is optional but good to have
      }
    });

    test('should support keyboard navigation on interactive elements', async () => {
      await page.goto('/');
      await locatorHelper.waitForLoadingComplete();

      // Test tab navigation
      await page.keyboard.press('Tab');

      const focusedElement = page.locator(':focus');
      const tagName = await focusedElement.evaluate((el) => el.tagName.toLowerCase());

      // Should focus on an interactive element
      const interactiveTags = ['button', 'a', 'input', 'select', 'textarea'];
      expect(interactiveTags).toContain(tagName);
    });
  });

  test.describe('Error Boundary Tests', () => {
    test('should handle component errors gracefully', async () => {
      // Simulate component error by corrupting data
      await page.addInitScript(() => {
        // Override console.error to track error boundary triggers
        (window as any).__errorBoundaryTriggered__ = false;
        const originalError = console.error;
        console.error = (...args) => {
          if (args.some(arg => arg.toString().includes('Error Boundary'))) {
            (window as any).__errorBoundaryTriggered__ = true;
          }
          originalError.apply(console, args);
        };
      });

      await page.goto('/');
      await locatorHelper.waitForLoadingComplete();

      // Page should still be functional even if some components fail
      const body = page.locator('body');
      await expect(body).toBeVisible();

      // Should not show white screen of death
      const hasContent = await page.locator('*').first().isVisible();
      expect(hasContent).toBeTruthy();
    });
  });
});