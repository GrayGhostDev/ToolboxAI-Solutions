import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';
import { DashboardPage } from './DashboardPage';

/**
 * Admin Dashboard Page Object Model
 * Extends DashboardPage with admin-specific functionality
 */
export class AdminDashboardPage extends DashboardPage {
  // Admin-specific tabs
  readonly overviewTab = () => this.page.getByRole('tab', { name: /overview/i });
  readonly usersTab = () => this.page.getByRole('tab', { name: /users/i });
  readonly contentTab = () => this.page.getByRole('tab', { name: /content/i });
  readonly securityTab = () => this.page.getByRole('tab', { name: /security/i });
  readonly settingsTab = () => this.page.getByRole('tab', { name: /settings/i });

  // User management
  readonly userTable = () => this.page.locator('[data-testid="user-table"], table').first();
  readonly addUserButton = () => this.page.getByRole('button', { name: /add.*user|new.*user/i });
  readonly editUserButtons = () => this.page.getByRole('button', { name: /edit/i });
  readonly deleteUserButtons = () => this.page.getByRole('button', { name: /delete/i });
  readonly userSearchInput = () => this.page.getByPlaceholder(/search.*users/i);

  // System metrics
  readonly totalUsersMetric = () => this.page.getByText(/total users/i).locator('..');
  readonly activeSessionsMetric = () => this.page.getByText(/active sessions/i).locator('..');
  readonly contentGeneratedMetric = () => this.page.getByText(/content generated/i).locator('..');
  readonly systemHealthMetric = () => this.page.getByText(/system health/i).locator('..');

  // Content management
  readonly contentTable = () => this.page.locator('[data-testid="content-table"], .content-table');
  readonly approveContentButtons = () => this.page.getByRole('button', { name: /approve/i });
  readonly rejectContentButtons = () => this.page.getByRole('button', { name: /reject/i });

  // Security settings
  readonly securityAlerts = () => this.page.locator('[data-testid="security-alerts"], .security-alert');
  readonly auditLogTable = () => this.page.locator('[data-testid="audit-log"], .audit-log');
  readonly twoFactorToggle = () => this.page.getByRole('switch', { name: /two.*factor/i });
  readonly sessionTimeoutInput = () => this.page.getByLabel(/session.*timeout/i);

  // System settings
  readonly maintenanceModeToggle = () => this.page.getByRole('switch', { name: /maintenance.*mode/i });
  readonly emailSettingsForm = () => this.page.locator('[data-testid="email-settings"]');
  readonly apiKeysSection = () => this.page.locator('[data-testid="api-keys"]');
  readonly saveSettingsButton = () => this.page.getByRole('button', { name: /save.*settings/i });

  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to admin dashboard
   */
  async goto() {
    await super.goto('/admin/dashboard');
  }

  /**
   * Verify admin dashboard is loaded
   */
  async verifyAdminDashboard() {
    await expect(this.page.getByRole('heading', { name: /admin.*dashboard/i })).toBeVisible();
    await expect(this.page.getByText(/system overview and management tools/i)).toBeVisible();

    // Verify admin-specific metrics are visible
    await expect(this.totalUsersMetric()).toBeVisible();
    await expect(this.activeSessionsMetric()).toBeVisible();
    await expect(this.contentGeneratedMetric()).toBeVisible();
    await expect(this.systemHealthMetric()).toBeVisible();
  }

  /**
   * Switch to Users tab and verify it's loaded
   */
  async goToUsersTab() {
    await this.usersTab().click();
    await this.page.waitForLoadState('networkidle');
    await expect(this.userTable()).toBeVisible();
  }

  /**
   * Search for a user
   */
  async searchUser(query: string) {
    await this.goToUsersTab();
    await this.userSearchInput().fill(query);
    await this.userSearchInput().press('Enter');
    await this.page.waitForTimeout(500); // Wait for search results
  }

  /**
   * Get list of users from the table
   */
  async getUsersList(): Promise<string[]> {
    await this.goToUsersTab();
    const userRows = await this.userTable().locator('tbody tr').all();
    const users: string[] = [];

    for (const row of userRows) {
      const nameCell = row.locator('td').first();
      const name = await nameCell.textContent();
      if (name) {
        users.push(name.trim());
      }
    }

    return users;
  }

