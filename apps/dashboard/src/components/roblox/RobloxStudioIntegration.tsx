/**
 * RobloxStudioIntegration Component
 *
 * Main integration component that combines the AI chat interface with
 * Roblox Studio plugin communication and environment management.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Box, Grid, Paper, Text, Button, Alert, Badge, Stack, Card, ActionIcon, Tooltip, Progress, Divider, Group, useMantineTheme } from '@mantine/core';
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
  IconAlertTriangle
} from '@tabler/icons-react';

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
  }, []);

  // Periodic plugin status check
  useEffect(() => {
    const interval = setInterval(checkPluginStatus, 30000);
    return () => clearInterval(interval);
  }, [checkPluginStatus]);

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

      // Show success message
      setError(null);
    } catch (err) {
      console.error('Failed to deploy to Studio:', err);
      setError('Failed to deploy environment to Roblox Studio. Please try again.');
    }
  }, [pluginStatus.connected]);

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
        // Fallback to clipboard
        navigator.clipboard?.writeText(environment.previewUrl);
      }
    } else if (environment.previewUrl) {
      // Fallback to clipboard
      navigator.clipboard?.writeText(environment.previewUrl);
      // Could show a toast notification here
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

  return (
    <Box style={{
      height: '100%',
      width: '100%',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <Paper shadow="xs" style={{
        padding: theme.spacing.md,
        marginBottom: theme.spacing.md,
        backgroundColor: theme.colors.gray[0]
      }}>
        <Group position="apart" align="center">
          <div>
            <Text size="xl" weight={700} mb="xs">
              Roblox Studio Integration
            </Text>
            <Text size="sm" color="dimmed">
              Create, manage, and deploy educational Roblox environments
            </Text>
          </div>

          {/* Plugin Status */}
          <Group spacing={theme.spacing.md}>
            <Badge
              leftSection={pluginStatus.connected ? <IconCircleCheck size={14} /> : <IconExclamationMark size={14} />}
              color={pluginStatus.connected ? 'green' : 'red'}
              variant="outline"
            >
              {pluginStatus.connected ? 'Plugin Connected' : 'Plugin Disconnected'}
            </Badge>

            <Button
              variant="outline"
              onClick={checkPluginStatus}
              disabled={isCheckingPlugin}
              leftIcon={<IconRefresh />}
            >
              {isCheckingPlugin ? 'Checking...' : 'Refresh'}
            </Button>

            {!pluginStatus.connected && (
              <Button
                onClick={installPlugin}
                leftIcon={<IconCloudUpload />}
              >
                Install Plugin
              </Button>
            )}
          </Group>
        </Group>

        {/* Plugin Status Details */}
        {pluginStatus.connected && pluginStatus.version && (
          <Box mt="xs">
            <Text size="xs" color="dimmed">
              Plugin Version: {pluginStatus.version}
              {pluginStatus.studioVersion && ` | Studio Version: ${pluginStatus.studioVersion}`}
            </Text>
          </Box>
        )}
      </Paper>

      {/* Error Alert */}
      {error && (
        <Alert
          color="red"
          onClose={() => setError(null)}
          style={{ marginBottom: theme.spacing.md }}
          withCloseButton
        >
          {error}
        </Alert>
      )}

      {/* Main Content */}
      <Grid style={{
        flex: 1,
        overflow: 'hidden',
        height: '100%'
      }}>
        {/* AI Chat Interface */}
        <Grid.Col span={12} md={6}>
          <Paper shadow="sm" style={{
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
          }}>
            <RobloxAIChat />
          </Paper>
        </Grid.Col>

        {/* Environment Management */}
        <Grid.Col span={12} md={6}>
          <Paper shadow="sm" style={{
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
          }}>
            <Box style={{ padding: theme.spacing.md, borderBottom: `1px solid ${theme.colors.gray[3]}` }}>
              <Text size="lg" weight={600}>Generated Environments</Text>
              <Text size="sm" color="dimmed">
                Manage and deploy your AI-generated Roblox worlds
              </Text>
            </Box>

            <Box style={{ flex: 1, overflow: 'auto', padding: theme.spacing.md }}>
              {environments.length === 0 ? (
                <Box style={{ textAlign: 'center', padding: theme.spacing.xl }}>
                  <Text size="lg" color="dimmed" mb="xs">
                    No environments generated yet
                  </Text>
                  <Text size="sm" color="dimmed">
                    Use the AI chat to create your first Roblox environment
                  </Text>
                </Box>
              ) : (
                <Stack spacing={theme.spacing.md}>
                  {environments.map((environment) => (
                    <Card
                      key={environment.id}
                      withBorder
                      style={{
                        cursor: 'pointer',
                        borderColor: selectedEnvironment === environment.id
                          ? theme.colors.blue[4]
                          : theme.colors.gray[3],
                        borderWidth: selectedEnvironment === environment.id ? 2 : 1,
                      }}
                      onClick={() => setSelectedEnvironment(environment.id)}
                    >
                      <Card.Section withBorder inheritPadding py="xs">
                        <Group position="apart" align="center">
                          <Text weight={600} style={{ flex: 1 }} truncate>
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
                              environment.status === 'error' ? <IconExclamationMark size={12} /> : <IconAlertTriangle size={12} />
                            }
                          >
                            {environment.status}
                          </Badge>
                        </Group>
                      </Card.Section>

                      {environment.metadata && (
                        <Box mb="md">
                          <Text size="sm" color="dimmed" mb="xs">
                            Theme: {environment.metadata.theme} | Type: {environment.metadata.mapType}
                          </Text>
                          {environment.metadata.learningObjectives.length > 0 && (
                            <Text size="sm" color="dimmed">
                              Objectives: {environment.metadata.learningObjectives.join(', ')}
                            </Text>
                          )}
                        </Box>
                      )}

                      {environment.status === 'generating' && environment.progress !== undefined && (
                        <Box mb="md">
                          <Progress
                            value={environment.progress}
                            mb="xs"
                          />
                          <Text size="xs" color="dimmed">
                            Generating... {environment.progress}%
                          </Text>
                        </Box>
                      )}

                      {environment.status === 'error' && environment.error && (
                        <Alert color="red" mb="md">
                          {environment.error}
                        </Alert>
                      )}

                      {environment.status === 'ready' && (
                        <Card.Section inheritPadding py="xs">
                          <Group spacing={theme.spacing.xs}>
                            <Button
                              size="xs"
                              leftIcon={<IconPlayerPlay />}
                              onClick={(e) => {
                                e.stopPropagation();
                                deployToStudio(environment.id);
                              }}
                              disabled={!pluginStatus.connected}
                            >
                              Deploy to Studio
                            </Button>

                            <Button
                              size="xs"
                              variant="outline"
                              leftIcon={<IconDownload />}
                              onClick={(e) => {
                                e.stopPropagation();
                                downloadEnvironment(environment.id);
                              }}
                            >
                              Download
                            </Button>

                            {environment.previewUrl && (
                              <Button
                                size="xs"
                                variant="outline"
                                leftIcon={<IconEye />}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  window.open(environment.previewUrl, '_blank');
                                }}
                              >
                                Preview
                              </Button>
                            )}

                            <Tooltip label="Share">
                              <ActionIcon
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  shareEnvironment(environment);
                                }}
                              >
                                <IconShare />
                              </ActionIcon>
                            </Tooltip>
                          </Group>
                        </Card.Section>
                      )}
                    </Card>
                  ))}
                </Stack>
              )}
            </Box>
          </Paper>
        </Grid.Col>
      </Grid>
    </Box>
  );
};

export default RobloxStudioIntegration;