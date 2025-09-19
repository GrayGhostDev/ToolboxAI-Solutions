import { Page } from '@playwright/test';

/**
 * Pusher Test Helper
 * Utilities for testing real-time Pusher features in E2E tests
 */

export interface PusherMessage {
  channel: string;
  event: string;
  data: any;
  timestamp?: number;
}

export class PusherTestHelper {
  private page: Page;
  private messages: PusherMessage[] = [];

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Initialize Pusher test helper in the browser context
   */
  async initialize() {
    await this.page.evaluate(() => {
      // Create a global test helper object
      (window as any).pusherTestHelper = {
        messages: [],
        channels: new Map(),
        lastEvent: null,

        // Method to track Pusher events
        trackEvent: function (channel: string, event: string, data: any) {
          const message = {
            channel,
            event,
            data,
            timestamp: Date.now()
          };
          this.messages.push(message);
          this.lastEvent = message;

          // Dispatch custom event for Playwright to listen
          window.dispatchEvent(new CustomEvent('pusher-test-event', {
            detail: message
          }));
        }
      };

      // Override Pusher if it exists
      if ((window as any).Pusher) {
        const originalPusher = (window as any).Pusher;

        // Wrap Pusher constructor
        (window as any).Pusher = function (...args: any[]) {
          const instance = new originalPusher(...args);

          // Wrap subscribe method
          const originalSubscribe = instance.subscribe.bind(instance);
          instance.subscribe = function (channelName: string) {
            const channel = originalSubscribe(channelName);

            // Track channel subscription
            (window as any).pusherTestHelper.channels.set(channelName, channel);

            // Wrap bind method on channel
            const originalBind = channel.bind.bind(channel);
            channel.bind = function (eventName: string, callback: Function) {
              // Wrap the callback to track events
              const wrappedCallback = function (data: any) {
                (window as any).pusherTestHelper.trackEvent(channelName, eventName, data);
                return callback(data);
              };
              return originalBind(eventName, wrappedCallback);
            };

            return channel;
          };

          return instance;
        };

        // Copy static properties
        Object.setPrototypeOf((window as any).Pusher, originalPusher);
      }
    });
  }

