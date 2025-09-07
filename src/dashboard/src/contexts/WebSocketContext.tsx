/**
 * WebSocket Context Provider for ToolboxAI Dashboard
 * 
 * Provides WebSocket functionality throughout the React application
 * with automatic connection management and state synchronization.
 */

import React, { createContext, useContext, useEffect, useState, useCallback, useRef, useMemo } from 'react';
import { useAppDispatch, useAppSelector } from '../store';
import { websocketService, WebSocketService } from '../services/websocket';
import {
  WebSocketState,
  WebSocketMessage,
  WebSocketMessageType,
  WebSocketError,
  WebSocketStats,
  WebSocketEventHandler,
  WebSocketChannel,
  ContentGenerationRequest,
  ContentGenerationProgress,
  QuizMessage,
  ProgressUpdate,
  CollaborationMessage,
  RobloxEventMessage,
  SystemNotification
} from '../types/websocket';
import { addNotification } from '../store/slices/uiSlice';
import { ENABLE_WEBSOCKET, WS_URL, DEBUG_MODE } from '../config';

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
  debug = DEBUG_MODE
}) => {
  const dispatch = useAppDispatch();
  const authToken = useAppSelector(state => state.user.token);
  const userId = useAppSelector(state => state.user.userId);
  
  // State
  const [state, setState] = useState<WebSocketState>(WebSocketState.DISCONNECTED);
  const [stats, setStats] = useState<WebSocketStats>(websocketService.getStats());
  const [error, setError] = useState<WebSocketError | null>(null);
  
  // Refs for cleanup
  const cleanupFunctions = useRef<Set<() => void>>(new Set());
  const isConnecting = useRef(false);
  
  // Initialize WebSocket service
  useEffect(() => {
    if (!ENABLE_WEBSOCKET) {
      console.log('WebSocket disabled by configuration');
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
        payload: { state: newState, previousState }
      });
      
      // Show notification for connection events
      if (newState === WebSocketState.CONNECTED) {
        dispatch(addNotification({
          type: 'success',
          message: 'Real-time connection established',
          autoHide: true
        }));
      } else if (newState === WebSocketState.DISCONNECTED && previousState === WebSocketState.CONNECTED) {
        dispatch(addNotification({
          type: 'warning',
          message: 'Real-time connection lost. Attempting to reconnect...',
          autoHide: true
        }));
      }
    });
    
    cleanupFunctions.current.add(unsubscribeState);
    
    // Set up error handler
    const unsubscribeError = service.onError((wsError) => {
      setError(wsError);
      dispatch(addNotification({
        type: 'error',
        message: `Connection error: ${wsError.message}`,
        autoHide: true
      }));
    });
    
    cleanupFunctions.current.add(unsubscribeError);
    
    // Auto-connect if enabled and authenticated
    if (autoConnect && authToken && !isConnecting.current) {
      isConnecting.current = true;
      service.connect(authToken)
        .then(() => {
          isConnecting.current = false;
          // Subscribe to user-specific channel
          if (userId) {
            service.subscribe(`user_${userId}`, (message) => {
              handleUserMessage(message);
            });
          }
        })
        .catch((error) => {
          isConnecting.current = false;
          console.error('Failed to connect WebSocket:', error);
        });
    }
    
    // Cleanup function
    return () => {
      cleanupFunctions.current.forEach(fn => fn());
      cleanupFunctions.current.clear();
    };
  }, [authToken, userId, autoConnect, dispatch]);
  
  // Handle authentication changes
  useEffect(() => {
    if (!ENABLE_WEBSOCKET) return;
    
    if (authToken && state === WebSocketState.DISCONNECTED && !isConnecting.current) {
      // Reconnect with new token
      connect(authToken);
    } else if (!authToken && state === WebSocketState.CONNECTED) {
      // Disconnect if logged out
      disconnect('User logged out');
    }
  }, [authToken]);
  
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
  
  // Connection management functions
  const connect = useCallback(async (token?: string) => {
    if (isConnecting.current) return;
    
    try {
      isConnecting.current = true;
      await websocketService.connect(token || authToken);
    } finally {
      isConnecting.current = false;
    }
  }, [authToken]);
  
  const disconnect = useCallback((reason?: string) => {
    websocketService.disconnect(reason);
  }, []);
  
  const reconnect = useCallback(async () => {
    disconnect('Manual reconnection');
    await new Promise(resolve => setTimeout(resolve, 100));
    await connect();
  }, [connect, disconnect]);
  
  // Messaging functions
  const sendMessage = useCallback(<T = any>(
    type: WebSocketMessageType,
    payload?: T,
    options?: {
      channel?: string;
      awaitAcknowledgment?: boolean;
      timeout?: number;
    }
  ) => {
    return websocketService.send(type, payload, options);
  }, []);
  
  // Subscription functions
  const subscribe = useCallback((
    channel: string | WebSocketChannel,
    handler: WebSocketEventHandler,
    filter?: (message: WebSocketMessage) => boolean
  ) => {
    const subscriptionId = websocketService.subscribe(channel, handler, filter);
    cleanupFunctions.current.add(() => websocketService.unsubscribe(subscriptionId));
    return subscriptionId;
  }, []);
  
  const unsubscribe = useCallback((subscriptionId: string) => {
    websocketService.unsubscribe(subscriptionId);
  }, []);
  
  // Event handler functions
  const on = useCallback((
    type: WebSocketMessageType | string,
    handler: WebSocketEventHandler
  ): (() => void) => {
    websocketService.on(type, handler);
    const cleanup = () => websocketService.off(type, handler);
    cleanupFunctions.current.add(cleanup);
    return cleanup;
  }, []);
  
  const once = useCallback((
    type: WebSocketMessageType | string,
    handler: WebSocketEventHandler
  ) => {
    const wrappedHandler: WebSocketEventHandler = (data) => {
      handler(data);
      websocketService.off(type, wrappedHandler);
    };
    websocketService.on(type, wrappedHandler);
  }, []);
  
  // Content generation functions
  const requestContent = useCallback(async (request: ContentGenerationRequest) => {
    await sendMessage(WebSocketMessageType.CONTENT_REQUEST, request, {
      channel: WebSocketChannel.CONTENT_UPDATES,
      awaitAcknowledgment: true,
      timeout: 10000
    });
  }, [sendMessage]);
  
  const onContentProgress = useCallback((
    handler: (progress: ContentGenerationProgress) => void
  ): (() => void) => {
    return on(WebSocketMessageType.CONTENT_PROGRESS, handler);
  }, [on]);
  
  // Quiz functions
  const sendQuizResponse = useCallback(async (response: QuizMessage) => {
    await sendMessage(WebSocketMessageType.QUIZ_RESPONSE, response, {
      channel: WebSocketChannel.QUIZ_EVENTS,
      awaitAcknowledgment: true,
      timeout: 5000
    });
  }, [sendMessage]);
  
  const onQuizFeedback = useCallback((handler: (feedback: any) => void): (() => void) => {
    return on(WebSocketMessageType.QUIZ_FEEDBACK, handler);
  }, [on]);
  
  // Progress tracking functions
  const updateProgress = useCallback(async (progress: ProgressUpdate) => {
    await sendMessage(WebSocketMessageType.PROGRESS_UPDATE, progress, {
      channel: WebSocketChannel.STUDENT_UPDATES,
      awaitAcknowledgment: true,
      timeout: 5000
    });
  }, [sendMessage]);
  
  const onProgressUpdate = useCallback((
    handler: (progress: ProgressUpdate) => void
  ): (() => void) => {
    return on(WebSocketMessageType.PROGRESS_UPDATE, handler);
  }, [on]);
  
  // Collaboration functions
  const sendCollaborationMessage = useCallback(async (message: CollaborationMessage) => {
    await sendMessage(WebSocketMessageType.USER_MESSAGE, message, {
      channel: `collaboration_${message.roomId}`,
      awaitAcknowledgment: false
    });
  }, [sendMessage]);
  
  const onCollaborationEvent = useCallback((
    handler: (message: CollaborationMessage) => void
  ): (() => void) => {
    return on(WebSocketMessageType.USER_MESSAGE, handler);
  }, [on]);
  
  // Roblox event handler
  const onRobloxEvent = useCallback((
    handler: (event: RobloxEventMessage) => void
  ): (() => void) => {
    return on(WebSocketMessageType.ROBLOX_EVENT, handler);
  }, [on]);
  
  // System notification handler
  const onSystemNotification = useCallback((
    handler: (notification: SystemNotification) => void
  ): (() => void) => {
    return on(WebSocketMessageType.SYSTEM_NOTIFICATION, handler);
  }, [on]);
  
  // Handle user-specific messages
  const handleUserMessage = useCallback((message: WebSocketMessage) => {
    // Dispatch to Redux for state management
    dispatch({
      type: 'websocket/messageReceived',
      payload: message
    });
    
    // Handle specific message types
    switch (message.type) {
      case WebSocketMessageType.SYSTEM_NOTIFICATION:
        const notification = message.payload as SystemNotification;
        dispatch(addNotification({
          type: notification.level === 'error' ? 'error' : 
                notification.level === 'warning' ? 'warning' : 
                notification.level === 'success' ? 'success' : 'info',
          message: `${notification.title}: ${notification.message}`,
          autoHide: notification.dismissible
        }));
        break;
      
      case WebSocketMessageType.PROGRESS_UPDATE:
        // Update progress state
        dispatch({
          type: 'progress/updated',
          payload: message.payload
        });
        break;
      
      case WebSocketMessageType.QUIZ_FEEDBACK:
        // Update quiz state
        dispatch({
          type: 'assessments/feedbackReceived',
          payload: message.payload
        });
        break;
      
      default:
        if (debug) {
          console.log('[WebSocket] User message:', message);
        }
    }
  }, [dispatch, debug]);
  
  // Create memoized context value
  const contextValue = useMemo<WebSocketContextValue>(() => ({
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
    onSystemNotification
  }), [
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
    onSystemNotification
  ]);
  
  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
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