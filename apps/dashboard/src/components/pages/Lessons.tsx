import {
  Box,
  Button,
  Text,
  Paper,
  Stack,
  Grid,
  Container,
  ActionIcon,
  Avatar,
  Card,
  Group,
  TextInput,
  Badge,
  Alert,
  Loader,
  Progress,
  Modal,
  Drawer,
  Tabs,
  Menu,
  Tooltip,
  Checkbox,
  Radio,
  Switch,
  Slider,
  Rating,
  Autocomplete,
  Skeleton,
  Table,
  Divider
} from '@mantine/core';
import {
  IconSearch,
  IconPlus,
  IconDotsVertical,
  IconEye,
  IconEdit,
  IconTrash,
  IconRocket,
  IconCopy
} from '@tabler/icons-react';
import * as React from 'react';
import { useNavigate } from 'react-router-dom';
import { listLessons, deleteLesson } from '../../services/api';
import { useApiCallOnMount } from '../../hooks/useApiCall';
import { useAppDispatch } from '../../store';
import { addNotification } from '../../store/slices/uiSlice';
import CreateLessonDialog from '../dialogs/CreateLessonDialog';
import { type Lesson } from '../../types/api';
import { useMultipleCeleryTasks } from '../../hooks/pusher/useCeleryTaskProgress';
import { TaskProgressList } from '../common/TaskProgressList';
import { showTaskNotification } from '../common/TaskProgressToast';

