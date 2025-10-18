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
  IconBolt,
  IconTrendingUp,
} from '@tabler/icons-react';
import { usePusher } from '../../hooks/usePusher';
import { useAgentAPI } from '../../hooks/useAgentAPI';
import { useSupabaseAgent } from '../../hooks/useSupabaseAgent';
import { AgentCard } from './AgentCard';
import { AgentTaskDialog } from './AgentTaskDialog';
import { AgentMetricsPanel } from './AgentMetricsPanel';
import { SystemHealthIndicator } from './SystemHealthIndicator';

// Types
interface AgentStatus {
  agent_id: string;
  agent_type: string;
  status: 'initializing' | 'idle' | 'busy' | 'processing' | 'waiting' | 'error' | 'offline' | 'maintenance';
  current_task_id?: string;
  total_tasks_completed: number;
  total_tasks_failed: number;
  average_execution_time: number;
  last_activity: string;
  created_at: string;
  performance_metrics: {
    uptime: number;
    throughput: number;
    error_rate: number;
    success_rate: number;
  };
  resource_usage: {
    cpu_percent: number;
    memory_mb: number;
    gpu_percent: number;
  };
}

interface SystemMetrics {
  agents: {
    total: number;
    idle: number;
    busy: number;
    error: number;
    utilization_rate: number;
  };
  tasks: {
    total: number;
    completed: number;
    failed: number;
    running: number;
    queued: number;
    success_rate: number;
  };
  system: {
    status: 'healthy' | 'degraded' | 'error';
    uptime: string;
    last_updated: string;
  };
}

