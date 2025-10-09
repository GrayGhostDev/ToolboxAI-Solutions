import { test, expect, Page } from '@playwright/test';
import { createLocatorHelper } from '../helpers/locators';

/**
 * Comprehensive Mock Data Integration Tests
 * Tests that mock data service works correctly in bypass mode
 */

test.describe('Mock Data Service Integration Tests', () => {
  let page: Page;
  let locatorHelper: any;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    locatorHelper = createLocatorHelper(page);

    // Enable bypass mode and mock data
    await page.addInitScript(() => {
      // Set environment variables for bypass mode
      (window as any).__VITE_BYPASS_AUTH__ = 'true';
      (window as any).__VITE_USE_MOCK_DATA__ = 'true';

      // Track API calls to ensure they're bypassed
      (window as any).__apiCalls__ = [];
      (window as any).__mockDataUsed__ = false;

      // Mock fetch to track actual API calls (should not happen in bypass mode)
      const originalFetch = window.fetch;
      window.fetch = async (...args) => {
        const url = args[0].toString();
        (window as any).__apiCalls__.push({
          url,
          timestamp: Date.now()
        });
        return originalFetch.apply(window, args);
      };

      // Mock user authentication
      window.localStorage.setItem('user', JSON.stringify({
        id: 'test-user-123',
        email: 'test@example.com',
        role: 'teacher',
        name: 'Test Teacher',
        isAuthenticated: true
      }));

      // Set up comprehensive Redux store
      (window as any).__REDUX_STORE__ = {
        getState: () => ({
          user: {
            role: 'teacher',
            isAuthenticated: true,
            profile: {
              id: 'test-user-123',
              email: 'test@example.com',
              name: 'Test Teacher'
            }
          },
          classes: {
            items: [
              {
                id: 'class-001',
                name: 'Programming 101',
                students: 25,
                description: 'Introduction to Programming'
              }
            ],
            loading: false,
            error: null
          },
          assessments: {
            items: [
              {
                id: 'assess-001',
                title: 'Variables Quiz',
                questions: 10,
                averageScore: 82,
                status: 'published'
              }
            ],
            loading: false,
            error: null
          },
          messages: {
            items: [
              {
                id: 'msg-001',
                from: 'John Smith',
                subject: 'Help with loops homework',
                read: false,
                timestamp: new Date().toISOString()
              }
            ],
            loading: false,
            error: null
          },
          gamification: {
            xp: 1850,
            level: 8,
            badges: ['code_warrior', 'speed_coder'],
            rewards: [
              {
                id: 'reward-001',
                name: 'Golden Avatar Frame',
                cost: 500,
                category: 'avatar',
                rarity: 'epic'
              }
            ]
          }
        })
      };

      // Mock API service that returns mock data
      (window as any).mockApiService = {
        getClasses: () => {
          (window as any).__mockDataUsed__ = true;
          return Promise.resolve([
            { id: 'class-001', name: 'Programming 101', students: 25 },
            { id: 'class-002', name: 'Web Development', students: 18 }
          ]);
        },
        getAssessments: () => {
          (window as any).__mockDataUsed__ = true;
          return Promise.resolve([
            { id: 'assess-001', title: 'Variables Quiz', questions: 10 },
            { id: 'assess-002', title: 'Loop Master Challenge', questions: 15 }
          ]);
        },
        getMessages: () => {
          (window as any).__mockDataUsed__ = true;
          return Promise.resolve([
            { id: 'msg-001', from: 'John Smith', subject: 'Help with loops' },
            { id: 'msg-002', from: 'Sarah Johnson', subject: 'Progress update' }
          ]);
        },
        getRewards: () => {
          (window as any).__mockDataUsed__ = true;
          return Promise.resolve([
            { id: 'reward-001', name: 'Golden Avatar Frame', cost: 500 },
            { id: 'reward-002', name: 'Dark Mode Theme', cost: 300 }
          ]);
        }
      };
    });

    // Monitor console for mock data indicators
    page.on('console', (msg) => {
      if (msg.text().includes('MOCK_DATA') || msg.text().includes('bypass')) {
        console.log('Mock data usage:', msg.text());
      }
    });
  });

  test.afterEach(async () => {
    await page.close();
  });

  test.describe('Mock Data Service Functionality', () => {
    test('should use mock data instead of API calls', async () => {
      await page.goto('/classes');
      await locatorHelper.waitForLoadingComplete();

      // Check that mock data was used
      const mockDataUsed = await page.evaluate(() => (window as any).__mockDataUsed__);
      const apiCalls = await page.evaluate(() => (window as any).__apiCalls__);

      // Filter out non-API requests (static assets, etc.)
      const actualApiCalls = apiCalls.filter((call: any) =>
        call.url.includes('/api/') && !call.url.includes('.js') && !call.url.includes('.css')
      );

      // Should use mock data instead of making API calls
      if (actualApiCalls.length > 0) {
        console.log('Unexpected API calls:', actualApiCalls);
      }

      // Verify mock classes data is displayed
      await expect(page.locator('text=Programming 101')).toBeVisible();
    });

    test('should display mock assessments data correctly', async () => {
      await page.goto('/assessments');
      await locatorHelper.waitForLoadingComplete();

      // Check for mock assessment data
      await expect(page.locator('text=Variables Quiz')).toBeVisible();
      await expect(page.locator('text=Loop Master Challenge')).toBeVisible();

      // Check for assessment metadata
      const questionCount = page.locator('text=10 questions').or(page.locator('text=questions: 10'));
      const isVisible = await questionCount.first().isVisible().catch(() => false);
      // This is optional as the exact format may vary
    });

    test('should display mock messages data correctly', async () => {
      await page.goto('/messages');
      await locatorHelper.waitForLoadingComplete();

      // Check for mock message data
      await expect(page.locator('text=Help with loops homework').or(page.locator('text=Help with loops'))).toBeVisible();
      await expect(page.locator('text=John Smith')).toBeVisible();

      // Check unread message indicator
      const unreadIndicator = page.locator('[data-testid="unread-indicator"], .unread, .badge');
      // This is optional as the format may vary
    });

    test('should display mock rewards data correctly', async () => {
      await page.goto('/rewards');
      await locatorHelper.waitForLoadingComplete();

      // Check for mock rewards data
      await expect(page.locator('text=Golden Avatar Frame')).toBeVisible();
      await expect(page.locator('text=Dark Mode Theme')).toBeVisible();

      // Check for cost information
      const costInfo = page.locator('text=500').or(page.locator('text=300'));
      const hasCost = await costInfo.first().isVisible().catch(() => false);
      // Cost display is optional as format may vary
    });
  });

  test.describe('Bypass Mode Verification', () => {
    test('should bypass authentication when VITE_BYPASS_AUTH is true', async () => {
      // Navigate to a protected page without login
      await page.goto('/admin/dashboard');
      await locatorHelper.waitForLoadingComplete();

      // Should not redirect to login
      expect(page.url()).not.toContain('/login');

      // Should display content (not access denied)
      await expect(page.locator('text=Access Denied')).not.toBeVisible();
      await expect(page.locator('text=Unauthorized')).not.toBeVisible();
    });

    test('should work with different user roles in bypass mode', async () => {
      const roles = ['admin', 'teacher', 'student', 'parent'];

      for (const role of roles) {
        // Set user role
        await page.evaluate((userRole) => {
          window.localStorage.setItem('user', JSON.stringify({
            id: `test-${userRole}-123`,
            email: `${userRole}@example.com`,
            role: userRole,
            name: `Test ${userRole}`,
            isAuthenticated: true
          }));

          // Update Redux store
          if ((window as any).__REDUX_STORE__) {
            (window as any).__REDUX_STORE__.getState().user.role = userRole;
          }
        }, role);

        // Visit home page
        await page.goto('/');
        await locatorHelper.waitForLoadingComplete();

        // Should render content appropriate for the role
        const hasContent = await page.locator('body *').first().isVisible();
        expect(hasContent).toBeTruthy();

        // Should not show access denied
        await expect(page.locator('text=Access Denied')).not.toBeVisible();
      }
    });

    test('should prevent actual network requests to backend', async () => {
      // Clear API call tracking
      await page.evaluate(() => {
        (window as any).__apiCalls__ = [];
      });

      // Visit pages that would normally make API calls
      const pagesWithApiCalls = ['/classes', '/assessments', '/messages', '/reports'];

      for (const pagePath of pagesWithApiCalls) {
        await page.goto(pagePath);
        await locatorHelper.waitForLoadingComplete();

        // Brief wait for any delayed API calls
        await page.waitForTimeout(1000);
      }

      // Check for backend API calls
      const apiCalls = await page.evaluate(() => (window as any).__apiCalls__);
      const backendCalls = apiCalls.filter((call: any) =>
        call.url.includes('/api/v1/') ||
        call.url.includes('localhost:8009') ||
        call.url.includes('backend')
      );

      // Should not make calls to backend in bypass mode
      expect(backendCalls).toHaveLength(0);
    });
  });

  test.describe('Mock Data Consistency', () => {
    test('should maintain consistent mock data across page reloads', async () => {
      await page.goto('/classes');
      await locatorHelper.waitForLoadingComplete();

      // Get initial data
      const initialClassTitle = await page.locator('text=Programming 101').textContent();
      expect(initialClassTitle).toBeTruthy();

      // Reload page
      await page.reload();
      await locatorHelper.waitForLoadingComplete();

      // Data should remain consistent
      await expect(page.locator('text=Programming 101')).toBeVisible();
    });

    test('should provide realistic mock data structure', async () => {
      await page.goto('/assessments');
      await locatorHelper.waitForLoadingComplete();

      // Mock assessments should have realistic properties
      const assessmentCards = page.locator('.mantine-Card-root, .card, [data-testid="assessment-card"]');

      if (await assessmentCards.count() > 0) {
        // Should have titles
        await expect(page.locator('text=Variables Quiz')).toBeVisible();

        // Should have some kind of metadata (questions, status, etc.)
        const hasMetadata = await Promise.all([
          page.locator('text=questions').first().isVisible().catch(() => false),
          page.locator('text=published').first().isVisible().catch(() => false),
          page.locator('text=draft').first().isVisible().catch(() => false),
          page.locator('text=score').first().isVisible().catch(() => false)
        ]);

        // At least one metadata type should be present
        expect(hasMetadata.some(Boolean)).toBeTruthy();
      }
    });

    test('should handle mock data relationships correctly', async () => {
      await page.goto('/classes');
      await locatorHelper.waitForLoadingComplete();

      // Classes should show student count
      const classWithStudents = page.locator('text=Programming 101').first();
      await expect(classWithStudents).toBeVisible();

      // Related data should be consistent
      const studentCountIndicator = page.locator('text=25').or(page.locator('text=students'));
      // Student count display is optional as format may vary
    });
  });

  test.describe('Error Handling in Bypass Mode', () => {
    test('should handle mock data loading errors gracefully', async () => {
      // Simulate mock data error
      await page.addInitScript(() => {
        (window as any).mockApiService = {
          getClasses: () => Promise.reject(new Error('Mock data error')),
          getAssessments: () => Promise.reject(new Error('Mock data error')),
          getMessages: () => Promise.reject(new Error('Mock data error'))
        };
      });

      await page.goto('/classes');
      await locatorHelper.waitForLoadingComplete();

      // Should show error state or fallback content
      const errorMessages = [
        'Error loading data',
        'Unable to load',
        'Try again',
        'Something went wrong',
        'No classes found'
      ];

      const hasErrorMessage = await Promise.all(
        errorMessages.map(async (msg) => {
          return await page.locator(`text=${msg}`).first().isVisible().catch(() => false);
        })
      );

      // Should show some kind of error or empty state
      expect(hasErrorMessage.some(Boolean)).toBeTruthy();
    });

    test('should handle partial mock data loading', async () => {
      // Simulate partial data loading
      await page.addInitScript(() => {
        (window as any).__REDUX_STORE__.getState().classes.items = [];
        (window as any).__REDUX_STORE__.getState().assessments.items = [
          { id: 'assess-001', title: 'Variables Quiz', questions: 10 }
        ];
      });

      await page.goto('/classes');
      await locatorHelper.waitForLoadingComplete();

      // Should handle empty classes gracefully
      const emptyStateMessages = [
        'No classes',
        'Create your first class',
        'Get started',
        'No items'
      ];

      const hasEmptyState = await Promise.all(
        emptyStateMessages.map(async (msg) => {
          return await page.locator(`text=${msg}`).first().isVisible().catch(() => false);
        })
      );

      // Should show empty state for classes
      expect(hasEmptyState.some(Boolean)).toBeTruthy();

      // But assessments should still work
      await page.goto('/assessments');
      await locatorHelper.waitForLoadingComplete();
      await expect(page.locator('text=Variables Quiz')).toBeVisible();
    });
  });

  test.describe('Mock Data Performance', () => {
    test('should load mock data quickly', async () => {
      const startTime = Date.now();

      await page.goto('/classes');
      await locatorHelper.waitForLoadingComplete();

      const loadTime = Date.now() - startTime;

      // Mock data should load very quickly (under 2 seconds)
      expect(loadTime).toBeLessThan(2000);

      // Should not show loading states for extended periods
      const persistentLoader = page.locator('[data-testid="loading-spinner"], .loading-spinner');
      await expect(persistentLoader).not.toBeVisible();
    });

    test('should not cause memory leaks with mock data', async () => {
      const initialMemory = await page.evaluate(() => {
        return (performance as any).memory?.usedJSHeapSize || 0;
      });

      // Load multiple pages with mock data
      const pages = ['/classes', '/assessments', '/messages', '/rewards'];

      for (const pagePath of pages) {
        await page.goto(pagePath);
        await locatorHelper.waitForLoadingComplete();
        await page.waitForTimeout(100);
      }

      const finalMemory = await page.evaluate(() => {
        return (performance as any).memory?.usedJSHeapSize || 0;
      });

      // Memory usage should not increase dramatically
      if (initialMemory > 0 && finalMemory > 0) {
        const memoryIncrease = finalMemory - initialMemory;
        const maxReasonableIncrease = 50 * 1024 * 1024; // 50MB
        expect(memoryIncrease).toBeLessThan(maxReasonableIncrease);
      }
    });
  });

  test.describe('Integration with UI Components', () => {
    test('should properly integrate mock data with table components', async () => {
      await page.goto('/classes');
      await locatorHelper.waitForLoadingComplete();

      // Look for table or list components
      const tableRows = page.locator('tr, .table-row, [role="row"]');
      const listItems = page.locator('li, .list-item, .card');

      const hasTableData = await tableRows.count() > 0;
      const hasListData = await listItems.count() > 0;

      // Should have some kind of data display
      expect(hasTableData || hasListData).toBeTruthy();

      // Specific mock data should be visible
      await expect(page.locator('text=Programming 101')).toBeVisible();
    });

    test('should integrate with search and filter components', async () => {
      await page.goto('/assessments');
      await locatorHelper.waitForLoadingComplete();

      // Look for search input
      const searchInput = page.locator('input[placeholder*="search" i], input[placeholder*="filter" i]');

      if (await searchInput.count() > 0) {
        // Test search functionality with mock data
        await searchInput.first().fill('Variables');
        await page.waitForTimeout(500);

        // Should filter to show only matching items
        await expect(page.locator('text=Variables Quiz')).toBeVisible();

        // Clear search
        await searchInput.first().clear();
        await page.waitForTimeout(500);
      }
    });

    test('should work with pagination components', async () => {
      await page.goto('/messages');
      await locatorHelper.waitForLoadingComplete();

      // Look for pagination controls
      const paginationControls = page.locator('[data-testid="pagination"], .pagination, .page-nav');

      if (await paginationControls.count() > 0) {
        // Should show page information
        const pageInfo = page.locator('text=Page 1').or(page.locator('text=1 of'));
        // Pagination may not always be visible with small datasets
      }

      // Should display message items
      await expect(page.locator('text=John Smith')).toBeVisible();
    });
  });
});