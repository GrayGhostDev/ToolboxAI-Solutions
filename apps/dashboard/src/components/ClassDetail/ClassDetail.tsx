import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Paper,
  Text,
  Tabs,
  Button,
  Loader,
  Alert,
  Breadcrumbs,
  Anchor,
  Badge,
} from '@mantine/core';
import {
  IconArrowLeft,
  IconSchool,
  IconFileText,
  IconUsers,
  IconChartBar,
  IconSettings,
} from '@tabler/icons-react';
import { apiClient } from '../../services/api';
import { StudentManagement } from '../StudentManagement';
import { notifications } from '@mantine/notifications';
import { useAuth } from '../../hooks/useAuth';


interface ClassData {
  id: string;
  name: string;
  subject: string;
  teacher_id: string;
  teacher_name?: string;
  description?: string;
  schedule?: string;
  room?: string;
  max_students: number;
  student_count?: number;
  created_at: string;
  updated_at?: string;
  status: 'active' | 'inactive' | 'archived';
}

export const ClassDetail: React.FC = () => {
  const { classId } = useParams<{ classId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [classData, setClassData] = useState<ClassData | null>(null);
  const [loading, setLoading] = useState(true);
  const [tabValue, setTabValue] = useState<string | null>('0');
  const [studentCount, setStudentCount] = useState(0);

  useEffect(() => {
    if (classId) {
      loadClassData();
    }
  }, [classId]);

  const loadClassData = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get(`/api/v1/classes/${classId}`);
      setClassData(response.data.data);
      setStudentCount(response.data.data.student_count || 0);
    } catch (error: any) {
      notifications.show({
        title: 'Error',
        message: error.response?.data?.message || 'Failed to load class details',
        color: 'red',
      });
      navigate('/classes');
    } finally {
      setLoading(false);
    }
  };

  const handleStudentCountChange = (count: number) => {
    setStudentCount(count);
    if (classData) {
      setClassData({ ...classData, student_count: count });
    }
  };

  if (loading) {
    return (
      <Container>
        <Box style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
          <Loader />
        </Box>
      </Container>
    );
  }

  if (!classData) {
    return (
      <Container>
        <Alert color="red">Class not found</Alert>
      </Container>
    );
  }

  const isTeacher = user?.id === classData.teacher_id;
  const isAdmin = user?.role === 'admin';
  const canManage = isTeacher || isAdmin;

  return (
    <Container size="lg">
      {/* Breadcrumbs */}
      <Box mb="md">
        <Breadcrumbs>
          <Anchor
            onClick={(e) => {
              e.preventDefault();
              navigate('/dashboard');
            }}
          >
            Dashboard
          </Anchor>
          <Anchor
            onClick={(e) => {
              e.preventDefault();
              navigate('/classes');
            }}
          >
            Classes
          </Anchor>
          <Text>{classData.name}</Text>
        </Breadcrumbs>
      </Box>

      {/* Header */}
      <Paper p="lg" mb="md">
        <Box style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Box style={{ display: 'flex', alignItems: 'center', gap: 8 }} mb="md">
              <Button
                leftSection={<IconArrowLeft size={16} />}
                onClick={() => navigate('/classes')}
                variant="subtle"
              >
                Back to Classes
              </Button>
            </Box>
            <Text size="xl" fw={600} mb="md">
              {classData.name}
            </Text>
            <Box style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
              <Badge
                leftSection={<IconSchool size={14} />}
                color="blue"
              >
                {classData.subject}
              </Badge>
              <Badge
                color={studentCount >= classData.max_students ? 'red' : 'gray'}
              >
                {studentCount} / {classData.max_students} Students
              </Badge>
              <Badge
                color={classData.status === 'active' ? 'green' : 'gray'}
                size="sm"
              >
                {classData.status}
              </Badge>
              {classData.room && (
                <Text size="sm" c="dimmed">
                  Room: {classData.room}
                </Text>
              )}
            </Box>
            {classData.description && (
              <Text c="dimmed" mt="md">
                {classData.description}
              </Text>
            )}
            {classData.schedule && (
              <Text size="sm" c="dimmed" mt="xs">
                Schedule: {classData.schedule}
              </Text>
            )}
          </Box>
          {canManage && (
            <Box>
              <Button
                leftSection={<IconSettings size={16} />}
                onClick={() => navigate(`/classes/${classId}/settings`)}
              >
                Settings
              </Button>
            </Box>
          )}
        </Box>
      </Paper>

      {/* Tabs */}
      <Paper mb="md">
        <Tabs value={tabValue} onChange={setTabValue}>
          <Tabs.List>
            <Tabs.Tab value="0" leftSection={<IconSchool size={16} />}>
              Overview
            </Tabs.Tab>
            {canManage && (
              <Tabs.Tab value="1" leftSection={<IconUsers size={16} />}>
                Students
              </Tabs.Tab>
            )}
            <Tabs.Tab value={canManage ? '2' : '1'} leftSection={<IconFileText size={16} />}>
              Assignments
            </Tabs.Tab>
            <Tabs.Tab value={canManage ? '3' : '2'} leftSection={<IconChartBar size={16} />}>
              Analytics
            </Tabs.Tab>
          </Tabs.List>
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <Tabs.Panel value="0">
        <Paper p="lg">
          <Text size="lg" fw={500} mb="md">
            Class Overview
          </Text>
          <Box style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 24 }}>
            <Box>
              <Text size="sm" fw={500} c="dimmed">
                Subject
              </Text>
              <Text>{classData.subject}</Text>
            </Box>
            <Box>
              <Text size="sm" fw={500} c="dimmed">
                Teacher
              </Text>
              <Text>
                {classData.teacher_name || 'Loading...'}
              </Text>
            </Box>
            <Box>
              <Text size="sm" fw={500} c="dimmed">
                Schedule
              </Text>
              <Text>
                {classData.schedule || 'Not set'}
              </Text>
            </Box>
            <Box>
              <Text size="sm" fw={500} c="dimmed">
                Room
              </Text>
              <Text>{classData.room || 'Not set'}</Text>
            </Box>
            <Box>
              <Text size="sm" fw={500} c="dimmed">
                Created
              </Text>
              <Text>
                {new Date(classData.created_at).toLocaleDateString()}
              </Text>
            </Box>
            <Box>
              <Text size="sm" fw={500} c="dimmed">
                Status
              </Text>
              <Badge
                color={classData.status === 'active' ? 'green' : 'gray'}
                size="sm"
              >
                {classData.status}
              </Badge>
            </Box>
          </Box>
          {classData.description && (
            <Box mt="lg">
              <Text size="sm" fw={500} c="dimmed" mb="xs">
                Description
              </Text>
              <Text>{classData.description}</Text>
            </Box>
          )}
        </Paper>
      </Tabs.Panel>

      {canManage && (
        <Tabs.Panel value="1">
          <StudentManagement
            classId={classData.id}
            className={classData.name}
            teacherId={classData.teacher_id}
            maxStudents={classData.max_students}
            onStudentCountChange={handleStudentCountChange}
          />
        </Tabs.Panel>
      )}

      <Tabs.Panel value={canManage ? '2' : '1'}>
        <Paper p="lg">
          <Text size="lg" fw={500} mb="md">
            Assignments
          </Text>
          <Alert color="blue">
            Assignment management coming soon. Teachers will be able to create, distribute, and
            grade assignments here.
          </Alert>
        </Paper>
      </Tabs.Panel>

      <Tabs.Panel value={canManage ? '3' : '2'}>
        <Paper p="lg">
          <Text size="lg" fw={500} mb="md">
            Analytics
          </Text>
          <Alert color="blue">
            Class analytics and performance metrics will be displayed here, including student
            progress, attendance, and assignment completion rates.
          </Alert>
        </Paper>
      </Tabs.Panel>
    </Container>
  );
};