import {
  Button,
  Text,
  Stack,
  Grid,
  ActionIcon,
  Card,
  Group,
  TextInput,
  Badge,
  Loader,
  Menu,
  Table,
} from '@mantine/core';

// Type assertion helper for Mantine compound components
const GridCol = Grid.Col as any;
const CardSection = Card.Section as any;
const TableThead = Table.Thead as any;
const TableTbody = Table.Tbody as any;
const TableTr = Table.Tr as any;
const TableTh = Table.Th as any;
const TableTd = Table.Td as any;
const MenuTarget = Menu.Target as any;
const MenuDropdown = Menu.Dropdown as any;
const MenuItem = Menu.Item as any;
import {
  IconSearch,
  IconPlus,
  IconDotsVertical,
  IconEye,
  IconEdit,
  IconTrash,
  IconRocket,
  IconCopy,
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

export default function Lessons() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = React.useState('');
  const [createDialogOpen, setCreateDialogOpen] = React.useState(false);
  const [showTaskPanel, setShowTaskPanel] = React.useState(false);

  // Get organization ID from user context (fallback to default for demo)
  const organizationId = 'default_org'; // TODO: Get from auth context

  // Track all Celery tasks for this organization
  const { tasks, removeTask, activeTasks, completedTasks } =
    useMultipleCeleryTasks(organizationId);

  // Show task panel when there are active tasks
  React.useEffect(() => {
    if (activeTasks.length > 0) {
      setShowTaskPanel(true);
    }
  }, [activeTasks.length]);

  // Use the API hook for fetching lessons
  const {
    data: lessonsData,
    loading,
    error,
    execute: refetchLessons,
  } = useApiCallOnMount(() => listLessons() as any, { mockEndpoint: '/lessons', showNotification: false });

  // Ensure lessons is always an array
  const lessons = React.useMemo(() => {
    if (!lessonsData) return [];
    if (Array.isArray(lessonsData)) return lessonsData;
    // Handle case where API returns data wrapped in an object
    if (
      typeof lessonsData === 'object' &&
      'data' in lessonsData &&
      Array.isArray(lessonsData.data)
    ) {
      return lessonsData.data;
    }
    // Handle case where API returns items array
    if (
      typeof lessonsData === 'object' &&
      'items' in lessonsData &&
      Array.isArray(lessonsData.items)
    ) {
      return lessonsData.items;
    }
    return [];
  }, [lessonsData]);

  // Handle error from the hook
  React.useEffect(() => {
    if (error) {
      const errorDetail = (error as any).response?.data?.detail;
      let errorMessage = 'Failed to load lessons. Please try again.';
      if (typeof errorDetail === 'string') {
        errorMessage = errorDetail;
      } else if (Array.isArray(errorDetail)) {
        errorMessage = errorDetail
          .map((err: any) => err.msg || err.message || 'Validation error')
          .join(', ');
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
      refetchLessons();
    } catch (error) {
      dispatch(
        addNotification({
          type: 'error',
          message: 'Failed to delete lesson',
        })
      );
    }
  };
  const filteredLessons = lessons.filter(
    (lesson: Lesson) =>
      lesson.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      lesson.subject.toLowerCase().includes(searchTerm.toLowerCase())
  );
  // Handle task removal
  const handleRemoveTask = React.useCallback(
    (taskId: string) => {
      removeTask(taskId);
    },
    [removeTask]
  );

  // Handle clear completed tasks
  const handleClearCompleted = React.useCallback(() => {
    completedTasks.forEach((task) => removeTask(task.taskId));
  }, [completedTasks, removeTask]);

  return (
    <Grid gutter="md">
      <GridCol span={12}>
        <Card>
          <CardSection p="md">
            <Group justify="space-between" align="center">
              <Text size="xl" fw={600}>
                Lessons
              </Text>
              <Group gap="sm">
                <TextInput
                  size="sm"
                  placeholder="Search lessons..."
                  value={searchTerm}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.currentTarget.value)}
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
          </CardSection>
        </Card>
      </GridCol>

      {/* Task Progress Panel */}
      {showTaskPanel && tasks.length > 0 && (
        <GridCol span={12}>
          <TaskProgressList
            tasks={tasks}
            onRemove={handleRemoveTask}
            onClearCompleted={handleClearCompleted}
            maxHeight={400}
            showCompact={false}
            title="Content Generation Tasks"
          />
        </GridCol>
      )}
      <GridCol span={12}>
        <Card>
          <Table>
            <TableThead>
              <TableTr>
                <TableTh>Title</TableTh>
                <TableTh>Subject</TableTh>
                <TableTh>Status</TableTh>
                <TableTh>Classes</TableTh>
                <TableTh>Roblox</TableTh>
                <TableTh style={{ textAlign: 'right' }}>Actions</TableTh>
              </TableTr>
            </TableThead>
            <TableTbody>
              {loading ? (
                <TableTr>
                  <TableTd colSpan={6} style={{ textAlign: 'center' }}>
                    <Group justify="center">
                      <Loader size="sm" />
                      <Text>Loading...</Text>
                    </Group>
                  </TableTd>
                </TableTr>
              ) : filteredLessons.length === 0 ? (
                <TableTr>
                  <TableTd colSpan={6} style={{ textAlign: 'center' }}>
                    <Text>No lessons found</Text>
                  </TableTd>
                </TableTr>
              ) : (
                filteredLessons.map((lesson: Lesson) => (
                  <TableTr key={lesson.id}>
                    <TableTd>
                      <Stack gap="xs">
                        <Text size="sm" fw={500}>
                          {lesson.title}
                        </Text>
                        <Text size="xs" c="dimmed">
                          {lesson.description}
                        </Text>
                      </Stack>
                    </TableTd>
                    <TableTd>
                      <Badge size="sm" color="blue" variant="outline">
                        {lesson.subject}
                      </Badge>
                    </TableTd>
                    <TableTd>
                      <Badge size="sm" color={lesson.status === 'published' ? 'green' : 'gray'}>
                        {lesson.status}
                      </Badge>
                    </TableTd>
                    <TableTd>
                      <Text>{lesson.classIds?.length || 0}</Text>
                    </TableTd>
                    <TableTd>
                      {lesson.robloxWorldId ? (
                        <Badge size="sm" color="green" leftSection={<IconRocket size={12} />}>
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
                    </TableTd>
                    <TableTd style={{ textAlign: 'right' }}>
                      <Menu position="bottom-end">
                        <MenuTarget>
                          <ActionIcon size="sm" variant="subtle">
                            <IconDotsVertical size={16} />
                          </ActionIcon>
                        </MenuTarget>
                        <MenuDropdown>
                          <MenuItem
                            leftSection={<IconEye size={16} />}
                            onClick={() => navigate(`/lessons/${lesson.id}`)}
                          >
                            View Details
                          </MenuItem>
                          <MenuItem
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
                          </MenuItem>
                          <MenuItem
                            leftSection={<IconCopy size={16} />}
                            onClick={() => {
                              // TODO: Implement actual duplication API call
                              dispatch(
                                addNotification({
                                  type: 'success',
                                  message: `Lesson "${lesson.title}" duplicated!`,
                                })
                              );
                              refetchLessons();
                            }}
                          >
                            Duplicate
                          </MenuItem>
                          {!lesson.robloxWorldId && (
                            <MenuItem
                              leftSection={<IconRocket size={16} />}
                              onClick={() => handlePushToRoblox(lesson)}
                            >
                              Push to Roblox
                            </MenuItem>
                          )}
                          <MenuItem
                            leftSection={<IconTrash size={16} />}
                            color="red"
                            onClick={() => handleDelete(lesson)}
                          >
                            Delete
                          </MenuItem>
                        </MenuDropdown>
                      </Menu>
                    </TableTd>
                  </TableTr>
                ))
              )}
            </TableTbody>
          </Table>
        </Card>
      </GridCol>
      <CreateLessonDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        onSuccess={refetchLessons}
      />
    </Grid>
  );
}
