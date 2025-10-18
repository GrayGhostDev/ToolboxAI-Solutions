/**
 * RobloxStudioIntegration Component
 *
 * Enhanced integration component with modern UI/UX combining AI chat interface
 * with Roblox Studio plugin communication and environment management.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Grid,
  Paper,
  Text,
  Button,
  Alert,
  Badge,
  Stack,
  Card,
  ActionIcon,
  Tooltip,
  Progress,
  Divider,
  Group,
  Tabs,
  Timeline,
  Avatar,
  ThemeIcon,
  SimpleGrid,
  useMantineTheme
} from '@mantine/core';
import {
  IconPlayerPlay,
  IconDownload,
  IconShare,
  IconRefresh,
  IconSettings,
  IconCode,
  IconEye,
  IconCloudUpload,
  IconCircleCheck,
  IconExclamationMark,
  IconAlertTriangle,
  IconRocket,
  IconBook,
  IconWorld,
  IconSparkles,
  IconBrandRoblox,
  IconChecks,
  IconClock,
  IconX
} from '@tabler/icons-react';

// Type assertion helpers for Mantine compound components
const GridCol = Grid.Col as any;
const CardSection = Card.Section as any;
const TabsList = Tabs.List as any;
const TabsTab = Tabs.Tab as any;
const TabsPanel = Tabs.Panel as any;
const TimelineItem = Timeline.Item as any;

import { RobloxAIChat } from './RobloxAIChat';
import { useAppSelector } from '../../store';
import { api } from '../../services/api';
import { pusherService } from '../../services/pusher';
import { WebSocketMessageType } from '../../types/websocket';

interface PluginStatus {
  connected: boolean;
  version?: string;
  studioVersion?: string;
  lastHeartbeat?: string;
}

interface GeneratedEnvironment {
  id: string;
  name: string;
  status: 'generating' | 'ready' | 'error';
  progress?: number;
  previewUrl?: string;
  downloadUrl?: string;
  deployUrl?: string;
  error?: string;
  metadata?: {
    theme: string;
    mapType: string;
    learningObjectives: string[];
    difficulty: string;
  };
}

export const RobloxStudioIntegration: React.FunctionComponent<Record<string, any>> = () => {
  const theme = useMantineTheme();
  const currentUser = useAppSelector(state => state.user);

  // State
  const [pluginStatus, setPluginStatus] = useState<PluginStatus>({ connected: false });
  const [environments, setEnvironments] = useState<GeneratedEnvironment[]>([]);
  const [isCheckingPlugin, setIsCheckingPlugin] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedEnvironment, setSelectedEnvironment] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('create');

  // Check plugin status
  const checkPluginStatus = useCallback(async () => {
    setIsCheckingPlugin(true);
    try {
      const status = await api.checkRobloxPluginStatus();
      setPluginStatus(status);
      setError(null);
    } catch (err) {
      console.error('Failed to check plugin status:', err);
      setPluginStatus({ connected: false });
      setError('Unable to connect to Roblox Studio plugin. Please ensure the plugin is installed and Studio is running.');
    } finally {
      setIsCheckingPlugin(false);
    }
  }, []);

  // Load environments
  const loadEnvironments = useCallback(async () => {
    try {
      const worlds = await api.listRobloxWorlds();
      const mappedEnvironments: GeneratedEnvironment[] = worlds.map(world => ({
        id: world.id,
        name: world.name || 'Untitled Environment',
        status: world.status === 'published' ? 'ready' : world.status === 'draft' ? 'generating' : 'ready',
        previewUrl: world.previewUrl,
        downloadUrl: world.downloadUrl,
        metadata: {
          theme: world.theme || 'Unknown',
          mapType: world.mapType || 'classroom',
          learningObjectives: world.learningObjectives || [],
          difficulty: world.difficulty || 'medium'
        }
      }));
      setEnvironments(mappedEnvironments);
    } catch (err) {
      console.error('Failed to load environments:', err);
    }
  }, []);

  // Initialize
  useEffect(() => {
    checkPluginStatus();
    loadEnvironments();

    // Set up periodic plugin status checks
    const interval = setInterval(checkPluginStatus, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, [checkPluginStatus, loadEnvironments]);

  // Handle environment generation completion
  useEffect(() => {
    const handleEnvironmentReady = (data: any) => {
      const { environmentId, previewUrl, downloadUrl } = data;

      setEnvironments(prev => prev.map(env =>
        env.id === environmentId
          ? { ...env, status: 'ready', previewUrl, downloadUrl }
          : env
      ));
    };

    const handleEnvironmentError = (data: any) => {
      const { requestId, error } = data;

      setEnvironments(prev => prev.map(env =>
        env.id === requestId
          ? { ...env, status: 'error', error }
          : env
      ));
    };

    // Subscribe to environment events
    const subscriptionId = pusherService.subscribe(
      'roblox-environments',
      (message: any) => {
        switch (message.type) {
          case WebSocketMessageType.ROBLOX_ENV_READY:
            handleEnvironmentReady(message.payload);
            break;
          case WebSocketMessageType.ROBLOX_ENV_ERROR:
            handleEnvironmentError(message.payload);
            break;
        }
      }
    );

    return () => {
      pusherService.unsubscribe(subscriptionId);
    };
  }, []);

  // Deploy to Roblox Studio
  const deployToStudio = useCallback(async (environmentId: string) => {
    if (!pluginStatus.connected) {
      setError('Roblox Studio plugin is not connected. Please ensure Studio is running and the plugin is installed.');
      return;
    }

    try {
      await api.deployToRoblox(environmentId);
      setError(null);
      loadEnvironments();
    } catch (err) {
      console.error('Failed to deploy to Studio:', err);
      setError('Failed to deploy environment to Roblox Studio. Please try again.');
    }
  }, [pluginStatus.connected, loadEnvironments]);

  // Download environment
  const downloadEnvironment = useCallback(async (environmentId: string) => {
    try {
      const response = await api.exportRobloxEnvironment(environmentId);

      // Create download link
      const blob = new Blob([response], { type: 'application/octet-stream' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `roblox-environment-${environmentId}.rbxl`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download environment:', err);
      setError('Failed to download environment. Please try again.');
    }
  }, []);

  // Share environment
  const shareEnvironment = useCallback(async (environment: GeneratedEnvironment) => {
    if (navigator.share && environment.previewUrl) {
      try {
        await navigator.share({
          title: environment.name,
          text: `Check out this Roblox educational environment: ${environment.name}`,
          url: environment.previewUrl
        });
      } catch (err) {
        navigator.clipboard?.writeText(environment.previewUrl);
      }
    } else if (environment.previewUrl) {
      navigator.clipboard?.writeText(environment.previewUrl);
    }
  }, []);

  // Install plugin
  const installPlugin = useCallback(async () => {
    try {
      const installInfo = await api.getRobloxPluginInstallInfo();

      if (installInfo.installUrl) {
        window.open(installInfo.installUrl, '_blank');
      }
    } catch (err) {
      console.error('Failed to get plugin install info:', err);
      setError('Failed to get plugin installation information.');
    }
  }, []);

  // Get environment counts
  const envCounts = {
    total: environments.length,
    ready: environments.filter(e => e.status === 'ready').length,
    generating: environments.filter(e => e.status === 'generating').length,
    error: environments.filter(e => e.status === 'error').length
  };

  return (
    <Box style={{
      height: '100%',
      width: '100%',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden'
    }}>
      {/* Enhanced Header with Stats */}
      <Paper shadow="md" p="lg" mb="md" style={{
        background: 'linear-gradient(135deg, rgba(6, 147, 227, 0.1) 0%, rgba(155, 81, 224, 0.1) 100%)',
        borderLeft: `4px solid ${theme.colors.blue[6]}`
      }}>
        <Group justify="space-between" align="flex-start">
          <div>
            <Group gap="sm" mb="xs">
              <ThemeIcon size="xl" variant="gradient" gradient={{ from: 'blue', to: 'violet' }}>
                <IconBrandRoblox size={24} />
              </ThemeIcon>
              <div>
                <Text size="xl" fw={700} mb={4}>
                  Roblox Studio Integration
                </Text>
                <Text size="sm" c="dimmed">
                  Create, manage, and deploy educational Roblox environments with AI
                </Text>
              </div>
            </Group>

            {/* Quick Stats */}
            <SimpleGrid cols={4} spacing="md" mt="md">
              <Paper p="xs" radius="md" withBorder>
                <Group gap="xs">
                  <ThemeIcon size="sm" color="blue" variant="light">
                    <IconWorld size={14} />
                  </ThemeIcon>
                  <div>
                    <Text size="xs" c="dimmed">Total</Text>
                    <Text size="lg" fw={600}>{envCounts.total}</Text>
                  </div>
                </Group>
              </Paper>
              <Paper p="xs" radius="md" withBorder>
                <Group gap="xs">
                  <ThemeIcon size="sm" color="green" variant="light">
                    <IconChecks size={14} />
                  </ThemeIcon>
                  <div>
                    <Text size="xs" c="dimmed">Ready</Text>
                    <Text size="lg" fw={600}>{envCounts.ready}</Text>
                  </div>
                </Group>
              </Paper>
              <Paper p="xs" radius="md" withBorder>
                <Group gap="xs">
                  <ThemeIcon size="sm" color="yellow" variant="light">
                    <IconClock size={14} />
                  </ThemeIcon>
                  <div>
                    <Text size="xs" c="dimmed">Generating</Text>
                    <Text size="lg" fw={600}>{envCounts.generating}</Text>
                  </div>
                </Group>
              </Paper>
              <Paper p="xs" radius="md" withBorder>
                <Group gap="xs">
                  <ThemeIcon size="sm" color="red" variant="light">
                    <IconX size={14} />
                  </ThemeIcon>
                  <div>
                    <Text size="xs" c="dimmed">Errors</Text>
                    <Text size="lg" fw={600}>{envCounts.error}</Text>
                  </div>
                </Group>
              </Paper>
            </SimpleGrid>
          </div>

          {/* Plugin Status */}
          <Stack gap="sm" align="flex-end">
            <Badge
              size="lg"
              leftSection={pluginStatus.connected ? <IconCircleCheck size={16} /> : <IconExclamationMark size={16} />}
              color={pluginStatus.connected ? 'green' : 'red'}
              variant="dot"
            >
              {pluginStatus.connected ? 'Plugin Connected' : 'Plugin Disconnected'}
            </Badge>

            <Group gap="xs">
              <Button
                size="xs"
                variant="light"
                onClick={checkPluginStatus}
                disabled={isCheckingPlugin}
                leftSection={<IconRefresh size={14} />}
              >
                {isCheckingPlugin ? 'Checking...' : 'Refresh'}
              </Button>

              {!pluginStatus.connected && (
                <Button
                  size="xs"
                  onClick={installPlugin}
                  leftSection={<IconCloudUpload size={14} />}
                  gradient={{ from: 'blue', to: 'violet' }}
                  variant="gradient"
                >
                  Install Plugin
                </Button>
              )}
            </Group>

            {pluginStatus.connected && pluginStatus.version && (
              <Text size="xs" c="dimmed">
                v{pluginStatus.version}
                {pluginStatus.studioVersion && ` • Studio ${pluginStatus.studioVersion}`}
              </Text>
            )}
          </Stack>
        </Group>
      </Paper>

      {/* Error Alert */}
      {error && (
        <Alert
          color="red"
          mb="md"
          title="Error"
          icon={<IconAlertTriangle />}
          onClose={() => setError(null)}
          closeButtonLabel="Close"
        >
          {error}
        </Alert>
      )}

      {/* Main Content with Tabs */}
      <Tabs value={activeTab} onChange={(value) => setActiveTab(value || 'create')} style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <TabsList>
          <TabsTab value="create" leftSection={<IconSparkles size={16} />}>
            Create Environment
          </TabsTab>
          <TabsTab value="manage" leftSection={<IconWorld size={16} />}>
            Manage ({environments.length})
          </TabsTab>
          <TabsTab value="docs" leftSection={<IconBook size={16} />}>
            Documentation
          </TabsTab>
        </TabsList>

        {/* Create Tab */}
        <TabsPanel value="create" style={{ flex: 1, display: 'flex', overflow: 'hidden', paddingTop: 16 }}>
          <Grid style={{ flex: 1, overflow: 'hidden', height: '100%' }}>
            <GridCol span={12}>
              <Paper shadow="sm" style={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden'
              }}>
                <RobloxAIChat />
              </Paper>
            </GridCol>
          </Grid>
        </TabsPanel>

        {/* Manage Tab */}
        <TabsPanel value="manage" style={{ flex: 1, overflow: 'auto', paddingTop: 16 }}>
          <Box style={{ padding: theme.spacing.sm }}>
            {environments.length === 0 ? (
              <Paper p="xl" radius="md" withBorder style={{ textAlign: 'center' }}>
                <ThemeIcon size={64} radius="xl" variant="light" color="blue" style={{ margin: '0 auto 1rem' }}>
                  <IconRocket size={32} />
                </ThemeIcon>
                <Text size="lg" fw={600} mb="xs">
                  No environments created yet
                </Text>
                <Text size="sm" c="dimmed" mb="lg">
                  Use the AI chat in the "Create Environment" tab to generate your first Roblox world
                </Text>
                <Button
                  onClick={() => setActiveTab('create')}
                  leftSection={<IconSparkles size={16} />}
                  variant="gradient"
                  gradient={{ from: 'blue', to: 'violet' }}
                >
                  Create Your First Environment
                </Button>
              </Paper>
            ) : (
              <SimpleGrid cols={{ base: 1, md: 2, lg: 3 }} spacing="md">
                {environments.map((environment) => (
                  <Card
                    key={environment.id}
                    shadow="sm"
                    padding="lg"
                    radius="md"
                    withBorder
                    style={{
                      cursor: 'pointer',
                      borderColor: selectedEnvironment === environment.id
                        ? theme.colors.blue[4]
                        : undefined,
                      borderWidth: selectedEnvironment === environment.id ? 2 : 1,
                      transition: 'all 0.2s ease'
                    }}
                    onClick={() => setSelectedEnvironment(environment.id)}
                  >
                    <CardSection withBorder inheritPadding py="xs">
                      <Group justify="space-between" align="center">
                        <Text fw={600} lineClamp={1}>
                          {environment.name}
                        </Text>

                        <Badge
                          size="sm"
                          color={
                            environment.status === 'ready' ? 'green' :
                            environment.status === 'error' ? 'red' : 'yellow'
                          }
                          leftSection={
                            environment.status === 'ready' ? <IconCircleCheck size={12} /> :
                            environment.status === 'error' ? <IconExclamationMark size={12} /> : <IconClock size={12} />
                          }
                        >
                          {environment.status}
                        </Badge>
                      </Group>
                    </CardSection>

                    {environment.metadata && (
                      <Box my="md">
                        <Group gap="xs" mb="xs">
                          <Badge size="xs" variant="light" color="blue">
                            {environment.metadata.theme}
                          </Badge>
                          <Badge size="xs" variant="light" color="violet">
                            {environment.metadata.mapType}
                          </Badge>
                          <Badge size="xs" variant="light" color="grape">
                            {environment.metadata.difficulty}
                          </Badge>
                        </Group>
                        {environment.metadata.learningObjectives.length > 0 && (
                          <Text size="xs" c="dimmed" lineClamp={2}>
                            {environment.metadata.learningObjectives.join(', ')}
                          </Text>
                        )}
                      </Box>
                    )}

                    {environment.status === 'generating' && environment.progress !== undefined && (
                      <Box mb="md">
                        <Group justify="space-between" mb="xs">
                          <Text size="xs" c="dimmed">
                            Generating...
                          </Text>
                          <Text size="xs" fw={600}>
                            {environment.progress}%
                          </Text>
                        </Group>
                        <Progress value={environment.progress} color="blue" size="sm" />
                      </Box>
                    )}

                    {environment.status === 'error' && environment.error && (
                      <Alert color="red" mb="md" variant="light">
                        {environment.error}
                      </Alert>
                    )}

                    {environment.status === 'ready' && (
                      <CardSection inheritPadding py="xs">
                        <Group gap="xs">
                          <Button
                            size="xs"
                            leftSection={<IconPlayerPlay size={14} />}
                            onClick={(e) => {
                              e.stopPropagation();
                              deployToStudio(environment.id);
                            }}
                            disabled={!pluginStatus.connected}
                            fullWidth
                            variant="gradient"
                            gradient={{ from: 'blue', to: 'violet' }}
                          >
                            Deploy
                          </Button>

                          <Tooltip label="Download">
                            <ActionIcon
                              variant="light"
                              color="blue"
                              onClick={(e) => {
                                e.stopPropagation();
                                downloadEnvironment(environment.id);
                              }}
                            >
                              <IconDownload size={16} />
                            </ActionIcon>
                          </Tooltip>

                          {environment.previewUrl && (
                            <Tooltip label="Preview">
                              <ActionIcon
                                variant="light"
                                color="violet"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  window.open(environment.previewUrl, '_blank');
                                }}
                              >
                                <IconEye size={16} />
                              </ActionIcon>
                            </Tooltip>
                          )}

                          <Tooltip label="Share">
                            <ActionIcon
                              variant="light"
                              color="grape"
                              onClick={(e) => {
                                e.stopPropagation();
                                shareEnvironment(environment);
                              }}
                            >
                              <IconShare size={16} />
                            </ActionIcon>
                          </Tooltip>
                        </Group>
                      </CardSection>
                    )}
                  </Card>
                ))}
              </SimpleGrid>
            )}
          </Box>
        </TabsPanel>

        {/* Documentation Tab */}
        <TabsPanel value="docs" style={{ flex: 1, overflow: 'auto', paddingTop: 16 }}>
          <Box style={{ padding: theme.spacing.md }}>
            <Paper p="xl" radius="md" withBorder>
              <Text size="xl" fw={700} mb="md">
                Getting Started with Roblox Studio Integration
              </Text>

              <Timeline active={1} bulletSize={24} lineWidth={2}>
                <TimelineItem bullet={<IconCloudUpload size={12} />} title="Install Plugin">
                  <Text c="dimmed" size="sm">
                    Download and install the ToolboxAI plugin from the Roblox Creator Store
                  </Text>
                  <Button
                    size="xs"
                    variant="light"
                    mt="xs"
                    leftSection={<IconCloudUpload size={14} />}
                    onClick={installPlugin}
                  >
                    Get Plugin
                  </Button>
                </TimelineItem>

                <TimelineItem bullet={<IconSparkles size={12} />} title="Create Environment">
                  <Text c="dimmed" size="sm">
                    Use the AI chat to describe your educational environment and let AI generate it
                  </Text>
                </TimelineItem>

                <TimelineItem bullet={<IconPlayerPlay size={12} />} title="Deploy to Studio">
                  <Text c="dimmed" size="sm">
                    Once generated, deploy your environment directly to Roblox Studio with one click
                  </Text>
                </TimelineItem>

                <TimelineItem bullet={<IconRocket size={12} />} title="Publish & Share">
                  <Text c="dimmed" size="sm">
                    Customize in Studio, then publish to Roblox for your students to experience
                  </Text>
                </TimelineItem>
              </Timeline>

              <Divider my="xl" />

              <Text size="lg" fw={600} mb="md">
                Features
              </Text>
              <Stack gap="md">
                <Group>
                  <ThemeIcon color="blue" variant="light">
                    <IconSparkles size={16} />
                  </ThemeIcon>
                  <div style={{ flex: 1 }}>
                    <Text fw={500}>AI-Powered Generation</Text>
                    <Text size="sm" c="dimmed">
                      Describe your learning objectives and let AI create engaging 3D environments
                    </Text>
                  </div>
                </Group>
                <Group>
                  <ThemeIcon color="violet" variant="light">
                    <IconCode size={16} />
                  </ThemeIcon>
                  <div style={{ flex: 1 }}>
                    <Text fw={500}>Script Optimization</Text>
                    <Text size="sm" c="dimmed">
                      Automatically optimize Lua scripts for performance and best practices
                    </Text>
                  </div>
                </Group>
                <Group>
                  <ThemeIcon color="grape" variant="light">
                    <IconWorld size={16} />
                  </ThemeIcon>
                  <div style={{ flex: 1 }}>
                    <Text fw={500}>Environment Management</Text>
                    <Text size="sm" c="dimmed">
                      Track, deploy, and share your generated environments across projects
                    </Text>
                  </div>
                </Group>
              </Stack>
            </Paper>
          </Box>
        </TabsPanel>
      </Tabs>
    </Box>
  );
};

export default RobloxStudioIntegration;
