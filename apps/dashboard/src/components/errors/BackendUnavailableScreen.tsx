/**
 * Backend Unavailable Screen
 * Shown when the backend API is unreachable or unhealthy
 */

import React from 'react';
import { Container, Title, Text, Button, Stack, Paper, Alert, List } from '@mantine/core';
import { IconAlertCircle, IconRefresh, IconServerOff } from '@tabler/icons-react';

interface BackendUnavailableScreenProps {
  /** Callback when user clicks retry button */
  onRetry: () => void;
  /** Optional error message to display */
  errorMessage?: string;
  /** Optional response time from health check */
  responseTime?: number;
}

export const BackendUnavailableScreen: React.FC<BackendUnavailableScreenProps> = ({
  onRetry,
  errorMessage,
  responseTime
}) => {
  return (
    <Container size="sm" style={{ marginTop: '10vh' }}>
      <Paper shadow="md" p="xl" radius="md" withBorder>
        <Stack gap="lg" align="center">
          {/* Icon */}
          <IconServerOff size={64} color="var(--mantine-color-red-6)" />

          {/* Title */}
          <Title order={2} ta="center">
            Backend Temporarily Unavailable
          </Title>

          {/* Error Message */}
          {errorMessage && (
            <Alert
              icon={<IconAlertCircle size={16} />}
              title="Error Details"
              color="red"
              style={{ width: '100%' }}
            >
              {errorMessage}
              {responseTime && (
                <Text size="sm" c="dimmed" mt="xs">
                  Response time: {responseTime}ms
                </Text>
              )}
            </Alert>
          )}

          {/* Information */}
          <Text c="dimmed" ta="center" size="sm">
            The ToolBoxAI backend service is currently unreachable. This may be because:
          </Text>

          <List spacing="xs" size="sm" style={{ width: '100%', maxWidth: '500px' }}>
            <List.Item>
              <Text size="sm">
                <strong>Service is starting up</strong> - Free tier services on Render.com go to sleep after 15 minutes of inactivity.
                The first request can take 30-60 seconds to wake up the service.
              </Text>
            </List.Item>
            <List.Item>
              <Text size="sm">
                <strong>Network connectivity issues</strong> - There may be a temporary network problem between your device and the server.
              </Text>
            </List.Item>
            <List.Item>
              <Text size="sm">
                <strong>Scheduled maintenance</strong> - The service may be undergoing updates or maintenance.
              </Text>
            </List.Item>
            <List.Item>
              <Text size="sm">
                <strong>Server overload</strong> - The backend may be experiencing high traffic.
              </Text>
            </List.Item>
          </List>

          {/* Action Buttons */}
          <Stack gap="sm" style={{ width: '100%', maxWidth: '300px' }}>
            <Button
              leftSection={<IconRefresh size={16} />}
              onClick={onRetry}
              size="md"
              fullWidth
            >
              Retry Connection
            </Button>

            <Text size="xs" c="dimmed" ta="center">
              If the problem persists, please wait a few moments and try again.
              The service may be starting up for the first time today.
            </Text>
          </Stack>

          {/* Additional Help */}
          <Alert
            icon={<IconAlertCircle size={16} />}
            title="Running in Limited Mode"
            color="blue"
            style={{ width: '100%' }}
          >
            <Text size="sm">
              You can enable <strong>bypass mode</strong> in the configuration to test the frontend
              independently from the backend. This is useful for development and testing purposes.
            </Text>
            <Text size="xs" c="dimmed" mt="xs">
              Set <code>VITE_BYPASS_AUTH=true</code> in your environment variables.
            </Text>
          </Alert>
        </Stack>
      </Paper>
    </Container>
  );
};

export default BackendUnavailableScreen;
