/**
 * WebSocket connection status hook
 * Provides connection state and statistics
 */

import { useMemo } from 'react';
import { useWebSocket } from './useWebSocket';
import { WebSocketState } from '../../types/websocket';

export interface WebSocketStatusInfo {
  state: WebSocketState;
  isConnected: boolean;
  isConnecting: boolean;
  isDisconnected: boolean;
  isError: boolean;
  messagesSent: number;
  messagesReceived: number;
  reconnectAttempts: number;
  lastConnected?: Date;
  lastDisconnected?: Date;
  lastError?: Date;
  latency?: number;
}

export function useWebSocketStatus(): WebSocketStatusInfo {
  const { state, isConnected, stats, error } = useWebSocket();
  
  return useMemo(() => ({
    state,
    isConnected,
    isConnecting: state === WebSocketState.CONNECTING || state === WebSocketState.RECONNECTING,
    isDisconnected: state === WebSocketState.DISCONNECTED,
    isError: state === WebSocketState.ERROR,
    messagesSent: stats.messagesSent,
    messagesReceived: stats.messagesReceived,
    reconnectAttempts: stats.reconnectAttempts,
    lastConnected: stats.connectedAt ? new Date(stats.connectedAt) : undefined,
    lastDisconnected: undefined,
    lastError: undefined,
    latency: stats.latency
  }), [state, isConnected, stats]);
}