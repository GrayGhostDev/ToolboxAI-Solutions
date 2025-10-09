import {
  IconPlus,
  IconClipboardCheck,
  IconFilter,
  IconDots,
  IconRefresh,
} from '@tabler/icons-react';
import {
  Alert,
  Box,
  Button,
  Card,
  Badge,
  Loader,
  Grid,
  ActionIcon,
  Progress,
  Menu,
  Stack,
  Text,
  Group,
  Title,
  Container,
  Center
} from '@mantine/core';
import * as React from 'react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch } from '../../store';
import { addNotification } from '../../store/slices/uiSlice';
import { useApiCall, useApiCallOnMount } from '../../hooks/useApiCall';
import CreateAssessmentDialog from '../dialogs/CreateAssessmentDialog';
import { useMultipleCeleryTasks } from '../../hooks/pusher/useCeleryTaskProgress';
import { TaskProgressList } from '../common/TaskProgressList';

export default function Assessments() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  // State management
  const [filters, setFiltersState] = useState<any>({});
  const [filterAnchorEl, setFilterAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedAssessment, setSelectedAssessment] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [menuAssessment, setMenuAssessment] = useState<any>(null);
  const [showTaskPanel, setShowTaskPanel] = useState(false);

  // Get organization ID from user context (fallback to default for demo)
  const organizationId = 'default_org'; // TODO: Get from auth context

  // Track all Celery tasks for quiz generation
  const {
    tasks,
    addTask,
    removeTask,
    activeTasks,
    completedTasks
  } = useMultipleCeleryTasks(organizationId);

  // Show task panel when there are active tasks
  useEffect(() => {
    if (activeTasks.length > 0) {
      setShowTaskPanel(true);
    }
  }, [activeTasks.length]);

  // Fetch assessments using API hook
  const {
    data: assessmentsData,
    loading: assessmentsLoading,
    error: assessmentsError,
    refetch: refetchAssessments
  } = useApiCallOnMount(
    null,
    { mockEndpoint: '/assessments', showNotification: false }
  );

  // Fetch submissions using API hook
  const {
    data: submissionsData,
    loading: submissionsLoading,
    error: submissionsError,
    refetch: refetchSubmissions
  } = useApiCallOnMount(
    null,
    { mockEndpoint: '/submissions', showNotification: false }
  );

  // API hooks for mutations
  const { execute: deleteAssessmentApi } = useApiCall();

  const assessments = (assessmentsData as any[]) || [];
  const submissions = (submissionsData as any[]) || [];
  const loading = assessmentsLoading || submissionsLoading;
  const error = assessmentsError || submissionsError;

  const handleRefresh = () => {
    refetchAssessments();
    refetchSubmissions();
  };

  const handleFilterChange = (filterType: string, value: any) => {
    const newFilters = { ...filters, [filterType]: value };
    setFiltersState(newFilters);
    // In a real implementation, you'd refetch with filters
    refetchAssessments();
  };

  const handleFilterMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setFilterAnchorEl(event.currentTarget);
  };

  const handleFilterMenuClose = () => {
    setFilterAnchorEl(null);
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, assessment: any) => {
    event.stopPropagation();
    setMenuAnchorEl(event.currentTarget);
    setMenuAssessment(assessment);
  };

  const handleMenuClose = () => {
    setMenuAnchorEl(null);
    setMenuAssessment(null);
  };

  const handleViewAssessment = (assessmentId: string) => {
    navigate(`/assessments/${assessmentId}`);
    handleMenuClose();
  };

  const handleGradeAssessment = (assessmentId: string) => {
    navigate(`/assessments/${assessmentId}/grade`);
    handleMenuClose();
  };

  const handleEditAssessment = (assessmentId: string) => {
    dispatch(
      addNotification({
        type: 'info',
        message: 'Edit functionality coming soon!',
      })
    );
    handleMenuClose();
  };

  const handleDeleteAssessment = async (assessment: any) => {
    if (window.confirm(`Are you sure you want to delete "${assessment.title}"?`)) {
      try {
        await deleteAssessmentApi('DELETE', `/assessments/${assessment.id}`, null);
        dispatch(
          addNotification({
            type: 'success',
            message: `Assessment "${assessment.title}" deleted successfully!`,
          })
        );
        refetchAssessments();
      } catch (error) {
        dispatch(
          addNotification({
            type: 'error',
            message: 'Failed to delete assessment',
          })
        );
      }
    }
    handleMenuClose();
  };

  // Calculate statistics from real data
  const activeAssessments = assessments.filter((a) => a.status === 'active').length;
  const pendingGrading = submissions.filter((s) => !s.gradedAt).length;
  const scoredSubmissions = submissions.filter((s) => s.score !== undefined && s.score !== null);
  const averageScore =
    scoredSubmissions.length > 0
      ? Math.round(
          scoredSubmissions.reduce((acc, s) => acc + (s.score || 0), 0) /
          scoredSubmissions.length
        )
      : 0;
  const completionRate =
    assessments.length > 0
      ? Math.round(
          (assessments.filter((a) => a.submissions >= a.maxSubmissions).length /
            assessments.length) *
            100
        )
      : 0;

  const dueTodayCount = assessments.filter((a) => {
    if (!a.dueDate) return false;
    const dueDate = new Date(a.dueDate);
    const today = new Date();
    return dueDate.toDateString() === today.toDateString();
  }).length;

  if (loading && assessments.length === 0) {
    return (
      <Center style={{ minHeight: 400 }}>
        <Loader size="lg" />
      </Center>
    );
  }

  return (
    <Container size="xl">
      <Grid>
        <Grid.Col span={12}>
          <Card padding="md">
            <Group justify="space-between" align="center">
              <Title order={3} fw={600}>
                Assessments
              </Title>
              <Group gap="xs">
                <ActionIcon onClick={handleRefresh} disabled={loading}>
                  <IconRefresh size={16} />
                </ActionIcon>
                <Menu
                  trigger="click"
                  position="bottom-end"
                  offset={5}
                >
                  <Menu.Target>
                    <ActionIcon>
                      <IconFilter size={16} />
                    </ActionIcon>
                  </Menu.Target>
                  <Menu.Dropdown>
                    <Menu.Item
                      onClick={() => {
                        handleFilterChange('status', 'active');
                      }}
                    >
                      Active Only
                    </Menu.Item>
                    <Menu.Item
                      onClick={() => {
                        handleFilterChange('status', 'draft');
                      }}
                    >
                      Drafts
                    </Menu.Item>
                    <Menu.Item
                      onClick={() => {
                        handleFilterChange('type', 'quiz');
                      }}
                    >
                      Quizzes
                    </Menu.Item>
                    <Menu.Item
                      onClick={() => {
                        handleFilterChange('type', 'test');
                      }}
                    >
                      Tests
                    </Menu.Item>
                    <Menu.Item
                      onClick={() => {
                        handleFilterChange('type', undefined);
                      }}
                    >
                      All Types
                    </Menu.Item>
                  </Menu.Dropdown>
                </Menu>
                <Button
                  leftSection={<IconPlus />}
                  onClick={() => setCreateDialogOpen(true)}
                >
                  Create Assessment
                </Button>
              </Group>
            </Group>
          </Card>
        </Grid.Col>

        {/* Assessment Stats */}
        <Grid.Col span={{ base: 12, md: 3 }}>
          <Card padding="md">
            <Stack gap="xs">
              <Text size="xs" c="dimmed">
                Active Assessments
              </Text>
              <Title order={2} fw={700}>
                {activeAssessments}
              </Title>
              {dueTodayCount > 0 && (
                <Badge size="sm" color="yellow">{dueTodayCount} due today</Badge>
              )}
            </Stack>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 3 }}>
          <Card padding="md">
            <Stack gap="xs">
              <Text size="xs" c="dimmed">
                Pending Grading
              </Text>
              <Title order={2} fw={700}>
                {pendingGrading}
              </Title>
              <Progress
                value={
                  submissions.length > 0
                    ? ((submissions.length - pendingGrading) / submissions.length) * 100
                    : 0
                }
              />
            </Stack>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 3 }}>
          <Card padding="md">
            <Stack gap="xs">
              <Text size="xs" c="dimmed">
                Average Score
              </Text>
              <Title order={2} fw={700}>
                {averageScore}%
              </Title>
              <Text size="xs" c="dimmed">
                Class Average
              </Text>
            </Stack>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 3 }}>
          <Card padding="md">
            <Stack gap="xs">
              <Text size="xs" c="dimmed">
                Completion Rate
              </Text>
              <Title order={2} fw={700}>
                {completionRate}%
              </Title>
              <Progress value={completionRate} color="green" />
            </Stack>
          </Card>
        </Grid.Col>

        {/* Task Progress Panel */}
        {showTaskPanel && tasks.length > 0 && (
          <Grid.Col span={12}>
            <TaskProgressList
              tasks={tasks}
              onRemove={removeTask}
              onClearCompleted={() => {
                completedTasks.forEach(task => removeTask(task.taskId));
              }}
              maxHeight={400}
              showCompact={false}
              title="Quiz Generation Tasks"
            />
          </Grid.Col>
        )}

        {/* Recent Assessments */}
        <Grid.Col span={12}>
          <Card padding="md">
            <Title order={4} mb="md" fw={600}>
              Recent Assessments
            </Title>
            {error && (
              <Alert color="red" onClose={() => dispatch(clearError())} mb="md">
                {error}
              </Alert>
            )}
            <Stack gap="md">
              {assessments.length === 0 ? (
                <Text c="dimmed" ta="center" py="xl">
                  No assessments found. Create your first assessment to get started.
                </Text>
              ) : (
                assessments.slice(0, 5).map((assessment) => (
                  <Box
                    key={assessment.id}
                    p="md"
                    style={{
                      borderRadius: 8,
                      backgroundColor: 'var(--mantine-color-gray-0)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                    }}
                    onClick={() => navigate(`/assessments/${assessment.id}`)}
                  >
                    <Group gap="md" align="center">
                      <IconClipboardCheck color="blue" />
                      <Stack gap="xs">
                        <Text fw={500} size="sm">
                          {assessment.title}
                        </Text>
                        <Group gap="xs">
                          <Badge
                            size="sm"
                            color={
                              assessment.type === 'quiz'
                                ? 'blue'
                                : assessment.type === 'test'
                                ? 'yellow'
                                : 'gray'
                            }
                          >
                            {assessment.type}
                          </Badge>
                          <Badge
                            size="sm"
                            color={
                              assessment.status === 'active'
                                ? 'green'
                                : assessment.status === 'draft'
                                ? 'gray'
                                : 'red'
                            }
                          >
                            {assessment.status}
                          </Badge>
                          <Text size="xs" c="dimmed">
                            Submissions: {assessment.submissions}/{assessment.maxSubmissions}
                          </Text>
                        </Group>
                      </Stack>
                    </Group>
                    <Stack align="flex-end" gap="xs">
                      <Group align="center" gap="xs">
                        <Text fw={500} size="sm">
                          {assessment.averageScore ? `${assessment.averageScore}%` : 'Pending'}
                        </Text>
                        <Menu position="bottom-end" offset={5}>
                          <Menu.Target>
                            <ActionIcon
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                setMenuAssessment(assessment);
                              }}
                            >
                              <IconDots size={16} />
                            </ActionIcon>
                          </Menu.Target>
                          <Menu.Dropdown>
                            <Menu.Item onClick={() => menuAssessment && handleViewAssessment(menuAssessment.id)}>
                              View Details
                            </Menu.Item>
                            <Menu.Item onClick={() => menuAssessment && handleGradeAssessment(menuAssessment.id)}>
                              Grade Submissions
                            </Menu.Item>
                            <Menu.Item onClick={() => menuAssessment && handleEditAssessment(menuAssessment.id)}>
                              Edit Assessment
                            </Menu.Item>
                            <Menu.Item color="red" onClick={() => menuAssessment && handleDeleteAssessment(menuAssessment)}>
                              Delete Assessment
                            </Menu.Item>
                          </Menu.Dropdown>
                        </Menu>
                      </Group>
                      <Text size="xs" c="dimmed">
                        {assessment.dueDate
                          ? `Due: ${new Date(assessment.dueDate).toLocaleDateString()}`
                          : 'No due date'}
                      </Text>
                    </Stack>
                  </Box>
                ))
              )}
            </Stack>
          </Card>
        </Grid.Col>
      </Grid>

      {/* Create Assessment Dialog */}
      <CreateAssessmentDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        onSave={async (assessmentData) => {
          try {
            // Call API to create assessment
            const createdAssessment = await createAssessment(assessmentData);

            dispatch(
              addNotification({
                type: 'success',
                message: `Assessment "${createdAssessment.title}" created successfully!`,
              })
            );
            setCreateDialogOpen(false);
            // Refresh assessments list
            dispatch(fetchAssessments());
          } catch (error) {
            console.error('Failed to create assessment:', error);
            dispatch(
              addNotification({
                type: 'error',
                message: 'Failed to create assessment. Please try again.',
              })
            );
          }
        }}
      />
    </Container>
  );
}
