/**
 * React Hooks for Pusher Presence Features
 *
 * Provides hooks for managing user presence, online status,
 * and real-time collaboration features.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { usePusherContext } from '../../contexts/PusherContext';
import { PusherMember, PusherPresenceChannelData } from '../../types/pusher';
import { logger } from '../../utils/logger';

export interface UsePresenceOptions {
  enabled?: boolean;
  userInfo?: PusherPresenceChannelData['user_info'];
  onMemberJoin?: (member: PusherMember) => void;
  onMemberLeave?: (member: PusherMember) => void;
  onError?: (error: Error) => void;
}

export interface UsePresenceReturn {
  members: PusherMember[];
  myId: string | null;
  isJoined: boolean;
  join: () => Promise<void>;
  leave: () => void;
  updateStatus: (status: 'online' | 'away' | 'busy') => void;
  getMember: (id: string) => PusherMember | undefined;
  onlineCount: number;
}

/**
 * Hook for managing presence in a Pusher presence channel
 *
 * @param channelName - Name of the presence channel (without prefix)
 * @param options - Presence options
 * @returns Presence state and controls
 */
export function usePusherPresence(
  channelName: string,
  options: UsePresenceOptions = {}
): UsePresenceReturn {
  const {
    enabled = true,
    userInfo,
    onMemberJoin,
    onMemberLeave,
    onError
  } = options;

  const {
    joinPresenceChannel,
    leavePresenceChannel,
    getPresenceMembers,
    isInPresenceChannel
  } = usePusherContext();

  const [members, setMembers] = useState<PusherMember[]>([]);
  const [myId, setMyId] = useState<string | null>(null);
  const [isJoined, setIsJoined] = useState(false);
  const channelRef = useRef<any>(null);

  // Join presence channel
  const join = useCallback(async () => {
    if (!enabled || isJoined) {
      return;
    }

    try {
      const channel = await joinPresenceChannel(channelName, userInfo || {
        name: 'Anonymous User',
        status: 'online'
      });

      channelRef.current = channel;
      setIsJoined(true);

      // Get initial members
      const currentMembers = getPresenceMembers(channelName);
      setMembers(currentMembers);

      // Set my ID if available
      if ('me' in channel && channel.me) {
        setMyId(channel.me.id);
      }

      logger.debug(`Joined presence channel: ${channelName}`, { members: currentMembers });
    } catch (error) {
      logger.error(`Failed to join presence channel ${channelName}:`, error);
      onError?.(error as Error);
    }
  }, [enabled, isJoined, channelName, userInfo, joinPresenceChannel, getPresenceMembers, onError]);

  // Leave presence channel
  const leave = useCallback(() => {
    if (!isJoined) {
      return;
    }

    try {
      leavePresenceChannel(channelName);
      setIsJoined(false);
      setMembers([]);
      setMyId(null);
      channelRef.current = null;

      logger.debug(`Left presence channel: ${channelName}`);
    } catch (error) {
      logger.error(`Failed to leave presence channel ${channelName}:`, error);
      onError?.(error as Error);
    }
  }, [isJoined, channelName, leavePresenceChannel, onError]);

  // Update user status
  const updateStatus = useCallback((status: 'online' | 'away' | 'busy') => {
    if (!isJoined || !myId) {
      return;
    }

    // This would typically trigger a server-side update
    logger.debug(`Updating status to ${status} for user ${myId}`);

    // Update local member list
    setMembers(prev => prev.map(member =>
      member.id === myId
        ? { ...member, info: { ...member.info, status } }
        : member
    ));
  }, [isJoined, myId]);

  // Get specific member
  const getMember = useCallback((id: string) => {
    return members.find(member => member.id === id);
  }, [members]);

  // Auto-join when enabled
  useEffect(() => {
    if (enabled && !isJoined) {
      join();
    }

    return () => {
      if (isJoined) {
        leave();
      }
    };
  }, [enabled]); // Intentionally limited deps to prevent re-joining

  // Update members when channel membership changes
  useEffect(() => {
    if (!isJoined) {
      return;
    }

    const checkInterval = setInterval(() => {
      const currentMembers = getPresenceMembers(channelName);

      // Check for new members
      currentMembers.forEach(member => {
        const existingMember = members.find(m => m.id === member.id);
        if (!existingMember) {
          onMemberJoin?.(member);
        }
      });

      // Check for left members
      members.forEach(member => {
        const stillPresent = currentMembers.find(m => m.id === member.id);
        if (!stillPresent) {
          onMemberLeave?.(member);
        }
      });

      setMembers(currentMembers);
    }, 1000); // Check every second

    return () => clearInterval(checkInterval);
  }, [isJoined, channelName, members, getPresenceMembers, onMemberJoin, onMemberLeave]);

  return {
    members,
    myId,
    isJoined,
    join,
    leave,
    updateStatus,
    getMember,
    onlineCount: members.filter(m => m.info.status === 'online').length
  };
}

