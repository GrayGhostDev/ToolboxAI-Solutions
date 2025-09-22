import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Settings Page Object Model
 * Handles settings and configuration interactions
 */
export class SettingsPage extends BasePage {
  // Settings sections
  private settingsTabs: {
    profile: Locator;
    account: Locator;
    notifications: Locator;
    privacy: Locator;
    appearance: Locator;
    integrations: Locator;
    security: Locator;
  };

  // Profile settings
  private profileSection: {
    avatarUpload: Locator;
    firstNameInput: Locator;
    lastNameInput: Locator;
    emailInput: Locator;
    phoneInput: Locator;
    bioTextarea: Locator;
    timezoneSelect: Locator;
    languageSelect: Locator;
    saveButton: Locator;
  };

  // Account settings
  private accountSection: {
    usernameInput: Locator;
    changePasswordButton: Locator;
    twoFactorToggle: Locator;
    deleteAccountButton: Locator;
    exportDataButton: Locator;
  };

  // Notification settings
  private notificationSection: {
    emailNotifications: Locator;
    pushNotifications: Locator;
    smsNotifications: Locator;
    newsUpdates: Locator;
    marketingEmails: Locator;
    classReminders: Locator;
    messageAlerts: Locator;
  };

  // Privacy settings
  private privacySection: {
    profileVisibility: Locator;
    showEmail: Locator;
    showPhone: Locator;
    allowMessages: Locator;
    dataSharing: Locator;
    cookiePreferences: Locator;
  };

  // Appearance settings
  private appearanceSection: {
    themeSelect: Locator;
    fontSizeSlider: Locator;
    colorScheme: Locator;
    compactMode: Locator;
    animationsToggle: Locator;
  };

  constructor(page: Page) {
    super(page);

    // Initialize settings tabs
    this.settingsTabs = {
      profile: page.locator('[data-testid="settings-tab-profile"]'),
      account: page.locator('[data-testid="settings-tab-account"]'),
      notifications: page.locator('[data-testid="settings-tab-notifications"]'),
      privacy: page.locator('[data-testid="settings-tab-privacy"]'),
      appearance: page.locator('[data-testid="settings-tab-appearance"]'),
      integrations: page.locator('[data-testid="settings-tab-integrations"]'),
      security: page.locator('[data-testid="settings-tab-security"]')
    };

    // Initialize profile section
    this.profileSection = {
      avatarUpload: page.locator('[data-testid="avatar-upload"]'),
      firstNameInput: page.locator('[data-testid="first-name-input"]'),
      lastNameInput: page.locator('[data-testid="last-name-input"]'),
      emailInput: page.locator('[data-testid="email-input"]'),
      phoneInput: page.locator('[data-testid="phone-input"]'),
      bioTextarea: page.locator('[data-testid="bio-textarea"]'),
      timezoneSelect: page.locator('[data-testid="timezone-select"]'),
      languageSelect: page.locator('[data-testid="language-select"]'),
      saveButton: page.locator('[data-testid="save-profile-button"]')
    };

    // Initialize account section
    this.accountSection = {
      usernameInput: page.locator('[data-testid="username-input"]'),
      changePasswordButton: page.locator('[data-testid="change-password-button"]'),
      twoFactorToggle: page.locator('[data-testid="two-factor-toggle"]'),
      deleteAccountButton: page.locator('[data-testid="delete-account-button"]'),
      exportDataButton: page.locator('[data-testid="export-data-button"]')
    };

    // Initialize notification section
    this.notificationSection = {
      emailNotifications: page.locator('[data-testid="toggle-email-notifications"]'),
      pushNotifications: page.locator('[data-testid="toggle-push-notifications"]'),
      smsNotifications: page.locator('[data-testid="toggle-sms-notifications"]'),
      newsUpdates: page.locator('[data-testid="toggle-news-updates"]'),
      marketingEmails: page.locator('[data-testid="toggle-marketing"]'),
      classReminders: page.locator('[data-testid="toggle-class-reminders"]'),
      messageAlerts: page.locator('[data-testid="toggle-message-alerts"]')
    };

    // Initialize privacy section
    this.privacySection = {
      profileVisibility: page.locator('[data-testid="profile-visibility-select"]'),
      showEmail: page.locator('[data-testid="show-email-toggle"]'),
      showPhone: page.locator('[data-testid="show-phone-toggle"]'),
      allowMessages: page.locator('[data-testid="allow-messages-toggle"]'),
      dataSharing: page.locator('[data-testid="data-sharing-toggle"]'),
      cookiePreferences: page.locator('[data-testid="cookie-preferences-button"]')
    };

    // Initialize appearance section
    this.appearanceSection = {
      themeSelect: page.locator('[data-testid="theme-select"]'),
      fontSizeSlider: page.locator('[data-testid="font-size-slider"]'),
      colorScheme: page.locator('[data-testid="color-scheme-select"]'),
      compactMode: page.locator('[data-testid="compact-mode-toggle"]'),
      animationsToggle: page.locator('[data-testid="animations-toggle"]')
    };
  }

