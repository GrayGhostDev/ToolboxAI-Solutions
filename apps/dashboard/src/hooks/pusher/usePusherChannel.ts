/**
 * React Hook for Pusher Channel Subscriptions
 *
 * Provides a declarative way to subscribe to Pusher channels
 * and handle events with automatic cleanup.
 */

import { useEffect, useCallback, useRef, useState } from 'react';
import { usePusherContext } from '../../contexts/PusherContext';
import {
  PusherChannelType,
  type PusherChannelOptions,
  type PusherEventHandler,
  type PusherConnectionState
} from '../../types/pusher';
import { logger } from '../../utils/logger';

export interface UsePusherChannelOptions extends PusherChannelOptions {
  enabled?: boolean;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Error) => void;
}

export interface UsePusherChannelReturn {
  isSubscribed: boolean;
  isConnected: boolean;
  connectionState: PusherConnectionState;
  subscribe: () => void;
  unsubscribe: () => void;
  bind: (event: string, handler: PusherEventHandler) => () => void;
  unbind: (event: string, handler?: PusherEventHandler) => void;
  trigger: (event: string, data: any) => Promise<void>;
}

/**
 * Hook for subscribing to a Pusher channel
 *
 * @param channelName - Name of the channel to subscribe to
 * @param eventHandlers - Object mapping event names to handler functions
 * @param options - Channel subscription options
 * @returns Channel subscription controls and state
 */
export function usePusherChannel(
  channelName: string,
  eventHandlers: Record<string, PusherEventHandler> = {},
  options: UsePusherChannelOptions = {}
): UsePusherChannelReturn {
  const {
    enabled = true,
    autoSubscribe = true,
    onConnect,
    onDisconnect,
    onError,
    ...channelOptions
  } = options;

  const {
    isConnected,
    connectionState,
    subscribeToChannel,
    unsubscribeFromChannel,
    sendMessage
  } = usePusherContext();

  const [isSubscribed, setIsSubscribed] = useState(false);
  const subscriptionIdRef = useRef<string | null>(null);
  const handlersRef = useRef<Map<string, Set<PusherEventHandler>>>(new Map());

  // Subscribe to channel
  const subscribe = useCallback(() => {
    if (!enabled || !isConnected || subscriptionIdRef.current) {
      return;
    }

    try {
      const subscriptionId = subscribeToChannel(
        channelName,
        eventHandlers,
        { autoSubscribe, ...channelOptions }
      );

      subscriptionIdRef.current = subscriptionId;
      setIsSubscribed(true);
      onConnect?.();

      logger.debug(`Subscribed to channel: ${channelName}`, { subscriptionId });
    } catch (error) {
      logger.error(`Failed to subscribe to channel ${channelName}:`, error);
      onError?.(error as Error);
    }
  }, [
    enabled,
    isConnected,
    channelName,
    eventHandlers,
    autoSubscribe,
    channelOptions,
    subscribeToChannel,
    onConnect,
    onError
  ]);

  // Unsubscribe from channel
  const unsubscribe = useCallback(() => {
    if (!subscriptionIdRef.current) {
      return;
    }

    try {
      unsubscribeFromChannel(subscriptionIdRef.current);
      subscriptionIdRef.current = null;
      setIsSubscribed(false);
      onDisconnect?.();

      logger.debug(`Unsubscribed from channel: ${channelName}`);
    } catch (error) {
      logger.error(`Failed to unsubscribe from channel ${channelName}:`, error);
      onError?.(error as Error);
    }
  }, [channelName, unsubscribeFromChannel, onDisconnect, onError]);

  // Bind event handler
  const bind = useCallback((event: string, handler: PusherEventHandler): (() => void) => {
    if (!handlersRef.current.has(event)) {
      handlersRef.current.set(event, new Set());
    }
    handlersRef.current.get(event)!.add(handler);

    // If already subscribed, update the subscription
    if (subscriptionIdRef.current && isSubscribed) {
      // Re-subscribe with updated handlers
      unsubscribe();
      subscribe();
    }

    // Return unbind function
    return () => unbind(event, handler);
  }, [isSubscribed, subscribe, unsubscribe]);

  // Unbind event handler
  const unbind = useCallback((event: string, handler?: PusherEventHandler) => {
    if (!handlersRef.current.has(event)) {
      return;
    }

    if (handler) {
      handlersRef.current.get(event)?.delete(handler);
      if (handlersRef.current.get(event)?.size === 0) {
        handlersRef.current.delete(event);
      }
    } else {
      handlersRef.current.delete(event);
    }

    // If subscribed, update the subscription
    if (subscriptionIdRef.current && isSubscribed) {
      // Re-subscribe with updated handlers
      unsubscribe();
      subscribe();
    }
  }, [isSubscribed, subscribe, unsubscribe]);

  // Trigger event on channel
  const trigger = useCallback(async (event: string, data: any) => {
    if (!isConnected) {
      throw new Error('Not connected to Pusher');
    }

    await sendMessage(event, data, { channel: channelName });
  }, [isConnected, channelName, sendMessage]);

  // Auto-subscribe when connected
  useEffect(() => {
    if (enabled && autoSubscribe && isConnected && !subscriptionIdRef.current) {
      subscribe();
    }

    return () => {
      if (subscriptionIdRef.current) {
        unsubscribe();
      }
    };
  }, [enabled, autoSubscribe, isConnected, subscribe, unsubscribe]);

  // Handle connection state changes
  useEffect(() => {
    if (!isConnected && subscriptionIdRef.current) {
      setIsSubscribed(false);
      onDisconnect?.();
    } else if (isConnected && !subscriptionIdRef.current && autoSubscribe && enabled) {
      subscribe();
    }
  }, [isConnected, autoSubscribe, enabled, subscribe, onDisconnect]);

  return {
    isSubscribed,
    isConnected,
    connectionState,
    subscribe,
    unsubscribe,
    bind,
    unbind,
    trigger
  };
}

