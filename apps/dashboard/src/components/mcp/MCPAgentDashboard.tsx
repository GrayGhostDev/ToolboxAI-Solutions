import * as React from 'react';
import { useState, useEffect } from 'react';
import {
  Card,
  Text,
  Box,
  Stack,
  Badge,
  ActionIcon,
  Skeleton,
  Alert,
  Grid,
  Paper,
  Progress,
  Avatar,
  Divider,
  Select,
  Button,
  Modal,
  TextInput,
  Textarea,
  Group,
} from '@mantine/core';
import {
  IconRobot,
  IconBrain,
  IconSchool,
  IconQuestionMark,
  IconMountain,
  IconCode,
  IconStarFilled,
  IconPlayerPlay,
  IconPlayerPause,
  IconPlayerStop,
  IconRefresh,
  IconSettings,
  IconMemory,
  IconGauge,
  IconCircleCheck,
  IconExclamationMark,
  IconAlertTriangle,
  IconInfoCircle,
} from '@tabler/icons-react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import { useAppDispatch } from '../../store';
import { addNotification } from '../../store/slices/uiSlice';

interface MCPAgent {
  id: string;
  name: string;
  type: 'supervisor' | 'content' | 'quiz' | 'terrain' | 'script' | 'review';
  status: 'active' | 'idle' | 'working' | 'error' | 'offline';
  lastActivity: string;
  tasksCompleted: number;
  avgResponseTime: number;
  successRate: number;
  memoryUsage: number;
  cpuUsage: number;
  currentTask?: {
    id: string;
    type: string;
    progress: number;
    startedAt: string;
  };
  capabilities: string[];
  metrics: {
    timestamp: string;
    responseTime: number;
    memoryUsage: number;
    cpuUsage: number;
  }[];
}

interface MCPMessage {
  id: string;
  type: 'request' | 'response' | 'notification' | 'error';
  agentId: string;
  content: string;
  timestamp: string;
  data?: any;
}

interface MCPAgentDashboardProps {
  autoRefresh?: boolean;
  showLogs?: boolean;
}

const AGENT_ICONS: Record<string, React.ReactElement> = {
  supervisor: <IconRobot size={20} />,
  content: <IconBrain size={20} />,
  quiz: <IconQuestionMark size={20} />,
  terrain: <IconMountain size={20} />,
  script: <IconCode size={20} />,
  review: <IconStarFilled size={20} />,
};

const AGENT_COLORS: Record<string, string> = {
  supervisor: '#2563EB',
  content: '#22C55E',
  quiz: '#FACC15',
  terrain: '#9333EA',
  script: '#EF4444',
  review: '#06B6D4',
};

