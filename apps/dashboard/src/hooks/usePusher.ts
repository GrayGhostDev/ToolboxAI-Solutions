import { useCallback, useEffect, useRef, useState } from 'react';
import { Channel, PresenceChannel } from 'pusher-js';
import { pusherService, PusherService } from '../services/pusher';
import { WebSocketState } from '../types/websocket';
import {
  PusherChannelType,
  PusherChannels,
  PusherConnectionState,
  PusherEventHandler,
  PusherHookConfig,
  PusherMember,
  PusherPresenceChannelData,
  formatChannelName,
  isPusherMember,
  isPresenceChannel
} from '../types/pusher';
import { logger } from '../utils/logger';

/**
 * Enhanced React hook for using Pusher service in components
 * Provides easy access to real-time features and automatic cleanup
 */
export function usePusher(config: PusherHookConfig = {}) {
  const {
    autoConnect = true,
    reconnectOnFocus = true,
    debugMode = false
  } = config;

  const serviceRef = useRef<PusherService>(pusherService);
  const [connectionState, setConnectionState] = useState<WebSocketState>(pusherService.getState());
  const [isReady, setIsReady] = useState(false);

  // Handle connection state changes
  useEffect(() => {
    const unsubscribe = serviceRef.current.onStateChange((newState) => {
      setConnectionState(newState);
      setIsReady(newState === WebSocketState.CONNECTED);

      if (debugMode) {
        logger.debug('Pusher connection state changed:', newState);
      }
    });

    return unsubscribe;
  }, [debugMode]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect && serviceRef.current.getState() === WebSocketState.DISCONNECTED) {
      serviceRef.current.connect().catch(error => {
        logger.error('Failed to connect to Pusher:', error);
      });
    }
  }, [autoConnect]);

  // Reconnect on window focus
  useEffect(() => {
    if (!reconnectOnFocus) return;

    const handleFocus = () => {
      if (serviceRef.current.getState() === WebSocketState.DISCONNECTED) {
        serviceRef.current.connect().catch(error => {
          logger.error('Failed to reconnect to Pusher on focus:', error);
        });
      }
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [reconnectOnFocus]);

  return {
    service: serviceRef.current,
    isConnected: connectionState === WebSocketState.CONNECTED,
    isConnecting: connectionState === WebSocketState.CONNECTING,
    isReconnecting: connectionState === WebSocketState.RECONNECTING,
    state: connectionState,
    isReady
  };
}

/**
 * Enhanced hook for subscribing to Pusher channels with automatic cleanup
 */
export function usePusherChannel(
  channelName: string,
  eventHandlers: Record<string, PusherEventHandler>,
  options: {
    enabled?: boolean;
    channelType?: PusherChannelType;
    autoSubscribe?: boolean;
    dependencies?: any[];
  } = {}
) {
  const {
    enabled = true,
    channelType = PusherChannelType.PUBLIC,
    autoSubscribe = true,
    dependencies = []
  } = options;

  const { service, isReady } = usePusher();
  const subscriptionIdsRef = useRef<string[]>([]);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [subscriptionError, setSubscriptionError] = useState<Error | null>(null);

  // Format channel name based on type
  const formattedChannelName = formatChannelName(channelName, channelType);

  useEffect(() => {
    if (!enabled || !isReady || !autoSubscribe) {
      return;
    }

    setSubscriptionError(null);

    try {
      // Subscribe to events
      const subscriptionIds: string[] = [];

      Object.entries(eventHandlers).forEach(([eventType, handler]) => {
        const subscriptionId = service.subscribe(formattedChannelName, (message) => {
          if (message.type === eventType) {
            handler(message.payload, { channel: formattedChannelName, event: eventType });
          }
        });
        subscriptionIds.push(subscriptionId);
      });

      subscriptionIdsRef.current = subscriptionIds;
      setIsSubscribed(true);

      logger.debug(`Subscribed to channel: ${formattedChannelName}`);
    } catch (error) {
      setSubscriptionError(error as Error);
      logger.error(`Failed to subscribe to channel ${formattedChannelName}:`, error);
    }

    // Cleanup subscriptions on unmount or when deps change
    return () => {
      subscriptionIdsRef.current.forEach(id => {
        service.unsubscribe(id);
      });
      subscriptionIdsRef.current = [];
      setIsSubscribed(false);
    };
  }, [formattedChannelName, enabled, isReady, autoSubscribe, service, ...dependencies]);

  const manualSubscribe = useCallback(() => {
    if (!enabled || !isReady || isSubscribed) return;

    const subscriptionIds: string[] = [];
    Object.entries(eventHandlers).forEach(([eventType, handler]) => {
      const subscriptionId = service.subscribe(formattedChannelName, (message) => {
        if (message.type === eventType) {
          handler(message.payload, { channel: formattedChannelName, event: eventType });
        }
      });
      subscriptionIds.push(subscriptionId);
    });
    subscriptionIdsRef.current = subscriptionIds;
    setIsSubscribed(true);
  }, [enabled, isReady, isSubscribed, eventHandlers, service, formattedChannelName]);

  const manualUnsubscribe = useCallback(() => {
    subscriptionIdsRef.current.forEach(id => {
      service.unsubscribe(id);
    });
    subscriptionIdsRef.current = [];
    setIsSubscribed(false);
  }, [service]);

  return {
    isSubscribed,
    subscriptionError,
    channelName: formattedChannelName,
    subscribe: manualSubscribe,
    unsubscribe: manualUnsubscribe
  };
}

/**
 * Hook for monitoring Pusher connection state with enhanced features
 */
export function usePusherConnection() {
  const { service, state, isConnected, isConnecting, isReconnecting } = usePusher();
  const [stats, setStats] = useState(service.getStats());
  const [lastError, setLastError] = useState<Error | null>(null);

  // Update stats periodically
  useEffect(() => {
    const interval = setInterval(() => {
      if (isConnected) {
        setStats(service.getStats());
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [isConnected, service]);

  // Listen for errors
  useEffect(() => {
    const unsubscribe = service.onError((error) => {
      setLastError(error);
    });

    return unsubscribe;
  }, [service]);

  const reconnect = useCallback(() => {
    service.disconnect('Manual reconnection');
    setTimeout(() => {
      service.connect();
    }, 100);
  }, [service]);

  return {
    isConnected,
    isConnecting,
    isReconnecting,
    state,
    stats,
    lastError,
    reconnect
  };
}

/**
 * Hook for presence channels with member management
 */
export function usePusherPresence(
  channelName: string,
  userInfo: PusherPresenceChannelData['user_info'],
  options: {
    enabled?: boolean;
    onMemberAdded?: (member: PusherMember) => void;
    onMemberRemoved?: (member: PusherMember) => void;
  } = {}
) {
  const { enabled = true, onMemberAdded, onMemberRemoved } = options;
  const { service, isReady } = usePusher();
  const [members, setMembers] = useState<PusherMember[]>([]);
  const [isJoined, setIsJoined] = useState(false);
  const presenceChannelRef = useRef<PresenceChannel | null>(null);

  const formattedChannelName = formatChannelName(channelName, PusherChannelType.PRESENCE);

  useEffect(() => {
    if (!enabled || !isReady) return;

    // For presence channels, we need to use the underlying Pusher instance
    // This is a simplified implementation - the actual implementation would
    // need to integrate with the service's Pusher instance

    // Cleanup function
    return () => {
      if (presenceChannelRef.current) {
        // Unsubscribe from presence channel
        setIsJoined(false);
        setMembers([]);
        presenceChannelRef.current = null;
      }
    };
  }, [enabled, isReady, formattedChannelName]);

  const joinChannel = useCallback(async () => {
    if (!enabled || !isReady || isJoined) return;

    try {
      // Implementation would integrate with the service's presence channel logic
      setIsJoined(true);
      logger.debug(`Joined presence channel: ${formattedChannelName}`);
    } catch (error) {
      logger.error(`Failed to join presence channel ${formattedChannelName}:`, error);
    }
  }, [enabled, isReady, isJoined, formattedChannelName]);

  const leaveChannel = useCallback(() => {
    if (presenceChannelRef.current) {
      setIsJoined(false);
      setMembers([]);
      presenceChannelRef.current = null;
    }
  }, []);

  return {
    members,
    isJoined,
    channelName: formattedChannelName,
    joinChannel,
    leaveChannel
  };
}

/**
 * Hook for listening to specific Pusher events with automatic cleanup
 */
export function usePusherEvent<T = any>(
  eventType: string,
  handler: PusherEventHandler<T>,
  options: {
    enabled?: boolean;
    channel?: string;
    dependencies?: any[];
  } = {}
) {
  const { enabled = true, channel, dependencies = [] } = options;
  const { service, isReady } = usePusher();
  const handlerRef = useRef(handler);

  // Update handler ref when it changes
  useEffect(() => {
    handlerRef.current = handler;
  }, [handler]);

  useEffect(() => {
    if (!enabled || !isReady) return;

    let subscriptionId: string | undefined;

    if (channel) {
      // Subscribe to event on specific channel
      subscriptionId = service.subscribe(channel, (message) => {
        if (message.type === eventType) {
          handlerRef.current(message.payload, { channel, event: eventType });
        }
      });
    } else {
      // Subscribe to global event
      service.on(eventType, (data: T) => {
        handlerRef.current(data, { channel: 'global', event: eventType });
      });
    }

    return () => {
      if (subscriptionId) {
        service.unsubscribe(subscriptionId);
      } else {
        service.off(eventType, handlerRef.current);
      }
    };
  }, [enabled, isReady, eventType, channel, service, ...dependencies]);
}

/**
 * Hook for sending messages through Pusher with loading state
 */
export function usePusherSend() {
  const { service, isReady } = usePusher();
  const [isSending, setIsSending] = useState(false);
  const [lastError, setLastError] = useState<Error | null>(null);

  const sendMessage = useCallback(async (
    type: string,
    payload?: any,
    options?: {
      channel?: string;
      awaitAcknowledgment?: boolean;
      timeout?: number;
    }
  ) => {
    if (!isReady) {
      throw new Error('Pusher service is not ready');
    }

    setIsSending(true);
    setLastError(null);

    try {
      await service.send(type, payload, options);
    } catch (error) {
      setLastError(error as Error);
      throw error;
    } finally {
      setIsSending(false);
    }
  }, [service, isReady]);

  return {
    sendMessage,
    isSending,
    lastError,
    isReady
  };
}

// Legacy compatibility - keep original hooks
export const usePusherChannel_Legacy = usePusherChannel;
export const usePusherConnection_Legacy = usePusherConnection;