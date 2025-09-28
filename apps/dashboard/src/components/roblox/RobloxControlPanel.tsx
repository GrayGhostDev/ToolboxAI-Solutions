/**
 * Roblox Control Panel Component (Mantine v8)
 * Main control interface for teachers to manage Roblox educational content
 * Updated to use Mantine v8 components instead of MUI
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  Group,
  Button,
  Text,
  Title,
  Badge,
  ActionIcon,
  TextInput,
  Select,
  Alert,
  Loader,
  Tooltip,
  Divider,
  Switch,
  Paper,
  Stack,
  Modal,
  Stepper,
  Progress,
  Tabs,
  ScrollArea,
  Code,
  SimpleGrid,
  Indicator,
  Notification
} from '@mantine/core';
import {
  IconDeviceGamepad2 as GameIcon,
  IconRobot as AIIcon,
  IconUsers as GroupIcon,
  IconCode as CodeIcon,
  IconPlayerPlay as PlayIcon,
  IconPlayerPause as PauseIcon,
  IconPlayerStop as StopIcon,
  IconRefresh as RefreshIcon,
  IconSettings as SettingsIcon,
  IconDownload as DownloadIcon,
  IconUpload as UploadIcon,
  IconCheck as CheckIcon,
  IconX as CloseIcon,
  IconAlertCircle as WarningIcon,
  IconBulb as LightbulbIcon,
  IconChevronDown as ExpandMoreIcon,
  IconChevronUp as ExpandLessIcon,
  IconWifi as WifiIcon,
  IconWifiOff as WifiOffIcon,
  IconCircle as FiberManualRecord
} from '@tabler/icons-react';
import { usePusher } from '../../hooks/usePusher';
import { useAppDispatch } from '../../store';
import { WebSocketMessageType, ContentGenerationRequest } from '../../types/websocket';

interface RobloxControlPanelProps {
  className?: string;
}

interface PluginStatus {
  connected: boolean;
  version: string;
  lastHeartbeat: number;
  studioVersion?: string;
  capabilities: string[];
}

interface ActiveSession {
  id: string;
  userId: string;
  userName: string;
  worldId: string;
  worldName: string;
  startTime: number;
  status: 'active' | 'paused' | 'completed';
  progress: {
    currentObjective: string;
    completedObjectives: number;
    totalObjectives: number;
    xpEarned: number;
  };
}

interface ContentGenerationTask {
  id: string;
  type: 'lesson' | 'quiz' | 'environment' | 'script';
  status: 'pending' | 'generating' | 'completed' | 'failed';
  progress: number;
  description: string;
  result?: any;
  error?: string;
  createdAt: number;
}

// Sample data for demonstration
const sampleSessions: ActiveSession[] = [
  {
    id: 'session_1',
    userId: 'user_123',
    userName: 'Alice Johnson',
    worldId: 'world_math_001',
    worldName: 'Algebra Adventure',
    startTime: Date.now() - 1200000, // 20 minutes ago
    status: 'active',
    progress: {
      currentObjective: 'Solve linear equations',
      completedObjectives: 3,
      totalObjectives: 8,
      xpEarned: 150
    }
  },
  {
    id: 'session_2',
    userId: 'user_456',
    userName: 'Bob Smith',
    worldId: 'world_science_002',
    worldName: 'Chemistry Lab',
    startTime: Date.now() - 600000, // 10 minutes ago
    status: 'active',
    progress: {
      currentObjective: 'Mix chemical compounds',
      completedObjectives: 2,
      totalObjectives: 5,
      xpEarned: 100
    }
  }
];

export const RobloxControlPanel: React.FunctionComponent<RobloxControlPanelProps> = ({ className }) => {
  const dispatch = useAppDispatch();
  const { send: sendMessage, isConnected, state: wsState } = usePusher();

  // Local state
  const [pluginStatus, setPluginStatus] = useState<PluginStatus>({
    connected: false,
    version: '1.0.0',
    lastHeartbeat: 0,
    capabilities: ['content-generation', 'world-sync', 'student-tracking']
  });

  const [activeSessions, setActiveSessions] = useState<ActiveSession[]>(sampleSessions);
  const [contentTasks, setContentTasks] = useState<ContentGenerationTask[]>([]);
  const [selectedTab, setSelectedTab] = useState<string>('overview');

  // Content generation form state
  const [contentForm, setContentForm] = useState({
    type: 'lesson' as 'lesson' | 'quiz' | 'environment' | 'script',
    subject: 'Mathematics',
    grade: 8,
    topic: '',
    difficulty: 'medium' as 'easy' | 'medium' | 'hard',
    description: ''
  });

  const [showGenerationDialog, setShowGenerationDialog] = useState(false);
  const [generationStep, setGenerationStep] = useState(0);

  // Plugin management
  const connectToPlugin = async () => {
    try {
      await sendMessage(WebSocketMessageType.ROBLOX_UPDATE, {
        action: 'connect_plugin',
        timestamp: Date.now()
      }, { channel: 'roblox-updates' });

      setPluginStatus(prev => ({ ...prev, connected: true, lastHeartbeat: Date.now() }));
        } catch (error) {
      console.error('Failed to connect to Roblox Studio plugin:', error);
    }
  };

  const disconnectFromPlugin = async () => {
    try {
      await sendMessage(WebSocketMessageType.ROBLOX_UPDATE, {
        action: 'disconnect_plugin',
        timestamp: Date.now()
      }, { channel: 'roblox-updates' });

      setPluginStatus(prev => ({ ...prev, connected: false }));
    } catch (error) {
      console.error('Failed to disconnect from Roblox Studio plugin:', error);
    }
  };

  // Content generation
  const generateContent = async () => {
    if (!contentForm.topic.trim()) {
      alert('Please enter a topic for content generation');
      return;
    }

    const task: ContentGenerationTask = {
      id: `task_${Date.now()}`,
      type: contentForm.type,
      status: 'pending',
      progress: 0,
      description: `${contentForm.type} - ${contentForm.topic}`,
      createdAt: Date.now()
    };

    setContentTasks(prev => [task, ...prev]);
    setShowGenerationDialog(false);

    const request: ContentGenerationRequest = {
      type: contentForm.type,
      subject: contentForm.subject,
      grade: contentForm.grade,
      topic: contentForm.topic,
      difficulty: contentForm.difficulty,
      customInstructions: contentForm.description
    };

    try {
      await sendMessage(WebSocketMessageType.CONTENT_UPDATE, request, {
        channel: 'content-generation'
      });
    } catch (error) {
      console.error('Failed to send content generation request:', error);
      setContentTasks(prev => prev.map(t =>
        t.id === task.id ? { ...t, status: 'failed', error: 'Failed to send request' } : t
      ));
    }
  };

  return (
    <Box className={className} p="xl">
      <Stack gap="lg">
        {/* Header */}
        <Group justify="space-between" align="center">
          <Title order={2}>Roblox Control Panel</Title>
          <Group gap="sm">
            <Badge
              color={isConnected ? 'green' : 'red'}
              variant="filled"
              leftSection={isConnected ? <WifiIcon size={14} /> : <WifiOffIcon size={14} />}
            >
              {isConnected ? 'Connected' : 'Disconnected'}
            </Badge>
            <Badge
              color={pluginStatus.connected ? 'blue' : 'gray'}
              variant="outline"
            >
              Plugin: {pluginStatus.connected ? 'Connected' : 'Disconnected'}
            </Badge>
          </Group>
        </Group>

        {/* Connection Alert */}
        {!isConnected && (
          <Alert color="orange" icon={<WarningIcon size={16} />} title="Connection Required">
            <Text size="sm">
              Pusher connection is required for real-time Roblox integration.
              Please check your connection and try again.
            </Text>
          </Alert>
        )}

        <Tabs value={selectedTab} onChange={setSelectedTab}>
          <Tabs.List>
            <Tabs.Tab value="overview">Overview</Tabs.Tab>
            <Tabs.Tab value="plugin">Studio Plugin</Tabs.Tab>
            <Tabs.Tab value="content">Content Generation</Tabs.Tab>
            <Tabs.Tab value="sessions">Active Sessions</Tabs.Tab>
          </Tabs.List>

          {/* Overview Tab */}
          <Tabs.Panel value="overview">
            <Stack gap="md" mt="md">
              <SimpleGrid cols={3} spacing="md">
                <Card withBorder>
                  <Stack gap="sm" align="center">
                    <GameIcon size={32} color="var(--mantine-color-blue-6)" />
                    <Text fw={600}>Studio Plugin</Text>
                    <Badge color={pluginStatus.connected ? 'green' : 'red'}>
                      {pluginStatus.connected ? 'Connected' : 'Disconnected'}
                    </Badge>
                    <Text size="xs" c="dimmed">v{pluginStatus.version}</Text>
                  </Stack>
                </Card>

                <Card withBorder>
                  <Stack gap="sm" align="center">
                    <GroupIcon size={32} color="var(--mantine-color-green-6)" />
                    <Text fw={600}>Active Sessions</Text>
                    <Text size="xl" fw={700}>{activeSessions.length}</Text>
                    <Text size="xs" c="dimmed">Students online</Text>
                  </Stack>
                </Card>

                <Card withBorder>
                  <Stack gap="sm" align="center">
                    <AIIcon size={32} color="var(--mantine-color-purple-6)" />
                    <Text fw={600}>Content Tasks</Text>
                    <Text size="xl" fw={700}>{contentTasks.length}</Text>
                    <Text size="xs" c="dimmed">Generation queue</Text>
                  </Stack>
                </Card>
              </SimpleGrid>
            </Stack>
          </Tabs.Panel>

          {/* Plugin Tab */}
          <Tabs.Panel value="plugin">
            <Stack gap="md" mt="md">
              <Card withBorder>
                <Card.Section p="md" withBorder>
                  <Group justify="space-between">
                    <Group gap="sm">
                      <GameIcon size={24} color="var(--mantine-color-blue-6)" />
                      <Title order={4}>Roblox Studio Plugin</Title>
                    </Group>
                    <Badge color={pluginStatus.connected ? 'green' : 'red'}>
                      {pluginStatus.connected ? 'Connected' : 'Disconnected'}
                    </Badge>
                  </Group>
                </Card.Section>

                <Stack gap="md" p="md">
                  <Group justify="space-between">
                    <Text>Plugin Version:</Text>
                    <Code>{pluginStatus.version}</Code>
                  </Group>

                  {pluginStatus.connected && (
                    <Group justify="space-between">
                      <Text>Last Heartbeat:</Text>
                      <Text size="sm" c="dimmed">
                        {new Date(pluginStatus.lastHeartbeat).toLocaleTimeString()}
                      </Text>
                    </Group>
                  )}

                  <Divider />

                  <Group>
                    {pluginStatus.connected ? (
                      <Button
                        color="red"
                        variant="outline"
                        leftSection={<CloseIcon size={16} />}
                        onClick={disconnectFromPlugin}
                      >
                        Disconnect Plugin
                      </Button>
                    ) : (
                      <Button
                        color="blue"
                        leftSection={<CheckIcon size={16} />}
                        onClick={connectToPlugin}
                        disabled={!isConnected}
                      >
                        Connect Plugin
                      </Button>
                    )}

                    <Button
                      variant="outline"
                      leftSection={<RefreshIcon size={16} />}
                      onClick={() => {/* Refresh plugin status */}}
                    >
                      Refresh Status
                    </Button>
                  </Group>

                  {pluginStatus.capabilities.length > 0 && (
                    <>
                      <Divider />
                      <Stack gap="xs">
                        <Text fw={500}>Plugin Capabilities:</Text>
                        <Group gap="xs">
                          {pluginStatus.capabilities.map((capability) => (
                            <Badge key={capability} variant="outline" size="sm">
                              {capability}
                            </Badge>
                          ))}
                        </Group>
                      </Stack>
                    </>
                  )}
                </Stack>
              </Card>
            </Stack>
          </Tabs.Panel>

          {/* Content Generation Tab */}
          <Tabs.Panel value="content">
            <Stack gap="md" mt="md">
              <Group justify="space-between">
                <Title order={4}>Content Generation</Title>
                <Button
                  leftSection={<AIIcon size={16} />}
                  onClick={() => setShowGenerationDialog(true)}
                  disabled={!isConnected}
                >
                  Generate Content
                </Button>
              </Group>

              {/* Active Tasks */}
              <Card withBorder>
                <Card.Section p="md" withBorder>
                  <Title order={5}>Generation Queue</Title>
                </Card.Section>

                <Stack gap="sm" p="md">
                  {contentTasks.length === 0 ? (
                    <Text c="dimmed" ta="center" py="xl">
                      No content generation tasks
                    </Text>
                  ) : (
                    contentTasks.map((task) => (
                      <Paper key={task.id} p="md" withBorder>
                        <Group justify="space-between" align="flex-start">
                          <Stack gap="xs" style={{ flex: 1 }}>
                            <Group gap="sm">
                              <Badge variant="outline">{task.type}</Badge>
                              <Badge
                                color={
                                  task.status === 'completed' ? 'green' :
                                  task.status === 'failed' ? 'red' :
                                  task.status === 'generating' ? 'blue' : 'gray'
                                }
                              >
                                {task.status}
                              </Badge>
                            </Group>
                            <Text size="sm" fw={500}>{task.description}</Text>
                            {task.status === 'generating' && (
                              <Progress value={task.progress} size="sm" />
                            )}
                            {task.error && (
                              <Text size="xs" c="red">{task.error}</Text>
                            )}
                          </Stack>
                          <Text size="xs" c="dimmed">
                            {new Date(task.createdAt).toLocaleTimeString()}
                          </Text>
                        </Group>
                      </Paper>
                    ))
                  )}
                </Stack>
          </Card>
            </Stack>
          </Tabs.Panel>

          {/* Sessions Tab */}
          <Tabs.Panel value="sessions">
            <Stack gap="md" mt="md">
              <Group justify="space-between">
                <Title order={4}>Active Sessions</Title>
                <Badge variant="outline">{activeSessions.length} active</Badge>
              </Group>

              <Card withBorder>
                <Stack gap="sm" p="md">
              {activeSessions.length === 0 ? (
                    <Text c="dimmed" ta="center" py="xl">
                      No active sessions
                    </Text>
                  ) : (
                    activeSessions.map((session) => (
                      <Paper key={session.id} p="md" withBorder>
                        <Group justify="space-between" align="flex-start">
                          <Stack gap="xs" style={{ flex: 1 }}>
                            <Group gap="sm">
                              <Text fw={500}>{session.userName}</Text>
                              <Badge color="blue" size="sm">{session.worldName}</Badge>
                              <Badge
                                color={session.status === 'active' ? 'green' : 'orange'}
                                size="sm"
                              >
                                {session.status}
                              </Badge>
                            </Group>

                            <Text size="sm" c="dimmed">
                              {session.progress.currentObjective}
                            </Text>

                            <Progress
                              value={(session.progress.completedObjectives / session.progress.totalObjectives) * 100}
                              size="sm"
                              label={`${session.progress.completedObjectives}/${session.progress.totalObjectives} objectives`}
                            />

                            <Group gap="md">
                              <Text size="xs" c="dimmed">
                                XP Earned: {session.progress.xpEarned}
                              </Text>
                              <Text size="xs" c="dimmed">
                                Started: {new Date(session.startTime).toLocaleTimeString()}
                              </Text>
                            </Group>
                          </Stack>

                          <Group gap="xs">
                            <ActionIcon variant="outline" size="sm">
                              <PauseIcon size={14} />
                            </ActionIcon>
                            <ActionIcon variant="outline" size="sm" color="red">
                              <StopIcon size={14} />
                            </ActionIcon>
                          </Group>
                        </Group>
                      </Paper>
                    ))
                  )}
                </Stack>
          </Card>
            </Stack>
          </Tabs.Panel>
        </Tabs>

        {/* Content Generation Dialog */}
        <Modal
          opened={showGenerationDialog}
          onClose={() => setShowGenerationDialog(false)}
          title="Generate Educational Content"
          size="lg"
        >
          <Stack gap="md">
            <Stepper active={generationStep} onStepClick={setGenerationStep}>
              <Stepper.Step label="Content Type" description="Choose what to generate">
                <Stack gap="md" mt="md">
                  <Select
                    label="Content Type"
                    value={contentForm.type}
                    onChange={(value) => value && setContentForm(prev => ({ ...prev, type: value as any }))}
                    data={[
                      { value: 'lesson', label: 'Interactive Lesson' },
                      { value: 'quiz', label: 'Quiz/Assessment' },
                      { value: 'environment', label: 'Virtual Environment' },
                      { value: 'script', label: 'Lua Script' }
                    ]}
                  />

                  <Group grow>
                    <Select
                          label="Subject"
                          value={contentForm.subject}
                      onChange={(value) => value && setContentForm(prev => ({ ...prev, subject: value }))}
                      data={[
                        'Mathematics',
                        'Science',
                        'History',
                        'English',
                        'Computer Science'
                      ]}
                    />

                    <Select
                          label="Grade Level"
                      value={contentForm.grade.toString()}
                      onChange={(value) => value && setContentForm(prev => ({ ...prev, grade: parseInt(value) }))}
                      data={Array.from({ length: 12 }, (_, i) => ({
                        value: (i + 1).toString(),
                        label: `Grade ${i + 1}`
                      }))}
                    />
                  </Group>
                </Stack>
              </Stepper.Step>

              <Stepper.Step label="Details" description="Specify content details">
                <Stack gap="md" mt="md">
                  <TextInput
                    label="Topic"
                    value={contentForm.topic}
                    onChange={(e) => setContentForm(prev => ({ ...prev, topic: e.target.value }))}
                    placeholder="e.g., Linear Equations, Photosynthesis, etc."
                    required
                  />

                      <Select
                    label="Difficulty"
                    value={contentForm.difficulty}
                    onChange={(value) => value && setContentForm(prev => ({ ...prev, difficulty: value as any }))}
                    data={[
                      { value: 'easy', label: 'Easy' },
                      { value: 'medium', label: 'Medium' },
                      { value: 'hard', label: 'Hard' }
                    ]}
                  />

                  <TextInput
                    label="Custom Instructions"
                    value={contentForm.description}
                    onChange={(e) => setContentForm(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Any specific requirements or instructions..."
                    multiline
                    rows={3}
                  />
                </Stack>
              </Stepper.Step>

              <Stepper.Step label="Generate" description="Create the content">
                <Stack gap="md" mt="md">
                  <Alert color="blue" icon={<LightbulbIcon size={16} />}>
                    <Text size="sm">
                      Ready to generate {contentForm.type} content for {contentForm.topic}
                      (Grade {contentForm.grade} {contentForm.subject})
                    </Text>
                  </Alert>

                  <Group>
                    <Button
                      leftSection={<AIIcon size={16} />}
                      onClick={generateContent}
                      disabled={!contentForm.topic.trim() || !isConnected}
                    >
                      Generate Content
                    </Button>
                    <Button variant="outline" onClick={() => setShowGenerationDialog(false)}>
                      Cancel
                    </Button>
                  </Group>
                </Stack>
              </Stepper.Step>
          </Stepper>
          </Stack>
        </Modal>
      </Stack>
    </Box>
  );
};
