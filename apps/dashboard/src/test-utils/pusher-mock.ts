/**
 * Pusher Test Utilities and Mocks
 *
 * Provides comprehensive mocking utilities for testing Pusher functionality:
 * - Mock Pusher client with full API compatibility
 * - Mock channel objects with event simulation
 * - Mock presence functionality
 * - Event simulation helpers
 * - Connection state mocks
 */

import { vi } from 'vitest';
import { WebSocketState, WebSocketMessageType } from '../types/websocket';

export interface MockPusherChannel {
  name: string;
  bind: ReturnType<typeof vi.fn>;
  unbind: ReturnType<typeof vi.fn>;
  trigger: ReturnType<typeof vi.fn>;
  unsubscribe: ReturnType<typeof vi.fn>;
  members?: MockPusherMembers;
}

export interface MockPusherMembers {
  count: number;
  members: Record<string, any>;
  me?: any;
  each: ReturnType<typeof vi.fn>;
  get: ReturnType<typeof vi.fn>;
}

export interface MockPusherConnection {
  state: string;
  bind: ReturnType<typeof vi.fn>;
  unbind: ReturnType<typeof vi.fn>;
  socket_id?: string;
}

export interface MockPusherClient {
  connection: MockPusherConnection;
  channels: Record<string, MockPusherChannel>;
  subscribe: ReturnType<typeof vi.fn>;
  unsubscribe: ReturnType<typeof vi.fn>;
  bind: ReturnType<typeof vi.fn>;
  unbind: ReturnType<typeof vi.fn>;
  unbind_all: ReturnType<typeof vi.fn>;
  disconnect: ReturnType<typeof vi.fn>;
  channel: ReturnType<typeof vi.fn>;
  config: {
    auth: {
      headers: Record<string, string>;
    };
  };
}

/**
 * Creates a mock Pusher channel with full functionality
 */
export function createMockChannel(name: string): MockPusherChannel {
  const eventHandlers: Record<string, Array<(payload: unknown) => void>> = {};

  const channel: MockPusherChannel = {
    name,
    bind: vi.fn((event: string, callback: (payload: unknown) => void) => {
      if (!eventHandlers[event]) {
        eventHandlers[event] = [];
      }
      eventHandlers[event].push(callback);
    }),
    unbind: vi.fn((event?: string, callback?: (payload: unknown) => void) => {
      if (event && callback) {
        const handlers = eventHandlers[event] || [];
        const index = handlers.indexOf(callback);
        if (index !== -1) {
          handlers.splice(index, 1);
        }
      } else if (event) {
        delete eventHandlers[event];
      } else {
        Object.keys(eventHandlers).forEach(key => {
          delete eventHandlers[key];
        });
      }
    }),
    trigger: vi.fn((event: string, data: any) => {
      const handlers = eventHandlers[event] || [];
      handlers.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error('Mock channel handler error:', error);
        }
      });
      return true;
    }),
    unsubscribe: vi.fn()
  };

  // Add presence functionality for presence channels
  if (name.startsWith('presence-')) {
    channel.members = createMockMembers();
  }

  // Store event handlers for testing
  (channel as any).__eventHandlers = eventHandlers;

  return channel;
}

/**
 * Creates mock presence members object
 */
export function createMockMembers(): MockPusherMembers {
  const members: Record<string, any> = {};

  return {
    count: 0,
    members,
    me: undefined,
    each: vi.fn((callback: (member: any) => void) => {
      Object.values(members).forEach(callback);
    }),
    get: vi.fn((id: string) => members[id])
  };
}

/**
 * Creates a mock Pusher client instance
 */
