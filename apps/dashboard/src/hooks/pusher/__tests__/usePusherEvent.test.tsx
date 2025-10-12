import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { ReactNode } from 'react';
import {
  usePusherEvent,
  usePusherEvents,
  useContentGenerationEvents,
  useQuizEvents,
  useAgentEvents,
  useSystemEvents
} from '../usePusherEvent';
import { PusherContext } from '../../../contexts/PusherContext';
import type { PusherConnectionState, PusherEventHandler } from '../../../types/pusher';

// Mock logger
vi.mock('../../../utils/logger', () => ({
  logger: {
    debug: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
  },
}));

describe('usePusherEvent', () => {
  const mockOn = vi.fn();
  const mockOff = vi.fn();
  const mockSubscribeToChannel = vi.fn();
  const mockUnsubscribeFromChannel = vi.fn();

  const createMockPusherContext = (overrides = {}) => ({
    isConnected: true,
    connectionState: 'connected' as PusherConnectionState,
    on: mockOn,
    off: mockOff,
    subscribeToChannel: mockSubscribeToChannel,
    unsubscribeFromChannel: mockUnsubscribeFromChannel,
    sendMessage: vi.fn(),
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
    mockOn.mockReturnValue(vi.fn()); // Return unsubscribe function
    mockSubscribeToChannel.mockReturnValue('subscription-id');
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Global Event Listening', () => {
    it('should listen to global events', () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const handler = vi.fn();

      renderHook(
        () => usePusherEvent('test-event', handler),
        { wrapper }
      );

      expect(mockOn).toHaveBeenCalledWith(
        'test-event',
        expect.any(Function)
      );
    });

    it('should not listen when disabled', () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const handler = vi.fn();

      renderHook(
        () => usePusherEvent('test-event', handler, { enabled: false }),
        { wrapper }
      );

      expect(mockOn).not.toHaveBeenCalled();
    });

    it('should call handler when event occurs', () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const handler = vi.fn();
      let capturedHandler: PusherEventHandler | null = null;

      mockOn.mockImplementation((event, h) => {
        capturedHandler = h;
        return vi.fn();
      });

      renderHook(
        () => usePusherEvent('test-event', handler),
        { wrapper }
      );

      const testData = { message: 'Hello' };
      const testMetadata = { timestamp: Date.now() };

      capturedHandler?.(testData, testMetadata);

      expect(handler).toHaveBeenCalledWith(testData, testMetadata);
    });

    it('should unsubscribe on unmount', () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const mockUnsubscribe = vi.fn();
      mockOn.mockReturnValue(mockUnsubscribe);

      const handler = vi.fn();

      const { unmount } = renderHook(
        () => usePusherEvent('test-event', handler),
        { wrapper }
      );

      expect(mockOn).toHaveBeenCalled();

      unmount();

      expect(mockUnsubscribe).toHaveBeenCalled();
    });
  });

  describe('Channel-Specific Event Listening', () => {
    it('should subscribe to channel with event', () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const handler = vi.fn();

      renderHook(
        () => usePusherEvent('test-event', handler, { channel: 'test-channel' }),
        { wrapper }
      );

      expect(mockSubscribeToChannel).toHaveBeenCalledWith(
        'test-channel',
        { 'test-event': expect.any(Function) },
        { autoSubscribe: true }
      );
    });

    it('should unsubscribe from channel on unmount', () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const handler = vi.fn();

      const { unmount } = renderHook(
        () => usePusherEvent('test-event', handler, { channel: 'test-channel' }),
        { wrapper }
      );

      expect(mockSubscribeToChannel).toHaveBeenCalled();

      unmount();

      expect(mockUnsubscribeFromChannel).toHaveBeenCalledWith('subscription-id');
    });
  });

  describe('Error Handling', () => {
    it('should catch errors in handler', () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const error = new Error('Handler error');
      const handler = vi.fn(() => { throw error; });
      const onError = vi.fn();

      let capturedHandler: PusherEventHandler | null = null;

      mockOn.mockImplementation((event, h) => {
        capturedHandler = h;
        return vi.fn();
      });

      renderHook(
        () => usePusherEvent('test-event', handler, { onError }),
        { wrapper }
      );

      capturedHandler?.({}, {});

      expect(onError).toHaveBeenCalledWith(error);
    });

    it('should call onError when subscription fails', () => {
      const error = new Error('Subscription failed');
      mockSubscribeToChannel.mockImplementation(() => {
        throw error;
      });

      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const handler = vi.fn();
      const onError = vi.fn();

      renderHook(
        () => usePusherEvent('test-event', handler, { channel: 'test-channel', onError }),
        { wrapper }
      );

      expect(onError).toHaveBeenCalledWith(error);
    });
  });

  describe('Handler Updates', () => {
    it('should use latest handler ref', () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      let handler = vi.fn();
      let capturedHandler: PusherEventHandler | null = null;

      mockOn.mockImplementation((event, h) => {
        capturedHandler = h;
        return vi.fn();
      });

      const { rerender } = renderHook(
        ({ h }) => usePusherEvent('test-event', h),
        { wrapper, initialProps: { h: handler } }
      );

      const newHandler = vi.fn();
      rerender({ h: newHandler });

      capturedHandler?.({}, {});

      expect(handler).not.toHaveBeenCalled();
      expect(newHandler).toHaveBeenCalled();
    });
  });
});

