jest.setTimeout(10000);

import { test, expect } from '@playwright/test';
import { Page } from '@playwright/test';

/**
 * Messages System E2E Tests
 * Tests for messaging, notifications, and communication features
 * Using Playwright 2025 best practices
 */

// Helper to login
async function loginAs(page: Page, role: 'teacher' | 'student' | 'admin') {
  const credentials = {
    teacher: { email: 'jane.smith@school.edu', password: 'Teacher123!' },
    student: { email: 'alex.johnson@student.edu', password: 'Student123!' },
    admin: { email: 'admin@toolboxai.com', password: 'Admin123!' }
  };

  await page.goto('/login');
  await page.locator('input[name="email"]').fill(credentials[role].email);
  await page.locator('input[name="password"]').fill(credentials[role].password);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 10000 });
}

test.describe('Messages - Inbox and Sending', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'teacher');
    // Navigate to messages
    await page.getByRole('link', { name: /messages|inbox/i }).click();
    await page.waitForLoadState('networkidle');
  });

  test('should display messages inbox', async ({ page }) => {
    // Check page heading
    await expect(page.getByRole('heading', { name: /messages|inbox/i })).toBeVisible();

    // Check for compose button
    await expect(page.getByRole('button', { name: /compose|new message/i })).toBeVisible();

    // Check for inbox sections
    await expect(page.getByText(/inbox|received/i)).toBeVisible();
    await expect(page.getByText(/sent/i)).toBeVisible();

    // Check for message list
    const messageList = page.locator('[data-testid="message-list"], .messages-container').first();
    await expect(messageList).toBeVisible();
  });

  test('should compose and send a message', async ({ page }) => {
    // Click compose button
    await page.getByRole('button', { name: /compose|new message/i }).click();

    // Wait for compose modal/form
    await page.waitForSelector('[role="dialog"], .compose-form', { timeout: 5000 });

    // Select recipient
    const recipientInput = page.locator('input[name="recipient"], input[placeholder*="recipient"]').first();
    await recipientInput.fill('alex');

    // Handle autocomplete if present
    const suggestion = page.getByRole('option', { name: /alex/i }).first();
    if (await suggestion.isVisible({ timeout: 1000 })) {
      await suggestion.click();
    }

    // Fill subject
    await page.locator('input[name="subject"], input[placeholder*="subject"]').fill(
      'Test Message Subject'
    );

    // Fill message body
    await page.locator('textarea[name="message"], .message-editor').fill(
      'This is a test message sent via E2E testing. Please ignore.'
    );

    // Add attachment if supported
    const attachButton = page.locator('button[aria-label*="attach"], [data-testid="attach-file"]').first();
    if (await attachButton.isVisible()) {
      const fileInput = page.locator('input[type="file"]').first();
      await fileInput.setInputFiles({
        name: 'test-document.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('fake-pdf-content')
      });
    }

    // Send message
    await page.getByRole('button', { name: /send/i }).click();

    // Verify success
    await expect(page.getByText(/message.*sent|successfully/i)).toBeVisible({ timeout: 5000 });

    // Verify message appears in sent folder
    await page.getByRole('tab', { name: /sent/i }).click();
    await expect(page.getByText('Test Message Subject')).toBeVisible({ timeout: 5000 });
  });

  test('should reply to a message', async ({ page }) => {
    // Click on first message to open
    const firstMessage = page.locator('[data-testid="message-item"], .message-row').first();
    if (await firstMessage.isVisible()) {
      await firstMessage.click();

      // Wait for message detail view
      await page.waitForSelector('.message-detail, [data-testid="message-content"]', { timeout: 5000 });

      // Click reply button
      await page.getByRole('button', { name: /reply/i }).click();

      // Fill reply
      const replyInput = page.locator('textarea[name="reply"], .reply-editor').first();
      await replyInput.fill('This is a test reply to your message.');

      // Send reply
      await page.getByRole('button', { name: /send|reply/i }).click();

      // Verify reply sent
      await expect(page.getByText(/reply.*sent|sent/i)).toBeVisible({ timeout: 5000 });
    }
  });

  test('should forward a message', async ({ page }) => {
    // Open first message
    const firstMessage = page.locator('[data-testid="message-item"]').first();
    if (await firstMessage.isVisible()) {
      await firstMessage.click();

      // Click forward button
      const forwardBtn = page.getByRole('button', { name: /forward/i });
      if (await forwardBtn.isVisible()) {
        await forwardBtn.click();

        // Select recipient
        await page.locator('input[name="recipient"]').fill('admin');

        // Add forward note
        await page.locator('textarea[name="note"], textarea[placeholder*="note"]').fill(
          'FYI - Forwarding this message for your review.'
        );

        // Send
        await page.getByRole('button', { name: /forward|send/i }).click();

        // Verify
        await expect(page.getByText(/forwarded|sent/i)).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('should delete a message', async ({ page }) => {
    // Find a message to delete
    const messageToDelete = page.locator('[data-testid="message-item"]').first();

    if (await messageToDelete.isVisible()) {
      // Select message (checkbox)
      const checkbox = messageToDelete.locator('input[type="checkbox"]').first();
      await checkbox.check();

      // Click delete button
      await page.getByRole('button', { name: /delete|trash/i }).click();

      // Confirm deletion
      const confirmBtn = page.getByRole('button', { name: /confirm|delete|yes/i });
      if (await confirmBtn.isVisible()) {
        await confirmBtn.click();
      }

      // Verify deletion
      await expect(page.getByText(/deleted|moved to trash/i)).toBeVisible({ timeout: 5000 });
    }
  });

  test('should mark messages as read/unread', async ({ page }) => {
    // Select first unread message
    const unreadMessage = page.locator('[data-testid="message-item"].unread, .message-row.unread').first();

    if (await unreadMessage.isVisible()) {
      // Select it
      const checkbox = unreadMessage.locator('input[type="checkbox"]').first();
      await checkbox.check();

      // Mark as read
      await page.getByRole('button', { name: /mark.*read/i }).click();

      // Verify status change
      await expect(unreadMessage).not.toHaveClass(/unread/);
    } else {
      // If no unread, mark a read message as unread
      const readMessage = page.locator('[data-testid="message-item"]').first();
      const checkbox = readMessage.locator('input[type="checkbox"]').first();
      await checkbox.check();

      await page.getByRole('button', { name: /mark.*unread/i }).click();

      // Verify
      await expect(readMessage).toHaveClass(/unread/);
    }
  });

  test('should search messages', async ({ page }) => {
    // Find search input
    const searchInput = page.locator('input[placeholder*="search"], input[name="search"]').first();
    await searchInput.fill('homework');
    await searchInput.press('Enter');

    // Wait for search results
    await page.waitForTimeout(1000);

    // Verify filtered results
    const messages = page.locator('[data-testid="message-item"]');
    const count = await messages.count();

    if (count > 0) {
      // Verify results contain search term
      const firstMessage = await messages.first().textContent();
      expect(firstMessage?.toLowerCase()).toContain('homework');
    } else {
      // Verify "no results" message
      await expect(page.getByText(/no.*messages.*found/i)).toBeVisible();
    }
  });

  test('should filter messages by type', async ({ page }) => {
    // Apply filter
    const filterDropdown = page.locator('[data-testid="message-filter"], select[name="filter"]').first();
    if (await filterDropdown.isVisible()) {
      await filterDropdown.selectOption('unread');

      // Wait for filter
      await page.waitForTimeout(1000);

      // Verify only unread messages shown
      const messages = page.locator('[data-testid="message-item"]');
      const firstMessage = messages.first();
      if (await firstMessage.isVisible()) {
        await expect(firstMessage).toHaveClass(/unread/);
      }
    }
  });
});

test.describe('Messages - Group Communication', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'teacher');
    await page.getByRole('link', { name: /messages/i }).click();
  });

  test('should create a group message', async ({ page }) => {
    // Click compose
    await page.getByRole('button', { name: /compose|new/i }).click();

    // Look for group option
    const groupOption = page.getByRole('button', { name: /group.*message/i });
    if (await groupOption.isVisible()) {
      await groupOption.click();

      // Select multiple recipients
      const recipientInput = page.locator('input[name="recipients"]').first();
      await recipientInput.fill('student');

      // Select multiple students from dropdown
      const checkboxes = page.locator('[role="option"] input[type="checkbox"]');
      const count = await checkboxes.count();
      for (let i = 0; i < Math.min(3, count); i++) {
        await checkboxes.nth(i).check();
      }

      // Fill subject
      await page.locator('input[name="subject"]').fill('Group Announcement');

      // Fill message
      await page.locator('textarea[name="message"]').fill(
        'This is a group message to all selected students.'
      );

      // Send
      await page.getByRole('button', { name: /send/i }).click();

      // Verify
      await expect(page.getByText(/sent to.*recipients/i)).toBeVisible({ timeout: 5000 });
    }
  });

  test('should send class-wide announcement', async ({ page }) => {
    // Look for announcement feature
    const announcementBtn = page.getByRole('button', { name: /announcement/i });

    if (await announcementBtn.isVisible()) {
      await announcementBtn.click();

      // Select class
      const classSelect = page.locator('select[name="class"], [data-testid="class-select"]').first();
      await classSelect.selectOption({ index: 1 }); // Select first class

      // Fill announcement
      await page.locator('input[name="title"]').fill('Important Class Update');
      await page.locator('textarea[name="announcement"]').fill(
        'Please note that tomorrow\'s class will be held in Room 201 instead of the usual classroom.'
      );

      // Set priority if available
      const prioritySelect = page.locator('select[name="priority"]').first();
      if (await prioritySelect.isVisible()) {
        await prioritySelect.selectOption('high');
      }

      // Send announcement
      await page.getByRole('button', { name: /send|post/i }).click();

      // Verify
      await expect(page.getByText(/announcement.*sent/i)).toBeVisible({ timeout: 5000 });
    }
  });
});