export function createMockPusherClient(): MockPusherClient {
  const channels: Record<string, MockPusherChannel> = {};
  const globalEventHandlers: Record<string, Array<(payload: unknown) => void>> = {};

  const connection: MockPusherConnection = {
    state: 'disconnected',
    bind: vi.fn((event: string, callback: (payload: unknown) => void) => {
      if (!globalEventHandlers[event]) {
        globalEventHandlers[event] = [];
      }
      globalEventHandlers[event].push(callback);
    }),
    unbind: vi.fn((event?: string, callback?: (payload: unknown) => void) => {
      if (event && callback) {
        const handlers = globalEventHandlers[event] || [];
        const index = handlers.indexOf(callback);
        if (index !== -1) {
          handlers.splice(index, 1);
        }
      } else if (event) {
        delete globalEventHandlers[event];
      }
    }),
    socket_id: 'mock-socket-id'
  };

  const client: MockPusherClient = {
    connection,
    channels,
    subscribe: vi.fn((channelName: string) => {
      if (!channels[channelName]) {
        channels[channelName] = createMockChannel(channelName);
      }
      return channels[channelName];
    }),
    unsubscribe: vi.fn((channelName: string) => {
      delete channels[channelName];
    }),
    bind: vi.fn((event: string, callback: (payload: unknown) => void) => {
      if (!globalEventHandlers[event]) {
        globalEventHandlers[event] = [];
      }
      globalEventHandlers[event].push(callback);
    }),
    unbind: vi.fn((event?: string, callback?: (payload: unknown) => void) => {
      if (event && callback) {
        const handlers = globalEventHandlers[event] || [];
        const index = handlers.indexOf(callback);
        if (index !== -1) {
          handlers.splice(index, 1);
        }
      } else if (event) {
        delete globalEventHandlers[event];
      }
    }),
    unbind_all: vi.fn(() => {
      Object.keys(globalEventHandlers).forEach(event => {
        delete globalEventHandlers[event];
      });
      Object.values(channels).forEach(channel => {
        channel.unbind();
      });
    }),
    disconnect: vi.fn(() => {
      connection.state = 'disconnected';
      const handlers = globalEventHandlers['disconnected'] || [];
      handlers.forEach(handler => handler());
    }),
    channel: vi.fn((channelName: string) => {
      return channels[channelName] || null;
    }),
    config: {
      auth: {
        headers: {}
      }
    }
  };

  // Store event handlers for testing
  (client as any).__globalEventHandlers = globalEventHandlers;

  return client;
}

/**
 * Event simulation helpers
 */
export class PusherEventSimulator {
  constructor(private client: MockPusherClient) {}

  /**
   * Simulate connection events
   */
  connect(): void {
    this.client.connection.state = 'connected';
    this.triggerConnectionEvent('connected');
  }

  disconnect(): void {
    this.client.connection.state = 'disconnected';
    this.triggerConnectionEvent('disconnected');
  }

  error(error: any): void {
    this.triggerConnectionEvent('error', error);
  }

  private triggerConnectionEvent(event: string, data?: any): void {
    const handlers = (this.client as any).__globalEventHandlers[event] || [];
    handlers.forEach((handler: (payload: unknown) => void) => {
      try {
        handler(data);
      } catch (error) {
        console.error('Mock connection handler error:', error);
      }
    });
  }

  /**
   * Simulate channel events
   */
  triggerChannelEvent(channelName: string, event: string, data: any): void {
    const channel = this.client.channels[channelName];
    if (channel) {
      channel.trigger(event, data);
    }
  }

  /**
   * Simulate subscription events
   */
  subscriptionSucceeded(channelName: string, data?: any): void {
    this.triggerChannelEvent(channelName, 'pusher:subscription_succeeded', data);
  }

  subscriptionError(channelName: string, error: any): void {
    this.triggerChannelEvent(channelName, 'pusher:subscription_error', error);
  }

  /**
   * Simulate presence events
   */
  memberAdded(channelName: string, member: any): void {
    const channel = this.client.channels[channelName];
    if (channel?.members) {
      channel.members.members[member.id] = member;
      channel.members.count++;
      this.triggerChannelEvent(channelName, 'pusher:member_added', member);
    }
  }

