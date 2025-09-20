import type { Page, Locator } from '@playwright/test';
import { expect } from '@playwright/test';

/**
 * Dashboard Page Object Model
 * Handles common dashboard interactions across all user roles
 */
export class DashboardPage {
  readonly page: Page;

  // Navigation elements
  readonly navigation = () => this.page.getByRole('navigation');
  readonly sidebarMenu = () => this.page.locator('[data-testid="sidebar"], aside');
  readonly topbar = () => this.page.locator('[data-testid="topbar"], header');

  // User menu
  readonly userMenuButton = () => this.page.getByRole('button', { name: /user menu|account|profile/i });
  readonly avatarButton = () => this.page.locator('[aria-label*="user"], [aria-label*="account"], [data-testid="user-menu"]').first();
  readonly logoutButton = () => this.page.getByRole('button', { name: /logout|sign out/i });
  readonly logoutMenuItem = () => this.page.getByText(/logout|sign out/i);

  // Dashboard content
  readonly pageHeading = () => this.page.getByRole('heading', { level: 1 });
  readonly dashboardHeading = () => this.page.getByRole('heading', { name: /dashboard/i });
  readonly overviewSection = () => this.page.getByText(/overview/i);

  // Common dashboard cards
  readonly statsCards = () => this.page.locator('[data-testid*="stat-card"], .stat-card, .metric-card');
  readonly chartContainers = () => this.page.locator('[data-testid*="chart"], .chart-container, canvas');

  // Tabs and sections
  readonly tabList = () => this.page.getByRole('tablist');
  readonly tabButtons = () => this.page.getByRole('tab');

  // Notifications
  readonly notificationBell = () => this.page.getByRole('button', { name: /notifications/i });
  readonly notificationBadge = () => this.page.locator('[data-testid="notification-badge"]');

  // Search
  readonly searchInput = () => this.page.getByRole('searchbox');

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Navigate to dashboard
   */
  async goto(path: string = '/dashboard') {
    await this.page.goto(path);
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Wait for dashboard to be loaded
   */
  async waitForDashboardLoad() {
    // Wait for at least one dashboard indicator
    const indicators = [
      this.dashboardHeading(),
      this.overviewSection(),
      this.navigation()
    ];

    let loaded = false;
    for (const indicator of indicators) {
      if (await indicator.isVisible().catch(() => false)) {
        loaded = true;
        break;
      }
    }

    if (!loaded) {
      throw new Error('Dashboard did not load properly');
    }

    // Wait for any loading spinners to disappear
    await this.page.waitForSelector('[data-testid="loading-spinner"]', {
      state: 'hidden',
      timeout: 5000
    }).catch(() => {}); // Ignore if no spinner exists
  }

  /**
   * Check if user is on dashboard
   */
  isOnDashboard(): boolean {
    const url = this.page.url();
    return url.includes('dashboard') || url === this.page.context().pages()[0].url() + '/';
  }

  /**
   * Get current user role from UI
   */
  async getCurrentUserRole(): Promise<string | null> {
    // Try to find role indicator in UI
    const roleSelectors = [
      'text=/admin/i',
      'text=/teacher/i',
      'text=/student/i'
    ];

    for (const selector of roleSelectors) {
      const element = this.page.locator(selector);
      if (await element.isVisible().catch(() => false)) {
        const text = await element.textContent();
        if (text) {
          if (text.toLowerCase().includes('admin')) return 'admin';
          if (text.toLowerCase().includes('teacher')) return 'teacher';
          if (text.toLowerCase().includes('student')) return 'student';
        }
      }
    }

    return null;
  }

  /**
   * Navigate to a menu item
   */
  async navigateToMenuItem(itemName: string) {
    const menuItem = this.page.getByRole('link', { name: new RegExp(itemName, 'i') });
    const alternativeMenuItem = this.page.getByText(new RegExp(itemName, 'i'));

    if (await menuItem.isVisible().catch(() => false)) {
      await menuItem.click();
    } else if (await alternativeMenuItem.isVisible().catch(() => false)) {
      await alternativeMenuItem.click();
    } else {
      throw new Error(`Menu item "${itemName}" not found`);
    }

    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Switch between tabs
   */
  async switchToTab(tabName: string) {
    const tab = this.page.getByRole('tab', { name: new RegExp(tabName, 'i') });
    await tab.click();
    await this.page.waitForTimeout(500); // Wait for tab transition
  }

  /**
   * Logout from dashboard
   */
  async logout() {
    // Try different logout strategies

    // Strategy 1: Direct logout button
    if (await this.logoutButton().isVisible().catch(() => false)) {
      await this.logoutButton().click();
      await this.waitForLogout();
      return;
    }

    // Strategy 2: User menu dropdown
    if (await this.userMenuButton().isVisible().catch(() => false)) {
      await this.userMenuButton().click();
      await this.logoutMenuItem().click();
      await this.waitForLogout();
      return;
    }

    // Strategy 3: Avatar button
    if (await this.avatarButton().isVisible().catch(() => false)) {
      await this.avatarButton().click();
      await this.logoutMenuItem().click();
      await this.waitForLogout();
      return;
    }

    throw new Error('Could not find logout option');
  }

  /**
   * Wait for logout to complete
   */
  private async waitForLogout() {
    await this.page.waitForURL('**/login', { timeout: 10000 });
  }

  /**
   * Check if a specific section is visible
   */
  async isSectionVisible(sectionName: string): Promise<boolean> {
    const section = this.page.getByText(new RegExp(sectionName, 'i'));
    return await section.isVisible().catch(() => false);
  }

  /**
   * Get all visible menu items
   */
  async getVisibleMenuItems(): Promise<string[]> {
    const menuItems = await this.navigation().locator('a, button').all();
    const visibleItems: string[] = [];

    for (const item of menuItems) {
      if (await item.isVisible()) {
        const text = await item.textContent();
        if (text) {
          visibleItems.push(text.trim());
        }
      }
    }

    return visibleItems;
  }

  /**
   * Check if user has access to admin features
   */
  async hasAdminAccess(): Promise<boolean> {
    // Check for admin-specific elements
    const adminIndicators = [
      this.page.getByText(/admin.*dashboard/i),
      this.page.getByText(/user.*management/i),
      this.page.getByText(/system.*settings/i),
      this.page.getByRole('link', { name: /admin/i })
    ];

    for (const indicator of adminIndicators) {
      if (await indicator.isVisible().catch(() => false)) {
        return true;
      }
    }

    return false;
  }

  /**
   * Get dashboard statistics
   */
  async getDashboardStats(): Promise<{ label: string; value: string }[]> {
    const stats: { label: string; value: string }[] = [];
    const cards = await this.statsCards().all();

    for (const card of cards) {
      const label = await card.locator('.label, [data-testid="stat-label"]').textContent().catch(() => '');
      const value = await card.locator('.value, [data-testid="stat-value"]').textContent().catch(() => '');

      if (label && value) {
        stats.push({ label: label.trim(), value: value.trim() });
      }
    }

    return stats;
  }

  /**
   * Search for content
   */
  async search(query: string) {
    const searchBox = this.searchInput();
    if (await searchBox.isVisible()) {
      await searchBox.fill(query);
      await searchBox.press('Enter');
      await this.page.waitForLoadState('networkidle');
    } else {
      throw new Error('Search box not found');
    }
  }

  /**
   * Check notification count
   */
  async getNotificationCount(): Promise<number> {
    const badge = this.notificationBadge();
    if (await badge.isVisible().catch(() => false)) {
      const text = await badge.textContent();
      return parseInt(text || '0', 10);
    }
    return 0;
  }
}