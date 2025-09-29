/**
 * Pusher Provider Component
 * Provides Pusher context to the entire application
 * @module PusherProvider
 * @version 1.0.0
 * @since 2025-09-26
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { pusherClient } from '../services/pusher-client';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import { Alert, Progress, Box, Text, Group } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { config } from '../config';

// Types
interface PusherContextValue {
  isConnected: boolean;
  connectionState: string;
  isInitialized: boolean;
  error: string | null;
  debugInfo: any;
}

interface PusherProviderProps {
  children: ReactNode;
  fallbackComponent?: ReactNode;
  showConnectionStatus?: boolean;
  autoReconnect?: boolean;
}

// Create context
const PusherContext = createContext<PusherContextValue>({
  isConnected: false,
  connectionState: 'uninitialized',
  isInitialized: false,
  error: null,
  debugInfo: {},
});

/**
 * Pusher Provider Component
 */
export const PusherProvider: React.FC<PusherProviderProps> = ({
  children,
  fallbackComponent,
  showConnectionStatus = true,
  autoReconnect = true,
}) => {
  const { user, token } = useSelector((state: RootState) => state.auth);
  const [contextValue, setContextValue] = useState<PusherContextValue>({
    isConnected: false,
    connectionState: 'uninitialized',
    isInitialized: false,
    error: null,
    debugInfo: {},
  });
  const [showError, setShowError] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  // Initialize Pusher when user is authenticated
  useEffect(() => {
    if (user?.id && token && config.pusher.enabled) {
      try {
        console.log('Initializing Pusher for user:', user.id);
        pusherClient.initialize(user.id, token);

        setContextValue(prev => ({
          ...prev,
          isInitialized: true,
          error: null,
        }));
      } catch (error) {
        console.error('Failed to initialize Pusher:', error);
        setContextValue(prev => ({
          ...prev,
          isInitialized: false,
          error: (error as Error).message,
        }));
        setShowError(true);
      }
    } else if (!config.pusher.enabled) {
      console.log('Pusher is disabled in configuration');
      setContextValue(prev => ({
        ...prev,
        connectionState: 'disabled',
        error: 'Real-time updates are disabled',
      }));
    }

    // Cleanup on unmount or when user changes
    return () => {
      if (contextValue.isInitialized) {
        console.log('Cleaning up Pusher connection');
        pusherClient.disconnect();
        setContextValue({
          isConnected: false,
          connectionState: 'disconnected',
          isInitialized: false,
          error: null,
          debugInfo: {},
        });
      }
    };
  }, [user?.id, token]);

  // Monitor connection state
  useEffect(() => {
    if (!contextValue.isInitialized) return;

    const interval = setInterval(() => {
      const state = pusherClient.getConnectionState();
      const isConnected = pusherClient.isConnected();
      const debugInfo = pusherClient.getDebugInfo();

      setContextValue(prev => ({
        ...prev,
        connectionState: state,
        isConnected,
        debugInfo,
        error: debugInfo.lastError || null,
      }));

      // Update reconnect attempts
      if (debugInfo.connectionAttempts !== reconnectAttempts) {
        setReconnectAttempts(debugInfo.connectionAttempts);
      }

      // Show error if connection failed after max attempts
      if (debugInfo.fallbackToPolling && !showError) {
        setShowError(true);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [contextValue.isInitialized, reconnectAttempts, showError]);

  // Render connection status bar
  const renderConnectionStatus = () => {
    if (!showConnectionStatus || !contextValue.isInitialized) return null;

    const { connectionState } = contextValue;

    if (connectionState === 'connecting' || reconnectAttempts > 0) {
      return (
        <Box
          style={{
            width: '100%',
            position: 'fixed',
            top: 0,
            left: 0,
            zIndex: 9999,
          }}
        >
          <Progress value={reconnectAttempts * 20} size="xs" animated />
          <Group
            style={{
              backgroundColor: 'var(--mantine-color-blue-6)',
              color: 'white',
              padding: '4px 8px',
              justifyContent: 'center',
            }}
          >
            <Text size="xs">
              {reconnectAttempts > 0
                ? `Reconnecting... (Attempt ${reconnectAttempts}/5)`
                : 'Connecting to real-time updates...'}
            </Text>
          </Group>
        </Box>
      );
    }

    if (connectionState === 'polling') {
      return (
        <Box
          style={{
            width: '100%',
            position: 'fixed',
            top: 0,
            left: 0,
            zIndex: 9999,
            backgroundColor: 'var(--mantine-color-yellow-6)',
            color: 'white',
            padding: '4px 8px',
            textAlign: 'center',
          }}
        >
          <Text size="xs">
            📊 Using polling for updates (Pusher WebSocket unavailable)
          </Text>
        </Box>
      );
    }

    return null;
  };

  // Show error notifications using Mantine
  React.useEffect(() => {
    if (contextValue.error && showError) {
      notifications.show({
        id: 'pusher-error',
        title: 'Real-time Connection Issue',
        message: contextValue.error,
        color: 'yellow',
        autoClose: 6000,
        onClose: () => setShowError(false),
      });
    }
  }, [contextValue.error, showError]);

  // Show fallback component if not initialized
  if (!contextValue.isInitialized && fallbackComponent) {
    return <>{fallbackComponent}</>;
  }

  return (
    <PusherContext.Provider value={contextValue}>
      {renderConnectionStatus()}
      {children}
    </PusherContext.Provider>
  );
};

/**
 * Hook to use Pusher context
 */
export const usePusherContext = () => {
  const context = useContext(PusherContext);

  if (!context) {
    throw new Error('usePusherContext must be used within PusherProvider');
  }

  return context;
};

/**
 * Connection Status Component
 */
export const PusherConnectionStatus: React.FC = () => {
  const { isConnected, connectionState, debugInfo } = usePusherContext();

  const getStatusColor = () => {
    if (isConnected) return 'success.main';
    if (connectionState === 'connecting') return 'info.main';
    if (connectionState === 'polling') return 'warning.main';
    return 'error.main';
  };

  const getStatusText = () => {
    if (isConnected) return 'Connected';
    if (connectionState === 'connecting') return 'Connecting...';
    if (connectionState === 'polling') return 'Polling Mode';
    if (connectionState === 'disconnected') return 'Disconnected';
    return 'Not Initialized';
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Box
        sx={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          backgroundColor: getStatusColor(),
          animation: connectionState === 'connecting' ? 'pulse 1.5s infinite' : 'none',
        }}
      />
      <Typography variant="caption" color="text.secondary">
        {getStatusText()}
      </Typography>
    </Box>
  );
};

// Debug component for development
export const PusherDebugPanel: React.FC = () => {
  const { debugInfo } = usePusherContext();

  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <Box
      sx={{
        position: 'fixed',
        bottom: 16,
        left: 16,
        backgroundColor: 'background.paper',
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 1,
        padding: 2,
        maxWidth: 300,
        zIndex: 9999,
      }}
    >
      <Typography variant="subtitle2" gutterBottom>
        Pusher Debug Info
      </Typography>
      <pre style={{ fontSize: '10px', margin: 0 }}>
        {JSON.stringify(debugInfo, null, 2)}
      </pre>
    </Box>
  );
};

// Export components
export default PusherProvider;