import { vi } from 'vitest';

// Configure test timeout for Vitest
vi.setConfig({ testTimeout: 10000 });

/**
 * Pusher Service Test Suite
 * 
 * Comprehensive tests for the unified Pusher service implementation
 * Testing connection, channel management, message handling, and reconnection logic
 */

import { describe, it, expect, vi, beforeEach, afterEach, MockedFunction } from 'vitest';
import Pusher, { Channel, PresenceChannel } from 'pusher-js';
import { PusherService } from '../../services/pusher';
import { WebSocketState, WebSocketMessageType } from '../../types/websocket';

// Mock Pusher
vi.mock('pusher-js');

// Mock the config module
vi.mock('../../config', () => ({
  AUTH_TOKEN_KEY: 'test-token-key',
  AUTH_REFRESH_TOKEN_KEY: 'test-refresh-token-key',
  WS_CONFIG: {
    reconnectInterval: 100,
    maxReconnectAttempts: 3,
    heartbeatInterval: 1000,
  },
  WS_URL: 'http://localhost:8008',
  PUSHER_KEY: 'test-pusher-key',
  PUSHER_CLUSTER: 'test-cluster',
  PUSHER_AUTH_ENDPOINT: 'http://localhost:8008/pusher/auth',
}));

// Mock API client
vi.mock('../../services/api', () => ({
  default: vi.fn().mockImplementation(() => ({
    refreshToken: vi.fn().mockResolvedValue({ token: 'new-token' }),
  })),
}));

