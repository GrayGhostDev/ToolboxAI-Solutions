import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { ReactNode } from 'react';
import {
  usePusherPresence,
  useUserActivity,
  useCollaboration,
  useOnlineStatus,
} from '../usePusherPresence';
import { PusherContext } from '../../../contexts/PusherContext';
import type { PusherMember } from '../../../types/pusher';

// Mock logger
vi.mock('../../../utils/logger', () => ({
  logger: {
    debug: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
  },
}));

describe('usePusherPresence', () => {
  const mockJoinPresenceChannel = vi.fn();
  const mockLeavePresenceChannel = vi.fn();
  const mockGetPresenceMembers = vi.fn();
  const mockIsInPresenceChannel = vi.fn();
  const mockSendMessage = vi.fn();

  const mockMembers: PusherMember[] = [
    { id: 'user-1', info: { name: 'User 1', status: 'online' } },
    { id: 'user-2', info: { name: 'User 2', status: 'away' } },
    { id: 'user-3', info: { name: 'User 3', status: 'online' } },
  ];

  const createMockPusherContext = (overrides = {}) => ({
    isConnected: true,
    connectionState: 'connected' as const,
    subscribeToChannel: vi.fn(),
    unsubscribeFromChannel: vi.fn(),
    sendMessage: mockSendMessage,
    on: vi.fn(),
    off: vi.fn(),
    joinPresenceChannel: mockJoinPresenceChannel,
    leavePresenceChannel: mockLeavePresenceChannel,
    getPresenceMembers: mockGetPresenceMembers,
    isInPresenceChannel: mockIsInPresenceChannel,
    subscribe: vi.fn(),
    unsubscribe: vi.fn(),
    send: vi.fn(),
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
    vi.useFakeTimers();

    // Default mock implementations
    mockJoinPresenceChannel.mockResolvedValue({
      me: { id: 'my-id' },
    });
    mockGetPresenceMembers.mockReturnValue(mockMembers);
    mockIsInPresenceChannel.mockReturnValue(false);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  describe('Basic Presence', () => {
    it('should auto-join presence channel when enabled', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      renderHook(() => usePusherPresence('test-room'), { wrapper });

      await waitFor(() => {
        expect(mockJoinPresenceChannel).toHaveBeenCalledWith(
          'test-room',
          expect.objectContaining({ name: 'Anonymous User', status: 'online' })
        );
      });
    });

    it('should not auto-join when disabled', () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      renderHook(() => usePusherPresence('test-room', { enabled: false }), { wrapper });

      expect(mockJoinPresenceChannel).not.toHaveBeenCalled();
    });

    it('should join with custom user info', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const userInfo = { name: 'John Doe', status: 'online' as const };

      renderHook(() => usePusherPresence('test-room', { userInfo }), { wrapper });

      await waitFor(() => {
        expect(mockJoinPresenceChannel).toHaveBeenCalledWith('test-room', userInfo);
      });
    });

    it('should set initial members after joining', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const { result } = renderHook(() => usePusherPresence('test-room'), { wrapper });

      await waitFor(() => {
        expect(result.current.isJoined).toBe(true);
      });

      expect(result.current.members).toEqual(mockMembers);
      expect(result.current.onlineCount).toBe(2); // Two members with status 'online'
    });

    it('should set my ID after joining', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const { result } = renderHook(() => usePusherPresence('test-room'), { wrapper });

      await waitFor(() => {
        expect(result.current.myId).toBe('my-id');
      });
    });

    it('should leave presence channel on unmount', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const { unmount } = renderHook(() => usePusherPresence('test-room'), { wrapper });

      await waitFor(() => {
        expect(mockJoinPresenceChannel).toHaveBeenCalled();
      });

      unmount();

      expect(mockLeavePresenceChannel).toHaveBeenCalledWith('test-room');
    });
  });

  describe('Manual Join/Leave', () => {
    it('should allow manual join', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const { result } = renderHook(
        () => usePusherPresence('test-room', { enabled: false }),
        { wrapper }
      );

      expect(result.current.isJoined).toBe(false);

      await act(async () => {
        await result.current.join();
      });

      expect(mockJoinPresenceChannel).toHaveBeenCalled();
      expect(result.current.isJoined).toBe(true);
    });

    it('should not join twice', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const { result } = renderHook(() => usePusherPresence('test-room'), { wrapper });

      await waitFor(() => {
        expect(result.current.isJoined).toBe(true);
      });

      await act(async () => {
        await result.current.join();
      });

      expect(mockJoinPresenceChannel).toHaveBeenCalledTimes(1);
    });

    it('should allow manual leave', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const { result } = renderHook(() => usePusherPresence('test-room'), { wrapper });

      await waitFor(() => {
        expect(result.current.isJoined).toBe(true);
      });

      act(() => {
        result.current.leave();
      });

      expect(mockLeavePresenceChannel).toHaveBeenCalledWith('test-room');
      expect(result.current.isJoined).toBe(false);
      expect(result.current.members).toEqual([]);
      expect(result.current.myId).toBeNull();
    });

    it('should not leave when not joined', () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const { result } = renderHook(
        () => usePusherPresence('test-room', { enabled: false }),
        { wrapper }
      );

      act(() => {
        result.current.leave();
      });

      expect(mockLeavePresenceChannel).not.toHaveBeenCalled();
    });
  });

  describe('Status Updates', () => {
    it('should update user status', async () => {
      mockJoinPresenceChannel.mockResolvedValue({ me: { id: 'user-1' } });

      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const { result } = renderHook(() => usePusherPresence('test-room'), { wrapper });

      await waitFor(() => {
        expect(result.current.isJoined).toBe(true);
      });

      act(() => {
        result.current.updateStatus('away');
      });

      // Check that the member status was updated locally
      const updatedMember = result.current.members.find(m => m.id === 'user-1');
      expect(updatedMember?.info.status).toBe('away');
    });

    it('should not update status when not joined', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const { result } = renderHook(
        () => usePusherPresence('test-room', { enabled: false }),
        { wrapper }
      );

      act(() => {
        result.current.updateStatus('away');
      });

      // Should not throw error, just no-op
      expect(result.current.members).toEqual([]);
    });
  });

  describe('Member Queries', () => {
    it('should get specific member', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const { result } = renderHook(() => usePusherPresence('test-room'), { wrapper });

      await waitFor(() => {
        expect(result.current.isJoined).toBe(true);
      });

      const member = result.current.getMember('user-1');
      expect(member).toEqual(mockMembers[0]);
    });

    it('should return undefined for non-existent member', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const { result } = renderHook(() => usePusherPresence('test-room'), { wrapper });

      await waitFor(() => {
        expect(result.current.isJoined).toBe(true);
      });

      const member = result.current.getMember('non-existent');
      expect(member).toBeUndefined();
    });

    it('should count online members correctly', async () => {
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const { result } = renderHook(() => usePusherPresence('test-room'), { wrapper });

      await waitFor(() => {
        expect(result.current.isJoined).toBe(true);
      });

      expect(result.current.onlineCount).toBe(2); // user-1 and user-3 are online
    });
  });

  describe('Member Join/Leave Callbacks', () => {
    it('should call onMemberJoin when new member joins', async () => {
      const onMemberJoin = vi.fn();
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      // Start with no members
      mockGetPresenceMembers.mockReturnValueOnce([]);

      const { result } = renderHook(
        () => usePusherPresence('test-room', { onMemberJoin }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isJoined).toBe(true);
      });

      // Simulate new member joining
      mockGetPresenceMembers.mockReturnValue([mockMembers[0]]);

      act(() => {
        vi.advanceTimersByTime(1000);
      });

      await waitFor(() => {
        expect(onMemberJoin).toHaveBeenCalledWith(mockMembers[0]);
      });
    });

    it('should call onMemberLeave when member leaves', async () => {
      const onMemberLeave = vi.fn();
      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const { result } = renderHook(
        () => usePusherPresence('test-room', { onMemberLeave }),
        { wrapper }
      );

      await waitFor(() => {
        expect(result.current.isJoined).toBe(true);
      });

      // Simulate member leaving
      mockGetPresenceMembers.mockReturnValue([mockMembers[0], mockMembers[1]]);

      act(() => {
        vi.advanceTimersByTime(1000);
      });

      await waitFor(() => {
        expect(onMemberLeave).toHaveBeenCalledWith(mockMembers[2]);
      });
    });
  });

  describe('Error Handling', () => {
    it('should call onError when join fails', async () => {
      const error = new Error('Join failed');
      const onError = vi.fn();
      mockJoinPresenceChannel.mockRejectedValue(error);

      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      renderHook(() => usePusherPresence('test-room', { onError }), { wrapper });

      await waitFor(() => {
        expect(onError).toHaveBeenCalledWith(error);
      });
    });

    it('should call onError when leave fails', async () => {
      const error = new Error('Leave failed');
      const onError = vi.fn();
      mockLeavePresenceChannel.mockImplementation(() => {
        throw error;
      });

      const mockContext = createMockPusherContext();
      const wrapper = createWrapper(mockContext);

      const { result } = renderHook(() => usePusherPresence('test-room', { onError }), { wrapper });

      await waitFor(() => {
        expect(result.current.isJoined).toBe(true);
      });

      act(() => {
        result.current.leave();
      });

      expect(onError).toHaveBeenCalledWith(error);
    });
  });
});

