/**
 * Unit Tests for Enhanced Pusher Hooks
 *
 * Tests the React hooks that provide Pusher functionality:
 * - usePusher hook for service access with enhanced features
 * - usePusherChannel hook for channel subscription
 * - usePusherConnection hook for connection monitoring
 * - usePusherPresence hook for presence channels
 * - usePusherEvent hook for event listening
 * - usePusherSend hook for sending messages
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, cleanup } from '@testing-library/react';
import {
  usePusher,
  usePusherChannel,
  usePusherConnection,
  usePusherPresence,
  usePusherEvent,
  usePusherSend
} from '../usePusher';
import { WebSocketState } from '../../types/websocket';
import { PusherChannelType } from '../../types/pusher';

// Mock the pusher service
const mockPusherService = {
  connect: vi.fn(),
  disconnect: vi.fn(),
  subscribe: vi.fn(),
  unsubscribe: vi.fn(),
  getState: vi.fn(),
  onStateChange: vi.fn(),
  onError: vi.fn(),
  send: vi.fn(),
  on: vi.fn(),
  off: vi.fn(),
  isConnected: vi.fn(),
  getStats: vi.fn()
};

vi.mock('../services/pusher', () => ({
  pusherService: mockPusherService,
  PusherService: vi.fn().mockImplementation(() => mockPusherService)
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

describe('Enhanced Pusher Hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPusherService.getState.mockReturnValue(WebSocketState.DISCONNECTED);
    mockPusherService.subscribe.mockReturnValue('subscription-id');
    mockPusherService.onStateChange.mockReturnValue(() => {});
    mockPusherService.onError.mockReturnValue(() => {});
    mockPusherService.connect.mockResolvedValue(undefined);
    mockPusherService.send.mockResolvedValue(undefined);
    mockPusherService.getStats.mockReturnValue({
      connectionState: WebSocketState.DISCONNECTED,
      messagesSent: 0,
      messagesReceived: 0,
      reconnectAttempts: 0,
      bytesReceived: 0,
      bytesSent: 0
    });
  });

  afterEach(() => {
    cleanup();
  });

  describe('usePusher', () => {
    it('should return enhanced pusher state object', () => {
      mockPusherService.getState.mockReturnValue(WebSocketState.CONNECTED);

      const { result } = renderHook(() => usePusher());

      expect(result.current).toEqual({
        service: mockPusherService,
        isConnected: true,
        isConnecting: false,
        isReconnecting: false,
        state: WebSocketState.CONNECTED,
        isReady: true
      });
    });

    it('should connect when service is disconnected and autoConnect is true', () => {
      mockPusherService.getState.mockReturnValue(WebSocketState.DISCONNECTED);

      renderHook(() => usePusher({ autoConnect: true }));

      expect(mockPusherService.connect).toHaveBeenCalled();
    });

    it('should not connect when autoConnect is false', () => {
      mockPusherService.getState.mockReturnValue(WebSocketState.DISCONNECTED);

      renderHook(() => usePusher({ autoConnect: false }));

      expect(mockPusherService.connect).not.toHaveBeenCalled();
    });

    it('should update state when connection changes', () => {
      let stateChangeListener: (state: WebSocketState) => void;
      mockPusherService.onStateChange.mockImplementation((listener) => {
        stateChangeListener = listener;
        return () => {};
      });

      const { result } = renderHook(() => usePusher());

      act(() => {
        stateChangeListener(WebSocketState.CONNECTED);
      });

      expect(result.current.isConnected).toBe(true);
      expect(result.current.isReady).toBe(true);
    });

    it('should handle window focus reconnection', () => {
      mockPusherService.getState.mockReturnValue(WebSocketState.DISCONNECTED);

      renderHook(() => usePusher({ reconnectOnFocus: true }));

      // Clear the initial connect call
      mockPusherService.connect.mockClear();

      // Simulate window focus
      act(() => {
        window.dispatchEvent(new Event('focus'));
      });

      expect(mockPusherService.connect).toHaveBeenCalled();
    });

    it('should not reconnect on focus when disabled', () => {
      mockPusherService.getState.mockReturnValue(WebSocketState.DISCONNECTED);

      renderHook(() => usePusher({ reconnectOnFocus: false }));

      mockPusherService.connect.mockClear();

      act(() => {
        window.dispatchEvent(new Event('focus'));
      });

      expect(mockPusherService.connect).not.toHaveBeenCalled();
    });
  });

  describe('usePusherChannel', () => {
    const mockEventHandlers = {
      'message': vi.fn(),
      'update': vi.fn(),
      'error': vi.fn()
    };

    beforeEach(() => {
      Object.values(mockEventHandlers).forEach(handler => handler.mockClear());
      mockPusherService.getState.mockReturnValue(WebSocketState.CONNECTED);
    });

    it('should return enhanced channel state', () => {
      const { result } = renderHook(() =>
        usePusherChannel('test-channel', mockEventHandlers)
      );

      expect(result.current).toEqual({
        isSubscribed: true,
        subscriptionError: null,
        channelName: 'test-channel',
        subscribe: expect.any(Function),
        unsubscribe: expect.any(Function)
      });
    });

    it('should format channel name based on type', () => {
      const { result } = renderHook(() =>
        usePusherChannel('chat', mockEventHandlers, {
          channelType: PusherChannelType.PRIVATE
        })
      );

      expect(result.current.channelName).toBe('private-chat');
    });

    it('should not subscribe when disabled', () => {
      renderHook(() =>
        usePusherChannel('test-channel', mockEventHandlers, { enabled: false })
      );

      expect(mockPusherService.subscribe).not.toHaveBeenCalled();
    });

    it('should not subscribe when service is not ready', () => {
      mockPusherService.getState.mockReturnValue(WebSocketState.DISCONNECTED);

      renderHook(() =>
        usePusherChannel('test-channel', mockEventHandlers)
      );

      expect(mockPusherService.subscribe).not.toHaveBeenCalled();
    });

    it('should handle manual subscription', () => {
      const { result } = renderHook(() =>
        usePusherChannel('test-channel', mockEventHandlers, { autoSubscribe: false })
      );

      expect(mockPusherService.subscribe).not.toHaveBeenCalled();
      expect(result.current.isSubscribed).toBe(false);

      act(() => {
        result.current.subscribe();
      });

      expect(mockPusherService.subscribe).toHaveBeenCalled();
      expect(result.current.isSubscribed).toBe(true);
    });

    it('should handle manual unsubscription', () => {
      const { result } = renderHook(() =>
        usePusherChannel('test-channel', mockEventHandlers)
      );

      expect(result.current.isSubscribed).toBe(true);

      act(() => {
        result.current.unsubscribe();
      });

      expect(mockPusherService.unsubscribe).toHaveBeenCalled();
      expect(result.current.isSubscribed).toBe(false);
    });

    it('should handle subscription errors', () => {
      mockPusherService.subscribe.mockImplementation(() => {
        throw new Error('Subscription failed');
      });

      const { result } = renderHook(() =>
        usePusherChannel('test-channel', mockEventHandlers)
      );

      expect(result.current.subscriptionError).toBeInstanceOf(Error);
      expect(result.current.isSubscribed).toBe(false);
    });

    it('should handle message with enhanced metadata', () => {
      const messageHandler = vi.fn();
      const eventHandlers = { 'message': messageHandler };

      renderHook(() =>
        usePusherChannel('test-channel', eventHandlers)
      );

      const subscribeCall = mockPusherService.subscribe.mock.calls[0];
      const subscriptionHandler = subscribeCall[1];

      const message = {
        type: 'message',
        payload: { data: 'test' }
      };

      act(() => {
        subscriptionHandler(message);
      });

      expect(messageHandler).toHaveBeenCalledWith(
        { data: 'test' },
        { channel: 'test-channel', event: 'message' }
      );
    });
  });

  describe('usePusherConnection', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('should return enhanced connection status', () => {
      mockPusherService.getState.mockReturnValue(WebSocketState.CONNECTED);

      const { result } = renderHook(() => usePusherConnection());

      expect(result.current).toEqual({
        isConnected: true,
        isConnecting: false,
        isReconnecting: false,
        state: WebSocketState.CONNECTED,
        stats: expect.any(Object),
        lastError: null,
        reconnect: expect.any(Function)
      });
    });

    it('should update stats periodically when connected', () => {
      mockPusherService.getState.mockReturnValue(WebSocketState.CONNECTED);

      renderHook(() => usePusherConnection());

      // Fast-forward time to trigger stats update
      act(() => {
        vi.advanceTimersByTime(5000);
      });

      expect(mockPusherService.getStats).toHaveBeenCalled();
    });

    it('should not update stats when disconnected', () => {
      mockPusherService.getState.mockReturnValue(WebSocketState.DISCONNECTED);

      renderHook(() => usePusherConnection());

      mockPusherService.getStats.mockClear();

      act(() => {
        vi.advanceTimersByTime(5000);
      });

      expect(mockPusherService.getStats).toHaveBeenCalledTimes(1); // Only initial call
    });

    it('should handle error events', () => {
      let errorListener: (error: Error) => void;
      mockPusherService.onError.mockImplementation((listener) => {
        errorListener = listener;
        return () => {};
      });

      const { result } = renderHook(() => usePusherConnection());

      const testError = new Error('Connection error');

      act(() => {
        errorListener(testError);
      });

      expect(result.current.lastError).toBe(testError);
    });

    it('should handle manual reconnection', () => {
      const { result } = renderHook(() => usePusherConnection());

      act(() => {
        result.current.reconnect();
      });

      expect(mockPusherService.disconnect).toHaveBeenCalledWith('Manual reconnection');

      // Advance time to trigger reconnect
      act(() => {
        vi.advanceTimersByTime(100);
      });

      expect(mockPusherService.connect).toHaveBeenCalled();
    });
  });

  describe('usePusherPresence', () => {
    const mockUserInfo = {
      name: 'Test User',
      email: 'test@example.com',
      avatar: 'avatar.png',
      role: 'student'
    };

    beforeEach(() => {
      mockPusherService.getState.mockReturnValue(WebSocketState.CONNECTED);
    });

    it('should return presence channel state', () => {
      const { result } = renderHook(() =>
        usePusherPresence('classroom-1', mockUserInfo)
      );

      expect(result.current).toEqual({
        members: [],
        isJoined: false,
        channelName: 'presence-classroom-1',
        joinChannel: expect.any(Function),
        leaveChannel: expect.any(Function)
      });
    });

    it('should format presence channel name correctly', () => {
      const { result } = renderHook(() =>
        usePusherPresence('classroom-1', mockUserInfo)
      );

      expect(result.current.channelName).toBe('presence-classroom-1');
    });

    it('should handle joining a channel', async () => {
      const { result } = renderHook(() =>
        usePusherPresence('classroom-1', mockUserInfo)
      );

      await act(async () => {
        await result.current.joinChannel();
      });

      expect(result.current.isJoined).toBe(true);
    });

    it('should handle leaving a channel', () => {
      const { result } = renderHook(() =>
        usePusherPresence('classroom-1', mockUserInfo)
      );

      act(() => {
        result.current.leaveChannel();
      });

      expect(result.current.isJoined).toBe(false);
      expect(result.current.members).toEqual([]);
    });

    it('should not join when disabled', async () => {
      const { result } = renderHook(() =>
        usePusherPresence('classroom-1', mockUserInfo, { enabled: false })
      );

      await act(async () => {
        await result.current.joinChannel();
      });

      expect(result.current.isJoined).toBe(false);
    });
  });

  describe('usePusherEvent', () => {
    const mockHandler = vi.fn();

    beforeEach(() => {
      mockHandler.mockClear();
      mockPusherService.getState.mockReturnValue(WebSocketState.CONNECTED);
    });

    it('should subscribe to global events', () => {
      renderHook(() =>
        usePusherEvent('test-event', mockHandler)
      );

      expect(mockPusherService.on).toHaveBeenCalledWith('test-event', expect.any(Function));
    });

    it('should subscribe to channel-specific events', () => {
      renderHook(() =>
        usePusherEvent('test-event', mockHandler, { channel: 'test-channel' })
      );

      expect(mockPusherService.subscribe).toHaveBeenCalledWith('test-channel', expect.any(Function));
    });

    it('should not subscribe when disabled', () => {
      renderHook(() =>
        usePusherEvent('test-event', mockHandler, { enabled: false })
      );

      expect(mockPusherService.on).not.toHaveBeenCalled();
      expect(mockPusherService.subscribe).not.toHaveBeenCalled();
    });

    it('should update handler when it changes', () => {
      let handler = vi.fn();
      const { rerender } = renderHook(() =>
        usePusherEvent('test-event', handler)
      );

      // Change handler
      handler = vi.fn();
      rerender();

      // Should unsubscribe and resubscribe
      expect(mockPusherService.off).toHaveBeenCalled();
      expect(mockPusherService.on).toHaveBeenCalledTimes(2);
    });
  });

  describe('usePusherSend', () => {
    beforeEach(() => {
      mockPusherService.getState.mockReturnValue(WebSocketState.CONNECTED);
    });

    it('should return send functionality', () => {
      const { result } = renderHook(() => usePusherSend());

      expect(result.current).toEqual({
        sendMessage: expect.any(Function),
        isSending: false,
        lastError: null,
        isReady: true
      });
    });

    it('should send messages successfully', async () => {
      const { result } = renderHook(() => usePusherSend());

      await act(async () => {
        await result.current.sendMessage('test-event', { data: 'test' });
      });

      expect(mockPusherService.send).toHaveBeenCalledWith('test-event', { data: 'test' }, undefined);
      expect(result.current.isSending).toBe(false);
      expect(result.current.lastError).toBe(null);
    });

    it('should handle send errors', async () => {
      const testError = new Error('Send failed');
      mockPusherService.send.mockRejectedValue(testError);

      const { result } = renderHook(() => usePusherSend());

      await expect(act(async () => {
        await result.current.sendMessage('test-event', { data: 'test' });
      })).rejects.toThrow('Send failed');

      expect(result.current.lastError).toBe(testError);
    });

    it('should not send when service is not ready', async () => {
      mockPusherService.getState.mockReturnValue(WebSocketState.DISCONNECTED);

      const { result } = renderHook(() => usePusherSend());

      await expect(act(async () => {
        await result.current.sendMessage('test-event', { data: 'test' });
      })).rejects.toThrow('Pusher service is not ready');
    });

    it('should track sending state', async () => {
      let resolveSend: () => void;
      const sendPromise = new Promise<void>(resolve => { resolveSend = resolve; });
      mockPusherService.send.mockReturnValue(sendPromise);

      const { result } = renderHook(() => usePusherSend());

      const messagePromise = act(async () => {
        await result.current.sendMessage('test-event', { data: 'test' });
      });

      expect(result.current.isSending).toBe(true);

      resolveSend!();
      await messagePromise;

      expect(result.current.isSending).toBe(false);
    });
  });

  describe('Hook Integration', () => {
    beforeEach(() => {
      mockPusherService.getState.mockReturnValue(WebSocketState.CONNECTED);
    });

    it('should work together in a component', () => {
      const TestComponent = () => {
        const pusher = usePusher();
        const connection = usePusherConnection();
        const channel = usePusherChannel('test-channel', { 'message': vi.fn() });
        const send = usePusherSend();

        return { pusher, connection, channel, send };
      };

      const { result } = renderHook(() => TestComponent());

      expect(result.current.pusher.service).toBe(mockPusherService);
      expect(result.current.connection.isConnected).toBe(true);
      expect(result.current.channel.isSubscribed).toBe(true);
      expect(result.current.send.isReady).toBe(true);
    });

    it('should handle service failures gracefully', () => {
      mockPusherService.subscribe.mockImplementation(() => {
        throw new Error('Subscription failed');
      });

      expect(() => {
        renderHook(() =>
          usePusherChannel('test-channel', { 'message': vi.fn() })
        );
      }).not.toThrow();
    });

    it('should coordinate state between hooks', () => {
      let stateChangeListener: (state: WebSocketState) => void;
      mockPusherService.onStateChange.mockImplementation((listener) => {
        stateChangeListener = listener;
        return () => {};
      });

      const { result } = renderHook(() => ({
        pusher: usePusher(),
        connection: usePusherConnection(),
        send: usePusherSend()
      }));

      // Initially connected
      expect(result.current.pusher.isConnected).toBe(true);
      expect(result.current.connection.isConnected).toBe(true);
      expect(result.current.send.isReady).toBe(true);

      // Simulate disconnection
      act(() => {
        stateChangeListener(WebSocketState.DISCONNECTED);
      });

      expect(result.current.pusher.isConnected).toBe(false);
      expect(result.current.connection.isConnected).toBe(false);
      expect(result.current.send.isReady).toBe(false);
    });
  });

  describe('Cleanup and Memory Leaks', () => {
    beforeEach(() => {
      mockPusherService.getState.mockReturnValue(WebSocketState.CONNECTED);
    });

    it('should clean up subscriptions on unmount', () => {
      const eventHandlers = { 'message': vi.fn(), 'update': vi.fn() };

      const { unmount } = renderHook(() =>
        usePusherChannel('test-channel', eventHandlers)
      );

      expect(mockPusherService.subscribe).toHaveBeenCalledTimes(2);

      unmount();

      expect(mockPusherService.unsubscribe).toHaveBeenCalledTimes(2);
    });

    it('should clean up timers on unmount', () => {
      vi.useFakeTimers();

      const { unmount } = renderHook(() => usePusherConnection());

      // Fast-forward to ensure timer is set
      act(() => {
        vi.advanceTimersByTime(1000);
      });

      unmount();

      // Should not throw when timers are cleared
      expect(() => {
        vi.runAllTimers();
      }).not.toThrow();

      vi.useRealTimers();
    });

    it('should clean up event listeners on unmount', () => {
      const unsubscribeFns = [vi.fn(), vi.fn()];
      mockPusherService.onStateChange.mockReturnValue(unsubscribeFns[0]);
      mockPusherService.onError.mockReturnValue(unsubscribeFns[1]);

      const { unmount } = renderHook(() => usePusherConnection());

      unmount();

      unsubscribeFns.forEach(fn => {
        expect(fn).toHaveBeenCalled();
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty event handlers object', () => {
      mockPusherService.getState.mockReturnValue(WebSocketState.CONNECTED);

      const { result } = renderHook(() =>
        usePusherChannel('test-channel', {})
      );

      expect(mockPusherService.subscribe).not.toHaveBeenCalled();
      expect(result.current.isSubscribed).toBe(false);
    });

    it('should handle service not ready for presence', async () => {
      mockPusherService.getState.mockReturnValue(WebSocketState.DISCONNECTED);

      const { result } = renderHook(() =>
        usePusherPresence('classroom-1', { name: 'Test' })
      );

      await act(async () => {
        await result.current.joinChannel();
      });

      expect(result.current.isJoined).toBe(false);
    });

    it('should handle rapid state changes', () => {
      let stateChangeListener: (state: WebSocketState) => void;
      mockPusherService.onStateChange.mockImplementation((listener) => {
        stateChangeListener = listener;
        return () => {};
      });

      const { result } = renderHook(() => usePusher());

      const states = [
        WebSocketState.CONNECTING,
        WebSocketState.CONNECTED,
        WebSocketState.DISCONNECTED,
        WebSocketState.RECONNECTING,
        WebSocketState.CONNECTED
      ];

      states.forEach(state => {
        act(() => {
          stateChangeListener(state);
        });
        expect(result.current.state).toBe(state);
      });
    });

    it('should handle concurrent subscription attempts', () => {
      mockPusherService.getState.mockReturnValue(WebSocketState.CONNECTED);

      const { result } = renderHook(() =>
        usePusherChannel('test-channel', { 'message': vi.fn() }, { autoSubscribe: false })
      );

      // Attempt multiple concurrent subscriptions
      act(() => {
        result.current.subscribe();
        result.current.subscribe();
        result.current.subscribe();
      });

      // Should only subscribe once
      expect(result.current.isSubscribed).toBe(true);
    });
  });

  describe('Performance', () => {
    it('should not cause unnecessary rerenders', () => {
      mockPusherService.getState.mockReturnValue(WebSocketState.CONNECTED);

      let renderCount = 0;
      const TestComponent = () => {
        renderCount++;
        return usePusher();
      };

      const { rerender } = renderHook(() => TestComponent());

      const initialRenderCount = renderCount;

      // Multiple rerenders with same props
      rerender();
      rerender();
      rerender();

      // Should only have rendered once more per rerender call
      expect(renderCount).toBe(initialRenderCount + 3);
    });

    it('should handle many simultaneous subscriptions', () => {
      mockPusherService.getState.mockReturnValue(WebSocketState.CONNECTED);

      const channels = Array.from({ length: 100 }, (_, i) => `channel-${i}`);

      channels.forEach(channel => {
        renderHook(() =>
          usePusherChannel(channel, { 'message': vi.fn() })
        );
      });

      expect(mockPusherService.subscribe).toHaveBeenCalledTimes(100);
    });
  });
});