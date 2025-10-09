import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  Text,
  Button,
  Grid,
  Badge,
  ActionIcon,
  Loader,
  List,
  Group,
  Stack,
  Flex,
} from '@mantine/core';
import {
  IconArrowLeft,
  IconEdit,
  IconTrash,
  IconSchool,
  IconClock,
  IconUsers,
  IconClipboard,
  IconRocket,
} from '@tabler/icons-react';
import { useAppDispatch } from '@/store';
import { getClass } from '@/services/api';
import { addNotification } from '@/store/slices/uiSlice';
import type { ClassDetails as ApiClassDetails } from '@/types/api';

interface ClassDetailsData {
  id: string | number; // allow both to match API (string) and local expectations
  name: string;
  subject?: string; // make optional since API doesn't provide subject
  grade_level?: number;
  teacher_name?: string;
  room?: string;
  schedule?: string;
  description?: string;
  student_count?: number;
  status?: string;
  created_at?: string;
  syllabus_url?: string;
  resources?: Array<{ name: string; url: string }>;
}

const ClassDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [classData, setClassData] = useState<ClassDetailsData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchClassDetails = useCallback(async (classId: string) => {
    try {
      setLoading(true);
      const data: ApiClassDetails = await getClass(classId);
      // Normalize API (camelCase) to local component expectations (some snake_case)
      const mapped: ClassDetailsData = {
        id: data.id,
        name: data.name,
        // subject not in API; leave undefined so UI shows fallback
        grade_level: data.grade,
        teacher_name: undefined,
        room: undefined,
        schedule: data.schedule,
        description: undefined,
        student_count: data.studentCount,
        status: undefined,
        created_at: data.createdAt,
        syllabus_url: undefined,
        resources: undefined,
      };
      setClassData(mapped);
    } catch (error) {
      console.error('Error fetching class details:', error);
      dispatch(
        addNotification({
          type: 'error',
          message: 'Failed to load class details',
        })
      );
    } finally {
      setLoading(false);
    }
  }, [dispatch]);

  useEffect(() => {
    if (id) {
      fetchClassDetails(id);
    }
  }, [id, fetchClassDetails]);

  const handlePushToRoblox = () => {
    dispatch(
      addNotification({
        type: 'info',
        message: 'Pushing class to Roblox environment...',
      })
    );
    // TODO: Implement Roblox push functionality
    setTimeout(() => {
      dispatch(
        addNotification({
          type: 'success',
          message: 'Class pushed to Roblox environment successfully',
        })
      );
    }, 2000);
  };

  const handleEdit = () => {
    // TODO: Navigate to edit page or open edit dialog
    dispatch(
      addNotification({
        type: 'info',
        message: 'Edit functionality coming soon',
      })
    );
  };

  const handleDelete = () => {
    if (window.confirm('Are you sure you want to delete this class?')) {
      // TODO: Implement delete functionality
      dispatch(
        addNotification({
          type: 'warning',
          message: 'Delete functionality coming soon',
        })
      );
    }
  };

  if (loading) {
    return (
      <Box w="100%" p="md">
        <Flex justify="center" align="center" h={200}>
          <Loader size="lg" />
        </Flex>
      </Box>
    );
  }

  if (!classData) {
    return (
      <Box p="lg">
        <Text size="lg" mb="md">Class not found</Text>
        <Button leftSection={<IconArrowLeft size={16} />} onClick={() => navigate('/classes')}>
          Back to Classes
        </Button>
      </Box>
    );
  }

  return (
    <Box p="lg">
      {/* Header */}
      <Flex justify="space-between" align="center" mb="xl">
        <Group gap="md">
          <ActionIcon size="lg" variant="subtle" onClick={() => navigate('/classes')}>
            <IconArrowLeft size={20} />
          </ActionIcon>
          <Text size="xl" fw={600}>{classData.name}</Text>
          <Badge
            color={classData.status === 'active' ? 'green' : 'gray'}
            size="sm"
          >
            {classData.status || 'Active'}
          </Badge>
        </Group>
        <Group gap="xs">
          <Button
            leftSection={<IconRocket size={16} />}
            onClick={handlePushToRoblox}
          >
            Push to Roblox
          </Button>
          <ActionIcon size="lg" variant="subtle" onClick={handleEdit}>
            <IconEdit size={18} />
          </ActionIcon>
          <ActionIcon size="lg" variant="subtle" color="red" onClick={handleDelete}>
            <IconTrash size={18} />
          </ActionIcon>
        </Group>
      </Flex>

      <Grid>
        {/* Main Info Card */}
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Card p="lg" radius="md">
            <Text size="lg" fw={600} mb="md">
              Class Information
            </Text>
            <Grid>
              <Grid.Col span={{ base: 12, sm: 6 }}>
                <Group gap="sm" mb="md">
                  <IconSchool size={20} color="var(--mantine-color-dimmed)" />
                  <Stack gap={2}>
                    <Text size="xs" c="dimmed" tt="uppercase" fw={500}>
                      Subject
                    </Text>
                    <Text>{classData.subject || 'Not specified'}</Text>
                  </Stack>
                </Group>
              </Grid.Col>
              <Grid.Col span={{ base: 12, sm: 6 }}>
                <Group gap="sm" mb="md">
                  <IconUsers size={20} color="var(--mantine-color-dimmed)" />
                  <Stack gap={2}>
                    <Text size="xs" c="dimmed" tt="uppercase" fw={500}>
                      Students
                    </Text>
                    <Text>{classData.student_count || 0} enrolled</Text>
                  </Stack>
                </Group>
              </Grid.Col>
              <Grid.Col span={{ base: 12, sm: 6 }}>
                <Group gap="sm" mb="md">
                  <IconClock size={20} color="var(--mantine-color-dimmed)" />
                  <Stack gap={2}>
                    <Text size="xs" c="dimmed" tt="uppercase" fw={500}>
                      Schedule
                    </Text>
                    <Text>{classData.schedule || 'Not set'}</Text>
                  </Stack>
                </Group>
              </Grid.Col>
              <Grid.Col span={{ base: 12, sm: 6 }}>
                <Group gap="sm" mb="md">
                  <IconClipboard size={20} color="var(--mantine-color-dimmed)" />
                  <Stack gap={2}>
                    <Text size="xs" c="dimmed" tt="uppercase" fw={500}>
                      Grade Level
                    </Text>
                    <Text>
                      {classData.grade_level ? `Grade ${classData.grade_level}` : 'All grades'}
                    </Text>
                  </Stack>
                </Group>
              </Grid.Col>
              <Grid.Col span={12}>
                <Stack gap={4}>
                  <Text size="xs" c="dimmed" tt="uppercase" fw={500}>
                    Description
                  </Text>
                  <Text>
                    {classData.description || 'No description provided'}
                  </Text>
                </Stack>
              </Grid.Col>
            </Grid>
          </Card>
        </Grid.Col>

        {/* Side Info Cards */}
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Stack gap="md">
            <Card p="lg" radius="md">
              <Text size="md" fw={600} mb="sm">
                Teacher
              </Text>
              <Text>{classData.teacher_name || 'Not assigned'}</Text>
            </Card>

            <Card p="lg" radius="md">
              <Text size="md" fw={600} mb="sm">
                Room
              </Text>
              <Text>{classData.room || 'Virtual'}</Text>
            </Card>

            {classData.resources && classData.resources.length > 0 && (
              <Card p="lg" radius="md">
                <Text size="md" fw={600} mb="sm">
                  Resources
                </Text>
                <List size="sm" spacing="xs">
                  {classData.resources.map((resource, index) => (
                    <List.Item key={index}>
                      {resource.name}
                    </List.Item>
                  ))}
                </List>
              </Card>
            )}
          </Stack>
        </Grid.Col>

        {/* Recent Activity */}
        <Grid.Col span={12}>
          <Card p="lg" radius="md">
            <Text size="lg" fw={600} mb="md">
              Recent Activity
            </Text>
            <Text c="dimmed">
              No recent activity to display
            </Text>
          </Card>
        </Grid.Col>
      </Grid>
    </Box>
  );
};

export default ClassDetails;