  /**
   * Navigate to settings page
   */
  async goto(): Promise<void> {
    await this.navigate('/settings');
    await this.waitForPageLoad();
  }

  /**
   * Switch to a specific settings tab
   */
  async switchToTab(tab: keyof typeof this.settingsTabs): Promise<void> {
    await this.settingsTabs[tab].click();
    await this.page.waitForTimeout(300); // Wait for tab transition
  }

  /**
   * Update profile information
   */
  async updateProfile(data: {
    firstName?: string;
    lastName?: string;
    email?: string;
    phone?: string;
    bio?: string;
    timezone?: string;
    language?: string;
  }): Promise<void> {
    await this.switchToTab('profile');

    if (data.firstName) {
      await this.fillInput(this.profileSection.firstNameInput, data.firstName);
    }
    if (data.lastName) {
      await this.fillInput(this.profileSection.lastNameInput, data.lastName);
    }
    if (data.email) {
      await this.fillInput(this.profileSection.emailInput, data.email);
    }
    if (data.phone) {
      await this.fillInput(this.profileSection.phoneInput, data.phone);
    }
    if (data.bio) {
      await this.fillInput(this.profileSection.bioTextarea, data.bio);
    }
    if (data.timezone) {
      await this.profileSection.timezoneSelect.selectOption(data.timezone);
    }
    if (data.language) {
      await this.profileSection.languageSelect.selectOption(data.language);
    }

    await this.profileSection.saveButton.click();
    await this.waitForAPIResponse('/api/v1/settings/profile');
  }

  /**
   * Upload avatar
   */
  async uploadAvatar(filePath: string): Promise<void> {
    await this.switchToTab('profile');
    await this.profileSection.avatarUpload.setInputFiles(filePath);
    await this.waitForAPIResponse('/api/v1/settings/avatar');
  }

  /**
   * Change password
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await this.switchToTab('account');
    await this.accountSection.changePasswordButton.click();

    const modal = this.page.locator('[data-testid="change-password-modal"]');
    await modal.waitFor({ state: 'visible' });

    const currentInput = modal.locator('[data-testid="current-password"]');
    const newInput = modal.locator('[data-testid="new-password"]');
    const confirmInput = modal.locator('[data-testid="confirm-password"]');
    const submitButton = modal.locator('[data-testid="submit-password-change"]');

    await this.fillInput(currentInput, currentPassword);
    await this.fillInput(newInput, newPassword);
    await this.fillInput(confirmInput, newPassword);
    await submitButton.click();

    await this.waitForAPIResponse('/api/v1/auth/change-password');
    await modal.waitFor({ state: 'hidden' });
  }

  /**
   * Enable/disable two-factor authentication
   */
  async toggleTwoFactor(enable: boolean): Promise<void> {
    await this.switchToTab('account');
    const isEnabled = await this.accountSection.twoFactorToggle.isChecked();

    if (isEnabled !== enable) {
      await this.accountSection.twoFactorToggle.click();

      if (enable) {
        // Handle 2FA setup modal
        const setupModal = this.page.locator('[data-testid="2fa-setup-modal"]');
        await setupModal.waitFor({ state: 'visible' });
        // Additional 2FA setup steps would go here
      }

      await this.waitForAPIResponse('/api/v1/settings/2fa');
    }
  }

  /**
   * Configure notification preferences
   */
  async configureNotifications(settings: {
    emailNotifications?: boolean;
    pushNotifications?: boolean;
    smsNotifications?: boolean;
    newsUpdates?: boolean;
    marketingEmails?: boolean;
    classReminders?: boolean;
    messageAlerts?: boolean;
  }): Promise<void> {
    await this.switchToTab('notifications');

    for (const [key, value] of Object.entries(settings)) {
      if (value !== undefined) {
        const toggle = this.notificationSection[key as keyof typeof this.notificationSection];
        const isChecked = await toggle.isChecked();

        if (isChecked !== value) {
          await toggle.click();
        }
      }
    }

    await this.waitForAPIResponse('/api/v1/settings/notifications');
  }

