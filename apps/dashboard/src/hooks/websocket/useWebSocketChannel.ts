/**
 * WebSocket Channel Hook (Pusher Implementation)
 * Provides channel subscription management using Pusher service
 * Updated for 2025 standards
 */

import { useEffect, useCallback, useState } from 'react';
import { pusherService } from '../../services/pusher';
import { type WebSocketChannel, type WebSocketEventHandler, type WebSocketMessage } from '../../types/websocket';

export interface UseWebSocketChannelOptions {
  autoSubscribe?: boolean;
  filter?: (message: WebSocketMessage) => boolean;
  onSubscribed?: () => void;
  onUnsubscribed?: () => void;
  onError?: (error: Error) => void;
}

export interface UseWebSocketChannelReturn {
  isSubscribed: boolean;
  messages: WebSocketMessage[];
  subscribe: () => void;
  unsubscribe: () => void;
  clearMessages: () => void;
}

export function useWebSocketChannel(
  channel: WebSocketChannel | string,
  handler: WebSocketEventHandler,
  options: UseWebSocketChannelOptions = {}
): UseWebSocketChannelReturn {
  const { autoSubscribe = true, filter, onSubscribed, onUnsubscribed, onError } = options;
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [subscriptionId, setSubscriptionId] = useState<string | null>(null);

  const subscribe = useCallback(() => {
    try {
      const id = pusherService.subscribe(
        channel as string,
        (message: WebSocketMessage) => {
          // Store message in history
          setMessages(prev => [...prev, message]);
          // Call the handler
          handler(message);
        },
        filter
      );
      
      setSubscriptionId(id);
      setIsSubscribed(true);
      onSubscribed?.();
    } catch (error) {
      onError?.(error as Error);
    }
  }, [channel, handler, filter, onSubscribed, onError]);

  const unsubscribe = useCallback(() => {
    if (subscriptionId) {
      pusherService.unsubscribe(subscriptionId);
      setSubscriptionId(null);
      setIsSubscribed(false);
      onUnsubscribed?.();
    }
  }, [subscriptionId, onUnsubscribed]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  useEffect(() => {
    if (autoSubscribe) {
      subscribe();
    }

    return () => {
      unsubscribe();
    };
  }, [autoSubscribe, subscribe, unsubscribe]);

  return {
    isSubscribed,
    messages,
    subscribe,
    unsubscribe,
    clearMessages,
  };
}

export function useWebSocketChannels(
  channels: (WebSocketChannel | string)[],
  handlers: Record<string, WebSocketEventHandler>,
  options: UseWebSocketChannelOptions = {}
) {
  const [subscriptions, setSubscriptions] = useState<Record<string, string>>({});
  const [isSubscribed, setIsSubscribed] = useState(false);

  const subscribe = useCallback(() => {
    const newSubscriptions: Record<string, string> = {};
    
    channels.forEach(channel => {
      const handler = handlers[channel as string];
      if (handler) {
        try {
          const id = pusherService.subscribe(
            channel as string,
            handler,
            options.filter
          );
          newSubscriptions[channel as string] = id;
        } catch (error) {
          options.onError?.(error as Error);
        }
      }
    });

    setSubscriptions(newSubscriptions);
    setIsSubscribed(Object.keys(newSubscriptions).length > 0);
    options.onSubscribed?.();
  }, [channels, handlers, options]);

  const unsubscribe = useCallback(() => {
    Object.values(subscriptions).forEach(id => {
      pusherService.unsubscribe(id);
    });
    setSubscriptions({});
    setIsSubscribed(false);
    options.onUnsubscribed?.();
  }, [subscriptions, options]);

  useEffect(() => {
    if (options.autoSubscribe !== false) {
      subscribe();
    }

    return () => {
      unsubscribe();
    };
  }, [subscribe, unsubscribe, options.autoSubscribe]);

  return {
    isSubscribed,
    subscriptions,
    subscribe,
    unsubscribe,
  };
}