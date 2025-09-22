import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Dashboard Page Object Model
 * Handles main dashboard interactions and navigation
 */
export class DashboardPage extends BasePage {
  // Navigation elements
  private sidebar: Locator;
  private topbar: Locator;
  private navLinks: {
    dashboard: Locator;
    classes: Locator;
    messages: Locator;
    assessments: Locator;
    progress: Locator;
    settings: Locator;
    profile: Locator;
  };

  // Dashboard widgets
  private welcomeMessage: Locator;
  private statsCards: Locator;
  private activityFeed: Locator;
  private quickActions: Locator;
  private recentClasses: Locator;
  private upcomingEvents: Locator;
  private notificationBell: Locator;
  private userMenu: Locator;

  // Metrics
  private totalStudents: Locator;
  private totalClasses: Locator;
  private averageScore: Locator;
  private completionRate: Locator;

  constructor(page: Page) {
    super(page);

    // Initialize navigation locators
    this.sidebar = page.locator('[data-testid="sidebar"]');
    this.topbar = page.locator('[data-testid="topbar"]');

    this.navLinks = {
      dashboard: page.locator('[data-testid="nav-dashboard"]'),
      classes: page.locator('[data-testid="nav-classes"]'),
      messages: page.locator('[data-testid="nav-messages"]'),
      assessments: page.locator('[data-testid="nav-assessments"]'),
      progress: page.locator('[data-testid="nav-progress"]'),
      settings: page.locator('[data-testid="nav-settings"]'),
      profile: page.locator('[data-testid="nav-profile"]')
    };

    // Initialize widget locators
    this.welcomeMessage = page.locator('[data-testid="welcome-message"]');
    this.statsCards = page.locator('[data-testid="stats-cards"]');
    this.activityFeed = page.locator('[data-testid="activity-feed"]');
    this.quickActions = page.locator('[data-testid="quick-actions"]');
    this.recentClasses = page.locator('[data-testid="recent-classes"]');
    this.upcomingEvents = page.locator('[data-testid="upcoming-events"]');
    this.notificationBell = page.locator('[data-testid="notification-bell"]');
    this.userMenu = page.locator('[data-testid="user-menu"]');

    // Initialize metrics locators
    this.totalStudents = page.locator('[data-testid="metric-total-students"]');
    this.totalClasses = page.locator('[data-testid="metric-total-classes"]');
    this.averageScore = page.locator('[data-testid="metric-average-score"]');
    this.completionRate = page.locator('[data-testid="metric-completion-rate"]');
  }

  /**
   * Navigate to dashboard
   */
  async goto(): Promise<void> {
    await this.navigate('/dashboard');
    await this.waitForPageLoad();
  }

  /**
   * Navigate to a specific section
   */
  async navigateTo(section: keyof typeof this.navLinks): Promise<void> {
    await this.navLinks[section].click();
    await this.waitForPageLoad();
  }

  /**
   * Get welcome message text
   */
  async getWelcomeMessage(): Promise<string | null> {
    return await this.welcomeMessage.textContent();
  }

  /**
   * Get dashboard metrics
   */
  async getMetrics(): Promise<{
    totalStudents: string | null;
    totalClasses: string | null;
    averageScore: string | null;
    completionRate: string | null;
  }> {
    return {
      totalStudents: await this.totalStudents.textContent(),
      totalClasses: await this.totalClasses.textContent(),
      averageScore: await this.averageScore.textContent(),
      completionRate: await this.completionRate.textContent()
    };
  }

  /**
   * Get activity feed items
   */
  async getActivityFeedItems(): Promise<string[]> {
    const items = await this.activityFeed.locator('.activity-item').all();
    return Promise.all(items.map(item => item.textContent() || ''));
  }

  /**
   * Get recent classes
   */
  async getRecentClasses(): Promise<Array<{ name: string; students: string }>> {
    const classCards = await this.recentClasses.locator('.class-card').all();
    const classes = [];

    for (const card of classCards) {
      const name = await card.locator('.class-name').textContent();
      const students = await card.locator('.student-count').textContent();
      classes.push({ name: name || '', students: students || '' });
    }

    return classes;
  }

  /**
   * Check if user has notifications
   */
  async hasNotifications(): Promise<boolean> {
    const badge = this.notificationBell.locator('.notification-badge');
    return await this.isElementVisible(badge);
  }

  /**
   * Get notification count
   */
  async getNotificationCount(): Promise<number> {
    const badge = this.notificationBell.locator('.notification-badge');
    if (await this.isElementVisible(badge)) {
      const count = await badge.textContent();
      return parseInt(count || '0', 10);
    }
    return 0;
  }

