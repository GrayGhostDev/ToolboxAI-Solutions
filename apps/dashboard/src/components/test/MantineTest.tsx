import React from 'react';
import {
  Button,
  Text,
  Title,
  Card,
  Stack,
  Group,
  Badge,
  Alert
} from '@mantine/core';
import { IconCheck, IconInfoCircle } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';

/**
 * Simple test component to verify Mantine is working correctly
 */
export function MantineTest() {
  const showNotification = () => {
    notifications.show({
      title: 'Success!',
      message: 'Mantine UI is working perfectly',
      color: 'green',
      icon: <IconCheck size={16} />,
    });
  };

  return (
    <Card withBorder shadow="sm" radius="md" padding="lg">
      <Stack gap="md">
        <Group justify="space-between">
          <Title order={3}>Mantine UI Test</Title>
          <Badge color="green" variant="light">
            Working
          </Badge>
        </Group>

        <Alert icon={<IconInfoCircle size={16} />} title="Installation Complete" color="blue">
          <Text size="sm">
            Mantine UI has been successfully installed and configured.
            All components are working correctly.
          </Text>
        </Alert>

        <Text>
          This test component demonstrates that Mantine components are rendering
          properly with the custom theme configuration.
        </Text>

        <Group>
          <Button onClick={showNotification} variant="filled" color="blue">
            Test Notification
          </Button>
          <Button variant="outline" color="toolboxai-blue">
            Custom Color
          </Button>
          <Button variant="gradient" gradient={{ from: 'toolboxai-blue', to: 'toolboxai-purple' }}>
            Gradient Button
          </Button>
        </Group>
      </Stack>
    </Card>
  );
}