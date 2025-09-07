/**
 * WebSocket channel subscription hook
 * Manages subscriptions to specific channels
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { useWebSocket } from './useWebSocket';
import { WebSocketChannel } from '../../types/websocket';

export interface UseWebSocketChannelOptions {
  enabled?: boolean;
  autoSubscribe?: boolean;
  onMessage?: (message: any) => void;
  onSubscribe?: (subscriptionId: string) => void;
  onUnsubscribe?: (subscriptionId: string) => void;
}

export interface UseWebSocketChannelReturn {
  subscriptionId: string | null;
  isSubscribed: boolean;
  messages: any[];
  subscribe: () => void;
  unsubscribe: () => void;
  clearMessages: () => void;
}

export function useWebSocketChannel(
  channel: WebSocketChannel,
  options: UseWebSocketChannelOptions = {}
): UseWebSocketChannelReturn {
  const { subscribe, unsubscribe, isConnected } = useWebSocket();
  const {
    enabled = true,
    autoSubscribe = true,
    onMessage,
    onSubscribe,
    onUnsubscribe
  } = options;
  
  const [subscriptionId, setSubscriptionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  
  // Store callbacks in refs
  const onMessageRef = useRef(onMessage);
  const onSubscribeRef = useRef(onSubscribe);
  const onUnsubscribeRef = useRef(onUnsubscribe);
  
  onMessageRef.current = onMessage;
  onSubscribeRef.current = onSubscribe;
  onUnsubscribeRef.current = onUnsubscribe;
  
  // Handle message callback
  const handleMessage = useCallback((message: any) => {
    setMessages(prev => [...prev, message]);
    if (onMessageRef.current) {
      onMessageRef.current(message);
    }
  }, []);
  
  // Subscribe to channel
  const subscribeToChannel = useCallback(() => {
    if (!isConnected || subscriptionId) return;
    
    const id = subscribe(channel, handleMessage);
    setSubscriptionId(id);
    
    if (onSubscribeRef.current) {
      onSubscribeRef.current(id);
    }
  }, [channel, subscribe, handleMessage, isConnected, subscriptionId]);
  
  // Unsubscribe from channel
  const unsubscribeFromChannel = useCallback(() => {
    if (!subscriptionId) return;
    
    unsubscribe(subscriptionId);
    const oldId = subscriptionId;
    setSubscriptionId(null);
    
    if (onUnsubscribeRef.current) {
      onUnsubscribeRef.current(oldId);
    }
  }, [unsubscribe, subscriptionId]);
  
  // Clear messages
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);
  
  // Auto-subscribe effect
  useEffect(() => {
    if (!enabled || !isConnected || !autoSubscribe) return;
    
    subscribeToChannel();
    
    return () => {
      if (subscriptionId) {
        unsubscribeFromChannel();
      }
    };
  }, [enabled, isConnected, autoSubscribe]);
  
  return {
    subscriptionId,
    isSubscribed: !!subscriptionId,
    messages,
    subscribe: subscribeToChannel,
    unsubscribe: unsubscribeFromChannel,
    clearMessages
  };
}

/**
 * Hook for subscribing to multiple channels
 */
export function useWebSocketChannels(
  channels: WebSocketChannel[],
  options: Omit<UseWebSocketChannelOptions, 'autoSubscribe'> = {}
): Record<WebSocketChannel, UseWebSocketChannelReturn> {
  const results: Record<string, UseWebSocketChannelReturn> = {};
  
  channels.forEach(channel => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    results[channel] = useWebSocketChannel(channel, { ...options, autoSubscribe: true });
  });
  
  return results as Record<WebSocketChannel, UseWebSocketChannelReturn>;
}