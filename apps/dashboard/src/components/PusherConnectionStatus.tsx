/**
 * Pusher Connection Status Component
 *
 * Displays the current Pusher connection status with visual indicators,
 * reconnection controls, and detailed connection information.
 */

import React, { useState } from 'react';
import {
  Box,
  Chip,
  IconButton,
  Popover,
  Paper,
  Typography,
  Button,
  Stack,
  Divider,
  Tooltip,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';

import { usePusherConnection } from '../hooks/usePusher';
import { usePusherContext } from '../contexts/PusherContext';
import { ConnectionStateUtils } from '../utils/pusher';
import { PusherConnectionState } from '../types/pusher';

interface PusherConnectionStatusProps {
  /**
   * Show detailed status in popover
   */
  showDetails?: boolean;
  /**
   * Size of the status indicator
   */
  size?: 'small' | 'medium' | 'large';
  /**
   * Position of the component
   */
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'inline';
  /**
   * Custom styling
   */
  sx?: any;
}

/**
 * Connection Status Component
 */
export const PusherConnectionStatus: React.FC<PusherConnectionStatusProps> = ({
  showDetails = true,
  size = 'medium',
  position = 'inline',
  sx = {},
}) => {
  const { isConnected, isConnecting, state, stats, lastError, reconnect } = usePusherConnection();
  const { connectionState } = usePusherContext();
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const [isReconnecting, setIsReconnecting] = useState(false);

  const handleStatusClick = (event: React.MouseEvent<HTMLElement>) => {
    if (showDetails) {
      setAnchorEl(event.currentTarget);
    }
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleReconnect = async () => {
    setIsReconnecting(true);
    try {
      await reconnect();
    } catch (error) {
      console.error('Reconnection failed:', error);
    } finally {
      setIsReconnecting(false);
      handleClose();
    }
  };

  // Determine status properties
  const getStatusProps = () => {
    if (isConnecting || isReconnecting) {
      return {
        color: 'info' as const,
        icon: <WifiIcon />,
        label: 'Connecting...',
        showProgress: true,
      };
    }

    if (isConnected) {
      return {
        color: 'success' as const,
        icon: <CheckCircleIcon />,
        label: 'Connected',
        showProgress: false,
      };
    }

    if (lastError) {
      return {
        color: 'error' as const,
        icon: <ErrorIcon />,
        label: 'Error',
        showProgress: false,
      };
    }

    return {
      color: 'warning' as const,
      icon: <WifiOffIcon />,
      label: 'Disconnected',
      showProgress: false,
    };
  };

  const statusProps = getStatusProps();
  const open = Boolean(anchorEl);

  // Format uptime
  const formatUptime = (connectedAt?: string) => {
    if (!connectedAt) return 'N/A';
    
    const uptime = Date.now() - new Date(connectedAt).getTime();
    const minutes = Math.floor(uptime / 60000);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    }
    return `${minutes}m`;
  };

  // Position styles
  const getPositionStyles = () => {
    if (position === 'inline') return {};
    
    const baseStyles = {
      position: 'fixed' as const,
      zIndex: 1000,
    };
    
    switch (position) {
      case 'top-right':
        return { ...baseStyles, top: 16, right: 16 };
      case 'top-left':
        return { ...baseStyles, top: 16, left: 16 };
      case 'bottom-right':
        return { ...baseStyles, bottom: 16, right: 16 };
      case 'bottom-left':
        return { ...baseStyles, bottom: 16, left: 16 };
      default:
        return baseStyles;
    }
  };

  return (
    <Box sx={{ ...getPositionStyles(), ...sx }}>
      <Tooltip title={ConnectionStateUtils.getStatusMessage(connectionState)} arrow>
        <Chip
          icon={statusProps.icon}
          label={statusProps.label}
          color={statusProps.color}
          size={size}
          onClick={showDetails ? handleStatusClick : undefined}
          sx={{
            cursor: showDetails ? 'pointer' : 'default',
            '& .MuiChip-icon': {
              animation: (isConnecting || isReconnecting) ? 'pulse 1.5s infinite' : 'none',
            },
            '@keyframes pulse': {
              '0%': { opacity: 1 },
              '50%': { opacity: 0.5 },
              '100%': { opacity: 1 },
            },
          }}
        />
      </Tooltip>

      {statusProps.showProgress && (
        <LinearProgress
          color={statusProps.color}
          sx={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            height: 2,
          }}
        />
      )}

      {showDetails && (
        <Popover
          open={open}
          anchorEl={anchorEl}
          onClose={handleClose}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'center',
          }}
          transformOrigin={{
            vertical: 'top',
            horizontal: 'center',
          }}
        >
          <Paper sx={{ p: 2, minWidth: 300, maxWidth: 400 }}>
            <Stack spacing={2}>
              {/* Header */}
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Typography variant="h6" component="h3">
                  Connection Status
                </Typography>
                <IconButton
                  size="small"
                  onClick={handleReconnect}
                  disabled={isConnecting || isReconnecting}
                  title="Reconnect"
                >
                  <RefreshIcon />
                </IconButton>
              </Box>

              {/* Status Alert */}
              {lastError ? (
                <Alert severity="error" variant="outlined">
                  <Typography variant="body2">
                    {lastError.message}
                  </Typography>
                </Alert>
              ) : isConnected ? (
                <Alert severity="success" variant="outlined">
                  <Typography variant="body2">
                    Real-time connection is active
                  </Typography>
                </Alert>
              ) : (
                <Alert severity="warning" variant="outlined">
                  <Typography variant="body2">
                    Real-time features are unavailable
                  </Typography>
                </Alert>
              )}

              <Divider />

              {/* Connection Details */}
              <Stack spacing={1}>
                <Typography variant="subtitle2" color="text.secondary">
                  Connection Details
                </Typography>

                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2">Status:</Typography>
                  <Typography variant="body2" fontWeight="medium">
                    {ConnectionStateUtils.getStatusMessage(connectionState)}
                  </Typography>
                </Box>

                {stats.connectedAt && (
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="body2">Uptime:</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {formatUptime(stats.connectedAt)}
                    </Typography>
                  </Box>
                )}

                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2">Reconnect Attempts:</Typography>
                  <Typography variant="body2" fontWeight="medium">
                    {stats.reconnectAttempts}
                  </Typography>
                </Box>

                {stats.latency !== undefined && (
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="body2">Latency:</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {stats.latency}ms
                    </Typography>
                  </Box>
                )}
              </Stack>

              <Divider />

              {/* Message Statistics */}
              <Stack spacing={1}>
                <Typography variant="subtitle2" color="text.secondary">
                  Message Statistics
                </Typography>

                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2">Messages Sent:</Typography>
                  <Typography variant="body2" fontWeight="medium">
                    {stats.messagesSent.toLocaleString()}
                  </Typography>
                </Box>

                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2">Messages Received:</Typography>
                  <Typography variant="body2" fontWeight="medium">
                    {stats.messagesReceived.toLocaleString()}
                  </Typography>
                </Box>

                {stats.lastMessageAt && (
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="body2">Last Message:</Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {new Date(stats.lastMessageAt).toLocaleTimeString()}
                    </Typography>
                  </Box>
                )}
              </Stack>

              {/* Actions */}
              <Stack direction="row" spacing={1} justifyContent="flex-end">
                {!isConnected && (
                  <Button
                    variant="contained"
                    size="small"
                    onClick={handleReconnect}
                    disabled={isConnecting || isReconnecting}
                    startIcon={<RefreshIcon />}
                  >
                    {isReconnecting ? 'Reconnecting...' : 'Reconnect'}
                  </Button>
                )}
                <Button
                  variant="outlined"
                  size="small"
                  onClick={handleClose}
                >
                  Close
                </Button>
              </Stack>
            </Stack>
          </Paper>
        </Popover>
      )}
    </Box>
  );
};

/**
 * Minimal Connection Indicator
 */
export const PusherConnectionIndicator: React.FC<{
  size?: number;
  showTooltip?: boolean;
}> = ({ size = 12, showTooltip = true }) => {
  const { isConnected, isConnecting } = usePusherConnection();
  
  const getColor = () => {
    if (isConnecting) return '#2196f3'; // blue
    if (isConnected) return '#4caf50'; // green
    return '#f44336'; // red
  };
  
  const indicator = (
    <Box
      sx={{
        width: size,
        height: size,
        borderRadius: '50%',
        backgroundColor: getColor(),
        animation: isConnecting ? 'pulse 1.5s infinite' : 'none',
        '@keyframes pulse': {
          '0%': { opacity: 1 },
          '50%': { opacity: 0.5 },
          '100%': { opacity: 1 },
        },
      }}
    />
  );
  
  if (showTooltip) {
    return (
      <Tooltip
        title={isConnected ? 'Connected' : isConnecting ? 'Connecting...' : 'Disconnected'}
        arrow
      >
        {indicator}
      </Tooltip>
    );
  }
  
  return indicator;
};

export default PusherConnectionStatus;