  /**
   * Add a new user
   */
  async addUser(userData: {
    email: string;
    name: string;
    role: 'admin' | 'teacher' | 'student';
    password: string;
  }) {
    await this.goToUsersTab();
    await this.addUserButton().click();

    // Fill in the user form (adjust selectors based on actual implementation)
    await this.page.getByLabel(/email/i).fill(userData.email);
    await this.page.getByLabel(/name/i).fill(userData.name);
    await this.page.getByRole('combobox', { name: /role/i }).selectOption(userData.role);
    await this.page.getByLabel(/password/i).fill(userData.password);

    await this.page.getByRole('button', { name: /create|add|submit/i }).click();
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Switch to Content tab
   */
  async goToContentTab() {
    await this.contentTab().click();
    await this.page.waitForLoadState('networkidle');
    await expect(this.contentTable()).toBeVisible();
  }

  /**
   * Approve content by index
   */
  async approveContent(index: number = 0) {
    await this.goToContentTab();
    const approveButtons = await this.approveContentButtons().all();
    if (approveButtons[index]) {
      await approveButtons[index].click();
      await this.page.waitForTimeout(500); // Wait for action to complete
    }
  }

  /**
   * Switch to Security tab
   */
  async goToSecurityTab() {
    await this.securityTab().click();
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Get security alerts count
   */
  async getSecurityAlertsCount(): Promise<number> {
    await this.goToSecurityTab();
    const alerts = await this.securityAlerts().all();
    return alerts.length;
  }

  /**
   * Toggle two-factor authentication
   */
  async toggleTwoFactorAuth() {
    await this.goToSecurityTab();
    await this.twoFactorToggle().click();
    await this.page.waitForTimeout(500); // Wait for toggle animation
  }

  /**
   * Switch to Settings tab
   */
  async goToSettingsTab() {
    await this.settingsTab().click();
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Toggle maintenance mode
   */
  async toggleMaintenanceMode() {
    await this.goToSettingsTab();
    await this.maintenanceModeToggle().click();

    // Confirm the action if dialog appears
    const confirmButton = this.page.getByRole('button', { name: /confirm/i });
    if (await confirmButton.isVisible().catch(() => false)) {
      await confirmButton.click();
    }

    await this.page.waitForTimeout(500);
  }

  /**
   * Update session timeout
   */
  async updateSessionTimeout(minutes: number) {
    await this.goToSettingsTab();
    await this.sessionTimeoutInput().fill(minutes.toString());
    await this.saveSettingsButton().click();
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Get system metrics
   */
  async getSystemMetrics(): Promise<{
    totalUsers: string;
    activeSessions: string;
    contentGenerated: string;
    systemHealth: string;
  }> {
    await this.goto();

    const totalUsers = await this.totalUsersMetric().locator('.value, [data-testid="metric-value"]').textContent() || '0';
    const activeSessions = await this.activeSessionsMetric().locator('.value, [data-testid="metric-value"]').textContent() || '0';
    const contentGenerated = await this.contentGeneratedMetric().locator('.value, [data-testid="metric-value"]').textContent() || '0';
    const systemHealth = await this.systemHealthMetric().locator('.value, [data-testid="metric-value"]').textContent() || 'Unknown';

    return {
      totalUsers: totalUsers.trim(),
      activeSessions: activeSessions.trim(),
      contentGenerated: contentGenerated.trim(),
      systemHealth: systemHealth.trim()
    };
  }

  /**
   * Verify all admin tabs are accessible
   */
  async verifyAllTabsAccessible() {
    const tabs = [
      { tab: this.overviewTab, name: 'Overview' },
      { tab: this.usersTab, name: 'Users' },
      { tab: this.contentTab, name: 'Content' },
      { tab: this.securityTab, name: 'Security' },
      { tab: this.settingsTab, name: 'Settings' }
    ];

    for (const { tab, name } of tabs) {
      await tab().click();
      await this.page.waitForLoadState('networkidle');
      // Verify we can access the tab without errors
      await expect(this.page.getByText(/error|unauthorized|forbidden/i)).not.toBeVisible();
    }
  }

  /**
   * Check if user has full admin privileges
   */
  async hasFullAdminPrivileges(): Promise<boolean> {
    try {
      await this.verifyAllTabsAccessible();
      return true;
    } catch {
      return false;
    }
  }
}