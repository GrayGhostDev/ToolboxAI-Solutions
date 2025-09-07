/**
 * WebSocket message listener hook
 * Listens for specific message types and triggers callbacks
 */

import { useEffect, useCallback, useRef } from 'react';
import { useWebSocket } from './useWebSocket';
import { WebSocketMessageType } from '../../types/websocket';

export interface UseWebSocketMessageOptions {
  enabled?: boolean;
  once?: boolean;
}

export function useWebSocketMessage<T = any>(
  messageType: WebSocketMessageType,
  callback: (data: T) => void,
  options: UseWebSocketMessageOptions = {}
): void {
  const { on, isConnected } = useWebSocket();
  const { enabled = true, once = false } = options;
  
  // Store callback in ref to avoid re-subscriptions
  const callbackRef = useRef(callback);
  callbackRef.current = callback;
  
  // Memoize the handler
  const handler = useCallback((data: T) => {
    callbackRef.current(data);
  }, []);
  
  useEffect(() => {
    if (!enabled || !isConnected) return;
    
    let unsubscribe: (() => void) | null = null;
    
    if (once) {
      // Subscribe with once behavior
      const handleOnce = (data: T) => {
        handler(data);
        if (unsubscribe) unsubscribe();
      };
      unsubscribe = on(messageType, handleOnce);
    } else {
      // Regular subscription
      unsubscribe = on(messageType, handler);
    }
    
    return () => {
      if (unsubscribe) unsubscribe();
    };
  }, [messageType, handler, on, isConnected, enabled, once]);
}

/**
 * Hook for listening to multiple message types
 */
export function useWebSocketMessages(
  handlers: Record<WebSocketMessageType, (data: any) => void>,
  options: UseWebSocketMessageOptions = {}
): void {
  const { on, isConnected } = useWebSocket();
  const { enabled = true } = options;
  
  useEffect(() => {
    if (!enabled || !isConnected) return;
    
    const unsubscribers: Array<() => void> = [];
    
    Object.entries(handlers).forEach(([messageType, handler]) => {
      const unsubscribe = on(messageType as WebSocketMessageType, handler);
      unsubscribers.push(unsubscribe);
    });
    
    return () => {
      unsubscribers.forEach(unsubscribe => unsubscribe());
    };
  }, [handlers, on, isConnected, enabled]);
}