/**
 * WebSocket Test Component
 * 
 * Comprehensive testing interface for WebSocket functionality
 */
import React, { useState, useEffect, useCallback } from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Chip from '@mui/material/Chip';
import Grid from '@mui/material/Grid';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import Divider from '@mui/material/Divider';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Tooltip from '@mui/material/Tooltip';
import {
  Send as SendIcon,
  Refresh as RefreshIcon,
  Clear as ClearIcon,
  WifiTethering as ConnectedIcon,
  WifiTetheringOff as DisconnectedIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon
} from '@mui/icons-material';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import {
  WebSocketState,
  WebSocketMessageType,
  WebSocketChannel,
  ContentGenerationRequest
} from '../../types/websocket';
export const WebSocketTest: React.FunctionComponent<Record<string, any>> = () => {
  const {
    state,
    isConnected,
    stats,
    error,
    connect,
    disconnect,
    reconnect,
    sendMessage,
    subscribe,
    unsubscribe,
    on,
    requestContent,
    onContentProgress
  } = useWebSocketContext();
  // Local state
  const [messageLog, setMessageLog] = useState<Array<{
    id: string;
    timestamp: Date;
    type: 'sent' | 'received' | 'error' | 'system';
    message: any;
  }>>([]);
  const [testMessage, setTestMessage] = useState('');
  const [selectedChannel, setSelectedChannel] = useState<WebSocketChannel>(WebSocketChannel.SYSTEM_EVENTS);
  const [activeSubscriptions, setActiveSubscriptions] = useState<string[]>([]);
  const [contentRequestId, setContentRequestId] = useState<string>('');
  const [contentProgress, setContentProgress] = useState<any>(null);
  // Add message to log
  const addToLog = useCallback((type: 'sent' | 'received' | 'error' | 'system', message: any) => {
    setMessageLog(prev => [{
      id: `${Date.now()}_${Math.random()}`,
      timestamp: new Date(),
      type,
      message
    }, ...prev].slice(0, 50)); // Keep last 50 messages
  }, []);
  // Setup message handlers
  useEffect(() => {
    // Subscribe to all message types for testing
    const handlers: Array<() => void> = [];
    // System notifications
    handlers.push(
      on(WebSocketMessageType.SYSTEM_NOTIFICATION, (data) => {
        addToLog('received', { type: 'SYSTEM_NOTIFICATION', data });
      })
    );
    // Connection events
    handlers.push(
      on(WebSocketMessageType.CONNECT, () => {
        addToLog('system', 'Connected to WebSocket server');
      })
    );
    handlers.push(
      on(WebSocketMessageType.DISCONNECT, () => {
        addToLog('system', 'Disconnected from WebSocket server');
      })
    );
    // Ping/Pong
    handlers.push(
      on(WebSocketMessageType.PONG, (data) => {
        addToLog('received', { type: 'PONG', data });
      })
    );
    // Content progress
    const unsubscribeProgress = onContentProgress((progress) => {
      setContentProgress(progress);
      addToLog('received', { type: 'CONTENT_PROGRESS', progress });
    });
    handlers.push(unsubscribeProgress);
    // Cleanup
    return () => {
      handlers.forEach(unsubscribe => unsubscribe());
    };
  }, [on, onContentProgress, addToLog]);
  // Handle connection
  const handleConnect = async () => {
    try {
      await connect();
      addToLog('system', 'Connection initiated');
    } catch (error) {
      addToLog('error', `Connection failed: ${error}`);
    }
  };
  const handleDisconnect = () => {
    disconnect('Manual disconnect');
    addToLog('system', 'Disconnected manually');
  };
  const handleReconnect = async () => {
    try {
      await reconnect();
      addToLog('system', 'Reconnection initiated');
    } catch (error) {
      addToLog('error', `Reconnection failed: ${error}`);
    }
  };
  // Send test message
  const handleSendMessage = async () => {
    if (!testMessage.trim()) return;
    try {
      const result = await sendMessage(
        WebSocketMessageType.USER_MESSAGE,
        { text: testMessage, timestamp: new Date().toISOString() },
        { channel: selectedChannel, awaitAcknowledgment: true, timeout: 5000 }
      );
      addToLog('sent', {
        type: 'USER_MESSAGE',
        channel: selectedChannel,
        payload: { text: testMessage },
        result
      });
      setTestMessage('');
    } catch (error) {
      addToLog('error', `Send failed: ${error}`);
    }
  };
  // Send ping
  const handleSendPing = async () => {
    try {
      await sendMessage(WebSocketMessageType.PING, { timestamp: Date.now() });
      addToLog('sent', { type: 'PING', timestamp: Date.now() });
    } catch (error) {
      addToLog('error', `Ping failed: ${error}`);
    }
  };
  // Subscribe to channel
  const handleSubscribeChannel = () => {
    const subscriptionId = subscribe(selectedChannel, (message) => {
      addToLog('received', { channel: selectedChannel, message });
    });
    setActiveSubscriptions(prev => [...prev, subscriptionId]);
    addToLog('system', `Subscribed to channel: ${selectedChannel} (ID: ${subscriptionId})`);
  };
  // Unsubscribe from channel
  const handleUnsubscribeChannel = (subscriptionId: string) => {
    unsubscribe(subscriptionId);
    setActiveSubscriptions(prev => prev.filter(id => id !== subscriptionId));
    addToLog('system', `Unsubscribed: ${subscriptionId}`);
  };
  // Request content generation
  const handleContentRequest = async () => {
    const request: ContentGenerationRequest = {
      subject: 'Mathematics',
      gradeLevel: 5,
      learningObjectives: ['Fractions', 'Decimals', 'Percentages'],
      environmentType: 'classroom',
      includeQuiz: true,
      difficultyLevel: 'intermediate',
      requestId: `test_${Date.now()}`,
      userId: 'test_user'
    };
    try {
      await requestContent(request);
      setContentRequestId(request.requestId);
      addToLog('sent', { type: 'CONTENT_REQUEST', request });
    } catch (error) {
      addToLog('error', `Content request failed: ${error}`);
    }
  };
  // Clear log
  const handleClearLog = () => {
    setMessageLog([]);
    addToLog('system', 'Log cleared');
  };
  // Get connection status color
  const getStatusColor = () => {
    switch (state) {
      case WebSocketState.CONNECTED:
        return 'success';
      case WebSocketState.CONNECTING:
      case WebSocketState.RECONNECTING:
        return 'warning';
      case WebSocketState.ERROR:
        return 'error';
      default:
        return 'default';
    }
  };
  // Get connection icon
  const getStatusIcon = () => {
    switch (state) {
      case WebSocketState.CONNECTED:
        return <ConnectedIcon color="success" />;
      case WebSocketState.DISCONNECTED:
        return <DisconnectedIcon color="disabled" />;
      case WebSocketState.ERROR:
        return <ErrorIcon color="error" />;
      default:
        return <CircularProgress size={20} />;
    }
  };
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        WebSocket Test Interface
      </Typography>
      {/* Connection Status */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <Box display="flex" alignItems="center" gap={1}>
              {getStatusIcon()}
              <Typography variant="h6">
                Status: <Chip label={state} color={getStatusColor()} size="small" />
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={4}>
            <Typography variant="body2">
              Messages Sent: {stats.messagesSent} | Received: {stats.messagesReceived}
            </Typography>
            <Typography variant="body2">
              Reconnect Attempts: {stats.reconnectAttempts}
            </Typography>
            {stats.latency && (
              <Typography variant="body2">
                Latency: {stats.latency}ms
              </Typography>
            )}
          </Grid>
          <Grid item xs={12} md={4}>
            <Box display="flex" gap={1}>
              <Button
                variant="contained"
                color="primary"
                onClick={(e: React.MouseEvent) => handleConnect}
                disabled={isConnected}
                startIcon={<ConnectedIcon />}
              >
                Connect
              </Button>
              <Button
                variant="outlined"
                color="secondary"
                onClick={(e: React.MouseEvent) => handleDisconnect}
                disabled={!isConnected}
                startIcon={<DisconnectedIcon />}
              >
                Disconnect
              </Button>
              <Tooltip title="Reconnect">
                <IconButton onClick={(e: React.MouseEvent) => handleReconnect} color="primary">
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </Grid>
        </Grid>
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error.message} ({error.code})
          </Alert>
        )}
      </Paper>
      {/* Message Controls */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Message Testing
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Test Message"
              value={testMessage}
              onChange={(e) => setTestMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              disabled={!isConnected}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Channel</InputLabel>
              <Select
                value={selectedChannel}
                onChange={(e) => setSelectedChannel(e.target.value as WebSocketChannel)}
                label="Channel"
                disabled={!isConnected}
              >
                {Object.values(WebSocketChannel).map(channel => (
                  <MenuItem key={channel} value={channel}>
                    {channel}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
            <Box display="flex" gap={1} height="100%">
              <Button
                fullWidth
                variant="contained"
                onClick={(e: React.MouseEvent) => handleSendMessage}
                disabled={!isConnected || !testMessage}
                startIcon={<SendIcon />}
              >
                Send
              </Button>
              <Button
                variant="outlined"
                onClick={(e: React.MouseEvent) => handleSendPing}
                disabled={!isConnected}
              >
                Ping
              </Button>
            </Box>
          </Grid>
        </Grid>
        <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            onClick={(e: React.MouseEvent) => handleSubscribeChannel}
            disabled={!isConnected}
          >
            Subscribe to {selectedChannel}
          </Button>
          <Button
            variant="outlined"
            color="warning"
            onClick={(e: React.MouseEvent) => handleContentRequest}
            disabled={!isConnected}
          >
            Test Content Generation
          </Button>
        </Box>
      </Paper>
      {/* Active Subscriptions */}
      {activeSubscriptions.length > 0 && (
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            Active Subscriptions
          </Typography>
          <Box display="flex" gap={1} flexWrap="wrap">
            {activeSubscriptions.map(id => (
              <Chip
                key={id}
                label={id}
                onDelete={() => handleUnsubscribeChannel(id)}
                color="primary"
                variant="outlined"
              />
            ))}
          </Box>
        </Paper>
      )}
      {/* Content Generation Progress */}
      {contentProgress && (
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            Content Generation Progress
          </Typography>
          <Box>
            <Typography>Request ID: {contentProgress.requestId}</Typography>
            <Typography>Stage: {contentProgress.stage}</Typography>
            <Typography>Progress: {contentProgress.percentage}%</Typography>
            {contentProgress.currentAgent && (
              <Typography>Current Agent: {contentProgress.currentAgent}</Typography>
            )}
            {contentProgress.message && (
              <Typography>Message: {contentProgress.message}</Typography>
            )}
          </Box>
        </Paper>
      )}
      {/* Message Log */}
      <Paper sx={{ p: 2 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Message Log ({messageLog.length})
          </Typography>
          <IconButton onClick={(e: React.MouseEvent) => handleClearLog} size="small">
            <ClearIcon />
          </IconButton>
        </Box>
        <List sx={{ maxHeight: 400, overflow: 'auto', bgcolor: 'background.default' }}>
          {messageLog.map((entry) => (
            <React.Fragment key={entry.id}>
              <ListItem>
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={1}>
                      {entry.type === 'sent' && <SendIcon fontSize="small" color="primary" />}
                      {entry.type === 'received' && <SuccessIcon fontSize="small" color="success" />}
                      {entry.type === 'error' && <ErrorIcon fontSize="small" color="error" />}
                      {entry.type === 'system' && <Chip label="SYSTEM" size="small" />}
                      <Typography variant="caption">
                        {entry.timestamp.toLocaleTimeString()}
                      </Typography>
                    </Box>
                  }
                  secondary={
                    <Typography
                      variant="body2"
                      component="pre"
                      sx={{ 
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                        fontFamily: 'monospace',
                        fontSize: '0.85rem'
                      }}
                    >
                      {typeof entry.message === 'string' 
                        ? entry.message 
                        : JSON.stringify(entry.message, null, 2)}
                    </Typography>
                  }
                />
              </ListItem>
              <Divider />
            </React.Fragment>
          ))}
        </List>
      </Paper>
    </Box>
  );
};