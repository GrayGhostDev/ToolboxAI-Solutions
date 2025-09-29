import { Box, Button, Typography, Paper, Stack, Grid, Container, IconButton, Avatar, Card, CardContent, CardActions, List, ListItem, ListItemText, Divider, TextField, Select, MenuItem, Chip, Badge, Alert, CircularProgress, LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions, Drawer, AppBar, Toolbar, Tabs, Tab, Menu, Tooltip, Checkbox, Radio, RadioGroup, FormControl, FormControlLabel, InputLabel, Switch, Slider, Rating, Autocomplete, Skeleton, Table } from '../utils/mui-imports';
/**
 * Pusher Usage Examples for ToolboxAI Dashboard
 *
 * This file demonstrates how to use the comprehensive Pusher service
 * with various React hooks and components.
 */

import React, { useEffect, useState } from 'react';

// Import Pusher hooks and utilities
import {
  usePusher,
  usePusherChannel,
  usePusherConnection,
  usePusherEvent,
  usePusherSend,
  usePusherPresence
} from '../hooks/usePusher';
import {
  usePusherContext,
  usePusherState,
  usePusherChannels,
  usePusherMessaging
} from '../contexts/PusherContext';
import {
  ChannelNameGenerator,
  EVENT_NAMES,
  MessageFormatter,
  ConnectionStateUtils
} from '../utils/pusher';
import {
  PusherChannelType,
  PusherChannels,
  PusherEvents
} from '../types/pusher';
import { WebSocketMessageType } from '../types/websocket';
import { PusherConnectionStatus } from '../components/PusherConnectionStatus';

/**
 * Example 1: Basic Connection Monitoring
 */
