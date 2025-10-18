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
  TextInput,
  Select,
  SegmentedControl,
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
  IconX,
  IconSearch,
  IconFilter,
  IconSortAscending,
  IconTrash
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

  // Manage tab state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('name');

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

  // Filter and sort environments
  const filteredEnvironments = React.useMemo(() => {
    let filtered = environments;

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(env =>
        env.name.toLowerCase().includes(query) ||
        env.metadata?.theme.toLowerCase().includes(query) ||
        env.metadata?.mapType.toLowerCase().includes(query) ||
        env.metadata?.learningObjectives.some(obj => obj.toLowerCase().includes(query))
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(env => env.status === statusFilter);
    }

    // Apply sorting
    const sorted = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'name-desc':
          return b.name.localeCompare(a.name);
        case 'status':
          return a.status.localeCompare(b.status);
        case 'difficulty':
          return (a.metadata?.difficulty || '').localeCompare(b.metadata?.difficulty || '');
        default:
          return 0;
      }
    });

    return sorted;
  }, [environments, searchQuery, statusFilter, sortBy]);

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
            {/* Search and Filter Controls */}
            {environments.length > 0 && (
              <Paper p="md" mb="md" withBorder>
                <Stack gap="md">
                  <Group align="flex-end">
                    <TextInput
                      placeholder="Search by name, theme, or learning objectives..."
                      leftSection={<IconSearch size={16} />}
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      style={{ flex: 1 }}
                    />
                    <Select
                      placeholder="Filter by Status"
                      leftSection={<IconFilter size={16} />}
                      value={statusFilter}
                      onChange={(value) => setStatusFilter(value || 'all')}
                      data={[
                        { value: 'all', label: 'All Status' },
                        { value: 'ready', label: 'Ready' },
                        { value: 'generating', label: 'Generating' },
                        { value: 'error', label: 'Error' }
                      ]}
                      style={{ minWidth: 160 }}
                    />
                    <Select
                      placeholder="Sort By"
                      leftSection={<IconSortAscending size={16} />}
                      value={sortBy}
                      onChange={(value) => setSortBy(value || 'name')}
                      data={[
                        { value: 'name', label: 'Name (A-Z)' },
                        { value: 'name-desc', label: 'Name (Z-A)' },
                        { value: 'status', label: 'Status' },
                        { value: 'difficulty', label: 'Difficulty' }
                      ]}
                      style={{ minWidth: 160 }}
                    />
                  </Group>

                  {(searchQuery || statusFilter !== 'all') && (
                    <Group gap="xs">
                      <Text size="sm" c="dimmed">
                        Showing {filteredEnvironments.length} of {environments.length} environments
                      </Text>
                      {(searchQuery || statusFilter !== 'all') && (
                        <Button
                          size="xs"
                          variant="subtle"
                          onClick={() => {
                            setSearchQuery('');
                            setStatusFilter('all');
                          }}
                        >
                          Clear filters
                        </Button>
                      )}
                    </Group>
                  )}
                </Stack>
              </Paper>
            )}

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
            ) : filteredEnvironments.length === 0 ? (
              <Paper p="xl" radius="md" withBorder style={{ textAlign: 'center' }}>
                <ThemeIcon size={64} radius="xl" variant="light" color="yellow" style={{ margin: '0 auto 1rem' }}>
                  <IconSearch size={32} />
                </ThemeIcon>
                <Text size="lg" fw={600} mb="xs">
                  No environments found
                </Text>
                <Text size="sm" c="dimmed" mb="lg">
                  Try adjusting your search or filters to find what you're looking for
                </Text>
                <Button
                  onClick={() => {
                    setSearchQuery('');
                    setStatusFilter('all');
                  }}
                  variant="light"
                >
                  Clear filters
                </Button>
              </Paper>
            ) : (
              <SimpleGrid cols={{ base: 1, md: 2, lg: 3 }} spacing="md">
                {filteredEnvironments.map((environment) => (
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
            <Stack gap="lg">
              {/* Getting Started */}
              <Paper p="xl" radius="md" withBorder>
                <Text size="xl" fw={700} mb="md">
                  Getting Started with Roblox Studio Integration
                </Text>

                <Timeline active={3} bulletSize={24} lineWidth={2}>
                  <TimelineItem bullet={<IconCloudUpload size={12} />} title="Install Plugin">
                    <Text c="dimmed" size="sm" mb="xs">
                      Download and install the ToolboxAI plugin from the Roblox Creator Store or directly from Roblox Studio.
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
                    <Text size="xs" c="dimmed" mt="md">
                      <strong>Alternative:</strong> In Roblox Studio, go to Plugins → Manage Plugins → Search for "ToolboxAI"
                    </Text>
                  </TimelineItem>

                  <TimelineItem bullet={<IconSparkles size={12} />} title="Create Environment">
                    <Text c="dimmed" size="sm" mb="xs">
                      Use the AI chat in the "Create Environment" tab to describe your educational environment. Specify:
                    </Text>
                    <Stack gap="xs" ml="md" mt="xs">
                      <Text size="xs" c="dimmed">• Learning objectives (e.g., "teach Newton's laws of motion")</Text>
                      <Text size="xs" c="dimmed">• Target age group or grade level</Text>
                      <Text size="xs" c="dimmed">• Environment theme (sci-fi, medieval, modern, etc.)</Text>
                      <Text size="xs" c="dimmed">• Interactive elements needed (puzzles, experiments, games)</Text>
                      <Text size="xs" c="dimmed">• Difficulty level (easy, medium, hard)</Text>
                    </Stack>
                  </TimelineItem>

                  <TimelineItem bullet={<IconPlayerPlay size={12} />} title="Deploy to Studio">
                    <Text c="dimmed" size="sm" mb="xs">
                      Once your environment is generated (status shows "Ready"), click the "Deploy" button to send it directly to your open Roblox Studio instance.
                    </Text>
                    <Text size="xs" c="dimmed" mt="xs">
                      <strong>Note:</strong> Ensure Roblox Studio is running and the ToolboxAI plugin is active.
                    </Text>
                  </TimelineItem>

                  <TimelineItem bullet={<IconSettings size={12} />} title="Customize & Refine">
                    <Text c="dimmed" size="sm" mb="xs">
                      In Roblox Studio, customize the generated environment:
                    </Text>
                    <Stack gap="xs" ml="md" mt="xs">
                      <Text size="xs" c="dimmed">• Adjust lighting and atmosphere</Text>
                      <Text size="xs" c="dimmed">• Fine-tune scripts and interactions</Text>
                      <Text size="xs" c="dimmed">• Add custom assets and decorations</Text>
                      <Text size="xs" c="dimmed">• Test gameplay and learning flow</Text>
                    </Stack>
                  </TimelineItem>

                  <TimelineItem bullet={<IconRocket size={12} />} title="Publish & Share">
                    <Text c="dimmed" size="sm">
                      Publish your environment to Roblox using Studio's publish feature. Share the game link with your students or use the "Share" button to distribute via various channels.
                    </Text>
                  </TimelineItem>
                </Timeline>
              </Paper>

              {/* System Requirements */}
              <Paper p="xl" radius="md" withBorder>
                <Group mb="md">
                  <ThemeIcon size="lg" variant="light" color="blue">
                    <IconSettings size={20} />
                  </ThemeIcon>
                  <Text size="lg" fw={600}>
                    System Requirements
                  </Text>
                </Group>

                <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg">
                  <div>
                    <Text size="sm" fw={600} mb="xs">Roblox Studio</Text>
                    <Stack gap="xs">
                      <Text size="xs" c="dimmed">• Version: Latest stable release recommended</Text>
                      <Text size="xs" c="dimmed">• Operating System: Windows 10+ or macOS 10.13+</Text>
                      <Text size="xs" c="dimmed">• RAM: 4GB minimum, 8GB recommended</Text>
                      <Text size="xs" c="dimmed">• Storage: 2GB free space for plugin and assets</Text>
                    </Stack>
                  </div>
                  <div>
                    <Text size="sm" fw={600} mb="xs">Browser Requirements</Text>
                    <Stack gap="xs">
                      <Text size="xs" c="dimmed">• Chrome 90+, Firefox 88+, Safari 14+, Edge 90+</Text>
                      <Text size="xs" c="dimmed">• JavaScript enabled</Text>
                      <Text size="xs" c="dimmed">• Stable internet connection</Text>
                      <Text size="xs" c="dimmed">• Minimum 5 Mbps upload/download speed</Text>
                    </Stack>
                  </div>
                </SimpleGrid>
              </Paper>

              {/* Features */}
              <Paper p="xl" radius="md" withBorder>
                <Group mb="md">
                  <ThemeIcon size="lg" variant="light" color="violet">
                    <IconSparkles size={20} />
                  </ThemeIcon>
                  <Text size="lg" fw={600}>
                    Key Features
                  </Text>
                </Group>

                <Stack gap="md">
                  <Group align="flex-start">
                    <ThemeIcon color="blue" variant="light">
                      <IconSparkles size={16} />
                    </ThemeIcon>
                    <div style={{ flex: 1 }}>
                      <Text fw={500}>AI-Powered Environment Generation</Text>
                      <Text size="sm" c="dimmed">
                        Leverage advanced AI to create fully immersive 3D learning environments tailored to your curriculum. The AI understands educational concepts and automatically generates appropriate terrain, structures, interactive elements, and Lua scripts aligned with your learning objectives.
                      </Text>
                    </div>
                  </Group>

                  <Group align="flex-start">
                    <ThemeIcon color="violet" variant="light">
                      <IconCode size={16} />
                    </ThemeIcon>
                    <div style={{ flex: 1 }}>
                      <Text fw={500}>Automatic Script Optimization</Text>
                      <Text size="sm" c="dimmed">
                        All generated Lua scripts are automatically optimized for performance, following Roblox best practices. Includes proper event handling, memory management, and efficient algorithms to ensure smooth gameplay even on lower-end devices.
                      </Text>
                    </div>
                  </Group>

                  <Group align="flex-start">
                    <ThemeIcon color="grape" variant="light">
                      <IconWorld size={16} />
                    </ThemeIcon>
                    <div style={{ flex: 1 }}>
                      <Text fw={500}>Environment Management Dashboard</Text>
                      <Text size="sm" c="dimmed">
                        Track all your generated environments in one place. View status, preview before deployment, download .rbxl files for offline editing, and manage multiple projects simultaneously with version control.
                      </Text>
                    </div>
                  </Group>

                  <Group align="flex-start">
                    <ThemeIcon color="teal" variant="light">
                      <IconPlayerPlay size={16} />
                    </ThemeIcon>
                    <div style={{ flex: 1 }}>
                      <Text fw={500}>One-Click Deployment</Text>
                      <Text size="sm" c="dimmed">
                        Seamlessly deploy generated environments directly to your open Roblox Studio instance. No manual file management or complex setup required - just click "Deploy" and the environment loads instantly.
                      </Text>
                    </div>
                  </Group>

                  <Group align="flex-start">
                    <ThemeIcon color="orange" variant="light">
                      <IconShare size={16} />
                    </ThemeIcon>
                    <div style={{ flex: 1 }}>
                      <Text fw={500}>Collaborative Sharing</Text>
                      <Text size="sm" c="dimmed">
                        Share your environments with other educators, co-teachers, or students. Generate shareable links, export to common formats, and collaborate on environment improvements with built-in version tracking.
                      </Text>
                    </div>
                  </Group>
                </Stack>
              </Paper>

              {/* Troubleshooting */}
              <Paper p="xl" radius="md" withBorder>
                <Group mb="md">
                  <ThemeIcon size="lg" variant="light" color="yellow">
                    <IconAlertTriangle size={20} />
                  </ThemeIcon>
                  <Text size="lg" fw={600}>
                    Troubleshooting Common Issues
                  </Text>
                </Group>

                <Stack gap="lg">
                  <div>
                    <Text fw={600} size="sm" mb="xs">Plugin Not Connecting</Text>
                    <Stack gap="xs" ml="md">
                      <Text size="xs" c="dimmed">1. Ensure Roblox Studio is running and fully loaded</Text>
                      <Text size="xs" c="dimmed">2. Check that the ToolboxAI plugin is installed and enabled (Plugins → Manage Plugins)</Text>
                      <Text size="xs" c="dimmed">3. Try restarting Roblox Studio</Text>
                      <Text size="xs" c="dimmed">4. Verify your firewall isn't blocking the connection (allow port 34872)</Text>
                      <Text size="xs" c="dimmed">5. Check the plugin version matches your Studio version</Text>
                    </Stack>
                  </div>

                  <div>
                    <Text fw={600} size="sm" mb="xs">Environment Generation Failed</Text>
                    <Stack gap="xs" ml="md">
                      <Text size="xs" c="dimmed">1. Check your internet connection stability</Text>
                      <Text size="xs" c="dimmed">2. Verify you have sufficient credits/quota in your account</Text>
                      <Text size="xs" c="dimmed">3. Ensure your description includes clear learning objectives</Text>
                      <Text size="xs" c="dimmed">4. Try simplifying your request if it's too complex</Text>
                      <Text size="xs" c="dimmed">5. Contact support if the error persists</Text>
                    </Stack>
                  </div>

                  <div>
                    <Text fw={600} size="sm" mb="xs">Deployment Issues</Text>
                    <Stack gap="xs" ml="md">
                      <Text size="xs" c="dimmed">1. Confirm the environment status is "Ready" before deploying</Text>
                      <Text size="xs" c="dimmed">2. Check that you have a place open in Roblox Studio</Text>
                      <Text size="xs" c="dimmed">3. Ensure sufficient storage space in Studio workspace</Text>
                      <Text size="xs" c="dimmed">4. Try downloading the .rbxl file and importing manually if automatic deployment fails</Text>
                    </Stack>
                  </div>

                  <div>
                    <Text fw={600} size="sm" mb="xs">Performance Issues in Generated Environment</Text>
                    <Stack gap="xs" ml="md">
                      <Text size="xs" c="dimmed">1. Reduce part count by using meshes instead of unions where possible</Text>
                      <Text size="xs" c="dimmed">2. Enable streaming in your place settings for large environments</Text>
                      <Text size="xs" c="dimmed">3. Optimize lighting by using ShadowMap instead of Future lighting</Text>
                      <Text size="xs" c="dimmed">4. Use the Performance Profiler in Studio to identify bottlenecks</Text>
                    </Stack>
                  </div>
                </Stack>
              </Paper>

              {/* FAQ */}
              <Paper p="xl" radius="md" withBorder>
                <Group mb="md">
                  <ThemeIcon size="lg" variant="light" color="green">
                    <IconBook size={20} />
                  </ThemeIcon>
                  <Text size="lg" fw={600}>
                    Frequently Asked Questions
                  </Text>
                </Group>

                <Stack gap="lg">
                  <div>
                    <Text fw={600} size="sm" mb="xs">How long does it take to generate an environment?</Text>
                    <Text size="xs" c="dimmed">
                      Generation time varies based on complexity, typically ranging from 2-10 minutes. Simple classroom environments may take 2-3 minutes, while complex multi-level experiences with extensive scripting can take up to 10 minutes. You'll see real-time progress updates during generation.
                    </Text>
                  </div>

                  <div>
                    <Text fw={600} size="sm" mb="xs">Can I edit the generated environment?</Text>
                    <Text size="xs" c="dimmed">
                      Absolutely! Once deployed to Studio, you have full access to modify terrain, scripts, assets, lighting, and any other aspect. The AI-generated environment serves as a starting point that you can customize to perfectly match your needs.
                    </Text>
                  </div>

                  <div>
                    <Text fw={600} size="sm" mb="xs">What types of educational environments can I create?</Text>
                    <Text size="xs" c="dimmed">
                      You can create virtually any type of educational environment: science labs, historical recreations, mathematics visualizations, language learning scenarios, coding challenges, virtual field trips, simulation experiences, and more. The AI adapts to your subject matter and grade level.
                    </Text>
                  </div>

                  <div>
                    <Text fw={600} size="sm" mb="xs">Is there a limit to how many environments I can create?</Text>
                    <Text size="xs" c="dimmed">
                      Limits depend on your subscription tier. Free accounts can create up to 3 environments per month, while premium accounts have higher limits or unlimited creation. Check your account dashboard for your current usage and limits.
                    </Text>
                  </div>

                  <div>
                    <Text fw={600} size="sm" mb="xs">Can students access the environments I create?</Text>
                    <Text size="xs" c="dimmed">
                      Yes! Once you publish your environment to Roblox, students can access it just like any other Roblox experience. You can share the game link, create a private server, or publish it publicly. You maintain full control over access and permissions.
                    </Text>
                  </div>

                  <div>
                    <Text fw={600} size="sm" mb="xs">What happens if I lose internet connection during generation?</Text>
                    <Text size="xs" c="dimmed">
                      Your generation request continues on our servers. When you reconnect, refresh the "Manage" tab to see the current status. If the generation completed while you were offline, you'll find it ready for deployment.
                    </Text>
                  </div>

                  <div>
                    <Text fw={600} size="sm" mb="xs">Are the generated scripts secure and safe?</Text>
                    <Text size="xs" c="dimmed">
                      Yes, all generated scripts follow Roblox security best practices. They don't include any malicious code, backdoors, or vulnerabilities. However, we recommend reviewing scripts before publishing, especially for environments accessible to students.
                    </Text>
                  </div>
                </Stack>
              </Paper>

              {/* Best Practices */}
              <Paper p="xl" radius="md" withBorder>
                <Group mb="md">
                  <ThemeIcon size="lg" variant="light" color="cyan">
                    <IconChecks size={20} />
                  </ThemeIcon>
                  <Text size="lg" fw={600}>
                    Best Practices
                  </Text>
                </Group>

                <Stack gap="md">
                  <div>
                    <Text fw={500} size="sm" mb="xs">Writing Effective Environment Descriptions</Text>
                    <Text size="xs" c="dimmed" mb="xs">
                      Be specific about learning objectives, target audience, and desired interactions. Instead of "science environment," try "interactive physics lab for 8th graders demonstrating Newton's three laws of motion with hands-on experiments."
                    </Text>
                  </div>

                  <div>
                    <Text fw={500} size="sm" mb="xs">Testing Before Student Access</Text>
                    <Text size="xs" c="dimmed" mb="xs">
                      Always test environments in Studio first. Check for gameplay bugs, performance issues, and ensure learning objectives are clear. Test on both high and low-end devices if possible.
                    </Text>
                  </div>

                  <div>
                    <Text fw={500} size="sm" mb="xs">Version Control</Text>
                    <Text size="xs" c="dimmed" mb="xs">
                      Use Studio's version history to save iterations of your environment. This allows you to revert changes if needed and track improvements over time.
                    </Text>
                  </div>

                  <div>
                    <Text fw={500} size="sm" mb="xs">Accessibility Considerations</Text>
                    <Text size="xs" c="dimmed" mb="xs">
                      Ensure generated environments are accessible to all students. Add text labels for audio cues, provide alternative input methods, and test colorblind-friendly visual designs.
                    </Text>
                  </div>

                  <div>
                    <Text fw={500} size="sm" mb="xs">Regular Updates</Text>
                    <Text size="xs" c="dimmed" mb="xs">
                      Keep the ToolboxAI plugin updated to access new features and improvements. Enable auto-update in the plugin settings for seamless updates.
                    </Text>
                  </div>
                </Stack>
              </Paper>

              {/* Additional Resources */}
              <Paper p="xl" radius="md" withBorder style={{
                background: 'linear-gradient(135deg, rgba(6, 147, 227, 0.05) 0%, rgba(155, 81, 224, 0.05) 100%)'
              }}>
                <Group mb="md">
                  <ThemeIcon size="lg" variant="gradient" gradient={{ from: 'blue', to: 'violet' }}>
                    <IconBook size={20} />
                  </ThemeIcon>
                  <Text size="lg" fw={600}>
                    Additional Resources
                  </Text>
                </Group>

                <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
                  <Button
                    variant="light"
                    color="blue"
                    fullWidth
                    leftSection={<IconBook size={16} />}
                    component="a"
                    href="https://create.roblox.com/docs"
                    target="_blank"
                  >
                    Roblox Creator Documentation
                  </Button>
                  <Button
                    variant="light"
                    color="violet"
                    fullWidth
                    leftSection={<IconCode size={16} />}
                    component="a"
                    href="https://create.roblox.com/docs/scripting"
                    target="_blank"
                  >
                    Lua Scripting Guide
                  </Button>
                  <Button
                    variant="light"
                    color="grape"
                    fullWidth
                    leftSection={<IconWorld size={16} />}
                    component="a"
                    href="https://devforum.roblox.com"
                    target="_blank"
                  >
                    Roblox Developer Forum
                  </Button>
                  <Button
                    variant="light"
                    color="teal"
                    fullWidth
                    leftSection={<IconRocket size={16} />}
                    onClick={() => setActiveTab('create')}
                  >
                    Start Creating
                  </Button>
                </SimpleGrid>

                <Text size="xs" c="dimmed" mt="lg" style={{ textAlign: 'center' }}>
                  Need help? Contact our support team at support@toolboxai.com
                </Text>
              </Paper>
            </Stack>
          </Box>
        </TabsPanel>
      </Tabs>
    </Box>
  );
};

export default RobloxStudioIntegration;
