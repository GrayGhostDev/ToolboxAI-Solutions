/**
 * WebSocket Compatibility Layer
 *
 * Provides backward compatibility for components still using old WebSocket APIs
 * These components should be migrated to use Pusher directly
 *
 * @deprecated Use Pusher service directly via usePusher() hook
 */

import { pusherService } from '../services/pusher';
import { logger } from './logger';

let hasShownDeprecationWarning = false;

function showDeprecationWarning(method: string) {
  if (!hasShownDeprecationWarning) {
    logger.warn(`[DEPRECATED] WebSocket compatibility method '${method}' is deprecated. Please migrate to Pusher service.`);
    hasShownDeprecationWarning = true;
  }
}

/**
 * Legacy WebSocket-like interface for backward compatibility
 * @deprecated Use Pusher service directly
 */
export class WebSocketCompat {
  private subscriptions = new Map<string, string>();

  connect(): Promise<void> {
    showDeprecationWarning('connect');
    return pusherService.connect();
  }

  disconnect(reason?: string): void {
    showDeprecationWarning('disconnect');
    pusherService.disconnect(reason);
  }

  subscribe(channel: string, handler: (data: any) => void): { unsubscribe: () => void } {
    showDeprecationWarning('subscribe');
    const subscriptionId = pusherService.subscribe(channel, handler);
    this.subscriptions.set(channel, subscriptionId);

    return {
      unsubscribe: () => {
        const id = this.subscriptions.get(channel);
        if (id) {
          pusherService.unsubscribe(id);
          this.subscriptions.delete(channel);
        }
      }
    };
  }

  emit(eventType: string, data: any): void {
    showDeprecationWarning('emit');
    pusherService.send(eventType, data).catch(error => {
      logger.error('WebSocket compat emit failed:', error);
    });
  }

  on(eventType: string, handler: (data: any) => void): void {
    showDeprecationWarning('on');
    pusherService.on(eventType, handler);
  }

  off(eventType: string, handler?: (data: any) => void): void {
    showDeprecationWarning('off');
    if (handler) {
      pusherService.off(eventType, handler);
    }
  }

  get isConnected(): boolean {
    return pusherService.getState() === 'connected';
  }

  get connectionState(): string {
    return pusherService.getState();
  }
}

/**
 * @deprecated Use usePusher() hook instead
 */
export const websocketCompat = new WebSocketCompat();

/**
 * Legacy hook for backward compatibility
 * @deprecated Use usePusher() hook instead
 */
export function useWebSocketCompat() {
  showDeprecationWarning('useWebSocketCompat');
  return websocketCompat;
}