/**
 * Task Progress List Component
 *
 * Displays a list of Celery background tasks with real-time progress updates.
 */

import { Stack, Text, Group, Badge, ActionIcon, Card, Divider, ScrollArea, Box, Button } from '@mantine/core';
import { IconRefresh, IconTrash, IconChevronDown, IconChevronUp } from '@tabler/icons-react';
import { useMantineTheme } from '@mantine/core';
import { useState } from 'react';
import { TaskProgressCard } from './TaskProgressCard';
import type { CeleryTaskProgress } from '../../hooks/pusher/useCeleryTaskProgress';

export interface TaskProgressListProps {
  tasks: CeleryTaskProgress[];
  onRetry?: (taskId: string) => void;
  onRemove?: (taskId: string) => void;
  onClearCompleted?: () => void;
  maxHeight?: number;
  showCompact?: boolean;
  title?: string;
}

/**
 * List component for displaying multiple Celery task progresses
 */
export function TaskProgressList({
  tasks,
  onRetry,
  onRemove,
  onClearCompleted,
  maxHeight = 600,
  showCompact = false,
  title = 'Background Tasks'
}: TaskProgressListProps) {
  const theme = useMantineTheme();
  const [collapsed, setCollapsed] = useState(false);

  const activeTasks = tasks.filter(t => t.status === 'processing' || t.status === 'queued');
  const completedTasks = tasks.filter(t => t.status === 'completed');
  const failedTasks = tasks.filter(t => t.status === 'failed');

  const getStatusCounts = () => ({
    active: activeTasks.length,
    completed: completedTasks.length,
    failed: failedTasks.length,
    total: tasks.length
  });

  const counts = getStatusCounts();

  if (tasks.length === 0) {
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
        <Text color="dimmed" align="center" py="xl">
          No background tasks running
        </Text>
      </Card>
    );
  }

  return (
    <Card
      shadow="md"
      padding="lg"
      radius="md"
      withBorder
      style={{
        background: theme.colors.dark[7],
        borderColor: theme.colors.dark[5]
      }}
    >
      {/* Header */}
      <Group position="apart" mb="md">
        <Group spacing="md">
          <Text size="xl" fw={700} color="white">
            {title}
          </Text>
          <Badge color="gray" variant="filled">
            {counts.total}
          </Badge>
        </Group>
        <Group spacing="xs">
          {counts.active > 0 && (
            <Badge color="blue" variant="light">
              {counts.active} active
            </Badge>
          )}
          {counts.completed > 0 && (
            <Badge color="green" variant="light">
              {counts.completed} completed
            </Badge>
          )}
          {counts.failed > 0 && (
            <Badge color="red" variant="light">
              {counts.failed} failed
            </Badge>
          )}
          <ActionIcon
            variant="subtle"
            color="gray"
            onClick={() => setCollapsed(!collapsed)}
            title={collapsed ? 'Expand' : 'Collapse'}
          >
            {collapsed ? <IconChevronDown size={18} /> : <IconChevronUp size={18} />}
          </ActionIcon>
        </Group>
      </Group>

      {!collapsed && (
        <>
          <Divider mb="md" color={theme.colors.dark[5]} />

          {/* Actions */}
          {(completedTasks.length > 0 || failedTasks.length > 0) && (
            <Group position="right" mb="md">
              {onClearCompleted && completedTasks.length > 0 && (
                <Button
                  variant="subtle"
                  color="gray"
                  size="xs"
                  onClick={onClearCompleted}
                  leftIcon={<IconTrash size={14} />}
                >
                  Clear Completed
                </Button>
              )}
            </Group>
          )}

          {/* Task List */}
          <ScrollArea style={{ maxHeight }}>
            <Stack spacing="md">
              {/* Active Tasks */}
              {activeTasks.length > 0 && (
                <>
                  <Text size="sm" fw={600} color="dimmed" tt="uppercase">
                    Active Tasks
                  </Text>
                  {activeTasks.map(task => (
                    <Box key={task.taskId} pos="relative">
                      <TaskProgressCard
                        task={task}
                        compact={showCompact}
                        showActions={false}
                      />
                      {onRemove && (
                        <ActionIcon
                          color="red"
                          variant="subtle"
                          size="sm"
                          onClick={() => onRemove(task.taskId)}
                          style={{
                            position: 'absolute',
                            top: 8,
                            right: 8
                          }}
                          title="Remove task"
                        >
                          <IconTrash size={14} />
                        </ActionIcon>
                      )}
                    </Box>
                  ))}
                </>
              )}

              {/* Failed Tasks */}
              {failedTasks.length > 0 && (
                <>
                  {activeTasks.length > 0 && <Divider color={theme.colors.dark[5]} />}
                  <Text size="sm" fw={600} color="red" tt="uppercase">
                    Failed Tasks
                  </Text>
                  {failedTasks.map(task => (
                    <Box key={task.taskId} pos="relative">
                      <TaskProgressCard
                        task={task}
                        compact={showCompact}
                        onRetry={onRetry ? () => onRetry(task.taskId) : undefined}
                      />
                      {onRemove && (
                        <ActionIcon
                          color="red"
                          variant="subtle"
                          size="sm"
                          onClick={() => onRemove(task.taskId)}
                          style={{
                            position: 'absolute',
                            top: 8,
                            right: 8
                          }}
                          title="Remove task"
                        >
                          <IconTrash size={14} />
                        </ActionIcon>
                      )}
                    </Box>
                  ))}
                </>
              )}

              {/* Completed Tasks */}
              {completedTasks.length > 0 && (
                <>
                  {(activeTasks.length > 0 || failedTasks.length > 0) && (
                    <Divider color={theme.colors.dark[5]} />
                  )}
                  <Text size="sm" fw={600} color="green" tt="uppercase">
                    Completed Tasks
                  </Text>
                  {completedTasks.map(task => (
                    <Box key={task.taskId} pos="relative">
                      <TaskProgressCard
                        task={task}
                        compact={showCompact}
                        showActions={false}
                      />
                      {onRemove && (
                        <ActionIcon
                          color="red"
                          variant="subtle"
                          size="sm"
                          onClick={() => onRemove(task.taskId)}
                          style={{
                            position: 'absolute',
                            top: 8,
                            right: 8
                          }}
                          title="Remove task"
                        >
                          <IconTrash size={14} />
                        </ActionIcon>
                      )}
                    </Box>
                  ))}
                </>
              )}
            </Stack>
          </ScrollArea>
        </>
      )}
    </Card>
  );
}

export default TaskProgressList;