  memberRemoved(channelName: string, member: any): void {
    const channel = this.client.channels[channelName];
    if (channel?.members) {
      delete channel.members.members[member.id];
      channel.members.count--;
      this.triggerChannelEvent(channelName, 'pusher:member_removed', member);
    }
  }

  /**
   * Simulate application-specific events
   */
  messageReceived(channelName: string, messageType: WebSocketMessageType, payload: any): void {
    this.triggerChannelEvent(channelName, 'message', {
      type: messageType,
      payload,
      timestamp: new Date().toISOString(),
      messageId: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    });
  }

  contentProgress(channelName: string, progress: any): void {
    this.messageReceived(channelName, WebSocketMessageType.CONTENT_PROGRESS, progress);
  }

  contentComplete(channelName: string, content: any): void {
    this.messageReceived(channelName, WebSocketMessageType.CONTENT_COMPLETE, content);
  }

  systemNotification(channelName: string, notification: any): void {
    this.messageReceived(channelName, WebSocketMessageType.SYSTEM_NOTIFICATION, notification);
  }
}

/**
 * Mock Pusher service factory
 */
export function createMockPusherService() {
  const client = createMockPusherClient();
  const simulator = new PusherEventSimulator(client);

  const channels = new Map<string, any>();
  const subscriptions = new Map<string, Set<any>>();
  let state = WebSocketState.DISCONNECTED;
  const stateHandlers = new Set<(state: unknown) => void>();
  const errorHandlers = new Set<(err: Error) => void>();

  return {
    // Core methods
    connect: vi.fn().mockImplementation(async (token?: string) => {
      state = WebSocketState.CONNECTING;
      simulator.connect();
      state = WebSocketState.CONNECTED;
      stateHandlers.forEach(handler => handler(state));
    }),

    disconnect: vi.fn().mockImplementation((reason?: string) => {
      state = WebSocketState.DISCONNECTING;
      simulator.disconnect();
      state = WebSocketState.DISCONNECTED;
      stateHandlers.forEach(handler => handler(state));
    }),

    subscribe: vi.fn().mockImplementation((channelName: string, handler: (payload: unknown) => void) => {
      const subscriptionId = `sub_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

      if (!subscriptions.has(channelName)) {
        subscriptions.set(channelName, new Set());
        const channel = client.subscribe(channelName);
        channels.set(channelName, channel);
      }

      const subscription = { subscriptionId, handler, channel: channelName };
      subscriptions.get(channelName)?.add(subscription);

      return subscriptionId;
    }),

    unsubscribe: vi.fn().mockImplementation((subscriptionId: string) => {
      for (const [channelName, subs] of subscriptions.entries()) {
        const sub = Array.from(subs).find((s: any) => s.subscriptionId === subscriptionId);
        if (sub) {
          subs.delete(sub);
          if (subs.size === 0) {
            subscriptions.delete(channelName);
            client.unsubscribe(channelName);
            channels.delete(channelName);
          }
          break;
        }
      }
    }),

    send: vi.fn().mockResolvedValue({ ok: true }),

    // State management
    getState: vi.fn(() => state),
    isConnected: vi.fn(() => state === WebSocketState.CONNECTED),

    // Event handlers
    on: vi.fn(),
    off: vi.fn(),
    onStateChange: vi.fn((handler: (state: unknown) => void) => {
      stateHandlers.add(handler);
      return () => stateHandlers.delete(handler);
    }),
    onError: vi.fn((handler: (err: Error) => void) => {
      errorHandlers.add(handler);
      return () => errorHandlers.delete(handler);
    }),

    // Statistics
    getStats: vi.fn(() => ({
      connectionState: state,
      messagesSent: 0,
      messagesReceived: 0,
      reconnectAttempts: 0,
      bytesReceived: 0,
      bytesSent: 0
    })),

    // Authentication
    refreshToken: vi.fn().mockResolvedValue(undefined),

    // Internal for testing
    __client: client,
    __simulator: simulator,
    __channels: channels,
    __subscriptions: subscriptions,
    __setState: (newState: WebSocketState) => {
      state = newState;
      stateHandlers.forEach(handler => handler(state));
    },
    __triggerError: (error: any) => {
      errorHandlers.forEach(handler => handler(error));
    }
  };
}

/**
 * Test scenario helpers
 */
export class PusherTestScenarios {
  constructor(private service: ReturnType<typeof createMockPusherService>) {}

  /**
   * Simulate successful connection flow
   */
  async simulateConnection(token?: string): Promise<void> {
    await this.service.connect(token);
  }

  /**
   * Simulate connection failure
   */
  async simulateConnectionFailure(error: any): Promise<void> {
    this.service.connect.mockRejectedValueOnce(error);
    try {
      await this.service.connect();
    } catch (e) {
      // Expected to fail
    }
  }

  /**
   * Simulate network disconnection
   */
  simulateNetworkDisconnection(): void {
    this.service.__setState(WebSocketState.DISCONNECTED);
    this.service.__simulator.disconnect();
  }

  /**
   * Simulate authentication error
   */
  simulateAuthError(): void {
    const error = {
      code: 'AUTH_ERROR',
      message: 'Authentication failed',
      timestamp: new Date().toISOString(),
      recoverable: false
    };
    this.service.__triggerError(error);
  }

  /**
   * Simulate message flow
   */
  simulateMessageFlow(channelName: string, messages: any[]): void {
    messages.forEach((message, index) => {
      setTimeout(() => {
        this.service.__simulator.messageReceived(
          channelName,
          message.type || WebSocketMessageType.MESSAGE,
          message.payload
        );
      }, index * 100);
    });
  }

  /**
   * Simulate presence scenario
   */
  simulatePresenceScenario(channelName: string): void {
    // Subscription succeeded
    this.service.__simulator.subscriptionSucceeded(channelName, {
      presence: {
        count: 1,
        ids: ['user-1'],
        hash: { 'user-1': { name: 'Test User' } }
      }
    });

    // Member added
    setTimeout(() => {
      this.service.__simulator.memberAdded(channelName, {
        id: 'user-2',
        info: { name: 'Another User' }
      });
    }, 100);

    // Member removed
    setTimeout(() => {
      this.service.__simulator.memberRemoved(channelName, {
        id: 'user-1',
        info: { name: 'Test User' }
      });
    }, 200);
  }
}

/**
 * Assertion helpers for testing
 */
export const pusherAssertions = {
  /**
   * Assert that a channel is subscribed
   */
  toBeSubscribed(service: any, channelName: string): void {
    const isSubscribed = service.__subscriptions.has(channelName);
    expect(isSubscribed).toBe(true);
  },

  /**
   * Assert that a channel is not subscribed
   */
  toNotBeSubscribed(service: any, channelName: string): void {
    const isSubscribed = service.__subscriptions.has(channelName);
    expect(isSubscribed).toBe(false);
  },

  /**
   * Assert connection state
   */
  toBeInState(service: any, expectedState: WebSocketState): void {
    expect(service.getState()).toBe(expectedState);
  },

  /**
   * Assert that an event was handled
   */
  toHaveHandledEvent(mockHandler: any, expectedData?: any): void {
    expect(mockHandler).toHaveBeenCalled();
    if (expectedData) {
      expect(mockHandler).toHaveBeenCalledWith(expectedData);
    }
  }
};

/**
 * Default mock configuration
 */
export const defaultMockConfig = {
  autoConnect: false,
  defaultChannels: ['dashboard-updates', 'system-notifications'],
  simulateLatency: false,
  latencyMs: 100
};

/**
 * Factory for creating test instances
 */
export function createPusherTestEnvironment(config = defaultMockConfig) {
  const service = createMockPusherService();
  const scenarios = new PusherTestScenarios(service);

  return {
    service,
    scenarios,
    simulator: service.__simulator,
    client: service.__client,
    assertions: pusherAssertions
  };
}
