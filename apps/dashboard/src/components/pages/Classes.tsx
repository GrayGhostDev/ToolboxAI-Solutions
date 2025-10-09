import * as React from 'react';
import {
  Card,
  Text,
  Button,
  Stack,
  Avatar,
  Badge,
  ActionIcon,
  Menu,
  Box,
  Progress,
  TextInput,
  Select,
  Grid,
  Group,
  Divider,
  Loader
} from '@mantine/core';

import { useNavigate } from 'react-router-dom';
import {
  IconPlus,
  IconSearch,
  IconDots,
  IconUsers,
  IconRocket,
  IconEdit,
  IconTrash,
  IconEye
} from '@tabler/icons-react';
import { useAppDispatch, useAppSelector } from '../../store';
import { addNotification } from '../../store/slices/uiSlice';
import { setClasses, removeClass, setClassOnlineStatus } from '../../store/slices/classesSlice';
import { listClasses, createClass, updateClass, deleteClass } from '../../services/api';
import { getClassDetailsRoute } from '../../config/routes';
import CreateClassDialog from '../dialogs/CreateClassDialog';
import StudentProgressTracker from '../widgets/StudentProgressTracker';
import { useApiCallOnMount } from '../../hooks/useApiCall';
interface ClassCardData {
  id: string;
  name: string;
  grade: number;
  studentCount: number;
  schedule: string;
  averageXP: number;
  completionRate: number;
  nextLesson: string;
  isOnline: boolean;
  studentAvatars: string[];
}
export default function Classes() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const role = useAppSelector((s) => s.user.role);
  const [classes, setClasses] = React.useState<ClassCardData[]>([]);
  const [searchTerm, setSearchTerm] = React.useState('');
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const [selectedClass, setSelectedClass] = React.useState<ClassCardData | null>(null);
  const [createClassOpen, setCreateClassOpen] = React.useState(false);
  const [editClassOpen, setEditClassOpen] = React.useState(false);
  const [editingClass, setEditingClass] = React.useState<ClassCardData | null>(null);
  // Filter states
  const [filterGrade, setFilterGrade] = React.useState<string>('all');
  const [filterStatus, setFilterStatus] = React.useState<string>('all');
  const [sortBy, setSortBy] = React.useState<string>('name');

  // Use the API hook for fetching classes
  const { data: classesData, loading, error } = useApiCallOnMount(
    listClasses,
    { mockEndpoint: '/classes', showNotification: false }
  );

  React.useEffect(() => {
    if (classesData) {
      transformAndSetClasses(classesData);
    }
  }, [classesData]);

  const transformAndSetClasses = (data: any) => {
    // Handle both mock data format and API response format
    const transformedClasses: ClassCardData[] = data.classes?.map((classItem: any) => ({
      id: classItem.id,
      name: classItem.name,
      grade: classItem.grade || classItem.grade_level || 0,
      studentCount: classItem.students || classItem.student_count || classItem.studentCount || 0,
      schedule: classItem.schedule || classItem.teacher || 'Schedule not set',
      averageXP: classItem.averageXP || Math.round((classItem.progress || classItem.average_progress || 0.75) * 100),
      completionRate: classItem.progress || classItem.completion_rate || 75,
      nextLesson: classItem.next_lesson || classItem.next_session || 'No upcoming lessons',
      isOnline: classItem.is_online || classItem.status === 'active' || false,
      studentAvatars: classItem.student_avatars || [],
    })) || [];

    setClasses(transformedClasses);
    dispatch(setClasses(transformedClasses));
  };

  // Show error notification if there's an error
  React.useEffect(() => {
    if (error) {
      dispatch(
        addNotification({
          type: 'error',
          message: 'Failed to load classes. Please try again.',
        })
      );
    }
  }, [error, dispatch]);

  const fetchClasses = async () => {
    setLoading(true);

    // Check if we're in bypass mode
    const bypassAuth = import.meta.env.VITE_BYPASS_AUTH === 'true';
    const useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true';

    if (bypassAuth || useMockData) {
      // Use mock data in bypass mode
      const mockClasses = [
        {
          id: 'class-001',
          name: 'Introduction to Programming',
          grade: 6,
          student_count: 24,
          schedule: 'Mon/Wed/Fri 10:00 AM',
          average_progress: 0.78,
          completion_rate: 0.85,
          next_session: 'Variables & Data Types',
          is_online: true,
          student_avatars: ['/avatars/1.png', '/avatars/2.png', '/avatars/3.png']
        },
        {
          id: 'class-002',
          name: 'Advanced Robotics',
          grade: 8,
          student_count: 18,
          schedule: 'Tue/Thu 2:00 PM',
          average_progress: 0.65,
          completion_rate: 0.72,
          next_session: 'Servo Motor Control',
          is_online: false,
          student_avatars: ['/avatars/4.png', '/avatars/5.png']
        },
        {
          id: 'class-003',
          name: 'Game Design Basics',
          grade: 7,
          student_count: 30,
          schedule: 'Mon/Wed 1:00 PM',
          average_progress: 0.92,
          completion_rate: 0.88,
          next_session: 'Level Design Principles',
          is_online: true,
          student_avatars: ['/avatars/1.png', '/avatars/3.png', '/avatars/5.png']
        }
      ];

      // Transform mock data to match component interface
      const transformedClasses: ClassCardData[] = mockClasses.map((classItem: any) => ({
        id: classItem.id,
        name: classItem.name,
        grade: classItem.grade,
        studentCount: classItem.student_count,
        schedule: classItem.schedule,
        averageXP: Math.round(classItem.average_progress * 1000),
        completionRate: classItem.completion_rate * 100,
        nextLesson: classItem.next_session,
        isOnline: classItem.is_online,
        studentAvatars: classItem.student_avatars
      }));

      setClasses(transformedClasses);
      dispatch(setClasses(transformedClasses));
      setLoading(false);
      return;
    }

    try {
      const data = await listClasses();
      // Transform API response to match component interface
      const transformedClasses: ClassCardData[] = data.map((classItem: any) => {
        // Calculate progress based on available data or use defaults
        const progressValue = classItem.average_progress || classItem.progress || 0.75; // Default 75% progress
        // Format next session into readable lesson string
        let nextLessonText = 'No upcoming lessons';
        if (classItem.next_session) {
          const nextDate = new Date(classItem.next_session);
          nextLessonText = `Next: ${nextDate.toLocaleDateString()} at ${nextDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
        } else if (classItem.next_lesson) {
          nextLessonText = classItem.next_lesson;
        }
        return {
          id: classItem.id,
          name: classItem.name,
          grade: classItem.grade_level || classItem.grade || 0,
          studentCount: classItem.student_count || classItem.studentCount || 0,
          schedule: classItem.schedule || 'Schedule not set',
          averageXP: Math.round(progressValue * 100),
          completionRate: progressValue * 100,
          nextLesson: nextLessonText,
          isOnline: classItem.is_online || classItem.status === 'active' || false,
          studentAvatars: classItem.student_avatars || [], // Will be populated when we have student endpoints
        };
      });
      setClasses(transformedClasses);
    } catch (error: any) {
      console.error('Failed to fetch classes:', error);
      const errorDetail = error.response?.data?.detail;
      let errorMessage = 'Failed to load classes. Please try again.';
      if (typeof errorDetail === 'string') {
        errorMessage = errorDetail;
      } else if (Array.isArray(errorDetail)) {
        // Handle Pydantic validation errors
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
      setClasses([]); // Set empty array instead of mock data
    } finally {
      setLoading(false);
    }
  };
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, classData: ClassCardData) => {
    setAnchorEl(event.currentTarget);
    setSelectedClass(classData);
  };
  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedClass(null);
  };
  const handlePushToRoblox = (classData: ClassCardData) => {
    console.log('Pushing to Roblox:', classData);
    dispatch(
      addNotification({
        type: 'info',
        message: `Preparing Roblox environment for "${classData.name}"...`,
      })
    );
    // Simulate push process then navigate to Roblox dashboard
    setTimeout(() => {
      dispatch(
        addNotification({
          type: 'success',
          message: `Class "${classData.name}" is ready in Roblox!`,
        })
      );
      // Navigate to Roblox dashboard with class context
      navigate(`/roblox?classId=${classData.id}&className=${encodeURIComponent(classData.name)}`);
    }, 1500);
    handleMenuClose();
  };
  const handleEditClass = (classData: ClassCardData) => {
    setEditingClass(classData);
    setEditClassOpen(true);
    handleMenuClose();
  };
  const handleDeleteClass = async (classData: ClassCardData) => {
    if (window.confirm(`Are you sure you want to delete "${classData.name}"?`)) {
      try {
        await deleteClass(classData.id);
        dispatch(
          addNotification({
            type: 'success',
            message: `Class "${classData.name}" deleted successfully`,
          })
        );
        setClasses(classes.filter((c) => c.id !== classData.id));
      } catch (error: any) {
        console.error('Error deleting class:', error);
        dispatch(
          addNotification({
            type: 'error',
            message: error.response?.data?.detail || 'Failed to delete class',
          })
        );
      }
    }
    handleMenuClose();
  };
  // Apply filters
  const filteredClasses = React.useMemo(() => {
    const filtered = classes.filter((c) => {
      // Search filter
      if (searchTerm && !c.name.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }
      // Grade filter
      if (filterGrade !== 'all' && c.grade.toString() !== filterGrade) {
        return false;
      }
      // Status filter
      if (filterStatus !== 'all') {
        if (filterStatus === 'online' && !c.isOnline) return false;
        if (filterStatus === 'offline' && c.isOnline) return false;
      }
      return true;
    });
    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'grade':
          return a.grade - b.grade;
        case 'students':
          return b.studentCount - a.studentCount;
        case 'progress':
          return b.completionRate - a.completionRate;
        default:
          return 0;
      }
    });
    return filtered;
  }, [classes, searchTerm, filterGrade, filterStatus, sortBy]);
  return (
    <Grid gutter="md">
      {/* Header */}
      <Grid.Col span={12}>
        <Card>
          <Stack
            justify="space-between"
            align={{ base: 'flex-start', md: 'center' }}
            gap="md"
            style={{ flexDirection: 'row', flexWrap: 'wrap' }}
          >
            <Text size="xl" fw={600}>
              My Classes
            </Text>
            <Group gap="md" style={{ flexWrap: 'wrap' }}>
              <TextInput
                size="sm"
                placeholder="Search classes..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ minWidth: 200 }}
                leftSection={<IconSearch size={16} />}
                data-testid="search-input"
              />
              <Select
                size="sm"
                placeholder="Grade"
                value={filterGrade}
                onChange={(value) => setFilterGrade(value || 'all')}
                data={[
                  { value: 'all', label: 'All Grades' },
                  { value: '1', label: 'Grade 1' },
                  { value: '2', label: 'Grade 2' },
                  { value: '3', label: 'Grade 3' },
                  { value: '4', label: 'Grade 4' },
                  { value: '5', label: 'Grade 5' },
                  { value: '6', label: 'Grade 6' },
                  { value: '7', label: 'Grade 7' },
                  { value: '8', label: 'Grade 8' },
                  { value: '9', label: 'Grade 9' },
                  { value: '10', label: 'Grade 10' },
                  { value: '11', label: 'Grade 11' },
                  { value: '12', label: 'Grade 12' },
                ]}
                style={{ minWidth: 120 }}
                data-testid="grade-filter"
              />
              <Select
                size="sm"
                placeholder="Status"
                value={filterStatus}
                onChange={(value) => setFilterStatus(value || 'all')}
                data={[
                  { value: 'all', label: 'All Status' },
                  { value: 'online', label: 'Online' },
                  { value: 'offline', label: 'Offline' },
                ]}
                style={{ minWidth: 120 }}
                data-testid="status-filter"
              />
              <Select
                size="sm"
                placeholder="Sort By"
                value={sortBy}
                onChange={(value) => setSortBy(value || 'name')}
                data={[
                  { value: 'name', label: 'Name' },
                  { value: 'grade', label: 'Grade' },
                  { value: 'students', label: 'Students' },
                  { value: 'progress', label: 'Progress' },
                ]}
                style={{ minWidth: 120 }}
                data-testid="sort-by"
              />
              {role === 'teacher' && (
                <Button
                  leftSection={<IconPlus size={16} />}
                  onClick={() => setCreateClassOpen(true)}
                  data-testid="create-class-button"
                >
                  Create Class
                </Button>
              )}
            </Group>
          </Stack>
        </Card>
      </Grid.Col>
      {/* Stats Overview */}
      <Grid.Col span={{ base: 12, md: 3 }}>
        <Card>
          <Stack gap="xs">
            <Text size="xs" c="dimmed">
              Total Students
            </Text>
            <Text size="xl" fw={700}>
              {classes.reduce((sum, c) => sum + c.studentCount, 0)}
            </Text>
          </Stack>
        </Card>
      </Grid.Col>
      <Grid.Col span={{ base: 12, md: 3 }}>
        <Card>
          <Stack gap="xs">
            <Text size="xs" c="dimmed">
              Active Classes
            </Text>
            <Text size="xl" fw={700}>
              {classes.length}
            </Text>
          </Stack>
        </Card>
      </Grid.Col>
      <Grid.Col span={{ base: 12, md: 3 }}>
        <Card>
          <Stack gap="xs">
            <Text size="xs" c="dimmed">
              Average XP
            </Text>
            <Text size="xl" fw={700}>
              {Math.round(
                classes.reduce((sum, c) => sum + c.averageXP, 0) / classes.length || 0
              )}
            </Text>
          </Stack>
        </Card>
      </Grid.Col>
      <Grid.Col span={{ base: 12, md: 3 }}>
        <Card>
          <Stack gap="xs">
            <Text size="xs" c="dimmed">
              Avg Completion
            </Text>
            <Text size="xl" fw={700}>
              {Math.round(
                classes.reduce((sum, c) => sum + c.completionRate, 0) / classes.length || 0
              )}
              %
            </Text>
          </Stack>
        </Card>
      </Grid.Col>
      {/* Class Cards */}
      {loading ? (
        <Grid.Col span={12}>
          <Group justify="center">
            <Loader />
            <Text>Loading classes...</Text>
          </Group>
        </Grid.Col>
      ) : filteredClasses.length === 0 ? (
        <Grid.Col span={12}>
          <Card>
            <Text ta="center" c="dimmed">
              No classes found. Create your first class to get started!
            </Text>
          </Card>
        </Grid.Col>
      ) : (
        <>
          <Grid.Col span={12} data-testid="classes-list" className="classes-grid">
            {/* Hidden element for test detection */}
            <div style={{ display: 'none' }}>Classes List Container</div>
          </Grid.Col>
          {filteredClasses.map((classData) => (
            <Grid.Col
              key={classData.id}
              span={{ base: 12, md: 6, lg: 4 }}
              data-testid="class-row"
              className="class-card"
            >
            <Card
              data-testid="class-card"
              style={{
                height: '100%',
                transition: 'all 0.3s ease',
                cursor: 'pointer',
              }}
              onClick={() => navigate(`/classes/${classData.id}`)}
              __hover={{
                transform: 'translateY(-4px)',
                boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
              }}
            >
              <Stack gap="md">
                {/* Header */}
                <Group justify="space-between" align="flex-start">
                  <Stack gap="xs">
                    <Group gap="xs" align="center">
                      <Text
                        size="lg"
                        fw={600}
                        data-testid="class-name"
                      >
                        {classData.name}
                      </Text>
                      {classData.isOnline && (
                        <Badge
                          color="green"
                          size="sm"
                          data-testid="online-status"
                        >
                          Online
                        </Badge>
                      )}
                    </Group>
                    <Text size="sm" c="dimmed">
                      Grade {classData.grade} • {classData.schedule}
                    </Text>
                  </Stack>
                  <ActionIcon
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleMenuOpen(e, classData);
                    }}
                    aria-label="More options"
                    data-testid="class-menu-button"
                  >
                    <IconDots size={16} />
                  </ActionIcon>
                </Group>
                {/* Students */}
                <Group gap="md" align="center">
                  <Avatar.Group spacing="sm">
                    {classData.studentAvatars.slice(0, 4).map((avatar, index) => (
                      <Avatar key={index} src={avatar} size="sm" />
                    ))}
                    {classData.studentAvatars.length > 4 && (
                      <Avatar size="sm">+{classData.studentAvatars.length - 4}</Avatar>
                    )}
                  </Avatar.Group>
                  <Stack gap="xs">
                    <Text size="sm" fw={500}>
                      {classData.studentCount} Students
                    </Text>
                    <Text size="xs" c="dimmed">
                      Avg. {classData.averageXP} XP
                    </Text>
                  </Stack>
                </Group>
                {/* Progress */}
                <Box>
                  <Group justify="space-between" mb="xs">
                    <Text size="xs" c="dimmed">
                      Completion Rate
                    </Text>
                    <Text size="xs" fw={600}>
                      {classData.completionRate}%
                    </Text>
                  </Group>
                  <Progress
                    value={classData.completionRate}
                    size="lg"
                    radius="xl"
                  />
                </Box>
                {/* Next Lesson */}
                <Box
                  style={{
                    padding: 12,
                    borderRadius: 8,
                    backgroundColor: 'var(--mantine-color-gray-0)',
                  }}
                >
                  <Text size="xs" c="dimmed">
                    Next Lesson
                  </Text>
                  <Text size="sm" fw={500}>
                    {classData.nextLesson}
                  </Text>
                </Box>
                {/* Actions */}
                <Group gap="xs">
                  <Button
                    size="sm"
                    variant="outline"
                    leftSection={<IconEye size={14} />}
                    style={{ flex: 1 }}
                    onClick={(e) => {
                      e.stopPropagation();
                      console.log('View button clicked for class:', classData.id);
                      const route = `/classes/${classData.id}`;
                      console.log('Navigating to:', route);
                      navigate(route);
                    }}
                  >
                    View
                  </Button>
                  <Button
                    size="sm"
                    leftSection={<IconRocket size={14} />}
                    style={{ flex: 1 }}
                    onClick={(e) => {
                      e.stopPropagation();
                      handlePushToRoblox(classData);
                    }}
                  >
                    Roblox
                  </Button>
                </Group>
              </Stack>
            </Card>
          </Grid.Col>
        ))}
        </>
      )}
      {/* Action Menu */}
      <Menu
        opened={Boolean(anchorEl)}
        onClose={handleMenuClose}
        position="bottom-end"
      >
        <Menu.Item
          leftSection={<IconEye size={16} />}
          onClick={() => {
            if (selectedClass) {
              navigate(getClassDetailsRoute(selectedClass.id));
            }
            handleMenuClose();
          }}
        >
          View Details
        </Menu.Item>
        <Menu.Item
          leftSection={<IconEdit size={16} />}
          onClick={() => {
            if (selectedClass) {
              handleEditClass(selectedClass);
            }
          }}
          data-testid="edit-class"
        >
          Edit Class
        </Menu.Item>
        <Menu.Item
          leftSection={<IconUsers size={16} />}
          onClick={() => {
            // TODO: Navigate to manage students page
            handleMenuClose();
          }}
          data-testid="manage-students"
        >
          Manage Students
        </Menu.Item>
        {selectedClass && !selectedClass.isOnline && (
          <Menu.Item
            leftSection={<IconRocket size={16} />}
            onClick={() => selectedClass && handlePushToRoblox(selectedClass)}
            data-testid="push-to-roblox"
          >
            Push to Roblox
          </Menu.Item>
        )}
        <Menu.Item
          leftSection={<IconTrash size={16} />}
          color="red"
          onClick={() => selectedClass && handleDeleteClass(selectedClass)}
          data-testid="delete-class"
        >
          Delete Class
        </Menu.Item>
      </Menu>
      {/* Create Class Dialog */}
      <CreateClassDialog
        open={createClassOpen}
        onClose={() => setCreateClassOpen(false)}
        onSave={async (classData) => {
          try {
            setLoading(true);
            const newClass = await createClass(classData);
            // Normalize backend snake_case fields safely
            const newClassAny: any = newClass as any;
            // Calculate progress based on available data or use defaults
            const progressValue = newClassAny.average_progress || newClassAny.progress || 0.0; // New class starts at 0%
            // Format next session into readable lesson string
            let nextLessonText = 'No upcoming lessons';
            if (newClassAny.next_session) {
              const nextDate = new Date(newClassAny.next_session);
              nextLessonText = `Next: ${nextDate.toLocaleDateString()} at ${nextDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
            } else if (newClassAny.next_lesson) {
              nextLessonText = newClassAny.next_lesson;
            }
            // Add the new class to the list immediately
            const transformedClass: ClassCardData = {
              id: newClassAny.id,
              name: newClassAny.name,
              grade: newClassAny.grade_level ?? newClassAny.grade ?? 0,
              studentCount: newClassAny.student_count ?? newClassAny.studentCount ?? 0,
              schedule: newClassAny.schedule || 'Schedule not set',
              averageXP: Math.round(progressValue * 100),
              completionRate: progressValue * 100,
              nextLesson: nextLessonText,
              isOnline: newClassAny.is_online ?? newClassAny.status === 'active' ?? false,
              studentAvatars: newClassAny.student_avatars || [],
            };
            setClasses(prev => [transformedClass, ...prev]);
            dispatch(
              addNotification({
                type: 'success',
                message: `Class "${classData.name}" created successfully!`,
              })
            );
            setCreateClassOpen(false);
            // Also refresh from server to ensure consistency
            await fetchClasses();
          } catch (error: any) {
            console.error('Error creating class:', error);
            const errorMessage = error.response?.data?.detail || 'Failed to create class';
            dispatch(
              addNotification({
                type: 'error',
                message: errorMessage,
              })
            );
          } finally {
            setLoading(false);
          }
        }}
      />
      {/* Edit Class Dialog */}
      {editingClass && (
        <CreateClassDialog
          open={editClassOpen}
          editMode={true}
          initialData={{
            name: editingClass.name,
            grade_level: editingClass.grade,
            grade: editingClass.grade,
            schedule: editingClass.schedule,
            subject: 'Mathematics', // Will need to be stored in the data
            room: '', // Will need to be stored in the data
            description: '', // Will need to be stored in the data
          }}
          onClose={() => {
            setEditClassOpen(false);
            setEditingClass(null);
          }}
          onSave={async (classData) => {
            try {
              setLoading(true);
              const updatedClass = await updateClass(editingClass.id, classData);
              // Update the class in the local state
              const updatedClassAny: any = updatedClass as any;
              // Calculate progress based on available data or use existing
              const progressValue = updatedClassAny.average_progress || updatedClassAny.progress || editingClass.completionRate / 100;
              // Format next session into readable lesson string
              let nextLessonText = editingClass.nextLesson;
              if (updatedClassAny.next_session) {
                const nextDate = new Date(updatedClassAny.next_session);
                nextLessonText = `Next: ${nextDate.toLocaleDateString()} at ${nextDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
              } else if (updatedClassAny.next_lesson) {
                nextLessonText = updatedClassAny.next_lesson;
              }
              // Update the transformed class
              const transformedClass: ClassCardData = {
                ...editingClass,
                name: updatedClassAny.name,
                grade: updatedClassAny.grade_level ?? updatedClassAny.grade ?? editingClass.grade,
                schedule: updatedClassAny.schedule || editingClass.schedule,
                averageXP: Math.round(progressValue * 100),
                completionRate: progressValue * 100,
                nextLesson: nextLessonText,
              };
              setClasses(prev => prev.map(c => c.id === editingClass.id ? transformedClass : c));
              dispatch(
                addNotification({
                  type: 'success',
                  message: `Class "${classData.name}" updated successfully!`,
                })
              );
              setEditClassOpen(false);
              setEditingClass(null);
              // Also refresh from server to ensure consistency
              await fetchClasses();
            } catch (error: any) {
              console.error('Error updating class:', error);
              const errorMessage = error.response?.data?.detail || 'Failed to update class';
              dispatch(
                addNotification({
                  type: 'error',
                  message: errorMessage,
                })
              );
            } finally {
              setLoading(false);
            }
          }}
        />
      )}
      {/* Student Progress Tracker for Teachers */}
      {role === 'teacher' && (
        <Grid.Col span={12}>
          <Text size="lg" mb="md" fw={600}>
            Student Progress Tracker
          </Text>
          <StudentProgressTracker />
        </Grid.Col>
      )}
    </Grid>
  );
}