describe('usePusherEvents', () => {
  const mockSubscribeToChannel = vi.fn();
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
    mockSubscribeToChannel.mockReturnValue('subscription-id');
  });

  it('should subscribe to multiple events on a channel', () => {
    const mockContext = {
      isConnected: true,
      connectionState: 'connected' as PusherConnectionState,
      subscribeToChannel: mockSubscribeToChannel,
      unsubscribeFromChannel: mockUnsubscribeFromChannel,
      on: vi.fn(),
      off: vi.fn(),
      sendMessage: vi.fn(),
      joinPresenceChannel: vi.fn(),
      leavePresenceChannel: vi.fn(),
      getPresenceMembers: vi.fn(() => []),
      send: vi.fn(),
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
    };

    const wrapper = createWrapper(mockContext);

    const eventHandlers = {
      'event-1': vi.fn(),
      'event-2': vi.fn(),
      'event-3': vi.fn(),
    };

    renderHook(
      () => usePusherEvents(eventHandlers, { channel: 'test-channel' }),
      { wrapper }
    );

    expect(mockSubscribeToChannel).toHaveBeenCalledWith(
      'test-channel',
      eventHandlers,
      { autoSubscribe: true }
    );
  });

  it('should not subscribe when no event handlers', () => {
    const mockContext = {
      isConnected: true,
      connectionState: 'connected' as PusherConnectionState,
      subscribeToChannel: mockSubscribeToChannel,
      unsubscribeFromChannel: mockUnsubscribeFromChannel,
      on: vi.fn(),
      off: vi.fn(),
      sendMessage: vi.fn(),
      joinPresenceChannel: vi.fn(),
      leavePresenceChannel: vi.fn(),
      getPresenceMembers: vi.fn(() => []),
      send: vi.fn(),
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
    };

    const wrapper = createWrapper(mockContext);

    renderHook(
      () => usePusherEvents({}, { channel: 'test-channel' }),
      { wrapper }
    );

    expect(mockSubscribeToChannel).not.toHaveBeenCalled();
  });

  it('should unsubscribe on unmount', () => {
    const mockContext = {
      isConnected: true,
      connectionState: 'connected' as PusherConnectionState,
      subscribeToChannel: mockSubscribeToChannel,
      unsubscribeFromChannel: mockUnsubscribeFromChannel,
      on: vi.fn(),
      off: vi.fn(),
      sendMessage: vi.fn(),
      joinPresenceChannel: vi.fn(),
      leavePresenceChannel: vi.fn(),
      getPresenceMembers: vi.fn(() => []),
      send: vi.fn(),
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
    };

    const wrapper = createWrapper(mockContext);

    const { unmount } = renderHook(
      () => usePusherEvents({ 'event-1': vi.fn() }, { channel: 'test-channel' }),
      { wrapper }
    );

    unmount();

    expect(mockUnsubscribeFromChannel).toHaveBeenCalledWith('subscription-id');
  });
});