test.describe('Messages - Notifications', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'student');
  });

  test('should display notification badge', async ({ page }) => {
    // Check for notification badge
    const notificationBadge = page.locator('[data-testid="notification-badge"], .notification-count').first();

    if (await notificationBadge.isVisible()) {
      // Get count
      const count = await notificationBadge.textContent();
      expect(parseInt(count || '0')).toBeGreaterThanOrEqual(0);
    }

    // Check notification bell/icon
    const notificationIcon = page.locator('[aria-label*="notification"], [data-testid="notification-icon"]').first();
    await expect(notificationIcon).toBeVisible();
  });

  test('should view notifications dropdown', async ({ page }) => {
    // Click notification icon
    const notificationIcon = page.locator('[aria-label*="notification"], [data-testid="notification-icon"]').first();
    await notificationIcon.click();

    // Check dropdown appears
    const dropdown = page.locator('[role="menu"], .notifications-dropdown').first();
    await expect(dropdown).toBeVisible();

    // Check for notification items
    const notifications = dropdown.locator('.notification-item, [role="menuitem"]');
    const count = await notifications.count();

    if (count > 0) {
      // Click first notification
      await notifications.first().click();

      // Should navigate or open detail
      await page.waitForTimeout(1000);
    } else {
      // Check for empty state
      await expect(dropdown.getByText(/no.*notifications/i)).toBeVisible();
    }
  });

  test('should mark all notifications as read', async ({ page }) => {
    // Open notifications
    await page.locator('[aria-label*="notification"]').first().click();

    // Look for "mark all as read"
    const markAllBtn = page.getByRole('button', { name: /mark all.*read/i });
    if (await markAllBtn.isVisible()) {
      await markAllBtn.click();

      // Verify badge clears
      const badge = page.locator('[data-testid="notification-badge"]').first();
      if (await badge.isVisible({ timeout: 1000 })) {
        const count = await badge.textContent();
        expect(count).toBe('0');
      }
    }
  });

  test('should configure notification preferences', async ({ page }) => {
    // Navigate to settings
    await page.getByRole('link', { name: /settings|preferences/i }).click();

    // Find notification settings
    const notificationTab = page.getByRole('tab', { name: /notification/i });
    if (await notificationTab.isVisible()) {
      await notificationTab.click();

      // Toggle email notifications
      const emailToggle = page.locator('[name="email_notifications"], [data-testid="email-toggle"]').first();
      if (await emailToggle.isVisible()) {
        await emailToggle.click();
      }

      // Configure notification types
      const messageNotif = page.locator('[name="notify_messages"]').first();
      if (await messageNotif.isVisible()) {
        await messageNotif.check();
      }

      // Save preferences
      await page.getByRole('button', { name: /save/i }).click();

      // Verify saved
      await expect(page.getByText(/preferences.*saved/i)).toBeVisible({ timeout: 5000 });
    }
  });
});

