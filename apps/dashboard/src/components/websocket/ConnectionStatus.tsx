/**
 * Pusher Connection Status Component (Mantine v8)
 * Displays real-time connection status and statistics
 * Updated to use Mantine v8 components instead of MUI
 */

import React, { useState } from 'react';
import {
  Box,
  ActionIcon,
  Tooltip,
  Text,
  Paper,
  Collapse,
  Badge,
  Progress,
  Button,
  Alert,
  Stack,
  Divider,
  Group,
  Card,
  Code
} from '@mantine/core';
import {
  IconWifi,
  IconWifiOff,
  IconRefresh,
  IconChevronDown,
  IconChevronUp,
  IconAlertCircle,
  IconCheck,
  IconX,
  IconClock,
  IconSend,
  IconDownload
} from '@tabler/icons-react';
import { usePusher } from '../../hooks/usePusher';
import { useAppSelector } from '../../store';
import { selectWebSocketStats, selectWebSocketError } from '../../store/slices/realtimeSlice';
import { WebSocketState } from '../../types/websocket';
import { API_BASE_URL, DEBUG_MODE } from '../../config';

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
  showLabel?: boolean;
  size?: 'small' | 'medium' | 'large';
}

export default function ConnectionStatus({
  variant = 'compact',
  showStats = false,
  position = 'relative',
  floatingPosition = { bottom: 20, right: 20 },
  showLabel = false,
  size = 'medium'
}: ConnectionStatusProps) {
  const status = usePusher();
  const stats = useAppSelector(selectWebSocketStats);
  const error = useAppSelector(selectWebSocketError);
  const [expanded, setExpanded] = useState(false);
  const [serverDiag, setServerDiag] = useState<any | null>(null);

  // Get status color based on connection state
  const getStatusColor = () => {
    switch (status.state) {
      case WebSocketState.CONNECTED:
        return 'green';
      case WebSocketState.CONNECTING:
      case WebSocketState.RECONNECTING:
        return 'yellow';
      case WebSocketState.ERROR:
      case WebSocketState.FAILED:
        return 'red';
      default:
        return 'gray';
    }
  };

  // Get status icon
  const getStatusIcon = () => {
    const iconSize = size === 'small' ? 16 : size === 'large' ? 24 : 20;

    switch (status.state) {
      case WebSocketState.CONNECTED:
        return <IconCheck size={iconSize} color="green" />;
      case WebSocketState.DISCONNECTED:
        return <IconWifiOff size={iconSize} color="gray" />;
      case WebSocketState.ERROR:
      case WebSocketState.FAILED:
        return <IconX size={iconSize} color="red" />;
      default:
        return <IconWifi size={iconSize} color="gray" />;
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
        return 'Reconnecting...';
      case WebSocketState.DISCONNECTED:
        return 'Disconnected';
      case WebSocketState.ERROR:
      case WebSocketState.FAILED:
        return 'Connection Failed';
      default:
        return 'Unknown';
    }
  };

  // Fetch server diagnostics
  const fetchServerDiagnostics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health/websocket`);
      const data = await response.json();
      setServerDiag(data);
    } catch (err) {
      console.error('Failed to fetch server diagnostics:', err);
      setServerDiag({ error: 'Failed to fetch diagnostics' });
    }
  };

  // Compact variant
  if (variant === 'compact') {
    const containerStyle = position === 'fixed' ? {
      position: 'fixed' as const,
      ...floatingPosition,
      zIndex: 1000,
    } : {};

    return (
      <Box style={containerStyle}>
        <Tooltip label={`Pusher Status: ${getStatusText()}`}>
          <ActionIcon
            variant="subtle"
            size={size === 'small' ? 'sm' : size === 'large' ? 'lg' : 'md'}
            color={getStatusColor()}
            onClick={() => setExpanded(!expanded)}
          >
            {getStatusIcon()}
          </ActionIcon>
        </Tooltip>

        {showLabel && (
          <Text size="xs" c="dimmed" ta="center" mt={4}>
            {getStatusText()}
          </Text>
        )}

        <Collapse in={expanded}>
          <Paper p="md" mt="xs" shadow="md" style={{ minWidth: 300, maxWidth: 400 }}>
            <Stack gap="sm">
              {/* Header */}
              <Group justify="space-between" align="center">
                <Text fw={600}>Pusher Status</Text>
                <ActionIcon
                  size="sm"
                  variant="subtle"
                  onClick={() => setExpanded(false)}
                >
                  <IconChevronUp size={16} />
                </ActionIcon>
              </Group>

              <Divider />

              {/* Status Info */}
              <Group justify="space-between">
                <Text size="sm">Status:</Text>
                <Badge color={getStatusColor()} variant="filled">
                  {getStatusText()}
                </Badge>
              </Group>

              {error && (
                <Alert color="red" icon={<IconAlertCircle size={16} />}>
                  <Text size="sm">{error.message}</Text>
                </Alert>
              )}

              {showStats && stats && (
                <>
                  <Divider />
                  <Stack gap="xs">
                    <Text size="sm" fw={500}>Statistics</Text>
                    <Group justify="space-between">
                      <Text size="xs">Messages Sent:</Text>
                      <Text size="xs" fw={500}>{stats.messagesSent || 0}</Text>
                    </Group>
                    <Group justify="space-between">
                      <Text size="xs">Messages Received:</Text>
                      <Text size="xs" fw={500}>{stats.messagesReceived || 0}</Text>
                    </Group>
                    <Group justify="space-between">
                      <Text size="xs">Reconnect Attempts:</Text>
                      <Text size="xs" fw={500}>{stats.reconnectAttempts || 0}</Text>
                    </Group>
                    {stats.latency && (
                      <Group justify="space-between">
                        <Text size="xs">Latency:</Text>
                        <Text size="xs" fw={500}>{stats.latency}ms</Text>
                      </Group>
                    )}
                  </Stack>
                </>
              )}

              <Divider />

              <Group>
                <Button
                  size="xs"
                  variant="outline"
                  leftSection={<IconRefresh size={14} />}
                  onClick={() => status.connect?.()}
                  disabled={status.isConnected}
                >
                  Reconnect
                </Button>

                {DEBUG_MODE && (
                  <Button
                    size="xs"
                    variant="outline"
                    leftSection={<IconClock size={14} />}
                    onClick={fetchServerDiagnostics}
                  >
                    Diagnostics
                  </Button>
                )}
              </Group>

              {serverDiag && (
                <>
                  <Divider />
                  <Stack gap="xs">
                    <Text size="sm" fw={500}>Server Diagnostics</Text>
                    <Code block style={{ fontSize: '0.75rem' }}>
                      {JSON.stringify(serverDiag, null, 2)}
                    </Code>
                  </Stack>
                </>
              )}
            </Stack>
          </Paper>
        </Collapse>
      </Box>
    );
  }

  // Detailed variant
  return (
    <Card withBorder p="lg">
      <Stack gap="md">
        <Group justify="space-between">
          <Title order={3}>Pusher Connection Status</Title>
          <Badge color={getStatusColor()} variant="filled" leftSection={getStatusIcon()}>
            {getStatusText()}
          </Badge>
        </Group>

        {status.state === WebSocketState.CONNECTING && (
          <Progress value={undefined} animated />
        )}

        {error && (
          <Alert color="red" icon={<IconAlertCircle size={16} />} title="Connection Error">
            <Text size="sm">{error.message}</Text>
            {error.recoverable && (
              <Button
                size="xs"
                variant="outline"
                mt="sm"
                leftSection={<IconRefresh size={14} />}
                onClick={() => status.connect?.()}
              >
                Retry Connection
              </Button>
            )}
          </Alert>
        )}

        {showStats && stats && (
          <Card withBorder>
            <Stack gap="sm">
              <Text fw={500}>Connection Statistics</Text>

              <Group grow>
                <Paper p="sm" withBorder>
                  <Stack gap={4} align="center">
                    <IconSend size={20} color="blue" />
                    <Text size="lg" fw={700}>{stats.messagesSent || 0}</Text>
                    <Text size="xs" c="dimmed">Sent</Text>
                  </Stack>
                </Paper>

                <Paper p="sm" withBorder>
                  <Stack gap={4} align="center">
                    <IconDownload size={20} color="green" />
                    <Text size="lg" fw={700}>{stats.messagesReceived || 0}</Text>
                    <Text size="xs" c="dimmed">Received</Text>
                  </Stack>
                </Paper>

                <Paper p="sm" withBorder>
                  <Stack gap={4} align="center">
                    <IconRefresh size={20} color="orange" />
                    <Text size="lg" fw={700}>{stats.reconnectAttempts || 0}</Text>
                    <Text size="xs" c="dimmed">Reconnects</Text>
                  </Stack>
                </Paper>
              </Group>

              {stats.connectedAt && (
                <Group justify="space-between">
                  <Text size="sm">Connected Since:</Text>
                  <Text size="sm" fw={500}>
                    {new Date(stats.connectedAt).toLocaleString()}
                  </Text>
                </Group>
              )}

              {stats.latency && (
                <Group justify="space-between">
                  <Text size="sm">Latency:</Text>
                  <Text size="sm" fw={500}>{stats.latency}ms</Text>
                </Group>
              )}
            </Stack>
          </Card>
        )}

        <Group>
          <Button
            variant="outline"
            leftSection={<IconRefresh size={16} />}
            onClick={() => status.connect?.()}
            disabled={status.isConnected}
          >
            Reconnect
          </Button>

          {DEBUG_MODE && (
            <Button
              variant="outline"
              leftSection={<IconClock size={16} />}
              onClick={fetchServerDiagnostics}
            >
              Server Diagnostics
            </Button>
          )}
        </Group>
      </Stack>
    </Card>
  );
}

// Mini status indicator for app bar
export const ConnectionStatusIndicator: React.FunctionComponent<Record<string, any>> = () => {
  const status = usePusher();

  const getColor = () => {
    switch (status.state) {
      case WebSocketState.CONNECTED:
        return '#4caf50';
      case WebSocketState.CONNECTING:
      case WebSocketState.RECONNECTING:
        return '#ff9800';
      case WebSocketState.ERROR:
      case WebSocketState.FAILED:
        return '#f44336';
      default:
        return '#9e9e9e';
    }
  };

  return (
    <Tooltip label={`Pusher: ${status.state}`}>
      <Box
        style={{
          width: 12,
          height: 12,
          borderRadius: '50%',
          backgroundColor: getColor(),
          border: '2px solid white',
          boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
          animation: status.state === WebSocketState.CONNECTING ? 'pulse 2s infinite' : 'none',
        }}
      />
    </Tooltip>
  );
};
