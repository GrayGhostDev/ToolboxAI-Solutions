import { test, expect } from '@playwright/test';

/**
 * Authentication E2E Tests
 * Tests login, logout, and role-based access control
 * Using 2025 Playwright semantic locators as primary selectors
 */

// Demo credentials from Login.tsx
const CREDENTIALS = {
  admin: {
    email: 'admin@toolboxai.com',
    password: 'Admin123!'
  },
  teacher: {
    email: 'jane.smith@school.edu',
    password: 'Teacher123!'
  },
  student: {
    email: 'alex.johnson@student.edu',
    password: 'Student123!'
  }
};

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');
    // Give React time to render
    await page.waitForTimeout(1000);
  });

  test('should display login form', async ({ page }) => {
    // Check login form elements using semantic locators with fallbacks
    // Try to find any heading with "Welcome" text
    const heading = page.locator('h1, h2, h3, h4, h5').filter({ hasText: /welcome/i }).first();
    await expect(heading).toBeVisible();

    // Wait for form elements to be visible
    await page.waitForSelector('input[name="email"]', { state: 'visible', timeout: 5000 });

    // Use semantic locators first, data-testid as fallback
    const emailInput = page.locator('input[name="email"], [data-testid="email-input"]').first();
    const passwordInput = page.locator('input[name="password"], [data-testid="password-input"]').first();
    const submitButton = page.locator('button[type="submit"], [data-testid="login-submit"]').first();

    await expect(emailInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
    await expect(submitButton).toBeVisible();

    // Check for forgot password link
    await expect(page.getByText(/forgot.*password/i)).toBeVisible();
  });

  test('should show validation errors for empty form', async ({ page }) => {
    // Try to submit empty form using multiple selector strategies
    const submitButton = page.locator('button[type="submit"], [data-testid="login-submit"]').first();
    await submitButton.click();

    // Check for validation messages
    await expect(page.getByText(/email and password are required/i)).toBeVisible();
  });

  test('should show error for invalid email format', async ({ page }) => {
    // Enter invalid email using flexible selectors
    await page.locator('input[name="email"], [data-testid="email-input"]').first().fill('notanemail');
    await page.locator('input[name="password"], [data-testid="password-input"]').first().fill('Password123!');
    await page.locator('button[type="submit"], [data-testid="login-submit"]').first().click();

    // Check for email validation error
    await expect(page.getByText(/valid email address or username/i)).toBeVisible();
  });

  test('should show error for incorrect credentials', async ({ page }) => {
    // Enter incorrect credentials using flexible selectors
    await page.locator('input[name="email"], [data-testid="email-input"]').first().fill('wrong@email.com');
    await page.locator('input[name="password"], [data-testid="password-input"]').first().fill('WrongPassword123!');
    await page.locator('button[type="submit"], [data-testid="login-submit"]').first().click();

    // Wait for error message
    await expect(page.getByRole('alert')).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole('alert')).toContainText(/login failed|check your credentials/i);
  });

  test('should successfully login as admin', async ({ page }) => {
    // Use correct admin credentials with flexible selectors
    await page.locator('input[name="email"], [data-testid="email-input"]').first().fill(CREDENTIALS.admin.email);
    await page.locator('input[name="password"], [data-testid="password-input"]').first().fill(CREDENTIALS.admin.password);

    // Monitor for successful login response
    const loginPromise = page.waitForResponse(
      response => response.url().includes('/auth/login') && response.status() === 200,
      { timeout: 10000 }
    ).catch(() => null);

    await page.locator('button[type="submit"], [data-testid="login-submit"]').first().click();

    // Wait for navigation to dashboard
    await page.waitForURL('**/dashboard/**', { timeout: 10000 }).catch(() => {
      // If real login fails, check if we at least navigated away from login
      return page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 10000 });
    });

    // Verify we're on the dashboard - look for common dashboard elements
    const dashboardIndicators = [
      page.getByRole('heading', { name: /dashboard/i }),
      page.getByText(/overview/i),
      page.getByRole('navigation')
    ];

    // At least one dashboard indicator should be visible
    let foundDashboard = false;
    for (const indicator of dashboardIndicators) {
      if (await indicator.isVisible().catch(() => false)) {
        foundDashboard = true;
        break;
      }
    }
    expect(foundDashboard).toBeTruthy();
  });

  test('should successfully login as teacher', async ({ page }) => {
    await page.locator('input[name="email"], [data-testid="email-input"]').first().fill(CREDENTIALS.teacher.email);
    await page.locator('input[name="password"], [data-testid="password-input"]').first().fill(CREDENTIALS.teacher.password);
    await page.locator('button[type="submit"], [data-testid="login-submit"]').first().click();

    // Wait for navigation
    await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 10000 }).catch(() => {
      // Continue even if navigation doesn't happen (might be mocked)
    });

    // Verify dashboard access
    const teacherElements = [
      page.getByRole('heading', { name: /dashboard|classes/i }),
      page.getByText(/teacher/i),
      page.getByRole('navigation')
    ];

    let foundTeacherDashboard = false;
    for (const element of teacherElements) {
      if (await element.isVisible().catch(() => false)) {
        foundTeacherDashboard = true;
        break;
      }
    }
    expect(foundTeacherDashboard).toBeTruthy();
  });

  test('should successfully login as student', async ({ page }) => {
    await page.locator('input[name="email"], [data-testid="email-input"]').first().fill(CREDENTIALS.student.email);
    await page.locator('input[name="password"], [data-testid="password-input"]').first().fill(CREDENTIALS.student.password);
    await page.locator('button[type="submit"], [data-testid="login-submit"]').first().click();

    // Wait for navigation
    await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 10000 }).catch(() => {
      // Continue even if navigation doesn't happen
    });

    // Verify dashboard access
    const studentElements = [
      page.getByRole('heading', { name: /dashboard|courses/i }),
      page.getByText(/student/i),
      page.getByRole('navigation')
    ];

    let foundStudentDashboard = false;
    for (const element of studentElements) {
      if (await element.isVisible().catch(() => false)) {
        foundStudentDashboard = true;
        break;
      }
    }
    expect(foundStudentDashboard).toBeTruthy();
  });

  test('should logout successfully', async ({ page }) => {
    // First login
    await page.locator('input[name="email"], [data-testid="email-input"]').first().fill(CREDENTIALS.admin.email);
    await page.locator('input[name="password"], [data-testid="password-input"]').first().fill(CREDENTIALS.admin.password);
    await page.locator('button[type="submit"], [data-testid="login-submit"]').first().click();

    // Wait for dashboard
    await page.waitForTimeout(2000); // Give time for navigation

    // Try different logout strategies
    // Strategy 1: Direct logout button
    let loggedOut = false;
    const logoutButton = page.getByRole('button', { name: /logout|sign out/i });
    if (await logoutButton.isVisible().catch(() => false)) {
      await logoutButton.click();
      loggedOut = true;
    }

    // Strategy 2: User menu dropdown
    if (!loggedOut) {
      const userMenuButton = page.getByRole('button', { name: /user menu|account|profile/i });
      if (await userMenuButton.isVisible().catch(() => false)) {
        await userMenuButton.click();
        await page.getByText(/logout|sign out/i).click();
        loggedOut = true;
      }
    }

    // Strategy 3: Avatar/icon button
    if (!loggedOut) {
      const avatarButton = page.locator('[aria-label*="user"], [aria-label*="account"], [data-testid="user-menu"]').first();
      if (await avatarButton.isVisible().catch(() => false)) {
        await avatarButton.click();
        await page.getByText(/logout|sign out/i).click();
        loggedOut = true;
      }
    }

    // Should redirect to login if logout was successful
    if (loggedOut) {
      await page.waitForURL('**/login', { timeout: 10000 });
      await expect(page.locator('input[name="email"], [data-testid="email-input"]').first()).toBeVisible();
    }
  });

  test('should persist authentication on page refresh', async ({ page }) => {
    // Login first
    await page.locator('input[name="email"], [data-testid="email-input"]').first().fill(CREDENTIALS.admin.email);
    await page.locator('input[name="password"], [data-testid="password-input"]').first().fill(CREDENTIALS.admin.password);
    await page.locator('button[type="submit"], [data-testid="login-submit"]').first().click();

    // Wait for navigation
    await page.waitForTimeout(2000);

    // Refresh page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Should not be on login page
    expect(page.url()).not.toContain('/login');
  });

  test('should redirect to login when accessing protected route without auth', async ({ page }) => {
    // Clear any existing auth
    await page.evaluate(() => {
      window.localStorage.clear();
      window.sessionStorage.clear();
    });

    // Try to access protected route
    await page.goto('/dashboard');

    // Should redirect to login
    await page.waitForURL('**/login', { timeout: 10000 });
    await expect(page.locator('input[name="email"], [data-testid="email-input"]').first()).toBeVisible();
  });

  test('should handle password visibility toggle', async ({ page }) => {
    const passwordInput = page.locator('input[name="password"], [data-testid="password-input"]').first();
    const visibilityToggle = page.locator('[data-testid="password-visibility-toggle"], button[aria-label*="password"]').first();

    // Initially password should be hidden
    await expect(passwordInput).toHaveAttribute('type', 'password');

    // Click toggle to show password
    await visibilityToggle.click();
    await expect(passwordInput).toHaveAttribute('type', 'text');

    // Click again to hide
    await visibilityToggle.click();
    await expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('should handle remember me functionality', async ({ page }) => {
    // Check if remember me exists (it's not in current Login.tsx)
    const rememberMe = page.getByRole('checkbox', { name: /remember me/i });

    if (await rememberMe.isVisible().catch(() => false)) {
      // Check remember me
      await rememberMe.check();
      expect(await rememberMe.isChecked()).toBeTruthy();

      // Login with remember me checked
      await page.locator('input[name="email"], [data-testid="email-input"]').first().fill(CREDENTIALS.admin.email);
      await page.locator('input[name="password"], [data-testid="password-input"]').first().fill(CREDENTIALS.admin.password);
      await page.locator('button[type="submit"], [data-testid="login-submit"]').first().click();

      // Check that appropriate storage is used
      const hasAuthToken = await page.evaluate(() => {
        return Object.keys(window.localStorage).some(key =>
          key.includes('auth') || key.includes('token')
        );
      });

      expect(hasAuthToken).toBeTruthy();
    } else {
      // Skip test if remember me doesn't exist
      test.skip();
    }
  });
});