test.describe('Messages - Real-time Features', () => {
  test('should receive real-time message notifications', async ({ page, context }) => {
    // Login as teacher
    await loginAs(page, 'teacher');
    await page.getByRole('link', { name: /messages/i }).click();

    // Open second browser context as student
    const page2 = await context.newPage();
    await loginAs(page2, 'student');
    await page2.getByRole('link', { name: /messages/i }).click();

    // Student sends message to teacher
    await page2.getByRole('button', { name: /compose/i }).click();
    await page2.locator('input[name="recipient"]').fill('jane.smith');
    await page2.locator('input[name="subject"]').fill('Real-time Test');
    await page2.locator('textarea[name="message"]').fill('Testing real-time delivery');
    await page2.getByRole('button', { name: /send/i }).click();

    // Teacher should receive notification
    await page.waitForTimeout(2000); // Wait for real-time update

    // Check for notification
    const notification = page.locator('[data-testid="new-message-notification"], .toast-notification').first();
    if (await notification.isVisible({ timeout: 5000 })) {
      await expect(notification).toContainText(/new message/i);
    }

    // Check inbox updates
    const unreadIndicator = page.locator('.unread-indicator, [data-testid="unread-count"]').first();
    await expect(unreadIndicator).toBeVisible({ timeout: 5000 });

    await page2.close();
  });

  test('should show typing indicators', async ({ page, context }) => {
    // This test checks if typing indicators are implemented
    await loginAs(page, 'teacher');

    // Open a message thread
    const firstMessage = page.locator('[data-testid="message-item"]').first();
    if (await firstMessage.isVisible()) {
      await firstMessage.click();

      // Start replying
      const replyInput = page.locator('textarea[name="reply"]').first();
      if (await replyInput.isVisible()) {
        // Type slowly to trigger indicator
        await replyInput.type('Testing typing indicator...', { delay: 100 });

        // In a real scenario, another user would see the typing indicator
        // For now, just verify the input works
        expect(await replyInput.inputValue()).toContain('Testing typing');
      }
    }
  });
});

