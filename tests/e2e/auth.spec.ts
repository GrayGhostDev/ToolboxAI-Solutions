import { test, expect } from '@playwright/test';
import { LoginPage } from '../page-objects/LoginPage';
import { DashboardPage } from '../page-objects/DashboardPage';

test.describe('Authentication Tests', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    await loginPage.goto();
  });

  test.describe('Login Functionality', () => {
    test('should login successfully with valid credentials', async () => {
      await loginPage.login('teacher@test.com', 'Teacher123!');

      const isLoggedIn = await loginPage.isLoginSuccessful();
      expect(isLoggedIn).toBeTruthy();

      const welcomeMessage = await dashboardPage.getWelcomeMessage();
      expect(welcomeMessage).toContain('Welcome');
    });

    test('should show error with invalid credentials', async () => {
      await loginPage.login('invalid@test.com', 'wrongpassword');

      const hasError = await loginPage.hasLoginError();
      expect(hasError).toBeTruthy();

      const errorMessage = await loginPage.getLoginErrorMessage();
      expect(errorMessage).toContain('Invalid credentials');
    });

    test('should validate empty fields', async () => {
      await loginPage.login('', '');

      const hasError = await loginPage.hasLoginError();
      expect(hasError).toBeTruthy();

      const errorMessage = await loginPage.getLoginErrorMessage();
      expect(errorMessage).toMatch(/required|empty/i);
    });

    test('should remember user with remember me checkbox', async () => {
      await loginPage.login('teacher@test.com', 'Teacher123!', true);

      const isLoggedIn = await loginPage.isLoginSuccessful();
      expect(isLoggedIn).toBeTruthy();

      // Check if remember me cookie is set
      const cookies = await loginPage.page.context().cookies();
      const rememberCookie = cookies.find(c => c.name === 'remember_token');
      expect(rememberCookie).toBeDefined();
      expect(rememberCookie?.expires).toBeGreaterThan(Date.now() / 1000);
    });

    test('should navigate to forgot password', async () => {
      await loginPage.clickForgotPassword();

      const url = loginPage.page.url();
      expect(url).toContain('password-reset');
    });

    test('should navigate to register page', async () => {
      await loginPage.clickRegister();

      const url = loginPage.page.url();
      expect(url).toContain('register');
    });
  });

  test.describe('Role-based Login', () => {
    test('should login as admin and have admin access', async () => {
      await loginPage.quickLogin('admin');

      const isLoggedIn = await loginPage.isLoginSuccessful();
      expect(isLoggedIn).toBeTruthy();

      const roleAccess = await dashboardPage.checkRoleAccess('admin');
      expect(roleAccess.canAccessSettings).toBeTruthy();
      expect(roleAccess.canViewAllStudents).toBeTruthy();
    });

    test('should login as teacher and have teacher access', async () => {
      await loginPage.quickLogin('teacher');

      const isLoggedIn = await loginPage.isLoginSuccessful();
      expect(isLoggedIn).toBeTruthy();

      const roleAccess = await dashboardPage.checkRoleAccess('teacher');
      expect(roleAccess.canCreateClass).toBeTruthy();
      expect(roleAccess.canAccessSettings).toBeTruthy();
    });

    test('should login as student and have limited access', async () => {
      await loginPage.quickLogin('student');

      const isLoggedIn = await loginPage.isLoginSuccessful();
      expect(isLoggedIn).toBeTruthy();

      const roleAccess = await dashboardPage.checkRoleAccess('student');
      expect(roleAccess.canCreateClass).toBeFalsy();
      expect(roleAccess.canViewAllStudents).toBeFalsy();
    });
  });

  test.describe('Clerk Authentication', () => {
    test('should redirect to Clerk for OAuth login', async () => {
      await loginPage.loginWithClerk();

      // Wait for redirect to Clerk
      await loginPage.page.waitForTimeout(2000);

      const url = loginPage.page.url();
      expect(url).toContain('clerk.accounts.dev');
    });
  });

  test.describe('Logout Functionality', () => {
    test('should logout successfully from dashboard', async ({ page }) => {
      // First login
      await loginPage.quickLogin('teacher');
      await loginPage.isLoginSuccessful();

      // Navigate to dashboard and logout
      await dashboardPage.goto();
      await dashboardPage.logoutFromMenu();

      // Check if redirected to login
      const url = page.url();
      expect(url).toContain('login');

      // Verify session is cleared
      const cookies = await page.context().cookies();
      const sessionCookie = cookies.find(c => c.name === 'session');
      expect(sessionCookie).toBeUndefined();
    });
  });

  test.describe('Two-Factor Authentication', () => {
    test.skip('should handle 2FA when enabled', async () => {
      // This test would require a test account with 2FA enabled
      await loginPage.login('2fa@test.com', 'Password123!');

      // Handle 2FA code input
      await loginPage.handleTwoFactor('123456');

      const isLoggedIn = await loginPage.isLoginSuccessful();
      expect(isLoggedIn).toBeTruthy();
    });
  });

  test.describe('Session Management', () => {
    test('should redirect to login when session expires', async ({ page }) => {
      await loginPage.quickLogin('teacher');
      await loginPage.isLoginSuccessful();

      // Clear session cookie to simulate expiry
      await page.context().clearCookies();

      // Try to navigate to dashboard
      await dashboardPage.goto();

      // Should be redirected to login
      await page.waitForURL(/login/);
      const url = page.url();
      expect(url).toContain('login');
    });

    test('should maintain session across page refreshes', async ({ page }) => {
      await loginPage.quickLogin('teacher');
      await loginPage.isLoginSuccessful();

      // Refresh the page
      await page.reload();

      // Should still be on dashboard
      const url = page.url();
      expect(url).toContain('dashboard');

      // Should not show login page
      const isStillLoggedIn = await loginPage.isAlreadyLoggedIn();
      expect(isStillLoggedIn).toBeTruthy();
    });
  });

  test.describe('Security Tests', () => {
    test('should prevent SQL injection in login', async () => {
      const sqlInjection = "' OR '1'='1";
      await loginPage.login(sqlInjection, sqlInjection);

      const hasError = await loginPage.hasLoginError();
      expect(hasError).toBeTruthy();

      // Should not be logged in
      const url = loginPage.page.url();
      expect(url).not.toContain('dashboard');
    });

    test('should prevent XSS in login fields', async () => {
      const xssPayload = '<script>alert("XSS")</script>';
      await loginPage.login(xssPayload, 'password');

      // Check that script is not executed
      const alertDialog = loginPage.page.locator('dialog');
      const isAlertVisible = await alertDialog.isVisible();
      expect(isAlertVisible).toBeFalsy();

      // Should show validation error instead
      const hasError = await loginPage.hasLoginError();
      expect(hasError).toBeTruthy();
    });

    test('should implement rate limiting', async () => {
      // Attempt multiple failed logins
      for (let i = 0; i < 6; i++) {
        await loginPage.login('test@test.com', 'wrongpassword');
        await loginPage.page.waitForTimeout(100);
      }

      // Should show rate limit error after multiple attempts
      const errorMessage = await loginPage.getLoginErrorMessage();
      expect(errorMessage).toMatch(/too many attempts|rate limit/i);
    });
  });

  test.describe('Password Requirements', () => {
    test('should validate password complexity', async ({ page }) => {
      // Navigate to register page
      await loginPage.clickRegister();

      const passwordInput = page.locator('[data-testid="password-input"]');
      const errorMessage = page.locator('[data-testid="password-error"]');

      // Test weak password
      await passwordInput.fill('weak');
      await passwordInput.blur();

      const weakError = await errorMessage.textContent();
      expect(weakError).toMatch(/must contain|too weak|requirements/i);

      // Test strong password
      await passwordInput.clear();
      await passwordInput.fill('Strong123!@#');
      await passwordInput.blur();

      const strongError = await errorMessage.isVisible();
      expect(strongError).toBeFalsy();
    });
  });

  test.describe('Accessibility', () => {
    test('should be keyboard navigable', async ({ page }) => {
      await loginPage.goto();

      // Tab through form elements
      await page.keyboard.press('Tab'); // Focus username
      await page.keyboard.type('teacher@test.com');

      await page.keyboard.press('Tab'); // Focus password
      await page.keyboard.type('Teacher123!');

      await page.keyboard.press('Tab'); // Focus remember me
      await page.keyboard.press('Space'); // Check remember me

      await page.keyboard.press('Tab'); // Focus login button
      await page.keyboard.press('Enter'); // Submit form

      // Should login successfully
      const isLoggedIn = await loginPage.isLoginSuccessful();
      expect(isLoggedIn).toBeTruthy();
    });

    test('should have proper ARIA labels', async ({ page }) => {
      await loginPage.goto();

      // Check ARIA labels
      const usernameInput = page.locator('[data-testid="username-input"]');
      const usernameLabel = await usernameInput.getAttribute('aria-label');
      expect(usernameLabel).toBeTruthy();

      const loginButton = page.locator('[data-testid="login-button"]');
      const buttonLabel = await loginButton.getAttribute('aria-label');
      expect(buttonLabel).toBeTruthy();

      // Check form role
      const form = page.locator('form');
      const formRole = await form.getAttribute('role');
      expect(formRole).toBe('form');
    });
  });
});