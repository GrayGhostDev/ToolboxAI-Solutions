/**
 * Realtime Test Provider
 *
 * Mock Pusher/WebSocket context for testing
 * Provides compatibility with both Pusher and legacy WebSocket APIs
 */

import React, { createContext, useContext } from 'react';

// Create mock realtime context (Pusher-compatible)
const WebSocketContext = createContext({
  isConnected: true,
  connectionState: 'connected' as const,
  subscribe: () => ({ unsubscribe: () => {} }),
  unsubscribe: () => {},
  emit: () => {},
  on: () => ({ off: () => {} }),
  off: () => {},
  connect: () => Promise.resolve(),
  disconnect: () => {},
  sendMessage: () => {},
  lastMessage: null,
  error: null,
  // Pusher-specific mock methods
  trigger: () => Promise.resolve(),
  channel: () => ({
    bind: () => {},
    unbind: () => {},
    trigger: () => Promise.resolve(),
  }),
});

export const useWebSocket = () => useContext(WebSocketContext);

interface WebSocketProviderProps {
  children: React.ReactNode;
}

export const WebSocketProvider: React.FunctionComponent<WebSocketProviderProps> = ({ children }) => {
  const value = {
    isConnected: true,
    connectionState: 'connected' as const,
    subscribe: () => ({ unsubscribe: () => {} }),
    unsubscribe: () => {},
    emit: () => {},
    on: () => ({ off: () => {} }),
    off: () => {},
    connect: () => Promise.resolve(),
    disconnect: () => {},
    sendMessage: () => {},
    lastMessage: null,
    error: null,
    // Pusher-specific mock methods
    trigger: () => Promise.resolve(),
    channel: () => ({
      bind: () => {},
      unbind: () => {},
      trigger: () => Promise.resolve(),
    }),
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

export { WebSocketContext };