  /**
   * Mock Pusher connection for predictable testing
   */
  async mockPusherConnection() {
    await this.page.route('**/pusher/**', async route => {
      const url = route.request().url();

      // Mock auth endpoint
      if (url.includes('/pusher/auth')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            auth: 'test-auth-signature',
            channel_data: JSON.stringify({
              user_id: 'test-user',
              user_info: { name: 'Test User' }
            })
          })
        });
        return;
      }

      // Mock connection establishment
      if (url.includes('websocket')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            event: 'pusher:connection_established',
            data: { socket_id: 'test-socket-id' }
          })
        });
        return;
      }

      // Let other requests through
      await route.continue();
    });
  }

  /**
   * Simulate a Pusher event in the browser
   */
  async simulateEvent(channel: string, event: string, data: any) {
    await this.page.evaluate(
      ({ channel, event, data }) => {
        // Check if channel is subscribed
        const pusherHelper = (window as any).pusherTestHelper;
        if (!pusherHelper) {
          throw new Error('Pusher test helper not initialized');
        }

        // Track the event
        pusherHelper.trackEvent(channel, event, data);

        // Try to trigger the event on the actual channel if it exists
        const channelInstance = pusherHelper.channels.get(channel);
        if (channelInstance && channelInstance.emit) {
          channelInstance.emit(event, data);
        }

        // Also dispatch a custom event that tests can listen for
        window.dispatchEvent(new CustomEvent(`pusher:${channel}:${event}`, {
          detail: data
        }));
      },
      { channel, event, data }
    );
  }

  /**
   * Wait for a specific Pusher event
   */
  async waitForEvent(channel: string, event: string, timeout: number = 10000): Promise<any> {
    return await this.page.waitForFunction(
      ({ channel, event }) => {
        const helper = (window as any).pusherTestHelper;
        if (!helper) return false;

        const lastEvent = helper.lastEvent;
        return lastEvent && lastEvent.channel === channel && lastEvent.event === event;
      },
      { channel, event },
      { timeout }
    ).then(async () => {
      // Return the event data
      return await this.page.evaluate(() => {
        const helper = (window as any).pusherTestHelper;
        return helper.lastEvent?.data;
      });
    });
  }

  /**
   * Get all events for a channel
   */
  async getChannelEvents(channel: string): Promise<PusherMessage[]> {
    return await this.page.evaluate((channel) => {
      const helper = (window as any).pusherTestHelper;
      if (!helper) return [];

      return helper.messages.filter((msg: any) => msg.channel === channel);
    }, channel);
  }

  /**
   * Get all tracked events
   */
  async getAllEvents(): Promise<PusherMessage[]> {
    return await this.page.evaluate(() => {
      const helper = (window as any).pusherTestHelper;
      return helper ? helper.messages : [];
    });
  }

  /**
   * Clear tracked events
   */
  async clearEvents() {
    await this.page.evaluate(() => {
      const helper = (window as any).pusherTestHelper;
      if (helper) {
        helper.messages = [];
        helper.lastEvent = null;
      }
    });
  }

  /**
   * Check if connected to Pusher
   */
  async isConnected(): Promise<boolean> {
    return await this.page.evaluate(() => {
      const pusher = (window as any).pusherInstance || (window as any).pusher;
      if (!pusher) return false;

      return pusher.connection?.state === 'connected';
    });
  }

  /**
   * Get connection state
   */
  async getConnectionState(): Promise<string> {
    return await this.page.evaluate(() => {
      const pusher = (window as any).pusherInstance || (window as any).pusher;
      if (!pusher) return 'not_initialized';

      return pusher.connection?.state || 'unknown';
    });
  }

  /**
   * Get list of subscribed channels
   */
  async getSubscribedChannels(): Promise<string[]> {
    return await this.page.evaluate(() => {
      const helper = (window as any).pusherTestHelper;
      if (!helper) return [];

      return Array.from(helper.channels.keys());
    });
  }

  /**
   * Wait for channel subscription
   */
  async waitForChannelSubscription(channelName: string, timeout: number = 5000): Promise<boolean> {
    return await this.page.waitForFunction(
      (channel) => {
        const helper = (window as any).pusherTestHelper;
        return helper && helper.channels.has(channel);
      },
      channelName,
      { timeout }
    ).then(() => true).catch(() => false);
  }

  /**
   * Simulate connection state change
   */
  async simulateConnectionStateChange(state: 'connected' | 'disconnected' | 'connecting' | 'failed') {
    await this.page.evaluate((state) => {
      const pusher = (window as any).pusherInstance || (window as any).pusher;
      if (!pusher || !pusher.connection) return;

      // Trigger state change event
      pusher.connection.state = state;
      if (pusher.connection.emit) {
        pusher.connection.emit('state_change', {
          previous: pusher.connection.state,
          current: state
        });
      }
    }, state);
  }

  /**
   * Simulate error condition
   */
  async simulateError(errorMessage: string) {
    await this.page.evaluate((message) => {
      const pusher = (window as any).pusherInstance || (window as any).pusher;
      if (!pusher || !pusher.connection) return;

      if (pusher.connection.emit) {
        pusher.connection.emit('error', {
          type: 'WebSocketError',
          error: { message }
        });
      }
    }, errorMessage);
  }

  /**
   * Wait for real-time update in UI
   */
  async waitForUIUpdate(selector: string, expectedText: string | RegExp, timeout: number = 10000): Promise<boolean> {
    try {
      await this.page.waitForSelector(selector, { state: 'visible', timeout });
      const element = this.page.locator(selector);
      await element.waitFor({ state: 'visible' });

      if (expectedText) {
        await this.page.waitForFunction(
          ({ selector, text }) => {
            const element = document.querySelector(selector);
            if (!element) return false;

            const content = element.textContent || '';
            if (typeof text === 'string') {
              return content.includes(text);
            } else {
              // Handle RegExp
              return new RegExp(text.source, text.flags).test(content);
            }
          },
          { selector, text: expectedText instanceof RegExp ? { source: expectedText.source, flags: expectedText.flags } : expectedText },
          { timeout }
        );
      }

      return true;
    } catch {
      return false;
    }
  }

  /**
   * Create mock Pusher instance for offline testing
   */
  async createMockPusher() {
    await this.page.evaluate(() => {
      if ((window as any).Pusher) return; // Already exists

      // Create mock Pusher class
      class MockPusher {
        connection: any;
        channels: Map<string, any>;

        constructor() {
          this.channels = new Map();
          this.connection = {
            state: 'connecting',
            bind: (event: string, callback: Function) => {},
            emit: (event: string, data: any) => {}
          };

          // Simulate connection after a delay
          setTimeout(() => {
            this.connection.state = 'connected';
            this.connection.emit('connected', {});
          }, 100);
        }

        subscribe(channelName: string) {
          const channel = {
            name: channelName,
            subscribed: true,
            callbacks: new Map(),

            bind: function (event: string, callback: Function) {
              if (!this.callbacks.has(event)) {
                this.callbacks.set(event, []);
              }
              this.callbacks.get(event).push(callback);
            },

            emit: function (event: string, data: any) {
              const callbacks = this.callbacks.get(event) || [];
              callbacks.forEach((cb: Function) => cb(data));
            },

            unbind: function (event?: string) {
              if (event) {
                this.callbacks.delete(event);
              } else {
                this.callbacks.clear();
              }
            }
          };

          this.channels.set(channelName, channel);
          return channel;
        }

        unsubscribe(channelName: string) {
          this.channels.delete(channelName);
        }

        disconnect() {
          this.connection.state = 'disconnected';
          this.channels.clear();
        }
      }

      (window as any).Pusher = MockPusher;
      (window as any).mockPusherEnabled = true;
    });
  }
}

/**
 * Create a Pusher test helper instance
 */
export function createPusherTestHelper(page: Page): PusherTestHelper {
  return new PusherTestHelper(page);
}