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
  IconClipboardList,
  IconUsers,
  IconChartBar,
  IconSettings,
} from '@tabler/icons-react';
import { apiClient } from '../../services/api';
import { StudentManagement } from '../StudentManagement';
import { notifications } from '@mantine/notifications';
import { useAuth } from '../../hooks/useAuth';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`class-tabpanel-${index}`}
      aria-labelledby={`class-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ py: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `class-tab-${index}`,
    'aria-controls': `class-tabpanel-${index}`,
  };
}

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
  // Using Mantine notifications instead of notistack
  const [classData, setClassData] = useState<ClassData | null>(null);
  const [loading, setLoading] = useState(true);
  const [tabValue, setTabValue] = useState(0);
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

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
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
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <Loader />
        </Box>
      </Container>
    );
  }

  if (!classData) {
    return (
      <Container>
        <Alert severity="error">Class not found</Alert>
      </Container>
    );
  }

  const isTeacher = user?.id === classData.teacher_id;
  const isAdmin = user?.role === 'admin';
  const canManage = isTeacher || isAdmin;

  return (
    <Container maxWidth="lg">
      {/* Breadcrumbs */}
      <Box mb={3}>
        <Breadcrumbs aria-children="breadcrumb">
          <Anchor
            color="inherit"
            href="#"
            onClick={(e) => {
              e.preventDefault();
              navigate('/dashboard');
            }}
          >
            Dashboard
          </Anchor>
          <Anchor
            color="inherit"
            href="#"
            onClick={(e) => {
              e.preventDefault();
              navigate('/classes');
            }}
          >
            Classes
          </Anchor>
          <Text color="dimmed">{classData.name}</Text>
        </Breadcrumbs>
      </Box>

      {/* Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <Box display="flex" alignItems="center" gap={1} mb={2}>
              <Button
                startIcon={<ArrowBackIcon />}
                onClick={() => navigate('/classes')}
                variant="text"
              >
                Back to Classes
              </Button>
            </Box>
            <Text size="xl" fw={600} mb="md">
              {classData.name}
            </Text>
            <Box display="flex" gap={2} alignItems="center">
              <Badge
                color="blue"
                leftSection={<IconSchool />}
              >
                {classData.subject}
              </Badge>
              <Badge
                color={studentCount >= classData.max_students ? 'red' : 'gray'}
              >
                {studentCount} / {classData.max_students} Students
              </Badge>
              <Badge
                children={classData.status}
                color={classData.status === 'active' ? 'green' : 'gray'}
                size="sm"
              />
              {classData.room && (
                <Text size="xs" c="dimmed">
                  Room: {classData.room}
                </Text>
              )}
            </Box>
            {classData.description && (
              <Text size="sm" c="dimmed" sx={{ mt: 2 }}>
                {classData.description}
              </Text>
            )}
            {classData.schedule && (
              <Text size="xs" c="dimmed" sx={{ mt: 1 }}>
                Schedule: {classData.schedule}
              </Text>
            )}
          </Box>
          {canManage && (
            <Box>
              <Button
                variant="contained"
                startIcon={<SettingsIcon />}
                onClick={() => navigate(`/classes/${classId}/settings`)}
              >
                Settings
              </Button>
            </Box>
          )}
        </Box>
      </Paper>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          aria-children="class detail tabs"
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<SchoolIcon />} children="Overview" {...a11yProps(0)} />
          {canManage && (
            <Tab icon={<PeopleIcon />} children="Students" {...a11yProps(1)} />
          )}
          <Tab icon={<AssignmentIcon />} children="Assignments" {...a11yProps(2)} />
          <Tab icon={<AnalyticsIcon />} children="Analytics" {...a11yProps(3)} />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        <Paper sx={{ p: 3 }}>
          <Text size="lg" mb="md">
            Class Overview
          </Text>
          <Box display="grid" gridTemplateColumns="repeat(auto-fit, minmax(250px, 1fr))" gap={3}>
            <Box>
              <Text size="xs" c="dimmed">
                Subject
              </Text>
              <Text size="sm">{classData.subject}</Text>
            </Box>
            <Box>
              <Text size="xs" c="dimmed">
                Teacher
              </Text>
              <Text size="sm">
                {classData.teacher_name || 'Loading...'}
              </Text>
            </Box>
            <Box>
              <Text size="xs" c="dimmed">
                Schedule
              </Text>
              <Text size="sm">
                {classData.schedule || 'Not set'}
              </Text>
            </Box>
            <Box>
              <Text size="xs" c="dimmed">
                Room
              </Text>
              <Text size="sm">{classData.room || 'Not set'}</Text>
            </Box>
            <Box>
              <Text size="xs" c="dimmed">
                Created
              </Text>
              <Text size="sm">
                {new Date(classData.created_at).toLocaleDateString()}
              </Text>
            </Box>
            <Box>
              <Text size="xs" c="dimmed">
                Status
              </Text>
              <Badge
                children={classData.status}
                color={classData.status === 'active' ? 'green' : 'gray'}
                size="sm"
              />
            </Box>
          </Box>
          {classData.description && (
            <Box mt={3}>
              <Text size="xs" c="dimmed" mb="md">
                Description
              </Text>
              <Text size="sm">{classData.description}</Text>
            </Box>
          )}
        </Paper>
      </TabPanel>

      {canManage && (
        <TabPanel value={tabValue} index={1}>
          <StudentManagement
            classId={classData.id}
            className={classData.name}
            teacherId={classData.teacher_id}
            maxStudents={classData.max_students}
            onStudentCountChange={handleStudentCountChange}
          />
        </TabPanel>
      )}

      <TabPanel value={tabValue} index={canManage ? 2 : 1}>
        <Paper sx={{ p: 3 }}>
          <Text size="lg" mb="md">
            Assignments
          </Text>
          <Alert severity="info">
            Assignment management coming soon. Teachers will be able to create, distribute, and
            grade assignments here.
          </Alert>
        </Paper>
      </TabPanel>

      <TabPanel value={tabValue} index={canManage ? 3 : 2}>
        <Paper sx={{ p: 3 }}>
          <Text size="lg" mb="md">
            Analytics
          </Text>
          <Alert severity="info">
            Class analytics and performance metrics will be displayed here, including student
            progress, attendance, and assignment completion rates.
          </Alert>
        </Paper>
      </TabPanel>
    </Container>
  );
};
