/**
 * Pusher hooks exports (backward compatibility)
 * Centralized export for all real-time communication hooks
 * Updated to use Pusher instead of WebSocket
 */

// Re-export main Pusher hook with WebSocket alias for backward compatibility
export { usePusher as useWebSocket } from '../usePusher';
export { usePusher } from '../usePusher';

// Export Pusher-specific hooks
export { usePusherEvents } from '../pusher/usePusherEvent';
export { usePusherChannel } from '../pusher/usePusherChannel';

// Re-export types for convenience
export type { 
  WebSocketState,
  WebSocketConnectionState,
  WebSocketEventHandler 
} from '../../types/websocket';

export type {
  PusherConnectionState,
  PusherEventHandler,
  PusherHookConfig
} from '../../types/pusher';