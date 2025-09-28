/**
 * RobloxSessionManager Component
 * 
 * Manages Roblox educational game sessions
 * Handles session creation, configuration, and lifecycle management
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardActions,
  Typography,
  Grid,
  Button,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  FormControlLabel,
  Checkbox,
  Switch,
  Slider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Avatar,
  AvatarGroup,
  Tooltip,
  Alert,
  AlertTitle,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Paper,
  Divider,
  Stack,
  Badge,
  useTheme,
  alpha,
  FormGroup,
  FormLabel,
  RadioGroup,
  Radio,
  Autocomplete
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Stop,
  Settings,
  People,
  Schedule,
  Lock,
  LockOpen,
  Add,
  Edit,
  Delete,
  ContentCopy,
  Share,
  QrCode2,
  Link,
  Timer,
  School,
  Assignment,
  Quiz,
  Terrain,
  Games,
  EmojiEvents,
  Warning,
  CheckCircle,
  Info,
  Groups,
  PersonAdd,
  PersonRemove,
  Refresh,
  Download,
  Upload,
  Save,
  Cancel
} from '@mui/icons-material';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import { WebSocketMessageType } from '../../types/websocket';
import { useAppSelector } from '../../store';

interface RobloxSession {
  id: string;
  name: string;
  description?: string;
  status: 'draft' | 'ready' | 'active' | 'paused' | 'completed' | 'archived';
  createdAt: Date;
  startedAt?: Date;
  endedAt?: Date;
  settings: {
    maxPlayers: number;
    minPlayers: number;
    timeLimit?: number;
    accessType: 'public' | 'private' | 'invite-only';
    accessCode?: string;
    allowLateJoin: boolean;
    allowRejoin: boolean;
    recordSession: boolean;
    enableChat: boolean;
    enableVoice: boolean;
  };
  content: {
    subject: string;
    gradeLevel: number;
    environmentType: string;
    objectives: string[];
    hasQuiz: boolean;
    quizSettings?: {
      numQuestions: number;
      timePerQuestion?: number;
      passingScore: number;
      allowRetake: boolean;
    };
  };
  participants: {
    teacherId: string;
    students: Array<{
      id: string;
      name: string;
      status: 'invited' | 'joined' | 'active' | 'left' | 'kicked';
      joinedAt?: Date;
      leftAt?: Date;
    }>;
  };
  metrics: {
    totalPlayers: number;
    activePlayers: number;
    averageProgress: number;
    completionRate: number;
  };
  gameServerInfo?: {
    serverId: string;
    serverUrl: string;
    placeId: string;
    jobId: string;
  };
}

interface SessionTemplate {
  id: string;
  name: string;
  description: string;
  settings: RobloxSession['settings'];
  content: RobloxSession['content'];
}

const SESSION_TEMPLATES: SessionTemplate[] = [
  {
    id: 'quick-math',
    name: 'Quick Math Challenge',
    description: '15-minute math practice session',
    settings: {
      maxPlayers: 30,
      minPlayers: 1,
      timeLimit: 15,
      accessType: 'public',
      allowLateJoin: true,
      allowRejoin: false,
      recordSession: true,
      enableChat: true,
      enableVoice: false
    },
    content: {
      subject: 'Mathematics',
      gradeLevel: 5,
      environmentType: 'classroom',
      objectives: ['Basic arithmetic', 'Problem solving'],
      hasQuiz: true,
      quizSettings: {
        numQuestions: 10,
        timePerQuestion: 60,
        passingScore: 70,
        allowRetake: true
      }
    }
  },
  {
    id: 'science-exploration',
    name: 'Science Exploration',
    description: 'Interactive science discovery session',
    settings: {
      maxPlayers: 25,
      minPlayers: 5,
      timeLimit: 30,
      accessType: 'private',
      allowLateJoin: false,
      allowRejoin: true,
      recordSession: true,
      enableChat: true,
      enableVoice: true
    },
    content: {
      subject: 'Science',
      gradeLevel: 7,
      environmentType: 'laboratory',
      objectives: ['Scientific method', 'Experimentation'],
      hasQuiz: true,
      quizSettings: {
        numQuestions: 15,
        passingScore: 75,
        allowRetake: false
      }
    }
  }
];

export const RobloxSessionManager: React.FC = () => {
  const theme = useTheme();
  const { sendMessage, on, isConnected } = useWebSocketContext();
  const currentUser = useAppSelector(state => state.user);
  
  const [sessions, setSessions] = useState<RobloxSession[]>([]);
  const [selectedSession, setSelectedSession] = useState<RobloxSession | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [newSession, setNewSession] = useState<Partial<RobloxSession>>({
    name: '',
    description: '',
    settings: {
      maxPlayers: 30,
      minPlayers: 1,
      accessType: 'public',
      allowLateJoin: true,
      allowRejoin: true,
      recordSession: true,
      enableChat: true,
      enableVoice: false
    },
    content: {
      subject: '',
      gradeLevel: 5,
      environmentType: 'classroom',
      objectives: [],
      hasQuiz: false
    }
  });
  const [studentSearch, setStudentSearch] = useState('');
  const [selectedStudents, setSelectedStudents] = useState<string[]>([]);

  // WebSocket event handlers
  useEffect(() => {
    if (!isConnected) return;

    const unsubscribeSessions = on(WebSocketMessageType.SESSION_UPDATE, (data: any) => {
      if (data.action === 'created') {
        setSessions(prev => [...prev, data.session]);
      } else if (data.action === 'updated') {
        setSessions(prev => prev.map(s => s.id === data.session.id ? data.session : s));
      } else if (data.action === 'deleted') {
        setSessions(prev => prev.filter(s => s.id !== data.sessionId));
      }
    });

    const unsubscribeStatus = on(WebSocketMessageType.SESSION_STATUS, (data: any) => {
      setSessions(prev => prev.map(session => {
        if (session.id === data.sessionId) {
          return {
            ...session,
            status: data.status,
            metrics: data.metrics || session.metrics
          };
        }
        return session;
      }));
    });

    // Load existing sessions
    sendMessage(WebSocketMessageType.REQUEST_SESSIONS, {});

    return () => {
      unsubscribeSessions();
      unsubscribeStatus();
    };
  }, [isConnected]);

  const handleCreateSession = () => {
    if (activeStep < 3) {
      setActiveStep(prev => prev + 1);
      return;
    }

    const session: RobloxSession = {
      id: `session_${Date.now()}`,
      name: newSession.name!,
      description: newSession.description,
      status: 'draft',
      createdAt: new Date(),
      settings: newSession.settings!,
      content: newSession.content!,
      participants: {
        teacherId: currentUser.userId!,
        students: selectedStudents.map(id => ({
          id,
          name: `Student ${id}`,
          status: 'invited' as const
        }))
      },
      metrics: {
        totalPlayers: 0,
        activePlayers: 0,
        averageProgress: 0,
        completionRate: 0
      }
    };

    sendMessage(WebSocketMessageType.CREATE_SESSION, session);
    setSessions(prev => [...prev, session]);
    setCreateDialogOpen(false);
    resetNewSession();
  };

  const handleStartSession = (sessionId: string) => {
    sendMessage(WebSocketMessageType.SESSION_CONTROL, {
      sessionId,
      action: 'start'
    });
    
    setSessions(prev => prev.map(s => {
      if (s.id === sessionId) {
        return { ...s, status: 'active', startedAt: new Date() };
      }
      return s;
    }));
  };

  const handlePauseSession = (sessionId: string) => {
    sendMessage(WebSocketMessageType.SESSION_CONTROL, {
      sessionId,
      action: 'pause'
    });
    
    setSessions(prev => prev.map(s => {
      if (s.id === sessionId) {
        return { ...s, status: 'paused' };
      }
      return s;
    }));
  };

  const handleStopSession = (sessionId: string) => {
    sendMessage(WebSocketMessageType.SESSION_CONTROL, {
      sessionId,
      action: 'stop'
    });
    
    setSessions(prev => prev.map(s => {
      if (s.id === sessionId) {
        return { ...s, status: 'completed', endedAt: new Date() };
      }
      return s;
    }));
  };

  const handleDeleteSession = (sessionId: string) => {
    sendMessage(WebSocketMessageType.DELETE_SESSION, { sessionId });
    setSessions(prev => prev.filter(s => s.id !== sessionId));
  };

  const handleDuplicateSession = (session: RobloxSession) => {
    const duplicated = {
      ...session,
      id: `session_${Date.now()}`,
      name: `${session.name} (Copy)`,
      status: 'draft' as const,
      createdAt: new Date(),
      startedAt: undefined,
      endedAt: undefined
    };
    
    sendMessage(WebSocketMessageType.CREATE_SESSION, duplicated);
    setSessions(prev => [...prev, duplicated]);
  };

  const handleApplyTemplate = (template: SessionTemplate) => {
    setNewSession({
      ...newSession,
      settings: { ...template.settings },
      content: { ...template.content }
    });
  };

  const resetNewSession = () => {
    setNewSession({
      name: '',
      description: '',
      settings: {
        maxPlayers: 30,
        minPlayers: 1,
        accessType: 'public',
        allowLateJoin: true,
        allowRejoin: true,
        recordSession: true,
        enableChat: true,
        enableVoice: false
      },
      content: {
        subject: '',
        gradeLevel: 5,
        environmentType: 'classroom',
        objectives: [],
        hasQuiz: false
      }
    });
    setActiveStep(0);
    setSelectedStudents([]);
  };

  const getSessionStatusColor = (status: RobloxSession['status']) => {
    switch (status) {
      case 'draft': return 'default';
      case 'ready': return 'info';
      case 'active': return 'success';
      case 'paused': return 'warning';
      case 'completed': return 'default';
      case 'archived': return 'default';
      default: return 'default';
    }
  };

  const generateAccessCode = () => {
    const code = Math.random().toString(36).substring(2, 8).toUpperCase();
    setNewSession(prev => ({
      ...prev,
      settings: {
        ...prev.settings!,
        accessCode: code
      }
    }));
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', gap: 2 }}>
      {/* Header */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Games color="primary" fontSize="large" />
              <Box>
                <Typography variant="h5">Session Manager</Typography>
                <Typography variant="body2" color="text.secondary">
                  Create and manage Roblox educational game sessions
                </Typography>
              </Box>
            </Box>
            
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setCreateDialogOpen(true)}
            >
              New Session
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Sessions Grid */}
      <Grid container spacing={2} sx={{ flex: 1, overflow: 'auto' }}>
        {sessions.map((session) => (
          <Grid item xs={12} md={6} lg={4} key={session.id}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                border: session.status === 'active' ? 2 : 1,
                borderColor: session.status === 'active' 
                  ? 'success.main' 
                  : alpha(theme.palette.divider, 0.2)
              }}
            >
              <CardContent sx={{ flex: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      {session.name}
                    </Typography>
                    <Chip
                      label={session.status}
                      size="small"
                      color={getSessionStatusColor(session.status) as any}
                    />
                  </Box>
                  
                  <Stack direction="row" spacing={0.5}>
                    {session.settings.accessType === 'private' && (
                      <Tooltip title="Private Session">
                        <Lock fontSize="small" color="action" />
                      </Tooltip>
                    )}
                    {session.settings.recordSession && (
                      <Tooltip title="Recording Enabled">
                        <Badge variant="dot" color="error">
                          <Timer fontSize="small" color="action" />
                        </Badge>
                      </Tooltip>
                    )}
                  </Stack>
                </Box>

                {session.description && (
                  <Typography variant="body2" color="text.secondary" paragraph>
                    {session.description}
                  </Typography>
                )}

                <Grid container spacing={1} sx={{ mb: 2 }}>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Subject</Typography>
                    <Typography variant="body2">{session.content.subject}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Grade</Typography>
                    <Typography variant="body2">Level {session.content.gradeLevel}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Environment</Typography>
                    <Typography variant="body2">{session.content.environmentType}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">Players</Typography>
                    <Typography variant="body2">
                      {session.metrics.activePlayers}/{session.settings.maxPlayers}
                    </Typography>
                  </Grid>
                </Grid>

                {session.participants.students.length > 0 && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <AvatarGroup max={4} sx={{ '& .MuiAvatar-root': { width: 24, height: 24, fontSize: 12 } }}>
                      {session.participants.students
                        .filter(s => s.status === 'active')
                        .map((student) => (
                          <Avatar key={student.id}>
                            {student.name[0]}
                          </Avatar>
                        ))}
                    </AvatarGroup>
                    <Typography variant="caption" color="text.secondary">
                      {session.participants.students.filter(s => s.status === 'active').length} active
                    </Typography>
                  </Box>
                )}

                {session.settings.timeLimit && (
                  <Alert severity="info" sx={{ mt: 2, py: 0 }}>
                    <Typography variant="caption">
                      {session.settings.timeLimit} minute time limit
                    </Typography>
                  </Alert>
                )}
              </CardContent>

              <Divider />

              <CardActions>
                {session.status === 'draft' && (
                  <>
                    <Button
                      size="small"
                      startIcon={<Edit />}
                      onClick={() => {
                        setSelectedSession(session);
                        setSettingsDialogOpen(true);
                      }}
                    >
                      Edit
                    </Button>
                    <Button
                      size="small"
                      color="success"
                      startIcon={<PlayArrow />}
                      onClick={() => handleStartSession(session.id)}
                    >
                      Start
                    </Button>
                  </>
                )}
                
                {session.status === 'active' && (
                  <>
                    <Button
                      size="small"
                      color="warning"
                      startIcon={<Pause />}
                      onClick={() => handlePauseSession(session.id)}
                    >
                      Pause
                    </Button>
                    <Button
                      size="small"
                      color="error"
                      startIcon={<Stop />}
                      onClick={() => handleStopSession(session.id)}
                    >
                      Stop
                    </Button>
                  </>
                )}
                
                {session.status === 'paused' && (
                  <Button
                    size="small"
                    color="success"
                    startIcon={<PlayArrow />}
                    onClick={() => handleStartSession(session.id)}
                  >
                    Resume
                  </Button>
                )}

                <IconButton
                  size="small"
                  onClick={() => handleDuplicateSession(session)}
                >
                  <ContentCopy fontSize="small" />
                </IconButton>
                
                <IconButton
                  size="small"
                  onClick={() => {
                    setSelectedSession(session);
                    setSettingsDialogOpen(true);
                  }}
                >
                  <Settings fontSize="small" />
                </IconButton>
                
                <IconButton
                  size="small"
                  onClick={() => {
                    setSelectedSession(session);
                    setInviteDialogOpen(true);
                  }}
                >
                  <Share fontSize="small" />
                </IconButton>
                
                {(session.status === 'draft' || session.status === 'completed') && (
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => handleDeleteSession(session.id)}
                  >
                    <Delete fontSize="small" />
                  </IconButton>
                )}
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Create Session Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create New Session</DialogTitle>
        <DialogContent>
          <Stepper activeStep={activeStep} orientation="vertical">
            <Step>
              <StepLabel>Basic Information</StepLabel>
              <StepContent>
                <Box sx={{ mt: 2 }}>
                  <TextField
                    fullWidth
                    label="Session Name"
                    value={newSession.name}
                    onChange={(e) => setNewSession({ ...newSession, name: e.target.value })}
                    sx={{ mb: 2 }}
                  />
                  <TextField
                    fullWidth
                    label="Description (Optional)"
                    multiline
                    rows={3}
                    value={newSession.description}
                    onChange={(e) => setNewSession({ ...newSession, description: e.target.value })}
                    sx={{ mb: 2 }}
                  />
                  
                  <Typography variant="subtitle2" gutterBottom>
                    Quick Templates
                  </Typography>
                  <Stack direction="row" spacing={1}>
                    {SESSION_TEMPLATES.map((template) => (
                      <Chip
                        key={template.id}
                        label={template.name}
                        onClick={() => handleApplyTemplate(template)}
                        clickable
                      />
                    ))}
                  </Stack>
                </Box>
              </StepContent>
            </Step>

            <Step>
              <StepLabel>Content Settings</StepLabel>
              <StepContent>
                <Grid container spacing={2} sx={{ mt: 1 }}>
                  <Grid item xs={6}>
                    <FormControl fullWidth>
                      <InputLabel>Subject</InputLabel>
                      <Select
                        value={newSession.content?.subject}
                        onChange={(e) => setNewSession({
                          ...newSession,
                          content: { ...newSession.content!, subject: e.target.value }
                        })}
                      >
                        <MenuItem value="Mathematics">Mathematics</MenuItem>
                        <MenuItem value="Science">Science</MenuItem>
                        <MenuItem value="English">English</MenuItem>
                        <MenuItem value="History">History</MenuItem>
                        <MenuItem value="Geography">Geography</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  <Grid item xs={6}>
                    <FormControl fullWidth>
                      <InputLabel>Grade Level</InputLabel>
                      <Select
                        value={newSession.content?.gradeLevel}
                        onChange={(e) => setNewSession({
                          ...newSession,
                          content: { ...newSession.content!, gradeLevel: Number(e.target.value) }
                        })}
                      >
                        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(grade => (
                          <MenuItem key={grade} value={grade}>Grade {grade}</MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  <Grid item xs={12}>
                    <FormControl fullWidth>
                      <InputLabel>Environment Type</InputLabel>
                      <Select
                        value={newSession.content?.environmentType}
                        onChange={(e) => setNewSession({
                          ...newSession,
                          content: { ...newSession.content!, environmentType: e.target.value }
                        })}
                      >
                        <MenuItem value="classroom">Classroom</MenuItem>
                        <MenuItem value="laboratory">Laboratory</MenuItem>
                        <MenuItem value="outdoor">Outdoor</MenuItem>
                        <MenuItem value="space_station">Space Station</MenuItem>
                        <MenuItem value="underwater">Underwater</MenuItem>
                        <MenuItem value="historical">Historical</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>

                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={newSession.content?.hasQuiz}
                          onChange={(e) => setNewSession({
                            ...newSession,
                            content: { ...newSession.content!, hasQuiz: e.target.checked }
                          })}
                        />
                      }
                      label="Include Quiz"
                    />
                  </Grid>
                </Grid>
              </StepContent>
            </Step>

            <Step>
              <StepLabel>Session Settings</StepLabel>
              <StepContent>
                <Grid container spacing={2} sx={{ mt: 1 }}>
                  <Grid item xs={12}>
                    <FormControl component="fieldset">
                      <FormLabel>Access Type</FormLabel>
                      <RadioGroup
                        row
                        value={newSession.settings?.accessType}
                        onChange={(e) => setNewSession({
                          ...newSession,
                          settings: { ...newSession.settings!, accessType: e.target.value as any }
                        })}
                      >
                        <FormControlLabel value="public" control={<Radio />} label="Public" />
                        <FormControlLabel value="private" control={<Radio />} label="Private" />
                        <FormControlLabel value="invite-only" control={<Radio />} label="Invite Only" />
                      </RadioGroup>
                    </FormControl>
                  </Grid>

                  {newSession.settings?.accessType === 'private' && (
                    <Grid item xs={12}>
                      <TextField
                        label="Access Code"
                        value={newSession.settings?.accessCode}
                        onChange={(e) => setNewSession({
                          ...newSession,
                          settings: { ...newSession.settings!, accessCode: e.target.value }
                        })}
                        InputProps={{
                          endAdornment: (
                            <Button size="small" onClick={generateAccessCode}>
                              Generate
                            </Button>
                          )
                        }}
                      />
                    </Grid>
                  )}

                  <Grid item xs={6}>
                    <Typography gutterBottom>Max Players: {newSession.settings?.maxPlayers}</Typography>
                    <Slider
                      value={newSession.settings?.maxPlayers}
                      onChange={(e, value) => setNewSession({
                        ...newSession,
                        settings: { ...newSession.settings!, maxPlayers: value as number }
                      })}
                      min={1}
                      max={50}
                      marks
                      step={5}
                    />
                  </Grid>

                  <Grid item xs={6}>
                    <Typography gutterBottom>Time Limit (minutes): {newSession.settings?.timeLimit || 'None'}</Typography>
                    <Slider
                      value={newSession.settings?.timeLimit || 0}
                      onChange={(e, value) => setNewSession({
                        ...newSession,
                        settings: { ...newSession.settings!, timeLimit: value as number || undefined }
                      })}
                      min={0}
                      max={120}
                      marks
                      step={15}
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <FormGroup>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={newSession.settings?.allowLateJoin}
                            onChange={(e) => setNewSession({
                              ...newSession,
                              settings: { ...newSession.settings!, allowLateJoin: e.target.checked }
                            })}
                          />
                        }
                        label="Allow Late Join"
                      />
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={newSession.settings?.recordSession}
                            onChange={(e) => setNewSession({
                              ...newSession,
                              settings: { ...newSession.settings!, recordSession: e.target.checked }
                            })}
                          />
                        }
                        label="Record Session"
                      />
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={newSession.settings?.enableChat}
                            onChange={(e) => setNewSession({
                              ...newSession,
                              settings: { ...newSession.settings!, enableChat: e.target.checked }
                            })}
                          />
                        }
                        label="Enable Chat"
                      />
                    </FormGroup>
                  </Grid>
                </Grid>
              </StepContent>
            </Step>

            <Step>
              <StepLabel optional={<Typography variant="caption">Optional</Typography>}>
                Invite Students
              </StepLabel>
              <StepContent>
                <Box sx={{ mt: 2 }}>
                  <Autocomplete
                    multiple
                    options={['student1', 'student2', 'student3']} // Would be fetched from API
                    value={selectedStudents}
                    onChange={(e, value) => setSelectedStudents(value)}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Search students..."
                        placeholder="Type to search"
                      />
                    )}
                  />
                  
                  <Alert severity="info" sx={{ mt: 2 }}>
                    <AlertTitle>Note</AlertTitle>
                    You can also invite students after creating the session
                  </Alert>
                </Box>
              </StepContent>
            </Step>
          </Stepper>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setCreateDialogOpen(false);
            resetNewSession();
          }}>
            Cancel
          </Button>
          {activeStep > 0 && (
            <Button onClick={() => setActiveStep(prev => prev - 1)}>
              Back
            </Button>
          )}
          <Button
            variant="contained"
            onClick={handleCreateSession}
          >
            {activeStep < 3 ? 'Next' : 'Create Session'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Session Settings Dialog */}
      <Dialog
        open={settingsDialogOpen}
        onClose={() => setSettingsDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Session Settings</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <FormControl fullWidth>
              <InputLabel>Access Type</InputLabel>
              <Select value="public">
                <MenuItem value="public">Public</MenuItem>
                <MenuItem value="private">Private</MenuItem>
                <MenuItem value="friends">Friends Only</MenuItem>
              </Select>
            </FormControl>
            
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle2" gutterBottom>Player Limits</Typography>
              <Slider
                valueLabelDisplay="auto"
                step={1}
                min={1}
                max={50}
                defaultValue={30}
              />
            </Paper>
            
            <Divider />
            
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Enable Chat"
            />
            <FormControlLabel
              control={<Switch />}
              label="Enable Voice Chat"
            />
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Record Session"
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsDialogOpen(false)}>Cancel</Button>
          <Button variant="contained">Save Settings</Button>
        </DialogActions>
      </Dialog>

      {/* Student Invite Dialog */}
      <Dialog
        open={inviteDialogOpen}
        onClose={() => setInviteDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Invite Students</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              fullWidth
              label="Search Students"
              value={studentSearch}
              onChange={(e) => setStudentSearch(e.target.value)}
              placeholder="Type student name or email..."
            />
            
            <List sx={{ maxHeight: 300, overflow: 'auto' }}>
              {/* Mock student list filtered by search */}
              {['Alice Johnson', 'Bob Smith', 'Carol Brown', 'David Wilson'].filter(name => 
                name.toLowerCase().includes(studentSearch.toLowerCase())
              ).map((student) => (
                <ListItem key={student}>
                  <ListItemIcon>
                    <Avatar sx={{ width: 32, height: 32 }}>
                      {student[0]}
                    </Avatar>
                  </ListItemIcon>
                  <ListItemText primary={student} />
                  <ListItemSecondaryAction>
                    <Checkbox
                      checked={selectedStudents.includes(student)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedStudents([...selectedStudents, student]);
                        } else {
                          setSelectedStudents(selectedStudents.filter(s => s !== student));
                        }
                      }}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
            
            {selectedStudents.length > 0 && (
              <Paper sx={{ p: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Selected Students ({selectedStudents.length})
                </Typography>
                <AvatarGroup max={5}>
                  {selectedStudents.map((student) => (
                    <Avatar key={student} sx={{ width: 32, height: 32 }}>
                      {student[0]}
                    </Avatar>
                  ))}
                </AvatarGroup>
              </Paper>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInviteDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            disabled={selectedStudents.length === 0}
            onClick={() => {
              // Handle student invitations
              console.error('Inviting students:', selectedStudents);
              setInviteDialogOpen(false);
              setSelectedStudents([]);
            }}
          >
            Send Invites
          </Button>
        </DialogActions>
      </Dialog>

      {/* Empty State */}
      {sessions.length === 0 && (
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
          <Games sx={{ fontSize: 64, color: 'text.disabled' }} />
          <Typography variant="h6" color="text.secondary">
            No sessions yet
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Create your first educational game session
          </Typography>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Create Session
          </Button>
        </Box>
      )}
    </Box>
  );
};