export const AgentDashboard= () => {
  // State
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<AgentStatus | null>(null);
  const [taskDialogOpen, setTaskDialogOpen] = useState(false);
  const [metricsDialogOpen, setMetricsDialogOpen] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Hooks
  const { service: pusher, isConnected } = usePusher();
  const {
    getAgentsStatus,
    getSystemMetrics,
    executeTask,
    getAgentStatus,
    loading: apiLoading
  } = useAgentAPI();
  
  // Supabase integration
  const {
    agents: supabaseAgents,
    executions: supabaseExecutions,
    metrics: supabaseMetrics,
    systemHealth: supabaseSystemHealth,
    healthSummary: supabaseHealthSummary,
    loading: supabaseLoading,
    error: supabaseError,
    configured: supabaseConfigured,
    actions: supabaseActions
  } = useSupabaseAgent({
    enableRealtime: true,
    refreshInterval: 30000,
    autoRefresh: autoRefresh
  });

  // Status color mapping
  const getStatusColor = useCallback((status: string) => {
    switch (status) {
      case 'idle': return 'success';
      case 'busy': 
      case 'processing': return 'primary';
      case 'waiting': return 'warning';
      case 'error': return 'error';
      case 'offline': 
      case 'maintenance': return 'default';
      case 'initializing': return 'info';
      default: return 'default';
    }
  }, []);

  // Status icon mapping
  const getStatusIcon = useCallback((status: string) => {
    switch (status) {
      case 'idle': return <IconCircleCheck />;
      case 'busy':
      case 'processing': return <IconPlayerPlay />;
      case 'waiting': return <IconClock />;
      case 'error': return <IconAlertTriangle />;
      case 'offline':
      case 'maintenance': return <IconPlayerStop />;
      case 'initializing': return <IconRefresh />;
      default: return <IconCircleCheck />;
    }
  }, []);

  // Load initial data
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Load data from both API and Supabase
      const [agentsData, metricsData] = await Promise.all([
        getAgentsStatus(),
        getSystemMetrics()
      ]);

      // Use API data as primary source
      if (agentsData.success) {
        setAgents(agentsData.data || []);
      } else if (supabaseConfigured && supabaseAgents.length > 0) {
        // Fallback to Supabase data if API fails
        const convertedAgents: AgentStatus[] = supabaseAgents.map(agent => ({
          agent_id: agent.agent_id,
          agent_type: agent.agent_type,
          status: agent.status,
          current_task_id: agent.current_task_id,
          total_tasks_completed: agent.total_tasks_completed,
          total_tasks_failed: agent.total_tasks_failed,
          average_execution_time: agent.average_execution_time,
          last_activity: agent.last_activity,
          created_at: agent.created_at,
          performance_metrics: {
            uptime: 100, // Default values
            throughput: 0,
            error_rate: 0,
            success_rate: agent.total_tasks_completed > 0 ? 
              (agent.total_tasks_completed / (agent.total_tasks_completed + agent.total_tasks_failed)) * 100 : 100
          },
          resource_usage: {
            cpu_percent: 0,
            memory_mb: 0,
            gpu_percent: 0
          }
        }));
        setAgents(convertedAgents);
      } else {
        throw new Error(agentsData.message || 'Failed to load agents');
      }

      if (metricsData.success) {
        setSystemMetrics(metricsData.data);
      } else if (supabaseConfigured && supabaseHealthSummary) {
        // Fallback to Supabase health summary
        const fallbackMetrics: SystemMetrics = {
          agents: {
            total: supabaseHealthSummary.total_agents,
            idle: supabaseHealthSummary.total_agents - supabaseHealthSummary.busy_agents - supabaseHealthSummary.error_agents,
            busy: supabaseHealthSummary.busy_agents,
            error: supabaseHealthSummary.error_agents,
            utilization_rate: supabaseHealthSummary.total_agents > 0 ? 
              (supabaseHealthSummary.busy_agents / supabaseHealthSummary.total_agents) * 100 : 0
          },
          tasks: {
            total: 0, // Would need additional data from Supabase
            completed: 0,
            failed: 0,
            running: 0,
            queued: 0,
            success_rate: supabaseHealthSummary.success_rate
          },
          system: {
            status: supabaseHealthSummary.total_agents > 0 && supabaseHealthSummary.error_agents === 0 ? 'healthy' : 
                   supabaseHealthSummary.error_agents > 0 ? 'error' : 'degraded',
            uptime: '99.9%', // Default value
            last_updated: new Date().toISOString()
          }
        };
        setSystemMetrics(fallbackMetrics);
      } else {
        throw new Error(metricsData.message || 'Failed to load system metrics');
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
      console.error('Error loading agent data:', err);
    } finally {
      setLoading(false);
    }
  }, [getAgentsStatus, getSystemMetrics, supabaseConfigured, supabaseAgents, supabaseHealthSummary]);

  // Handle Pusher events
  const handleAgentUpdate = useCallback((data: any) => {
    const { agent_id, event_type, data: eventData } = data;
    
    setAgents(prev => prev.map(agent => {
      if (agent.agent_id === agent_id) {
        // Update agent based on event type
        switch (event_type) {
          case 'agent_idle':
            return { ...agent, status: 'idle' as const };
          case 'agent_busy':
            return { ...agent, status: 'busy' as const };
          case 'agent_error':
            return { ...agent, status: 'error' as const };
          case 'task_started':
            return { 
              ...agent, 
              status: 'busy' as const, 
              current_task_id: eventData.task_id 
            };
          case 'task_completed':
            return { 
              ...agent, 
              status: 'idle' as const, 
              current_task_id: undefined,
              total_tasks_completed: agent.total_tasks_completed + 1,
              average_execution_time: eventData.execution_time || agent.average_execution_time
            };
          case 'task_failed':
            return { 
              ...agent, 
              status: 'idle' as const, 
              current_task_id: undefined,
              total_tasks_failed: agent.total_tasks_failed + 1
            };
          default:
            return agent;
        }
      }
      return agent;
    }));
  }, []);

  const handleMetricsUpdate = useCallback((data: any) => {
    const { metrics } = data;
    setSystemMetrics(metrics);
  }, []);

  const handleHealthUpdate = useCallback((data: any) => {
    const { health } = data;
    setSystemMetrics(prev => prev ? { ...prev, system: health.system } : null);
  }, []);

  // Setup Pusher subscriptions
  useEffect(() => {
    if (!isConnected) return;

    const subscriptionIds: string[] = [];

    // Subscribe to agent updates
    subscriptionIds.push(pusher.subscribe('agent-updates', (message) => {
      if (message.type?.includes('agent.') || message.type?.includes('task.')) {
        handleAgentUpdate(message.payload);
      }
    }));

    // Subscribe to metrics updates
    subscriptionIds.push(pusher.subscribe('agent-metrics', (message) => {
      if (message.type === 'metrics.updated') {
        handleMetricsUpdate(message.payload);
      }
    }));

    subscriptionIds.push(pusher.subscribe('system-health', (message) => {
      if (message.type === 'health.updated') {
        handleHealthUpdate(message.payload);
      }
    }));

    return () => {
      subscriptionIds.forEach(id => pusher.unsubscribe(id));
    };
  }, [
    isConnected,
    pusher,
    handleAgentUpdate,
    handleMetricsUpdate,
    handleHealthUpdate
  ]);

  // Auto-refresh data
  useEffect(() => {
    loadData();
    
    if (autoRefresh) {
      const interval = setInterval(loadData, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [loadData, autoRefresh]);

  // Computed values
  const agentsByType = useMemo(() => {
    return agents.reduce((acc, agent) => {
      if (!acc[agent.agent_type]) {
        acc[agent.agent_type] = [];
      }
      acc[agent.agent_type].push(agent);
      return acc;
    }, {} as Record<string, AgentStatus[]>);
  }, [agents]);

  const healthyAgents = useMemo(() => 
    agents.filter(a => !['error', 'offline'].includes(a.status)).length
  , [agents]);

  // Handlers
  const handleRefresh = useCallback(() => {
    loadData();
  }, [loadData]);

  const handleAgentClick = useCallback((agent: AgentStatus) => {
    setSelectedAgent(agent);
  }, []);

  const handleTaskExecute = useCallback((agent: AgentStatus) => {
    setSelectedAgent(agent);
    setTaskDialogOpen(true);
  }, []);

  const handleShowMetrics = useCallback(() => {
    setMetricsDialogOpen(true);
  }, []);

  if (loading && agents.length === 0) {
    return (
      <Container size="xl" p="md">
        <Title order={2} mb="lg">
          Agent Dashboard
        </Title>
        <SimpleGrid cols={{ base: 1, sm: 2, md: 3, lg: 4 }} spacing="md">
          {[1, 2, 3, 4].map(i => (
            <Card key={i} padding="md" withBorder>
              <Stack gap="sm">
                <Skeleton height={20} width="60%" />
                <Skeleton height={60} />
                <Skeleton height={16} width="40%" />
              </Stack>
            </Card>
          ))}
        </SimpleGrid>
      </Container>
    );
  }

  return (
    <Container size="xl" p="md">
      {/* Header */}
      <Flex justify="space-between" align="center" mb="lg">
        <Title order={2}>
          Agent Dashboard
        </Title>
        <Group gap="sm">
          <SystemHealthIndicator
            status={systemMetrics?.system.status || 'error'}
            isConnected={isConnected}
          />
          <Button
            variant="outline"
            leftSection={<IconChartBar size={16} />}
            onClick={handleShowMetrics}
          >
            Metrics
          </Button>
          <Button
            variant="outline"
            leftSection={<IconRefresh size={16} />}
            onClick={handleRefresh}
            disabled={apiLoading}
          >
            Refresh
          </Button>
        </Group>
      </Flex>

      {/* Error Alert */}
      {error && (
        <Alert color="red" onClose={() => setError(null)} withCloseButton mb="lg">
          {error}
        </Alert>
      )}

      {/* System Overview Cards */}
      {systemMetrics && (
        <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} spacing="md" mb="xl">
          <Card padding="md" withBorder>
            <Stack gap="xs">
              <Group gap="xs">
                <IconCpu color="var(--mantine-color-blue-6)" />
                <Text size="lg" fw={600}>Total Agents</Text>
              </Group>
              <Text size="xl" fw={700} c="blue">
                {systemMetrics.agents.total}
              </Text>
              <Text size="sm" c="dimmed">
                {healthyAgents} healthy
              </Text>
            </Stack>
          </Card>

          <Card padding="md" withBorder>
            <Stack gap="xs">
              <Group gap="xs">
                <IconBolt color="var(--mantine-color-green-6)" />
                <Text size="lg" fw={600}>Utilization</Text>
              </Group>
              <Text size="xl" fw={700} c="green">
                {systemMetrics.agents.utilization_rate.toFixed(1)}%
              </Text>
              <Progress
                value={systemMetrics.agents.utilization_rate}
                color="green"
                size="sm"
                radius="md"
              />
            </Stack>
          </Card>

          <Card padding="md" withBorder>
            <Stack gap="xs">
              <Group gap="xs">
                <IconTrendingUp color="var(--mantine-color-cyan-6)" />
                <Text size="lg" fw={600}>Success Rate</Text>
              </Group>
              <Text size="xl" fw={700} c="cyan">
                {systemMetrics.tasks.success_rate.toFixed(1)}%
              </Text>
              <Text size="sm" c="dimmed">
                {systemMetrics.tasks.completed} completed
              </Text>
            </Stack>
          </Card>

          <Card padding="md" withBorder>
            <Stack gap="xs">
              <Group gap="xs">
                <IconClock color="var(--mantine-color-orange-6)" />
                <Text size="lg" fw={600}>Queue</Text>
              </Group>
              <Text size="xl" fw={700} c="orange">
                {systemMetrics.tasks.queued}
              </Text>
              <Text size="sm" c="dimmed">
                {systemMetrics.tasks.running} running
              </Text>
            </Stack>
          </Card>
        </SimpleGrid>
      )}

      {/* Agents Grid */}
      <Title order={3} mb="md">
        Active Agents
      </Title>

      {agents.length === 0 ? (
        <Alert color="blue">
          No agents are currently registered. The agent service may be starting up.
        </Alert>
      ) : (
        <SimpleGrid cols={{ base: 1, sm: 2, md: 3, lg: 4 }} spacing="md">
          {agents.map(agent => (
            <AgentCard
              key={agent.agent_id}
              agent={agent}
              onAgentClick={handleAgentClick}
              onTaskExecute={handleTaskExecute}
              getStatusColor={getStatusColor}
              getStatusIcon={getStatusIcon}
            />
          ))}
        </SimpleGrid>
      )}

      {/* Agents by Type */}
      {Object.keys(agentsByType).length > 1 && (
        <Box mt="xl">
          <Title order={3} mb="md">
            Agents by Type
          </Title>
          <Stack gap="md">
            {Object.entries(agentsByType).map(([type, typeAgents]) => (
              <Card key={type} padding="md" withBorder>
                <Stack gap="md">
                  <Group gap="sm">
                    <Text size="lg" fw={600}>
                      {type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </Text>
                    <Badge size="sm" variant="light">
                      {typeAgents.length}
                    </Badge>
                  </Group>
                  <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="sm">
                    {typeAgents.map(agent => (
                      <Box
                        key={agent.agent_id}
                        p="sm"
                        style={{
                          border: '1px solid var(--mantine-color-gray-3)',
                          borderRadius: 'var(--mantine-radius-sm)',
                          display: 'flex',
                          alignItems: 'center'
                        }}
                      >
                        <Indicator
                          color={getStatusColor(agent.status)}
                          size={8}
                          mr="sm"
                        >
                          {getStatusIcon(agent.status)}
                        </Indicator>
                        <Box style={{ flexGrow: 1 }}>
                          <Text size="sm" lineClamp={1}>
                            {agent.agent_id}
                          </Text>
                          <Text size="xs" c="dimmed">
                            {agent.total_tasks_completed} tasks
                          </Text>
                        </Box>
                        <Tooltip label="Execute Task">
                          <ActionIcon
                            size="sm"
                            variant="subtle"
                            onClick={() => handleTaskExecute(agent)}
                            disabled={agent.status !== 'idle'}
                          >
                            <IconPlayerPlay size={16} />
                          </ActionIcon>
                        </Tooltip>
                      </Box>
                    ))}
                  </SimpleGrid>
                </Stack>
              </Card>
            ))}
          </Stack>
        </Box>
      )}

      {/* Task Execution Dialog */}
      <AgentTaskDialog
        open={taskDialogOpen}
        onClose={() => setTaskDialogOpen(false)}
        agent={selectedAgent}
        onExecute={executeTask}
      />

      {/* Metrics Dialog */}
      <AgentMetricsPanel
        open={metricsDialogOpen}
        onClose={() => setMetricsDialogOpen(false)}
        systemMetrics={systemMetrics}
        agents={agents}
      />
    </Container>
  );
};

export default AgentDashboard;
