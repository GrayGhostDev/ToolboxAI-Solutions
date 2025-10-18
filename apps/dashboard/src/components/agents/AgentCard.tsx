/**
 * Agent Card Component
 *
 * Individual agent status card with real-time updates and actions.
 *
 * @author ToolboxAI Team
 * @created 2025-09-21
 * @version 1.0.0
 */

import React from 'react';
import {
  Card,
  Text,
  Badge,
  Button,
  Box,
  Progress,
  Tooltip,
  ActionIcon,
  Indicator,
  Group,
  Stack,
  Flex,
} from '@mantine/core';
import {
  IconPlayerPlay,
  IconSettings,
  IconChartBar,
  IconCpu,
  IconBolt,
} from '@tabler/icons-react';

interface AgentStatus {
  agent_id: string;
  agent_type: string;
  status: string;
  current_task_id?: string;
  total_tasks_completed: number;
  total_tasks_failed: number;
  average_execution_time: number;
  last_activity: string;
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

interface AgentCardProps {
  agent: AgentStatus;
  onAgentClick: (agent: AgentStatus) => void;
  onTaskExecute: (agent: AgentStatus) => void;
  getStatusColor: (status: string) => string;
  getStatusIcon: (status: string) => React.ReactNode;
}

export const AgentCard = ({
  agent,
  onAgentClick,
  onTaskExecute,
  getStatusColor,
  getStatusIcon,
}: AgentCardProps) => {
  const formatAgentType = (type: string) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const formatLastActivity = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return `${Math.floor(diffMins / 1440)}d ago`;
  };

  const getResourceColor = (percent: number) => {
    if (percent < 50) return 'success';
    if (percent < 80) return 'warning';
    return 'error';
  };

  return (
    <Card
      padding="md"
      radius="md"
      withBorder
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        cursor: 'pointer',
        transition: 'all 0.2s ease-in-out'
      }}
      onClick={() => onAgentClick(agent)}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.12)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      <Stack style={{ flexGrow: 1 }} gap="md">
        {/* Header */}
        <Flex justify="space-between" align="flex-start">
          <Box>
            <Text size="lg" fw={600} lineClamp={1}>
              {formatAgentType(agent.agent_type)}
            </Text>
            <Text size="sm" c="dimmed" lineClamp={1}>
              {agent.agent_id}
            </Text>
          </Box>
          <Indicator
            color={getStatusColor(agent.status)}
            size={8}
            offset={2}
          >
            {getStatusIcon(agent.status)}
          </Indicator>
        </Flex>

        {/* Status */}
        <Box>
          <Badge
            color={getStatusColor(agent.status)}
            size="sm"
            style={{ marginBottom: 4 }}
          >
            {agent.status.toUpperCase()}
          </Badge>
          {agent.current_task_id && (
            <Text size="xs" c="dimmed">
              Running: {agent.current_task_id.substring(0, 8)}...
            </Text>
          )}
        </Box>

        {/* Performance Stats */}
        <Box>
          <Flex justify="space-between" style={{ marginBottom: 4 }}>
            <Text size="sm">
              Tasks: {agent.total_tasks_completed}
            </Text>
            <Text size="sm" c={agent.total_tasks_failed > 0 ? 'red' : 'dimmed'}>
              Failed: {agent.total_tasks_failed}
            </Text>
          </Flex>

          <Flex justify="space-between" style={{ marginBottom: 4 }}>
            <Text size="sm">
              Success Rate: {agent.performance_metrics.success_rate.toFixed(1)}%
            </Text>
            <Text size="sm">
              Avg Time: {agent.average_execution_time.toFixed(1)}s
            </Text>
          </Flex>
        </Box>

        {/* Resource Usage */}
        <Box>
          <Text size="sm" fw={500} style={{ marginBottom: 8 }}>
            Resource Usage
          </Text>

          <Box style={{ marginBottom: 8 }}>
            <Flex justify="space-between" align="center" style={{ marginBottom: 4 }}>
              <Text size="xs">CPU</Text>
              <Text size="xs">{agent.resource_usage.cpu_percent.toFixed(1)}%</Text>
            </Flex>
            <Progress
              value={agent.resource_usage.cpu_percent}
              color={getResourceColor(agent.resource_usage.cpu_percent)}
              size="sm"
              radius="md"
            />
          </Box>

          <Box style={{ marginBottom: 8 }}>
            <Flex justify="space-between" align="center" style={{ marginBottom: 4 }}>
              <Text size="xs">Memory</Text>
              <Text size="xs">{agent.resource_usage.memory_mb}MB</Text>
            </Flex>
            <Progress
              value={Math.min((agent.resource_usage.memory_mb / 1024) * 100, 100)}
              color={getResourceColor((agent.resource_usage.memory_mb / 1024) * 100)}
              size="sm"
              radius="md"
            />
          </Box>
        </Box>

        {/* Last Activity */}
        <Text size="xs" c="dimmed">
          Last activity: {formatLastActivity(agent.last_activity)}
        </Text>
      </Stack>

      <Flex justify="space-between" align="center" style={{ marginTop: 'auto', paddingTop: 12 }}>
        <Group gap="xs">
          <Tooltip label="View Metrics">
            <ActionIcon size="sm" variant="subtle" onClick={(e) => { e.stopPropagation(); /* Handle metrics view */ }}>
              <IconChartBar size={16} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label="Settings">
            <ActionIcon size="sm" variant="subtle" onClick={(e) => { e.stopPropagation(); /* Handle settings */ }}>
              <IconSettings size={16} />
            </ActionIcon>
          </Tooltip>
        </Group>

        <Button
          variant="filled"
          size="xs"
          leftSection={<IconPlayerPlay size={14} />}
          disabled={agent.status !== 'idle'}
          onClick={(e) => {
            e.stopPropagation();
            onTaskExecute(agent);
          }}
        >
          Execute
        </Button>
      </Flex>
    </Card>
  );
};

export default AgentCard;
