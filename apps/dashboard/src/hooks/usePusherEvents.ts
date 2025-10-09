/**
 * React Hooks for Pusher Events
 * Custom hooks for managing Pusher subscriptions and events in React components
 * @module usePusherEvents
 * @version 1.0.0
 * @since 2025-09-26
 */

import { useEffect, useCallback, useRef, useState, useMemo } from 'react';
import { pusherClient } from '../services/pusher-client';
import { useSelector } from 'react-redux';
import { type RootState } from '../store';

// Types
export interface PusherEventOptions {
  enabled?: boolean;
  dependencies?: any[];
  onError?: (error: Error) => void;
}

export interface PusherPresenceState {
  count: number;
  members: Map<string, any>;
  myId?: string;
}

/**
 * Hook to initialize Pusher client
 */
export const usePusherClient = () => {
  // Fix: Changed from state.auth to state.user as auth slice doesn't exist
  // Defensive: Safe fallback for Redux state access
  const user = useSelector((state: RootState) => state?.user || null);
  const token = user?.token || null;
  const [isInitialized, setIsInitialized] = useState(false);
  const [connectionState, setConnectionState] = useState<string>('uninitialized');

  useEffect(() => {
    // Defensive: Check for valid user data before initializing
    if (user?.id && token && typeof user.id === 'string' && typeof token === 'string') {
      try {
        pusherClient.initialize(user.id, token);
        setIsInitialized(true);
      } catch (error) {
        console.error('Failed to initialize Pusher:', error);
        setIsInitialized(false);
      }
    } else {
      // Defensive: Reset initialization state if user data is invalid
      setIsInitialized(false);
    }

    return () => {
      // Don't disconnect on unmount as other components might be using it
      // pusherClient.disconnect();
    };
  }, [user?.id, token]);

  useEffect(() => {
    const interval = setInterval(() => {
      try {
        // Defensive: Safely get connection state with fallback
        const state = pusherClient?.getConnectionState?.() || 'unknown';
        setConnectionState(state);
      } catch (error) {
        console.error('Error getting Pusher connection state:', error);
        setConnectionState('error');
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return {
    client: pusherClient,
    isInitialized,
    connectionState,
    // Defensive: Safely check connection with fallback
    isConnected: pusherClient?.isConnected?.() || false,
  };
};

/**
 * Hook to subscribe to a Pusher channel and event
 */
export const usePusherEvent = <T = any>(
  channelName: string,
  eventName: string,
  callback: (data: T) => void,
  options: PusherEventOptions = {}
) => {
  const { enabled = true, dependencies = [], onError } = options;
  const callbackRef = useRef(callback);
  const { isInitialized } = usePusherClient();

  // Update callback ref when it changes
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    // Defensive: Validate all required parameters
    if (!enabled || !isInitialized || !channelName || !eventName ||
        typeof channelName !== 'string' || typeof eventName !== 'string') {
      return;
    }

    // Wrapped callback to use the latest version
    const wrappedCallback = (data: T) => {
      try {
        // Defensive: Check if callback ref is still valid
        if (typeof callbackRef.current === 'function') {
          callbackRef.current(data);
        }
      } catch (error) {
        console.error(`Error in Pusher event handler for ${eventName}:`, error);
        onError?.(error as Error);
      }
    };

    try {
      // Subscribe to channel
      const channel = pusherClient?.subscribe?.(channelName);

      if (channel && pusherClient?.bind) {
        // Bind event
        pusherClient.bind(channelName, eventName, wrappedCallback);

        console.log(`📡 Subscribed to ${channelName}:${eventName}`);
      }
    } catch (error) {
      console.error(`Failed to subscribe to ${channelName}:${eventName}:`, error);
      onError?.(error as Error);
    }

    // Cleanup
    return () => {
      try {
        // Defensive: Safely cleanup subscriptions
        pusherClient?.unbind?.(channelName, eventName, wrappedCallback);
        pusherClient?.unsubscribe?.(channelName);
        console.log(`🔌 Unsubscribed from ${channelName}:${eventName}`);
      } catch (error) {
        console.error(`Error during cleanup for ${channelName}:${eventName}:`, error);
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [channelName, eventName, enabled, isInitialized, dependencies]);
};

/**
 * Hook to subscribe to multiple events on a channel
 */
export const usePusherChannel = <T extends Record<string, any>>(
  channelName: string,
  events: { [K in keyof T]: (data: T[K]) => void },
  options: PusherEventOptions = {}
) => {
  const { enabled = true, dependencies = [], onError } = options;
  const eventsRef = useRef(events);
  const { isInitialized } = usePusherClient();

  // Update events ref when it changes
  useEffect(() => {
    eventsRef.current = events;
  }, [events]);

  useEffect(() => {
    if (!enabled || !isInitialized || !channelName) {
      return;
    }

    const wrappedCallbacks = new Map<string, (data: unknown) => void>();

    try {
      // Subscribe to channel
      const channel = pusherClient.subscribe(channelName);

      if (channel) {
        // Bind all events
        Object.entries(eventsRef.current).forEach(([eventName, callback]) => {
          const wrappedCallback = (data: unknown) => {
            try {
              (callback as (payload: unknown) => void)(data);
            } catch (error) {
              console.error(`Error in handler for ${eventName}:`, error);
              onError?.(error as Error);
            }
          };

          wrappedCallbacks.set(eventName, wrappedCallback);
          pusherClient.bind(channelName, eventName, wrappedCallback);
        });

        console.log(`📡 Subscribed to channel ${channelName} with ${wrappedCallbacks.size} events`);
      }
    } catch (error) {
      console.error(`Failed to subscribe to channel ${channelName}:`, error);
      onError?.(error as Error);
    }

    // Cleanup
    return () => {
      try {
        wrappedCallbacks.forEach((callback, eventName) => {
          pusherClient.unbind(channelName, eventName, callback);
        });
        pusherClient.unsubscribe(channelName);
        console.log(`🔌 Unsubscribed from channel ${channelName}`);
      } catch (error) {
        console.error(`Error during cleanup for channel ${channelName}:`, error);
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [channelName, enabled, isInitialized, dependencies]);
};

/**
 * Hook for presence channels
 */
export const usePusherPresence = (
  channelName: string,
  options: PusherEventOptions = {}
): PusherPresenceState => {
  const [presenceState, setPresenceState] = useState<PusherPresenceState>({
    count: 0,
    members: new Map(),
  });

  const handleMemberAdded = useCallback((member: any) => {
    setPresenceState(prev => {
      const newMembers = new Map(prev.members);
      newMembers.set(member.id, member.info);
      return {
        ...prev,
        count: newMembers.size,
        members: newMembers,
      };
    });
  }, []);

  const handleMemberRemoved = useCallback((member: any) => {
    setPresenceState(prev => {
      const newMembers = new Map(prev.members);
      newMembers.delete(member.id);
      return {
        ...prev,
        count: newMembers.size,
        members: newMembers,
      };
    });
  }, []);

  const handleSubscriptionSucceeded = useCallback((members: any) => {
    const memberMap = new Map();

    if (members.members) {
      Object.entries(members.members).forEach(([id, info]) => {
        memberMap.set(id, info);
      });
    }

    setPresenceState({
      count: memberMap.size,
      members: memberMap,
      myId: members.myID,
    });
  }, []);

  // Use the channel hook with presence events
  usePusherChannel(
    channelName,
    {
      'pusher:subscription_succeeded': handleSubscriptionSucceeded,
      'pusher:member_added': handleMemberAdded,
      'pusher:member_removed': handleMemberRemoved,
    },
    options
  );

  return presenceState;
};

/**
 * Hook to trigger client events
 */
export const usePusherTrigger = (channelName: string) => {
  const { isInitialized } = usePusherClient();

  const trigger = useCallback(
    (eventName: string, data: any) => {
      if (!isInitialized) {
        console.warn('Cannot trigger event: Pusher not initialized');
        return;
      }

      if (!eventName.startsWith('client-')) {
        console.warn('Client events must be prefixed with "client-"');
        return;
      }

      try {
        pusherClient.trigger(channelName, eventName, data);
      } catch (error) {
        console.error(`Failed to trigger event ${eventName}:`, error);
      }
    },
    [channelName, isInitialized]
  );

  return trigger;
};

/**
 * Hook for connection status
 */
export const usePusherConnectionStatus = () => {
  const [status, setStatus] = useState({
    state: 'uninitialized',
    isConnected: false,
    isPolling: false,
  });

  useEffect(() => {
    const interval = setInterval(() => {
      try {
        // Defensive: Safely get debug info and connection state
        const debugInfo = pusherClient?.getDebugInfo?.() || {};
        const connectionState = pusherClient?.getConnectionState?.() || 'unknown';
        const isConnected = pusherClient?.isConnected?.() || false;

        setStatus({
          state: connectionState,
          isConnected,
          isPolling: debugInfo?.fallbackToPolling || false,
        });
      } catch (error) {
        console.error('Error getting Pusher connection status:', error);
        setStatus({
          state: 'error',
          isConnected: false,
          isPolling: false,
        });
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return status;
};

/**
 * Hook for auto-reconnect with exponential backoff
 */
export const usePusherAutoReconnect = (
  maxAttempts: number = 5,
  baseDelay: number = 1000
) => {
  const [attempts, setAttempts] = useState(0);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const { connectionState } = usePusherClient();

  useEffect(() => {
    if (connectionState === 'disconnected' && attempts < maxAttempts) {
      setIsReconnecting(true);
      const delay = baseDelay * Math.pow(2, attempts);

      const timeout = setTimeout(() => {
        setAttempts(prev => prev + 1);
        // Pusher client handles reconnection internally
      }, delay);

      return () => clearTimeout(timeout);
    } else if (connectionState === 'connected') {
      setAttempts(0);
      setIsReconnecting(false);
    }
  }, [connectionState, attempts, maxAttempts, baseDelay]);

  return { attempts, isReconnecting, maxAttempts };
};

/**
 * Hook for subscribing to typed events with TypeScript support
 */
export function useTypedPusherEvent<T extends Record<string, any>>(
  channelName: string,
  eventName: keyof T,
  callback: (data: T[keyof T]) => void,
  options: PusherEventOptions = {}
) {
  return usePusherEvent(
    channelName,
    String(eventName),
    callback,
    options
  );
}

/**
 * Hook for batched event processing
 */
export const usePusherBatchedEvents = <T = any>(
  channelName: string,
  eventName: string,
  processor: (batch: T[]) => void,
  batchSize: number = 10,
  batchTimeout: number = 1000,
  options: PusherEventOptions = {}
) => {
  const batchRef = useRef<T[]>([]);
  const timeoutRef = useRef<NodeJS.Timeout>();

  const processBatch = useCallback(() => {
    if (batchRef.current.length > 0) {
      processor([...batchRef.current]);
      batchRef.current = [];
    }
  }, [processor]);

  const handleEvent = useCallback((data: T) => {
    batchRef.current.push(data);

    // Clear existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Process batch if size reached
    if (batchRef.current.length >= batchSize) {
      processBatch();
    } else {
      // Set timeout for batch processing
      timeoutRef.current = setTimeout(processBatch, batchTimeout);
    }
  }, [batchSize, batchTimeout, processBatch]);

  // Subscribe to event
  usePusherEvent(channelName, eventName, handleEvent, options);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      processBatch(); // Process any remaining items
    };
  }, [processBatch]);
};

// Export all hooks
export default {
  usePusherClient,
  usePusherEvent,
  usePusherChannel,
  usePusherPresence,
  usePusherTrigger,
  usePusherConnectionStatus,
  usePusherAutoReconnect,
  useTypedPusherEvent,
  usePusherBatchedEvents,
};
