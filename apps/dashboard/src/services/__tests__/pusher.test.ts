/**
 * Unit Tests for Pusher Service
 *
 * Tests the core functionality of the PusherService including:
 * - Connection management
 * - Channel subscription/unsubscription
 * - Event handling
 * - Authentication flow
 * - Error handling
 * - Reconnection logic
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { PusherService } from '../pusher';
import { WebSocketState, WebSocketMessageType } from '../../types/websocket';

// Mock Pusher library
const mockPusherInstance = {
  connection: {
    bind: vi.fn(),
    unbind: vi.fn(),
    state: 'connected'
  },
  subscribe: vi.fn(),
  unsubscribe: vi.fn(),
  bind: vi.fn(),
  unbind: vi.fn(),
  unbind_all: vi.fn(),
  disconnect: vi.fn(),
  channel: vi.fn(),
  config: {
    auth: {
      headers: {}
    }
  }
};

const mockChannel = {
  bind: vi.fn(),
  unbind: vi.fn(),
  trigger: vi.fn(),
  unsubscribe: vi.fn()
};

vi.mock('pusher-js', () => ({
  default: vi.fn().mockImplementation(() => mockPusherInstance)
}));

// Mock config
vi.mock('../../config', () => ({
  WS_URL: 'ws://localhost:8009',
  PUSHER_KEY: 'test-pusher-key',
  PUSHER_CLUSTER: 'us2',
  PUSHER_AUTH_ENDPOINT: '/pusher/auth',
  AUTH_TOKEN_KEY: 'auth_token',
  AUTH_REFRESH_TOKEN_KEY: 'refresh_token',
  WS_CONFIG: {
    reconnectInterval: 1000,
    maxReconnectAttempts: 5,
    heartbeatInterval: 30000
  }
}));

// Mock API client
const mockApiClient = {
  realtimeTrigger: vi.fn(),
  refreshToken: vi.fn()
};

vi.mock('../api', () => ({
  default: vi.fn().mockImplementation(() => mockApiClient)
}));

// Mock logger
vi.mock('../../utils/logger', () => ({
  logger: {
    debug: vi.fn(),
    error: vi.fn(),
    warn: vi.fn(),
    info: vi.fn()
  }
}));

// Mock token refresh manager
vi.mock('../../utils/tokenRefreshManager', () => ({
  tokenRefreshManager: {
    addListener: vi.fn()
  }
}));

describe('PusherService', () => {
  let pusherService: PusherService;

  beforeEach(() => {
    // Clear singleton instance
    (PusherService as any).instance = null;

    // Reset all mocks
    vi.clearAllMocks();

    // Reset localStorage
    localStorage.clear();

    // Reset mock implementations
    mockPusherInstance.subscribe.mockReturnValue(mockChannel);
    mockPusherInstance.channel.mockReturnValue(mockChannel);
    mockApiClient.realtimeTrigger.mockResolvedValue({ ok: true });
    mockApiClient.refreshToken.mockResolvedValue({
      accessToken: 'new-token',
      refreshToken: 'new-refresh-token'
    });

    pusherService = new PusherService({
      url: 'ws://localhost:8009',
      debug: true
    });
  });

  afterEach(() => {
    pusherService?.disconnect();
    vi.clearAllTimers();
  });

  describe('Singleton Pattern', () => {
    it('should return the same instance', () => {
      const instance1 = PusherService.getInstance();
      const instance2 = PusherService.getInstance();
      expect(instance1).toBe(instance2);
    });

    it('should create new instance with options', () => {
      const instance = PusherService.getInstance({ debug: true });
      expect(instance).toBeInstanceOf(PusherService);
    });
  });

  describe('Connection Management', () => {
    it('should connect successfully with token', async () => {
      localStorage.setItem('auth_token', 'test-token');

      await pusherService.connect();

      expect(pusherService.getState()).toBe(WebSocketState.CONNECTING);

      // Simulate connection success
      const connectCallback = mockPusherInstance.connection.bind.mock.calls
        .find(call => call[0] === 'connected')?.[1];
      connectCallback();

      expect(pusherService.getState()).toBe(WebSocketState.CONNECTED);
    });

    it('should connect with provided token', async () => {
      const testToken = 'provided-token';

      await pusherService.connect(testToken);

      expect(pusherService.getState()).toBe(WebSocketState.CONNECTING);
    });

    it('should handle connection without token in development', async () => {
      // Mock development environment
      vi.stubGlobal('import.meta', { env: { MODE: 'development' } });

      await pusherService.connect();

      expect(pusherService.getState()).toBe(WebSocketState.CONNECTING);
    });

    it('should reject connection without token in production', async () => {
      vi.stubGlobal('import.meta', { env: { MODE: 'production' } });

      await expect(pusherService.connect()).rejects.toThrow('Authentication token required');
    });

    it('should skip connection when Pusher not configured', async () => {
      // Create service with dummy key
      const serviceWithDummyKey = new PusherService();
      vi.doMock('../../config', () => ({
        PUSHER_KEY: 'dummy-key-for-development'
      }));

      await serviceWithDummyKey.connect();

      expect(serviceWithDummyKey.getState()).toBe(WebSocketState.DISCONNECTED);
    });

    it('should disconnect properly', () => {
      pusherService.disconnect('Test disconnect');

      expect(pusherService.getState()).toBe(WebSocketState.DISCONNECTED);
      expect(mockPusherInstance.disconnect).toHaveBeenCalled();
    });

    it('should handle already connected state', async () => {
      // Manually set state to connected
      (pusherService as any).state = WebSocketState.CONNECTED;

      await pusherService.connect();

      expect(pusherService.getState()).toBe(WebSocketState.CONNECTED);
    });
  });

  describe('Channel Subscription', () => {
    beforeEach(() => {
      // Setup connected state
      (pusherService as any).state = WebSocketState.CONNECTED;
      (pusherService as any).pusher = mockPusherInstance;
    });

    it('should subscribe to channel', () => {
      const handler = vi.fn();
      const subscriptionId = pusherService.subscribe('test-channel', handler);

      expect(subscriptionId).toMatch(/^sub_\d+_/);
      expect(mockPusherInstance.subscribe).toHaveBeenCalledWith('test-channel');
      expect(mockChannel.bind).toHaveBeenCalledWith('message', expect.any(Function));
    });

    it('should handle existing channel subscription', () => {
      mockPusherInstance.channel.mockReturnValue(mockChannel);

      const handler = vi.fn();
      pusherService.subscribe('existing-channel', handler);

      expect(mockPusherInstance.channel).toHaveBeenCalledWith('existing-channel');
      expect(mockPusherInstance.subscribe).not.toHaveBeenCalled();
    });

    it('should unsubscribe from channel', () => {
      const handler = vi.fn();
      const subscriptionId = pusherService.subscribe('test-channel', handler);

      pusherService.unsubscribe(subscriptionId);

      expect(mockChannel.unbind).toHaveBeenCalledWith('message');
      expect(mockPusherInstance.unsubscribe).toHaveBeenCalledWith('test-channel');
    });

    it('should handle multiple subscriptions to same channel', () => {
      const handler1 = vi.fn();
      const handler2 = vi.fn();

      const sub1 = pusherService.subscribe('shared-channel', handler1);
      const sub2 = pusherService.subscribe('shared-channel', handler2);

      // Should only subscribe to Pusher once
      expect(mockPusherInstance.subscribe).toHaveBeenCalledTimes(1);

      // Unsubscribe first handler
      pusherService.unsubscribe(sub1);

      // Should not unsubscribe from Pusher yet
      expect(mockPusherInstance.unsubscribe).not.toHaveBeenCalled();

      // Unsubscribe second handler
      pusherService.unsubscribe(sub2);

      // Now should unsubscribe from Pusher
      expect(mockPusherInstance.unsubscribe).toHaveBeenCalledWith('shared-channel');
    });

    it('should sanitize channel names', () => {
      const handler = vi.fn();
      pusherService.subscribe('test-channel$%^&*()', handler);

      expect(mockPusherInstance.subscribe).toHaveBeenCalledWith('test-channel');
    });
  });

  describe('Message Handling', () => {
    beforeEach(() => {
      (pusherService as any).state = WebSocketState.CONNECTED;
      (pusherService as any).pusher = mockPusherInstance;
    });

    it('should send message through API', async () => {
      mockApiClient.realtimeTrigger.mockResolvedValue({ ok: true });

      await pusherService.send(WebSocketMessageType.MESSAGE, { test: 'data' }, {
        channel: 'test-channel'
      });

      expect(mockApiClient.realtimeTrigger).toHaveBeenCalledWith({
        channel: 'test-channel',
        event: 'message',
        type: WebSocketMessageType.MESSAGE,
        payload: { test: 'data' }
      });
    });

    it('should queue messages when not connected', async () => {
      (pusherService as any).state = WebSocketState.DISCONNECTED;

      const sendPromise = pusherService.send(WebSocketMessageType.MESSAGE, { test: 'data' });

      // Message should be queued
      expect((pusherService as any).messageQueue).toHaveLength(1);

      // Connect and flush queue
      (pusherService as any).state = WebSocketState.CONNECTED;
      await (pusherService as any).flushMessageQueue();

      expect(mockApiClient.realtimeTrigger).toHaveBeenCalled();
    });

    it('should handle send errors', async () => {
      mockApiClient.realtimeTrigger.mockRejectedValue(new Error('Send failed'));

      await expect(
        pusherService.send(WebSocketMessageType.MESSAGE, { test: 'data' })
      ).rejects.toThrow('Send failed');
    });

    it('should handle message acknowledgment', async () => {
      mockApiClient.realtimeTrigger.mockResolvedValue({
        ok: true,
        messageId: 'test-msg-id'
      });

      const result = await pusherService.send(
        WebSocketMessageType.MESSAGE,
        { test: 'data' },
        { awaitAcknowledgment: true }
      );

      expect(result).toEqual(
        expect.objectContaining({ ok: true, messageId: 'test-msg-id' })
      );
    });

    it('should handle message timeout', async () => {
      vi.useFakeTimers();

      mockApiClient.realtimeTrigger.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      const sendPromise = pusherService.send(
        WebSocketMessageType.MESSAGE,
        { test: 'data' },
        { awaitAcknowledgment: true, timeout: 1000 }
      );

      vi.advanceTimersByTime(1000);

      await expect(sendPromise).rejects.toThrow('Message timeout after 1000ms');

      vi.useRealTimers();
    });
  });

  describe('Event Handlers', () => {
    it('should register message type handler', () => {
      const handler = vi.fn();
      pusherService.on(WebSocketMessageType.MESSAGE, handler);

      expect((pusherService as any).messageHandlers.has(WebSocketMessageType.MESSAGE)).toBe(true);
    });

    it('should remove message type handler', () => {
      const handler = vi.fn();
      pusherService.on(WebSocketMessageType.MESSAGE, handler);
      pusherService.off(WebSocketMessageType.MESSAGE, handler);

      const handlers = (pusherService as any).messageHandlers.get(WebSocketMessageType.MESSAGE);
      expect(handlers?.has(handler)).toBe(false);
    });

    it('should register state change handler', () => {
      const handler = vi.fn();
      const unsubscribe = pusherService.onStateChange(handler);

      expect(typeof unsubscribe).toBe('function');
      expect((pusherService as any).stateHandlers.has(handler)).toBe(true);

      unsubscribe();
      expect((pusherService as any).stateHandlers.has(handler)).toBe(false);
    });

    it('should register error handler', () => {
      const handler = vi.fn();
      const unsubscribe = pusherService.onError(handler);

      expect(typeof unsubscribe).toBe('function');
      expect((pusherService as any).errorHandlers.has(handler)).toBe(true);

      unsubscribe();
      expect((pusherService as any).errorHandlers.has(handler)).toBe(false);
    });
  });

  describe('Authentication', () => {
    it('should handle token refresh', async () => {
      localStorage.setItem('refresh_token', 'test-refresh-token');

      const newToken = await (pusherService as any).refreshTokenWithAPI();

      expect(newToken).toBe('new-token');
      expect(localStorage.getItem('auth_token')).toBe('new-token');
      expect(localStorage.getItem('refresh_token')).toBe('new-refresh-token');
    });

    it('should handle token refresh failure', async () => {
      mockApiClient.refreshToken.mockRejectedValue(new Error('Refresh failed'));

      const newToken = await (pusherService as any).refreshTokenWithAPI();

      expect(newToken).toBe(null);
    });

    it('should schedule token refresh', () => {
      vi.useFakeTimers();

      // Create a valid JWT token (expires in 1 hour)
      const payload = { exp: Math.floor(Date.now() / 1000) + 3600 };
      const token = `header.${btoa(JSON.stringify(payload))}.signature`;

      (pusherService as any).scheduleTokenRefresh(token);

      expect((pusherService as any).tokenRefreshTimer).toBeTruthy();

      vi.useRealTimers();
    });

    it('should handle invalid JWT token', () => {
      const invalidToken = 'invalid.token';

      (pusherService as any).scheduleTokenRefresh(invalidToken);

      // Should set default expiry time
      expect((pusherService as any).tokenExpiryTime).toBeTruthy();
    });

    it('should skip refresh for dev tokens', () => {
      const devToken = 'dev-token-123456';

      (pusherService as any).scheduleTokenRefresh(devToken);

      expect((pusherService as any).tokenRefreshTimer).toBe(null);
    });
  });

  describe('Reconnection Logic', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('should attempt reconnection on disconnect', () => {
      (pusherService as any).state = WebSocketState.CONNECTED;
      (pusherService as any).options.reconnect = true;
      (pusherService as any).options.maxReconnectAttempts = 3;

      (pusherService as any).handleDisconnect('connection lost');

      expect((pusherService as any).state).toBe(WebSocketState.RECONNECTING);
      expect((pusherService as any).reconnectTimer).toBeTruthy();
    });

    it('should use exponential backoff for reconnection', () => {
      (pusherService as any).state = WebSocketState.CONNECTED;
      (pusherService as any).options.reconnect = true;
      (pusherService as any).reconnectAttempts = 2;

      const connectSpy = vi.spyOn(pusherService, 'connect').mockResolvedValue();

      (pusherService as any).reconnect();

      // Should calculate exponential delay (base 1000ms * 2^2 = 4000ms + jitter)
      expect((pusherService as any).reconnectTimer).toBeTruthy();

      vi.advanceTimersByTime(5000); // Account for jitter

      expect(connectSpy).toHaveBeenCalled();
    });

    it('should stop reconnecting after max attempts', () => {
      (pusherService as any).state = WebSocketState.CONNECTED;
      (pusherService as any).options.reconnect = true;
      (pusherService as any).options.maxReconnectAttempts = 3;
      (pusherService as any).reconnectAttempts = 3;

      const connectSpy = vi.spyOn(pusherService, 'connect').mockRejectedValue(new Error('Failed'));

      (pusherService as any).reconnect();

      vi.advanceTimersByTime(10000);

      expect((pusherService as any).state).toBe(WebSocketState.ERROR);
    });

    it('should not reconnect on auth errors', () => {
      (pusherService as any).state = WebSocketState.CONNECTED;
      (pusherService as any).options.reconnect = true;

      (pusherService as any).handleDisconnect('unauthorized');

      expect((pusherService as any).reconnectTimer).toBe(null);
    });
  });

  describe('Error Handling', () => {
    it('should handle connection errors', () => {
      const errorHandler = vi.fn();
      pusherService.onError(errorHandler);

      const error = {
        code: 'CONNECTION_FAILED',
        message: 'Connection failed',
        timestamp: new Date().toISOString(),
        recoverable: true
      };

      (pusherService as any).handleError(error);

      expect(errorHandler).toHaveBeenCalledWith(error);
    });

    it('should attempt recovery on recoverable errors', () => {
      (pusherService as any).options.reconnect = true;
      const reconnectSpy = vi.spyOn(pusherService as any, 'reconnect');

      const error = {
        code: 'RECOVERABLE_ERROR',
        message: 'Recoverable error',
        timestamp: new Date().toISOString(),
        recoverable: true
      };

      (pusherService as any).handleError(error);

      expect(reconnectSpy).toHaveBeenCalled();
    });
  });

  describe('Statistics', () => {
    it('should track connection statistics', () => {
      const stats = pusherService.getStats();

      expect(stats).toEqual(
        expect.objectContaining({
          connectionState: WebSocketState.DISCONNECTED,
          messagesSent: 0,
          messagesReceived: 0,
          reconnectAttempts: 0,
          bytesReceived: 0,
          bytesSent: 0
        })
      );
    });

    it('should update stats on message send', async () => {
      (pusherService as any).state = WebSocketState.CONNECTED;
      mockApiClient.realtimeTrigger.mockResolvedValue({ ok: true });

      await pusherService.send(WebSocketMessageType.MESSAGE, { test: 'data' });

      const stats = pusherService.getStats();
      expect(stats.messagesSent).toBe(1);
      expect(stats.bytesSent).toBeGreaterThan(0);
    });

    it('should update stats on message receive', () => {
      const message = {
        type: WebSocketMessageType.MESSAGE,
        payload: { test: 'data' },
        timestamp: new Date().toISOString(),
        messageId: 'test-msg-id'
      };

      (pusherService as any).handleMessage(message);

      const stats = pusherService.getStats();
      expect(stats.messagesReceived).toBe(1);
      expect(stats.bytesReceived).toBeGreaterThan(0);
    });
  });

  describe('Utility Methods', () => {
    it('should check connection status', () => {
      expect(pusherService.isConnected()).toBe(false);

      (pusherService as any).state = WebSocketState.CONNECTED;
      expect(pusherService.isConnected()).toBe(true);
    });

    it('should get current state', () => {
      expect(pusherService.getState()).toBe(WebSocketState.DISCONNECTED);
    });

    it('should generate unique IDs', () => {
      const id1 = (pusherService as any).generateMessageId();
      const id2 = (pusherService as any).generateMessageId();

      expect(id1).toMatch(/^msg_\d+_/);
      expect(id2).toMatch(/^msg_\d+_/);
      expect(id1).not.toBe(id2);
    });
  });

  describe('Message Queue', () => {
    it('should flush queued messages on connection', async () => {
      (pusherService as any).state = WebSocketState.DISCONNECTED;

      // Queue a message
      pusherService.send(WebSocketMessageType.MESSAGE, { test: 'data' });
      expect((pusherService as any).messageQueue).toHaveLength(1);

      // Connect and flush
      (pusherService as any).state = WebSocketState.CONNECTED;
      await (pusherService as any).flushMessageQueue();

      expect((pusherService as any).messageQueue).toHaveLength(0);
      expect(mockApiClient.realtimeTrigger).toHaveBeenCalled();
    });

    it('should retry failed messages', async () => {
      (pusherService as any).state = WebSocketState.DISCONNECTED;

      // Queue a message
      pusherService.send(WebSocketMessageType.MESSAGE, { test: 'data' });

      // Simulate failure on first attempt
      mockApiClient.realtimeTrigger
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValue({ ok: true });

      (pusherService as any).state = WebSocketState.CONNECTED;
      await (pusherService as any).flushMessageQueue();

      // Message should be retried
      expect((pusherService as any).messageQueue).toHaveLength(1);

      // Flush again (should succeed)
      await (pusherService as any).flushMessageQueue();
      expect((pusherService as any).messageQueue).toHaveLength(0);
    });
  });
});