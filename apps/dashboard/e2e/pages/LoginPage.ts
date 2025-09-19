import type { Page, expect } from '@playwright/test';

/**
 * Login Page Object Model
 * Uses 2025 Playwright best practices with semantic locators
 */
export class LoginPage {
  readonly page: Page;

  // Semantic locators
  readonly emailInput = () => this.page.getByLabel(/username or email/i);
  readonly passwordInput = () => this.page.getByLabel(/^password$/i);
  readonly signInButton = () => this.page.getByRole('button', { name: /sign in/i });
  readonly passwordToggle = () => this.page.getByRole('button', { name: /toggle password visibility/i });
  readonly forgotPasswordLink = () => this.page.getByText(/forgot.*password/i);
  readonly registerLink = () => this.page.getByText(/sign up here/i);
  readonly errorAlert = () => this.page.getByRole('alert');
  readonly heading = () => this.page.getByRole('heading', { name: /welcome back/i });

  // Demo credentials section
  readonly demoCredentials = () => this.page.getByText(/demo credentials/i);

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Navigate to the login page
   */
  async goto() {
    await this.page.goto('/login');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Perform login with credentials
   */
  async login(email: string, password: string) {
    await this.emailInput().fill(email);
    await this.passwordInput().fill(password);
    await this.signInButton().click();
  }

  /**
   * Login and wait for successful navigation
   */
  async loginAndWaitForDashboard(email: string, password: string) {
    await this.login(email, password);

    // Wait for navigation away from login page
    await this.page.waitForURL(url => !url.pathname.includes('/login'), {
      timeout: 10000
    }).catch(() => {
      // If navigation fails, continue
    });
  }

  /**
   * Check if login form is visible
   */
  async isLoginFormVisible(): Promise<boolean> {
    try {
      await expect(this.emailInput()).toBeVisible({ timeout: 5000 });
      await expect(this.passwordInput()).toBeVisible({ timeout: 5000 });
      await expect(this.signInButton()).toBeVisible({ timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get error message text
   */
  async getErrorMessage(): Promise<string | null> {
    try {
      await this.errorAlert().waitFor({ state: 'visible', timeout: 5000 });
      return await this.errorAlert().textContent();
    } catch {
      return null;
    }
  }

  /**
   * Toggle password visibility
   */
  async togglePasswordVisibility() {
    await this.passwordToggle().click();
  }

  /**
   * Check if password is visible
   */
  async isPasswordVisible(): Promise<boolean> {
    const type = await this.passwordInput().getAttribute('type');
    return type === 'text';
  }

  /**
   * Submit empty form and expect validation error
   */
  async submitEmptyForm() {
    await this.signInButton().click();
    await expect(this.page.getByText(/email and password are required/i)).toBeVisible();
  }

  /**
   * Clear form inputs
   */
  async clearForm() {
    await this.emailInput().clear();
    await this.passwordInput().clear();
  }

  /**
   * Navigate to forgot password page
   */
  async goToForgotPassword() {
    await this.forgotPasswordLink().click();
  }

  /**
   * Navigate to registration page
   */
  async goToRegister() {
    await this.registerLink().click();
  }

  /**
   * Wait for successful login
   * Returns true if navigated away from login page
   */
  async waitForSuccessfulLogin(): Promise<boolean> {
    try {
      await this.page.waitForURL(url => !url.pathname.includes('/login'), {
        timeout: 10000
      });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Check if user is on login page
   */
  isOnLoginPage(): boolean {
    return this.page.url().includes('/login');
  }
}