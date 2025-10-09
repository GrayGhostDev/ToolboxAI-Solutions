import React, { useState } from 'react';
import { Box, Text, Badge, Group, ActionIcon, Tooltip } from '@mantine/core';
import {
  IconWifi,
  IconWifiOff,
  IconRefresh,
  IconInfoCircle,
  IconAlertTriangle,
  IconX,
  IconCircleCheck,
} from '@tabler/icons-react';

/**
 * Pusher Connection Status Component
 *
 * Displays the current Pusher connection status with visual indicators,
 * reconnection controls, and detailed connection information.
 */

interface PusherConnectionStatusProps {
  showDetails?: boolean;
  size?: 'sm' | 'md' | 'lg';
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'inline';
}

const PusherConnectionStatus: React.FC<PusherConnectionStatusProps> = ({
  showDetails = true,
  size = 'md',
  position = 'inline',
}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  const getStatusColor = () => {
    if (isConnecting) return 'blue';
    if (isConnected) return 'green';
    return 'red';
  };

  const getStatusIcon = () => {
    if (isConnecting) return <IconWifi size={16} />;
    if (isConnected) return <IconCircleCheck size={16} />;
    return <IconWifiOff size={16} />;
  };

  const getStatusLabel = () => {
    if (isConnecting) return 'Connecting...';
    if (isConnected) return 'Connected';
    return 'Disconnected';
  };

  return (
    <Box>
      <Tooltip label={getStatusLabel()}>
        <Badge
          color={getStatusColor()}
          leftSection={getStatusIcon()}
          size={size}
          style={{ cursor: 'pointer' }}
        >
          {getStatusLabel()}
        </Badge>
      </Tooltip>
    </Box>
  );
};

export default PusherConnectionStatus;