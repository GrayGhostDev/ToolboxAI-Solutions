/**
 * WebSocket Connection Status Component
 * Displays real-time connection status and statistics
 */

import React, { useState } from 'react';
import {
  Box,
  IconButton,
  Tooltip,
  Typography,
  Paper,
  Collapse,
  Chip,
  LinearProgress,
  Button,
  Alert,
  Stack,
  Divider,
  Grid
} from '@mui/material';
import {
  WifiTethering as ConnectedIcon,
  WifiTetheringOff as DisconnectedIcon,
  Sync as ReconnectingIcon,
  Error as ErrorIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Refresh as RefreshIcon,
  Speed as SpeedIcon,
  Send as SendIcon,
  CallReceived as ReceiveIcon
} from '@mui/icons-material';
import { useWebSocketStatus } from '../../hooks/websocket';
import { useAppSelector } from '../../store';
import { selectWebSocketStats, selectWebSocketError } from '../../store/slices/realtimeSlice';
import { WebSocketState } from '../../types/websocket';

interface ConnectionStatusProps {
  variant?: 'compact' | 'detailed';
  showStats?: boolean;
  position?: 'fixed' | 'relative';
  floatingPosition?: {
    bottom?: number | string;
    right?: number | string;
    top?: number | string;
    left?: number | string;
  };
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  variant = 'compact',
  showStats = true,
  position = 'relative',
  floatingPosition = { bottom: 20, right: 20 }
}) => {
  const status = useWebSocketStatus();
  const stats = useAppSelector(selectWebSocketStats);
  const error = useAppSelector(selectWebSocketError);
  const [expanded, setExpanded] = useState(false);

  // Get status color
  const getStatusColor = (): 'success' | 'warning' | 'error' | 'info' => {
    switch (status.state) {
      case WebSocketState.CONNECTED:
        return 'success';
      case WebSocketState.CONNECTING:
      case WebSocketState.RECONNECTING:
        return 'warning';
      case WebSocketState.ERROR:
        return 'error';
      default:
        return 'info';
    }
  };

  // Get status icon
  const getStatusIcon = () => {
    switch (status.state) {
      case WebSocketState.CONNECTED:
        return <ConnectedIcon fontSize="small" />;
      case WebSocketState.CONNECTING:
      case WebSocketState.RECONNECTING:
        return <ReconnectingIcon fontSize="small" className="spin-animation" />;
      case WebSocketState.ERROR:
        return <ErrorIcon fontSize="small" />;
      default:
        return <DisconnectedIcon fontSize="small" />;
    }
  };

  // Get status text
  const getStatusText = () => {
    switch (status.state) {
      case WebSocketState.CONNECTED:
        return 'Connected';
      case WebSocketState.CONNECTING:
        return 'Connecting...';
      case WebSocketState.RECONNECTING:
        return `Reconnecting (${stats.reconnectAttempts})...`;
      case WebSocketState.ERROR:
        return 'Connection Error';
      case WebSocketState.DISCONNECTED:
        return 'Disconnected';
      default:
        return 'Unknown';
    }
  };

  // Format latency
  const formatLatency = (ms: number | null) => {
    if (ms === null) return 'N/A';
    if (ms < 100) return `${ms}ms ✅`;
    if (ms < 300) return `${ms}ms ⚠️`;
    return `${ms}ms ❌`;
  };

  // Compact view (icon only with tooltip)
  if (variant === 'compact' && !expanded) {
    return (
      <Box
        sx={{
          position: position === 'fixed' ? 'fixed' : 'relative',
          ...(position === 'fixed' ? floatingPosition : {}),
          zIndex: 1000
        }}
      >
        <Tooltip
          title={
            <Box>
              <Typography variant="caption">
                Status: {getStatusText()}
              </Typography>
              {showStats && status.isConnected && (
                <>
                  <br />
                  <Typography variant="caption">
                    Latency: {formatLatency(stats.latency)}
                  </Typography>
                  <br />
                  <Typography variant="caption">
                    Messages: ↑{stats.messagesSent} ↓{stats.messagesReceived}
                  </Typography>
                </>
              )}
              {error && (
                <>
                  <br />
                  <Typography variant="caption" color="error">
                    Error: {error.message}
                  </Typography>
                </>
              )}
            </Box>
          }
        >
          <IconButton
            size="small"
            onClick={() => setExpanded(!expanded)}
            sx={{
              backgroundColor: 'background.paper',
              border: '1px solid',
              borderColor: `${getStatusColor()}.main`,
              '&:hover': {
                backgroundColor: 'background.default'
              }
            }}
          >
            {getStatusIcon()}
          </IconButton>
        </Tooltip>
      </Box>
    );
  }

  // Detailed view
  return (
    <Paper
      elevation={3}
      sx={{
        position: position === 'fixed' ? 'fixed' : 'relative',
        ...(position === 'fixed' ? floatingPosition : {}),
        p: 2,
        minWidth: 300,
        maxWidth: 400,
        zIndex: 1000
      }}
    >
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
        <Box display="flex" alignItems="center" gap={1}>
          {getStatusIcon()}
          <Typography variant="subtitle2" fontWeight="bold">
            WebSocket Connection
          </Typography>
        </Box>
        {variant === 'compact' && (
          <IconButton size="small" onClick={() => setExpanded(!expanded)}>
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        )}
      </Box>

      {/* Status */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Chip
          label={getStatusText()}
          color={getStatusColor()}
          size="small"
        />
        <Stack direction="row" spacing={1}>
          <Button
            size="small"
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={onReconnect}
            disabled={status.state === WebSocketState.CONNECTING}
          >
            Reconnect
          </Button>
          <IconButton
            size="small"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Stack>
      </Box>

      <Collapse in={expanded}>

      {/* Progress bar for connecting states */}
      {(status.isConnecting) && (
        <LinearProgress color={getStatusColor()} sx={{ mb: 2 }} />
      )}

      {/* Error alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error.message}
          {error.code && (
            <Typography variant="caption" display="block">
              Code: {error.code}
            </Typography>
          )}
        </Alert>
      )}

      {/* Statistics */}
      {showStats && (variant === 'detailed' || expanded) && (
        <>
          <Divider sx={{ my: 1 }} />
          <Typography variant="subtitle2" gutterBottom>
            Statistics
          </Typography>

          <Grid container spacing={1}>
            <Grid item xs={6}>
              <Box display="flex" alignItems="center" gap={0.5}>
                <SpeedIcon fontSize="small" color="action" />
                <Typography variant="caption">
                  Latency: {formatLatency(stats.latency)}
                </Typography>
              </Box>
            </Grid>

            <Grid item xs={6}>
              <Box display="flex" alignItems="center" gap={0.5}>
                <RefreshIcon fontSize="small" color="action" />
                <Typography variant="caption">
                  Reconnects: {stats.reconnectAttempts}
                </Typography>
              </Box>
            </Grid>

            <Grid item xs={6}>
              <Box display="flex" alignItems="center" gap={0.5}>
                <SendIcon fontSize="small" color="primary" />
                <Typography variant="caption">
                  Sent: {stats.messagesSent}
                </Typography>
              </Box>
            </Grid>

            <Grid item xs={6}>
              <Box display="flex" alignItems="center" gap={0.5}>
                <ReceiveIcon fontSize="small" color="success" />
                <Typography variant="caption">
                  Received: {stats.messagesReceived}
                </Typography>
              </Box>
            </Grid>
          </Grid>

          {/* Last activity times */}
          {status.lastConnected && (
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              Last connected: {new Date(status.lastConnected).toLocaleTimeString()}
            </Typography>
          )}

          {status.lastDisconnected && (
            <Typography variant="caption" display="block">
              Last disconnected: {new Date(status.lastDisconnected).toLocaleTimeString()}
            </Typography>
          )}
        </>
      )}
      </Collapse>
    </Paper>
  );
};

// Mini status indicator for app bar
export const ConnectionStatusIndicator: React.FC = () => {
  const status = useWebSocketStatus();

  const getColor = () => {
    switch (status.state) {
      case WebSocketState.CONNECTED:
        return '#4caf50';
      case WebSocketState.CONNECTING:
      case WebSocketState.RECONNECTING:
        return '#ff9800';
      case WebSocketState.ERROR:
        return '#f44336';
      default:
        return '#9e9e9e';
    }
  };

  const isAnimating = status.state === WebSocketState.CONNECTING ||
                      status.state === WebSocketState.RECONNECTING;

  return (
    <Tooltip title={`WebSocket: ${status.state}`}>
      <Box
        sx={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          backgroundColor: getColor(),
          animation: isAnimating ? 'pulse 1.5s infinite' : 'none',
          '@keyframes pulse': {
            '0%': { opacity: 1 },
            '50%': { opacity: 0.4 },
            '100%': { opacity: 1 }
          }
        }}
      />
    </Tooltip>
  );
};
