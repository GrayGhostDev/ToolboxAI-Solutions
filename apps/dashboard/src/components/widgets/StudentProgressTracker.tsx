import React, { useEffect, useState } from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import LinearProgress from '@mui/material/LinearProgress';
import Avatar from '@mui/material/Avatar';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemAvatar from '@mui/material/ListItemAvatar';
import ListItemText from '@mui/material/ListItemText';
import Chip from '@mui/material/Chip';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import CircularProgress from '@mui/material/CircularProgress';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';

import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  TrendingDown,
  School,
  EmojiEvents,
  CheckCircle,
  Warning,
  Search,
  Refresh,
  Visibility,
  Assignment,
  Timeline,
  Close,
} from '@mui/icons-material';
import useRealTimeData from '../../hooks/useRealTimeData';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import { useAppDispatch } from '../../store';
import { addNotification } from '../../store/slices/uiSlice';

interface Student {
  id: string;
  name: string;
  avatar?: string;
  grade: number;
  overallProgress: number;
  xp: number;
  level: number;
  streak: number;
  lastActive: string;
  subjects: {
    name: string;
    progress: number;
    lastScore: number;
  }[];
  badges: string[];
  status: 'online' | 'offline' | 'idle';
}

interface ProgressMetrics {
  totalStudents: number;
  averageProgress: number;
  topPerformers: number;
  needsAttention: number;
  activeNow: number;
}