export const BasicConnectionExample: React.FC = () => {
  const { isConnected, isConnecting, state, stats } = usePusherConnection();

  return (
    <Card>
      <CardContent>
        <Typography order={6} gutterBottom>
          Basic Connection Monitoring
        </Typography>

        <Stack spacing={2}>
          <PusherConnectionStatus size="medium" />

          <Box>
            <Typography size="sm" color="text.secondary">
              Status: {ConnectionStateUtils.getStatusMessage(state)}
            </Typography>
            <Typography size="sm" color="text.secondary">
              Messages Sent: {stats.messagesSent}
            </Typography>
            <Typography size="sm" color="text.secondary">
              Messages Received: {stats.messagesReceived}
            </Typography>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
};

/**
 * Example 2: Channel Subscription
 */
export const ChannelSubscriptionExample: React.FC = () => {
  const [messages, setMessages] = useState<any[]>([]);
  const [channelName, setChannelName] = useState('dashboard-updates');

  // Subscribe to a channel with event handlers
  const { isSubscribed, subscriptionError } = usePusherChannel(
    channelName,
    {
      [EVENT_NAMES.CONTENT_GENERATION.PROGRESS]: (data) => {
        setMessages(prev => [...prev, {
          type: 'content-progress',
          data,
          timestamp: new Date().toISOString()
        }]);
      },
      [EVENT_NAMES.USER.NOTIFICATION]: (data) => {
        setMessages(prev => [...prev, {
          type: 'notification',
          data,
          timestamp: new Date().toISOString()
        }]);
      },
      [WebSocketMessageType.SYSTEM_ALERT]: (data) => {
        setMessages(prev => [...prev, {
          type: 'system-alert',
          data,
          timestamp: new Date().toISOString()
        }]);
      }
    },
    {
      enabled: true,
      channelType: PusherChannelType.PUBLIC,
      autoSubscribe: true
    }
  );

  return (
    <Card>
      <CardContent>
        <Typography order={6} gutterBottom>
          Channel Subscription Example
        </Typography>

        <Stack spacing={2}>
          <TextField
            label="Channel Name"
            value={channelName}
            onChange={(e) => setChannelName(e.target.value)}
            size="small"
          />

          <Box display="flex" gap={1} alignItems="center">
            <Chip
              label={isSubscribed ? 'Subscribed' : 'Not Subscribed'}
              color={isSubscribed ? 'success' : 'default'}
              size="small"
            />
            {subscriptionError && (
              <Chip
                label="Error"
                color="red"
                size="small"
                title={subscriptionError.message}
              />
            )}
          </Box>

          {subscriptionError && (
            <Alert severity="error">
              Subscription Error: {subscriptionError.message}
            </Alert>
          )}

          <Typography variant="subtitle2">
            Recent Messages ({messages.length}):
          </Typography>

          <List dense style={{ maxHeight: 200, overflow: 'auto' }}>
            {messages.slice(-10).map((message, index) => (
              <ListItem key={index}>
                <ListItemText
                  primary={`${message.type}: ${JSON.stringify(message.data).substring(0, 100)}...`}
                  secondary={new Date(message.timestamp).toLocaleTimeString()}
                />
              </ListItem>
            ))}
            {messages.length === 0 && (
              <ListItem>
                <ListItemText primary="No messages received yet" />
              </ListItem>
            )}
          </List>
        </Stack>
      </CardContent>
    </Card>
  );
};

/**
 * Example 3: Message Sending
 */
export const MessageSendingExample: React.FC = () => {
  const { sendMessage, isSending, lastError } = usePusherSend();
  const [messageText, setMessageText] = useState('');
  const [targetChannel, setTargetChannel] = useState('public-chat');
  const [sentMessages, setSentMessages] = useState<string[]>([]);

  const handleSendMessage = async () => {
    if (!messageText.trim()) return;

    try {
      await sendMessage(
        WebSocketMessageType.USER_MESSAGE,
        {
          text: messageText,
          timestamp: new Date().toISOString(),
          sender: 'Current User'
        },
        {
          channel: targetChannel,
          awaitAcknowledgment: true,
          timeout: 5000
        }
      );

      setSentMessages(prev => [...prev, `${messageText} (to ${targetChannel})`]);
      setMessageText('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography order={6} gutterBottom>
          Message Sending Example
        </Typography>

        <Stack spacing={2}>
          <TextField
            label="Target Channel"
            value={targetChannel}
            onChange={(e) => setTargetChannel(e.target.value)}
            size="small"
            placeholder="e.g., public-chat, private-user-123"
          />

          <TextField
            label="Message"
            value={messageText}
            onChange={(e) => setMessageText(e.target.value)}
            multiline
            rows={2}
            placeholder="Type your message here..."
          />

          <Button
            variant="filled"
            onClick={handleSendMessage}
            disabled={isSending || !messageText.trim()}
          >
            {isSending ? 'Sending...' : 'Send Message'}
          </Button>

          {lastError && (
            <Alert severity="error">
              Error: {lastError.message}
            </Alert>
          )}

          <Divider />

          <Typography variant="subtitle2">
            Sent Messages:
          </Typography>

          <List dense style={{ maxHeight: 150, overflow: 'auto' }}>
            {sentMessages.slice(-5).map((message, index) => (
              <ListItem key={index}>
                <ListItemText primary={message} />
              </ListItem>
            ))}
            {sentMessages.length === 0 && (
              <ListItem>
                <ListItemText primary="No messages sent yet" />
              </ListItem>
            )}
          </List>
        </Stack>
      </CardContent>
    </Card>
  );
};

/**
 * Example 4: Content Generation Monitoring
 */
export const ContentGenerationExample: React.FC = () => {
  const { subscribeToContentGeneration, triggerContentRequest } = usePusherContext();
  const [progressData, setProgressData] = useState<any[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    const unsubscribe = subscribeToContentGeneration((data) => {
      setProgressData(prev => [...prev, {
        ...data,
        timestamp: new Date().toISOString()
      }]);

      if (data.stage === 'finalizing' && data.percentage === 100) {
        setIsGenerating(false);
      }
    });

    return unsubscribe;
  }, [subscribeToContentGeneration]);

  const startContentGeneration = async () => {
    setIsGenerating(true);
    setProgressData([]);

    try {
      await triggerContentRequest({
        requestId: `req_${Date.now()}`,
        type: 'lesson',
        subject: 'Mathematics',
        gradeLevel: 8,
        topic: 'Algebra Basics'
      });
    } catch (error) {
      console.error('Failed to start content generation:', error);
      setIsGenerating(false);
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography order={6} gutterBottom>
          Content Generation Monitoring
        </Typography>

        <Stack spacing={2}>
          <Button
            variant="filled"
            onClick={startContentGeneration}
            disabled={isGenerating}
          >
            {isGenerating ? 'Generating...' : 'Start Content Generation'}
          </Button>

          <Typography variant="subtitle2">
            Progress Updates:
          </Typography>

          <List dense style={{ maxHeight: 200, overflow: 'auto' }}>
            {progressData.map((progress, index) => (
              <ListItem key={index}>
                <ListItemText
                  primary={`${progress.stage || 'Unknown'}: ${progress.percentage || 0}%`}
                  secondary={`${progress.message || ''} - ${new Date(progress.timestamp).toLocaleTimeString()}`}
                />
              </ListItem>
            ))}
            {progressData.length === 0 && (
              <ListItem>
                <ListItemText primary="No progress updates yet" />
              </ListItem>
            )}
          </List>
        </Stack>
      </CardContent>
    </Card>
  );
};

/**
 * Example 5: Presence Channel (Simplified)
 */
export const PresenceChannelExample: React.FC = () => {
  const { members, isJoined, joinChannel, leaveChannel } = usePusherPresence(
    'classroom-demo',
    {
      name: 'Demo User',
      avatar: 'https://via.placeholder.com/40',
      role: 'student',
      status: 'online'
    },
    {
      enabled: true,
      onMemberAdded: (member) => {
        console.log('Member joined:', member);
      },
      onMemberRemoved: (member) => {
        console.log('Member left:', member);
      }
    }
  );

  return (
    <Card>
      <CardContent>
        <Typography order={6} gutterBottom>
          Presence Channel Example
        </Typography>

        <Stack spacing={2}>
          <Box display="flex" gap={1}>
            <Button
              variant="filled"
              onClick={joinChannel}
              disabled={isJoined}
              size="small"
            >
              Join Channel
            </Button>
            <Button
              variant="outline"
              onClick={leaveChannel}
              disabled={!isJoined}
              size="small"
            >
              Leave Channel
            </Button>
          </Box>

          <Chip
            label={isJoined ? 'In Channel' : 'Not in Channel'}
            color={isJoined ? 'success' : 'default'}
            size="small"
          />

          <Typography variant="subtitle2">
            Online Members ({members.length}):
          </Typography>

          <List dense>
            {members.map((member) => (
              <ListItem key={member.id}>
                <ListItemText
                  primary={member.info.name}
                  secondary={`${member.info.role} - ${member.info.status}`}
                />
              </ListItem>
            ))}
            {members.length === 0 && (
              <ListItem>
                <ListItemText primary="No members online" />
              </ListItem>
            )}
          </List>
        </Stack>
      </CardContent>
    </Card>
  );
};

/**
 * Example 6: Event Listening
 */
export const EventListeningExample: React.FC = () => {
  const [events, setEvents] = useState<any[]>([]);

  // Listen to specific events
  usePusherEvent(
    EVENT_NAMES.USER.ACHIEVEMENT,
    (data) => {
      setEvents(prev => [...prev, {
        type: 'achievement',
        data,
        timestamp: new Date().toISOString()
      }]);
    },
    { enabled: true }
  );

  usePusherEvent(
    EVENT_NAMES.SYSTEM.ALERT,
    (data) => {
      setEvents(prev => [...prev, {
        type: 'system-alert',
        data,
        timestamp: new Date().toISOString()
      }]);
    },
    { enabled: true }
  );

  return (
    <Card>
      <CardContent>
        <Typography order={6} gutterBottom>
          Event Listening Example
        </Typography>

        <Typography size="sm" color="text.secondary" gutterBottom>
          Listening for: User Achievements, System Alerts
        </Typography>

        <Typography variant="subtitle2">
          Recent Events ({events.length}):
        </Typography>

        <List dense style={{ maxHeight: 200, overflow: 'auto' }}>
          {events.slice(-10).map((event, index) => (
            <ListItem key={index}>
              <ListItemText
                primary={`${event.type}: ${JSON.stringify(event.data).substring(0, 80)}...`}
                secondary={new Date(event.timestamp).toLocaleTimeString()}
              />
            </ListItem>
          ))}
          {events.length === 0 && (
            <ListItem>
              <ListItemText primary="No events received yet" />
            </ListItem>
          )}
        </List>
      </CardContent>
    </Card>
  );
};

/**
 * Main Examples Component
 */
export const PusherUsageExamples: React.FC = () => {
  return (
    <Box style={{ p: 3 }}>
      <Typography order={4} gutterBottom>
        Pusher Usage Examples
      </Typography>

      <Typography size="md" color="text.secondary" paragraph>
        This page demonstrates various ways to use the Pusher service in the ToolboxAI Dashboard.
      </Typography>

      <Stack spacing={3}>
        <BasicConnectionExample />
        <ChannelSubscriptionExample />
        <MessageSendingExample />
        <ContentGenerationExample />
        <PresenceChannelExample />
        <EventListeningExample />
      </Stack>
    </Box>
  );
};

export default PusherUsageExamples;