describe('useUserActivity', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should initialize with online status', () => {
    const { result } = renderHook(() => useUserActivity());

    expect(result.current.status).toBe('online');
    expect(result.current.lastActivity).toBeGreaterThan(0);
  });

  it('should transition to idle after timeout', () => {
    const idleTimeout = 1000;
    const { result } = renderHook(() => useUserActivity(idleTimeout, 2000));

    expect(result.current.status).toBe('online');

    act(() => {
      vi.advanceTimersByTime(idleTimeout);
    });

    expect(result.current.status).toBe('idle');
  });

  it('should transition to away after away timeout', () => {
    const idleTimeout = 1000;
    const awayTimeout = 2000;
    const { result } = renderHook(() => useUserActivity(idleTimeout, awayTimeout));

    act(() => {
      vi.advanceTimersByTime(awayTimeout);
    });

    expect(result.current.status).toBe('away');
  });

  it('should reset to online on user activity', () => {
    const idleTimeout = 1000;
    const { result } = renderHook(() => useUserActivity(idleTimeout, 2000));

    // Advance to idle
    act(() => {
      vi.advanceTimersByTime(idleTimeout);
    });

    expect(result.current.status).toBe('idle');

    // Simulate user activity
    act(() => {
      const event = new Event('mousedown');
      document.dispatchEvent(event);
    });

    expect(result.current.status).toBe('online');
  });

  it('should listen to multiple activity events', () => {
    const { result } = renderHook(() => useUserActivity(1000, 2000));

    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];

    events.forEach(eventType => {
      act(() => {
        const event = new Event(eventType);
        document.dispatchEvent(event);
      });

      expect(result.current.status).toBe('online');
    });
  });
});

