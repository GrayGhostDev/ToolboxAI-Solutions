/**
 * Task Progress Card Component
 *
 * Displays real-time progress for Celery background tasks
 * with Mantine UI styling and Roblox theme integration.
 */

import { Card, Progress, Text, Stack, Group, Badge, Alert, ActionIcon, Box } from '@mantine/core';
import { IconCheck, IconX, IconLoader, IconClock, IconRefresh } from '@tabler/icons-react';
import { useMantineTheme } from '@mantine/core';
import type { CeleryTaskProgress } from '../../hooks/pusher/useCeleryTaskProgress';

export interface TaskProgressCardProps {
  task: CeleryTaskProgress;
  onRetry?: () => void;
  showActions?: boolean;
  compact?: boolean;
}

/**
 * Card component for displaying Celery task progress
 */
export function TaskProgressCard({ task, onRetry, showActions = true, compact = false }: TaskProgressCardProps) {
  const theme = useMantineTheme();

  const getStatusColor = (status: CeleryTaskProgress['status']) => {
    switch (status) {
      case 'completed':
        return 'green';
      case 'failed':
        return 'red';
      case 'processing':
        return 'blue';
      case 'queued':
        return 'gray';
      default:
        return 'gray';
    }
  };

  const getStatusIcon = (status: CeleryTaskProgress['status']) => {
    switch (status) {
      case 'completed':
        return <IconCheck size={20} />;
      case 'failed':
        return <IconX size={20} />;
      case 'processing':
        return <IconLoader size={20} className="animate-spin" />;
      case 'queued':
        return <IconClock size={20} />;
      default:
        return null;
    }
  };

  const formatDuration = (startedAt?: string, completedAt?: string) => {
    if (!startedAt) return null;
    const start = new Date(startedAt);
    const end = completedAt ? new Date(completedAt) : new Date();
    const duration = Math.floor((end.getTime() - start.getTime()) / 1000);

    if (duration < 60) return `${duration}s`;
    if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`;
    return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`;
  };

  if (compact) {
    return (
      <Box
        p="sm"
        style={{
          background: theme.colors.dark[7],
          borderRadius: theme.radius.sm,
          border: `1px solid ${theme.colors.dark[5]}`
        }}
      >
        <Group position="apart" mb="xs">
          <Group spacing="xs">
            {getStatusIcon(task.status)}
            <Text size="sm" fw={600} color={getStatusColor(task.status)}>
              {task.status.toUpperCase()}
            </Text>
          </Group>
          {task.startedAt && (
            <Text size="xs" color="dimmed">
              {formatDuration(task.startedAt, task.completedAt)}
            </Text>
          )}
        </Group>
        {task.status === 'processing' && (
          <Progress
            value={task.progress}
            size="sm"
            color={getStatusColor(task.status)}
            striped
            animate
          />
        )}
        {task.message && (
          <Text size="xs" color="dimmed" mt="xs">
            {task.message}
          </Text>
        )}
      </Box>
    );
  }

  return (
    <Card
      shadow="sm"
      padding="lg"
      radius="md"
      withBorder
      style={{
        background: theme.colors.dark[7],
        borderColor: theme.colors.dark[5]
      }}
    >
      <Stack spacing="md">
        {/* Header */}
        <Group position="apart">
          <Group spacing="md">
            {getStatusIcon(task.status)}
            <div>
              <Text size="lg" fw={700} color="white">
                Task Progress
              </Text>
              <Text size="xs" color="dimmed">
                ID: {task.taskId.slice(0, 8)}...
              </Text>
            </div>
          </Group>
          <Badge color={getStatusColor(task.status)} size="lg" variant="filled">
            {task.status.toUpperCase()}
          </Badge>
        </Group>

        {/* Progress Bar */}
        {(task.status === 'processing' || task.status === 'queued') && (
          <div>
            <Group position="apart" mb="xs">
              <Text size="sm" color="dimmed">
                Progress
              </Text>
              <Text size="sm" fw={600} color={theme.colors.cyan[4]}>
                {task.progress}%
              </Text>
            </Group>
            <Progress
              value={task.progress}
              size="lg"
              radius="md"
              color={getStatusColor(task.status)}
              striped={task.status === 'processing'}
              animate={task.status === 'processing'}
              styles={{
                bar: {
                  background: task.status === 'processing'
                    ? `linear-gradient(90deg, ${theme.colors.blue[6]} 0%, ${theme.colors.cyan[5]} 100%)`
                    : undefined
                }
              }}
            />
          </div>
        )}

        {/* Message */}
        {task.message && (
          <Alert
            color={getStatusColor(task.status)}
            variant="light"
            styles={{
              root: {
                backgroundColor: theme.colors.dark[6]
              }
            }}
          >
            <Text size="sm">{task.message}</Text>
          </Alert>
        )}

        {/* Error */}
        {task.error && (
          <Alert icon={<IconX size={16} />} color="red" variant="filled">
            <Text size="sm" fw={600}>Error</Text>
            <Text size="xs" mt="xs">{task.error}</Text>
          </Alert>
        )}

        {/* Duration */}
        {task.startedAt && (
          <Group spacing="xs">
            <Text size="xs" color="dimmed">
              Duration:
            </Text>
            <Text size="xs" fw={600} color={theme.colors.cyan[4]}>
              {formatDuration(task.startedAt, task.completedAt)}
            </Text>
          </Group>
        )}

        {/* Actions */}
        {showActions && task.status === 'failed' && onRetry && (
          <Group position="right">
            <ActionIcon
              color="blue"
              variant="filled"
              size="lg"
              onClick={onRetry}
              title="Retry task"
            >
              <IconRefresh size={18} />
            </ActionIcon>
          </Group>
        )}
      </Stack>
    </Card>
  );
}

export default TaskProgressCard;
