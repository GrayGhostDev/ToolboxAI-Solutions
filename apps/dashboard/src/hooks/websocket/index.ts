/**
 * WebSocket hooks exports
 * Centralized export for all WebSocket-related hooks
 */

export { useWebSocket } from './useWebSocket';
export { useWebSocketStatus } from './useWebSocketStatus';
export { useWebSocketMessage, useWebSocketMessages } from './useWebSocketMessage';
export { useWebSocketChannel, useWebSocketChannels } from './useWebSocketChannel';
export { useRealtimeContent, useMultipleContentGeneration } from './useRealtimeContent';

// Re-export types for convenience
export type { WebSocketStatusInfo } from './useWebSocketStatus';
export type { UseWebSocketMessageOptions } from './useWebSocketMessage';
export type { UseWebSocketChannelOptions, UseWebSocketChannelReturn } from './useWebSocketChannel';
export type { 
  ContentGenerationState,
  UseRealtimeContentOptions,
  UseRealtimeContentReturn 
} from './useRealtimeContent';