describe('useCollaboration', () => {
  const mockSendMessage = vi.fn();
  const mockJoinPresenceChannel = vi.fn();
  const mockLeavePresenceChannel = vi.fn();
  const mockGetPresenceMembers = vi.fn(() => []);

  const createMockPusherContext = () => ({
    isConnected: true,
    connectionState: 'connected' as const,
    subscribeToChannel: vi.fn(),
    unsubscribeFromChannel: vi.fn(),
    sendMessage: mockSendMessage,
    on: vi.fn(),
    off: vi.fn(),
    joinPresenceChannel: mockJoinPresenceChannel,
    leavePresenceChannel: mockLeavePresenceChannel,
    getPresenceMembers: mockGetPresenceMembers,
    isInPresenceChannel: vi.fn(() => false),
    subscribe: vi.fn(),
    unsubscribe: vi.fn(),
    send: vi.fn(),
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
    mockJoinPresenceChannel.mockResolvedValue({ me: { id: 'test-user' } });
  });

  it('should join collaboration room', async () => {
    const mockContext = createMockPusherContext();
    const wrapper = createWrapper(mockContext);

    renderHook(() => useCollaboration('room-123', 'user-123'), { wrapper });

    await waitFor(() => {
      expect(mockJoinPresenceChannel).toHaveBeenCalledWith(
        'collaboration-room-123',
        expect.objectContaining({ name: 'user-123' })
      );
    });
  });

  it('should send cursor position', async () => {
    const mockContext = createMockPusherContext();
    const wrapper = createWrapper(mockContext);

    const { result } = renderHook(
      () => useCollaboration('room-123', 'user-123'),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isJoined).toBe(true);
    });

    act(() => {
      result.current.sendCursor(100, 200);
    });

    expect(mockSendMessage).toHaveBeenCalledWith(
      'cursor-move',
      { userId: 'user-123', x: 100, y: 200 },
      { channel: 'presence-collaboration-room-123' }
    );
  });

  it('should send selection update', async () => {
    const mockContext = createMockPusherContext();
    const wrapper = createWrapper(mockContext);

    const { result } = renderHook(
      () => useCollaboration('room-123', 'user-123'),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isJoined).toBe(true);
    });

    const selection = { start: 0, end: 10 };

    act(() => {
      result.current.sendSelection(selection);
    });

    expect(mockSendMessage).toHaveBeenCalledWith(
      'selection-update',
      { userId: 'user-123', selection },
      { channel: 'presence-collaboration-room-123' }
    );
  });

  it('should send typing indicator', async () => {
    const mockContext = createMockPusherContext();
    const wrapper = createWrapper(mockContext);

    const { result } = renderHook(
      () => useCollaboration('room-123', 'user-123'),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isJoined).toBe(true);
    });

    act(() => {
      result.current.sendTyping(true);
    });

    expect(mockSendMessage).toHaveBeenCalledWith(
      'user-typing',
      { userId: 'user-123', isTyping: true },
      { channel: 'presence-collaboration-room-123' }
    );
  });
});

describe('useOnlineStatus', () => {
  it('should initialize with current online status', () => {
    const { result } = renderHook(() => useOnlineStatus());

    expect(result.current).toBe(navigator.onLine);
  });

  it('should update when going online', () => {
    const { result } = renderHook(() => useOnlineStatus());

    act(() => {
      const event = new Event('online');
      window.dispatchEvent(event);
    });

    expect(result.current).toBe(true);
  });

  it('should update when going offline', () => {
    const { result } = renderHook(() => useOnlineStatus());

    act(() => {
      const event = new Event('offline');
      window.dispatchEvent(event);
    });

    expect(result.current).toBe(false);
  });

  it('should cleanup event listeners on unmount', () => {
    const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');

    const { unmount } = renderHook(() => useOnlineStatus());

    unmount();

    expect(removeEventListenerSpy).toHaveBeenCalledWith('online', expect.any(Function));
    expect(removeEventListenerSpy).toHaveBeenCalledWith('offline', expect.any(Function));
  });
});
