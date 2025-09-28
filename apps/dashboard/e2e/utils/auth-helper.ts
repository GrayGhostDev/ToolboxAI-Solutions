/**
 * E2E Authentication Helper
 * Supports both mock and real Clerk authentication for testing
 */

import { Page } from '@playwright/test';

export interface TestCredentials {
  email: string;
  password: string;
  role: 'admin' | 'teacher' | 'student';
}

export const TEST_CREDENTIALS: Record<string, TestCredentials> = {
  admin: {
    email: 'admin@toolboxai.com',
    password: 'Admin123!',
    role: 'admin'
  },
  teacher: {
    email: 'jane.smith@school.edu',
    password: 'Teacher123!',
    role: 'teacher'
  },
  student: {
    email: 'alex.johnson@student.edu',
    password: 'Student123!',
    role: 'student'
  }
};

export type AuthMode = 'mock' | 'real';

/**
 * Mock authentication for E2E tests
 * Bypasses Clerk entirely and sets up mock auth state
 */
export const mockAuthentication = async (
  page: Page,
  role: 'admin' | 'teacher' | 'student' = 'student'
) => {
  const credentials = TEST_CREDENTIALS[role];

  // Inject mock authentication state before page loads
  await page.addInitScript((creds) => {
    // Mock localStorage auth tokens
    localStorage.setItem('mock_auth_token', 'mock-jwt-token');
    localStorage.setItem('mock_refresh_token', 'mock-refresh-token');
    localStorage.setItem('mock_user_role', creds.role);
    localStorage.setItem('mock_user_email', creds.email);
    localStorage.setItem('mock_auth_state', 'authenticated');

    // Mock Clerk globals if they exist
    if (typeof window !== 'undefined') {
      (window as any).__CLERK_MOCK_STATE__ = {
        isSignedIn: true,
        user: {
          id: `mock-user-${creds.role}`,
          primaryEmailAddress: { emailAddress: creds.email },
          publicMetadata: { role: creds.role },
          firstName: creds.role.charAt(0).toUpperCase() + creds.role.slice(1),
          lastName: 'User'
        },
        session: {
          id: 'mock-session-id',
          status: 'active'
        }
      };
    }
  }, credentials);

  // Also set up API interception for auth endpoints if needed
  await page.route('**/api/v1/auth/**', (route) => {
    const url = route.request().url();
    if (url.includes('/login')) {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          accessToken: 'mock-jwt-token',
          refreshToken: 'mock-refresh-token',
          user: {
            id: `mock-user-${credentials.role}`,
            email: credentials.email,
            role: credentials.role
          }
        })
      });
    } else if (url.includes('/logout')) {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true })
      });
    } else {
      route.continue();
    }
  });
};

/**
 * Real Clerk authentication for E2E tests
 * Uses actual Clerk authentication flow
 */
export const realAuthentication = async (
  page: Page,
  role: 'admin' | 'teacher' | 'student' = 'student'
) => {
  const credentials = TEST_CREDENTIALS[role];

  // Navigate to login page
  await page.goto('/login');

  // Wait for Clerk authentication form to load
  await page.waitForSelector('input[name="identifier"], input[id="identifier-field"]', {
    state: 'visible',
    timeout: 10000
  });

  // Fill in credentials using Clerk-specific selectors
  await page.locator('input[name="identifier"], input[id="identifier-field"]').fill(credentials.email);
  await page.locator('input[name="password"], input[id="password-field"]').fill(credentials.password);

  // Submit the form
  await page.locator('button[type="submit"], button:has-text("Continue")').click();

  // Wait for successful authentication
  await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 30000 });
};

/**
 * Generic authentication function that chooses mock or real based on environment
 */
export const authenticate = async (
  page: Page,
  role: 'admin' | 'teacher' | 'student' = 'student',
  mode: AuthMode = process.env.E2E_AUTH_MODE as AuthMode || 'mock'
) => {
  if (mode === 'mock') {
    await mockAuthentication(page, role);
  } else {
    await realAuthentication(page, role);
  }
};

/**
 * Clear authentication state
 */
export const clearAuth = async (page: Page) => {
  await page.evaluate(() => {
    // Clear localStorage
    localStorage.clear();
    sessionStorage.clear();

    // Clear any Clerk state
    if ((window as any).__CLERK_MOCK_STATE__) {
      delete (window as any).__CLERK_MOCK_STATE__;
    }
  });
};

/**
 * Verify authentication state
 */
export const verifyAuthenticated = async (page: Page, role?: string) => {
  const isAuthenticated = await page.evaluate(() => {
    // Check for auth tokens
    const hasToken = localStorage.getItem('mock_auth_token') ||
                    localStorage.getItem('auth_token') ||
                    sessionStorage.getItem('auth_token');

    // Check for Clerk state
    const hasClerkState = (window as any).__CLERK_MOCK_STATE__?.isSignedIn ||
                         document.querySelector('[data-clerk-loaded="true"]');

    return !!(hasToken || hasClerkState);
  });

  if (role) {
    const userRole = await page.evaluate(() => {
      return localStorage.getItem('mock_user_role') ||
             (window as any).__CLERK_MOCK_STATE__?.user?.publicMetadata?.role;
    });
    return isAuthenticated && userRole === role;
  }

  return isAuthenticated;
};

/**
 * Logout helper
 */
export const logout = async (page: Page, mode: AuthMode = 'mock') => {
  if (mode === 'mock') {
    // Clear mock auth state
    await clearAuth(page);
    await page.goto('/login');
  } else {
    // Use real Clerk logout
    const logoutButton = page.locator('[data-testid="clerk-user-button"], button:has-text("Sign Out")');
    if (await logoutButton.isVisible()) {
      await logoutButton.click();
    }
    await page.waitForURL('**/login', { timeout: 10000 });
  }
};

/**
 * Setup authentication interceptors for mock mode
 */
export const setupAuthInterceptors = async (page: Page) => {
  // Intercept Clerk API calls and return mock responses
  await page.route('**/clerk/v1/**', (route) => {
    const url = route.request().url();
    if (url.includes('/sessions')) {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'mock-session-id',
          status: 'active',
          user: {
            id: 'mock-user-id',
            primary_email_address: { email_address: 'test@example.com' }
          }
        })
      });
    } else {
      route.continue();
    }
  });

  // Intercept our own auth endpoints
  await page.route('**/pusher/auth', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        auth: 'mock-pusher-auth'
      })
    });
  });
};

export default {
  authenticate,
  mockAuthentication,
  realAuthentication,
  clearAuth,
  verifyAuthenticated,
  logout,
  setupAuthInterceptors,
  TEST_CREDENTIALS
};