/**
 * Hook for subscribing to a private Pusher channel
 *
 * @param channelName - Name of the private channel (without 'private-' prefix)
 * @param eventHandlers - Event handlers for the channel
 * @param options - Channel options
 */
export function usePrivateChannel(
  channelName: string,
  eventHandlers: Record<string, PusherEventHandler> = {},
  options: UsePusherChannelOptions = {}
) {
  return usePusherChannel(
    `private-${channelName}`,
    eventHandlers,
    options
  );
}

/**
 * Hook for subscribing to a presence Pusher channel
 *
 * @param channelName - Name of the presence channel (without 'presence-' prefix)
 * @param eventHandlers - Event handlers for the channel
 * @param options - Channel options
 */
export function usePresenceChannel(
  channelName: string,
  eventHandlers: Record<string, PusherEventHandler> = {},
  options: UsePusherChannelOptions = {}
) {
  const { joinPresenceChannel, leavePresenceChannel, getPresenceMembers } = usePusherContext();
  const [members, setMembers] = useState<any[]>([]);

  const channelReturn = usePusherChannel(
    `presence-${channelName}`,
    {
      ...eventHandlers,
      'pusher:member_added': (member) => {
        setMembers(prev => [...prev, member]);
        eventHandlers['pusher:member_added']?.(member);
      },
      'pusher:member_removed': (member) => {
        setMembers(prev => prev.filter(m => m.id !== member.id));
        eventHandlers['pusher:member_removed']?.(member);
      }
    },
    options
  );

  // Get current members when subscribed
  useEffect(() => {
    if (channelReturn.isSubscribed) {
      const currentMembers = getPresenceMembers(`presence-${channelName}`);
      setMembers(currentMembers);
    }
  }, [channelReturn.isSubscribed, channelName, getPresenceMembers]);

  return {
    ...channelReturn,
    members
  };
}

export default usePusherChannel;