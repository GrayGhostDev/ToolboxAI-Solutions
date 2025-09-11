/**
 * Roblox Control Panel Component
 * Main control interface for teachers to manage Roblox educational content
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Grid,
  Button,
  Typography,
  Chip,
  IconButton,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  CircularProgress,
  Tooltip,
  Divider,
  Switch,
  FormControlLabel,
  Badge,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Fab
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Pause as PauseIcon,
  Refresh as RefreshIcon,
  Add as AddIcon,
  Send as SendIcon,
  CloudUpload as CloudIcon,
  School as SchoolIcon,
  Quiz as QuizIcon,
  Terrain as TerrainIcon,
  Code as CodeIcon,
  Group as GroupIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Settings as SettingsIcon,
  SportsEsports as GameIcon,
  Psychology as AIIcon,
  Visibility as PreviewIcon,
  Download as DownloadIcon,
  Save as SaveIcon,
  FiberManualRecord as RecordIcon
} from '@mui/icons-material';
import { useWebSocket } from '../../hooks/websocket';
import { useAppDispatch, useAppSelector } from '../../store';
import { WebSocketMessageType, ContentGenerationRequest } from '../../types/websocket';

interface RobloxControlPanelProps {
  className?: string;
}

interface PluginStatus {
  connected: boolean;
  version: string;
  lastHeartbeat: Date | null;
  capabilities: string[];
}

interface ActiveSession {
  id: string;
  name: string;
  lessonId: string;
  studentCount: number;
  status: 'waiting' | 'active' | 'paused' | 'completed';
  startTime: Date;
  duration: number;
}

interface ContentPreset {
  id: string;
  name: string;
  description: string;
  subject: string;
  gradeLevel: number;
  environment: string;
  includeQuiz: boolean;
}

const CONTENT_PRESETS: ContentPreset[] = [
  {
    id: 'math-fractions',
    name: 'Fractions Adventure',
    description: 'Interactive fraction learning in a pizza restaurant',
    subject: 'Mathematics',
    gradeLevel: 5,
    environment: 'restaurant',
    includeQuiz: true
  },
  {
    id: 'science-solar',
    name: 'Solar System Explorer',
    description: 'Journey through space to learn about planets',
    subject: 'Science',
    gradeLevel: 6,
    environment: 'space_station',
    includeQuiz: true
  },
  {
    id: 'history-ancient',
    name: 'Ancient Civilizations',
    description: 'Time travel to explore ancient Egypt and Rome',
    subject: 'History',
    gradeLevel: 7,
    environment: 'historical',
    includeQuiz: true
  },
  {
    id: 'english-grammar',
    name: 'Grammar Quest',
    description: 'Adventure game for learning grammar rules',
    subject: 'English',
    gradeLevel: 4,
    environment: 'fantasy_world',
    includeQuiz: true
  }
];

const ENVIRONMENT_TYPES = [
  'classroom',
  'outdoor',
  'laboratory',
  'space_station',
  'underwater',
  'fantasy_world',
  'historical',
  'urban',
  'restaurant',
  'museum'
];

export const RobloxControlPanel: React.FC<RobloxControlPanelProps> = ({ className }) => {
  const dispatch = useAppDispatch();
  const { sendMessage, isConnected, state: wsState } = useWebSocket();
  
  // Local state
  const [pluginStatus, setPluginStatus] = useState<PluginStatus>({
    connected: false,
    version: 'Unknown',
    lastHeartbeat: null,
    capabilities: []
  });
  
  const [activeSessions, setActiveSessions] = useState<ActiveSession[]>([]);
  const [selectedPreset, setSelectedPreset] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [showContentWizard, setShowContentWizard] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  
  // Content generation form state
  const [contentForm, setContentForm] = useState<ContentGenerationRequest>({
    requestId: '',
    subject: 'Mathematics',
    gradeLevel: 5,
    learningObjectives: [],
    environmentType: 'classroom',
    includeQuiz: true,
    difficulty: 'medium',
    duration: 30,
    maxStudents: 30
  });
  
  const [objectivesInput, setObjectivesInput] = useState('');
  
  // Check plugin connection status
  useEffect(() => {
    const checkPluginStatus = async () => {
      if (isConnected) {
        try {
          const response = await sendMessage(WebSocketMessageType.PLUGIN_STATUS_REQUEST);
          if (response) {
            setPluginStatus({
              connected: true,
              version: response.version || 'Unknown',
              lastHeartbeat: new Date(),
              capabilities: response.capabilities || []
            });
          }
        } catch (error) {
          console.error('Failed to check plugin status:', error);
          setPluginStatus(prev => ({ ...prev, connected: false }));
        }
      }
    };
    
    checkPluginStatus();
    const interval = setInterval(checkPluginStatus, 30000); // Check every 30 seconds
    
    return () => clearInterval(interval);
  }, [isConnected, sendMessage]);
  
  // Fetch active sessions
  useEffect(() => {
    const fetchSessions = async () => {
      if (isConnected) {
        try {
          const response = await sendMessage(WebSocketMessageType.GET_ACTIVE_SESSIONS);
          if (response && response.sessions) {
            setActiveSessions(response.sessions);
          }
        } catch (error) {
          console.error('Failed to fetch sessions:', error);
        }
      }
    };
    
    fetchSessions();
    const interval = setInterval(fetchSessions, 10000); // Update every 10 seconds
    
    return () => clearInterval(interval);
  }, [isConnected, sendMessage]);
  
  // Handle preset selection
  const handlePresetSelect = (presetId: string) => {
    const preset = CONTENT_PRESETS.find(p => p.id === presetId);
    if (preset) {
      setContentForm(prev => ({
        ...prev,
        subject: preset.subject,
        gradeLevel: preset.gradeLevel,
        environmentType: preset.environment,
        includeQuiz: preset.includeQuiz
      }));
      setSelectedPreset(presetId);
    }
  };
  
  // Handle content generation
  const handleGenerateContent = async () => {
    setIsGenerating(true);
    setGenerationProgress(0);
    
    try {
      // Parse learning objectives
      const objectives = objectivesInput
        .split(',')
        .map(obj => obj.trim())
        .filter(obj => obj.length > 0);
      
      const request: ContentGenerationRequest = {
        ...contentForm,
        requestId: `req_${Date.now()}`,
        learningObjectives: objectives
      };
      
      // Send generation request
      await sendMessage(WebSocketMessageType.CONTENT_GENERATION_REQUEST, request);
      
      // Simulate progress (real progress would come from WebSocket events)
      const progressInterval = setInterval(() => {
        setGenerationProgress(prev => {
          if (prev >= 100) {
            clearInterval(progressInterval);
            setIsGenerating(false);
            return 100;
          }
          return prev + 10;
        });
      }, 1000);
      
    } catch (error) {
      console.error('Failed to generate content:', error);
      setIsGenerating(false);
    }
  };
  
  // Handle session control
  const handleSessionControl = async (sessionId: string, action: 'start' | 'pause' | 'stop') => {
    try {
      await sendMessage(WebSocketMessageType.SESSION_CONTROL, {
        sessionId,
        action
      });
      
      // Update local state
      setActiveSessions(prev => prev.map(session => {
        if (session.id === sessionId) {
          switch (action) {
            case 'start':
              return { ...session, status: 'active' };
            case 'pause':
              return { ...session, status: 'paused' };
            case 'stop':
              return { ...session, status: 'completed' };
            default:
              return session;
          }
        }
        return session;
      }));
    } catch (error) {
      console.error(`Failed to ${action} session:`, error);
    }
  };
  
  // Wizard steps
  const wizardSteps = [
    'Select Subject & Grade',
    'Define Learning Objectives',
    'Choose Environment',
    'Configure Settings',
    'Review & Generate'
  ];
  
  const handleNext = () => {
    setActiveStep(prev => prev + 1);
  };
  
  const handleBack = () => {
    setActiveStep(prev => prev - 1);
  };
  
  const handleWizardComplete = () => {
    handleGenerateContent();
    setShowContentWizard(false);
    setActiveStep(0);
  };
  
  // Get connection status color
  const getStatusColor = (connected: boolean) => {
    return connected ? 'success' : 'error';
  };
  
  return (
    <Box className={className}>
      <Grid container spacing={3}>
        {/* Plugin Status Card */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader
              title="Roblox Studio Plugin"
              avatar={<GameIcon color="primary" />}
              action={
                <Chip
                  label={pluginStatus.connected ? 'Connected' : 'Disconnected'}
                  color={getStatusColor(pluginStatus.connected)}
                  icon={pluginStatus.connected ? <CheckIcon /> : <ErrorIcon />}
                  size="small"
                />
              }
            />
            <CardContent>
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <InfoIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Version" 
                    secondary={pluginStatus.version}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <RecordIcon 
                      fontSize="small" 
                      color={pluginStatus.connected ? 'success' : 'error'}
                    />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Status" 
                    secondary={pluginStatus.connected ? 'Online' : 'Offline'}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <RefreshIcon fontSize="small" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Last Heartbeat" 
                    secondary={
                      pluginStatus.lastHeartbeat 
                        ? new Date(pluginStatus.lastHeartbeat).toLocaleTimeString()
                        : 'Never'
                    }
                  />
                </ListItem>
              </List>
              
              <Box mt={2}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  disabled={!isConnected}
                >
                  Reconnect Plugin
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Quick Actions Card */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardHeader
              title="Quick Actions"
              avatar={<AIIcon color="primary" />}
            />
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Content Preset</InputLabel>
                    <Select
                      value={selectedPreset}
                      onChange={(e) => handlePresetSelect(e.target.value)}
                      label="Content Preset"
                    >
                      <MenuItem value="">
                        <em>Custom</em>
                      </MenuItem>
                      {CONTENT_PRESETS.map(preset => (
                        <MenuItem key={preset.id} value={preset.id}>
                          {preset.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <Button
                    fullWidth
                    variant="contained"
                    color="primary"
                    startIcon={isGenerating ? <CircularProgress size={20} /> : <CloudIcon />}
                    onClick={() => setShowContentWizard(true)}
                    disabled={!isConnected || !pluginStatus.connected || isGenerating}
                  >
                    {isGenerating ? 'Generating...' : 'Generate Content'}
                  </Button>
                </Grid>
                
                <Grid item xs={12}>
                  {selectedPreset && (
                    <Alert severity="info" icon={<InfoIcon />}>
                      {CONTENT_PRESETS.find(p => p.id === selectedPreset)?.description}
                    </Alert>
                  )}
                </Grid>
                
                {isGenerating && (
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Box sx={{ width: '100%', mr: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          Generating content... {generationProgress}%
                        </Typography>
                        <Box sx={{ width: '100%', mt: 1 }}>
                          <CircularProgress 
                            variant="determinate" 
                            value={generationProgress}
                            size={30}
                          />
                        </Box>
                      </Box>
                    </Box>
                  </Grid>
                )}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Active Sessions Card */}
        <Grid item xs={12}>
          <Card>
            <CardHeader
              title="Active Sessions"
              avatar={<GroupIcon color="primary" />}
              action={
                <Badge badgeContent={activeSessions.length} color="primary">
                  <IconButton size="small">
                    <RefreshIcon />
                  </IconButton>
                </Badge>
              }
            />
            <CardContent>
              {activeSessions.length === 0 ? (
                <Alert severity="info">
                  No active sessions. Generate content to start a new session.
                </Alert>
              ) : (
                <List>
                  {activeSessions.map(session => (
                    <ListItem key={session.id}>
                      <ListItemIcon>
                        <SchoolIcon color={session.status === 'active' ? 'success' : 'action'} />
                      </ListItemIcon>
                      <ListItemText
                        primary={session.name}
                        secondary={
                          <Box>
                            <Chip 
                              label={session.status} 
                              size="small" 
                              color={session.status === 'active' ? 'success' : 'default'}
                              sx={{ mr: 1 }}
                            />
                            <Typography variant="caption" component="span">
                              {session.studentCount} students • Started {new Date(session.startTime).toLocaleTimeString()}
                            </Typography>
                          </Box>
                        }
                      />
                      <ListItemSecondaryAction>
                        {session.status === 'active' ? (
                          <>
                            <IconButton 
                              edge="end" 
                              onClick={() => handleSessionControl(session.id, 'pause')}
                            >
                              <PauseIcon />
                            </IconButton>
                            <IconButton 
                              edge="end" 
                              onClick={() => handleSessionControl(session.id, 'stop')}
                            >
                              <StopIcon />
                            </IconButton>
                          </>
                        ) : session.status === 'paused' ? (
                          <IconButton 
                            edge="end" 
                            onClick={() => handleSessionControl(session.id, 'start')}
                          >
                            <PlayIcon />
                          </IconButton>
                        ) : null}
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
        
        {/* Statistics Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Typography variant="h4" color="primary">
              {activeSessions.reduce((sum, s) => sum + s.studentCount, 0)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Active Students
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Typography variant="h4" color="secondary">
              {activeSessions.length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Active Sessions
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Typography variant="h4" color="success.main">
              12
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Content Generated Today
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Typography variant="h4" color="info.main">
              85%
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Avg. Completion Rate
            </Typography>
          </Paper>
        </Grid>
      </Grid>
      
      {/* Content Generation Wizard Dialog */}
      <Dialog 
        open={showContentWizard} 
        onClose={() => setShowContentWizard(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Generate Educational Content
        </DialogTitle>
        <DialogContent>
          <Stepper activeStep={activeStep} orientation="vertical">
            {wizardSteps.map((label, index) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
                <StepContent>
                  {index === 0 && (
                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={6}>
                        <TextField
                          fullWidth
                          label="Subject"
                          value={contentForm.subject}
                          onChange={(e) => setContentForm(prev => ({ ...prev, subject: e.target.value }))}
                          margin="normal"
                        />
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <TextField
                          fullWidth
                          label="Grade Level"
                          type="number"
                          value={contentForm.gradeLevel}
                          onChange={(e) => setContentForm(prev => ({ ...prev, gradeLevel: parseInt(e.target.value) }))}
                          margin="normal"
                          InputProps={{ inputProps: { min: 1, max: 12 } }}
                        />
                      </Grid>
                    </Grid>
                  )}
                  
                  {index === 1 && (
                    <TextField
                      fullWidth
                      multiline
                      rows={4}
                      label="Learning Objectives (comma separated)"
                      value={objectivesInput}
                      onChange={(e) => setObjectivesInput(e.target.value)}
                      placeholder="e.g., Understanding fractions, Adding fractions, Converting to decimals"
                      margin="normal"
                    />
                  )}
                  
                  {index === 2 && (
                    <FormControl fullWidth margin="normal">
                      <InputLabel>Environment Type</InputLabel>
                      <Select
                        value={contentForm.environmentType}
                        onChange={(e) => setContentForm(prev => ({ ...prev, environmentType: e.target.value }))}
                        label="Environment Type"
                      >
                        {ENVIRONMENT_TYPES.map(env => (
                          <MenuItem key={env} value={env}>
                            {env.replace('_', ' ').charAt(0).toUpperCase() + env.slice(1)}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  )}
                  
                  {index === 3 && (
                    <Grid container spacing={2}>
                      <Grid item xs={12}>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={contentForm.includeQuiz}
                              onChange={(e) => setContentForm(prev => ({ ...prev, includeQuiz: e.target.checked }))}
                            />
                          }
                          label="Include Quiz/Assessment"
                        />
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <TextField
                          fullWidth
                          label="Session Duration (minutes)"
                          type="number"
                          value={contentForm.duration}
                          onChange={(e) => setContentForm(prev => ({ ...prev, duration: parseInt(e.target.value) }))}
                          margin="normal"
                        />
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <TextField
                          fullWidth
                          label="Max Students"
                          type="number"
                          value={contentForm.maxStudents}
                          onChange={(e) => setContentForm(prev => ({ ...prev, maxStudents: parseInt(e.target.value) }))}
                          margin="normal"
                        />
                      </Grid>
                    </Grid>
                  )}
                  
                  {index === 4 && (
                    <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
                      <Typography variant="h6" gutterBottom>Review Your Configuration</Typography>
                      <Grid container spacing={1}>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">Subject:</Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2">{contentForm.subject}</Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">Grade Level:</Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2">{contentForm.gradeLevel}</Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">Environment:</Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2">{contentForm.environmentType}</Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">Include Quiz:</Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2">{contentForm.includeQuiz ? 'Yes' : 'No'}</Typography>
                        </Grid>
                        <Grid item xs={12}>
                          <Typography variant="body2" color="text.secondary">Learning Objectives:</Typography>
                          <Typography variant="body2">{objectivesInput || 'None specified'}</Typography>
                        </Grid>
                      </Grid>
                    </Paper>
                  )}
                  
                  <Box sx={{ mb: 2, mt: 2 }}>
                    <Button
                      variant="contained"
                      onClick={index === wizardSteps.length - 1 ? handleWizardComplete : handleNext}
                      sx={{ mt: 1, mr: 1 }}
                    >
                      {index === wizardSteps.length - 1 ? 'Generate' : 'Continue'}
                    </Button>
                    <Button
                      disabled={index === 0}
                      onClick={handleBack}
                      sx={{ mt: 1, mr: 1 }}
                    >
                      Back
                    </Button>
                  </Box>
                </StepContent>
              </Step>
            ))}
          </Stepper>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowContentWizard(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>
      
      {/* Floating Action Button for Quick Generate */}
      <Fab
        color="primary"
        aria-label="quick generate"
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16
        }}
        onClick={() => setShowContentWizard(true)}
        disabled={!isConnected || !pluginStatus.connected}
      >
        <AddIcon />
      </Fab>
    </Box>
  );
};