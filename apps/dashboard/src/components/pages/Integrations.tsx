import {
  Box, Button, Text, Paper, Stack, Grid, Container, ActionIcon, Avatar, Card,
  List, Divider, TextInput, Select, Chip, Badge, Alert, Loader, Progress,
  Modal, Menu, Tooltip, Checkbox, Switch, Slider, Autocomplete, Skeleton,
  Table, Group, Notification
} from '@mantine/core';
import {
  IconApi, IconPlus, IconSettings, IconEye, IconCode,
  IconDownload, IconSchool, IconCloud, IconFolder, IconDeviceGamepad,
  IconDotsVertical, IconEdit, IconTrash, IconCheck, IconAlertTriangle, IconX
} from '@tabler/icons-react';
import * as React from 'react';

import { useAppSelector } from '../../store';

interface Integration {
  id: string;
  name: string;
  type: 'lms' | 'gaming' | 'cloud' | 'analytics' | 'communication';
  icon: React.ReactNode;
  status: 'connected' | 'disconnected' | 'error' | 'syncing';
  description: string;
  lastSync?: string;
  features: string[];
  apiKey?: string;
  webhookUrl?: string;
  permissions: string[];
}

interface ApiEndpoint {
  id: string;
  name: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  endpoint: string;
  description: string;
  status: 'active' | 'inactive' | 'error';
  lastCall?: string;
  callCount: number;
}

