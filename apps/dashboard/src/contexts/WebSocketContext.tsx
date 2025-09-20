/**
 * WebSocket Context Provider for ToolboxAI Dashboard
 *
 * Provides WebSocket functionality throughout the React application
 * with automatic connection management and state synchronization.
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
import { AUTH_TOKEN_KEY, DEBUG_MODE, ENABLE_WEBSOCKET, WS_URL } from '../config';
import { pusherService as websocketService } from '../services/pusher';
import { useAppDispatch, useAppSelector } from '../store';
import { addNotification } from '../store/slices/uiSlice';
import { logger } from '../utils/logger';
import {
  CollaborationMessage,
  ContentGenerationProgress,
  ContentGenerationRequest,
  ProgressUpdate,
  QuizMessage,
  RobloxEventMessage,
  SystemNotification,
  WebSocketChannel,
  WebSocketError,
  WebSocketEventHandler,
  WebSocketMessage,
  WebSocketMessageType,
  WebSocketState,
  WebSocketStats,
} from '../types/websocket';

// Context value interface
interface WebSocketContextValue {
  // Connection state
  state: WebSocketState;
  isConnected: boolean;
  stats: WebSocketStats;
  error: WebSocketError | null;

  // Connection management
  connect: (token?: string) => Promise<void>;
  disconnect: (reason?: string) => void;
  reconnect: () => Promise<void>;

  // Messaging
  sendMessage: <T = any>(
    type: WebSocketMessageType,
    payload?: T,
    options?: {
      channel?: string;
      awaitAcknowledgment?: boolean;
      timeout?: number;
    }
  ) => Promise<any>;

  // Subscriptions
  subscribe: (
    channel: string | WebSocketChannel,
    handler: WebSocketEventHandler,
    filter?: (message: WebSocketMessage) => boolean
  ) => string;
  unsubscribe: (subscriptionId: string) => void;

  // Event handlers
  on: (type: WebSocketMessageType | string, handler: WebSocketEventHandler) => () => void;
  once: (type: WebSocketMessageType | string, handler: WebSocketEventHandler) => void;

  // Content generation
  requestContent: (request: ContentGenerationRequest) => Promise<void>;
  onContentProgress: (handler: (progress: ContentGenerationProgress) => void) => () => void;

  // Quiz handling
  sendQuizResponse: (response: QuizMessage) => Promise<void>;
  onQuizFeedback: (handler: (feedback: any) => void) => () => void;

  // Progress tracking
  updateProgress: (progress: ProgressUpdate) => Promise<void>;
  onProgressUpdate: (handler: (progress: ProgressUpdate) => void) => () => void;

  // Collaboration
  sendCollaborationMessage: (message: CollaborationMessage) => Promise<void>;
  onCollaborationEvent: (handler: (message: CollaborationMessage) => void) => () => void;

  // Roblox events
  onRobloxEvent: (handler: (event: RobloxEventMessage) => void) => () => void;

  // System notifications
  onSystemNotification: (handler: (notification: SystemNotification) => void) => () => void;
}

// Create context with default values
const WebSocketContext = createContext<WebSocketContextValue | undefined>(undefined);

// Provider props
interface WebSocketProviderProps {
  children: React.ReactNode;
  url?: string;
  autoConnect?: boolean;
  debug?: boolean;
}

/**
 * WebSocket Provider Component
 */
