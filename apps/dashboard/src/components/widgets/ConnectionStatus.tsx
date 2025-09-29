import React from 'react';
import { Group, Badge, Tooltip, Loader, Box } from '@mantine/core';
import {
  IconWifiOff,
  IconWifi,
  IconWifi1,
  IconAlertTriangle,
  IconX,
} from '@tabler/icons-react';
import { usePusherContext } from '../PusherProvider';

interface ConnectionStatusProps {
  showLabel?: boolean;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
}

const ConnectionStatus: React.FunctionComponent<ConnectionStatusProps> = ({
  showLabel = true,
  size = 'sm',
}) => {
  const { isConnected, connectionState, debugInfo } = usePusherContext();

  const getStatusConfig = () => {
    switch (connectionState) {
      case 'connected':
        return {
          icon: <IconWifi size={size === 'sm' ? 16 : 20} />,
          label: 'Connected',
          color: 'green' as const,
          tooltip: `Connected to Pusher${debugInfo?.fallbackToPolling ? ' (Polling Mode)' : ''}`,
        };
      case 'connecting':
        return {
          icon: <Loader size={size === 'sm' ? 16 : 20} />,
          label: 'Connecting',
          color: 'blue' as const,
          tooltip: 'Establishing Pusher connection...',
        };
      case 'reconnecting':
        return {
          icon: <IconWifi1 size={size === 'sm' ? 16 : 20} />,
          label: 'Reconnecting',
          color: 'yellow' as const,
          tooltip: 'Attempting to reconnect to Pusher...',
        };
      case 'polling':
        return {
          icon: <IconWifi1 size={size === 'sm' ? 16 : 20} />,
          label: 'Polling',
          color: 'orange' as const,
          tooltip: 'Using polling fallback for real-time updates',
        };
      case 'disconnected':
        return {
          icon: <IconWifiOff size={size === 'sm' ? 16 : 20} />,
          label: 'Disconnected',
          color: 'gray' as const,
          tooltip: 'Not connected to Pusher',
        };
      case 'failed':
      case 'error':
        return {
          icon: <IconX size={size === 'sm' ? 16 : 20} />,
          label: 'Error',
          color: 'red' as const,
          tooltip: `Pusher connection error: ${debugInfo?.lastError || 'Unknown error'}`,
        };
      case 'disabled':
        return {
          icon: <IconAlertTriangle size={size === 'sm' ? 16 : 20} />,
          label: 'Disabled',
          color: 'gray' as const,
          tooltip: 'Real-time updates are disabled',
        };
      default:
        return {
          icon: <IconWifiOff size={size === 'sm' ? 16 : 20} />,
          label: 'Unknown',
          color: 'gray' as const,
          tooltip: 'Connection status unknown',
        };
    }
  };

  const config = getStatusConfig();

  return (
    <Tooltip label={config.tooltip} position="bottom">
      <Box>
        <Badge
          leftSection={config.icon}
          color={config.color}
          size={size}
          variant={isConnected ? 'filled' : 'outline'}
          style={{
            cursor: 'help',
          }}
        >
          {showLabel ? config.label : null}
        </Badge>
      </Box>
    </Tooltip>
  );
};

export default ConnectionStatus;