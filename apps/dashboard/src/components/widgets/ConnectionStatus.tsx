import React, { useEffect, useState } from 'react';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';
import CircularProgress from '@mui/material/CircularProgress';
import {
  WifiOff,
  Wifi,
  WifiTethering,
  Warning,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { websocketService } from '../../services/websocket';
import { WebSocketState } from '../../types/websocket';

interface ConnectionStatusProps {
  showLabel?: boolean;
  size?: 'small' | 'medium';
}

const ConnectionStatus: React.FunctionComponent<ConnectionStatusProps> = ({
  showLabel = true,
  size = 'small',
}) => {
  const [connectionState, setConnectionState] = useState<WebSocketState>(
    websocketService.getState()
  );
  const [latency, setLatency] = useState<number | null>(null);

  useEffect(() => {
    // Subscribe to connection state changes
    const unsubscribe = websocketService.onConnectionStatusChange((state) => {
      setConnectionState(state);
    });

    // Subscribe to latency updates
    const interval = setInterval(() => {
      const stats = websocketService.getStats();
      setLatency(stats.latency || null);
    }, 5000);

    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  }, []);

  const getStatusConfig = () => {
    switch (connectionState) {
      case WebSocketState.CONNECTED:
        return {
          icon: <Wifi fontSize={size} />,
          label: 'Connected',
          color: 'success' as const,
          tooltip: latency ? `Connected (${latency}ms)` : 'Connected to server',
        };
      case WebSocketState.CONNECTING:
        return {
          icon: <CircularProgress size={size === 'small' ? 16 : 20} thickness={4} />,
          label: 'Connecting',
          color: 'info' as const,
          tooltip: 'Establishing connection...',
        };
      case WebSocketState.RECONNECTING:
        return {
          icon: <WifiTethering fontSize={size} />,
          label: 'Reconnecting',
          color: 'warning' as const,
          tooltip: 'Attempting to reconnect...',
        };
      case WebSocketState.DISCONNECTING:
        return {
          icon: <Warning fontSize={size} />,
          label: 'Disconnecting',
          color: 'warning' as const,
          tooltip: 'Closing connection...',
        };
      case WebSocketState.DISCONNECTED:
        return {
          icon: <WifiOff fontSize={size} />,
          label: 'Disconnected',
          color: 'default' as const,
          tooltip: 'Not connected to server',
        };
      case WebSocketState.ERROR:
        return {
          icon: <ErrorIcon fontSize={size} />,
          label: 'Error',
          color: 'error' as const,
          tooltip: 'Connection error occurred',
        };
      default:
        return {
          icon: <WifiOff fontSize={size} />,
          label: 'Unknown',
          color: 'default' as const,
          tooltip: 'Connection status unknown',
        };
    }
  };

  const config = getStatusConfig();

  return (
    <Tooltip title={config.tooltip} arrow placement="bottom">
      <Box sx={{ display: 'inline-flex', alignItems: 'center' }}>
        <Chip
          icon={config.icon}
          label={showLabel ? config.label : undefined}
          color={config.color}
          size={size}
          variant={connectionState === WebSocketState.CONNECTED ? 'filled' : 'outlined'}
          sx={{
            '& .MuiChip-icon': {
              marginLeft: showLabel ? undefined : 0,
            },
            minWidth: showLabel ? undefined : 'auto',
            paddingLeft: showLabel ? undefined : 1,
            paddingRight: showLabel ? undefined : 1,
          }}
        />
      </Box>
    </Tooltip>
  );
};

export default ConnectionStatus;