/**
 * Hook for tracking user activity and idle state
 *
 * @param idleTimeout - Time in ms before user is considered idle (default: 5 minutes)
 * @param awayTimeout - Time in ms before user is considered away (default: 15 minutes)
 */
export function useUserActivity(
  idleTimeout = 5 * 60 * 1000,
  awayTimeout = 15 * 60 * 1000
) {
  const [status, setStatus] = useState<'online' | 'idle' | 'away'>('online');
  const [lastActivity, setLastActivity] = useState(Date.now());
  const timeoutRef = useRef<NodeJS.Timeout>();

  const resetActivity = useCallback(() => {
    setLastActivity(Date.now());
    setStatus('online');

    // Clear existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Set idle timeout
    timeoutRef.current = setTimeout(() => {
      setStatus('idle');

      // Set away timeout
      timeoutRef.current = setTimeout(() => {
        setStatus('away');
      }, awayTimeout - idleTimeout);
    }, idleTimeout);
  }, [idleTimeout, awayTimeout]);

  useEffect(() => {
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];

    events.forEach(event => {
      document.addEventListener(event, resetActivity, true);
    });

    // Initial activity
    resetActivity();

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, resetActivity, true);
      });

      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [resetActivity]);

  return { status, lastActivity };
}

/**
 * Hook for real-time collaboration features
 *
 * @param roomId - ID of the collaboration room
 * @param userId - ID of the current user
 */
export function useCollaboration(roomId: string, userId: string) {
  const [collaborators, setCollaborators] = useState<Map<string, any>>(new Map());
  const [cursors, setCursors] = useState<Map<string, { x: number; y: number }>>(new Map());
  const [selections, setSelections] = useState<Map<string, any>>(new Map());

  const presence = usePusherPresence(`collaboration-${roomId}`, {
    userInfo: { name: userId, status: 'online' }
  });

  const { sendMessage } = usePusherContext();

  // Send cursor position
  const sendCursor = useCallback((x: number, y: number) => {
    sendMessage('cursor-move', { userId, x, y }, {
      channel: `presence-collaboration-${roomId}`
    });
  }, [userId, roomId, sendMessage]);

  // Send selection
  const sendSelection = useCallback((selection: any) => {
    sendMessage('selection-update', { userId, selection }, {
      channel: `presence-collaboration-${roomId}`
    });
  }, [userId, roomId, sendMessage]);

  // Send typing indicator
  const sendTyping = useCallback((isTyping: boolean) => {
    sendMessage('user-typing', { userId, isTyping }, {
      channel: `presence-collaboration-${roomId}`
    });
  }, [userId, roomId, sendMessage]);

  return {
    ...presence,
    collaborators,
    cursors,
    selections,
    sendCursor,
    sendSelection,
    sendTyping
  };
}

/**
 * Hook for managing online/offline status
 */
export function useOnlineStatus() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      logger.info('Network connection restored');
    };

    const handleOffline = () => {
      setIsOnline(false);
      logger.warn('Network connection lost');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}

export default usePusherPresence;