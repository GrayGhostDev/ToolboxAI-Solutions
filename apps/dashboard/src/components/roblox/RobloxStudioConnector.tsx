import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Text,
  Button,
  Alert,
  Card,
  Grid,
  List,
  Chip,
  ActionIcon,
  Modal,
  Stepper,
  Loader,
  Tooltip,
  TextInput,
  Switch,
  Group,
  Stack,
  Title,
  Badge
} from '@mantine/core';
import {
  IconCloudUpload,
  IconCloudDownload,
  IconPlayerPlay,
  IconPlayerStop,
  IconRefresh,
  IconSettings,
  IconLink,
  IconLinkOff,
  IconShield,
  IconCircleCheck,
  IconExclamationMark,
  IconAlertTriangle,
  IconInfoCircle,
  IconCopy,
  IconExternalLink,
  IconTool,
  IconTrash
} from '@tabler/icons-react';
import { useSelector } from 'react-redux';
import { type RootState } from '../../store';
import api from '../../services/api';
import pusher from '../../services/pusher';

interface RojoProject {
  project_id: string;
  name: string;
  path: string;
  port: number;
  status: 'stopped' | 'starting' | 'running' | 'error';
  created_at: string;
  updated_at: string;
  user_id: string;
}

interface RojoSyncStatus {
  connected: boolean;
  session_id?: string;
  project_name?: string;
  client_count: number;
  last_sync?: string;
  errors: string[];
}

interface OAuthStatus {
  authenticated: boolean;
  roblox_user_id?: string;
  username?: string;
  expires_at?: string;
}

