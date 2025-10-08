import React from 'react';
import { Box, Chip, Tooltip } from '@mui/material';
import {
  IconAlertTriangle,
  IconCircleCheck,
  IconCircleX,
  IconWifiOff
} from '@tabler/icons-react';

/**
 * System Health Indicator Component
 *
 * Visual indicator for overall agent system health status.
 *
 * @author ToolboxAI Team
 * @created 2025-09-21
 * @version 1.0.0
 */

interface SystemHealthIndicatorProps {
  status: 'healthy' | 'degraded' | 'error';
  isConnected: boolean;
}

export const SystemHealthIndicator = ({
  status,
  isConnected,
}: SystemHealthIndicatorProps) => {
  const getHealthConfig = () => {
    if (!isConnected) {
      return {
        icon: <IconWifiOff />,
        color: 'error' as const,
        label: 'Disconnected',
        bgColor: '#ffebee',
        textColor: '#c62828',
      };
    }

    switch (status) {
      case 'healthy':
        return {
          icon: <IconCircleCheck />,
          color: 'success' as const,
          label: 'Healthy',
          bgColor: '#e8f5e9',
          textColor: '#2e7d32',
        };
      case 'degraded':
        return {
          icon: <IconAlertTriangle />,
          color: 'warning' as const,
          label: 'Degraded',
          bgColor: '#fff3e0',
          textColor: '#e65100',
        };
      case 'error':
        return {
          icon: <IconCircleX />,
          color: 'error' as const,
          label: 'Error',
          bgColor: '#ffebee',
          textColor: '#c62828',
        };
      default:
        return {
          icon: <IconCircleCheck />,
          color: 'default' as const,
          label: 'Unknown',
          bgColor: '#f5f5f5',
          textColor: '#757575',
        };
    }
  };

  const config = getHealthConfig();

  return (
    <Tooltip title={`System Status: ${config.label}`} arrow>
      <Box sx={{ display: 'inline-flex' }}>
        <Chip
          icon={config.icon}
          label={config.label}
          color={config.color}
          size="small"
          sx={{
            fontWeight: 600,
            backgroundColor: config.bgColor,
            color: config.textColor,
            '& .MuiChip-icon': {
              color: config.textColor,
            },
          }}
        />
      </Box>
    </Tooltip>
  );
};

export default SystemHealthIndicator;