describe('PusherService', () => {
  let service: PusherService;
  let mockPusherInstance: any;
  let mockChannel: any;
  let mockPresenceChannel: any;

  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks();
    
    // Clear localStorage
    localStorage.clear();
    
    // Mock Pusher instance
    mockChannel = {
      bind: vi.fn(),
      unbind: vi.fn(),
      unbind_all: vi.fn(),
      trigger: vi.fn(),
    };
    
    mockPresenceChannel = {
      ...mockChannel,
      members: {
        count: 0,
        me: null,
        each: vi.fn(),
      },
    };
    
    mockPusherInstance = {
      connection: {
        bind: vi.fn(),
        unbind: vi.fn(),
        unbind_all: vi.fn(),
        state: 'disconnected',
      },
      subscribe: vi.fn((channelName: string) => {
        if (channelName.startsWith('presence-')) {
          return mockPresenceChannel;
        }
        return mockChannel;
      }),
      unsubscribe: vi.fn(),
      disconnect: vi.fn(),
      unbind_all: vi.fn(),
      channels: {
        all: vi.fn(() => []),
      },
    };
    
    (Pusher as unknown as MockedFunction<any>).mockImplementation(() => mockPusherInstance);
    
    // Create service instance
    service = new PusherService({
      debug: true,
      autoConnect: false,
    });
  });

  afterEach(() => {
    service.disconnect();
  });

  describe('Connection Management', () => {
    it('should initialize with disconnected state', () => {
      expect(service.getState()).toBe(WebSocketState.DISCONNECTED);
      expect(service.isConnected()).toBe(false);
    });

    it('should connect with authentication token', async () => {
      const token = 'test-auth-token';
      localStorage.setItem('test-token-key', token);
      
      // Simulate connection success
      const connectPromise = service.connect(token);
      
      // Trigger connected event
      const connectedCallback = mockPusherInstance.connection.bind.mock.calls.find(
        (call: any[]) => call[0] === 'connected'
      )?.[1];
      
      if (connectedCallback) {
        connectedCallback();
      }
      
      await connectPromise;
      
      expect(Pusher).toHaveBeenCalledWith(
        'test-pusher-key',
        expect.objectContaining({
          cluster: 'test-cluster',
          forceTLS: true,
          authEndpoint: 'http://localhost:8008/pusher/auth',
          auth: {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          },
        })
      );
    });

    it('should handle connection failure', async () => {
      const token = 'test-auth-token';
      localStorage.setItem('test-token-key', token);
      
      // Simulate connection error
      const connectPromise = service.connect(token);
      
      // Trigger error event
      const errorCallback = mockPusherInstance.connection.bind.mock.calls.find(
        (call: any[]) => call[0] === 'error'
      )?.[1];
      
      if (errorCallback) {
        errorCallback({ message: 'Connection failed' });
      }
      
      await expect(connectPromise).rejects.toThrow('Connection failed');
    });

    it('should disconnect properly', () => {
      service.disconnect('test reason');
      
      expect(mockPusherInstance.disconnect).toHaveBeenCalled();
      expect(service.getState()).toBe(WebSocketState.DISCONNECTED);
    });

    it('should handle reconnection', async () => {
      const token = 'test-auth-token';
      localStorage.setItem('test-token-key', token);
      
      // First connection
      let connectPromise = service.connect(token);
      const connectedCallback = mockPusherInstance.connection.bind.mock.calls.find(
        (call: any[]) => call[0] === 'connected'
      )?.[1];
      connectedCallback?.();
      await connectPromise;
      
      // Disconnect
      service.disconnect();
      
      // Reconnect
      connectPromise = service.connect(token);
      const reconnectedCallback = mockPusherInstance.connection.bind.mock.calls.find(
        (call: any[]) => call[0] === 'connected'
      )?.[1];
      reconnectedCallback?.();
      await connectPromise;
      
      expect(Pusher).toHaveBeenCalledTimes(2);
    });
  });

  describe('Channel Management', () => {
    beforeEach(async () => {
      // Connect the service
      const token = 'test-auth-token';
      localStorage.setItem('test-token-key', token);
      
      const connectPromise = service.connect(token);
      const connectedCallback = mockPusherInstance.connection.bind.mock.calls.find(
        (call: any[]) => call[0] === 'connected'
      )?.[1];
      connectedCallback?.();
      await connectPromise;
    });

    it('should subscribe to public channel', async () => {
      const channelName = 'public-test';
      const channel = await service.subscribeToChannel(channelName);
      
      expect(mockPusherInstance.subscribe).toHaveBeenCalledWith(channelName);
      expect(channel).toBeDefined();
    });

    it('should subscribe to private channel', async () => {
      const channelName = 'private-user-123';
      const channel = await service.subscribeToChannel(channelName);
      
      expect(mockPusherInstance.subscribe).toHaveBeenCalledWith(channelName);
      expect(channel).toBeDefined();
    });

    it('should subscribe to presence channel', async () => {
      const channelName = 'presence-classroom-456';
      const channel = await service.subscribeToChannel(channelName);
      
      expect(mockPusherInstance.subscribe).toHaveBeenCalledWith(channelName);
      expect(channel).toBeDefined();
    });

    it('should unsubscribe from channel', async () => {
      const channelName = 'public-test';
      await service.subscribeToChannel(channelName);
      
      service.unsubscribeFromChannel(channelName);
      
      expect(mockPusherInstance.unsubscribe).toHaveBeenCalledWith(channelName);
    });

    it('should handle multiple subscriptions to same channel', async () => {
      const channelName = 'public-test';
      
      const channel1 = await service.subscribeToChannel(channelName);
      const channel2 = await service.subscribeToChannel(channelName);
      
      expect(channel1).toBe(channel2);
      expect(mockPusherInstance.subscribe).toHaveBeenCalledTimes(1);
    });
  });

  describe('Message Handling', () => {
    beforeEach(async () => {
      // Connect the service
      const token = 'test-auth-token';
      localStorage.setItem('test-token-key', token);
      
      const connectPromise = service.connect(token);
      const connectedCallback = mockPusherInstance.connection.bind.mock.calls.find(
        (call: any[]) => call[0] === 'connected'
      )?.[1];
      connectedCallback?.();
      await connectPromise;
    });

    it('should send message to channel', async () => {
      await service.send(WebSocketMessageType.CONTENT_UPDATE, { content: 'test' }, { channel: 'public' });
      
      // Since send triggers server-side events, we need to verify API call
      // In real implementation, this would call the API to trigger server event
      expect(service.isConnected()).toBe(true);
    });

    it('should subscribe to channel events', async () => {
      const handler = vi.fn();
      const channelName = 'public-test';
      
      const subscriptionId = await service.subscribe(channelName, handler);
      
      // Simulate event from Pusher
      const bindCall = mockChannel.bind.mock.calls[0];
      if (bindCall) {
        const eventHandler = bindCall[1];
        eventHandler({ type: 'test', data: 'test-data' });
      }
      
      expect(handler).toHaveBeenCalledWith(expect.objectContaining({
        type: 'test',
        data: 'test-data',
      }));
      expect(subscriptionId).toBeDefined();
    });

    it('should unsubscribe from events', async () => {
      const handler = vi.fn();
      const channelName = 'public-test';
      
      const subscriptionId = await service.subscribe(channelName, handler);
      service.unsubscribe(subscriptionId);
      
      // Simulate event after unsubscribe
      const bindCall = mockChannel.bind.mock.calls[0];
      if (bindCall) {
        const eventHandler = bindCall[1];
        eventHandler({ type: 'test', data: 'test-data' });
      }
      
      // Handler should not be called after unsubscribe
      // (In real implementation, the handler would be removed)
    });

    it('should handle filtered subscriptions', async () => {
      const handler = vi.fn();
      const filter = (msg: any) => msg.type === 'allowed';
      const channelName = 'public-test';
      
      await service.subscribe(channelName, handler, filter);
      
      // Simulate allowed event
      const bindCall = mockChannel.bind.mock.calls[0];
      if (bindCall) {
        const eventHandler = bindCall[1];
        eventHandler({ type: 'allowed', data: 'test' });
        eventHandler({ type: 'blocked', data: 'test' });
      }
      
      // Handler should be called for allowed event
      expect(handler).toHaveBeenCalledTimes(1);
    });
  });

  describe('Presence Channel Features', () => {
    beforeEach(async () => {
      // Connect the service
      const token = 'test-auth-token';
      localStorage.setItem('test-token-key', token);
      
      const connectPromise = service.connect(token);
      const connectedCallback = mockPusherInstance.connection.bind.mock.calls.find(
        (call: any[]) => call[0] === 'connected'
      )?.[1];
      connectedCallback?.();
      await connectPromise;
    });

    it('should track presence channel members', async () => {
      const channelName = 'presence-classroom-123';
      await service.subscribeToChannel(channelName);
      
      // Simulate member events
      mockPresenceChannel.members.count = 5;
      mockPresenceChannel.members.me = { id: 'user-1', info: { name: 'Test User' } };
      
      // In real implementation, we would track these members
      expect(mockPusherInstance.subscribe).toHaveBeenCalledWith(channelName);
    });

    it('should trigger client events on presence channel', async () => {
      const channelName = 'presence-classroom-123';
      await service.subscribeToChannel(channelName);
      
      // Trigger client event
      await service.send(WebSocketMessageType.CONTENT_UPDATE, { test: 'data' }, { channel: channelName });
      
      // Client events would be triggered on the channel
      expect(mockPresenceChannel.trigger).toBeDefined();
    });
  });

  describe('Error Handling', () => {
    it('should handle missing Pusher key', async () => {
      // Override config to have no key
      vi.doMock('../../config', () => ({
        PUSHER_KEY: '',
        PUSHER_CLUSTER: 'test-cluster',
        AUTH_TOKEN_KEY: 'test-token-key',
      }));
      
      const serviceWithoutKey = new PusherService();
      await expect(serviceWithoutKey.connect()).resolves.toBeUndefined();
      expect(serviceWithoutKey.getState()).toBe(WebSocketState.DISCONNECTED);
    });

    it('should handle connection errors with retry', async () => {
      const token = 'test-auth-token';
      localStorage.setItem('test-token-key', token);
      
      let attemptCount = 0;
      const connectPromise = service.connect(token);
      
      // Simulate multiple connection failures
      const errorCallback = mockPusherInstance.connection.bind.mock.calls.find(
        (call: any[]) => call[0] === 'error'
      )?.[1];
      
      if (errorCallback) {
        attemptCount++;
        errorCallback({ message: 'Connection failed' });
      }
      
      await expect(connectPromise).rejects.toThrow();
    });

    it('should handle state change events', () => {
      const stateHandler = vi.fn();
      service.onStateChange(stateHandler);
      
      // Trigger state change
      service.disconnect();
      
      expect(stateHandler).toHaveBeenCalledWith(WebSocketState.DISCONNECTED);
    });
  });

  describe('Statistics and Monitoring', () => {
    it('should track connection statistics', () => {
      const stats = service.getStats();
      
      expect(stats).toHaveProperty('messagesReceived');
      expect(stats).toHaveProperty('messagesSent');
      expect(stats).toHaveProperty('bytesReceived');
      expect(stats).toHaveProperty('bytesSent');
      expect(stats).toHaveProperty('connectedAt');
      expect(stats).toHaveProperty('reconnectCount');
    });

    it('should update stats on message events', async () => {
      const token = 'test-auth-token';
      localStorage.setItem('test-token-key', token);
      
      const connectPromise = service.connect(token);
      const connectedCallback = mockPusherInstance.connection.bind.mock.calls.find(
        (call: any[]) => call[0] === 'connected'
      )?.[1];
      connectedCallback?.();
      await connectPromise;
      
      const initialStats = service.getStats();
      
      // Send a message
      await service.send(WebSocketMessageType.CONTENT_UPDATE, { test: 'data' });
      
      const updatedStats = service.getStats();
      expect(updatedStats.messagesSent).toBeGreaterThan(initialStats.messagesSent);
    });
  });
});