  /**
   * Open notification panel
   */
  async openNotifications(): Promise<void> {
    await this.notificationBell.click();
    await this.page.waitForSelector('[data-testid="notification-panel"]');
  }

  /**
   * Open user menu
   */
  async openUserMenu(): Promise<void> {
    await this.userMenu.click();
    await this.page.waitForSelector('[data-testid="user-dropdown"]');
  }

  /**
   * Logout from user menu
   */
  async logoutFromMenu(): Promise<void> {
    await this.openUserMenu();
    await this.page.locator('[data-testid="logout-button"]').click();
    await this.page.waitForURL(/login/);
  }

  /**
   * Check if sidebar is collapsed
   */
  async isSidebarCollapsed(): Promise<boolean> {
    const sidebarClass = await this.sidebar.getAttribute('class');
    return sidebarClass?.includes('collapsed') || false;
  }

  /**
   * Toggle sidebar
   */
  async toggleSidebar(): Promise<void> {
    const toggleButton = this.page.locator('[data-testid="sidebar-toggle"]');
    await toggleButton.click();
    await this.page.waitForTimeout(300); // Wait for animation
  }

  /**
   * Search in dashboard
   */
  async search(query: string): Promise<void> {
    const searchInput = this.page.locator('[data-testid="dashboard-search"]');
    await this.fillInput(searchInput, query);
    await this.page.keyboard.press('Enter');
    await this.waitForAPIResponse('/api/v1/search');
  }

  /**
   * Quick action: Create new class
   */
  async quickCreateClass(): Promise<void> {
    const createClassButton = this.quickActions.locator('[data-testid="quick-create-class"]');
    await createClassButton.click();
    await this.page.waitForSelector('[data-testid="create-class-modal"]');
  }

  /**
   * Quick action: Send message
   */
  async quickSendMessage(): Promise<void> {
    const sendMessageButton = this.quickActions.locator('[data-testid="quick-send-message"]');
    await sendMessageButton.click();
    await this.page.waitForSelector('[data-testid="compose-message-modal"]');
  }

  /**
   * Quick action: Create assessment
   */
  async quickCreateAssessment(): Promise<void> {
    const createAssessmentButton = this.quickActions.locator('[data-testid="quick-create-assessment"]');
    await createAssessmentButton.click();
    await this.page.waitForSelector('[data-testid="create-assessment-modal"]');
  }

  /**
   * Check dashboard load performance
   */
  async checkLoadPerformance(): Promise<{
    loadTime: number;
    apiCalls: number;
    renderTime: number;
  }> {
    const metrics = await this.getPerformanceMetrics();
    const apiCalls = await this.page.evaluate(() =>
      performance.getEntriesByType('resource').filter(r => r.name.includes('/api/')).length
    );

    return {
      loadTime: metrics.loadComplete,
      apiCalls,
      renderTime: metrics.firstContentfulPaint
    };
  }

  /**
   * Validate dashboard layout
   */
  async validateLayout(): Promise<{
    sidebarVisible: boolean;
    topbarVisible: boolean;
    widgetsLoaded: boolean;
    navigationWorking: boolean;
  }> {
    const widgetsLoaded =
      await this.isElementVisible(this.statsCards) &&
      await this.isElementVisible(this.activityFeed) &&
      await this.isElementVisible(this.quickActions);

    const navItems = Object.values(this.navLinks);
    const navigationWorking = await Promise.all(
      navItems.map(item => item.isVisible())
    ).then(results => results.every(r => r));

    return {
      sidebarVisible: await this.isElementVisible(this.sidebar),
      topbarVisible: await this.isElementVisible(this.topbar),
      widgetsLoaded,
      navigationWorking
    };
  }

  /**
   * Check role-based access
   */
  async checkRoleAccess(role: 'admin' | 'teacher' | 'student'): Promise<{
    canAccessSettings: boolean;
    canCreateClass: boolean;
    canViewAllStudents: boolean;
  }> {
    const settingsVisible = await this.navLinks.settings.isVisible();
    const createClassVisible = await this.quickActions.locator('[data-testid="quick-create-class"]').isVisible();
    const allStudentsLink = this.page.locator('[data-testid="view-all-students"]');
    const allStudentsVisible = await allStudentsLink.isVisible().catch(() => false);

    return {
      canAccessSettings: settingsVisible,
      canCreateClass: createClassVisible,
      canViewAllStudents: allStudentsVisible
    };
  }
}