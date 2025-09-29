import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Login Page Object Model
 * Handles all login-related interactions
 */
export class LoginPage extends BasePage {
  // Locators
  private usernameInput: Locator;
  private passwordInput: Locator;
  private loginButton: Locator;
  private rememberMeCheckbox: Locator;
  private forgotPasswordLink: Locator;
  private registerLink: Locator;
  private clerkSignInButton: Locator;
  private errorAlert: Locator;
  private successMessage: Locator;

  constructor(page: Page) {
    super(page);

    // Initialize locators
    this.usernameInput = page.locator('[data-testid="username-input"]');
    this.passwordInput = page.locator('[data-testid="password-input"]');
    this.loginButton = page.locator('[data-testid="login-button"]');
    this.rememberMeCheckbox = page.locator('[data-testid="remember-me"]');
    this.forgotPasswordLink = page.locator('[data-testid="forgot-password-link"]');
    this.registerLink = page.locator('[data-testid="register-link"]');
    this.clerkSignInButton = page.locator('[data-testid="clerk-signin"]');
    this.errorAlert = page.locator('[role="alert"].error');
    this.successMessage = page.locator('[data-testid="success-message"]');
  }

  /**
   * Navigate to login page
   */
  async goto(): Promise<void> {
    await this.navigate('/login');
    await this.waitForPageLoad();
  }

  /**
   * Perform login with credentials
   */
  async login(username: string, password: string, rememberMe: boolean = false): Promise<void> {
    await this.fillInput(this.usernameInput, username);
    await this.fillInput(this.passwordInput, password);

    if (rememberMe) {
      await this.rememberMeCheckbox.check();
    }

    await this.loginButton.click();
    await this.page.waitForNavigation({ waitUntil: 'networkidle' });
  }

  /**
   * Quick login for test setup
   */
  async quickLogin(role: 'admin' | 'teacher' | 'student' = 'teacher'): Promise<void> {
    const credentials = {
      admin: { username: 'admin@test.com', password: 'Admin123!' },
      teacher: { username: 'teacher@test.com', password: 'Teacher123!' },
      student: { username: 'student@test.com', password: 'Student123!' }
    };

    const cred = credentials[role];
    await this.login(cred.username, cred.password);
  }

  /**
   * Login with Clerk authentication
   */
  async loginWithClerk(): Promise<void> {
    await this.clerkSignInButton.click();
    // Handle Clerk OAuth flow
    await this.page.waitForURL(/clerk\.accounts\.dev/);
  }

  /**
   * Check if login was successful
   */
  async isLoginSuccessful(): Promise<boolean> {
    try {
      await this.page.waitForURL(/dashboard/, { timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Check if error message is displayed
   */
  async hasLoginError(): Promise<boolean> {
    return await this.isElementVisible(this.errorAlert);
  }

  /**
   * Get login error message
   */
  async getLoginErrorMessage(): Promise<string | null> {
    if (await this.hasLoginError()) {
      return await this.errorAlert.textContent();
    }
    return null;
  }

  /**
   * Click forgot password link
   */
  async clickForgotPassword(): Promise<void> {
    await this.forgotPasswordLink.click();
    await this.page.waitForURL(/password-reset/);
  }

  /**
   * Click register link
   */
  async clickRegister(): Promise<void> {
    await this.registerLink.click();
    await this.page.waitForURL(/register/);
  }

  /**
   * Validate login form
   */
  async validateLoginForm(): Promise<{
    usernameVisible: boolean;
    passwordVisible: boolean;
    loginButtonEnabled: boolean;
  }> {
    return {
      usernameVisible: await this.isElementVisible(this.usernameInput),
      passwordVisible: await this.isElementVisible(this.passwordInput),
      loginButtonEnabled: await this.loginButton.isEnabled()
    };
  }

  /**
   * Test invalid login scenarios
   */
  async testInvalidLogin(username: string, password: string): Promise<string | null> {
    await this.login(username, password);
    return await this.getLoginErrorMessage();
  }

  /**
   * Logout (if logged in)
   */
  async logout(): Promise<void> {
    // Navigate to logout endpoint
    await this.page.goto(`${this.baseURL}/api/v1/auth/logout`);
    await this.page.waitForURL(/login/);
  }

  /**
   * Check if user is already logged in
   */
  async isAlreadyLoggedIn(): Promise<boolean> {
    const currentURL = this.page.url();
    return currentURL.includes('dashboard');
  }

  /**
   * Handle two-factor authentication if present
   */
  async handleTwoFactor(code: string): Promise<void> {
    const twoFactorInput = this.page.locator('[data-testid="2fa-code-input"]');
    const verifyButton = this.page.locator('[data-testid="2fa-verify-button"]');

    if (await this.isElementVisible(twoFactorInput)) {
      await this.fillInput(twoFactorInput, code);
      await verifyButton.click();
      await this.page.waitForNavigation();
    }
  }
}