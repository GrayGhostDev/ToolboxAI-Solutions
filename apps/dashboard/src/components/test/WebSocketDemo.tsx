/**
 * WebSocket Demo Component
 * Demonstrates real-time WebSocket and Pusher integration
 */

import React, { useEffect, useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import TextField from '@mui/material/TextField';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import CircularProgress from '@mui/material/CircularProgress';
import { pusherService } from '../../services/pusher';
import { WebSocketState, WebSocketMessageType } from '../../types/websocket';

interface Message {
  id: string;
  timestamp: string;
  type: string;
  content: string;
}

const WebSocketDemo: React.FunctionComponent<Record<string, any>> = () => {
  const [state, setState] = useState<WebSocketState>(WebSocketState.DISCONNECTED);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [messageInput, setMessageInput] = useState('');
  const [subscriptionId, setSubscriptionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState({
    messagesSent: 0,
    messagesReceived: 0,
    reconnectionAttempts: 0,
    lastActivity: null as Date | null
  });

  // Connect on component mount
  useEffect(() => {
    const connectToWebSocket = async () => {
      try {
        setState(WebSocketState.CONNECTING);
        await pusherService.connect();
        setState(WebSocketState.CONNECTED);
        setIsConnected(true);

        // Subscribe to demo channel
        const subId = pusherService.subscribe('demo-channel', (message) => {
          const newMessage: Message = {
            id: Date.now().toString(),
            timestamp: new Date().toLocaleTimeString(),
            type: message.type || 'message',
            content: JSON.stringify(message.payload || message)
          };
          setMessages(prev => [...prev, newMessage]);
          setStats(prev => ({ ...prev, messagesReceived: prev.messagesReceived + 1 }));
        });

        setSubscriptionId(subId);
      } catch (err) {
        setState(WebSocketState.ERROR);
        setError(err instanceof Error ? err.message : 'Connection failed');
      }
    };

    connectToWebSocket();

    return () => {
      if (subscriptionId) {
        pusherService.unsubscribe(subscriptionId);
      }
      pusherService.disconnect();
    };
  }, []);

  const handleSendMessage = () => {
    if (messageInput.trim()) {
      pusherService.send(WebSocketMessageType.MESSAGE, {
        text: messageInput,
        timestamp: new Date().toISOString()
      });
      setMessageInput('');
      setStats(prev => ({ ...prev, messagesSent: prev.messagesSent + 1 }));
    }
  };

  const handleTestNotification = () => {
    pusherService.send(WebSocketMessageType.SYSTEM_NOTIFICATION, {
      type: 'info',
      title: 'Test Notification',
      message: 'This is a test notification from the WebSocket demo!',
      timestamp: new Date().toISOString()
    });
    setStats(prev => ({ ...prev, messagesSent: prev.messagesSent + 1 }));
  };

  const handleTestProgress = () => {
    pusherService.send(WebSocketMessageType.CONTENT_PROGRESS, {
      taskId: 'demo-task',
      progress: Math.floor(Math.random() * 100),
      status: 'processing',
      timestamp: new Date().toISOString()
    });
    setStats(prev => ({ ...prev, messagesSent: prev.messagesSent + 1 }));
  };

  const handleConnect = async () => {
    try {
      setState(WebSocketState.CONNECTING);
      await pusherService.connect();
      setState(WebSocketState.CONNECTED);
      setIsConnected(true);
      setError(null);
    } catch (err) {
      setState(WebSocketState.ERROR);
      setError(err instanceof Error ? err.message : 'Connection failed');
    }
  };

  const handleDisconnect = () => {
    pusherService.disconnect();
    setState(WebSocketState.DISCONNECTED);
    setIsConnected(false);
  };

  const getStateColor = (state: WebSocketState) => {
    switch (state) {
      case WebSocketState.CONNECTED:
        return 'success';
      case WebSocketState.CONNECTING:
        return 'warning';
      case WebSocketState.DISCONNECTED:
        return 'default';
      case WebSocketState.ERROR:
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box sx={{ p: 3, maxWidth: 800, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom>
        WebSocket & Pusher Demo
      </Typography>

      <Typography variant="body1" color="text.secondary" paragraph>
        This component demonstrates the real-time WebSocket and Pusher integration.
        It shows connection status, message handling, and real-time features.
      </Typography>

      {/* Connection Status */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Connection Status
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
            <Chip
              label={state}
              color={getStateColor(state) as any}
              icon={state === WebSocketState.CONNECTING ? <CircularProgress size={16} /> : undefined}
            />
            <Chip
              label={isConnected ? 'Connected' : 'Disconnected'}
              color={isConnected ? 'success' : 'default'}
            />
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Error: {error}
            </Alert>
          )}

          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              onClick={(e: React.MouseEvent) => handleConnect}
              disabled={isConnected}
            >
              Connect
            </Button>
            <Button
              variant="outlined"
              onClick={(e: React.MouseEvent) => handleDisconnect}
              disabled={!isConnected}
            >
              Disconnect
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Statistics */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Statistics
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Messages Sent
              </Typography>
              <Typography variant="h6">
                {stats.messagesSent}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Messages Received
              </Typography>
              <Typography variant="h6">
                {stats.messagesReceived}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Reconnection Attempts
              </Typography>
              <Typography variant="h6">
                {stats.reconnectionAttempts}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Last Activity
              </Typography>
              <Typography variant="h6">
                {stats.lastActivity ? new Date(stats.lastActivity).toLocaleTimeString() : 'Never'}
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Message Input */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Send Messages
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <TextField
              fullWidth
              label="Message"
              value={messageInput}
              onChange={(e) => setMessageInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              disabled={!isConnected}
            />
            <Button
              variant="contained"
              onClick={(e: React.MouseEvent) => handleSendMessage}
              disabled={!isConnected || !messageInput.trim()}
            >
              Send
            </Button>
          </Box>

          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              onClick={(e: React.MouseEvent) => handleTestNotification}
              disabled={!isConnected}
            >
              Test Notification
            </Button>
            <Button
              variant="outlined"
              onClick={(e: React.MouseEvent) => handleTestProgress}
              disabled={!isConnected}
            >
              Test Progress Update
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Messages */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Received Messages
          </Typography>
          {messages.length === 0 ? (
            <Typography color="text.secondary">
              No messages received yet. Send a message or wait for real-time updates.
            </Typography>
          ) : (
            <List sx={{ maxHeight: 300, overflow: 'auto' }}>
              {messages.map((message) => (
                <ListItem key={message.id} divider>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                        <Chip label={message.type} size="small" />
                        <Typography variant="body2" color="text.secondary">
                          {message.timestamp}
                        </Typography>
                      </Box>
                    }
                    secondary={message.content}
                  />
                </ListItem>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      {/* Instructions */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            How to Test
          </Typography>
          <Typography variant="body2" paragraph>
            1. <strong>Connect:</strong> Click the Connect button to establish WebSocket connection
          </Typography>
          <Typography variant="body2" paragraph>
            2. <strong>Send Messages:</strong> Type a message and click Send to test message sending
          </Typography>
          <Typography variant="body2" paragraph>
            3. <strong>Test Features:</strong> Use the Test buttons to simulate different types of real-time events
          </Typography>
          <Typography variant="body2" paragraph>
            4. <strong>Backend Trigger:</strong> Use the backend API to trigger events:
            <br />
            <code>
              {`curl -X POST http://localhost:8008/realtime/trigger -H "Content-Type: application/json" -d '{"channel": "demo-channel", "event": "test", "data": {"message": "Hello from backend!"}}'`}
            </code>
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default WebSocketDemo;
