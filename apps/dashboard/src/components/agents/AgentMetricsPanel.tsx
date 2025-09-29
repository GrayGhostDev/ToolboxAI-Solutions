/**
 * Agent Metrics Panel Component
 * 
 * Comprehensive metrics display for agent system performance monitoring.
 * 
 * @author ToolboxAI Team
 * @created 2025-09-21
 * @version 1.0.0
 */

import React from 'react';
import {
  Modal,
  Button,
  SimpleGrid,
  Card,
  Text,
  Box,
  List,
  Progress,
  Badge,
  Table,
  Stack,
  Group,
  Flex,
  Title,
} from '@mantine/core';
import {
  IconX,
  IconTrendingUp,
  IconBolt,
  IconCpu,
  IconCircleCheck,
  IconAlertTriangle,
} from '@tabler/icons-react';

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
    status: string;
    uptime: string;
    last_updated: string;
  };
}

interface AgentStatus {
  agent_id: string;
  agent_type: string;
  status: string;
  total_tasks_completed: number;
  total_tasks_failed: number;
  average_execution_time: number;
  performance_metrics: {
    success_rate: number;
    error_rate: number;
    throughput: number;
    uptime: number;
  };
  resource_usage: {
    cpu_percent: number;
    memory_mb: number;
    gpu_percent: number;
  };
}

interface AgentMetricsPanelProps {
  open: boolean;
  onClose: () => void;
  systemMetrics: SystemMetrics | null;
  agents: AgentStatus[];
}

