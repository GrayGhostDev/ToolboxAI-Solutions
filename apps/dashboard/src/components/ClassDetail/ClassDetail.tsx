import React, { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import Breadcrumbs from '@mui/material/Breadcrumbs';
import Link from '@mui/material/Link';
import Chip from '@mui/material/Chip';

import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowBack as ArrowBackIcon,
  School as SchoolIcon,
  Assignment as AssignmentIcon,
  People as PeopleIcon,
  Analytics as AnalyticsIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { apiClient } from '../../services/api';
import { StudentManagement } from '../StudentManagement';
import { useSnackbar } from 'notistack';
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

export const ClassDetail: React.FunctionComponent<Record<string, any>> = () => {
  const { classId } = useParams<{ classId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { enqueueSnackbar } = useSnackbar();
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
      enqueueSnackbar(
        error.response?.data?.message || 'Failed to load class details',
        { variant: 'error' }
      );
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
          <CircularProgress />
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
        <Breadcrumbs aria-label="breadcrumb">
          <Link
            color="inherit"
            href="#"
            onClick={(e: React.MouseEvent) => (e) => {
              e.preventDefault();
              navigate('/dashboard');
            }}
          >
            Dashboard
          </Link>
          <Link
            color="inherit"
            href="#"
            onClick={(e: React.MouseEvent) => (e) => {
              e.preventDefault();
              navigate('/classes');
            }}
          >
            Classes
          </Link>
          <Typography color="text.primary">{classData.name}</Typography>
        </Breadcrumbs>
      </Box>

      {/* Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <Box display="flex" alignItems="center" gap={1} mb={2}>
              <Button
                startIcon={<ArrowBackIcon />}
                onClick={(e: React.MouseEvent) => () => navigate('/classes')}
                variant="text"
              >
                Back to Classes
              </Button>
            </Box>
            <Typography variant="h4" gutterBottom>
              {classData.name}
            </Typography>
            <Box display="flex" gap={2} alignItems="center">
              <Chip
                label={classData.subject}
                color="primary"
                icon={<SchoolIcon />}
              />
              <Chip
                label={`${studentCount} / ${classData.max_students} Students`}
                color={studentCount >= classData.max_students ? 'error' : 'default'}
              />
              <Chip
                label={classData.status}
                color={classData.status === 'active' ? 'success' : 'default'}
                size="small"
              />
              {classData.room && (
                <Typography variant="body2" color="text.secondary">
                  Room: {classData.room}
                </Typography>
              )}
            </Box>
            {classData.description && (
              <Typography variant="body1" color="text.secondary" sx={{ mt: 2 }}>
                {classData.description}
              </Typography>
            )}
            {classData.schedule && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Schedule: {classData.schedule}
              </Typography>
            )}
          </Box>
          {canManage && (
            <Box>
              <Button
                variant="contained"
                startIcon={<SettingsIcon />}
                onClick={(e: React.MouseEvent) => () => navigate(`/classes/${classId}/settings`)}
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
          aria-label="class detail tabs"
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<SchoolIcon />} label="Overview" {...a11yProps(0)} />
          {canManage && (
            <Tab icon={<PeopleIcon />} label="Students" {...a11yProps(1)} />
          )}
          <Tab icon={<AssignmentIcon />} label="Assignments" {...a11yProps(2)} />
          <Tab icon={<AnalyticsIcon />} label="Analytics" {...a11yProps(3)} />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Class Overview
          </Typography>
          <Box display="grid" gridTemplateColumns="repeat(auto-fit, minmax(250px, 1fr))" gap={3}>
            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                Subject
              </Typography>
              <Typography variant="body1">{classData.subject}</Typography>
            </Box>
            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                Teacher
              </Typography>
              <Typography variant="body1">
                {classData.teacher_name || 'Loading...'}
              </Typography>
            </Box>
            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                Schedule
              </Typography>
              <Typography variant="body1">
                {classData.schedule || 'Not set'}
              </Typography>
            </Box>
            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                Room
              </Typography>
              <Typography variant="body1">{classData.room || 'Not set'}</Typography>
            </Box>
            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                Created
              </Typography>
              <Typography variant="body1">
                {new Date(classData.created_at).toLocaleDateString()}
              </Typography>
            </Box>
            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                Status
              </Typography>
              <Chip
                label={classData.status}
                color={classData.status === 'active' ? 'success' : 'default'}
                size="small"
              />
            </Box>
          </Box>
          {classData.description && (
            <Box mt={3}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Description
              </Typography>
              <Typography variant="body1">{classData.description}</Typography>
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
          <Typography variant="h6" gutterBottom>
            Assignments
          </Typography>
          <Alert severity="info">
            Assignment management coming soon. Teachers will be able to create, distribute, and
            grade assignments here.
          </Alert>
        </Paper>
      </TabPanel>

      <TabPanel value={tabValue} index={canManage ? 3 : 2}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Analytics
          </Typography>
          <Alert severity="info">
            Class analytics and performance metrics will be displayed here, including student
            progress, attendance, and assignment completion rates.
          </Alert>
        </Paper>
      </TabPanel>
    </Container>
  );
};