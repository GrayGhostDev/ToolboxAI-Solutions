import React, { useState } from 'react';
import { Box, Chip, Tooltip, IconButton, Popover, Typography, Stack } from '@mui/material';
import {
  IconWifi,
  IconWifiOff,
  IconRefresh,
  IconInfoCircle,
  IconAlertTriangle,
  IconCircleX,
  IconCircleCheck,
} from '@tabler/icons-react';
import { usePusherContext } from '../contexts/PusherContext';

/**
 * Pusher Connection Status Component
 *
 * Displays the current Pusher connection status with visual indicators,
 * reconnection controls, and detailed connection information.
 */

interface PusherConnectionStatusProps {
  /**
   * Show detailed status in popover
   */
  showDetails?: boolean;
  /**
   * Show reconnect button
   */
  showReconnect?: boolean;
  /**
   * Compact mode (icon only)
   */
  compact?: boolean;
}

export const PusherConnectionStatus: React.FC<PusherConnectionStatusProps> = ({
  showDetails = true,
  showReconnect = true,
  compact = false,
}) => {
  const { state, reconnect } = usePusherContext();
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    if (showDetails) {
      setAnchorEl(event.currentTarget);
    }
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleReconnect = () => {
    reconnect();
    handleClose();
  };

  const getStatusConfig = () => {
    switch (state) {
      case 'connected':
        return {
          icon: <IconCircleCheck />,
          color: 'success' as const,
          label: 'Connected',
          bgColor: '#e8f5e9',
          textColor: '#2e7d32',
          description: 'Real-time connection is active',
        };
      case 'connecting':
        return {
          icon: <IconWifi />,
          color: 'info' as const,
          label: 'Connecting',
          bgColor: '#e3f2fd',
          textColor: '#1565c0',
          description: 'Establishing connection...',
        };
      case 'disconnected':
        return {
          icon: <IconWifiOff />,
          color: 'error' as const,
          label: 'Disconnected',
          bgColor: '#ffebee',
          textColor: '#c62828',
          description: 'Connection lost. Click to reconnect.',
        };
      case 'failed':
        return {
          icon: <IconCircleX />,
          color: 'error' as const,
          label: 'Failed',
          bgColor: '#ffebee',
          textColor: '#c62828',
          description: 'Connection failed. Please try again.',
        };
      case 'unavailable':
        return {
          icon: <IconAlertTriangle />,
          color: 'warning' as const,
          label: 'Unavailable',
          bgColor: '#fff3e0',
          textColor: '#e65100',
          description: 'Service temporarily unavailable',
        };
      default:
        return {
          icon: <IconInfoCircle />,
          color: 'default' as const,
          label: 'Unknown',
          bgColor: '#f5f5f5',
          textColor: '#757575',
          description: 'Connection status unknown',
        };
    }
  };

  const config = getStatusConfig();
  const open = Boolean(anchorEl);

  if (compact) {
    return (
      <Tooltip title={`${config.label}: ${config.description}`} arrow>
        <IconButton
          size="small"
          onClick={handleClick}
          sx={{
            color: config.textColor,
            '&:hover': {
              backgroundColor: config.bgColor,
            },
          }}
        >
          {config.icon}
        </IconButton>
      </Tooltip>
    );
  }

  return (
    <>
      <Tooltip title={showDetails ? 'Click for details' : config.description} arrow>
        <Box sx={{ display: 'inline-flex', cursor: showDetails ? 'pointer' : 'default' }}>
          <Chip
            icon={config.icon}
            label={config.label}
            color={config.color}
            size="small"
            onClick={handleClick}
            sx={{
              fontWeight: 600,
              backgroundColor: config.bgColor,
              color: config.textColor,
              '& .MuiChip-icon': {
                color: config.textColor,
              },
              cursor: showDetails ? 'pointer' : 'default',
            }}
          />
        </Box>
      </Tooltip>

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
          <Box sx={{ p: 2, minWidth: 250 }}>
            <Stack spacing={2}>
              <Box>
                <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                  Connection Status
                </Typography>
                <Stack direction="row" spacing={1} alignItems="center">
                  {config.icon}
                  <Typography variant="body2" color={config.textColor}>
                    {config.label}
                  </Typography>
                </Stack>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  {config.description}
                </Typography>
              </Box>

              {showReconnect && (state === 'disconnected' || state === 'failed') && (
                <Box>
                  <IconButton
                    size="small"
                    onClick={handleReconnect}
                    sx={{
                      color: 'primary.main',
                      '&:hover': {
                        backgroundColor: 'primary.light',
                      },
                    }}
                  >
                    <IconRefresh />
                    <Typography variant="button" sx={{ ml: 1 }}>
                      Reconnect
                    </Typography>
                  </IconButton>
                </Box>
              )}
            </Stack>
          </Box>
        </Popover>
      )}
    </>
  );
};

export default PusherConnectionStatus;

