/**
 * Pusher Context Provider for ToolboxAI Dashboard
 *
 * Provides comprehensive Pusher functionality throughout the React application
 * with enhanced features including presence channels, authentication state,
 * connection monitoring, and active channel tracking.
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { Channel, PresenceChannel } from 'pusher-js';

import { pusherService as websocketService } from '../services/pusher';
import { useAppDispatch, useAppSelector } from '../store';
import { addNotification } from '../store/slices/uiSlice';
import { logger } from '../utils/logger';

import {
  PusherChannelType,
  PusherChannels,
  PusherConnectionState,
  PusherEventHandler,
  PusherMember,
  PusherMessage,
  PusherPresenceChannelData,
  PusherServiceState,
  PusherSubscription,
  formatChannelName,
  isPusherMember,
  isPresenceChannel
} from '../types/pusher';

import {
  WebSocketState,
  WebSocketStats,
  WebSocketError,
  WebSocketMessage,
  WebSocketMessageType
} from '../types/websocket';

import { AUTH_TOKEN_KEY, DEBUG_MODE, ENABLE_WEBSOCKET } from '../config';

// Context value interface
interface PusherContextValue {
  // Connection state
  connectionState: PusherConnectionState;
  isConnected: boolean;
  isConnecting: boolean;
  isAuthenticated: boolean;
  stats: WebSocketStats;
  error: WebSocketError | null;

  // Service management
  connect: (token?: string) => Promise<void>;
  disconnect: (reason?: string) => void;
  reconnect: () => Promise<void>;

  // Channel management
  subscribeToChannel: (
    channelName: string,
    eventHandlers: Record<string, PusherEventHandler>,
    options?: {
      channelType?: PusherChannelType;
      autoSubscribe?: boolean;
    }
  ) => string;
  unsubscribeFromChannel: (subscriptionId: string) => void;
  getActiveChannels: () => string[];
  isChannelSubscribed: (channelName: string) => boolean;

  // Presence channels
  joinPresenceChannel: (
    channelName: string,
    userInfo: PusherPresenceChannelData['user_info']
  ) => Promise<PresenceChannel>;
  leavePresenceChannel: (channelName: string) => void;
  getPresenceMembers: (channelName: string) => PusherMember[];
  isInPresenceChannel: (channelName: string) => boolean;

  // Event handling
  on: (eventType: string, handler: PusherEventHandler) => () => void;
  off: (eventType: string, handler: PusherEventHandler) => void;
  emit: (eventType: string, data: any, channel?: string) => Promise<void>;

  // Authentication
  updateAuthToken: (token: string) => Promise<void>;
  refreshAuth: () => Promise<void>;

  // Utility functions
  sendMessage: <T = any>(
    type: WebSocketMessageType | string,
    payload?: T,
    options?: {
      channel?: string;
      awaitAcknowledgment?: boolean;
      timeout?: number;
    }
  ) => Promise<any>;

  // Feature-specific helpers
  subscribeToContentGeneration: (onProgress: (data: any) => void) => () => void;
  subscribeToUserNotifications: (onNotification: (data: any) => void) => () => void;
  subscribeToSystemEvents: (onEvent: (data: any) => void) => () => void;
  triggerContentRequest: (request: any) => Promise<void>;
  sendUserNotification: (userId: string, notification: any) => Promise<void>;
}

// Create context with default values
const PusherContext = createContext<PusherContextValue | undefined>(undefined);

// Provider props
interface PusherProviderProps {
  children: React.ReactNode;
  autoConnect?: boolean;
  enablePresence?: boolean;
  debug?: boolean;
  onConnectionChange?: (state: PusherConnectionState) => void;
  onError?: (error: WebSocketError) => void;
}

/**
 * Pusher Provider Component
 */
