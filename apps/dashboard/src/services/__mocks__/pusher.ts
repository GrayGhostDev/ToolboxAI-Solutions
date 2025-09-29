/**
 * Mock Pusher Service for Testing
 *
 * Provides a complete mock implementation that prevents real connections
 */

import { vi } from 'vitest';

class MockPusherService {
  private static instance: MockPusherService | null = null;
  private connectionState: string = 'disconnected';
  private channels: Map<string, any> = new Map();
  private eventHandlers: Map<string, Set<(data: any) => void>> = new Map();

  static getInstance(): MockPusherService {
    if (!MockPusherService.instance) {
      MockPusherService.instance = new MockPusherService();
    }
    return MockPusherService.instance;
  }

  static resetInstance(): void {
    MockPusherService.instance = null;
  }

  async connect(token?: string): Promise<void> {
    this.connectionState = 'connected';
    return Promise.resolve();
  }

  disconnect(reason?: string): void {
    this.connectionState = 'disconnected';
    this.channels.clear();
    this.eventHandlers.clear();
  }

  subscribe(channelName: string): any {
    const mockChannel = {
      bind: vi.fn((event: string, callback: (data: any) => void) => {
        const key = `${channelName}:${event}`;
        if (!this.eventHandlers.has(key)) {
          this.eventHandlers.set(key, new Set());
        }
        this.eventHandlers.get(key)?.add(callback);
      }),
      unbind: vi.fn(),
      trigger: vi.fn((event: string, data: any) => {
        const key = `${channelName}:${event}`;
        this.eventHandlers.get(key)?.forEach(cb => cb(data));
      }),
      unsubscribe: vi.fn(),
    };

    this.channels.set(channelName, mockChannel);
    return mockChannel;
  }

  unsubscribe(channelName: string): void {
    this.channels.delete(channelName);
    // Clear event handlers for this channel
    Array.from(this.eventHandlers.keys())
      .filter(key => key.startsWith(`${channelName}:`))
      .forEach(key => this.eventHandlers.delete(key));
  }

  trigger(channelName: string, eventName: string, data: any): void {
    const channel = this.channels.get(channelName);
    if (channel) {
      channel.trigger(eventName, data);
    }
  }

  getConnectionState(): string {
    return this.connectionState;
  }

  isConnected(): boolean {
    return this.connectionState === 'connected';
  }

  on(event: string, callback: (data: any) => void): void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    this.eventHandlers.get(event)?.add(callback);
  }

  off(event: string, callback?: (data: any) => void): void {
    if (callback) {
      this.eventHandlers.get(event)?.delete(callback);
    } else {
      this.eventHandlers.delete(event);
    }
  }

  setAuthToken(token: string): void {
    // Mock implementation
  }

  clearAuthToken(): void {
    // Mock implementation
  }

  async reconnect(): Promise<void> {
    this.connectionState = 'connected';
    return Promise.resolve();
  }
}

export const PusherService = MockPusherService;
export default MockPusherService;