  /**
   * Configure privacy settings
   */
  async configurePrivacy(settings: {
    profileVisibility?: 'public' | 'private' | 'friends';
    showEmail?: boolean;
    showPhone?: boolean;
    allowMessages?: boolean;
    dataSharing?: boolean;
  }): Promise<void> {
    await this.switchToTab('privacy');

    if (settings.profileVisibility) {
      await this.privacySection.profileVisibility.selectOption(settings.profileVisibility);
    }

    const toggleSettings = {
      showEmail: this.privacySection.showEmail,
      showPhone: this.privacySection.showPhone,
      allowMessages: this.privacySection.allowMessages,
      dataSharing: this.privacySection.dataSharing
    };

    for (const [key, toggle] of Object.entries(toggleSettings)) {
      const value = settings[key as keyof typeof settings];
      if (typeof value === 'boolean') {
        const isChecked = await toggle.isChecked();
        if (isChecked !== value) {
          await toggle.click();
        }
      }
    }

    await this.waitForAPIResponse('/api/v1/settings/privacy');
  }

  /**
   * Change theme
   */
  async changeTheme(theme: 'light' | 'dark' | 'auto'): Promise<void> {
    await this.switchToTab('appearance');
    await this.appearanceSection.themeSelect.selectOption(theme);
    await this.waitForAPIResponse('/api/v1/settings/appearance');
  }

  /**
   * Export user data
   */
  async exportUserData(): Promise<void> {
    await this.switchToTab('account');
    await this.accountSection.exportDataButton.click();

    const confirmButton = this.page.locator('[data-testid="confirm-export"]');
    await confirmButton.click();

    // Wait for download
    const download = await this.page.waitForEvent('download');
    await download.saveAs('downloads/user-data-export.zip');
  }

  /**
   * Delete account
   */
  async deleteAccount(confirmText: string): Promise<void> {
    await this.switchToTab('account');
    await this.accountSection.deleteAccountButton.click();

    const modal = this.page.locator('[data-testid="delete-account-modal"]');
    await modal.waitFor({ state: 'visible' });

    const confirmInput = modal.locator('[data-testid="delete-confirm-input"]');
    const deleteButton = modal.locator('[data-testid="confirm-delete-account"]');

    await this.fillInput(confirmInput, confirmText);
    await deleteButton.click();

    await this.waitForAPIResponse('/api/v1/account/delete');
  }

  /**
   * Get current settings values
   */
  async getCurrentSettings(): Promise<{
    profile: any;
    notifications: any;
    privacy: any;
    appearance: any;
  }> {
    const settings = {
      profile: {},
      notifications: {},
      privacy: {},
      appearance: {}
    };

    // Get profile settings
    await this.switchToTab('profile');
    settings.profile = {
      firstName: await this.profileSection.firstNameInput.inputValue(),
      lastName: await this.profileSection.lastNameInput.inputValue(),
      email: await this.profileSection.emailInput.inputValue(),
      phone: await this.profileSection.phoneInput.inputValue(),
      bio: await this.profileSection.bioTextarea.inputValue()
    };

    // Get notification settings
    await this.switchToTab('notifications');
    settings.notifications = {
      emailNotifications: await this.notificationSection.emailNotifications.isChecked(),
      pushNotifications: await this.notificationSection.pushNotifications.isChecked(),
      smsNotifications: await this.notificationSection.smsNotifications.isChecked()
    };

    // Get privacy settings
    await this.switchToTab('privacy');
    settings.privacy = {
      showEmail: await this.privacySection.showEmail.isChecked(),
      showPhone: await this.privacySection.showPhone.isChecked(),
      allowMessages: await this.privacySection.allowMessages.isChecked()
    };

    // Get appearance settings
    await this.switchToTab('appearance');
    settings.appearance = {
      theme: await this.appearanceSection.themeSelect.inputValue(),
      compactMode: await this.appearanceSection.compactMode.isChecked(),
      animations: await this.appearanceSection.animationsToggle.isChecked()
    };

    return settings;
  }

  /**
   * Reset to default settings
   */
  async resetToDefaults(): Promise<void> {
    const resetButton = this.page.locator('[data-testid="reset-to-defaults"]');
    await resetButton.click();

    const confirmButton = this.page.locator('[data-testid="confirm-reset"]');
    await confirmButton.click();

    await this.waitForAPIResponse('/api/v1/settings/reset');
  }
}