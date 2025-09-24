/**
 * System Health Indicator Component
 * 
 * Visual indicator for overall agent system health status.
 * 
 * @author ToolboxAI Team
 * @created 2025-09-21
 * @version 1.0.0
 */

import React from 'react';
import {
  Box,
  Chip,
  Tooltip,
  CircularProgress,
} from '@mui/material';
import {
  CheckCircle as HealthyIcon,
  Warning as DegradedIcon,
  Error as ErrorIcon,
  WifiOff as DisconnectedIcon,
} from '@mui/icons-material';

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
        color: 'default' as const,
        icon: <DisconnectedIcon />,
        label: 'Disconnected',
        tooltip: 'Not connected to real-time updates'
      };
    }

    switch (status) {
      case 'healthy':
        return {
          color: 'success' as const,
          icon: <HealthyIcon />,
          label: 'Healthy',
          tooltip: 'All systems operational'
        };
      case 'degraded':
        return {
          color: 'warning' as const,
          icon: <DegradedIcon />,
          label: 'Degraded',
          tooltip: 'Some agents experiencing issues'
        };
      case 'error':
        return {
          color: 'error' as const,
          icon: <ErrorIcon />,
          label: 'Error',
          tooltip: 'Critical system issues detected'
        };
      default:
        return {
          color: 'default' as const,
          icon: <CircularProgress size={16} />,
          label: 'Unknown',
          tooltip: 'System status unknown'
        };
    }
  };

  const config = getHealthConfig();

  return (
    <Tooltip title={config.tooltip}>
      <Chip
        icon={config.icon}
        label={config.label}
        color={config.color}
        variant="outlined"
        size="small"
      />
    </Tooltip>
  );
};

export default SystemHealthIndicator;
