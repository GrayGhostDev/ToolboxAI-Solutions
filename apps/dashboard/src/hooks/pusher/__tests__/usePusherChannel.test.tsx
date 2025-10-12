import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { ReactNode } from 'react';
import { usePusherChannel, usePrivateChannel, usePresenceChannel } from '../usePusherChannel';
import { PusherContext } from '../../../contexts/PusherContext';
import type { PusherConnectionState } from '../../../types/pusher';

// Mock logger
vi.mock('../../../utils/logger', () => ({
  logger: {
    debug: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
  },
}));

describe('usePusherChannel', () => {
  const mockSubscribeToChannel = vi.fn();
  const mockUnsubscribeFromChannel = vi.fn();
  const mockSendMessage = vi.fn();

  const createMockPusherContext = (overrides = {}) => ({
    isConnected: true,
    connectionState: 'connected' as PusherConnectionState,
    subscribeToChannel: mockSubscribeToChannel,
    unsubscribeFromChannel: mockUnsubscribeFromChannel,
    sendMessage: mockSendMessage,
    on: vi.fn(),
    off: vi.fn(),
    joinPresenceChannel: vi.fn(),
    leavePresenceChannel: vi.fn(),
    getPresenceMembers: vi.fn(() => []),
    send: vi.fn(),
    subscribe: vi.fn(),
    unsubscribe: vi.fn(),
    ...overrides,
  });

  const createWrapper = (contextValue: any) => {
    return ({ children }: { children: ReactNode }) => (
      <PusherContext.Provider value={contextValue}>
        {children}
      </PusherContext.Provider>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockSubscribeToChannel.mockReturnValue('subscription-id-123');
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Basic Subscription', () => {
    it('should subscribe to channel when connected', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const { result } = renderHook(
        () => usePusherChannel('test-channel'),
        { wrapper }
      );

      await waitFor(() => {
        expect(mockSubscribeToChannel).toHaveBeenCalledWith(
          'test-channel',
          {},
          expect.objectContaining({ autoSubscribe: true })
        );
      });

      expect(result.current.isSubscribed).toBe(true);
    });

    it('should not subscribe when not connected', () => {
      const mockContext = createMockPusherContext({ isConnected: false });
      const wrapper = createWrapper(mockContext);

      renderHook(
        () => usePusherChannel('test-channel'),
        { wrapper }
      );

      expect(mockSubscribeToChannel).not.toHaveBeenCalled();
    });

    it('should not subscribe when disabled', () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      renderHook(
        () => usePusherChannel('test-channel', {}, { enabled: false }),
        { wrapper }
      );

      expect(mockSubscribeToChannel).not.toHaveBeenCalled();
    });

    it('should not auto-subscribe when autoSubscribe is false', () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      renderHook(
        () => usePusherChannel('test-channel', {}, { autoSubscribe: false }),
        { wrapper }
      );

      expect(mockSubscribeToChannel).not.toHaveBeenCalled();
    });

    it('should unsubscribe on unmount', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const { unmount } = renderHook(
        () => usePusherChannel('test-channel'),
        { wrapper }
      );

      await waitFor(() => {
        expect(mockSubscribeToChannel).toHaveBeenCalled();
      });

      unmount();

      expect(mockUnsubscribeFromChannel).toHaveBeenCalledWith('subscription-id-123');
    });
  });

  describe('Event Handlers', () => {
    it('should subscribe with event handlers', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const eventHandlers = {
        'test-event': vi.fn(),
        'another-event': vi.fn(),
      };

      renderHook(
        () => usePusherChannel('test-channel', eventHandlers),
        { wrapper }
      );

      await waitFor(() => {
        expect(mockSubscribeToChannel).toHaveBeenCalledWith(
          'test-channel',
          eventHandlers,
          expect.any(Object)
        );
      });
    });

    it('should allow binding events dynamically', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const { result } = renderHook(
        () => usePusherChannel('test-channel'),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSubscribed).toBe(true);
      });

      const handler = vi.fn();
      let unbind: (() => void) | undefined;

      act(() => {
        unbind = result.current.bind('new-event', handler);
      });

      expect(typeof unbind).toBe('function');
    });

    it('should allow unbinding events', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const handler = vi.fn();

      const { result } = renderHook(
        () => usePusherChannel('test-channel'),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSubscribed).toBe(true);
      });

      act(() => {
        const unbind = result.current.bind('test-event', handler);
        unbind();
      });

      // Handler should be removed
      expect(result.current.isSubscribed).toBe(true);
    });
  });

  describe('Manual Subscribe/Unsubscribe', () => {
    it('should allow manual subscription', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const { result } = renderHook(
        () => usePusherChannel('test-channel', {}, { autoSubscribe: false }),
        { wrapper }
      );

      expect(result.current.isSubscribed).toBe(false);

      await act(async () => {
        result.current.subscribe();
      });

      expect(mockSubscribeToChannel).toHaveBeenCalled();
      expect(result.current.isSubscribed).toBe(true);
    });

    it('should allow manual unsubscription', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const { result } = renderHook(
        () => usePusherChannel('test-channel'),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSubscribed).toBe(true);
      });

      await act(async () => {
        result.current.unsubscribe();
      });

      expect(mockUnsubscribeFromChannel).toHaveBeenCalledWith('subscription-id-123');
      expect(result.current.isSubscribed).toBe(false);
    });

    it('should not subscribe twice', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const { result } = renderHook(
        () => usePusherChannel('test-channel'),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSubscribed).toBe(true);
      });

      act(() => {
        result.current.subscribe();
      });

      // Should still only be called once
      expect(mockSubscribeToChannel).toHaveBeenCalledTimes(1);
    });
  });

  describe('Trigger Events', () => {
    it('should trigger events on the channel', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const { result } = renderHook(
        () => usePusherChannel('test-channel'),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSubscribed).toBe(true);
      });

      const testData = { message: 'Hello' };

      await act(async () => {
        await result.current.trigger('test-event', testData);
      });

      expect(mockSendMessage).toHaveBeenCalledWith(
        'test-event',
        testData,
        { channel: 'test-channel' }
      );
    });

    it('should throw error when not connected', async () => {
      const mockContext = createMockPusherContext({ isConnected: false });
      const wrapper = createWrapper(mockContext);

      const { result } = renderHook(
        () => usePusherChannel('test-channel', {}, { enabled: false }),
        { wrapper }
      );

      await expect(async () => {
        await result.current.trigger('test-event', {});
      }).rejects.toThrow('Not connected to Pusher');
    });
  });

  describe('Connection State Changes', () => {
    it('should handle disconnection', async () => {
      let isConnected = true;
      const mockContext = createMockPusherContext({
        get isConnected() { return isConnected; }
      });
      const wrapper = createWrapper(mockContext);

      const onDisconnect = vi.fn();

      const { rerender } = renderHook(
        () => usePusherChannel('test-channel', {}, { onDisconnect }),
        { wrapper }
      );

      await waitFor(() => {
        expect(mockSubscribeToChannel).toHaveBeenCalled();
      });

      isConnected = false;
      rerender();

      await waitFor(() => {
        expect(onDisconnect).toHaveBeenCalled();
      });
    });

    it('should reconnect when connection restored', async () => {
      let isConnected = false;
      const mockContext = createMockPusherContext({
        get isConnected() { return isConnected; }
      });
      const wrapper = createWrapper(mockContext);

      const { rerender } = renderHook(
        () => usePusherChannel('test-channel'),
        { wrapper }
      );

      expect(mockSubscribeToChannel).not.toHaveBeenCalled();

      isConnected = true;
      rerender();

      await waitFor(() => {
        expect(mockSubscribeToChannel).toHaveBeenCalled();
      });
    });
  });

  describe('Callbacks', () => {
    it('should call onConnect when subscribed', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const onConnect = vi.fn();

      renderHook(
        () => usePusherChannel('test-channel', {}, { onConnect }),
        { wrapper }
      );

      await waitFor(() => {
        expect(onConnect).toHaveBeenCalled();
      });
    });

    it('should call onDisconnect when unsubscribed', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const onDisconnect = vi.fn();

      const { result } = renderHook(
        () => usePusherChannel('test-channel', {}, { onDisconnect }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isSubscribed).toBe(true);
      });

      await act(async () => {
        result.current.unsubscribe();
      });

      expect(onDisconnect).toHaveBeenCalled();
    });

    it('should call onError when subscription fails', async () => {
      const error = new Error('Subscription failed');
      mockSubscribeToChannel.mockImplementation(() => {
        throw error;
      });

      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const onError = vi.fn();

      renderHook(
        () => usePusherChannel('test-channel', {}, { onError }),
        { wrapper }
      );

      await waitFor(() => {
        expect(onError).toHaveBeenCalledWith(error);
      });
    });
  });

  describe('Return Values', () => {
    it('should return correct connection state', async () => {
      const mockContext = createMockPusherContext({
        connectionState: 'connecting' as PusherConnectionState
      });
      const wrapper = createWrapper(mockContext);

      const { result } = renderHook(
        () => usePusherChannel('test-channel'),
        { wrapper }
      );

      expect(result.current.connectionState).toBe('connecting');
    });

    it('should return isConnected status', () => {
      const mockContext = createMockPusherContext({ isConnected: false });
      const wrapper = createWrapper(mockContext);

      const { result } = renderHook(
        () => usePusherChannel('test-channel'),
        { wrapper }
      );

      expect(result.current.isConnected).toBe(false);
    });
  });
});