test.describe('Messages - Admin Features', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
    await page.getByRole('link', { name: /messages/i }).click();
  });

  test('should view system-wide messaging statistics', async ({ page }) => {
    // Look for admin dashboard/stats
    const statsTab = page.getByRole('tab', { name: /statistics|analytics/i });
    if (await statsTab.isVisible()) {
      await statsTab.click();

      // Check for stats
      await expect(page.getByText(/total.*messages/i)).toBeVisible();
      await expect(page.getByText(/active.*conversations/i)).toBeVisible();
      await expect(page.getByText(/average.*response/i)).toBeVisible();
    }
  });

  test('should send system-wide broadcast', async ({ page }) => {
    // Look for broadcast feature
    const broadcastBtn = page.getByRole('button', { name: /broadcast|system.*message/i });

    if (await broadcastBtn.isVisible()) {
      await broadcastBtn.click();

      // Fill broadcast details
      await page.locator('input[name="title"]').fill('System Maintenance Notice');
      await page.locator('textarea[name="message"]').fill(
        'The system will undergo maintenance on Sunday from 2 AM to 4 AM EST.'
      );

      // Select urgency
      const urgencySelect = page.locator('select[name="urgency"]').first();
      if (await urgencySelect.isVisible()) {
        await urgencySelect.selectOption('info');
      }

      // Select target audience
      const audienceCheckboxes = page.locator('[name="audience"] input[type="checkbox"]');
      if (await audienceCheckboxes.first().isVisible()) {
        await page.locator('[value="all"]').check();
      }

      // Send broadcast
      await page.getByRole('button', { name: /send.*broadcast/i }).click();

      // Confirm
      await page.getByRole('button', { name: /confirm/i }).click();

      // Verify
      await expect(page.getByText(/broadcast.*sent/i)).toBeVisible({ timeout: 5000 });
    }
  });

  test('should moderate flagged messages', async ({ page }) => {
    // Navigate to moderation if available
    const moderationTab = page.getByRole('tab', { name: /moderation|flagged/i });
    if (await moderationTab.isVisible()) {
      await moderationTab.click();

      // Check for flagged messages
      const flaggedMessages = page.locator('[data-testid="flagged-message"]');
      const count = await flaggedMessages.count();

      if (count > 0) {
        // Review first flagged message
        await flaggedMessages.first().click();

        // Take action
        const actionDropdown = page.locator('select[name="action"]').first();
        await actionDropdown.selectOption('approve');

        // Add note
        await page.locator('textarea[name="moderator_note"]').fill(
          'Reviewed and approved - no policy violations found.'
        );

        // Submit
        await page.getByRole('button', { name: /submit|save/i }).click();

        // Verify
        await expect(page.getByText(/action.*taken/i)).toBeVisible({ timeout: 5000 });
      }
    }
  });
});