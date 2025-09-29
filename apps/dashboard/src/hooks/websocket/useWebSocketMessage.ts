/**
 * WebSocket Message Hook (Pusher Implementation)
 * Provides message handling using Pusher service
 * Updated for 2025 standards
 */

import { useEffect, useCallback, useState } from 'react';
import { pusherService } from '../../services/pusher';
import { WebSocketMessageType, WebSocketEventHandler } from '../../types/websocket';

export interface UseWebSocketMessageOptions {
  autoConnect?: boolean;
  channel?: string;
  filter?: (message: any) => boolean;
}

export function useWebSocketMessage(
  messageType: WebSocketMessageType | string,
  handler: WebSocketEventHandler,
  options: UseWebSocketMessageOptions = {}
) {
  const { autoConnect = true, channel, filter } = options;
  const [isListening, setIsListening] = useState(false);

  useEffect(() => {
    if (!autoConnect) return;

    // Register message type handler
    pusherService.on(messageType, handler);
    setIsListening(true);

    return () => {
      pusherService.off(messageType, handler);
      setIsListening(false);
    };
  }, [messageType, handler, autoConnect]);

  const startListening = useCallback(() => {
    pusherService.on(messageType, handler);
    setIsListening(true);
  }, [messageType, handler]);

  const stopListening = useCallback(() => {
    pusherService.off(messageType, handler);
    setIsListening(false);
  }, [messageType, handler]);

  return {
    isListening,
    startListening,
    stopListening,
  };
}

export function useWebSocketMessages(
  messageTypes: (WebSocketMessageType | string)[],
  handlers: Record<string, WebSocketEventHandler>,
  options: UseWebSocketMessageOptions = {}
) {
  const { autoConnect = true } = options;
  const [isListening, setIsListening] = useState(false);

  useEffect(() => {
    if (!autoConnect) return;

    // Register all handlers
    Object.entries(handlers).forEach(([type, handler]) => {
      pusherService.on(type, handler);
    });
    setIsListening(true);

    return () => {
      Object.entries(handlers).forEach(([type, handler]) => {
        pusherService.off(type, handler);
      });
      setIsListening(false);
    };
  }, [handlers, autoConnect]);

  const startListening = useCallback(() => {
    Object.entries(handlers).forEach(([type, handler]) => {
      pusherService.on(type, handler);
    });
    setIsListening(true);
  }, [handlers]);

  const stopListening = useCallback(() => {
    Object.entries(handlers).forEach(([type, handler]) => {
      pusherService.off(type, handler);
    });
    setIsListening(false);
  }, [handlers]);

  return {
    isListening,
    startListening,
    stopListening,
  };
}