export function MCPAgentDashboard({
  autoRefresh = true,
  showLogs = true
}: MCPAgentDashboardProps) {
  const dispatch = useAppDispatch();
  const { isConnected, subscribe, unsubscribe, sendMessage } = useWebSocketContext();
  
  const [agents, setAgents] = useState<MCPAgent[]>([]);
  const [messages, setMessages] = useState<MCPMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<MCPAgent | null>(null);
  const [isTaskDialogOpen, setIsTaskDialogOpen] = useState(false);
  const [taskType, setTaskType] = useState<string>('');
  const [taskContent, setTaskContent] = useState<string>('');
  const [mcpWebSocket, setMcpWebSocket] = useState<WebSocket | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const MAX_RECONNECT_ATTEMPTS = 3;
  const RECONNECT_DELAY_BASE = 5000; // Base delay in ms

  // Connect to MCP WebSocket server on port 9876 with retry logic
  const connectToMCP = React.useCallback(async () => {
    // Check if we've exceeded max reconnection attempts
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      console.log('Max reconnection attempts reached. Using mock data.');
      setError('MCP server unavailable - using mock data');
      loadMockData();
      setLoading(false);
      return;
    }

    // Close existing connection if any
    if (mcpWebSocket && mcpWebSocket.readyState !== WebSocket.CLOSED) {
      mcpWebSocket.close();
    }

    try {
      setLoading(true);
      setError(null);

      // Initialize WebSocket connection to MCP server
      const mcpWs = new WebSocket('ws://localhost:9876/mcp');
      setMcpWebSocket(mcpWs);
      
      mcpWs.onopen = () => {
        console.log('Connected to MCP server');
        setReconnectAttempts(0); // Reset attempts on successful connection
        // Request agent status
        mcpWs.send(JSON.stringify({
          type: 'get_agents_status',
          timestamp: new Date().toISOString(),
        }));
      };

      mcpWs.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleMCPMessage(message);
      };

      mcpWs.onerror = (error) => {
        console.error('MCP WebSocket error:', error);
        setError('MCP connection error - will retry');
      };

      mcpWs.onclose = (event) => {
        console.log('MCP WebSocket connection closed:', event.code, event.reason);
        setMcpWebSocket(null);
        
        // Only retry if autoRefresh is enabled and we haven't exceeded max attempts
        if (autoRefresh && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
          const delay = RECONNECT_DELAY_BASE * Math.pow(2, reconnectAttempts); // Exponential backoff
          console.log(`Reconnecting in ${delay/1000} seconds... (attempt ${reconnectAttempts + 1}/${MAX_RECONNECT_ATTEMPTS})`);
          setReconnectAttempts(prev => prev + 1);
          setTimeout(() => {
            connectToMCP();
          }, delay);
        } else if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
          setError('MCP server unavailable - using mock data');
          loadMockData();
        }
      };

    } catch (err: any) {
      console.error('Failed to create WebSocket connection:', err);
      setError(err.message || 'Failed to connect to MCP server');
      setMcpWebSocket(null);
      
      // Use mock data as fallback
      if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS - 1) {
        loadMockData();
      }
    } finally {
      setLoading(false);
    }
  }, [autoRefresh, reconnectAttempts, mcpWebSocket]);

  // Handle MCP messages
  const handleMCPMessage = (message: any) => {
    switch (message.type) {
      case 'agents_status':
        if (message.agents) {
          setAgents(message.agents);
        }
        break;
      case 'agent_update':
        setAgents(prevAgents =>
          prevAgents.map(agent =>
            agent.id === message.agentId
              ? { ...agent, ...message.updates }
              : agent
          )
        );
        break;
      case 'task_progress':
        setAgents(prevAgents =>
          prevAgents.map(agent =>
            agent.id === message.agentId
              ? { 
                  ...agent, 
                  currentTask: message.task,
                  status: 'working'
                }
              : agent
          )
        );
        break;
      case 'task_completed':
        setAgents(prevAgents =>
          prevAgents.map(agent =>
            agent.id === message.agentId
              ? { 
                  ...agent, 
                  currentTask: undefined,
                  status: 'active',
                  tasksCompleted: agent.tasksCompleted + 1,
                  lastActivity: new Date().toISOString(),
                }
              : agent
          )
        );
        break;
      case 'error':
        dispatch(addNotification({
          type: 'error',
          message: `MCP Error: ${message.error}`,
        }));
        break;
      default:
        // Add to message log
        setMessages(prevMessages => [
          {
            id: Date.now().toString(),
            type: message.type,
            agentId: message.agentId || 'system',
            content: message.content || JSON.stringify(message),
            timestamp: new Date().toISOString(),
            data: message,
          },
          ...prevMessages.slice(0, 99), // Keep last 100 messages
        ]);
        break;
    }
  };

  // Load mock data when MCP is not available
  const loadMockData = () => {
    const mockAgents: MCPAgent[] = [
      {
        id: 'supervisor',
        name: 'Supervisor Agent',
        type: 'supervisor',
        status: 'active',
        lastActivity: new Date().toISOString(),
        tasksCompleted: 156,
        avgResponseTime: 245,
        successRate: 98.5,
        memoryUsage: 68,
        cpuUsage: 42,
        capabilities: ['orchestration', 'task_routing', 'error_handling'],
        metrics: Array.from({ length: 10 }, (_, i) => ({
          timestamp: new Date(Date.now() - i * 60000).toISOString(),
          responseTime: Math.floor(Math.random() * 500) + 200,
          memoryUsage: Math.floor(Math.random() * 20) + 60,
          cpuUsage: Math.floor(Math.random() * 30) + 30,
        })),
      },
      {
        id: 'content',
        name: 'Content Generator',
        type: 'content',
        status: 'working',
        lastActivity: new Date().toISOString(),
        tasksCompleted: 89,
        avgResponseTime: 1200,
        successRate: 94.2,
        memoryUsage: 85,
        cpuUsage: 78,
        currentTask: {
          id: 'task_001',
          type: 'generate_lesson',
          progress: 65,
          startedAt: new Date(Date.now() - 120000).toISOString(),
        },
        capabilities: ['lesson_generation', 'content_creation', 'curriculum_design'],
        metrics: Array.from({ length: 10 }, (_, i) => ({
          timestamp: new Date(Date.now() - i * 60000).toISOString(),
          responseTime: Math.floor(Math.random() * 1000) + 800,
          memoryUsage: Math.floor(Math.random() * 25) + 70,
          cpuUsage: Math.floor(Math.random() * 40) + 60,
        })),
      },
      {
        id: 'quiz',
        name: 'Quiz Agent',
        type: 'quiz',
        status: 'idle',
        lastActivity: new Date(Date.now() - 300000).toISOString(),
        tasksCompleted: 234,
        avgResponseTime: 180,
        successRate: 96.8,
        memoryUsage: 45,
        cpuUsage: 25,
        capabilities: ['quiz_generation', 'assessment_creation', 'grading'],
        metrics: Array.from({ length: 10 }, (_, i) => ({
          timestamp: new Date(Date.now() - i * 60000).toISOString(),
          responseTime: Math.floor(Math.random() * 300) + 150,
          memoryUsage: Math.floor(Math.random() * 15) + 40,
          cpuUsage: Math.floor(Math.random() * 20) + 20,
        })),
      },
      {
        id: 'terrain',
        name: 'Terrain Builder',
        type: 'terrain',
        status: 'active',
        lastActivity: new Date(Date.now() - 60000).toISOString(),
        tasksCompleted: 67,
        avgResponseTime: 3400,
        successRate: 91.5,
        memoryUsage: 92,
        cpuUsage: 85,
        capabilities: ['3d_modeling', 'environment_design', 'world_building'],
        metrics: Array.from({ length: 10 }, (_, i) => ({
          timestamp: new Date(Date.now() - i * 60000).toISOString(),
          responseTime: Math.floor(Math.random() * 2000) + 2500,
          memoryUsage: Math.floor(Math.random() * 20) + 80,
          cpuUsage: Math.floor(Math.random() * 30) + 70,
        })),
      },
      {
        id: 'script',
        name: 'Script Agent',
        type: 'script',
        status: 'error',
        lastActivity: new Date(Date.now() - 180000).toISOString(),
        tasksCompleted: 145,
        avgResponseTime: 890,
        successRate: 89.2,
        memoryUsage: 58,
        cpuUsage: 35,
        capabilities: ['lua_scripting', 'code_generation', 'debugging'],
        metrics: Array.from({ length: 10 }, (_, i) => ({
          timestamp: new Date(Date.now() - i * 60000).toISOString(),
          responseTime: Math.floor(Math.random() * 800) + 600,
          memoryUsage: Math.floor(Math.random() * 20) + 50,
          cpuUsage: Math.floor(Math.random() * 25) + 30,
        })),
      },
      {
        id: 'review',
        name: 'Review Agent',
        type: 'review',
        status: 'active',
        lastActivity: new Date(Date.now() - 30000).toISOString(),
        tasksCompleted: 201,
        avgResponseTime: 320,
        successRate: 97.1,
        memoryUsage: 52,
        cpuUsage: 28,
        capabilities: ['content_review', 'quality_assurance', 'validation'],
        metrics: Array.from({ length: 10 }, (_, i) => ({
          timestamp: new Date(Date.now() - i * 60000).toISOString(),
          responseTime: Math.floor(Math.random() * 400) + 250,
          memoryUsage: Math.floor(Math.random() * 15) + 45,
          cpuUsage: Math.floor(Math.random() * 20) + 25,
        })),
      },
    ];

    setAgents(mockAgents);
  };

  // Initial connection with cleanup
  useEffect(() => {
    let mounted = true;
    
    // Only connect if component is mounted and no existing connection
    if (mounted && !mcpWebSocket) {
      connectToMCP();
    }
    
    // Cleanup on unmount
    return () => {
      mounted = false;
      if (mcpWebSocket && mcpWebSocket.readyState !== WebSocket.CLOSED) {
        mcpWebSocket.close();
      }
    };
  }, []); // Remove connectToMCP from dependencies to avoid reconnection loops

  // Real-time updates via regular WebSocket
  useEffect(() => {
    if (!isConnected || !autoRefresh) return;

    const subscriptionId = subscribe('mcp_agents', (message: any) => {
      handleMCPMessage(message);
    });

    return () => {
      unsubscribe(subscriptionId);
    };
  }, [isConnected, autoRefresh, subscribe, unsubscribe]);

  // Send task to agent
  const handleSendTask = async () => {
    if (!selectedAgent || !taskType || !taskContent) return;

    try {
      // Send task via WebSocket or MCP
      const message = {
        type: 'assign_task',
        agentId: selectedAgent.id,
        task: {
          type: taskType,
          content: taskContent,
          timestamp: new Date().toISOString(),
        },
      };

      if (sendMessage) {
        (sendMessage as any)('mcp_agents', message);
      }

      dispatch(addNotification({
        type: 'success',
        message: `Task sent to ${selectedAgent.name}`,
      }));

      setIsTaskDialogOpen(false);
      setTaskType('');
      setTaskContent('');
    } catch (error) {
      dispatch(addNotification({
        type: 'error',
        message: 'Failed to send task to agent',
      }));
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'green';
      case 'working':
        return 'yellow';
      case 'idle':
        return 'gray';
      case 'error':
        return 'red';
      case 'offline':
        return 'red';
      default:
        return 'gray';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <IconCircleCheck size={16} style={{ color: 'var(--mantine-color-green-6)' }} />;
      case 'working':
        return <IconPlayerPlay size={16} style={{ color: 'var(--mantine-color-yellow-6)' }} />;
      case 'idle':
        return <IconPlayerPause size={16} style={{ color: 'var(--mantine-color-gray-6)' }} />;
      case 'error':
        return <IconExclamationMark size={16} style={{ color: 'var(--mantine-color-red-6)' }} />;
      case 'offline':
        return <IconPlayerStop size={16} style={{ color: 'var(--mantine-color-red-6)' }} />;
      default:
        return <IconInfoCircle size={16} />;
    }
  };

  if (loading) {
    return (
      <Grid>
        {[1, 2, 3, 4].map((item) => (
          <Grid.Col span={{ base: 12, md: 6, lg: 4 }} key={item}>
            <Card withBorder>
              <Stack gap="md">
                <Skeleton height={40} />
                <Skeleton height={200} />
              </Stack>
            </Card>
          </Grid.Col>
        ))}
      </Grid>
    );
  }

  return (
    <Grid>
      {/* Header */}
      <Grid.Col span={12}>
        <Card withBorder>
          <Stack gap="md">
            <Group justify="space-between" align="center">
              <Text size="xl" fw={600}>
                MCP Agent Dashboard
              </Text>
              <Group gap="sm" align="center">
                {mcpWebSocket && mcpWebSocket.readyState === WebSocket.OPEN ? (
                  <Badge color="green" size="sm">MCP Connected</Badge>
                ) : reconnectAttempts > 0 ? (
                  <Badge color="yellow" size="sm">
                    Reconnecting... ({reconnectAttempts}/{MAX_RECONNECT_ATTEMPTS})
                  </Badge>
                ) : (
                  <Badge color="gray" size="sm">MCP Offline</Badge>
                )}
                <ActionIcon
                  onClick={() => {
                    setReconnectAttempts(0);
                    connectToMCP();
                  }}
                  disabled={!!(mcpWebSocket && mcpWebSocket.readyState === WebSocket.CONNECTING)}
                  variant="subtle"
                >
                  <IconRefresh size={16} />
                </ActionIcon>
              </Group>
            </Group>

            {error && (
              <Alert color="yellow" title="MCP Connection Issue">
                {error} (Using mock data)
              </Alert>
            )}

            {/* Quick Stats */}
            <Grid>
              <Grid.Col span={{ base: 6, md: 3 }}>
                <Paper p="md" style={{ textAlign: 'center' }} withBorder>
                  <Text size="xs" c="dimmed">
                    Active Agents
                  </Text>
                  <Text size="xl" fw={700} c="green">
                    {agents.filter(a => a.status === 'active' || a.status === 'working').length}
                  </Text>
                </Paper>
              </Grid.Col>
              <Grid.Col span={{ base: 6, md: 3 }}>
                <Paper p="md" style={{ textAlign: 'center' }} withBorder>
                  <Text size="xs" c="dimmed">
                    Tasks Completed
                  </Text>
                  <Text size="xl" fw={700} c="blue">
                    {agents.reduce((sum, agent) => sum + agent.tasksCompleted, 0)}
                  </Text>
                </Paper>
              </Grid.Col>
              <Grid.Col span={{ base: 6, md: 3 }}>
                <Paper p="md" style={{ textAlign: 'center' }} withBorder>
                  <Text size="xs" c="dimmed">
                    Avg Response Time
                  </Text>
                  <Text size="xl" fw={700} c="cyan">
                    {Math.round(agents.reduce((sum, agent) => sum + agent.avgResponseTime, 0) / agents.length)}ms
                  </Text>
                </Paper>
              </Grid.Col>
              <Grid.Col span={{ base: 6, md: 3 }}>
                <Paper p="md" style={{ textAlign: 'center' }} withBorder>
                  <Text size="xs" c="dimmed">
                    Success Rate
                  </Text>
                  <Text size="xl" fw={700} c="orange">
                    {Math.round(agents.reduce((sum, agent) => sum + agent.successRate, 0) / agents.length)}%
                  </Text>
                </Paper>
              </Grid.Col>
            </Grid>
          </Stack>
        </Card>
      </Grid.Col>

      {/* Agent Cards */}
      {agents.map((agent) => (
        <Grid.Col span={{ base: 12, md: 6, lg: 4 }} key={agent.id}>
          <Card withBorder>
            <Stack gap="md">
              {/* Agent Header */}
              <Group justify="space-between" align="center">
                <Group align="center" gap="sm">
                  <Avatar
                    style={{
                      backgroundColor: AGENT_COLORS[agent.type] + '20',
                      color: AGENT_COLORS[agent.type]
                    }}
                  >
                    {AGENT_ICONS[agent.type]}
                  </Avatar>
                  <Box>
                    <Text size="lg" fw={600}>
                      {agent.name}
                    </Text>
                    <Badge
                      size="sm"
                      color={getStatusColor(agent.status)}
                      leftSection={getStatusIcon(agent.status)}
                    >
                      {agent.status}
                    </Badge>
                  </Box>
                </Group>
                <ActionIcon
                  size="sm"
                  variant="subtle"
                  onClick={() => {
                    setSelectedAgent(agent);
                    setIsTaskDialogOpen(true);
                  }}
                >
                  <IconSettings size={16} />
                </ActionIcon>
              </Group>

              {/* Current Task */}
              {agent.currentTask && (
                <Paper p="md" style={{ backgroundColor: 'var(--mantine-color-yellow-1)' }} withBorder>
                  <Text size="sm" fw={600} mb="xs">
                    Current Task: {agent.currentTask.type}
                  </Text>
                  <Progress
                    value={agent.currentTask.progress}
                    mb="xs"
                    color="yellow"
                  />
                  <Text size="xs" c="dimmed">
                    {agent.currentTask.progress}% complete • Started {new Date(agent.currentTask.startedAt).toLocaleTimeString()}
                  </Text>
                </Paper>
              )}

              {/* Agent Stats */}
              <Grid>
                <Grid.Col span={6}>
                  <Text size="xs" c="dimmed">
                    Tasks Completed
                  </Text>
                  <Text size="lg" fw={600}>
                    {agent.tasksCompleted}
                  </Text>
                </Grid.Col>
                <Grid.Col span={6}>
                  <Text size="xs" c="dimmed">
                    Success Rate
                  </Text>
                  <Text size="lg" fw={600}>
                    {agent.successRate.toFixed(1)}%
                  </Text>
                </Grid.Col>
                <Grid.Col span={6}>
                  <Text size="xs" c="dimmed">
                    Response Time
                  </Text>
                  <Text size="lg" fw={600}>
                    {agent.avgResponseTime}ms
                  </Text>
                </Grid.Col>
                <Grid.Col span={6}>
                  <Text size="xs" c="dimmed">
                    Memory Usage
                  </Text>
                  <Text size="lg" fw={600}>
                    {agent.memoryUsage}%
                  </Text>
                </Grid.Col>
              </Grid>

              {/* Performance Chart */}
              <Box style={{ height: 100 }}>
                <ResponsiveContainer>
                  <LineChart data={agent.metrics.slice(-10)}>
                    <Line
                      type="monotone"
                      dataKey="responseTime"
                      stroke={AGENT_COLORS[agent.type]}
                      strokeWidth={2}
                      dot={false}
                    />
                    <Tooltip />
                  </LineChart>
                </ResponsiveContainer>
              </Box>

              {/* Capabilities */}
              <Group gap="xs">
                {agent.capabilities.slice(0, 3).map((capability) => (
                  <Badge
                    key={capability}
                    size="xs"
                    variant="outline"
                  >
                    {capability}
                  </Badge>
                ))}
              </Group>
            </Stack>
          </Card>
        </Grid.Col>
      ))}

      {/* Message Log */}
      {showLogs && (
        <Grid.Col span={12}>
          <Card withBorder>
            <Stack gap="md">
              <Text size="lg" fw={600}>
                MCP Message Log
              </Text>
              <Box style={{ maxHeight: 300, overflow: 'auto' }}>
                <Stack gap="xs">
                  {messages.slice(0, 20).map((message, index) => (
                    <React.Fragment key={message.id}>
                      <Group align="flex-start" gap="sm">
                        <Box style={{ minWidth: 24 }}>
                          {AGENT_ICONS[agents.find(a => a.id === message.agentId)?.type || 'supervisor']}
                        </Box>
                        <Box style={{ flex: 1 }}>
                          <Text size="sm">
                            {message.content}
                          </Text>
                          <Text size="xs" c="dimmed">
                            {message.type} • {new Date(message.timestamp).toLocaleTimeString()}
                          </Text>
                        </Box>
                      </Group>
                      {index < messages.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </Stack>
              </Box>
            </Stack>
          </Card>
        </Grid.Col>
      )}

      {/* Task Assignment Modal */}
      <Modal
        opened={isTaskDialogOpen}
        onClose={() => setIsTaskDialogOpen(false)}
        title={`Assign Task to ${selectedAgent?.name}`}
        size="md"
      >
        <Stack gap="md">
          <Select
            label="Task Type"
            placeholder="Select task type"
            value={taskType}
            onChange={(value) => setTaskType(value || '')}
            data={[
              { value: 'generate_content', label: 'Generate Content' },
              { value: 'create_quiz', label: 'Create Quiz' },
              { value: 'build_terrain', label: 'Build Terrain' },
              { value: 'write_script', label: 'Write Script' },
              { value: 'review_content', label: 'Review Content' },
            ]}
          />
          <Textarea
            label="Task Content"
            placeholder="Describe the task details..."
            value={taskContent}
            onChange={(event) => setTaskContent(event.currentTarget.value)}
            rows={4}
          />
          <Group justify="flex-end" gap="sm">
            <Button variant="subtle" onClick={() => setIsTaskDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSendTask}>
              Assign Task
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Grid>
  );
}

export default MCPAgentDashboard;