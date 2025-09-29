import { Box, Button, Typography, Paper, Stack, Grid, Container, IconButton, Avatar, Card, CardContent, CardActions, List, ListItem, ListItemText, Divider, TextField, Select, MenuItem, Chip, Badge, Alert, CircularProgress, LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions, Drawer, AppBar, Toolbar, Tabs, Tab, Menu, Tooltip, Checkbox, Radio, RadioGroup, FormControl, FormControlLabel, InputLabel, Switch, Slider, Rating, Autocomplete, Skeleton, Table } from '../utils/mui-imports';
/**
 * ContentGenerationMonitor Component
 *
 * Real-time monitoring of AI content generation pipeline
 * Shows progress for each agent and overall generation status
 */
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  Text,
  Progress,
  Grid,
  Paper,
  Badge,
  ActionIcon,
  Button,
  Alert,
  Collapse,
  List,
  Tooltip,
  Stack,
  Group,
  Title,
  RingProgress,
  Loader,
  Switch
} from '@mantine/core';
import { useMantineTheme } from '@mantine/hooks';
import {
  IconPlayerPlay,
  IconPlayerPause,
  IconPlayerStop,
  IconRefresh,
  IconCircleCheck,
  IconExclamationMark,
  IconAlertTriangle,
  IconInfoCircle,
  IconCode,
  IconBrain,
  IconMountain,
  IconHelp,
  IconMovie,
  IconSettings,
  IconChevronDown,
  IconChevronUp,
  IconGauge,
  IconMemory,
  IconDatabase,
  IconClock,
  IconX,
  IconDownload,
  IconEye,
  IconEyeCheck
} from '@tabler/icons-react';
import { usePusherContext } from '../../contexts/PusherContext';
import {
  ContentGenerationProgress,
  WebSocketMessageType,
  WebSocketChannel
} from '../../types/websocket';
interface AgentStatus {
  id: string;
  name: string;
  type: 'supervisor' | 'content' | 'quiz' | 'terrain' | 'script' | 'review';
  status: 'idle' | 'working' | 'completed' | 'error' | 'cancelled';
  progress: number;
  currentTask?: string;
  startTime?: Date;
  completionTime?: Date;
  error?: string;
  output?: any;
  metrics?: {
    tokensUsed?: number;
    timeElapsed?: number;
    memoryUsage?: number;
  };
}
interface GenerationSession {
  id: string;
  status: 'initializing' | 'processing' | 'reviewing' | 'completed' | 'failed' | 'cancelled';
  startTime: Date;
  endTime?: Date;
  totalProgress: number;
  agents: AgentStatus[];
  request: {
    subject: string;
    gradeLevel: number;
    objectives: string[];
    environmentType: string;
  };
  output?: {
    terrain?: any;
    content?: any;
    quiz?: any;
    scripts?: any;
  };
  errors: string[];
  warnings: string[];
}
const getAgentIcon = (type: AgentStatus['type']) => {
  switch (type) {
    case 'supervisor': return <IconBrain />;
    case 'content': return <IconMovie />;
    case 'quiz': return <IconHelp />;
    case 'terrain': return <IconMountain />;
    case 'script': return <IconCode />;
    case 'review': return <IconCircleCheck />;
    default: return <IconSettings />;
  }
};
const getStatusColor = (status: AgentStatus['status']) => {
  switch (status) {
    case 'idle': return 'default';
    case 'working': return 'primary';
    case 'completed': return 'success';
    case 'error': return 'error';
    case 'cancelled': return 'warning';
    default: return 'default';
  }
};
export const ContentGenerationMonitor: React.FunctionComponent<Record<string, any>> = () => {
  const theme = useMantineTheme();
  const { on, sendMessage, isConnected } = usePusherContext();
  const [session, setSession] = useState<GenerationSession | null>(null);
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set());
  const [showPreview, setShowPreview] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [logs, setLogs] = useState<Array<{ time: Date; message: string; level: 'info' | 'warning' | 'error' }>>([]);
  // Initialize agent statuses
  const initializeAgents = (): AgentStatus[] => [
    { id: 'supervisor', name: 'Supervisor Agent', type: 'supervisor', status: 'idle', progress: 0 },
    { id: 'content', name: 'Content Agent', type: 'content', status: 'idle', progress: 0 },
    { id: 'quiz', name: 'Quiz Agent', type: 'quiz', status: 'idle', progress: 0 },
    { id: 'terrain', name: 'Terrain Agent', type: 'terrain', status: 'idle', progress: 0 },
    { id: 'script', name: 'Script Agent', type: 'script', status: 'idle', progress: 0 },
    { id: 'review', name: 'Review Agent', type: 'review', status: 'idle', progress: 0 }
  ];
  // WebSocket event handlers
  useEffect(() => {
    if (!isConnected) return;
    const unsubscribeProgress = on(WebSocketMessageType.CONTENT_PROGRESS, (data: ContentGenerationProgress) => {
      handleProgressUpdate(data);
    });
    const unsubscribeComplete = on(WebSocketMessageType.CONTENT_COMPLETE, (data: any) => {
      handleGenerationComplete(data);
    });
    const unsubscribeError = on(WebSocketMessageType.CONTENT_ERROR, (data: any) => {
      handleGenerationError(data);
    });
    return () => {
      unsubscribeProgress();
      unsubscribeComplete();
      unsubscribeError();
    };
  }, [isConnected]);
