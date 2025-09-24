import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Messages Page Object Model
 * Handles messaging functionality and interactions
 */
export class MessagesPage extends BasePage {
  // Page elements
  private inbox: Locator;
  private composeButton: Locator;
  private searchBar: Locator;
  private messageList: Locator;
  private messagePreview: Locator;
  private filterTabs: {
    all: Locator;
    unread: Locator;
    sent: Locator;
    archived: Locator;
  };

  // Compose modal
  private composeModal: {
    container: Locator;
    recipientInput: Locator;
    subjectInput: Locator;
    messageBody: Locator;
    attachButton: Locator;
    sendButton: Locator;
    cancelButton: Locator;
  };

  // Message actions
  private messageActions: {
    reply: Locator;
    forward: Locator;
    archive: Locator;
    delete: Locator;
    markAsRead: Locator;
    star: Locator;
  };

  constructor(page: Page) {
    super(page);

    // Initialize page elements
    this.inbox = page.locator('[data-testid="messages-inbox"]');
    this.composeButton = page.locator('[data-testid="compose-message-button"]');
    this.searchBar = page.locator('[data-testid="message-search"]');
    this.messageList = page.locator('[data-testid="message-list"]');
    this.messagePreview = page.locator('[data-testid="message-preview"]');

    // Initialize filter tabs
    this.filterTabs = {
      all: page.locator('[data-testid="filter-all"]'),
      unread: page.locator('[data-testid="filter-unread"]'),
      sent: page.locator('[data-testid="filter-sent"]'),
      archived: page.locator('[data-testid="filter-archived"]')
    };

    // Initialize compose modal
    this.composeModal = {
      container: page.locator('[data-testid="compose-modal"]'),
      recipientInput: page.locator('[data-testid="recipient-input"]'),
      subjectInput: page.locator('[data-testid="subject-input"]'),
      messageBody: page.locator('[data-testid="message-body"]'),
      attachButton: page.locator('[data-testid="attach-file"]'),
      sendButton: page.locator('[data-testid="send-message"]'),
      cancelButton: page.locator('[data-testid="cancel-compose"]')
    };

    // Initialize message actions
    this.messageActions = {
      reply: page.locator('[data-testid="reply-button"]'),
      forward: page.locator('[data-testid="forward-button"]'),
      archive: page.locator('[data-testid="archive-button"]'),
      delete: page.locator('[data-testid="delete-button"]'),
      markAsRead: page.locator('[data-testid="mark-read-button"]'),
      star: page.locator('[data-testid="star-button"]')
    };
  }

  /**
   * Navigate to messages page
   */
  async goto(): Promise<void> {
    await this.navigate('/messages');
    await this.waitForPageLoad();
  }

  /**
   * Compose and send a new message
   */
  async composeMessage(data: {
    recipient: string;
    subject: string;
    body: string;
    attachments?: string[];
  }): Promise<void> {
    await this.composeButton.click();
    await this.composeModal.container.waitFor({ state: 'visible' });

    await this.fillInput(this.composeModal.recipientInput, data.recipient);
    await this.fillInput(this.composeModal.subjectInput, data.subject);
    await this.fillInput(this.composeModal.messageBody, data.body);

    if (data.attachments) {
      for (const file of data.attachments) {
        await this.composeModal.attachButton.setInputFiles(file);
      }
    }

    await this.composeModal.sendButton.click();
    await this.waitForAPIResponse('/api/v1/messages/send');
    await this.composeModal.container.waitFor({ state: 'hidden' });
  }

  /**
   * Search messages
   */
  async searchMessages(query: string): Promise<void> {
    await this.fillInput(this.searchBar, query);
    await this.page.keyboard.press('Enter');
    await this.waitForAPIResponse('/api/v1/messages/search');
  }

  /**
   * Filter messages by type
   */
  async filterMessages(filter: keyof typeof this.filterTabs): Promise<void> {
    await this.filterTabs[filter].click();
    await this.waitForAPIResponse('/api/v1/messages');
  }