export const AgentMetricsPanel = ({
  open,
  onClose,
  systemMetrics,
  agents,
}: AgentMetricsPanelProps) => {
  const formatUptime = (uptime: number) => {
    return `${uptime.toFixed(1)}%`;
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
    return `${(seconds / 3600).toFixed(1)}h`;
  };

  const getPerformanceColor = (value: number, threshold: number = 80) => {
    if (value >= threshold) return 'success';
    if (value >= threshold * 0.7) return 'warning';
    return 'error';
  };

  return (
    <Modal
      opened={open}
      onClose={onClose}
      size="xl"
      title={
        <Flex justify="space-between" align="center" w="100%">
          <Title order={4}>Agent System Metrics</Title>
          <Text size="sm" c="dimmed">
            Last updated: {systemMetrics?.system.last_updated ?
              new Date(systemMetrics.system.last_updated).toLocaleString() : 'Never'}
          </Text>
        </Flex>
      }
      styles={{
        content: { height: '80vh' },
        body: { height: 'calc(100% - 60px)', overflow: 'auto' }
      }}
    >
      {!systemMetrics ? (
        <Text>No metrics data available</Text>
      ) : (
        <Stack spacing="lg">
          {/* System Overview */}
          <Card padding="md" withBorder>
            <Title order={5} mb="md">
              System Overview
            </Title>
            <SimpleGrid cols={{ base: 2, md: 4 }} spacing="md">
              <Box ta="center">
                <Text size="xl" fw={700} c="blue">
                  {systemMetrics.agents.total}
                </Text>
                <Text size="sm" c="dimmed">
                  Total Agents
                </Text>
              </Box>
              <Box ta="center">
                <Text size="xl" fw={700} c="green">
                  {systemMetrics.agents.utilization_rate.toFixed(1)}%
                </Text>
                <Text size="sm" c="dimmed">
                  Utilization
                </Text>
              </Box>
              <Box ta="center">
                <Text size="xl" fw={700} c="cyan">
                  {systemMetrics.tasks.success_rate.toFixed(1)}%
                </Text>
                <Text size="sm" c="dimmed">
                  Success Rate
                </Text>
              </Box>
              <Box ta="center">
                <Text size="xl" fw={700} c="orange">
                  {systemMetrics.tasks.queued}
                </Text>
                <Text size="sm" c="dimmed">
                  Queued Tasks
                </Text>
              </Box>
            </SimpleGrid>
          </Card>

          {/* Agent Status and Task Statistics */}
          <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
            {/* Agent Status Breakdown */}
            <Card padding="md" withBorder>
              <Title order={5} mb="md">
                Agent Status Breakdown
              </Title>
              <Stack spacing="sm">
                <Group justify="space-between">
                  <Box>
                    <Text fw={500}>Idle: {systemMetrics.agents.idle}</Text>
                    <Text size="sm" c="dimmed">Available for tasks</Text>
                  </Box>
                  <Badge
                    leftSection={<IconCircleCheck size={14} />}
                    color="green"
                    size="sm"
                  >
                    {systemMetrics.agents.idle}
                  </Badge>
                </Group>
                <Group justify="space-between">
                  <Box>
                    <Text fw={500}>Busy: {systemMetrics.agents.busy}</Text>
                    <Text size="sm" c="dimmed">Currently processing tasks</Text>
                  </Box>
                  <Badge
                    leftSection={<IconBolt size={14} />}
                    color="blue"
                    size="sm"
                  >
                    {systemMetrics.agents.busy}
                  </Badge>
                </Group>
                <Group justify="space-between">
                  <Box>
                    <Text fw={500}>Error: {systemMetrics.agents.error}</Text>
                    <Text size="sm" c="dimmed">Agents with errors</Text>
                  </Box>
                  <Badge
                    leftSection={<IconAlertTriangle size={14} />}
                    color="red"
                    size="sm"
                  >
                    {systemMetrics.agents.error}
                  </Badge>
                </Group>
              </Stack>
            </Card>

            {/* Task Statistics */}
            <Card padding="md" withBorder>
              <Title order={5} mb="md">
                Task Statistics
              </Title>
              <Stack spacing="sm">
                <Group justify="space-between">
                  <Text fw={500}>Completed: {systemMetrics.tasks.completed}</Text>
                  <Text size="sm" c="dimmed">Successfully completed tasks</Text>
                </Group>
                <Group justify="space-between">
                  <Text fw={500}>Failed: {systemMetrics.tasks.failed}</Text>
                  <Text size="sm" c="dimmed">Failed task executions</Text>
                </Group>
                <Group justify="space-between">
                  <Text fw={500}>Running: {systemMetrics.tasks.running}</Text>
                  <Text size="sm" c="dimmed">Currently executing</Text>
                </Group>
                <Group justify="space-between">
                  <Text fw={500}>Queued: {systemMetrics.tasks.queued}</Text>
                  <Text size="sm" c="dimmed">Waiting for execution</Text>
                </Group>
              </Stack>
            </Card>
          </SimpleGrid>

          {/* Individual Agent Performance */}
          <Card padding="md" withBorder>
            <Title order={5} mb="md">
              Individual Agent Performance
            </Title>
            <Table.ScrollContainer minWidth={800}>
              <Table>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Agent ID</Table.Th>
                    <Table.Th>Type</Table.Th>
                    <Table.Th>Status</Table.Th>
                    <Table.Th ta="right">Tasks</Table.Th>
                    <Table.Th ta="right">Success Rate</Table.Th>
                    <Table.Th ta="right">Avg Time</Table.Th>
                    <Table.Th ta="right">CPU</Table.Th>
                    <Table.Th ta="right">Memory</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {agents.map((agent) => (
                    <Table.Tr key={agent.agent_id}>
                      <Table.Td>
                        <Text size="sm" lineClamp={1}>
                          {agent.agent_id.substring(0, 12)}...
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm">
                          {agent.agent_type.replace(/_/g, ' ')}
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <Badge
                          color={
                            agent.status === 'idle' ? 'green' :
                            agent.status === 'busy' ? 'blue' :
                            agent.status === 'error' ? 'red' : 'gray'
                          }
                          size="sm"
                        >
                          {agent.status}
                        </Badge>
                      </Table.Td>
                      <Table.Td ta="right">
                        <Box>
                          <Text size="sm">
                            {agent.total_tasks_completed}
                          </Text>
                          {agent.total_tasks_failed > 0 && (
                            <Text size="xs" c="red" component="span" ml="xs">
                              ({agent.total_tasks_failed} failed)
                            </Text>
                          )}
                        </Box>
                      </Table.Td>
                      <Table.Td ta="right">
                        <Text
                          size="sm"
                          c={getPerformanceColor(agent.performance_metrics.success_rate)}
                        >
                          {agent.performance_metrics.success_rate.toFixed(1)}%
                        </Text>
                      </Table.Td>
                      <Table.Td ta="right">
                        <Text size="sm">
                          {formatDuration(agent.average_execution_time)}
                        </Text>
                      </Table.Td>
                      <Table.Td ta="right">
                        <Group spacing="xs" justify="flex-end" style={{ minWidth: 80 }}>
                          <Progress
                            value={agent.resource_usage.cpu_percent}
                            color={getPerformanceColor(100 - agent.resource_usage.cpu_percent)}
                            size="sm"
                            style={{ flex: 1 }}
                          />
                          <Text size="xs">
                            {agent.resource_usage.cpu_percent.toFixed(0)}%
                          </Text>
                        </Group>
                      </Table.Td>
                      <Table.Td ta="right">
                        <Text size="sm">
                          {agent.resource_usage.memory_mb}MB
                        </Text>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Table.ScrollContainer>
          </Card>
        </Stack>
      )}

      {/* Close Button */}
      <Group justify="flex-end" mt="md">
        <Button
          onClick={onClose}
          leftSection={<IconX size={16} />}
          variant="subtle"
        >
          Close
        </Button>
      </Group>
    </Modal>
  );
};

export default AgentMetricsPanel;