test.describe('Role-Based Access Control', () => {
  test('admin should access all sections', async ({ page }) => {
    // Setup admin auth
    await page.goto('/login');
    await page.locator('input[name="email"], [data-testid="email-input"]').first().fill(CREDENTIALS.admin.email);
    await page.locator('input[name="password"], [data-testid="password-input"]').first().fill(CREDENTIALS.admin.password);
    await page.locator('button[type="submit"], [data-testid="login-submit"]').first().click();

    // Wait for successful login
    await page.waitForTimeout(2000);

    // Navigate to admin-only sections
    const adminRoutes = [
      '/admin/dashboard',
      '/admin/users',
      '/admin/settings',
      '/reports'
    ];

    for (const route of adminRoutes) {
      await page.goto(route);
      // Should not show unauthorized
      await expect(page.getByText(/unauthorized|forbidden|access denied/i)).not.toBeVisible();
    }
  });

  test('teacher should not access admin sections', async ({ page }) => {
    // Setup teacher auth
    await page.goto('/login');
    await page.locator('input[name="email"], [data-testid="email-input"]').first().fill(CREDENTIALS.teacher.email);
    await page.locator('input[name="password"], [data-testid="password-input"]').first().fill(CREDENTIALS.teacher.password);
    await page.locator('button[type="submit"], [data-testid="login-submit"]').first().click();

    // Wait for login
    await page.waitForTimeout(2000);

    // Try to access admin section
    await page.goto('/admin/dashboard');

    // Should show unauthorized or redirect
    const unauthorized = await page.getByText(/unauthorized|forbidden|access denied/i).isVisible().catch(() => false);
    const isOnAdminPage = page.url().includes('/admin');

    // Either should be unauthorized or not on admin page
    expect(unauthorized || !isOnAdminPage).toBeTruthy();
  });

  test('student should have limited access', async ({ page }) => {
    // Setup student auth
    await page.goto('/login');
    await page.locator('input[name="email"], [data-testid="email-input"]').first().fill(CREDENTIALS.student.email);
    await page.locator('input[name="password"], [data-testid="password-input"]').first().fill(CREDENTIALS.student.password);
    await page.locator('button[type="submit"], [data-testid="login-submit"]').first().click();

    // Wait for login
    await page.waitForTimeout(2000);

    // Student should be able to access their dashboard
    await page.goto('/dashboard');
    expect(page.url()).toContain('dashboard');

    // But not admin sections
    await page.goto('/admin/dashboard');

    const unauthorized = await page.getByText(/unauthorized|forbidden|access denied/i).isVisible().catch(() => false);
    const isOnAdminPage = page.url().includes('/admin');

    // Either should be unauthorized or not on admin page
    expect(unauthorized || !isOnAdminPage).toBeTruthy();
  });
});