const StudentProgressTracker: React.FunctionComponent<Record<string, any>> = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { isConnected } = useWebSocketContext();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null);
  const [studentDetailsOpen, setStudentDetailsOpen] = useState(false);
  
  // Use real-time data hook for student progress
  const { data: progressData, loading, refetch } = useRealTimeData<any>('student-progress', {
    refreshInterval: 10000, // Refresh every 10 seconds
  });

  const [metrics, setMetrics] = useState<ProgressMetrics>({
    totalStudents: 0,
    averageProgress: 0,
    topPerformers: 0,
    needsAttention: 0,
    activeNow: 0,
  });

  const [students, setStudents] = useState<Student[]>([]);

  // Update data when real-time updates arrive
  useEffect(() => {
    if (progressData) {
const anyProgress: any = progressData as any;
      setMetrics(anyProgress.metrics || {
        totalStudents: anyProgress.students?.length || 0,
        averageProgress: (
          anyProgress.students?.reduce((acc: number, s: any) => acc + s.overallProgress, 0) /
          (anyProgress.students?.length || 1)
        ) || 0,
        topPerformers: anyProgress.students?.filter((s: any) => s.overallProgress >= 80).length || 0,
        needsAttention: anyProgress.students?.filter((s: any) => s.overallProgress < 60).length || 0,
        activeNow: anyProgress.students?.filter((s: any) => s.status === 'online').length || 0,
      });
      setStudents(anyProgress.students || mockStudents);
    } else {
      // Use mock data if no real data available
      setStudents(mockStudents);
      setMetrics({
        totalStudents: mockStudents.length,
        averageProgress: 72,
        topPerformers: 3,
        needsAttention: 2,
        activeNow: 5,
      });
    }
  }, [progressData]);

  // Mock data for demonstration
  const mockStudents: Student[] = [
    {
      id: '1',
      name: 'Alice Johnson',
      grade: 8,
      overallProgress: 92,
      xp: 2450,
      level: 24,
      streak: 15,
      lastActive: '2 minutes ago',
      subjects: [
        { name: 'Math', progress: 95, lastScore: 98 },
        { name: 'Science', progress: 88, lastScore: 85 },
        { name: 'English', progress: 93, lastScore: 90 },
      ],
      badges: ['Top Performer', 'Perfect Week', 'Math Wizard'],
      status: 'online',
    },
    {
      id: '2',
      name: 'Bob Smith',
      grade: 8,
      overallProgress: 78,
      xp: 1820,
      level: 18,
      streak: 7,
      lastActive: '1 hour ago',
      subjects: [
        { name: 'Math', progress: 75, lastScore: 72 },
        { name: 'Science', progress: 82, lastScore: 88 },
        { name: 'English', progress: 77, lastScore: 75 },
      ],
      badges: ['Consistent Learner', 'Science Explorer'],
      status: 'idle',
    },
    {
      id: '3',
      name: 'Charlie Brown',
      grade: 7,
      overallProgress: 65,
      xp: 1350,
      level: 13,
      streak: 3,
      lastActive: '3 hours ago',
      subjects: [
        { name: 'Math', progress: 62, lastScore: 58 },
        { name: 'Science', progress: 70, lastScore: 68 },
        { name: 'English', progress: 63, lastScore: 65 },
      ],
      badges: ['Getting Started'],
      status: 'offline',
    },
    {
      id: '4',
      name: 'Diana Prince',
      grade: 9,
      overallProgress: 88,
      xp: 2680,
      level: 26,
      streak: 21,
      lastActive: '5 minutes ago',
      subjects: [
        { name: 'Math', progress: 90, lastScore: 92 },
        { name: 'Science', progress: 85, lastScore: 88 },
        { name: 'English', progress: 89, lastScore: 87 },
      ],
      badges: ['Streak Master', 'All-Rounder', 'Top 10%'],
      status: 'online',
    },
    {
      id: '5',
      name: 'Eve Wilson',
      grade: 7,
      overallProgress: 55,
      xp: 980,
      level: 9,
      streak: 1,
      lastActive: '1 day ago',
      subjects: [
        { name: 'Math', progress: 48, lastScore: 45 },
        { name: 'Science', progress: 60, lastScore: 62 },
        { name: 'English', progress: 57, lastScore: 55 },
      ],
      badges: [],
      status: 'offline',
    },
  ];

  // Filter students based on search
  const filteredStudents = students.filter(student =>
    student.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Get progress color
  const getProgressColor = (progress: number) => {
    if (progress >= 80) return 'success';
    if (progress >= 60) return 'warning';
    return 'error';
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return '#4caf50';
      case 'idle': return '#ff9800';
      case 'offline': return '#9e9e9e';
      default: return '#9e9e9e';
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Metrics Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography color="textSecondary" gutterBottom variant="caption">
                Total Students
              </Typography>
              <Typography variant="h4">{metrics.totalStudents}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography color="textSecondary" gutterBottom variant="caption">
                Avg Progress
              </Typography>
              <Typography variant="h4" color="primary">
                {metrics.averageProgress}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography color="textSecondary" gutterBottom variant="caption">
                Top Performers
              </Typography>
              <Typography variant="h4" color="success.main">
                {metrics.topPerformers}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography color="textSecondary" gutterBottom variant="caption">
                Needs Attention
              </Typography>
              <Typography variant="h4" color="error">
                {metrics.needsAttention}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography color="textSecondary" gutterBottom variant="caption">
                Active Now
              </Typography>
              <Typography variant="h4" color="success.main">
                {metrics.activeNow}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Student Progress Table */}
      <Card>
        <CardHeader
          title="Student Progress Tracker"
          action={
            <Box display="flex" gap={1}>
              <TextField
                size="small"
                placeholder="Search students..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  ),
                }}
                sx={{ mr: 2 }}
              />
              <Tooltip title="Refresh data">
                <IconButton onClick={(e: React.MouseEvent) => () => refetch()}>
                  <Refresh />
                </IconButton>
              </Tooltip>
            </Box>
          }
        />
        <CardContent>
          {loading ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Student</TableCell>
                    <TableCell align="center">Status</TableCell>
                    <TableCell align="center">Overall Progress</TableCell>
                    <TableCell align="center">Level</TableCell>
                    <TableCell align="center">Streak</TableCell>
                    <TableCell align="center">Badges</TableCell>
                    <TableCell align="center">Last Active</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredStudents.map((student) => (
                    <TableRow key={student.id} hover>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={2}>
                          <Avatar sx={{ width: 32, height: 32 }}>
                            {student.name[0]}
                          </Avatar>
                          <Box>
                            <Typography variant="body2" fontWeight={500}>
                              {student.name}
                            </Typography>
                            <Typography variant="caption" color="textSecondary">
                              Grade {student.grade}
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          size="small"
                          label={student.status}
                          sx={{
                            bgcolor: getStatusColor(student.status),
                            color: 'white',
                          }}
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Box sx={{ width: '100%', minWidth: 100 }}>
                          <Box display="flex" alignItems="center" gap={1}>
                            <LinearProgress
                              variant="determinate"
                              value={student.overallProgress}
                              color={getProgressColor(student.overallProgress)}
                              sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                            />
                            <Typography variant="body2" fontWeight={500}>
                              {student.overallProgress}%
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        <Box display="flex" alignItems="center" justifyContent="center" gap={0.5}>
                          <EmojiEvents fontSize="small" color="warning" />
                          <Typography variant="body2">{student.level}</Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        <Box display="flex" alignItems="center" justifyContent="center" gap={0.5}>
                          <Typography variant="body2">{student.streak}</Typography>
                          <Typography>🔥</Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="body2">
                          {student.badges.length > 0 ? student.badges.length : '-'}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="caption" color="textSecondary">
                          {student.lastActive}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={(e: React.MouseEvent) => () => {
                              setSelectedStudent(student);
                              setStudentDetailsOpen(true);
                            }}
                          >
                            <Visibility />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="View Assignments">
                          <IconButton 
                            size="small"
                            onClick={() => {
                              dispatch(addNotification({
                                type: 'info',
                                message: `Loading assignments for ${student.name}...`
                              }));
                              // Navigate to assessments page with student filter
                              navigate(`/assessments?studentId=${student.id}&studentName=${encodeURIComponent(student.name)}`);
                            }}
                          >
                            <Assignment />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="View Timeline">
                          <IconButton 
                            size="small"
                            onClick={() => {
                              dispatch(addNotification({
                                type: 'info',
                                message: `Loading progress timeline for ${student.name}...`
                              }));
                              // Navigate to progress page with student filter
                              navigate(`/progress?studentId=${student.id}&view=timeline`);
                            }}
                          >
                            <Timeline />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Connection Status */}
      {!isConnected && (
        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Chip
            label="Offline - Showing cached data"
            color="error"
            size="small"
          />
        </Box>
      )}

      {/* Student Details Dialog */}
      <Dialog 
        open={studentDetailsOpen} 
        onClose={() => setStudentDetailsOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">
              {selectedStudent?.name} - Progress Details
            </Typography>
            <IconButton onClick={(e: React.MouseEvent) => () => setStudentDetailsOpen(false)}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {selectedStudent && (
            <Grid container spacing={3}>
              {/* Student Overview */}
              <Grid item xs={12}>
                <Box display="flex" alignItems="center" gap={2} mb={2}>
                  <Avatar sx={{ width: 64, height: 64 }}>
                    {selectedStudent.name[0]}
                  </Avatar>
                  <Box>
                    <Typography variant="h5">{selectedStudent.name}</Typography>
                    <Typography variant="body2" color="textSecondary">
                      Grade {selectedStudent.grade} • Level {selectedStudent.level}
                    </Typography>
                    <Chip 
                      label={selectedStudent.status} 
                      size="small"
                      sx={{ 
                        mt: 1,
                        bgcolor: getStatusColor(selectedStudent.status),
                        color: 'white'
                      }}
                    />
                  </Box>
                </Box>
              </Grid>

              {/* Progress Metrics */}
              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="caption" color="textSecondary">
                    Overall Progress
                  </Typography>
                  <Typography variant="h4" color="primary">
                    {selectedStudent.overallProgress}%
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={selectedStudent.overallProgress}
                    sx={{ mt: 1 }}
                  />
                </Paper>
              </Grid>
              
              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="caption" color="textSecondary">
                    XP Points
                  </Typography>
                  <Typography variant="h4">
                    {selectedStudent.xp}
                  </Typography>
                </Paper>
              </Grid>
              
              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="caption" color="textSecondary">
                    Current Streak
                  </Typography>
                  <Typography variant="h4">
                    {selectedStudent.streak} 🔥
                  </Typography>
                </Paper>
              </Grid>

              {/* Subject Progress */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Subject Progress
                </Typography>
                <List>
                  {selectedStudent.subjects.map((subject, index) => (
                    <ListItem key={index}>
                      <ListItemText 
                        primary={subject.name}
                        secondary={`Last Score: ${subject.lastScore}%`}
                      />
                      <Box sx={{ width: '50%', display: 'flex', alignItems: 'center' }}>
                        <Box sx={{ width: '100%', mr: 1 }}>
                          <LinearProgress 
                            variant="determinate" 
                            value={subject.progress}
                            color={subject.progress >= 70 ? 'success' : 'warning'}
                          />
                        </Box>
                        <Typography variant="body2" color="textSecondary">
                          {subject.progress}%
                        </Typography>
                      </Box>
                    </ListItem>
                  ))}
                </List>
              </Grid>

              {/* Badges */}
              {selectedStudent.badges.length > 0 && (
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    Badges Earned
                  </Typography>
                  <Box display="flex" gap={1} flexWrap="wrap">
                    {selectedStudent.badges.map((badge, index) => (
                      <Chip key={index} label={badge} />
                    ))}
                  </Box>
                </Grid>
              )}
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={(e: React.MouseEvent) => () => {
              setStudentDetailsOpen(false);
              navigate(`/progress?studentId=${selectedStudent?.id}`);
            }}
          >
            View Full Progress Report
          </Button>
          <Button 
            variant="contained"
            onClick={(e: React.MouseEvent) => () => setStudentDetailsOpen(false)}
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StudentProgressTracker;