describe('useContentGenerationEvents', () => {
  const mockSubscribeToChannel = vi.fn(() => 'subscription-id');

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

  it('should subscribe to content generation channel', () => {
    const mockContext = {
      isConnected: true,
      connectionState: 'connected' as PusherConnectionState,
      subscribeToChannel: mockSubscribeToChannel,
      unsubscribeFromChannel: vi.fn(),
      on: vi.fn(),
      off: vi.fn(),
      sendMessage: vi.fn(),
      joinPresenceChannel: vi.fn(),
      leavePresenceChannel: vi.fn(),
      getPresenceMembers: vi.fn(() => []),
      send: vi.fn(),
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
    };

    const wrapper = createWrapper(mockContext);

    const onProgress = vi.fn();
    const onComplete = vi.fn();
    const onError = vi.fn();

    renderHook(
      () => useContentGenerationEvents(onProgress, onComplete, onError),
      { wrapper }
    );

    expect(mockSubscribeToChannel).toHaveBeenCalledWith(
      'content-generation',
      {
        'content-progress': onProgress,
        'content-complete': onComplete,
        'content-error': onError,
      },
      { autoSubscribe: true }
    );
  });

  it('should only subscribe to provided handlers', () => {
    const mockContext = {
      isConnected: true,
      connectionState: 'connected' as PusherConnectionState,
      subscribeToChannel: mockSubscribeToChannel,
      unsubscribeFromChannel: vi.fn(),
      on: vi.fn(),
      off: vi.fn(),
      sendMessage: vi.fn(),
      joinPresenceChannel: vi.fn(),
      leavePresenceChannel: vi.fn(),
      getPresenceMembers: vi.fn(() => []),
      send: vi.fn(),
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
    };

    const wrapper = createWrapper(mockContext);

    const onProgress = vi.fn();

    renderHook(
      () => useContentGenerationEvents(onProgress),
      { wrapper }
    );

    expect(mockSubscribeToChannel).toHaveBeenCalledWith(
      'content-generation',
      { 'content-progress': onProgress },
      { autoSubscribe: true }
    );
  });
});

describe('useQuizEvents', () => {
  const mockSubscribeToChannel = vi.fn(() => 'subscription-id');

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

  it('should subscribe to quiz updates channel', () => {
    const mockContext = {
      isConnected: true,
      connectionState: 'connected' as PusherConnectionState,
      subscribeToChannel: mockSubscribeToChannel,
      unsubscribeFromChannel: vi.fn(),
      on: vi.fn(),
      off: vi.fn(),
      sendMessage: vi.fn(),
      joinPresenceChannel: vi.fn(),
      leavePresenceChannel: vi.fn(),
      getPresenceMembers: vi.fn(() => []),
      send: vi.fn(),
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
    };

    const wrapper = createWrapper(mockContext);

    const onStart = vi.fn();
    const onSubmit = vi.fn();
    const onResult = vi.fn();

    renderHook(
      () => useQuizEvents(onStart, onSubmit, onResult),
      { wrapper }
    );

    expect(mockSubscribeToChannel).toHaveBeenCalledWith(
      'quiz-updates',
      {
        'quiz-start': onStart,
        'quiz-submit': onSubmit,
        'quiz-result': onResult,
      },
      { autoSubscribe: true }
    );
  });
});

describe('useAgentEvents', () => {
  const mockSubscribeToChannel = vi.fn(() => 'subscription-id');

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

  it('should subscribe to agent-specific channel', () => {
    const mockContext = {
      isConnected: true,
      connectionState: 'connected' as PusherConnectionState,
      subscribeToChannel: mockSubscribeToChannel,
      unsubscribeFromChannel: vi.fn(),
      on: vi.fn(),
      off: vi.fn(),
      sendMessage: vi.fn(),
      joinPresenceChannel: vi.fn(),
      leavePresenceChannel: vi.fn(),
      getPresenceMembers: vi.fn(() => []),
      send: vi.fn(),
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
    };

    const wrapper = createWrapper(mockContext);

    const onStatusUpdate = vi.fn();
    const onResponse = vi.fn();

    renderHook(
      () => useAgentEvents('agent-123', onStatusUpdate, onResponse),
      { wrapper }
    );

    expect(mockSubscribeToChannel).toHaveBeenCalledWith(
      'agent-agent-123',
      {
        'agent-status-update': onStatusUpdate,
        'agent-response': onResponse,
      },
      { autoSubscribe: true }
    );
  });
});

describe('useSystemEvents', () => {
  const mockSubscribeToChannel = vi.fn(() => 'subscription-id');

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

  it('should subscribe to system announcements channel', () => {
    const mockContext = {
      isConnected: true,
      connectionState: 'connected' as PusherConnectionState,
      subscribeToChannel: mockSubscribeToChannel,
      unsubscribeFromChannel: vi.fn(),
      on: vi.fn(),
      off: vi.fn(),
      sendMessage: vi.fn(),
      joinPresenceChannel: vi.fn(),
      leavePresenceChannel: vi.fn(),
      getPresenceMembers: vi.fn(() => []),
      send: vi.fn(),
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
    };

    const wrapper = createWrapper(mockContext);

    const onNotification = vi.fn();
    const onAlert = vi.fn();
    const onMaintenance = vi.fn();

    renderHook(
      () => useSystemEvents(onNotification, onAlert, onMaintenance),
      { wrapper }
    );

    expect(mockSubscribeToChannel).toHaveBeenCalledWith(
      'system-announcements',
      {
        'system-notification': onNotification,
        'system-alert': onAlert,
        'system-maintenance': onMaintenance,
      },
      { autoSubscribe: true }
    );
  });
});
