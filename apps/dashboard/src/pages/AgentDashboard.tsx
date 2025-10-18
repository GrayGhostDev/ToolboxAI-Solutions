/**
 * Agent Dashboard Component
 *
 * Main dashboard for monitoring and managing AI agents in the ToolBoxAI system.
 * Provides real-time status updates via Pusher integration.
 *
 * Features:
 * - Real-time agent status monitoring
 * - Task execution interface
 * - Performance metrics display
 * - System health indicators
 * - Agent configuration management
 *
 * @author ToolboxAI Team
 * @created 2025-09-21
 * @version 1.0.0
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Box,
  Card,
  SimpleGrid,
  Text,
  Button,
  Badge,
  Alert,
  Skeleton,
  Tooltip,
  ActionIcon,
  Modal,
  Progress,
  List,
  Group,
  Stack,
  Flex,
  Indicator,
  Title,
  Container,
} from '@mantine/core';
import {
  IconRefresh,
  IconPlayerPlay,
  IconPlayerStop,
  IconSettings,
  IconChartBar,
  IconAlertTriangle,
  IconCircleCheck,
  IconClock,
  IconCpu,
  IconDatabase,
  IconServer,
  IconActivity,
  IconBrain,
  IconRobot,
  IconCloud,
  IconNetwork,
  IconMemory,
  IconClock24,
  IconPlayerPlayFilled,
  IconPlayerStopFilled,
} from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { type RootState } from '@/store';
import { useAuth } from '@/hooks/useAuth';
import { orchestratorApi } from '@/services/orchestratorApi';
import { usePusherChannel } from '@/hooks/usePusher';
import { showNotification } from '@mantine/notifications';

interface AgentInfo {
  name: string;
  category: string;
  description: string;
  capabilities: string[];
  status: string;
  metrics: Record<string, any>;
}

interface SystemStatus {
  orchestrator: {
    is_running: boolean;
    uptime: number;
    total_processed: number;
  };
  agents: Record<string, number>;
  tasks: {
    pending: number;
    active: number;
    completed: number;
    failed: number;
  };
  resources: {
    cpu_percent: number;
    memory_percent: number;
    memory_used_mb: number;
    memory_available_mb: number;
    disk_usage_percent: number;
    disk_free_gb: number;
    network_sent_mb: number;
    network_recv_mb: number;
    process_count: number;
  };
  worktrees?: any;
}

interface TaskInfo {
  task_id: string;
  status: string;
  agent_type: string;
  created_at: string;
  message?: string;
  result?: any;
}

const AgentDashboard: React.FunctionComponent = () => {
  const navigate = useNavigate();
  const { user, hasPermission } = useAuth();
  const settings = useSelector((state: RootState) => state.settings);

  // State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [recentTasks, setRecentTasks] = useState<TaskInfo[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000);
  const [showTaskModal, setShowTaskModal] = useState(false);

  // Check access permissions
  const canAccess = useCallback(() => {
    if (hasPermission('admin')) return true;
    if (hasPermission('teacher') && settings?.agentDashboard?.teacherAccess) return true;
    return false;
  }, [hasPermission, settings]);

  // Redirect if no access
  useEffect(() => {
    if (!canAccess()) {
      navigate('/dashboard');
    }
  }, [canAccess, navigate]);

  // Fetch agents
  const fetchAgents = useCallback(async () => {
    try {
      const data = await orchestratorApi.listAgents();
      setAgents(data);
    } catch (err) {
      console.error('Failed to fetch agents:', err);
    }
  }, []);

  // Fetch system status
  const fetchSystemStatus = useCallback(async () => {
    try {
      const data = await orchestratorApi.getSystemStatus();
      setSystemStatus(data);
    } catch (err) {
      console.error('Failed to fetch system status:', err);
    }
  }, []);

  // Initial load
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        await Promise.all([
          fetchAgents(),
          fetchSystemStatus(),
        ]);
      } catch (err) {
        setError('Failed to load agent system data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [fetchAgents, fetchSystemStatus]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      fetchSystemStatus();
    }, refreshInterval);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchSystemStatus]);

  // Subscribe to Pusher for real-time updates
  usePusherChannel(
    'agent-system',
    {
      'task-update': (data: any) => {
        // Update task in recentTasks if it exists
        setRecentTasks(prev => {
          const index = prev.findIndex(t => t.task_id === data.task_id);
          if (index !== -1) {
            const updated = [...prev];
            updated[index] = { ...updated[index], ...data };
            return updated;
          }
          return [data, ...prev].slice(0, 10); // Keep last 10 tasks
        });
      },
      'agent-status': (data: any) => {
        // Update agent status
        setAgents(prev => {
          const index = prev.findIndex(a => a.name === data.agent_name);
          if (index !== -1) {
            const updated = [...prev];
            updated[index] = { ...updated[index], status: data.status };
            return updated;
          }
          return prev;
        });
      },
      'system-metrics': (data: any) => {
        // Update system metrics
        setSystemStatus(prev => prev ? { ...prev, ...data } : null);
      }
    },
    { dependencies: [] }
  );

  // Submit test task
  const submitTestTask = async () => {
    try {
      const result = await orchestratorApi.submitTask({
        agent_type: 'content',
        task_data: {
          action: 'test',
          timestamp: new Date().toISOString(),
        },
        priority: 3,
      });

      // Add to recent tasks
      setRecentTasks(prev => [result, ...prev].slice(0, 10));

      showNotification({
        title: 'Task Submitted',
        message: `Task ${result.task_id} submitted successfully`,
        color: 'green',
      });
    } catch (err) {
      console.error('Failed to submit test task:', err);
      showNotification({
        title: 'Task Failed',
        message: 'Failed to submit test task',
        color: 'red',
      });
    }
  };

  // Format uptime
  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours}h ${minutes}m ${secs}s`;
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'running':
      case 'available':
      case 'completed':
        return 'green';
      case 'pending':
      case 'queued':
        return 'blue';
      case 'failed':
      case 'error':
        return 'red';
      case 'busy':
      case 'in_progress':
        return 'yellow';
      default:
        return 'gray';
    }
  };

  if (loading) {
    return (
      <Container size="xl" p="md">
        <Stack gap="md">
          <Skeleton height={60} />
          <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }} spacing="md">
            {[1, 2, 3, 4].map(i => (
              <Skeleton key={i} height={120} />
            ))}
          </SimpleGrid>
          <Skeleton height={400} />
        </Stack>
      </Container>
    );
  }

  if (error) {
    return (
      <Alert color="red" title="Error">
        {error}
      </Alert>
    );
  }

  return (
    <Container size="xl" p="md">
      {/* Header */}
      <Group justify="space-between" mb="xl">
        <Title order={2}>
          <IconBrain size={28} style={{ verticalAlign: 'middle', marginRight: 8 }} />
          Agent System Dashboard
        </Title>
        <Group gap="sm">
          <Button
            variant="subtle"
            leftSection={<IconRefresh size={16} />}
            onClick={fetchSystemStatus}
          >
            Refresh
          </Button>
          {hasPermission('admin') && (
            <Button
              variant="light"
              leftSection={<IconSettings size={16} />}
              onClick={() => navigate('/settings/agents')}
            >
              Settings
            </Button>
          )}
        </Group>
      </Group>

      {/* System Overview */}
      <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }} spacing="md" mb="xl">
        <Card shadow="sm">
          <Group justify="space-between">
            <div>
              <Text c="dimmed" size="xs" tt="uppercase" fw={700}>
                System Status
              </Text>
              <Group gap="xs" mt="xs">
                {systemStatus?.orchestrator.is_running ? (
                  <>
                    <IconCircleCheck size={20} color="green" />
                    <Text size="lg" fw={500} c="green">Running</Text>
                  </>
                ) : (
                  <>
                    <IconAlertTriangle size={20} color="red" />
                    <Text size="lg" fw={500} c="red">Stopped</Text>
                  </>
                )}
              </Group>
              <Text size="xs" c="dimmed" mt="xs">
                Uptime: {formatUptime(systemStatus?.orchestrator.uptime || 0)}
              </Text>
            </div>
            <IconServer size={30} color="gray" />
          </Group>
        </Card>

        <Card shadow="sm">
          <Group justify="space-between">
            <div>
              <Text c="dimmed" size="xs" tt="uppercase" fw={700}>
                Total Agents
              </Text>
              <Text size="xl" fw={700}>{agents.length}</Text>
              <Text size="xs" c="dimmed" mt="xs">
                Across {Object.keys(systemStatus?.agents || {}).length} categories
              </Text>
            </div>
            <IconRobot size={30} color="gray" />
          </Group>
        </Card>

        <Card shadow="sm">
          <Group justify="space-between">
            <div>
              <Text c="dimmed" size="xs" tt="uppercase" fw={700}>
                Tasks Processed
              </Text>
              <Text size="xl" fw={700}>
                {systemStatus?.orchestrator.total_processed || 0}
              </Text>
              <Group gap="xs" mt="xs">
                <Badge color="yellow" size="sm">
                  {systemStatus?.tasks.active || 0} active
                </Badge>
                <Badge color="blue" size="sm">
                  {systemStatus?.tasks.pending || 0} pending
                </Badge>
              </Group>
            </div>
            <IconActivity size={30} color="gray" />
          </Group>
        </Card>

        <Card shadow="sm">
          <Group justify="space-between">
            <div>
              <Text c="dimmed" size="xs" tt="uppercase" fw={700}>
                Resource Usage
              </Text>
              <Stack gap="xs" mt="xs">
                <div>
                  <Text size="xs" c="dimmed">CPU</Text>
                  <Progress
                    value={systemStatus?.resources.cpu_percent || 0}
                    color={systemStatus?.resources.cpu_percent > 80 ? 'red' : 'blue'}
                    size="sm"
                  />
                </div>
                <div>
                  <Text size="xs" c="dimmed">Memory</Text>
                  <Progress
                    value={systemStatus?.resources.memory_percent || 0}
                    color={systemStatus?.resources.memory_percent > 80 ? 'red' : 'green'}
                    size="sm"
                  />
                </div>
              </Stack>
            </div>
            <IconCpu size={30} color="gray" />
          </Group>
        </Card>
      </SimpleGrid>

      {/* Agents Grid */}
      <Card shadow="sm" mb="xl">
        <Group justify="space-between" mb="md">
          <Text size="lg" fw={600}>Registered Agents</Text>
          <Button
            variant="light"
            leftSection={<IconPlayerPlay size={16} />}
            onClick={submitTestTask}
          >
            Submit Test Task
          </Button>
        </Group>

        <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="md">
          {agents.map((agent) => (
            <Card key={agent.name} shadow="xs" p="sm" withBorder>
              <Group justify="space-between" mb="xs">
                <Text fw={500}>{agent.name}</Text>
                <Badge color={getStatusColor(agent.status)} size="sm">
                  {agent.status}
                </Badge>
              </Group>
              <Text size="xs" c="dimmed" mb="xs">
                {agent.description}
              </Text>
              <Text size="xs" c="dimmed">
                {agent.capabilities.length} capabilities
              </Text>
            </Card>
          ))}
        </SimpleGrid>
      </Card>

      {/* Recent Tasks */}
      <Card shadow="sm">
        <Text size="lg" fw={600} mb="md">Recent Tasks</Text>
        {recentTasks.length === 0 ? (
          <Text c="dimmed" ta="center" py="xl">
            No recent tasks
          </Text>
        ) : (
          <Stack gap="xs">
            {recentTasks.map((task) => (
              <Card key={task.task_id} shadow="xs" p="xs" withBorder>
                <Group justify="space-between">
                  <Group gap="xs">
                    <Text size="xs" fw={500} style={{ fontFamily: 'monospace' }}>
                      {task.task_id.substring(0, 8)}...
                    </Text>
                    <Badge variant="outline" size="sm">
                      {task.agent_type}
                    </Badge>
                    <Badge color={getStatusColor(task.status)} size="sm">
                      {task.status}
                    </Badge>
                  </Group>
                  <Text size="xs" c="dimmed">
                    {new Date(task.created_at).toLocaleTimeString()}
                  </Text>
                </Group>
                {task.message && (
                  <Text size="xs" c="dimmed" mt="xs">
                    {task.message}
                  </Text>
                )}
              </Card>
            ))}
          </Stack>
        )}
      </Card>
    </Container>
  );
};

export default AgentDashboard;