/**
 * WebSocket Status Hook (Pusher Implementation)
 * Provides connection status information using Pusher service
 * Updated for 2025 standards
 */

import { useState, useEffect } from 'react';
import { pusherService } from '../../services/pusher';
import { WebSocketState } from '../../types/websocket';

export interface WebSocketStatusInfo {
  state: WebSocketState;
  isConnected: boolean;
  isConnecting: boolean;
  isReconnecting: boolean;
  isDisconnected: boolean;
  hasError: boolean;
  connectionAttempts: number;
  lastError?: string;
  connectedAt?: string;
  messagesSent: number;
  messagesReceived: number;
  latency?: number;
}

export function useWebSocketStatus(): WebSocketStatusInfo {
  const [status, setStatus] = useState<WebSocketStatusInfo>(() => {
    const currentState = pusherService.getState();
    const stats = pusherService.getStats();

    return {
      state: currentState,
      isConnected: currentState === WebSocketState.CONNECTED,
      isConnecting: currentState === WebSocketState.CONNECTING,
      isReconnecting: currentState === WebSocketState.RECONNECTING,
      isDisconnected: currentState === WebSocketState.DISCONNECTED,
      hasError: currentState === WebSocketState.ERROR || currentState === WebSocketState.DISCONNECTED,
      connectionAttempts: stats.reconnectAttempts,
      connectedAt: stats.connectedAt,
      messagesSent: stats.messagesSent,
      messagesReceived: stats.messagesReceived,
      latency: stats.latency,
    };
  });

  useEffect(() => {
    // Subscribe to state changes
    const unsubscribe = pusherService.onStateChange((newState) => {
      const stats = pusherService.getStats();

      setStatus({
        state: newState,
        isConnected: newState === WebSocketState.CONNECTED,
        isConnecting: newState === WebSocketState.CONNECTING,
        isReconnecting: newState === WebSocketState.RECONNECTING,
        isDisconnected: newState === WebSocketState.DISCONNECTED,
        hasError: newState === WebSocketState.ERROR || newState === WebSocketState.DISCONNECTED,
        connectionAttempts: stats.reconnectAttempts,
        connectedAt: stats.connectedAt,
        messagesSent: stats.messagesSent,
        messagesReceived: stats.messagesReceived,
        latency: stats.latency,
      });
    });

    // Subscribe to errors
    const unsubscribeError = pusherService.onError((error) => {
      setStatus(prev => ({
        ...prev,
        lastError: error.message,
        hasError: true,
      }));
    });

    return () => {
      unsubscribe();
      unsubscribeError();
    };
  }, []);

  return status;
}
