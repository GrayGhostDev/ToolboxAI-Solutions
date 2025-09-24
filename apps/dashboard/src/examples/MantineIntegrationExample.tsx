import React from 'react';
import { MantineProvider } from '../providers/MantineProvider';
import { UIMigrationDemo } from '../components/migration/UIMigrationDemo';
import { MantineMigrationGuide } from '../components/migration/MantineMigrationGuide';
import { LoginMantine } from '../components/pages/LoginMantine';
import {
  Container,
  Tabs,
  Title,
  Text,
  Alert,
  Code,
  Stack,
  Button,
  Group
} from '@mantine/core';
import { IconInfoCircle, IconCode, IconEye, IconBook } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';

/**
 * Example component showing how to integrate Mantine UI
 * This demonstrates the complete setup and provides examples
 */
export function MantineIntegrationExample() {
  const showNotification = () => {
    notifications.show({
      title: 'Mantine Notification',
      message: 'This is how notifications work in Mantine!',
      color: 'blue',
      autoClose: 3000,
    });
  };

  return (
    <MantineProvider>
      <Container size="xl" py="xl">
        <Stack gap="xl">
          <div style={{ textAlign: 'center' }}>
            <Title order={1} mb="md">Mantine UI Integration Example</Title>
            <Text size="lg" c="dimmed">
              Complete setup and migration examples for ToolBoxAI Dashboard
            </Text>
          </div>

          <Alert icon={<IconInfoCircle />} color="blue">
            <Text fw={500}>Setup Complete</Text>
            <Text size="sm" mt="xs">
              Mantine UI has been successfully installed and configured. This example shows
              the integration pattern and provides migration guidance.
            </Text>
          </Alert>

          <Group justify="center">
            <Button onClick={showNotification} variant="outline">
              Test Notification System
            </Button>
          </Group>

          <Tabs defaultValue="setup" variant="outline">
            <Tabs.List grow>
              <Tabs.Tab value="setup" leftSection={<IconCode size={16} />}>
                Setup Instructions
              </Tabs.Tab>
              <Tabs.Tab value="demo" leftSection={<IconEye size={16} />}>
                Side-by-Side Demo
              </Tabs.Tab>
              <Tabs.Tab value="login" leftSection={<IconCode size={16} />}>
                Login Example
              </Tabs.Tab>
              <Tabs.Tab value="guide" leftSection={<IconBook size={16} />}>
                Migration Guide
              </Tabs.Tab>
            </Tabs.List>

            <Tabs.Panel value="setup" pt="md">
              <Stack gap="md">
                <Title order={3}>Integration Steps Completed</Title>

                <div>
                  <Title order={4} mb="xs">1. Dependencies Installed</Title>
                  <Code block>
{`npm install @mantine/core @mantine/hooks @mantine/form @mantine/notifications @tabler/icons-react`}
                  </Code>
                </div>

                <div>
                  <Title order={4} mb="xs">2. MantineProvider Created</Title>
                  <Text size="sm" c="dimmed">
                    Location: <Code>src/providers/MantineProvider.tsx</Code>
                  </Text>
                  <Code block>
{`import { MantineProvider } from './providers/MantineProvider';

function App() {
  return (
    <MantineProvider>
      {/* Your app content */}
    </MantineProvider>
  );
}`}
                  </Code>
                </div>

                <div>
                  <Title order={4} mb="xs">3. Vite Configuration Updated</Title>
                  <Text size="sm" c="dimmed">
                    Added Mantine to optimizeDeps and build configuration
                  </Text>
                  <Code block>
{`// Added to vite.config.ts optimizeDeps.include:
'@mantine/core',
'@mantine/hooks',
'@mantine/form',
'@mantine/notifications',
'@tabler/icons-react'`}
                  </Code>
                </div>

                <div>
                  <Title order={4} mb="xs">4. Theme Configuration</Title>
                  <Text size="sm" c="dimmed">
                    Custom theme with ToolBoxAI colors and styling
                  </Text>
                  <Code block>
{`const theme = createTheme({
  primaryColor: 'toolboxai-blue',
  colors: {
    'toolboxai-blue': [...],
    'toolboxai-purple': [...]
  },
  // Custom component defaults and styling
});`}
                  </Code>
                </div>

                <Alert color="green">
                  <Text fw={500}>Ready to Use!</Text>
                  <Text size="sm" mt="xs">
                    Mantine is now ready for use alongside Material-UI. You can start migrating
                    components gradually or use both frameworks in parallel.
                  </Text>
                </Alert>
              </Stack>
            </Tabs.Panel>

            <Tabs.Panel value="demo" pt="md">
              <UIMigrationDemo />
            </Tabs.Panel>

            <Tabs.Panel value="login" pt="md">
              <Stack gap="md">
                <Title order={3}>Login Component Migration Example</Title>
                <Text>
                  Here's how the Login component looks when migrated to Mantine.
                  Compare this with the original Material-UI version.
                </Text>
                <div style={{ maxHeight: '600px', overflow: 'auto' }}>
                  <LoginMantine />
                </div>
              </Stack>
            </Tabs.Panel>

            <Tabs.Panel value="guide" pt="md">
              <MantineMigrationGuide />
            </Tabs.Panel>
          </Tabs>

          <Alert color="orange">
            <Text fw={500}>Next Steps</Text>
            <Text size="sm" mt="xs">
              1. Start migrating new components to Mantine<br />
              2. Gradually convert existing components<br />
              3. Update tests for new component APIs<br />
              4. Consider removing Material-UI once migration is complete
            </Text>
          </Alert>
        </Stack>
      </Container>
    </MantineProvider>
  );
}