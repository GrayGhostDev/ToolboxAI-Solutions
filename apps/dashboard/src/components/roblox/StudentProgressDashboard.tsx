/**
 * StudentProgressDashboard Component
 * 
 * Real-time monitoring of student progress in Roblox educational environments
 * Displays individual and class-wide metrics with live updates
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Avatar,
  AvatarGroup,
  Chip,
  IconButton,
  Button,
  LinearProgress,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Paper,
  Tooltip,
  Badge,
  Stack,
  Alert,
  AlertTitle,
  useTheme,
  alpha,
  Divider,
  ToggleButton,
  ToggleButtonGroup,
  TextField,
  InputAdornment,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import {
  School,
  Person,
  Groups,
  TrendingUp,
  TrendingDown,
  AccessTime,
  CheckCircle,
  Warning,
  Error,
  Refresh,
  FilterList,
  Search,
  GridView,
  TableChart,
  MoreVert,
  Visibility,
  Message,
  Help,
  Star,
  EmojiEvents,
  LocalFireDepartment,
  PlayArrow,
  Pause,
  Stop,
  Assignment,
  Quiz,
  Speed,
  Circle
} from '@mui/icons-material';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import { ProgressUpdate, WebSocketMessageType } from '../../types/websocket';

interface StudentProgress {
  userId: string;
  username: string;
  avatar?: string;
  status: 'online' | 'offline' | 'idle' | 'active';
  currentActivity?: string;
  location?: string;
  sessionDuration: number;
  progress: {
    overall: number;
    objectives: Array<{
      id: string;
      name: string;
      completed: boolean;
      progress: number;
    }>;
    quizzes: Array<{
      id: string;
      name: string;
      score: number;
      attempts: number;
      completed: boolean;
    }>;
  };
  metrics: {
    engagement: number;
    accuracy: number;
    speed: number;
    collaboration: number;
    streak: number;
  };
  achievements: string[];
  needsHelp: boolean;
  lastUpdate: Date;
}

interface ClassMetrics {
  totalStudents: number;
  activeStudents: number;
  averageProgress: number;
  averageEngagement: number;
  completionRate: number;
  topPerformers: string[];
  strugglingStudents: string[];
}

type ViewMode = 'grid' | 'table';
type SortField = 'username' | 'progress' | 'engagement' | 'lastUpdate';
type SortOrder = 'asc' | 'desc';

const getStatusColor = (status: StudentProgress['status']) => {
  switch (status) {
    case 'active': return 'success';
    case 'online': return 'primary';
    case 'idle': return 'warning';
    case 'offline': return 'default';
    default: return 'default';
  }
};

const getMetricColor = (value: number) => {
  if (value >= 80) return 'success';
  if (value >= 60) return 'warning';
  return 'error';
};

export const StudentProgressDashboard: React.FC = () => {
  const theme = useTheme();
  const { on, sendMessage, isConnected } = useWebSocketContext();
  
  const [students, setStudents] = useState<StudentProgress[]>([]);
  const [classMetrics, setClassMetrics] = useState<ClassMetrics | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState<SortField>('username');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const [selectedStudent, setSelectedStudent] = useState<string | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // WebSocket subscriptions
  useEffect(() => {
    if (!isConnected) return;

    const unsubscribeProgress = on(WebSocketMessageType.PROGRESS_UPDATE, (data: ProgressUpdate) => {
      updateStudentProgress(data);
    });

    const unsubscribeStatus = on(WebSocketMessageType.STUDENT_STATUS, (data: any) => {
      updateStudentStatus(data);
    });

    const unsubscribeMetrics = on(WebSocketMessageType.CLASS_METRICS, (data: any) => {
      setClassMetrics(data);
    });

    // Request initial data
    sendMessage(WebSocketMessageType.REQUEST_PROGRESS, {});

    return () => {
      unsubscribeProgress();
      unsubscribeStatus();
      unsubscribeMetrics();
    };
  }, [isConnected]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh || !isConnected) return;

    const interval = setInterval(() => {
      sendMessage(WebSocketMessageType.REQUEST_PROGRESS, {});
    }, 5000);

    return () => clearInterval(interval);
  }, [autoRefresh, isConnected]);

  const updateStudentProgress = (update: ProgressUpdate) => {
    setStudents(prev => {
      const index = prev.findIndex(s => s.userId === update.userId);
      if (index === -1) {
        // New student
        return [...prev, createStudentFromUpdate(update)];
      }
      // Update existing student
      const updated = [...prev];
      updated[index] = {
        ...updated[index],
        ...update,
        lastUpdate: new Date()
      };
      return updated;
    });
  };

  const updateStudentStatus = (data: any) => {
    setStudents(prev => prev.map(student => {
      if (student.userId === data.userId) {
        return {
          ...student,
          status: data.status,
          currentActivity: data.activity,
          location: data.location
        };
      }
      return student;
    }));
  };

  const createStudentFromUpdate = (update: any): StudentProgress => ({
    userId: update.userId,
    username: update.username || `Student ${update.userId}`,
    status: 'online',
    sessionDuration: 0,
    progress: update.progress || { overall: 0, objectives: [], quizzes: [] },
    metrics: update.metrics || {
      engagement: 0,
      accuracy: 0,
      speed: 0,
      collaboration: 0,
      streak: 0
    },
    achievements: [],
    needsHelp: false,
    lastUpdate: new Date()
  });

  // Filtering and sorting
  const filteredAndSortedStudents = useMemo(() => {
    let filtered = students.filter(student =>
      student.username.toLowerCase().includes(searchQuery.toLowerCase())
    );

    filtered.sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortField) {
        case 'username':
          aValue = a.username;
          bValue = b.username;
          break;
        case 'progress':
          aValue = a.progress.overall;
          bValue = b.progress.overall;
          break;
        case 'engagement':
          aValue = a.metrics.engagement;
          bValue = b.metrics.engagement;
          break;
        case 'lastUpdate':
          aValue = a.lastUpdate;
          bValue = b.lastUpdate;
          break;
        default:
          aValue = a.username;
          bValue = b.username;
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return filtered;
  }, [students, searchQuery, sortField, sortOrder]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const handleStudentAction = (action: string, studentId: string) => {
    switch (action) {
      case 'view':
        setSelectedStudent(studentId);
        break;
      case 'message':
        sendMessage(WebSocketMessageType.TEACHER_MESSAGE, {
          studentId,
          type: 'direct'
        });
        break;
      case 'help':
        sendMessage(WebSocketMessageType.TEACHER_INTERVENTION, {
          studentId,
          type: 'assistance'
        });
        break;
    }
    setAnchorEl(null);
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', gap: 2 }}>
      {/* Header */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <School color="primary" fontSize="large" />
              <Box>
                <Typography variant="h5">Student Progress Dashboard</Typography>
                <Typography variant="body2" color="text.secondary">
                  Real-time monitoring of student activity and progress
                </Typography>
              </Box>
            </Box>
            
            <Stack direction="row" spacing={1}>
              <Chip
                icon={<Circle sx={{ fontSize: 12 }} />}
                label={isConnected ? 'Live' : 'Offline'}
                color={isConnected ? 'success' : 'error'}
                size="small"
              />
              <IconButton
                size="small"
                onClick={() => setAutoRefresh(!autoRefresh)}
                color={autoRefresh ? 'primary' : 'default'}
              >
                <Refresh />
              </IconButton>
            </Stack>
          </Box>
        </CardContent>
      </Card>

      {/* Class Metrics */}
      {classMetrics && (
        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4">{classMetrics.activeStudents}</Typography>
                    <Typography variant="body2" color="text.secondary">Active Students</Typography>
                  </Box>
                  <Groups color="primary" />
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={(classMetrics.activeStudents / classMetrics.totalStudents) * 100}
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={6} sm={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4">{Math.round(classMetrics.averageProgress)}%</Typography>
                    <Typography variant="body2" color="text.secondary">Avg Progress</Typography>
                  </Box>
                  <TrendingUp color="success" />
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={classMetrics.averageProgress}
                  color="success"
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={6} sm={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4">{Math.round(classMetrics.averageEngagement)}%</Typography>
                    <Typography variant="body2" color="text.secondary">Engagement</Typography>
                  </Box>
                  <LocalFireDepartment color="warning" />
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={classMetrics.averageEngagement}
                  color="warning"
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={6} sm={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4">{Math.round(classMetrics.completionRate)}%</Typography>
                    <Typography variant="body2" color="text.secondary">Completion</Typography>
                  </Box>
                  <CheckCircle color="success" />
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={classMetrics.completionRate}
                  color="success"
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Controls */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, flexWrap: 'wrap' }}>
            <TextField
              size="small"
              placeholder="Search students..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                )
              }}
              sx={{ minWidth: 200 }}
            />

            <Box sx={{ display: 'flex', gap: 1 }}>
              <ToggleButtonGroup
                value={viewMode}
                exclusive
                onChange={(e, value) => value && setViewMode(value)}
                size="small"
              >
                <ToggleButton value="grid">
                  <GridView />
                </ToggleButton>
                <ToggleButton value="table">
                  <TableChart />
                </ToggleButton>
              </ToggleButtonGroup>

              <Button
                variant="outlined"
                startIcon={<FilterList />}
                size="small"
              >
                Filters
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Student List/Grid */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {viewMode === 'grid' ? (
          <Grid container spacing={2}>
            {filteredAndSortedStudents.map((student) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={student.userId}>
                <Card
                  sx={{
                    position: 'relative',
                    border: student.needsHelp ? 2 : 1,
                    borderColor: student.needsHelp ? 'warning.main' : alpha(theme.palette.divider, 0.2),
                    transition: 'all 0.3s',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: theme.shadows[4]
                    }
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Badge
                          overlap="circular"
                          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                          badgeContent={
                            <Circle
                              sx={{
                                fontSize: 10,
                                color: getStatusColor(student.status) === 'success' ? 'success.main' :
                                       getStatusColor(student.status) === 'primary' ? 'primary.main' :
                                       getStatusColor(student.status) === 'warning' ? 'warning.main' :
                                       'text.disabled'
                              }}
                            />
                          }
                        >
                          <Avatar src={student.avatar}>
                            {student.username[0].toUpperCase()}
                          </Avatar>
                        </Badge>
                        <Box>
                          <Typography variant="subtitle2" fontWeight="bold">
                            {student.username}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {student.currentActivity || 'No activity'}
                          </Typography>
                        </Box>
                      </Box>
                      
                      <IconButton
                        size="small"
                        onClick={(e) => setAnchorEl(e.currentTarget)}
                      >
                        <MoreVert />
                      </IconButton>
                    </Box>

                    <Box sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Typography variant="caption" color="text.secondary">
                          Overall Progress
                        </Typography>
                        <Typography variant="caption" fontWeight="bold">
                          {student.progress.overall}%
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={student.progress.overall}
                        color={getMetricColor(student.progress.overall) as any}
                        sx={{ height: 6, borderRadius: 1 }}
                      />
                    </Box>

                    <Grid container spacing={1}>
                      <Grid item xs={6}>
                        <Box sx={{ textAlign: 'center' }}>
                          <Speed fontSize="small" color="action" />
                          <Typography variant="caption" display="block" color="text.secondary">
                            Engagement
                          </Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {student.metrics.engagement}%
                          </Typography>
                        </Box>
                      </Grid>
                      <Grid item xs={6}>
                        <Box sx={{ textAlign: 'center' }}>
                          <Quiz fontSize="small" color="action" />
                          <Typography variant="caption" display="block" color="text.secondary">
                            Accuracy
                          </Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {student.metrics.accuracy}%
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>

                    {student.achievements.length > 0 && (
                      <Box sx={{ mt: 2, display: 'flex', gap: 0.5 }}>
                        {student.achievements.slice(0, 3).map((achievement, index) => (
                          <Tooltip key={index} title={achievement}>
                            <EmojiEvents fontSize="small" color="warning" />
                          </Tooltip>
                        ))}
                        {student.achievements.length > 3 && (
                          <Typography variant="caption" color="text.secondary">
                            +{student.achievements.length - 3}
                          </Typography>
                        )}
                      </Box>
                    )}

                    {student.needsHelp && (
                      <Alert severity="warning" sx={{ mt: 2, py: 0 }}>
                        <Typography variant="caption">Needs assistance</Typography>
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        ) : (
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>
                    <TableSortLabel
                      active={sortField === 'username'}
                      direction={sortField === 'username' ? sortOrder : 'asc'}
                      onClick={() => handleSort('username')}
                    >
                      Student
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Activity</TableCell>
                  <TableCell align="center">
                    <TableSortLabel
                      active={sortField === 'progress'}
                      direction={sortField === 'progress' ? sortOrder : 'asc'}
                      onClick={() => handleSort('progress')}
                    >
                      Progress
                    </TableSortLabel>
                  </TableCell>
                  <TableCell align="center">
                    <TableSortLabel
                      active={sortField === 'engagement'}
                      direction={sortField === 'engagement' ? sortOrder : 'asc'}
                      onClick={() => handleSort('engagement')}
                    >
                      Engagement
                    </TableSortLabel>
                  </TableCell>
                  <TableCell align="center">Accuracy</TableCell>
                  <TableCell align="center">Duration</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredAndSortedStudents.map((student) => (
                  <TableRow key={student.userId}>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Avatar src={student.avatar} sx={{ width: 32, height: 32 }}>
                          {student.username[0].toUpperCase()}
                        </Avatar>
                        <Box>
                          <Typography variant="body2">{student.username}</Typography>
                          {student.needsHelp && (
                            <Chip label="Needs Help" size="small" color="warning" />
                          )}
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={student.status}
                        size="small"
                        color={getStatusColor(student.status) as any}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {student.currentActivity || '-'}
                      </Typography>
                      {student.location && (
                        <Typography variant="caption" color="text.secondary">
                          @ {student.location}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell align="center">
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <LinearProgress
                          variant="determinate"
                          value={student.progress.overall}
                          sx={{ flex: 1, height: 6 }}
                        />
                        <Typography variant="body2">
                          {student.progress.overall}%
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="center">
                      <Typography
                        variant="body2"
                        color={getMetricColor(student.metrics.engagement) === 'success' ? 'success.main' :
                               getMetricColor(student.metrics.engagement) === 'warning' ? 'warning.main' :
                               'error.main'}
                      >
                        {student.metrics.engagement}%
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Typography variant="body2">
                        {student.metrics.accuracy}%
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Typography variant="body2">
                        {formatDuration(student.sessionDuration)}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Stack direction="row" spacing={0.5} justifyContent="center">
                        <IconButton
                          size="small"
                          onClick={() => handleStudentAction('view', student.userId)}
                        >
                          <Visibility fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleStudentAction('message', student.userId)}
                        >
                          <Message fontSize="small" />
                        </IconButton>
                        {student.needsHelp && (
                          <IconButton
                            size="small"
                            color="warning"
                            onClick={() => handleStudentAction('help', student.userId)}
                          >
                            <Help fontSize="small" />
                          </IconButton>
                        )}
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Box>

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
      >
        <MenuItem onClick={() => handleStudentAction('view', selectedStudent!)}>
          <ListItemIcon>
            <Visibility fontSize="small" />
          </ListItemIcon>
          <ListItemText>View Details</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleStudentAction('message', selectedStudent!)}>
          <ListItemIcon>
            <Message fontSize="small" />
          </ListItemIcon>
          <ListItemText>Send Message</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleStudentAction('help', selectedStudent!)}>
          <ListItemIcon>
            <Help fontSize="small" />
          </ListItemIcon>
          <ListItemText>Offer Help</ListItemText>
        </MenuItem>
      </Menu>

      {/* Empty State */}
      {filteredAndSortedStudents.length === 0 && (
        <Box
          sx={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
            gap: 2
          }}
        >
          <Groups sx={{ fontSize: 64, color: 'text.disabled' }} />
          <Typography variant="h6" color="text.secondary">
            No students online
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Students will appear here when they join the session
          </Typography>
        </Box>
      )}
    </Box>
  );
};