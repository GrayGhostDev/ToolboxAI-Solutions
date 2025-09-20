import { useEffect, useRef, useState } from 'react';
import { pusherService, PusherService } from '../services/pusher';
import { WebSocketState } from '../types/websocket';

/**
 * React hook for using Pusher service in components
 * Provides easy access to real-time features and automatic cleanup
 */
export function usePusher() {
  const serviceRef = useRef<PusherService>(pusherService);

  useEffect(() => {
    // Ensure connection when component mounts
    if (serviceRef.current.getState() === WebSocketState.DISCONNECTED) {
      serviceRef.current.connect().catch(error => {
        console.error('Failed to connect to Pusher:', error);
      });
    }

    // No cleanup here - we want to keep the connection alive across components
  }, []);

  return serviceRef.current;
}

/**
 * Hook for subscribing to Pusher channels with automatic cleanup
 */
export function usePusherChannel(
  channelName: string,
  eventHandlers: Record<string, (data: any) => void>,
  enabled = true
) {
  const pusher = usePusher();
  const subscriptionIdsRef = useRef<string[]>([]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    // Subscribe to events
    const subscriptionIds: string[] = [];

    Object.entries(eventHandlers).forEach(([eventType, handler]) => {
      const subscriptionId = pusher.subscribe(channelName, (message) => {
        if (message.type === eventType) {
          handler(message.payload);
        }
      });
      subscriptionIds.push(subscriptionId);
    });

    subscriptionIdsRef.current = subscriptionIds;

    // Cleanup subscriptions on unmount or when deps change
    return () => {
      subscriptionIdsRef.current.forEach(id => {
        pusher.unsubscribe(id);
      });
      subscriptionIdsRef.current = [];
    };
  }, [channelName, enabled, pusher, JSON.stringify(Object.keys(eventHandlers))]);

  return pusher;
}

/**
 * Hook for monitoring Pusher connection state
 */
export function usePusherConnection() {
  const pusher = usePusher();
  const [connectionState, setConnectionState] = useState<WebSocketState>(pusher.getState());

  useEffect(() => {
    const unsubscribe = pusher.onStateChange((newState) => {
      setConnectionState(newState);
    });

    return unsubscribe;
  }, [pusher]);

  return {
    isConnected: connectionState === WebSocketState.CONNECTED,
    isConnecting: connectionState === WebSocketState.CONNECTING,
    isReconnecting: connectionState === WebSocketState.RECONNECTING,
    state: connectionState,
  };
}