  /**
   * Get all messages in list
   */
  async getAllMessages(): Promise<Array<{
    sender: string;
    subject: string;
    preview: string;
    time: string;
    isRead: boolean;
  }>> {
    const messageItems = await this.messageList.locator('.message-item').all();
    const messages = [];

    for (const item of messageItems) {
      messages.push({
        sender: await item.locator('.sender-name').textContent() || '',
        subject: await item.locator('.message-subject').textContent() || '',
        preview: await item.locator('.message-preview').textContent() || '',
        time: await item.locator('.message-time').textContent() || '',
        isRead: !(await item.locator('.unread-indicator').isVisible())
      });
    }

    return messages;
  }

  /**
   * Open a message by index
   */
  async openMessage(index: number): Promise<void> {
    const messageItem = this.messageList.locator('.message-item').nth(index);
    await messageItem.click();
    await this.messagePreview.waitFor({ state: 'visible' });
  }

  /**
   * Reply to current message
   */
  async replyToMessage(replyText: string): Promise<void> {
    await this.messageActions.reply.click();
    const replyBox = this.page.locator('[data-testid="reply-box"]');
    await this.fillInput(replyBox, replyText);
    const sendReply = this.page.locator('[data-testid="send-reply"]');
    await sendReply.click();
    await this.waitForAPIResponse('/api/v1/messages/reply');
  }

  /**
   * Forward current message
   */
  async forwardMessage(recipient: string, additionalText?: string): Promise<void> {
    await this.messageActions.forward.click();
    const forwardModal = this.page.locator('[data-testid="forward-modal"]');
    await forwardModal.waitFor({ state: 'visible' });

    const recipientInput = forwardModal.locator('[data-testid="forward-recipient"]');
    await this.fillInput(recipientInput, recipient);

    if (additionalText) {
      const textInput = forwardModal.locator('[data-testid="forward-text"]');
      await this.fillInput(textInput, additionalText);
    }

    const sendButton = forwardModal.locator('[data-testid="send-forward"]');
    await sendButton.click();
    await this.waitForAPIResponse('/api/v1/messages/forward');
  }

  /**
   * Archive current message
   */
  async archiveMessage(): Promise<void> {
    await this.messageActions.archive.click();
    await this.waitForAPIResponse('/api/v1/messages/archive');
  }

  /**
   * Delete current message
   */
  async deleteMessage(): Promise<void> {
    await this.messageActions.delete.click();
    const confirmButton = this.page.locator('[data-testid="confirm-delete-message"]');
    await confirmButton.click();
    await this.waitForAPIResponse('/api/v1/messages/delete');
  }

  /**
   * Mark message as read/unread
   */
  async toggleReadStatus(): Promise<void> {
    await this.messageActions.markAsRead.click();
    await this.waitForAPIResponse('/api/v1/messages/mark-read');
  }

  /**
   * Star/unstar message
   */
  async toggleStar(): Promise<void> {
    await this.messageActions.star.click();
    await this.waitForAPIResponse('/api/v1/messages/star');
  }

  /**
   * Get unread message count
   */
  async getUnreadCount(): Promise<number> {
    const unreadBadge = this.page.locator('[data-testid="unread-count"]');
    if (await unreadBadge.isVisible()) {
      const count = await unreadBadge.textContent();
      return parseInt(count || '0', 10);
    }
    return 0;
  }

  /**
   * Bulk select messages
   */
  async selectMessages(indices: number[]): Promise<void> {
    for (const index of indices) {
      const checkbox = this.messageList
        .locator('.message-item')
        .nth(index)
        .locator('[data-testid="message-checkbox"]');
      await checkbox.check();
    }
  }

  /**
   * Bulk delete selected messages
   */
  async bulkDelete(): Promise<void> {
    const bulkDeleteButton = this.page.locator('[data-testid="bulk-delete"]');
    await bulkDeleteButton.click();
    const confirmButton = this.page.locator('[data-testid="confirm-bulk-delete"]');
    await confirmButton.click();
    await this.waitForAPIResponse('/api/v1/messages/bulk-delete');
  }

  /**
   * Check if message thread is displayed
   */
  async hasMessageThread(): Promise<boolean> {
    const thread = this.page.locator('[data-testid="message-thread"]');
    return await this.isElementVisible(thread);
  }
}