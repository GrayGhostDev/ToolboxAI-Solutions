/**
 * WebSocket Service (Compatibility Layer)
 *
 * Wraps the Pusher service to maintain a simple WebSocket-like API
 * while leveraging the centralized message types and robust realtime layer.
 */

import { pusherService } from './pusher';
import {
  WebSocketMessageType,
  WebSocketMessage,
  WebSocketState,
} from '../types/websocket';

/**
 * Connect to WebSocket (delegates to Pusher)
 */
export function connectWebSocket(token?: string) {
  return pusherService.connect(token);
}

/**
 * Disconnect from WebSocket
 */
export function disconnectWebSocket() {
  pusherService.disconnect();
}

/**
 * Send a WebSocket message (delegates to Pusher REST trigger)
 */
export function sendWebSocketMessage<T = any>(
  type: WebSocketMessageType,
  payload?: T,
  options?: {
    channel?: string;
    awaitAcknowledgment?: boolean;
    timeout?: number;
  }
) {
  return pusherService.send(type, payload, options);
}

/**
 * Subscribe to a channel with optional message filter
 */
export function subscribeToChannel(
  channel: string,
  callback: (message: WebSocketMessage) => void,
  filter?: (message: WebSocketMessage) => boolean
): string {
  return pusherService.subscribe(channel, callback, filter);
}

/**
 * Unsubscribe from a channel using subscription id
 */
export function unsubscribeFromChannel(subscriptionId: string) {
  pusherService.unsubscribe(subscriptionId);
}

/**
 * WebSocket Service (singleton)
 */
export class WebSocketService {
  private static instance: WebSocketService;

  static getInstance(): WebSocketService {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService();
    }
    return WebSocketService.instance;
  }

  connect(token?: string) {
    return connectWebSocket(token);
  }

  disconnect() {
    disconnectWebSocket();
  }

  send<T = any>(
    type: WebSocketMessageType,
    payload?: T,
    options?: { channel?: string; awaitAcknowledgment?: boolean; timeout?: number }
  ) {
    return sendWebSocketMessage(type, payload, options);
  }

  subscribe(
    channel: string,
    callback: (message: WebSocketMessage) => void,
    filter?: (message: WebSocketMessage) => boolean
  ): () => void {
    const id = subscribeToChannel(channel, callback, filter);
    return () => unsubscribeFromChannel(id);
  }

  unsubscribe(id: string) {
    unsubscribeFromChannel(id);
  }

  isConnected(): boolean {
    return pusherService.isConnected();
  }

  // Proxies to underlying Pusher service for full feature parity

  getState(): WebSocketState {
    return pusherService.getState();
  }

  getStats() {
    return pusherService.getStats();
  }

  onConnectionStatusChange(handler: (state: WebSocketState) => void): () => void {
    return pusherService.onStateChange(handler);
  }

  on(type: WebSocketMessageType | string, handler: (data: any) => void): void {
    pusherService.on(type, handler);
  }

  off(type: WebSocketMessageType | string, handler: (data: any) => void): void {
    pusherService.off(type, handler);
  }

  onError(handler: (error: any) => void): () => void {
    return pusherService.onError(handler);
  }

  async refreshToken(newToken: string): Promise<void> {
    // Reconnect with new token (pusher service handles auth headers)
    await pusherService.connect(newToken);
  }

  async refreshTokenAndReconnect(): Promise<void> {
    await pusherService.refreshTokenAndReconnect();
  }

  onTokenRefresh(callback: () => void): () => void {
    // Reuse generic event system; backend should emit 'token_expired'
    // or client may simulate this event
    this.on('token_expired', () => callback());
    return () => this.off('token_expired', () => callback());
  }


}

// Export default instance
export const wsService = WebSocketService.getInstance();
export const websocketService = wsService; // Alias for backward compatibility
export default wsService;