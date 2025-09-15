import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  IconButton,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Divider,
  Paper,
} from '@mui/material';
import {
  ArrowBack,
  Edit,
  Delete,
  School,
  Schedule,
  People,
  Assignment,
  RocketLaunch,
} from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../../store';
import { getClass } from '../../services/api';
import { addNotification } from '../../store/slices/uiSlice';

interface ClassDetailsData {
  id: number;
  name: string;
  subject: string;
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

  useEffect(() => {
    if (id) {
      fetchClassDetails(id);
    }
  }, [id]);

  const fetchClassDetails = async (classId: string) => {
    try {
      setLoading(true);
      const data = await getClass(classId);
      setClassData(data);
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
  };

  const handlePushToRoblox = () => {
    dispatch(
      addNotification({
        type: 'info',
        message: 'Pushing class to Roblox environment...',
      })
    );
    // TODO: Implement Roblox push functionality
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
      <Box sx={{ width: '100%' }}>
        <LinearProgress />
      </Box>
    );
  }

  if (!classData) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography>Class not found</Typography>
        <Button onClick={() => navigate('/classes')} startIcon={<ArrowBack />}>
          Back to Classes
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton onClick={() => navigate('/classes')}>
            <ArrowBack />
          </IconButton>
          <Typography variant="h4">{classData.name}</Typography>
          <Chip 
            label={classData.status || 'Active'} 
            color={classData.status === 'active' ? 'success' : 'default'}
            size="small"
          />
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="contained"
            color="primary"
            startIcon={<RocketLaunch />}
            onClick={handlePushToRoblox}
          >
            Push to Roblox
          </Button>
          <IconButton onClick={handleEdit}>
            <Edit />
          </IconButton>
          <IconButton onClick={handleDelete} color="error">
            <Delete />
          </IconButton>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Main Info Card */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Class Information
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <School color="action" />
                    <Box>
                      <Typography variant="caption" color="textSecondary">
                        Subject
                      </Typography>
                      <Typography>{classData.subject || 'Not specified'}</Typography>
                    </Box>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <People color="action" />
                    <Box>
                      <Typography variant="caption" color="textSecondary">
                        Students
                      </Typography>
                      <Typography>{classData.student_count || 0} enrolled</Typography>
                    </Box>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <Schedule color="action" />
                    <Box>
                      <Typography variant="caption" color="textSecondary">
                        Schedule
                      </Typography>
                      <Typography>{classData.schedule || 'Not set'}</Typography>
                    </Box>
                  </Box>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <Assignment color="action" />
                    <Box>
                      <Typography variant="caption" color="textSecondary">
                        Grade Level
                      </Typography>
                      <Typography>
                        {classData.grade_level ? `Grade ${classData.grade_level}` : 'All grades'}
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="caption" color="textSecondary">
                    Description
                  </Typography>
                  <Typography>
                    {classData.description || 'No description provided'}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Side Info Cards */}
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Teacher
              </Typography>
              <Typography>{classData.teacher_name || 'Not assigned'}</Typography>
            </CardContent>
          </Card>

          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Room
              </Typography>
              <Typography>{classData.room || 'Virtual'}</Typography>
            </CardContent>
          </Card>

          {classData.resources && classData.resources.length > 0 && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Resources
                </Typography>
                <List dense>
                  {classData.resources.map((resource, index) => (
                    <ListItem key={index}>
                      <ListItemText primary={resource.name} />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          )}
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Activity
              </Typography>
              <Typography color="textSecondary">
                No recent activity to display
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ClassDetails;