export default function Integrations() {
  const [selectedIntegration, setSelectedIntegration] = React.useState<Integration | null>(null);
  const [configDialogOpen, setConfigDialogOpen] = React.useState(false);
  const [apiDialogOpen, setApiDialogOpen] = React.useState(false);

  const integrations: Integration[] = [
    {
      id: 'roblox',
      name: 'Roblox Studio',
      type: 'gaming',
      icon: <IconDeviceGamepad style={{ color: '#E74C3C' }} />,
      status: 'connected',
      description: 'Direct integration with Roblox for educational experiences',
      lastSync: '2024-01-29 10:30:00',
      features: ['Experience Publishing', 'Player Analytics', 'Asset Management', 'Badge System'],
      permissions: ['read', 'write', 'publish'],
    },
    {
      id: 'google-classroom',
      name: 'Google Classroom',
      type: 'lms',
      icon: <IconSchool style={{ color: '#4285F4' }} />,
      status: 'connected',
      description: 'Sync with Google Classroom for assignments and grades',
      lastSync: '2024-01-29 09:15:00',
      features: ['Assignment Sync', 'Grade Import', 'Class Roster', 'Calendar Integration'],
      permissions: ['read', 'write'],
    },
    {
      id: 'canvas',
      name: 'Canvas LMS',
      type: 'lms',
      icon: <IconSchool style={{ color: '#E74C3C' }} />,
      status: 'disconnected',
      description: 'Integration with Canvas Learning Management System',
      features: ['Course Management', 'Grade Book', 'Assignment Submission', 'Discussion Forums'],
      permissions: [],
    },
    {
      id: 'microsoft-teams',
      name: 'Microsoft Teams',
      type: 'communication',
      icon: <IconCloud style={{ color: '#5059C9' }} />,
      status: 'syncing',
      description: 'Collaborate through Microsoft Teams for Education',
      lastSync: '2024-01-29 11:00:00',
      features: ['Video Classes', 'Chat Integration', 'File Sharing', 'Assignment Distribution'],
      permissions: ['read', 'write', 'meetings'],
    },
    {
      id: 'google-drive',
      name: 'Google Drive',
      type: 'cloud',
      icon: <IconFolder style={{ color: '#0F9D58' }} />,
      status: 'connected',
      description: 'Store and share educational content via Google Drive',
      lastSync: '2024-01-29 08:45:00',
      features: ['File Storage', 'Document Sharing', 'Collaborative Editing', 'Backup'],
      permissions: ['read', 'write', 'share'],
    },
    {
      id: 'kahoot',
      name: 'Kahoot!',
      type: 'gaming',
      icon: <IconDeviceGamepad style={{ color: '#46178F' }} />,
      status: 'error',
      description: 'Create and play learning games with Kahoot!',
      features: ['Quiz Creation', 'Live Games', 'Reports', 'Student Engagement'],
      permissions: [],
    },
  ];

  const apiEndpoints: ApiEndpoint[] = [
    {
      id: '1',
      name: 'Get Student Progress',
      method: 'GET',
      endpoint: '/api/v1/students/{id}/progress',
      description: 'Retrieve student progress and achievements',
      status: 'active',
      lastCall: '2024-01-29 11:30:00',
      callCount: 1547,
    },
    {
      id: '2',
      name: 'Submit Assignment',
      method: 'POST',
      endpoint: '/api/v1/assignments/submit',
      description: 'Submit student assignments',
      status: 'active',
      lastCall: '2024-01-29 11:28:00',
      callCount: 892,
    },
    {
      id: '3',
      name: 'Update Grades',
      method: 'PUT',
      endpoint: '/api/v1/grades/{id}',
      description: 'Update student grades',
      status: 'active',
      lastCall: '2024-01-29 10:15:00',
      callCount: 456,
    },
    {
      id: '4',
      name: 'Sync Roblox Data',
      method: 'POST',
      endpoint: '/api/v1/roblox/sync',
      description: 'Synchronize data with Roblox platform',
      status: 'error',
      lastCall: '2024-01-29 09:00:00',
      callCount: 78,
    },
  ];


  const getStatusChip = (status: string) => {
    const statusConfig = {
      connected: { label: 'Connected', color: 'green' as const },
      disconnected: { label: 'Disconnected', color: 'gray' as const },
      error: { label: 'Error', color: 'red' as const },
      syncing: { label: 'Syncing', color: 'blue' as const },
      active: { label: 'Active', color: 'green' as const },
      inactive: { label: 'Inactive', color: 'gray' as const },
    };
    const config = statusConfig[status as keyof typeof statusConfig];
    return <Chip size="sm" color={config?.color || 'gray'}>{config?.label || status}</Chip>;
  };

  const handleConnect = (integration: Integration) => {
    setSelectedIntegration(integration);
    setConfigDialogOpen(true);
  };

  const handleDisconnect = (integration: Integration) => {
    console.log('Disconnecting:', integration.name);
  };

  return (
    <Grid gutter="lg">
      {/* Header */}
      <Grid.Col span={12}>
        <Card withBorder>
          <Group justify="space-between" align="center" p="md">
            <Group>
              <IconApi size={32} />
              <Box>
                <Text size="lg" fw={600}>
                  Platform Integrations
                </Text>
                <Text size="sm" c="dimmed">
                  Connect with learning management systems and external platforms
                </Text>
              </Box>
            </Group>
            <Group>
              <Button variant="outline" leftSection={<IconApi />} onClick={() => setApiDialogOpen(true)}>
                API Docs
              </Button>
              <Button leftSection={<IconPlus />}>
                Add Integration
              </Button>
            </Group>
          </Group>
        </Card>
      </Grid.Col>

      {/* Stats Cards */}
      <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
        <Card withBorder>
          <Stack gap="xs" p="md">
            <Text size="xs" c="dimmed">
              Active Integrations
            </Text>
            <Text size="xl" fw={700}>
              {integrations.filter(i => i.status === 'connected').length}
            </Text>
            <Text size="xs" c="green">
              {integrations.length} total available
            </Text>
          </Stack>
        </Card>
      </Grid.Col>

      <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
        <Card withBorder>
          <Stack gap="xs" p="md">
            <Text size="xs" c="dimmed">
              API Calls Today
            </Text>
            <Text size="xl" fw={700}>
              {apiEndpoints.reduce((sum, api) => sum + api.callCount, 0).toLocaleString()}
            </Text>
            <Text size="xs" c="dimmed">
              Across {apiEndpoints.length} endpoints
            </Text>
          </Stack>
        </Card>
      </Grid.Col>

      <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
        <Card withBorder>
          <Stack gap="xs" p="md">
            <Text size="xs" c="dimmed">
              Data Synced
            </Text>
            <Text size="xl" fw={700}>
              245 GB
            </Text>
            <Text size="xs" c="dimmed">
              This month
            </Text>
          </Stack>
        </Card>
      </Grid.Col>

      <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
        <Card withBorder>
          <Stack gap="xs" p="md">
            <Text size="xs" c="dimmed">
              System Health
            </Text>
            <Text size="xl" fw={700} c="green">
              98.5%
            </Text>
            <Text size="xs" c="dimmed">
              Uptime last 30 days
            </Text>
          </Stack>
        </Card>
      </Grid.Col>

      {/* Roblox Integration Highlight */}
      <Grid.Col span={12}>
        <Alert color="green" icon={<IconDeviceGamepad />}>
          <Group justify="space-between" align="center">
            <Box>
              <Text fw={500}>Roblox Integration Active</Text>
              <Text size="sm">Your educational experiences are syncing with Roblox. Last sync: 5 minutes ago.</Text>
            </Box>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                const robloxIntegration = integrations.find(i => i.id === 'roblox');
                if (robloxIntegration) {
                  setSelectedIntegration(robloxIntegration);
                  setApiDialogOpen(true);
                }
              }}
            >
              View Details
            </Button>
          </Group>
        </Alert>
      </Grid.Col>

      {/* Integration Cards */}
      <Grid.Col span={12}>
        <Text size="lg" fw={600} mb="md">
          Available Integrations
        </Text>
        <Grid gutter="md">
          {integrations.map((integration) => (
            <Grid.Col key={integration.id} span={{ base: 12, md: 6, lg: 4 }}>
              <Card
                withBorder
                h="100%"
                style={{
                  opacity: integration.status === 'disconnected' ? 0.7 : 1,
                  transition: 'all 0.3s',
                  cursor: integration.status !== 'disconnected' ? 'pointer' : 'default'
                }}
              >
                <Stack gap="md" p="md">
                  {/* Header */}
                  <Group justify="space-between" align="flex-start">
                    <Group>
                      {integration.icon}
                      <Box>
                        <Text size="sm" fw={600}>
                          {integration.name}
                        </Text>
                        <Text size="xs" c="dimmed">
                          {integration.type}
                        </Text>
                      </Box>
                    </Group>
                    {getStatusChip(integration.status)}
                  </Group>

                  {/* Description */}
                  <Text size="sm" c="dimmed">
                    {integration.description}
                  </Text>

                  {/* Features */}
                  <Box>
                    <Text size="xs" c="dimmed" mb="xs">
                      Features:
                    </Text>
                    <Group gap="xs">
                      {integration.features.map((feature, idx) => (
                        <Chip key={idx} size="xs" variant="outline">{feature}</Chip>
                      ))}
                    </Group>
                  </Box>

                  {/* Status Info */}
                  {integration.lastSync && (
                    <Group justify="space-between" align="center">
                      <Text size="xs" c="dimmed">
                        Last sync: {new Date(integration.lastSync).toLocaleString()}
                      </Text>
                      {integration.status === 'syncing' && (
                        <Progress value={75} size="sm" w={100} />
                      )}
                    </Group>
                  )}

                  {/* Actions */}
                  <Group>
                    {integration.status === 'disconnected' ? (
                      <Button
                        fullWidth
                        onClick={() => handleConnect(integration)}
                      >
                        Connect
                      </Button>
                    ) : (
                      <>
                        <Button
                          variant="outline"
                          leftSection={<IconSettings />}
                          style={{ flex: 1 }}
                          onClick={() => handleConnect(integration)}
                        >
                          Configure
                        </Button>
                        <Button
                          variant="outline"
                          color="red"
                          onClick={() => handleDisconnect(integration)}
                        >
                          Disconnect
                        </Button>
                      </>
                    )}
                  </Group>
                </Stack>
              </Card>
            </Grid.Col>
          ))}
        </Grid>
      </Grid.Col>

      {/* API Endpoints */}
      <Grid.Col span={12}>
        <Card withBorder>
          <Group justify="space-between" align="center" p="md">
            <Text size="lg" fw={600}>
              API Endpoints
            </Text>
            <Button variant="outline" leftSection={<IconCode />}>
              Generate API Key
            </Button>
          </Group>
          <Divider />
          {apiEndpoints.map((endpoint, index) => (
            <Box key={endpoint.id}>
              <Group justify="space-between" p="md">
                <Group>
                  <Chip
                    size="sm"
                    color={
                      endpoint.method === 'GET' ? 'blue' :
                      endpoint.method === 'POST' ? 'green' :
                      endpoint.method === 'PUT' ? 'yellow' : 'red'
                    }
                    style={{ minWidth: 60 }}
                  >
                    {endpoint.method}
                  </Chip>
                  <Box>
                    <Group gap="xs">
                      <Text size="sm" fw={600}>
                        {endpoint.name}
                      </Text>
                      {getStatusChip(endpoint.status)}
                    </Group>
                    <Text size="xs" ff="monospace" c="dimmed">
                      {endpoint.endpoint}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {endpoint.description} • {endpoint.callCount} calls
                      {endpoint.lastCall && ` • Last: ${new Date(endpoint.lastCall).toLocaleTimeString()}`}
                    </Text>
                  </Box>
                </Group>
                <ActionIcon size="sm" variant="subtle">
                  <IconEye />
                </ActionIcon>
              </Group>
              {index < apiEndpoints.length - 1 && <Divider />}
            </Box>
          ))}
        </Card>
      </Grid.Col>

      {/* Configuration Dialog */}
      <Modal
        opened={configDialogOpen}
        onClose={() => setConfigDialogOpen(false)}
        title={`Configure ${selectedIntegration?.name}`}
        size="md"
      >
        <Stack gap="md">
          <TextInput
            label="API Key"
            type="password"
            defaultValue={selectedIntegration?.apiKey}
            description="Enter your API key for this integration"
          />
          <TextInput
            label="Webhook URL"
            defaultValue={selectedIntegration?.webhookUrl}
            description="Optional: Webhook for real-time updates"
          />
          <Box>
            <Text size="sm" fw={500} mb="xs">
              Permissions
            </Text>
            <Stack gap="xs">
              <Checkbox defaultChecked label="Read data" />
              <Checkbox defaultChecked label="Write data" />
              <Checkbox label="Delete data" />
              <Checkbox defaultChecked label="Real-time sync" />
            </Stack>
          </Box>
          <Group justify="flex-end" mt="md">
            <Button variant="outline" onClick={() => setConfigDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => setConfigDialogOpen(false)}>
              Save Configuration
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* API Documentation Dialog */}
      <Modal
        opened={apiDialogOpen}
        onClose={() => setApiDialogOpen(false)}
        title="API Documentation"
        size="lg"
      >
        <Stack gap="md">
          <Alert color="blue">
            <Text fw={500}>API Base URL</Text>
            <Text size="sm" ff="monospace">https://api.educationalplatform.com/v1</Text>
          </Alert>
          <Text size="sm">
            Use your API key in the Authorization header: Bearer YOUR_API_KEY
          </Text>
          <Text size="sm">
            Rate limit: 1000 requests per hour
          </Text>
          <Group justify="flex-end" mt="md">
            <Button variant="outline" onClick={() => setApiDialogOpen(false)}>
              Close
            </Button>
            <Button leftSection={<IconDownload />}>
              Download Full Documentation
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Grid>
  );
}