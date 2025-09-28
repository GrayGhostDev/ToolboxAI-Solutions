/**
 * WebSocket Test Component (Mantine v8)
 *
 * Comprehensive testing interface for Pusher functionality
 * Updated to use Mantine v8 components instead of MUI
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Text,
  Title,
  Button,
  TextInput,
  Stack,
  Group,
  Badge,
  Alert,
  Progress,
  Divider,
  Select,
  ActionIcon,
  Tooltip,
  Card,
  ScrollArea,
  Code,
  Tabs
} from '@mantine/core';
import {
  IconSend,
  IconRefresh,
  IconTrash,
  IconSettings,
  IconWifi,
  IconWifiOff,
  IconAlertCircle,
  IconCheck,
  IconX
} from '@tabler/icons-react';
import { usePusherContext } from '../../contexts/PusherContext';
import {
  WebSocketState,
  WebSocketMessageType,
  WebSocketChannel,
  ContentGenerationRequest
} from '../../types/websocket';

interface Message {
  id: string;
  type: string;
  data: any;
  timestamp: number;
  channel?: string;
}

interface TestConfig {
  autoReconnect: boolean;
  debugMode: boolean;
  heartbeatInterval: number;
  maxReconnectAttempts: number;
}

export const WebSocketTest: React.FunctionComponent<Record<string, any>> = () => {
  const {
    isConnected,
    connectionState,
    send,
    subscribeToChannel,
    unsubscribeFromChannel,
    refreshAuth
  } = usePusherContext();

  // Component state
  const [messages, setMessages] = useState<Message[]>([]);
  const [messageInput, setMessageInput] = useState('');
  const [channelInput, setChannelInput] = useState('public');
  const [messageType, setMessageType] = useState<WebSocketMessageType>(WebSocketMessageType.INFO);
  const [subscriptions, setSubscriptions] = useState<Set<string>>(new Set());
  const [config, setConfig] = useState<TestConfig>({
    autoReconnect: true,
    debugMode: true,
    heartbeatInterval: 30000,
    maxReconnectAttempts: 5
  });
  const [stats, setStats] = useState({
    messagesSent: 0,
    messagesReceived: 0,
    connectionAttempts: 0,
    uptime: 0
  });

  // Message handler
  const handleMessage = useCallback((message: any) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      type: message.type || 'unknown',
      data: message.data || message,
      timestamp: Date.now(),
      channel: message.channel
    };
    setMessages(prev => [newMessage, ...prev].slice(0, 100)); // Keep last 100 messages
    setStats(prev => ({ ...prev, messagesReceived: prev.messagesReceived + 1 }));
  }, []);

  // Subscribe to test channels
  useEffect(() => {
    const testChannels = ['public', 'content-generation', 'agent-status'];
    const newSubscriptions = new Set<string>();

    testChannels.forEach(channel => {
      const subId = subscribeToChannel(channel, handleMessage);
      newSubscriptions.add(subId);
    });

    setSubscriptions(newSubscriptions);

    return () => {
      newSubscriptions.forEach(subId => {
        unsubscribeFromChannel(subId);
      });
    };
  }, [subscribeToChannel, unsubscribeFromChannel, handleMessage]);

  // Send test message
  const sendTestMessage = useCallback(async () => {
    if (!messageInput.trim()) return;

    try {
      await send(messageType, {
        message: messageInput,
        timestamp: new Date().toISOString(),
        testId: Date.now()
      }, { channel: channelInput });

      setStats(prev => ({ ...prev, messagesSent: prev.messagesSent + 1 }));
      setMessageInput('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  }, [messageInput, messageType, channelInput, send]);

  // Send content generation test
  const sendContentGenerationTest = useCallback(async () => {
    const request: ContentGenerationRequest = {
      type: 'lesson',
      subject: 'Mathematics',
      grade: 8,
      topic: 'Algebra Basics',
      difficulty: 'medium',
      length: 30,
      customInstructions: 'Focus on practical examples'
    };

    try {
      await send(WebSocketMessageType.CONTENT_UPDATE, request, {
        channel: 'content-generation'
      });
      setStats(prev => ({ ...prev, messagesSent: prev.messagesSent + 1 }));
    } catch (error) {
      console.error('Failed to send content generation request:', error);
    }
  }, [send]);

  // Clear messages
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // Get connection status info
  const getStatusColor = () => {
    switch (connectionState) {
      case 'connected':
        return 'green';
      case 'connecting':
      case 'reconnecting':
        return 'yellow';
      case 'failed':
        return 'red';
      default:
        return 'gray';
    }
  };

  const getStatusIcon = () => {
    switch (connectionState) {
      case 'connected':
        return <IconCheck color="green" />;
      case 'disconnected':
        return <IconWifiOff color="gray" />;
      case 'failed':
        return <IconX color="red" />;
      default:
        return <IconWifi color="gray" />;
    }
  };

  return (
    <Box p="xl">
      <Stack gap="lg">
        {/* Header */}
        <Group justify="space-between" align="center">
          <Title order={2}>Pusher Connection Test</Title>
          <Group gap="sm">
            <Badge color={getStatusColor()} variant="filled" leftSection={getStatusIcon()}>
              {connectionState?.toUpperCase() || 'UNKNOWN'}
            </Badge>
            <Button
              variant="outline"
              size="sm"
              leftSection={<IconRefresh size={16} />}
              onClick={() => refreshAuth()}
            >
              Reconnect
            </Button>
          </Group>
        </Group>

        {/* Connection Status Alert */}
        {!isConnected && (
          <Alert
            color="orange"
            title="Connection Status"
            icon={<IconAlertCircle size={16} />}
          >
            Pusher is not connected. Some features may not work properly.
          </Alert>
        )}

        <Tabs defaultValue="messaging">
          <Tabs.List>
            <Tabs.Tab value="messaging">Message Testing</Tabs.Tab>
            <Tabs.Tab value="content">Content Generation</Tabs.Tab>
            <Tabs.Tab value="stats">Statistics</Tabs.Tab>
            <Tabs.Tab value="config">Configuration</Tabs.Tab>
          </Tabs.List>

          {/* Message Testing Tab */}
          <Tabs.Panel value="messaging">
            <Stack gap="md" mt="md">
              <Card withBorder>
                <Stack gap="md">
                  <Title order={4}>Send Test Message</Title>

                  <Group grow>
                    <Select
                      label="Message Type"
                      value={messageType}
                      onChange={(value) => value && setMessageType(value as WebSocketMessageType)}
                      data={[
                        { value: WebSocketMessageType.INFO, label: 'Info' },
                        { value: WebSocketMessageType.WARNING, label: 'Warning' },
                        { value: WebSocketMessageType.ERROR, label: 'Error' },
                        { value: WebSocketMessageType.USER_UPDATE, label: 'User Update' },
                        { value: WebSocketMessageType.SYSTEM_NOTIFICATION, label: 'System Notification' }
                      ]}
                    />

                    <TextInput
                      label="Channel"
                      value={channelInput}
                      onChange={(e) => setChannelInput(e.target.value)}
                      placeholder="public"
                    />
                  </Group>

                  <TextInput
                    label="Message Content"
                    value={messageInput}
                    onChange={(e) => setMessageInput(e.target.value)}
                    placeholder="Enter test message..."
                    onKeyDown={(e) => e.key === 'Enter' && sendTestMessage()}
                  />

                  <Group>
                    <Button
                      leftSection={<IconSend size={16} />}
                      onClick={sendTestMessage}
                      disabled={!isConnected || !messageInput.trim()}
                    >
                      Send Message
                    </Button>

                    <Button
                      variant="outline"
                      leftSection={<IconTrash size={16} />}
                      onClick={clearMessages}
                      color="red"
                    >
                      Clear Messages
                    </Button>
                  </Group>
                </Stack>
              </Card>

              {/* Messages List */}
              <Card withBorder>
                <Stack gap="sm">
                  <Group justify="space-between">
                    <Title order={4}>Recent Messages</Title>
                    <Badge variant="outline">{messages.length} messages</Badge>
                  </Group>

                  <ScrollArea h={300}>
                    <Stack gap="xs">
                      {messages.length === 0 ? (
                        <Text c="dimmed" ta="center" py="xl">
                          No messages received yet
                        </Text>
                      ) : (
                        messages.map((msg) => (
                          <Paper key={msg.id} p="sm" withBorder>
                            <Group justify="space-between" align="flex-start">
                              <Stack gap={4}>
                                <Group gap="xs">
                                  <Badge size="sm" variant="outline">
                                    {msg.type}
                                  </Badge>
                                  {msg.channel && (
                                    <Badge size="sm" color="blue">
                                      {msg.channel}
                                    </Badge>
                                  )}
                                </Group>
                                <Code block>{JSON.stringify(msg.data, null, 2)}</Code>
                              </Stack>
                              <Text size="xs" c="dimmed">
                                {new Date(msg.timestamp).toLocaleTimeString()}
                              </Text>
                            </Group>
                          </Paper>
                        ))
                      )}
                    </Stack>
                  </ScrollArea>
                </Stack>
              </Card>
            </Stack>
          </Tabs.Panel>

          {/* Content Generation Tab */}
          <Tabs.Panel value="content">
            <Stack gap="md" mt="md">
              <Card withBorder>
                <Stack gap="md">
                  <Title order={4}>Content Generation Test</Title>
                  <Text size="sm" c="dimmed">
                    Test the content generation pipeline through Pusher
                  </Text>

                  <Button
                    leftSection={<IconSend size={16} />}
                    onClick={sendContentGenerationTest}
                    disabled={!isConnected}
                  >
                    Generate Test Content
                  </Button>
                </Stack>
              </Card>
            </Stack>
          </Tabs.Panel>

          {/* Statistics Tab */}
          <Tabs.Panel value="stats">
            <Stack gap="md" mt="md">
              <Card withBorder>
                <Stack gap="md">
                  <Title order={4}>Connection Statistics</Title>

                  <Group grow>
                    <Paper p="md" withBorder>
                      <Stack gap="xs">
                        <Text size="sm" c="dimmed">Messages Sent</Text>
                        <Text size="xl" fw={700}>{stats.messagesSent}</Text>
                      </Stack>
                    </Paper>

                    <Paper p="md" withBorder>
                      <Stack gap="xs">
                        <Text size="sm" c="dimmed">Messages Received</Text>
                        <Text size="xl" fw={700}>{stats.messagesReceived}</Text>
                      </Stack>
                    </Paper>

                    <Paper p="md" withBorder>
                      <Stack gap="xs">
                        <Text size="sm" c="dimmed">Connection Attempts</Text>
                        <Text size="xl" fw={700}>{stats.connectionAttempts}</Text>
                      </Stack>
                    </Paper>
                  </Group>

                  <Divider />

                  <Stack gap="xs">
                    <Text fw={500}>Active Subscriptions</Text>
                    <Group gap="xs">
                      {Array.from(subscriptions).map((subId) => (
                        <Badge key={subId} variant="outline" size="sm">
                          {subId.slice(0, 8)}...
                        </Badge>
                      ))}
                    </Group>
                  </Stack>
                </Stack>
              </Card>
            </Stack>
          </Tabs.Panel>

          {/* Configuration Tab */}
          <Tabs.Panel value="config">
            <Stack gap="md" mt="md">
              <Card withBorder>
                <Stack gap="md">
                  <Title order={4}>Test Configuration</Title>

                  <Group grow>
                    <TextInput
                      label="Heartbeat Interval (ms)"
                      type="number"
                      value={config.heartbeatInterval}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        heartbeatInterval: parseInt(e.target.value) || 30000
                      }))}
                    />

                    <TextInput
                      label="Max Reconnect Attempts"
                      type="number"
                      value={config.maxReconnectAttempts}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        maxReconnectAttempts: parseInt(e.target.value) || 5
                      }))}
                    />
                  </Group>

                  <Alert color="blue" title="Configuration Note">
                    <Text size="sm">
                      These settings are for testing purposes only.
                      Production configuration is managed through environment variables.
                    </Text>
                  </Alert>
                </Stack>
              </Card>
            </Stack>
          </Tabs.Panel>
        </Tabs>
      </Stack>
    </Box>
  );
};
