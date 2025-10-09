/**
 * Redux WebSocket Middleware
 * Bridges WebSocket events with Redux actions
 */

import { type Middleware } from '@reduxjs/toolkit';
import { type PusherService as WebSocketService } from '../../services/pusher';
import { 
  WebSocketMessageType, 
  type WebSocketChannel,
  type ContentGenerationProgress,
  type ContentGenerationResponse,
  type SystemNotification,
  WebSocketState
} from '../../types/websocket';
import { 
  setWebSocketState,
  setWebSocketError,
  updateWebSocketStats,
  addRealtimeMessage,
  updateContentProgress,
  setContentComplete,
  addSystemNotification,
  updateUserPresence,
  updateQuizState
} from '../slices/realtimeSlice';

// WebSocket action types
export const WEBSOCKET_CONNECT = 'websocket/connect';
export const WEBSOCKET_DISCONNECT = 'websocket/disconnect';
export const WEBSOCKET_SEND = 'websocket/send';
export const WEBSOCKET_SUBSCRIBE = 'websocket/subscribe';
export const WEBSOCKET_UNSUBSCRIBE = 'websocket/unsubscribe';

// WebSocket action interfaces
export interface WebSocketConnectAction {
  type: typeof WEBSOCKET_CONNECT;
  payload?: {
    url?: string;
    token?: string;
  };
}

export interface WebSocketDisconnectAction {
  type: typeof WEBSOCKET_DISCONNECT;
  payload?: {
    reason?: string;
  };
}

export interface WebSocketSendAction {
  type: typeof WEBSOCKET_SEND;
  payload: {
    messageType: WebSocketMessageType;
    data: any;
    options?: {
      channel?: WebSocketChannel;
      awaitAcknowledgment?: boolean;
      timeout?: number;
    };
  };
}

export interface WebSocketSubscribeAction {
  type: typeof WEBSOCKET_SUBSCRIBE;
  payload: {
    channel: WebSocketChannel;
  };
}

export interface WebSocketUnsubscribeAction {
  type: typeof WEBSOCKET_UNSUBSCRIBE;
  payload: {
    subscriptionId: string;
  };
}

export type WebSocketAction = 
  | WebSocketConnectAction
  | WebSocketDisconnectAction
  | WebSocketSendAction
  | WebSocketSubscribeAction
  | WebSocketUnsubscribeAction;

// Action creators
export const websocketActions = {
  connect: (url?: string, token?: string): WebSocketConnectAction => ({
    type: WEBSOCKET_CONNECT,
    payload: { url, token }
  }),
  
  disconnect: (reason?: string): WebSocketDisconnectAction => ({
    type: WEBSOCKET_DISCONNECT,
    payload: { reason }
  }),
  
  send: (
    messageType: WebSocketMessageType,
    data: any,
    options?: WebSocketSendAction['payload']['options']
  ): WebSocketSendAction => ({
    type: WEBSOCKET_SEND,
    payload: { messageType, data, options }
  }),
  
  subscribe: (channel: WebSocketChannel): WebSocketSubscribeAction => ({
    type: WEBSOCKET_SUBSCRIBE,
    payload: { channel }
  }),
  
  unsubscribe: (subscriptionId: string): WebSocketUnsubscribeAction => ({
    type: WEBSOCKET_UNSUBSCRIBE,
    payload: { subscriptionId }
  })
};

/**
 * Creates WebSocket middleware
 */
export const createWebSocketMiddleware = (
  webSocketService: WebSocketService
): Middleware => {
  return store => next => (action: any) => {
    // Handle WebSocket-specific actions
    switch (action.type) {
      case WEBSOCKET_CONNECT: {
        const { token } = (action as WebSocketConnectAction).payload || {};
        webSocketService.connect(token).catch(error => {
          store.dispatch(setWebSocketError({
            message: error.message,
            code: 'CONNECTION_FAILED',
            timestamp: new Date()
          }));
        });
        break;
      }
      
      case WEBSOCKET_DISCONNECT: {
        const { reason } = (action as WebSocketDisconnectAction).payload || {};
        webSocketService.disconnect(reason || 'User requested disconnect');
        break;
      }
      
      case WEBSOCKET_SEND: {
        const { messageType, data, options } = (action as WebSocketSendAction).payload;
        webSocketService.send(messageType, data, options).catch(error => {
          store.dispatch(setWebSocketError({
            message: error.message,
            code: 'SEND_FAILED',
            timestamp: new Date()
          }));
        });
        break;
      }
      
      case WEBSOCKET_SUBSCRIBE: {
        const { channel } = (action as WebSocketSubscribeAction).payload;
        const subscriptions = store.getState().realtime?.subscriptions || {};
        
        if (!subscriptions[channel]) {
          const subscriptionId = webSocketService.subscribe(channel, (message) => {
            // Handle channel messages
            store.dispatch(addRealtimeMessage({
              channel,
              message,
              timestamp: new Date()
            }));
          });
          
          // Store subscription ID in state
          store.dispatch({
            type: 'realtime/addSubscription',
            payload: { channel, subscriptionId }
          });
        }
        break;
      }
      
      case WEBSOCKET_UNSUBSCRIBE: {
        const { subscriptionId } = (action as WebSocketUnsubscribeAction).payload;
        webSocketService.unsubscribe(subscriptionId);
        
        // Remove subscription from state
        store.dispatch({
          type: 'realtime/removeSubscription',
          payload: { subscriptionId }
        });
        break;
      }
    }
    
    // Pass action to next middleware
    return next(action);
  };
};

/**
 * Setup WebSocket event listeners
 */
export const setupWebSocketListeners = (
  webSocketService: WebSocketService,
  dispatch: any
): void => {
  // Connection state changes via state handler
  webSocketService.onStateChange((newState: WebSocketState) => {
    dispatch(setWebSocketState(newState));
    dispatch(updateWebSocketStats({ connected: newState === WebSocketState.CONNECTED }));
  });
  
  webSocketService.on(WebSocketMessageType.ERROR, (error: any) => {
dispatch(setWebSocketError({
      message: (error as any)?.message || 'WebSocket error occurred',
      code: (error as any)?.code || 'UNKNOWN_ERROR',
      timestamp: new Date()
    }));
  });
  
  // System notifications
  webSocketService.on(WebSocketMessageType.SYSTEM_NOTIFICATION, (notification: SystemNotification) => {
    dispatch(addSystemNotification(notification));
  });
  
  // Content generation events
  webSocketService.on(WebSocketMessageType.CONTENT_PROGRESS, (progress: ContentGenerationProgress) => {
    dispatch(updateContentProgress(progress));
  });
  
  webSocketService.on(WebSocketMessageType.CONTENT_COMPLETE, (result: ContentGenerationResponse) => {
    dispatch(setContentComplete(result));
  });
  
  // User presence events
  webSocketService.on(WebSocketMessageType.USER_JOIN, (data: any) => {
dispatch(updateUserPresence({
      userId: data.userId,
      status: 'online',
      lastSeen: new Date()
    }));
  });
  
  webSocketService.on(WebSocketMessageType.USER_LEAVE, (data: any) => {
dispatch(updateUserPresence({
      userId: data.userId,
      status: 'offline',
      lastSeen: new Date()
    }));
  });
  
  // Quiz events
  webSocketService.on(WebSocketMessageType.QUIZ_UPDATE, (data: any) => {
    dispatch(updateQuizState(data));
  });
  
  webSocketService.on(WebSocketMessageType.QUIZ_RESULTS, (data: any) => {
    dispatch(updateQuizState({
      ...data,
      type: 'results'
    }));
  });
};