/**
 * WebSocket Test Provider
 *
 * Mock WebSocket context for testing
 */

import React, { createContext, useContext } from 'react';

// Create mock WebSocket context
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
});

export const useWebSocket = () => useContext(WebSocketContext);

interface WebSocketProviderProps {
  children: React.ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
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
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

export { WebSocketContext };