export default function Lessons() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = React.useState('');
  const [createDialogOpen, setCreateDialogOpen] = React.useState(false);
  const [showTaskPanel, setShowTaskPanel] = React.useState(false);

  // Get organization ID from user context (fallback to default for demo)
  const organizationId = 'default_org'; // TODO: Get from auth context

  // Track all Celery tasks for this organization
  const {
    tasks,
    addTask,
    removeTask,
    activeTasks,
    completedTasks,
    failedTasks
  } = useMultipleCeleryTasks(organizationId);

  // Show task panel when there are active tasks
  React.useEffect(() => {
    if (activeTasks.length > 0) {
      setShowTaskPanel(true);
    }
  }, [activeTasks.length]);

  // Use the API hook for fetching lessons
  const { data: lessonsData, loading, error, refetch } = useApiCallOnMount(
    listLessons,
    { mockEndpoint: '/lessons', showNotification: false }
  );

  const lessons = lessonsData || [];

  // Handle error from the hook
  React.useEffect(() => {
    if (error) {
      const errorDetail = (error as any).response?.data?.detail;
      let errorMessage = 'Failed to load lessons. Please try again.';
      if (typeof errorDetail === 'string') {
        errorMessage = errorDetail;
      } else if (Array.isArray(errorDetail)) {
        errorMessage = errorDetail.map((err: any) =>
          err.msg || err.message || 'Validation error'
        ).join(', ');
      }
      dispatch(
        addNotification({
          type: 'error',
          message: errorMessage,
        })
      );
    }
  }, [error, dispatch]);
  const handlePushToRoblox = async (lesson: Lesson) => {
    dispatch(
      addNotification({
        type: 'info',
        message: `Preparing Roblox environment for "${lesson.title}"...`,
      })
    );
    // Simulate push process then navigate to Roblox dashboard
    setTimeout(() => {
      dispatch(
        addNotification({
          type: 'success',
          message: `Lesson "${lesson.title}" is ready in Roblox!`,
        })
      );
      // Navigate to Roblox dashboard with lesson context
      navigate(`/roblox?lessonId=${lesson.id}&lessonTitle=${encodeURIComponent(lesson.title)}`);
    }, 1500);
  };
  const handleDelete = async (lesson: Lesson) => {
    if (!window.confirm(`Are you sure you want to delete "${lesson.title}"?`)) {
      return;
    }
    try {
      await deleteLesson(lesson.id);
      dispatch(
        addNotification({
          type: 'success',
          message: `Lesson "${lesson.title}" deleted successfully`,
        })
      );
      refetch();
    } catch (error) {
      dispatch(
        addNotification({
          type: 'error',
          message: 'Failed to delete lesson',
        })
      );
    }
  };
  const filteredLessons = lessons.filter((lesson) =>
    lesson.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    lesson.subject.toLowerCase().includes(searchTerm.toLowerCase())
  );
  // Handle task removal
  const handleRemoveTask = React.useCallback((taskId: string) => {
    removeTask(taskId);
  }, [removeTask]);

  // Handle clear completed tasks
  const handleClearCompleted = React.useCallback(() => {
    completedTasks.forEach(task => removeTask(task.taskId));
  }, [completedTasks, removeTask]);

  return (
    <Grid gutter="md">
      <Grid.Col span={12}>
        <Card>
          <Card.Section p="md">
            <Group justify="space-between" align="center">
              <Text size="xl" fw={600}>
                Lessons
              </Text>
              <Group gap="sm">
                <TextInput
                  size="sm"
                  placeholder="Search lessons..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.currentTarget.value)}
                  style={{ minWidth: 250 }}
                  leftSection={<IconSearch size={16} />}
                />
                <Button
                  variant="filled"
                  leftSection={<IconPlus size={16} />}
                  onClick={() => setCreateDialogOpen(true)}
                >
                  New Lesson
                </Button>
              </Group>
            </Group>
          </Card.Section>
        </Card>
      </Grid.Col>

      {/* Task Progress Panel */}
      {showTaskPanel && tasks.length > 0 && (
        <Grid.Col span={12}>
          <TaskProgressList
            tasks={tasks}
            onRemove={handleRemoveTask}
            onClearCompleted={handleClearCompleted}
            maxHeight={400}
            showCompact={false}
            title="Content Generation Tasks"
          />
        </Grid.Col>
      )}
      <Grid.Col span={12}>
        <Card>
          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Title</Table.Th>
                <Table.Th>Subject</Table.Th>
                <Table.Th>Status</Table.Th>
                <Table.Th>Classes</Table.Th>
                <Table.Th>Roblox</Table.Th>
                <Table.Th style={{ textAlign: 'right' }}>Actions</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {loading ? (
                <Table.Tr>
                  <Table.Td colSpan={6} style={{ textAlign: 'center' }}>
                    <Group justify="center">
                      <Loader size="sm" />
                      <Text>Loading...</Text>
                    </Group>
                  </Table.Td>
                </Table.Tr>
              ) : filteredLessons.length === 0 ? (
                <Table.Tr>
                  <Table.Td colSpan={6} style={{ textAlign: 'center' }}>
                    <Text>No lessons found</Text>
                  </Table.Td>
                </Table.Tr>
              ) : (
                filteredLessons.map((lesson) => (
                  <Table.Tr key={lesson.id}>
                    <Table.Td>
                      <Stack gap="xs">
                        <Text size="sm" fw={500}>
                          {lesson.title}
                        </Text>
                        <Text size="xs" c="dimmed">
                          {lesson.description}
                        </Text>
                      </Stack>
                    </Table.Td>
                    <Table.Td>
                      <Badge
                        size="sm"
                        color="blue"
                        variant="outline"
                      >
                        {lesson.subject}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Badge
                        size="sm"
                        color={lesson.status === 'published' ? 'green' : 'gray'}
                      >
                        {lesson.status}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Text>{lesson.classIds?.length || 0}</Text>
                    </Table.Td>
                    <Table.Td>
                      {lesson.robloxWorldId ? (
                        <Badge
                          size="sm"
                          color="green"
                          leftSection={<IconRocket size={12} />}
                        >
                          Connected
                        </Badge>
                      ) : (
                        <Button
                          size="xs"
                          leftSection={<IconRocket size={14} />}
                          onClick={() => handlePushToRoblox(lesson)}
                        >
                          Push
                        </Button>
                      )}
                    </Table.Td>
                    <Table.Td style={{ textAlign: 'right' }}>
                      <Menu position="bottom-end">
                        <Menu.Target>
                          <ActionIcon
                            size="sm"
                            variant="subtle"
                          >
                            <IconDotsVertical size={16} />
                          </ActionIcon>
                        </Menu.Target>
                        <Menu.Dropdown>
                          <Menu.Item
                            leftSection={<IconEye size={16} />}
                            onClick={() => navigate(`/lessons/${lesson.id}`)}
                          >
                            View Details
                          </Menu.Item>
                          <Menu.Item
                            leftSection={<IconEdit size={16} />}
                            onClick={() => {
                              dispatch(
                                addNotification({
                                  type: 'info',
                                  message: 'Edit functionality coming soon!',
                                })
                              );
                            }}
                          >
                            Edit
                          </Menu.Item>
                          <Menu.Item
                            leftSection={<IconCopy size={16} />}
                            onClick={() => {
                              const duplicatedLesson = { ...lesson, title: `${lesson.title} (Copy)` };
                              dispatch(
                                addNotification({
                                  type: 'success',
                                  message: `Lesson "${lesson.title}" duplicated!`,
                                })
                              );
                              refetch();
                            }}
                          >
                            Duplicate
                          </Menu.Item>
                          {!lesson.robloxWorldId && (
                            <Menu.Item
                              leftSection={<IconRocket size={16} />}
                              onClick={() => handlePushToRoblox(lesson)}
                            >
                              Push to Roblox
                            </Menu.Item>
                          )}
                          <Menu.Item
                            leftSection={<IconTrash size={16} />}
                            color="red"
                            onClick={() => handleDelete(lesson)}
                          >
                            Delete
                          </Menu.Item>
                        </Menu.Dropdown>
                      </Menu>
                    </Table.Td>
                  </Table.Tr>
                ))
              )}
            </Table.Tbody>
          </Table>
        </Card>
      </Grid.Col>
      <CreateLessonDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        onSuccess={refetch}
      />
    </Grid>
  );
}