describe('usePrivateChannel', () => {
  const mockSubscribeToChannel = vi.fn(() => 'subscription-id');
  const mockUnsubscribeFromChannel = vi.fn();

  const createWrapper = (contextValue: any) => {
    return ({ children }: { children: ReactNode }) => (
      <PusherContext.Provider value={contextValue}>
        {children}
      </PusherContext.Provider>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should prepend "private-" to channel name', async () => {
    const mockContext = {
      isConnected: true,
      connectionState: 'connected' as PusherConnectionState,
      subscribeToChannel: mockSubscribeToChannel,
      unsubscribeFromChannel: mockUnsubscribeFromChannel,
      sendMessage: vi.fn(),
      on: vi.fn(),
      off: vi.fn(),
      joinPresenceChannel: vi.fn(),
      leavePresenceChannel: vi.fn(),
      getPresenceMembers: vi.fn(() => []),
      send: vi.fn(),
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
    };

    const wrapper = createWrapper(mockContext);

    renderHook(
      () => usePrivateChannel('user-channel'),
      { wrapper }
    );

    await waitFor(() => {
      expect(mockSubscribeToChannel).toHaveBeenCalledWith(
        'private-user-channel',
        {},
        expect.any(Object)
      );
    });
  });
});

describe('usePresenceChannel', () => {
  const mockSubscribeToChannel = vi.fn(() => 'subscription-id');
  const mockUnsubscribeFromChannel = vi.fn();
  const mockGetPresenceMembers = vi.fn(() => [
    { id: '1', name: 'User 1' },
    { id: '2', name: 'User 2' },
  ]);

  const createWrapper = (contextValue: any) => {
    return ({ children }: { children: ReactNode }) => (
      <PusherContext.Provider value={contextValue}>
        {children}
      </PusherContext.Provider>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should prepend "presence-" to channel name', async () => {
    const mockContext = {
      isConnected: true,
      connectionState: 'connected' as PusherConnectionState,
      subscribeToChannel: mockSubscribeToChannel,
      unsubscribeFromChannel: mockUnsubscribeFromChannel,
      sendMessage: vi.fn(),
      on: vi.fn(),
      off: vi.fn(),
      joinPresenceChannel: vi.fn(),
      leavePresenceChannel: vi.fn(),
      getPresenceMembers: mockGetPresenceMembers,
      send: vi.fn(),
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
    };

    const wrapper = createWrapper(mockContext);

    renderHook(
      () => usePresenceChannel('room'),
      { wrapper }
    );

    await waitFor(() => {
      expect(mockSubscribeToChannel).toHaveBeenCalledWith(
        'presence-room',
        expect.any(Object),
        expect.any(Object)
      );
    });
  });

  it('should track members', async () => {
    const mockContext = {
      isConnected: true,
      connectionState: 'connected' as PusherConnectionState,
      subscribeToChannel: mockSubscribeToChannel,
      unsubscribeFromChannel: mockUnsubscribeFromChannel,
      sendMessage: vi.fn(),
      on: vi.fn(),
      off: vi.fn(),
      joinPresenceChannel: vi.fn(),
      leavePresenceChannel: vi.fn(),
      getPresenceMembers: mockGetPresenceMembers,
      send: vi.fn(),
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
    };

    const wrapper = createWrapper(mockContext);

    const { result } = renderHook(
      () => usePresenceChannel('room'),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.members).toHaveLength(2);
    });

    expect(result.current.members[0]).toEqual({ id: '1', name: 'User 1' });
    expect(result.current.members[1]).toEqual({ id: '2', name: 'User 2' });
  });
});