const handleProgressUpdate = (prog: ContentGenerationProgress) => {
    setSession(prev => {
      if (!prev) return null;
      const updatedAgents = prev.agents.map(agent => {
        if (agent.id === prog.agentId) {
          return {
            ...agent,
            status: (prog.status as AgentStatus['status']) || agent.status,
            progress: prog.progress ?? agent.progress,
            currentTask: prog.currentTask ?? agent.currentTask,
            metrics: prog.metrics ?? agent.metrics
          };
        }
        return agent;
      });
      const totalProgress = updatedAgents.reduce((sum, agent) => sum + (agent.progress ?? 0), 0) / updatedAgents.length;
      addLog(`${prog.agentId}: ${prog.currentTask} (${prog.progress ?? 0}%)`, 'info');
      return {
        ...prev,
        agents: updatedAgents,
        totalProgress,
        status: (prog.sessionStatus as GenerationSession['status']) || prev.status
      };
    });
  };
  const handleGenerationComplete = (data: any) => {
    setSession(prev => {
      if (!prev) return null;
      addLog('Content generation completed successfully!', 'info');
      return {
        ...prev,
        status: 'completed',
        endTime: new Date(),
        totalProgress: 100,
        output: data.output,
        agents: prev.agents.map(agent => ({
          ...agent,
          status: 'completed',
          progress: 100,
          completionTime: new Date()
        }))
      };
    });
  };
  const handleGenerationError = (data: any) => {
    setSession(prev => {
      if (!prev) return null;
      addLog(`Error: ${data.error}`, 'error');
      return {
        ...prev,
        status: 'failed',
        errors: [...prev.errors, data.error],
        agents: prev.agents.map(agent => {
          if (agent.id === data.agentId) {
            return {
              ...agent,
              status: 'error',
              error: data.error
            };
          }
          return agent;
        })
      };
    });
  };
  const addLog = (message: string, level: 'info' | 'warning' | 'error') => {
    setLogs(prev => [...prev, { time: new Date(), message, level }]);
  };
  const startGeneration = (request: GenerationSession['request']) => {
    const newSession: GenerationSession = {
      id: `gen_${Date.now()}`,
      status: 'initializing',
      startTime: new Date(),
      totalProgress: 0,
      agents: initializeAgents(),
      request,
      errors: [],
      warnings: []
    };
    setSession(newSession);
    setLogs([]);
    addLog('Starting content generation...', 'info');
    // Send generation request via WebSocket
    sendMessage(WebSocketMessageType.CONTENT_REQUEST, {
      sessionId: newSession.id,
      ...request
    }, {
      channel: WebSocketChannel.CONTENT_UPDATES
    });
  };
  const cancelGeneration = () => {
    if (!session) return;
    sendMessage(WebSocketMessageType.CONTENT_CANCEL, {
      sessionId: session.id
    });
    setSession(prev => {
      if (!prev) return null;
      return {
        ...prev,
        status: 'cancelled',
        endTime: new Date(),
        agents: prev.agents.map(agent => ({
          ...agent,
          status: agent.status === 'working' ? 'cancelled' : agent.status
        }))
      };
    });
    addLog('Generation cancelled by user', 'warning');
  };
  const toggleAgentExpansion = (agentId: string) => {
    setExpandedAgents(prev => {
      const newSet = new Set(prev);
      if (newSet.has(agentId)) {
        newSet.delete(agentId);
      } else {
        newSet.add(agentId);
      }
      return newSet;
    });
  };
  const formatTime = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };
  const downloadOutput = () => {
    if (!session?.output) return;
    const blob = new Blob([JSON.stringify(session.output, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `content_${session.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };
  return (
    <Box style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Header */}
      <Card>
        <Card.Section p="md">
          <Group justify="space-between" align="center">
            <Group align="center">
              <IconBrain color={theme.colors.blue[6]} size={32} />
              <Box>
                <Title order={3}>Content Generation Monitor</Title>
                <Text size="sm" c="dimmed">
                  Real-time AI agent orchestration and progress tracking
                </Text>
              </Box>
            </Group>
            <Group>
              <Badge
                color={isConnected ? 'green' : 'red'}
                size="sm"
              >
                {isConnected ? 'Connected' : 'Disconnected'}
              </Badge>
              {session && (
                <Badge
                  color={getStatusColor(session.status as any) === 'success' ? 'green' :
                         getStatusColor(session.status as any) === 'warning' ? 'yellow' :
                         getStatusColor(session.status as any) === 'error' ? 'red' : 'gray'}
                  size="sm"
                >
                  {session.status}
                </Badge>
              )}
            </Group>
          </Group>
        </Card.Section>
      </Card>
      {/* Session Overview */}
      {session && (
        <Card>
          <Card.Section p="md">
            <Grid gutter="md">
              <Grid.Col span={{ base: 12, md: 8 }}>
                <Box mb="md">
                  <Text size="sm" fw={600} mb="sm">
                    Overall Progress
                  </Text>
                  <Group align="center" gap="md">
                    <Box style={{ flex: 1 }}>
                      <Progress
                        value={session.totalProgress}
                        size="lg"
                        radius="md"
                      />
                    </Box>
                    <Text size="sm" fw={700}>
                      {Math.round(session.totalProgress)}%
                    </Text>
                  </Group>
                </Box>
                <Grid gutter="sm">
                  <Grid.Col span={{ base: 6, sm: 3 }}>
                    <Text size="xs" c="dimmed">Subject</Text>
                    <Text size="sm" fw={600}>{session.request.subject}</Text>
                  </Grid.Col>
                  <Grid.Col span={{ base: 6, sm: 3 }}>
                    <Text size="xs" c="dimmed">Grade Level</Text>
                    <Text size="sm" fw={600}>{session.request.gradeLevel}</Text>
                  </Grid.Col>
                  <Grid.Col span={{ base: 6, sm: 3 }}>
                    <Text size="xs" c="dimmed">Environment</Text>
                    <Text size="sm" fw={600}>{session.request.environmentType}</Text>
                  </Grid.Col>
                  <Grid.Col span={{ base: 6, sm: 3 }}>
                    <Text size="xs" c="dimmed">Duration</Text>
                    <Text size="sm" fw={600}>
                      {session.endTime
                        ? formatTime(session.endTime.getTime() - session.startTime.getTime())
                        : formatTime(Date.now() - session.startTime.getTime())
                      }
                    </Text>
                  </Grid.Col>
                </Grid>
              </Grid.Col>
              <Grid.Col span={{ base: 12, md: 4 }}>
                <Group justify="flex-end" wrap="wrap">
                  {session.status === 'processing' && (
                    <>
                      <Button
                        variant="outline"
                        color="yellow"
                        leftSection={<IconPlayerPause size={16} />}
                        size="sm"
                        disabled
                      >
                        Pause
                      </Button>
                      <Button
                        variant="outline"
                        color="red"
                        leftSection={<IconX size={16} />}
                        size="sm"
                        onClick={cancelGeneration}
                      >
                        Cancel
                      </Button>
                    </>
                  )}
                  {session.status === 'completed' && (
                    <>
                      <Button
                        variant="outline"
                        leftSection={<IconDownload size={16} />}
                        size="sm"
                        onClick={downloadOutput}
                      >
                        Download
                      </Button>
                      <Button
                        variant="outline"
                        leftSection={<IconEye size={16} />}
                        size="sm"
                        onClick={() => setShowPreview(!showPreview)}
                      >
                        Preview
                      </Button>
                    </>
                  )}
                  <Button
                    variant="outline"
                    leftSection={<IconRefresh size={16} />}
                    size="sm"
                    onClick={() => setSession(null)}
                  >
                    Reset
                  </Button>
                </Group>
              </Grid.Col>
            </Grid>
          </Card.Section>
        </Card>
      )}
      {/* Agent Status Grid */}
      {session && (
        <Grid container spacing={2} sx={{ flex: 1, overflow: 'auto' }}>
          {session.agents.map((agent) => (
            <Grid item xs={12} md={6} key={agent.id}>
              <Card
                sx={{
                  border: agent.status === 'working' ? 2 : 1,
                  borderColor: agent.status === 'working'
                    ? 'primary.main'
                    : alpha(theme.palette.divider, 0.2),
                  transition: 'all 0.3s'
                }}
              >
                <CardContent>
                  <Group justify="space-between" align="center" mb="md">
                    <Group align="center">
                      {agent.status === 'working' ? (
                        <RingProgress
                          size={40}
                          thickness={3}
                          sections={[{ value: agent.progress, color: 'blue' }]}
                          label={getAgentIcon(agent.type)}
                        />
                      ) : (
                        <Box style={{ position: 'relative' }}>
                          {getAgentIcon(agent.type)}
                          {agent.status === 'completed' && (
                            <IconCircleCheck
                              size={12}
                              style={{
                                position: 'absolute',
                                top: -4,
                                right: -4,
                                color: theme.colors.green[6]
                              }}
                            />
                          )}
                          {agent.status === 'error' && (
                            <IconExclamationMark
                              size={12}
                              style={{
                                position: 'absolute',
                                top: -4,
                                right: -4,
                                color: theme.colors.red[6]
                              }}
                            />
                          )}
                        </Box>
                      )}
                      <Text size="sm" fw={600}>
                        {agent.name}
                      </Text>
                    </Group>
                    <Group align="center">
                      <Badge
                        color={
                          getStatusColor(agent.status) === 'success' ? 'green' :
                          getStatusColor(agent.status) === 'warning' ? 'yellow' :
                          getStatusColor(agent.status) === 'error' ? 'red' : 'gray'
                        }
                        size="sm"
                      >
                        {agent.status}
                      </Badge>
                      <ActionIcon
                        size="sm"
                        onClick={() => toggleAgentExpansion(agent.id)}
                      >
                        {expandedAgents.has(agent.id) ? <IconChevronUp size={16} /> : <IconChevronDown size={16} />}
                      </ActionIcon>
                    </Group>
                  </Group>
                  <Box mb="sm">
                    <Progress
                      value={agent.progress}
                      size="sm"
                      radius="md"
                    />
                    <Group justify="space-between" mt="xs">
                      <Text size="xs" c="dimmed">
                        {agent.currentTask || 'Idle'}
                      </Text>
                      <Text size="xs" fw={600}>
                        {agent.progress}%
                      </Text>
                    </Group>
                  </Box>
                  <Collapse in={expandedAgents.has(agent.id)}>
                    <Box style={{ borderTop: `1px solid ${theme.colors.gray[3]}`, paddingTop: '8px' }}>
                      <Grid gutter="xs">
                        {agent.metrics?.tokensUsed && (
                          <Grid.Col span={4}>
                            <Group align="center" gap="xs">
                              <IconGauge size={16} color={theme.colors.gray[6]} />
                              <Box>
                                <Text size="xs" c="dimmed">Tokens</Text>
                                <Text size="sm">{agent.metrics.tokensUsed}</Text>
                              </Box>
                            </Group>
                          </Grid.Col>
                        )}
                        {agent.metrics?.timeElapsed && (
                          <Grid.Col span={4}>
                            <Group align="center" gap="xs">
                              <IconClock size={16} color={theme.colors.gray[6]} />
                              <Box>
                                <Text size="xs" c="dimmed">Time</Text>
                                <Text size="sm">{formatTime(agent.metrics.timeElapsed)}</Text>
                              </Box>
                            </Group>
                          </Grid.Col>
                        )}
                        {agent.metrics?.memoryUsage && (
                          <Grid.Col span={4}>
                            <Group align="center" gap="xs">
                              <IconMemory size={16} color={theme.colors.gray[6]} />
                              <Box>
                                <Text size="xs" c="dimmed">Memory</Text>
                                <Text size="sm">{agent.metrics.memoryUsage}MB</Text>
                              </Box>
                            </Group>
                          </Grid.Col>
                        )}
                      </Grid>
                      {agent.error && (
                        <Alert color="red" mt="sm">
                          <Text size="sm" fw={600}>Error</Text>
                          <Text size="sm">{agent.error}</Text>
                        </Alert>
                      )}
                    </Box>
                  </Collapse>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
      {/* Activity Log */}
      {session && logs.length > 0 && (
        <Card sx={{ maxHeight: 200, overflow: 'auto' }}>
          <CardContent>
            <Group justify="space-between" align="center" mb="sm">
              <Text size="sm" fw={600}>Activity Log</Text>
              <Group align="center">
                <Text size="sm">Auto-scroll</Text>
                <MuiSwitch
                  size="sm"
                  checked={autoScroll}
                  onChange={(event) => setAutoScroll(event.currentTarget.checked)}
                />
              </Group>
            </Group>
            <Stack gap="xs">
              {logs.map((log, index) => (
                <Group key={index} align="flex-start" gap="sm">
                  <Box style={{ marginTop: '2px' }}>
                    {log.level === 'error' ? <IconExclamationMark size={16} color={theme.colors.red[6]} /> :
                     log.level === 'warning' ? <IconAlertTriangle size={16} color={theme.colors.yellow[6]} /> :
                     <IconInfoCircle size={16} color={theme.colors.blue[6]} />}
                  </Box>
                  <Box style={{ flex: 1 }}>
                    <Text size="sm">{log.message}</Text>
                    <Text size="xs" c="dimmed">{log.time.toLocaleTimeString()}</Text>
                  </Box>
                </Group>
              ))}
            </Stack>
          </CardContent>
        </Card>
      )}
      {/* Empty State */}
      {!session && (
        <Box
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
            gap: '16px'
          }}
        >
          <IconBrain size={64} color={theme.colors.gray[4]} />
          <Text size="lg" c="dimmed">
            No active content generation
          </Text>
          <Text size="sm" c="dimmed">
            Start a new generation from the Roblox Control Panel
          </Text>
        </Box>
      )}
    </Box>
  );
};
// Add missing 