export const PusherProvider: React.FunctionComponent<PusherProviderProps> = ({
  children,
  autoConnect = true,
  enablePresence = true,
  debug = DEBUG_MODE,
  onConnectionChange,
  onError,
}) => {
  const dispatch = useAppDispatch();
  const authToken = useAppSelector((state) => state.user.token);
  const userId = useAppSelector((state) => state.user.userId);

  // State management
  const [connectionState, setConnectionState] = useState<PusherConnectionState>(
    PusherConnectionState.DISCONNECTED
  );
  const [stats, setStats] = useState<WebSocketStats>(websocketService.getStats());
  const [error, setError] = useState<WebSocketError | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [activeChannels, setActiveChannels] = useState<Set<string>>(new Set());
  const [presenceChannels, setPresenceChannels] = useState<Map<string, PresenceChannel>>(new Map());
  const [presenceMembers, setPresenceMembers] = useState<Map<string, PusherMember[]>>(new Map());

  // Refs for cleanup
  const subscriptionsRef = useRef<Map<string, PusherSubscription>>(new Map());
  const cleanupFunctions = useRef<Set<() => void>>(new Set());
  const isConnecting = useRef(false);

  // Connection management
  const connectFunc = useCallback(
    async (token?: string) => {
      if (isConnecting.current || connectionState === PusherConnectionState.CONNECTED) {
        return;
      }

      try {
        isConnecting.current = true;
        setConnectionState(PusherConnectionState.CONNECTING);

        const currentToken = token || localStorage.getItem(AUTH_TOKEN_KEY) || authToken;

        if (debug) {
          logger.debug('Pusher connecting', {
            hasToken: !!currentToken,
            tokenPrefix: currentToken ? `${currentToken.substring(0, 20)}...` : null
          });
        }

        await websocketService.connect(currentToken);
        setConnectionState(PusherConnectionState.CONNECTED);
        setIsAuthenticated(!!currentToken);
        setError(null);

        onConnectionChange?.(PusherConnectionState.CONNECTED);

        // Show success notification
        dispatch(
          addNotification({
            type: 'success',
            message: 'Real-time connection established',
            autoHide: true,
          })
        );

      } catch (error) {
        setConnectionState(PusherConnectionState.FAILED);
        const wsError: WebSocketError = {
          code: 'CONNECTION_FAILED',
          message: error instanceof Error ? error.message : 'Connection failed',
          timestamp: new Date().toISOString(),
          recoverable: true,
        };
        setError(wsError);
        onError?.(wsError);

        dispatch(
          addNotification({
            type: 'error',
            message: 'Failed to establish real-time connection',
            autoHide: true,
          })
        );
      } finally {
        isConnecting.current = false;
      }
    },
    [authToken, debug, dispatch, onConnectionChange, onError, connectionState]
  );

  const disconnectFunc = useCallback((reason?: string) => {
    setConnectionState(PusherConnectionState.DISCONNECTED);
    setIsAuthenticated(false);
    setActiveChannels(new Set());
    setPresenceChannels(new Map());
    setPresenceMembers(new Map());

    websocketService.disconnect(reason);

    if (debug) {
      logger.debug('Pusher disconnected:', reason);
    }

    onConnectionChange?.(PusherConnectionState.DISCONNECTED);
  }, [debug, onConnectionChange]);

  const reconnectFunc = useCallback(async () => {
    disconnectFunc('Manual reconnection');
    await new Promise(resolve => setTimeout(resolve, 100));
    await connectFunc();
  }, [connectFunc, disconnectFunc]);

  // Initialize service
  useEffect(() => {
    if (!ENABLE_WEBSOCKET) {
      logger.info('Pusher disabled by configuration');
      return;
    }

    // Set up state change handler
    const unsubscribeState = websocketService.onStateChange((newState, previousState) => {
      const pusherState = mapWebSocketStateToPusher(newState);
      setConnectionState(pusherState);
      setStats(websocketService.getStats());

      if (debug) {
        logger.debug('Pusher state changed:', { newState, previousState, pusherState });
      }

      onConnectionChange?.(pusherState);

      // Handle disconnection notifications
      if (newState === WebSocketState.DISCONNECTED && previousState === WebSocketState.CONNECTED) {
        dispatch(
          addNotification({
            type: 'warning',
            message: 'Real-time connection lost. Attempting to reconnect...',
            autoHide: true,
          })
        );
      }
    });

    cleanupFunctions.current.add(unsubscribeState);

    // Set up error handler
    const unsubscribeError = websocketService.onError((wsError) => {
      setError(wsError);
      onError?.(wsError);

      // Show user-friendly error messages
      let userMessage = 'Connection issue occurred';
      if (wsError.code === 'CONNECTION_FAILED') {
        userMessage = 'Unable to connect to server. Please check your internet connection.';
      } else if (wsError.code === 'AUTH_FAILED') {
        userMessage = 'Authentication failed. Please log in again.';
      }

      dispatch(
        addNotification({
          type: 'error',
          message: userMessage,
          autoHide: true,
        })
      );
    });

    cleanupFunctions.current.add(unsubscribeError);

    // Auto-connect if enabled
    if (autoConnect) {
      const currentToken = localStorage.getItem(AUTH_TOKEN_KEY) || authToken;
      if (currentToken) {
        connectFunc(currentToken);
      }
    }

    // Cleanup function
    return () => {
      cleanupFunctions.current.forEach((fn) => fn());
      cleanupFunctions.current.clear();
    };
  }, [authToken, autoConnect, debug, dispatch, onConnectionChange, onError, connectFunc]);

  // Channel management functions
  const subscribeToChannel = useCallback(
    (
      channelName: string,
      eventHandlers: Record<string, PusherEventHandler>,
      options: {
        channelType?: PusherChannelType;
        autoSubscribe?: boolean;
      } = {}
    ): string => {
      const { channelType = PusherChannelType.PUBLIC, autoSubscribe = true } = options;
      const formattedChannelName = formatChannelName(channelName, channelType);
      const subscriptionId = `${formattedChannelName}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

      if (autoSubscribe && connectionState === PusherConnectionState.CONNECTED) {
        try {
          const subscriptionIds: string[] = [];

          Object.entries(eventHandlers).forEach(([eventType, handler]) => {
            const wsSubscriptionId = websocketService.subscribe(formattedChannelName, (message) => {
              if (message.type === eventType) {
                handler(message.payload, { channel: formattedChannelName, event: eventType });
              }
            });
            subscriptionIds.push(wsSubscriptionId);
          });

          // Store subscription info
          const subscription: PusherSubscription = {
            id: subscriptionId,
            channel: formattedChannelName,
            channelType,
            eventHandlers: new Map(Object.entries(eventHandlers).map(([event, handler]) => [event, new Set([handler])])),
            options: { autoSubscribe },
            isSubscribed: true
          };

          subscriptionsRef.current.set(subscriptionId, subscription);
          setActiveChannels(prev => new Set([...prev, formattedChannelName]));

          if (debug) {
            logger.debug(`Subscribed to channel: ${formattedChannelName}`);
          }

        } catch (error) {
          logger.error(`Failed to subscribe to channel ${formattedChannelName}:`, error);
        }
      }

      return subscriptionId;
    },
    [connectionState, debug]
  );

  const unsubscribeFromChannel = useCallback((subscriptionId: string) => {
    const subscription = subscriptionsRef.current.get(subscriptionId);
    if (subscription) {
      // Unsubscribe from websocket service
      websocketService.unsubscribe(subscriptionId);
      
      // Remove from our tracking
      subscriptionsRef.current.delete(subscriptionId);
      setActiveChannels(prev => {
        const updated = new Set(prev);
        updated.delete(subscription.channel);
        return updated;
      });

      if (debug) {
        logger.debug(`Unsubscribed from channel: ${subscription.channel}`);
      }
    }
  }, [debug]);

  // Presence channel functions
  const joinPresenceChannel = useCallback(
    async (
      channelName: string,
      userInfo: PusherPresenceChannelData['user_info']
    ): Promise<PresenceChannel> => {
      if (!enablePresence) {
        throw new Error('Presence channels are disabled');
      }

      const formattedChannelName = formatChannelName(channelName, PusherChannelType.PRESENCE);
      
      // This is a simplified implementation
      // In a real implementation, you would integrate with the underlying Pusher instance
      // to create and manage presence channels
      
      if (debug) {
        logger.debug(`Joining presence channel: ${formattedChannelName}`, userInfo);
      }

      // Mock presence channel for now
      const mockPresenceChannel = {} as PresenceChannel;
      setPresenceChannels(prev => new Map([...prev, [formattedChannelName, mockPresenceChannel]]));
      
      return mockPresenceChannel;
    },
    [enablePresence, debug]
  );

  const leavePresenceChannel = useCallback((channelName: string) => {
    const formattedChannelName = formatChannelName(channelName, PusherChannelType.PRESENCE);
    setPresenceChannels(prev => {
      const updated = new Map(prev);
      updated.delete(formattedChannelName);
      return updated;
    });
    setPresenceMembers(prev => {
      const updated = new Map(prev);
      updated.delete(formattedChannelName);
      return updated;
    });

    if (debug) {
      logger.debug(`Left presence channel: ${formattedChannelName}`);
    }
  }, [debug]);

  // Event handling
  const on = useCallback((eventType: string, handler: PusherEventHandler): (() => void) => {
    websocketService.on(eventType, handler);
    return () => websocketService.off(eventType, handler);
  }, []);

  const off = useCallback((eventType: string, handler: PusherEventHandler) => {
    websocketService.off(eventType, handler);
  }, []);

  const emit = useCallback(async (eventType: string, data: any, channel?: string) => {
    await websocketService.send(eventType, data, { channel });
  }, []);

  // Message sending
  const sendMessage = useCallback(
    async <T = any>(
      type: WebSocketMessageType | string,
      payload?: T,
      options?: {
        channel?: string;
        awaitAcknowledgment?: boolean;
        timeout?: number;
      }
    ) => {
      return websocketService.send(type, payload, options);
    },
    []
  );

  // Authentication functions
  const updateAuthToken = useCallback(async (token: string) => {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
    setIsAuthenticated(true);
    
    if (connectionState === PusherConnectionState.CONNECTED) {
      await websocketService.refreshToken(token);
    }
  }, [connectionState]);

  const refreshAuth = useCallback(async () => {
    await websocketService.refreshTokenAndReconnect();
  }, []);

  // Feature-specific helper functions
  const subscribeToContentGeneration = useCallback((onProgress: (data: any) => void): (() => void) => {
    return on(WebSocketMessageType.CONTENT_PROGRESS, onProgress);
  }, [on]);

  const subscribeToUserNotifications = useCallback((onNotification: (data: any) => void): (() => void) => {
    if (userId) {
      const subscriptionId = subscribeToChannel(`user-${userId}`, {
        [WebSocketMessageType.SYSTEM_NOTIFICATION]: onNotification
      }, { channelType: PusherChannelType.PRIVATE });
      
      return () => unsubscribeFromChannel(subscriptionId);
    }
    return () => {};
  }, [subscribeToChannel, unsubscribeFromChannel, userId]);

  const subscribeToSystemEvents = useCallback((onEvent: (data: any) => void): (() => void) => {
    const subscriptionId = subscribeToChannel(PusherChannels.SYSTEM_ANNOUNCEMENTS, {
      [WebSocketMessageType.SYSTEM_NOTIFICATION]: onEvent,
      [WebSocketMessageType.SYSTEM_ALERT]: onEvent
    });
    
    return () => unsubscribeFromChannel(subscriptionId);
  }, [subscribeToChannel, unsubscribeFromChannel]);

  const triggerContentRequest = useCallback(async (request: any) => {
    await sendMessage(WebSocketMessageType.CONTENT_REQUEST, request, {
      channel: PusherChannels.CONTENT_GENERATION,
      awaitAcknowledgment: true
    });
  }, [sendMessage]);

  const sendUserNotification = useCallback(async (userId: string, notification: any) => {
    await sendMessage(WebSocketMessageType.SYSTEM_NOTIFICATION, notification, {
      channel: `private-user-${userId}`
    });
  }, [sendMessage]);

  // Utility functions
  const getActiveChannels = useCallback(() => Array.from(activeChannels), [activeChannels]);
  const isChannelSubscribed = useCallback((channelName: string) => activeChannels.has(channelName), [activeChannels]);
  const getPresenceMembers = useCallback((channelName: string) => presenceMembers.get(channelName) || [], [presenceMembers]);
  const isInPresenceChannel = useCallback((channelName: string) => presenceChannels.has(channelName), [presenceChannels]);

  // Create memoized context value
  const contextValue = useMemo<PusherContextValue>(
    () => ({
      // State
      connectionState,
      isConnected: connectionState === PusherConnectionState.CONNECTED,
      isConnecting: connectionState === PusherConnectionState.CONNECTING,
      isAuthenticated,
      stats,
      error,

      // Connection management
      connect: connectFunc,
      disconnect: disconnectFunc,
      reconnect: reconnectFunc,

      // Channel management
      subscribeToChannel,
      unsubscribeFromChannel,
      getActiveChannels,
      isChannelSubscribed,

      // Presence channels
      joinPresenceChannel,
      leavePresenceChannel,
      getPresenceMembers,
      isInPresenceChannel,

      // Event handling
      on,
      off,
      emit,

      // Authentication
      updateAuthToken,
      refreshAuth,

      // Messaging
      sendMessage,

      // Feature-specific helpers
      subscribeToContentGeneration,
      subscribeToUserNotifications,
      subscribeToSystemEvents,
      triggerContentRequest,
      sendUserNotification,
    }),
    [
      connectionState,
      isAuthenticated,
      stats,
      error,
      connectFunc,
      disconnectFunc,
      reconnectFunc,
      subscribeToChannel,
      unsubscribeFromChannel,
      getActiveChannels,
      isChannelSubscribed,
      joinPresenceChannel,
      leavePresenceChannel,
      getPresenceMembers,
      isInPresenceChannel,
      on,
      off,
      emit,
      updateAuthToken,
      refreshAuth,
      sendMessage,
      subscribeToContentGeneration,
      subscribeToUserNotifications,
      subscribeToSystemEvents,
      triggerContentRequest,
      sendUserNotification,
    ]
  );

  return <PusherContext.Provider value={contextValue}>{children}</PusherContext.Provider>;
};

/**
 * Hook to use Pusher context
 */
export const usePusherContext = (): PusherContextValue => {
  const context = useContext(PusherContext);
  if (!context) {
    throw new Error('usePusherContext must be used within PusherProvider');
  }
  return context;
};

// Export context for direct use
export { PusherContext };

// Convenience hooks
export const usePusherState = () => {
  const { connectionState, isConnected, isConnecting, isAuthenticated, stats, error } = usePusherContext();
  return { connectionState, isConnected, isConnecting, isAuthenticated, stats, error };
};

export const usePusherChannels = () => {
  const {
    subscribeToChannel,
    unsubscribeFromChannel,
    getActiveChannels,
    isChannelSubscribed
  } = usePusherContext();
  return {
    subscribeToChannel,
    unsubscribeFromChannel,
    getActiveChannels,
    isChannelSubscribed
  };
};

export const usePusherPresenceChannels = () => {
  const {
    joinPresenceChannel,
    leavePresenceChannel,
    getPresenceMembers,
    isInPresenceChannel
  } = usePusherContext();
  return {
    joinPresenceChannel,
    leavePresenceChannel,
    getPresenceMembers,
    isInPresenceChannel
  };
};

export const usePusherMessaging = () => {
  const { sendMessage, on, off, emit } = usePusherContext();
  return { sendMessage, on, off, emit };
};

// Helper function to map WebSocket states to Pusher states
function mapWebSocketStateToPusher(wsState: WebSocketState): PusherConnectionState {
  switch (wsState) {
    case WebSocketState.CONNECTING:
      return PusherConnectionState.CONNECTING;
    case WebSocketState.CONNECTED:
      return PusherConnectionState.CONNECTED;
    case WebSocketState.DISCONNECTING:
    case WebSocketState.DISCONNECTED:
      return PusherConnectionState.DISCONNECTED;
    case WebSocketState.RECONNECTING:
      return PusherConnectionState.CONNECTING;
    case WebSocketState.ERROR:
      return PusherConnectionState.FAILED;
    default:
      return PusherConnectionState.DISCONNECTED;
  }
}