const RobloxStudioConnector: React.FunctionComponent<Record<string, any>> = () => {
  const [projects, setProjects] = useState<RojoProject[]>([]);
  const [selectedProject, setSelectedProject] = useState<RojoProject | null>(null);
  const [syncStatus, setSyncStatus] = useState<RojoSyncStatus | null>(null);
  const [oauthStatus, setOAuthStatus] = useState<OAuthStatus>({ authenticated: false });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rojoInstalled, setRojoInstalled] = useState<boolean | null>(null);
  const [authDialogOpen, setAuthDialogOpen] = useState(false);
  const [connectionDialogOpen, setConnectionDialogOpen] = useState(false);
  const [autoSync, setAutoSync] = useState(true);

  // Fix: Changed from state.auth.user to state.user as auth slice doesn't exist
  // Defensive: Safe fallback for Redux state access
  const user = useSelector((state: RootState) => state?.user || null);

  // Check Rojo installation
  const checkRojoInstallation = useCallback(async () => {
    try {
      const response = await api.get('/api/v1/roblox/rojo/check');
      setRojoInstalled(response.data.rojo_installed);
    } catch (err) {
      setRojoInstalled(false);
    }
  }, []);

  // Load user's Rojo projects
  const loadProjects = useCallback(async () => {
    setLoading(true);
    setError(null); // Defensive: Clear previous errors
    try {
      const response = await api.get('/api/v1/roblox/rojo/projects');
      // Defensive: Safe array access with fallback
      const projectsData = response?.data?.projects;
      setProjects(Array.isArray(projectsData) ? projectsData : []);
    } catch (err: any) {
      const errorMessage = err?.response?.data?.message || err?.message || 'Failed to load projects';
      setError(errorMessage);
      // Defensive: Keep existing projects on error rather than clearing
      console.error('Error loading projects:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Check OAuth status
  const checkOAuthStatus = useCallback(async () => {
    try {
      // This would check if user has valid Roblox OAuth tokens
      // For now, we'll mock this
      const hasToken = localStorage.getItem('roblox_auth_token');
      if (hasToken) {
        setOAuthStatus({
          authenticated: true,
          roblox_user_id: 'mock_user_id',
          username: 'RobloxUser'
        });
      }
    } catch (err) {
      setOAuthStatus({ authenticated: false });
    }
  }, []);

  // Initiate OAuth2 flow
  const initiateOAuth = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/api/v1/roblox/auth/initiate', {
        additional_scopes: ['universe-messaging-service:publish']
      });

      if (response.data.success) {
        // Open OAuth window
        const authWindow = window.open(
          response.data.authorization_url,
          'roblox-auth',
          'width=600,height=800'
        );

        // Listen for OAuth completion
        const checkAuth = setInterval(() => {
          if (authWindow?.closed) {
            clearInterval(checkAuth);
            checkOAuthStatus();
            setAuthDialogOpen(false);
          }
        }, 1000);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to initiate authentication');
    } finally {
      setLoading(false);
    }
  };

  // Start Rojo server for project
  const startProject = async (projectId: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post(`/api/v1/roblox/rojo/project/${projectId}/start`);

      if (response.data.success) {
        setSyncStatus(response.data.sync_status);

        // Update project status
        setProjects(prev => prev.map(p =>
          p.project_id === projectId ? { ...p, status: 'running' } : p
        ));

        // Show connection instructions
        if (response.data.sync_status.connected) {
          setConnectionDialogOpen(true);
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start project');
    } finally {
      setLoading(false);
    }
  };

  // Stop Rojo server for project
  const stopProject = async (projectId: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post(`/api/v1/roblox/rojo/project/${projectId}/stop`);

      if (response.data.success) {
        setSyncStatus(null);

        // Update project status
        setProjects(prev => prev.map(p =>
          p.project_id === projectId ? { ...p, status: 'stopped' } : p
        ));
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to stop project');
    } finally {
      setLoading(false);
    }
  };

  // Build project to .rbxl file
  const buildProject = async (projectId: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post(`/api/v1/roblox/rojo/project/${projectId}/build`);

      if (response.data.success) {
        // Download the built file
        const link = document.createElement('a');
        link.href = response.data.output_path;
        link.download = `${selectedProject?.name || 'project'}.rbxl`;
        link.click();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to build project');
    } finally {
      setLoading(false);
    }
  };

  // Delete project
  const deleteProject = async (projectId: string) => {
    if (!confirm('Are you sure you want to delete this project?')) return;

    setLoading(true);
    setError(null);

    try {
      const response = await api.delete(`/api/v1/roblox/rojo/project/${projectId}`);

      if (response.data.success) {
        setProjects(prev => prev.filter(p => p.project_id !== projectId));
        setSelectedProject(null);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete project');
    } finally {
      setLoading(false);
    }
  };

  // Check sync status periodically
  useEffect(() => {
    // Defensive: Validate selectedProject before setting up interval
    if (selectedProject?.status === 'running' && selectedProject?.project_id && autoSync) {
      const interval = setInterval(async () => {
        try {
          const response = await api.get(`/api/v1/roblox/rojo/project/${selectedProject.project_id}`);
          // Defensive: Validate response data before updating state
          if (response?.data?.sync_status) {
            setSyncStatus(response.data.sync_status);
          }
        } catch (err) {
          // Defensive: Log errors but don't disrupt UI
          console.warn('Background sync status check failed:', err);
        }
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [selectedProject, autoSync]);

  // Initialize on mount
  useEffect(() => {
    checkRojoInstallation();
    checkOAuthStatus();
    loadProjects();
  }, [checkRojoInstallation, checkOAuthStatus, loadProjects]);

  // Copy to clipboard helper
  const copyToClipboard = async (text: string) => {
    try {
      // Defensive: Check if clipboard API is available
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
      }
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  return (
    <Box style={{ width: '100%', padding: '24px' }}>
      <Title order={2} mb="lg">
        Roblox Studio Connector
      </Title>

      {/* Status Cards */}
      <Grid gutter="md" mb="lg">
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card>
            <Group align="center" mb="sm">
              <IconSettings size={16} />
              <Text size="lg" fw={600}>Rojo Status</Text>
            </Group>
            {rojoInstalled === null ? (
              <Loader size={20} />
            ) : rojoInstalled ? (
              <Chip
                leftSection={<IconCircleCheck size={16} />}
                color="green"
                size="sm"
              >
                Installed
              </Chip>
            ) : (
              <Chip
                leftSection={<IconAlertTriangle size={16} />}
                color="red"
                size="sm"
              >
                Not Installed
              </Chip>
            )}
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card>
            <Group align="center" mb="sm">
              <IconShield size={16} />
              <Text size="lg" fw={600}>Authentication</Text>
            </Group>
            {oauthStatus.authenticated ? (
              <Box>
                <Chip
                  leftSection={<IconCircleCheck size={16} />}
                  color="green"
                  size="sm"
                >
                  Connected as {oauthStatus.username}
                </Chip>
              </Box>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAuthDialogOpen(true)}
                leftSection={<IconLink size={16} />}
              >
                Connect Roblox
              </Button>
            )}
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card>
            <Group align="center" mb="sm">
              {syncStatus?.connected ? <IconLink size={16} /> : <IconLinkOff size={16} />}
              <Text size="lg" fw={600}>Sync Status</Text>
            </Group>
            {syncStatus ? (
              <Box>
                <Chip
                  leftSection={syncStatus.connected ? <IconCircleCheck size={16} /> : <IconExclamationMark size={16} />}
                  color={syncStatus.connected ? 'green' : 'gray'}
                  size="sm"
                >
                  {syncStatus.connected ? 'Connected' : 'Disconnected'}
                </Chip>
                {syncStatus.client_count > 0 && (
                  <Text size="xs" c="dimmed" ml="sm">
                    {syncStatus.client_count} client(s)
                  </Text>
                )}
              </Box>
            ) : (
              <Text size="sm" c="dimmed">
                No active sync
              </Text>
            )}
          </Card>
        </Grid.Col>
      </Grid>

      {/* Project List */}
      <Paper p="lg" shadow="md">
        <Group justify="space-between" align="center" mb="md">
          <Text size="lg" fw={600}>Your Projects</Text>
          <Group align="center">
            <Text size="sm">Auto-sync</Text>
            <Switch checked={autoSync} onChange={(event) => setAutoSync(event.currentTarget.checked)} />
          </Group>
        </Group>

        {loading && (!projects || projects.length === 0) ? (
          <Group justify="center" p="lg">
            <Loader />
          </Group>
        ) : (!projects || projects.length === 0) ? (
          <Alert color="blue">
            No projects found. Create one from the Conversation Flow.
          </Alert>
        ) : (
          <Grid gutter="md">
            {/* Defensive: Safe array mapping with validation */}
            {Array.isArray(projects) && projects.map((project) => {
              // Defensive: Validate project object
              if (!project || !project.project_id) return null;

              return (
              <Grid.Col span={{ base: 12, md: 6, lg: 4 }} key={project.project_id}>
                <Card
                  style={{
                    cursor: 'pointer',
                    border: selectedProject?.project_id === project.project_id ? '2px solid var(--mantine-color-blue-6)' : 'none'
                  }}
                  onClick={() => setSelectedProject(project)}
                >
                  <Card.Section p="md">
                    <Text size="lg" fw={600} mb="sm">
                      {project.name || 'Unnamed Project'}
                    </Text>
                    <Stack gap="xs">
                      <Group justify="space-between">
                        <Text size="sm" c="dimmed">Port</Text>
                        <Text size="sm">{project.port || 'N/A'}</Text>
                      </Group>
                      <Group justify="space-between">
                        <Text size="sm" c="dimmed">Status</Text>
                        <Chip
                          color={
                            project.status === 'running' ? 'green' :
                            project.status === 'error' ? 'red' : 'gray'
                          }
                          size="sm"
                        >
                          {project.status || 'unknown'}
                        </Chip>
                      </Group>
                      <Group justify="space-between">
                        <Text size="sm" c="dimmed">Created</Text>
                        <Text size="sm">
                          {/* Defensive: Safe date formatting */}
                          {project.created_at ?
                            new Date(project.created_at).toLocaleString() :
                            'Unknown'
                          }
                        </Text>
                      </Group>
                    </Stack>
                  </Card.Section>
                  <Card.Section p="md" pt={0}>
                    <Group>
                      {project.status === 'stopped' ? (
                        <Button
                          size="sm"
                          leftSection={<IconPlayerPlay size={16} />}
                          onClick={(e) => {
                            e.stopPropagation();
                            startProject(project.project_id);
                          }}
                        >
                          Start
                        </Button>
                      ) : project.status === 'running' ? (
                        <Button
                          size="sm"
                          leftSection={<IconPlayerStop size={16} />}
                          onClick={(e) => {
                            e.stopPropagation();
                            stopProject(project.project_id);
                          }}
                        >
                          Stop
                        </Button>
                      ) : null}
                      <Button
                        size="sm"
                        leftSection={<IconTool size={16} />}
                        onClick={(e) => {
                          e.stopPropagation();
                          buildProject(project.project_id);
                        }}
                      >
                        Build
                      </Button>
                      <ActionIcon
                        size="sm"
                        color="red"
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteProject(project.project_id);
                        }}
                      >
                        <IconTrash size={16} />
                      </ActionIcon>
                    </Group>
                  </Card.Section>
                </Card>
              </Grid.Col>
              );
            })}
          </Grid>
        )}
      </Paper>

      {/* OAuth Dialog */}
      <Modal opened={authDialogOpen} onClose={() => setAuthDialogOpen(false)} title="Connect to Roblox" size="md">
        <Stack gap="md">
          <Text size="sm">
            To use all features, you need to authenticate with your Roblox account.
            This will allow you to:
          </Text>
          <List spacing="xs" size="sm">
            <List.Item icon={<IconCircleCheck size={16} color="var(--mantine-color-blue-6)" />}>
              Upload assets directly to Roblox
            </List.Item>
            <List.Item icon={<IconCircleCheck size={16} color="var(--mantine-color-blue-6)" />}>
              Publish places and games
            </List.Item>
            <List.Item icon={<IconCircleCheck size={16} color="var(--mantine-color-blue-6)" />}>
              Access DataStore and messaging services
            </List.Item>
          </List>
          <Alert color="blue">
            You will be redirected to Roblox to authorize the connection.
          </Alert>
          <Group justify="flex-end">
            <Button variant="outline" onClick={() => setAuthDialogOpen(false)}>Cancel</Button>
            <Button onClick={initiateOAuth} disabled={loading}>
              {loading ? <Loader size={16} /> : 'Connect'}
            </Button>
          </Group>
        </Stack>
      </Modal>

      {/* Connection Instructions Dialog */}
      <Modal opened={connectionDialogOpen} onClose={() => setConnectionDialogOpen(false)} title="Connect Roblox Studio" size="lg">
        <Stepper active={4} orientation="vertical">
          <Stepper.Step label="Open Roblox Studio">
            <Text size="sm">
              Launch Roblox Studio and open a new or existing place.
            </Text>
          </Stepper.Step>
          <Stepper.Step label="Install Rojo Plugin">
            <Text size="sm" mb="md">
              If not installed, get the Rojo plugin from the Roblox Studio marketplace.
            </Text>
            <Button
              size="sm"
              leftSection={<IconExternalLink size={16} />}
              component="a"
              href="https://www.roblox.com/library/13916111412/Rojo"
              target="_blank"
            >
              Get Rojo Plugin
            </Button>
          </Stepper.Step>
          <Stepper.Step label="Connect to Server">
            <Text size="sm" mb="md">
              In the Rojo plugin panel, click "Connect" and enter this URL:
            </Text>
            <Paper p="md" style={{ backgroundColor: 'var(--mantine-color-gray-1)' }}>
              <Group justify="space-between" align="center">
                <Text ff="monospace">
                  http://localhost:{selectedProject?.port || '34872'}
                </Text>
                <ActionIcon
                  size="sm"
                  onClick={() => copyToClipboard(`http://localhost:${selectedProject?.port || '34872'}`)}
                >
                  <IconCopy size={16} />
                </ActionIcon>
              </Group>
            </Paper>
          </Stepper.Step>
          <Stepper.Step label="Start Syncing">
            <Text size="sm">
              Once connected, Rojo will sync your educational content to Roblox Studio in real-time.
            </Text>
          </Stepper.Step>
        </Stepper>
        <Group justify="flex-end" mt="lg">
          <Button onClick={() => setConnectionDialogOpen(false)}>Close</Button>
        </Group>
      </Modal>

      {/* Error Display */}
      {error && (
        <Alert color="red" mt="md" withCloseButton onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
    </Box>
  );
};

export default RobloxStudioConnector;