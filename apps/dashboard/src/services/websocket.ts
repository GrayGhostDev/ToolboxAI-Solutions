/**
 * WebSocket Service (Compatibility Layer)
 *
 * This is a compatibility layer that wraps the Pusher service
 * to maintain backward compatibility with components expecting WebSocket
 */

import { pusherService } from './pusher';

/**
 * Connect to WebSocket (delegates to Pusher)
 */
export function connectWebSocket(token?: string) {
  if (token) {
    pusherService.connect(token);
  }
}

/**
 * Disconnect from WebSocket
 */
export function disconnectWebSocket() {
  pusherService.disconnect();
}

/**
 * Send a WebSocket message (compatibility function)
 */
export function sendWebSocketMessage(type: string, payload: any) {
  // In Pusher, we would trigger an event on a channel
  // This is a compatibility shim
  console.log('WebSocket message (via Pusher):', type, payload);
}

/**
 * Subscribe to a channel
 */
export function subscribeToChannel(channel: string, callback: (data: any) => void): string {
  // Return a subscription ID for compatibility
  return `sub-${channel}-${Date.now()}`;
}

/**
 * Unsubscribe from a channel
 */
export function unsubscribeFromChannel(subscriptionId: string) {
  // Compatibility function
  console.log('Unsubscribing:', subscriptionId);
}

/**
 * WebSocket Message Types (for compatibility)
 */
export enum WebSocketMessageType {
  CONNECT = 'connect',
  DISCONNECT = 'disconnect',
  CONTENT_UPDATE = 'content_update',
  QUIZ_UPDATE = 'quiz_update',
  PROGRESS_UPDATE = 'progress_update',
  CLASS_ONLINE = 'class_online',
  ACHIEVEMENT_UNLOCKED = 'achievement_unlocked',
  ASSIGNMENT_REMINDER = 'assignment_reminder',
  REQUEST_LEADERBOARD = 'request_leaderboard',
  LEADERBOARD_UPDATE = 'leaderboard_update',
  XP_GAINED = 'xp_gained',
  BADGE_EARNED = 'badge_earned',
  ERROR = 'error',
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
    connectWebSocket(token);
  }

  disconnect() {
    disconnectWebSocket();
  }

  send(type: string, payload: any) {
    sendWebSocketMessage(type, payload);
  }

  subscribe(channel: string, callback: (data: any) => void): () => void {
    const id = subscribeToChannel(channel, callback);
    return () => unsubscribeFromChannel(id);
  }

  unsubscribe(id: string) {
    unsubscribeFromChannel(id);
  }

  isConnected(): boolean {
    return pusherService.isConnected();
  }
}

// Export default instance
export const wsService = WebSocketService.getInstance();
export default wsService;