export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({
  children,
  url = WS_URL,
  autoConnect = true,
  debug = DEBUG_MODE,
}) => {
  const dispatch = useAppDispatch();
  const authToken = useAppSelector((state) => state.user.token);
  const userId = useAppSelector((state) => state.user.userId);

  // State
  const [state, setState] = useState<WebSocketState>(WebSocketState.DISCONNECTED);
  const [stats, setStats] = useState<WebSocketStats>(websocketService.getStats());
  const [error, setError] = useState<WebSocketError | null>(null);

  // Refs for cleanup
  const cleanupFunctions = useRef<Set<() => void>>(new Set());
  const isConnecting = useRef(false);

  // Connection management functions - defined early to avoid circular dependencies
  const connectFunc = useCallback(
    async (token?: string) => {
      if (isConnecting.current) return;

      try {
        isConnecting.current = true;
        // Get token from localStorage first, then fallback to Redux store, then provided token
        const currentToken = token || localStorage.getItem(AUTH_TOKEN_KEY) || authToken;
        logger.debug('WebSocket connecting', {
          hasToken: !!currentToken,
          tokenPrefix: currentToken ? `${currentToken.substring(0, 20)}...` : null
        });
        await websocketService.connect(currentToken);
      } finally {
        isConnecting.current = false;
      }
    },
    [authToken]
  );

  const disconnectFunc = useCallback((reason?: string) => {
    websocketService.disconnect(reason);
  }, []);

  // Create stable references
  const connect = connectFunc;
  const disconnect = disconnectFunc;

  // Handle user-specific messages
  const handleUserMessage = useCallback(
    (message: WebSocketMessage) => {
      // Dispatch to Redux for state management
      dispatch({
        type: 'websocket/messageReceived',
        payload: message,
      });

      // Handle specific message types
      switch (message.type) {
        case WebSocketMessageType.SYSTEM_NOTIFICATION: {
          const notification = message.payload as SystemNotification;
          dispatch(
            addNotification({
              type:
                notification.level === 'error'
                  ? 'error'
                  : notification.level === 'warning'
                  ? 'warning'
                  : notification.level === 'success'
                  ? 'success'
                  : 'info',
              message: `${notification.title}: ${notification.message}`,
              autoHide: notification.dismissible,
            })
          );
          break;
        }

        case WebSocketMessageType.PROGRESS_UPDATE:
          // Update progress state
          dispatch({
            type: 'progress/updated',
            payload: message.payload,
          });
          break;

        case WebSocketMessageType.QUIZ_FEEDBACK:
          // Update quiz state
          dispatch({
            type: 'assessments/feedbackReceived',
            payload: message.payload,
          });
          break;

        default:
          if (debug) {
            // Sanitize message for logging
            const safeMessage = {
              ...message,
              payload: message.payload ? '[PAYLOAD_SANITIZED]' : undefined,
            };
            logger.debug('WebSocket user message', safeMessage);
          }
      }
    },
    [dispatch, debug]
  );

  // Initialize WebSocket service
  useEffect(() => {
    if (!ENABLE_WEBSOCKET) {
      logger.info('WebSocket disabled by configuration');
      return;
    }

    // Configure WebSocket service
    const service = websocketService;

    // Set up state change handler
    const unsubscribeState = service.onStateChange((newState, previousState) => {
      setState(newState);
      setStats(service.getStats());

      // Dispatch Redux action for state change
      dispatch({
        type: 'websocket/stateChanged',
        payload: { state: newState, previousState },
      });

      // Show notification for connection events
      if (newState === WebSocketState.CONNECTED) {
        dispatch(
          addNotification({
            type: 'success',
            message: 'Real-time connection established',
            autoHide: true,
          })
        );
      } else if (
        newState === WebSocketState.DISCONNECTED &&
        previousState === WebSocketState.CONNECTED
      ) {
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
    const unsubscribeError = service.onError((wsError) => {
      setError(wsError);

      // Only show user-friendly error messages
      let userMessage = 'Connection issue occurred';
      if (wsError.code === 'CONNECTION_FAILED') {
        userMessage = 'Unable to connect to server. Please check your internet connection.';
      } else if (wsError.code === 'CONNECTION_TIMEOUT') {
        userMessage = 'Connection timed out. Retrying...';
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

    // Auto-connect if enabled and authenticated
    const currentToken = localStorage.getItem(AUTH_TOKEN_KEY) || authToken;
    if (autoConnect && currentToken && !isConnecting.current) {
      isConnecting.current = true;
      logger.debug('WebSocket auto-connecting', {
        tokenPrefix: currentToken.substring(0, 20)
      });
      service
        .connect(currentToken)
        .then(() => {
          isConnecting.current = false;
          logger.info('WebSocket successfully connected');
          // Subscribe to user-specific channel
          if (userId) {
            service.subscribe(`user_${userId}`, (message) => {
              handleUserMessage(message);
            });
          }
          // Reset error state on successful connection
          setError(null);
        })
        .catch((error) => {
          isConnecting.current = false;

          // Sanitize error message for logging
          const sanitizedError = String(error.message || error)
            .replace(/[\n\r]/g, '')
            .substring(0, 200);
          logger.error('Failed to connect WebSocket', { error: sanitizedError });

          // Set error state but don't show notification here (handled by error handler)
          setError({
            code: 'CONNECTION_FAILED',
            message: sanitizedError,
            timestamp: new Date().toISOString(),
            recoverable: true,
          });
        });
    }

    // Cleanup function
    return () => {
      cleanupFunctions.current.forEach((fn) => fn());
      cleanupFunctions.current.clear();
    };
  }, [authToken, userId, autoConnect, dispatch, handleUserMessage]);

  // Handle authentication changes - moved before handleTokenRefresh
  useEffect(() => {
    if (!ENABLE_WEBSOCKET) return;

    const currentToken = localStorage.getItem(AUTH_TOKEN_KEY) || authToken;

    if (currentToken && state === WebSocketState.DISCONNECTED && !isConnecting.current) {
      // Reconnect with new token
      logger.debug('WebSocket token detected, reconnecting');
      connectFunc(currentToken);
    } else if (!currentToken && state === WebSocketState.CONNECTED) {
      // Disconnect if logged out
      logger.debug('WebSocket no token detected, disconnecting');
      disconnectFunc('User logged out');
    }
  }, [authToken, state, connectFunc, disconnectFunc]);

  // Update stats periodically
  useEffect(() => {
    if (!ENABLE_WEBSOCKET) return;

    const interval = setInterval(() => {
      if (state === WebSocketState.CONNECTED) {
        setStats(websocketService.getStats());
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [state]);

  const reconnect = useCallback(async () => {
    disconnectFunc('Manual reconnection');
    await new Promise((resolve) => setTimeout(resolve, 100));
    await connectFunc();
  }, [connectFunc, disconnectFunc]);

  // Messaging functions
  const sendMessage = useCallback(
    <T = any,>(
      type: WebSocketMessageType,
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

  // Token refresh handler - defined after sendMessage
  const handleTokenRefresh = useCallback(async () => {
    const currentToken = localStorage.getItem(AUTH_TOKEN_KEY) || authToken;
    if (!currentToken) {
      logger.warn('WebSocket no token available for refresh');
      return;
    }

    try {
      logger.debug('WebSocket attempting manual token refresh');
      // Use the websocket service's refresh method
      await websocketService.refreshTokenAndReconnect();
      logger.info('WebSocket token refresh successful');
    } catch (error) {
      logger.error('WebSocket failed to refresh token', error);
      // Disconnect and attempt to reconnect
      disconnectFunc('Token refresh failed');
      setTimeout(() => connectFunc(), 1000);
    }
  }, [authToken, disconnectFunc, connectFunc]);

  // Set up token refresh monitoring
  useEffect(() => {
    if (!ENABLE_WEBSOCKET) return;

    const currentToken = localStorage.getItem(AUTH_TOKEN_KEY) || authToken;
    if (!currentToken) return;

    const unsubscribe = websocketService.on('token_expired', () => {
      logger.warn('WebSocket token expired event received');
      handleTokenRefresh();
    });

    return unsubscribe;
  }, [handleTokenRefresh, authToken]);

  // Subscription functions
  const subscribe = useCallback(
    (
      channel: string | WebSocketChannel,
      handler: WebSocketEventHandler,
      filter?: (message: WebSocketMessage) => boolean
    ) => {
      const subscriptionId = websocketService.subscribe(channel, handler, filter);
      cleanupFunctions.current.add(() => websocketService.unsubscribe(subscriptionId));
      return subscriptionId;
    },
    []
  );

  const unsubscribe = useCallback((subscriptionId: string) => {
    websocketService.unsubscribe(subscriptionId);
  }, []);

  // Event handler functions
  const on = useCallback(
    (type: WebSocketMessageType | string, handler: WebSocketEventHandler): (() => void) => {
      websocketService.on(type, handler);
      const cleanup = () => websocketService.off(type, handler);
      cleanupFunctions.current.add(cleanup);
      return cleanup;
    },
    []
  );

  const once = useCallback(
    (type: WebSocketMessageType | string, handler: WebSocketEventHandler) => {
      const wrappedHandler: WebSocketEventHandler = (data) => {
        handler(data);
        websocketService.off(type, wrappedHandler);
      };
      websocketService.on(type, wrappedHandler);
    },
    []
  );

  // Content generation functions
  const requestContent = useCallback(
    async (request: ContentGenerationRequest) => {
      await sendMessage(WebSocketMessageType.CONTENT_REQUEST, request, {
        channel: WebSocketChannel.CONTENT_UPDATES,
        awaitAcknowledgment: true,
        timeout: 10000,
      });
    },
    [sendMessage]
  );

  const onContentProgress = useCallback(
    (handler: (progress: ContentGenerationProgress) => void): (() => void) => {
      return on(WebSocketMessageType.CONTENT_PROGRESS, handler);
    },
    [on]
  );

  // Quiz functions
  const sendQuizResponse = useCallback(
    async (response: QuizMessage) => {
      await sendMessage(WebSocketMessageType.QUIZ_RESPONSE, response, {
        channel: WebSocketChannel.QUIZ_EVENTS,
        awaitAcknowledgment: true,
        timeout: 5000,
      });
    },
    [sendMessage]
  );

  const onQuizFeedback = useCallback(
    (handler: (feedback: any) => void): (() => void) => {
      return on(WebSocketMessageType.QUIZ_FEEDBACK, handler);
    },
    [on]
  );

  // Progress tracking functions
  const updateProgress = useCallback(
    async (progress: ProgressUpdate) => {
      await sendMessage(WebSocketMessageType.PROGRESS_UPDATE, progress, {
        channel: WebSocketChannel.STUDENT_UPDATES,
        awaitAcknowledgment: true,
        timeout: 5000,
      });
    },
    [sendMessage]
  );

  const onProgressUpdate = useCallback(
    (handler: (progress: ProgressUpdate) => void): (() => void) => {
      return on(WebSocketMessageType.PROGRESS_UPDATE, handler);
    },
    [on]
  );

  // Collaboration functions
  const sendCollaborationMessage = useCallback(
    async (message: CollaborationMessage) => {
      await sendMessage(WebSocketMessageType.USER_MESSAGE, message, {
        channel: `collaboration_${message.roomId}`,
        awaitAcknowledgment: false,
      });
    },
    [sendMessage]
  );

  const onCollaborationEvent = useCallback(
    (handler: (message: CollaborationMessage) => void): (() => void) => {
      return on(WebSocketMessageType.USER_MESSAGE, handler);
    },
    [on]
  );

  // Roblox event handler
  const onRobloxEvent = useCallback(
    (handler: (event: RobloxEventMessage) => void): (() => void) => {
      return on(WebSocketMessageType.ROBLOX_EVENT, handler);
    },
    [on]
  );

  // System notification handler
  const onSystemNotification = useCallback(
    (handler: (notification: SystemNotification) => void): (() => void) => {
      return on(WebSocketMessageType.SYSTEM_NOTIFICATION, handler);
    },
    [on]
  );

  // Create memoized context value
  const contextValue = useMemo<WebSocketContextValue>(
    () => ({
      // State
      state,
      isConnected: state === WebSocketState.CONNECTED,
      stats,
      error,

      // Connection management
      connect,
      disconnect,
      reconnect,

      // Messaging
      sendMessage,

      // Subscriptions
      subscribe,
      unsubscribe,

      // Event handlers
      on,
      once,

      // Feature-specific functions
      requestContent,
      onContentProgress,
      sendQuizResponse,
      onQuizFeedback,
      updateProgress,
      onProgressUpdate,
      sendCollaborationMessage,
      onCollaborationEvent,
      onRobloxEvent,
      onSystemNotification,
    }),
    [
      state,
      stats,
      error,
      connect,
      disconnect,
      reconnect,
      sendMessage,
      subscribe,
      unsubscribe,
      on,
      once,
      requestContent,
      onContentProgress,
      sendQuizResponse,
      onQuizFeedback,
      updateProgress,
      onProgressUpdate,
      sendCollaborationMessage,
      onCollaborationEvent,
      onRobloxEvent,
      onSystemNotification,
    ]
  );

  return <WebSocketContext.Provider value={contextValue}>{children}</WebSocketContext.Provider>;
};

/**
 * Hook to use WebSocket context
 */
export const useWebSocketContext = (): WebSocketContextValue => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within WebSocketProvider');
  }
  return context;
};

// Export context for direct use in custom hooks
export { WebSocketContext };

// Export convenience hooks
export const useWebSocketState = () => {
  const { state, isConnected, stats, error } = useWebSocketContext();
  return { state, isConnected, stats, error };
};

export const useWebSocketConnection = () => {
  const { connect, disconnect, reconnect } = useWebSocketContext();
  return { connect, disconnect, reconnect };
};

export const useWebSocketMessaging = () => {
  const { sendMessage, on, once } = useWebSocketContext();
  return { sendMessage, on, once };
};

export const useWebSocketSubscription = () => {
  const { subscribe, unsubscribe } = useWebSocketContext();
  return { subscribe, unsubscribe };
};
