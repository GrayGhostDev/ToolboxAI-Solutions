import {
  Box,
  Button,
  Text,
  Paper,
  Stack,
  Grid,
  Container,
  ActionIcon,
  Avatar,
  Card,
  List,
  Divider,
  TextInput,
  Select,
  Badge,
  Alert,
  Loader,
  Progress,
  Modal,
  Drawer,
  Tabs,
  Menu,
  Tooltip,
  Checkbox,
  Radio,
  Switch,
  Slider,
  Rating,
  Autocomplete,
  Skeleton
} from '@mantine/core';
/**
 * Pusher Usage Examples for ToolboxAI Dashboard
 *
 * This file demonstrates how to use the comprehensive Pusher service
 * with various Mantine components and React hooks.
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
    <Card withBorder shadow="sm" radius="md" p="lg">
      <Text fw={600} size="lg" mb="md">
        Basic Connection Monitoring
      </Text>

      <Stack gap="md">
        <PusherConnectionStatus size="medium" />

        <Box>
          <Text size="sm" c="dimmed">
            Status: {ConnectionStateUtils.getStatusMessage(state)}
          </Text>
          <Text size="sm" c="dimmed">
            Messages Sent: {stats.messagesSent}
          </Text>
          <Text size="sm" c="dimmed">
            Messages Received: {stats.messagesReceived}
          </Text>
        </Box>
      </Stack>
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
    <Card withBorder shadow="sm" radius="md" p="lg">
      <Text fw={600} size="lg" mb="md">
        Channel Subscription Example
      </Text>

      <Stack gap="md">
        <TextInput
          label="Channel Name"
          value={channelName}
          onChange={(e) => setChannelName(e.currentTarget.value)}
          size="sm"
        />

        <Box style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <Badge
            color={isSubscribed ? 'green' : 'gray'}
            size="sm"
          >
            {isSubscribed ? 'Subscribed' : 'Not Subscribed'}
          </Badge>
          {subscriptionError && (
            <Badge
              color="red"
              size="sm"
              title={subscriptionError.message}
            >
              Error
            </Badge>
          )}
        </Box>

        {subscriptionError && (
          <Alert color="red" variant="light">
            Subscription Error: {subscriptionError.message}
          </Alert>
        )}

        <Text fw={500} size="sm">
          Recent Messages ({messages.length}):
        </Text>

        <Box style={{ maxHeight: 200, overflow: 'auto' }}>
          <List spacing="xs" size="sm">
            {messages.slice(-10).map((message, index) => (
              <List.Item key={index}>
                <Box>
                  <Text size="sm">
                    {message.type}: {JSON.stringify(message.data).substring(0, 100)}...
                  </Text>
                  <Text size="xs" c="dimmed">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </Text>
                </Box>
              </List.Item>
            ))}
            {messages.length === 0 && (
              <List.Item>
                <Text size="sm" c="dimmed">No messages received yet</Text>
              </List.Item>
            )}
          </List>
        </Box>
      </Stack>
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
    <Card withBorder shadow="sm" radius="md" p="lg">
      <Text fw={600} size="lg" mb="md">
        Message Sending Example
      </Text>

      <Stack gap="md">
        <TextInput
          label="Target Channel"
          value={targetChannel}
          onChange={(e) => setTargetChannel(e.currentTarget.value)}
          size="sm"
          placeholder="e.g., public-chat, private-user-123"
        />

        <TextInput
          label="Message"
          value={messageText}
          onChange={(e) => setMessageText(e.currentTarget.value)}
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
          <Alert color="red" variant="light">
            Error: {lastError.message}
          </Alert>
        )}

        <Divider />

        <Text fw={500} size="sm">
          Sent Messages:
        </Text>

        <Box style={{ maxHeight: 150, overflow: 'auto' }}>
          <List spacing="xs" size="sm">
            {sentMessages.slice(-5).map((message, index) => (
              <List.Item key={index}>
                <Text size="sm">{message}</Text>
              </List.Item>
            ))}
            {sentMessages.length === 0 && (
              <List.Item>
                <Text size="sm" c="dimmed">No messages sent yet</Text>
              </List.Item>
            )}
          </List>
        </Box>
      </Stack>
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
    <Card withBorder shadow="sm" radius="md" p="lg">
      <Text fw={600} size="lg" mb="md">
        Content Generation Monitoring
      </Text>

      <Stack gap="md">
        <Button
          variant="filled"
          onClick={startContentGeneration}
          disabled={isGenerating}
        >
          {isGenerating ? 'Generating...' : 'Start Content Generation'}
        </Button>

        <Text fw={500} size="sm">
          Progress Updates:
        </Text>

        <Box style={{ maxHeight: 200, overflow: 'auto' }}>
          <List spacing="xs" size="sm">
            {progressData.map((progress, index) => (
              <List.Item key={index}>
                <Box>
                  <Text size="sm">
                    {progress.stage || 'Unknown'}: {progress.percentage || 0}%
                  </Text>
                  <Text size="xs" c="dimmed">
                    {progress.message || ''} - {new Date(progress.timestamp).toLocaleTimeString()}
                  </Text>
                </Box>
              </List.Item>
            ))}
            {progressData.length === 0 && (
              <List.Item>
                <Text size="sm" c="dimmed">No progress updates yet</Text>
              </List.Item>
            )}
          </List>
        </Box>
      </Stack>
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
    <Card withBorder shadow="sm" radius="md" p="lg">
      <Text fw={600} size="lg" mb="md">
        Presence Channel Example
      </Text>

      <Stack gap="md">
        <Box style={{ display: 'flex', gap: 8 }}>
          <Button
            variant="filled"
            onClick={joinChannel}
            disabled={isJoined}
            size="sm"
          >
            Join Channel
          </Button>
          <Button
            variant="outline"
            onClick={leaveChannel}
            disabled={!isJoined}
            size="sm"
          >
            Leave Channel
          </Button>
        </Box>

        <Badge
          color={isJoined ? 'green' : 'gray'}
          size="sm"
        >
          {isJoined ? 'In Channel' : 'Not in Channel'}
        </Badge>

        <Text fw={500} size="sm">
          Online Members ({members.length}):
        </Text>

        <List spacing="xs" size="sm">
          {members.map((member) => (
            <List.Item key={member.id}>
              <Box>
                <Text size="sm">{member.info.name}</Text>
                <Text size="xs" c="dimmed">
                  {member.info.role} - {member.info.status}
                </Text>
              </Box>
            </List.Item>
          ))}
          {members.length === 0 && (
            <List.Item>
              <Text size="sm" c="dimmed">No members online</Text>
            </List.Item>
          )}
        </List>
      </Stack>
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
    <Card withBorder shadow="sm" radius="md" p="lg">
      <Text fw={600} size="lg" mb="md">
        Event Listening Example
      </Text>

      <Text size="sm" c="dimmed" mb="md">
        Listening for: User Achievements, System Alerts
      </Text>

      <Text fw={500} size="sm">
        Recent Events ({events.length}):
      </Text>

      <Box style={{ maxHeight: 200, overflow: 'auto' }}>
        <List spacing="xs" size="sm">
          {events.slice(-10).map((event, index) => (
            <List.Item key={index}>
              <Box>
                <Text size="sm">
                  {event.type}: {JSON.stringify(event.data).substring(0, 80)}...
                </Text>
                <Text size="xs" c="dimmed">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </Text>
              </Box>
            </List.Item>
          ))}
          {events.length === 0 && (
            <List.Item>
              <Text size="sm" c="dimmed">No events received yet</Text>
            </List.Item>
          )}
        </List>
      </Box>
    </Card>
  );
};

/**
 * Main Examples Component
 */
export const PusherUsageExamples: React.FC = () => {
  return (
    <Container size="lg" py="xl">
      <Text size="xl" fw={700} mb="md">
        Pusher Usage Examples
      </Text>

      <Text size="md" c="dimmed" mb="xl">
        This page demonstrates various ways to use the Pusher service with Mantine components in the ToolboxAI Dashboard.
      </Text>

      <Stack gap="xl">
        <BasicConnectionExample />
        <ChannelSubscriptionExample />
        <MessageSendingExample />
        <ContentGenerationExample />
        <PresenceChannelExample />
        <EventListeningExample />
      </Stack>
    </Container>
  );
};

export default PusherUsageExamples;