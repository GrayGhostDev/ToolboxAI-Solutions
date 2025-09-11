/**
 * ContentGenerationMonitor Component
 * 
 * Real-time monitoring of AI content generation pipeline
 * Shows progress for each agent and overall generation status
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Grid,
  Paper,
  Chip,
  IconButton,
  Button,
  Alert,
  AlertTitle,
  Collapse,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  CircularProgress,
  Tooltip,
  Badge,
  Stack,
  useTheme,
  alpha
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Stop,
  Refresh,
  CheckCircle,
  Error,
  Warning,
  Info,
  Code,
  Psychology,
  Terrain,
  Quiz,
  Movie,
  Settings,
  ExpandMore,
  ExpandLess,
  Speed,
  Memory,
  Storage,
  Timer,
  Cancel,
  Download,
  Preview,
  Visibility
} from '@mui/icons-material';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import {
  ContentGenerationProgress,
  WebSocketMessageType,
  WebSocketChannel
} from '../../types/websocket';

interface AgentStatus {
  id: string;
  name: string;
  type: 'supervisor' | 'content' | 'quiz' | 'terrain' | 'script' | 'review';
  status: 'idle' | 'working' | 'completed' | 'error' | 'cancelled';
  progress: number;
  currentTask?: string;
  startTime?: Date;
  completionTime?: Date;
  error?: string;
  output?: any;
  metrics?: {
    tokensUsed?: number;
    timeElapsed?: number;
    memoryUsage?: number;
  };
}

interface GenerationSession {
  id: string;
  status: 'initializing' | 'processing' | 'reviewing' | 'completed' | 'failed' | 'cancelled';
  startTime: Date;
  endTime?: Date;
  totalProgress: number;
  agents: AgentStatus[];
  request: {
    subject: string;
    gradeLevel: number;
    objectives: string[];
    environmentType: string;
  };
  output?: {
    terrain?: any;
    content?: any;
    quiz?: any;
    scripts?: any;
  };
  errors: string[];
  warnings: string[];
}

const getAgentIcon = (type: AgentStatus['type']) => {
  switch (type) {
    case 'supervisor': return <Psychology />;
    case 'content': return <Movie />;
    case 'quiz': return <Quiz />;
    case 'terrain': return <Terrain />;
    case 'script': return <Code />;
    case 'review': return <CheckCircle />;
    default: return <Settings />;
  }
};

const getStatusColor = (status: AgentStatus['status']) => {
  switch (status) {
    case 'idle': return 'default';
    case 'working': return 'primary';
    case 'completed': return 'success';
    case 'error': return 'error';
    case 'cancelled': return 'warning';
    default: return 'default';
  }
};

export const ContentGenerationMonitor: React.FC = () => {
  const theme = useTheme();
  const { on, sendMessage, isConnected } = useWebSocketContext();
  const [session, setSession] = useState<GenerationSession | null>(null);
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set());
  const [showPreview, setShowPreview] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [logs, setLogs] = useState<Array<{ time: Date; message: string; level: 'info' | 'warning' | 'error' }>>([]);

  // Initialize agent statuses
  const initializeAgents = (): AgentStatus[] => [
    { id: 'supervisor', name: 'Supervisor Agent', type: 'supervisor', status: 'idle', progress: 0 },
    { id: 'content', name: 'Content Agent', type: 'content', status: 'idle', progress: 0 },
    { id: 'quiz', name: 'Quiz Agent', type: 'quiz', status: 'idle', progress: 0 },
    { id: 'terrain', name: 'Terrain Agent', type: 'terrain', status: 'idle', progress: 0 },
    { id: 'script', name: 'Script Agent', type: 'script', status: 'idle', progress: 0 },
    { id: 'review', name: 'Review Agent', type: 'review', status: 'idle', progress: 0 }
  ];

  // WebSocket event handlers
  useEffect(() => {
    if (!isConnected) return;

    const unsubscribeProgress = on(WebSocketMessageType.CONTENT_PROGRESS, (data: ContentGenerationProgress) => {
      handleProgressUpdate(data);
    });

    const unsubscribeComplete = on(WebSocketMessageType.CONTENT_COMPLETE, (data: any) => {
      handleGenerationComplete(data);
    });

    const unsubscribeError = on(WebSocketMessageType.CONTENT_ERROR, (data: any) => {
      handleGenerationError(data);
    });

    return () => {
      unsubscribeProgress();
      unsubscribeComplete();
      unsubscribeError();
    };
  }, [isConnected]);

  const handleProgressUpdate = (progress: ContentGenerationProgress) => {
    setSession(prev => {
      if (!prev) return null;

      const updatedAgents = prev.agents.map(agent => {
        if (agent.id === progress.agentId) {
          return {
            ...agent,
            status: progress.status as AgentStatus['status'],
            progress: progress.progress,
            currentTask: progress.currentTask,
            metrics: progress.metrics
          };
        }
        return agent;
      });

      const totalProgress = updatedAgents.reduce((sum, agent) => sum + agent.progress, 0) / updatedAgents.length;

      addLog(`${progress.agentId}: ${progress.currentTask} (${progress.progress}%)`, 'info');

      return {
        ...prev,
        agents: updatedAgents,
        totalProgress,
        status: progress.sessionStatus as GenerationSession['status'] || prev.status
      };
    });
  };

  const handleGenerationComplete = (data: any) => {
    setSession(prev => {
      if (!prev) return null;

      addLog('Content generation completed successfully!', 'info');

      return {
        ...prev,
        status: 'completed',
        endTime: new Date(),
        totalProgress: 100,
        output: data.output,
        agents: prev.agents.map(agent => ({
          ...agent,
          status: 'completed',
          progress: 100,
          completionTime: new Date()
        }))
      };
    });
  };

  const handleGenerationError = (data: any) => {
    setSession(prev => {
      if (!prev) return null;

      addLog(`Error: ${data.error}`, 'error');

      return {
        ...prev,
        status: 'failed',
        errors: [...prev.errors, data.error],
        agents: prev.agents.map(agent => {
          if (agent.id === data.agentId) {
            return {
              ...agent,
              status: 'error',
              error: data.error
            };
          }
          return agent;
        })
      };
    });
  };

  const addLog = (message: string, level: 'info' | 'warning' | 'error') => {
    setLogs(prev => [...prev, { time: new Date(), message, level }]);
  };

  const startGeneration = (request: GenerationSession['request']) => {
    const newSession: GenerationSession = {
      id: `gen_${Date.now()}`,
      status: 'initializing',
      startTime: new Date(),
      totalProgress: 0,
      agents: initializeAgents(),
      request,
      errors: [],
      warnings: []
    };

    setSession(newSession);
    setLogs([]);
    addLog('Starting content generation...', 'info');

    // Send generation request via WebSocket
    sendMessage(WebSocketMessageType.CONTENT_REQUEST, {
      sessionId: newSession.id,
      ...request
    }, {
      channel: WebSocketChannel.CONTENT_UPDATES
    });
  };

  const cancelGeneration = () => {
    if (!session) return;

    sendMessage(WebSocketMessageType.CONTENT_CANCEL, {
      sessionId: session.id
    });

    setSession(prev => {
      if (!prev) return null;
      return {
        ...prev,
        status: 'cancelled',
        endTime: new Date(),
        agents: prev.agents.map(agent => ({
          ...agent,
          status: agent.status === 'working' ? 'cancelled' : agent.status
        }))
      };
    });

    addLog('Generation cancelled by user', 'warning');
  };

  const toggleAgentExpansion = (agentId: string) => {
    setExpandedAgents(prev => {
      const newSet = new Set(prev);
      if (newSet.has(agentId)) {
        newSet.delete(agentId);
      } else {
        newSet.add(agentId);
      }
      return newSet;
    });
  };

  const formatTime = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  const downloadOutput = () => {
    if (!session?.output) return;

    const blob = new Blob([JSON.stringify(session.output, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `content_${session.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', gap: 2 }}>
      {/* Header */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Psychology color="primary" fontSize="large" />
              <Box>
                <Typography variant="h5">Content Generation Monitor</Typography>
                <Typography variant="body2" color="text.secondary">
                  Real-time AI agent orchestration and progress tracking
                </Typography>
              </Box>
            </Box>
            
            <Stack direction="row" spacing={1}>
              <Chip
                label={isConnected ? 'Connected' : 'Disconnected'}
                color={isConnected ? 'success' : 'error'}
                size="small"
              />
              {session && (
                <Chip
                  label={session.status}
                  color={getStatusColor(session.status as any)}
                  size="small"
                />
              )}
            </Stack>
          </Box>
        </CardContent>
      </Card>

      {/* Session Overview */}
      {session && (
        <Card>
          <CardContent>
            <Grid container spacing={2}>
              <Grid item xs={12} md={8}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Overall Progress
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Box sx={{ flex: 1 }}>
                      <LinearProgress
                        variant="determinate"
                        value={session.totalProgress}
                        sx={{ height: 10, borderRadius: 1 }}
                      />
                    </Box>
                    <Typography variant="body2" fontWeight="bold">
                      {Math.round(session.totalProgress)}%
                    </Typography>
                  </Box>
                </Box>

                <Grid container spacing={1}>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">Subject</Typography>
                    <Typography variant="body2" fontWeight="bold">{session.request.subject}</Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">Grade Level</Typography>
                    <Typography variant="body2" fontWeight="bold">{session.request.gradeLevel}</Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">Environment</Typography>
                    <Typography variant="body2" fontWeight="bold">{session.request.environmentType}</Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">Duration</Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {session.endTime 
                        ? formatTime(session.endTime.getTime() - session.startTime.getTime())
                        : formatTime(Date.now() - session.startTime.getTime())
                      }
                    </Typography>
                  </Grid>
                </Grid>
              </Grid>

              <Grid item xs={12} md={4}>
                <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                  {session.status === 'processing' && (
                    <>
                      <Button
                        variant="outlined"
                        color="warning"
                        startIcon={<Pause />}
                        size="small"
                        disabled
                      >
                        Pause
                      </Button>
                      <Button
                        variant="outlined"
                        color="error"
                        startIcon={<Cancel />}
                        size="small"
                        onClick={cancelGeneration}
                      >
                        Cancel
                      </Button>
                    </>
                  )}
                  {session.status === 'completed' && (
                    <>
                      <Button
                        variant="outlined"
                        startIcon={<Download />}
                        size="small"
                        onClick={downloadOutput}
                      >
                        Download
                      </Button>
                      <Button
                        variant="outlined"
                        startIcon={<Preview />}
                        size="small"
                        onClick={() => setShowPreview(!showPreview)}
                      >
                        Preview
                      </Button>
                    </>
                  )}
                  <Button
                    variant="outlined"
                    startIcon={<Refresh />}
                    size="small"
                    onClick={() => setSession(null)}
                  >
                    Reset
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Agent Status Grid */}
      {session && (
        <Grid container spacing={2} sx={{ flex: 1, overflow: 'auto' }}>
          {session.agents.map((agent) => (
            <Grid item xs={12} md={6} key={agent.id}>
              <Card
                sx={{
                  border: agent.status === 'working' ? 2 : 1,
                  borderColor: agent.status === 'working' 
                    ? 'primary.main' 
                    : alpha(theme.palette.divider, 0.2),
                  transition: 'all 0.3s'
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Badge
                        badgeContent={
                          agent.status === 'working' ? (
                            <CircularProgress size={10} thickness={6} />
                          ) : agent.status === 'completed' ? (
                            <CheckCircle sx={{ fontSize: 12 }} />
                          ) : agent.status === 'error' ? (
                            <Error sx={{ fontSize: 12 }} />
                          ) : null
                        }
                      >
                        {getAgentIcon(agent.type)}
                      </Badge>
                      <Typography variant="subtitle2" fontWeight="bold">
                        {agent.name}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip
                        label={agent.status}
                        size="small"
                        color={getStatusColor(agent.status)}
                      />
                      <IconButton
                        size="small"
                        onClick={() => toggleAgentExpansion(agent.id)}
                      >
                        {expandedAgents.has(agent.id) ? <ExpandLess /> : <ExpandMore />}
                      </IconButton>
                    </Box>
                  </Box>

                  <Box sx={{ mb: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={agent.progress}
                      sx={{ height: 6, borderRadius: 1 }}
                    />
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        {agent.currentTask || 'Idle'}
                      </Typography>
                      <Typography variant="caption" fontWeight="bold">
                        {agent.progress}%
                      </Typography>
                    </Box>
                  </Box>

                  <Collapse in={expandedAgents.has(agent.id)}>
                    <Divider sx={{ my: 1 }} />
                    <Grid container spacing={1}>
                      {agent.metrics?.tokensUsed && (
                        <Grid item xs={4}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <Speed fontSize="small" color="action" />
                            <Box>
                              <Typography variant="caption" color="text.secondary">Tokens</Typography>
                              <Typography variant="body2">{agent.metrics.tokensUsed}</Typography>
                            </Box>
                          </Box>
                        </Grid>
                      )}
                      {agent.metrics?.timeElapsed && (
                        <Grid item xs={4}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <Timer fontSize="small" color="action" />
                            <Box>
                              <Typography variant="caption" color="text.secondary">Time</Typography>
                              <Typography variant="body2">{formatTime(agent.metrics.timeElapsed)}</Typography>
                            </Box>
                          </Box>
                        </Grid>
                      )}
                      {agent.metrics?.memoryUsage && (
                        <Grid item xs={4}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <Memory fontSize="small" color="action" />
                            <Box>
                              <Typography variant="caption" color="text.secondary">Memory</Typography>
                              <Typography variant="body2">{agent.metrics.memoryUsage}MB</Typography>
                            </Box>
                          </Box>
                        </Grid>
                      )}
                    </Grid>
                    {agent.error && (
                      <Alert severity="error" sx={{ mt: 1 }}>
                        <AlertTitle>Error</AlertTitle>
                        {agent.error}
                      </Alert>
                    )}
                  </Collapse>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Activity Log */}
      {session && logs.length > 0 && (
        <Card sx={{ maxHeight: 200, overflow: 'auto' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="subtitle2">Activity Log</Typography>
              <FormControlLabel
                control={
                  <Switch
                    size="small"
                    checked={autoScroll}
                    onChange={(e) => setAutoScroll(e.target.checked)}
                  />
                }
                label="Auto-scroll"
              />
            </Box>
            <List dense>
              {logs.map((log, index) => (
                <ListItem key={index}>
                  <ListItemIcon sx={{ minWidth: 30 }}>
                    {log.level === 'error' ? <Error color="error" fontSize="small" /> :
                     log.level === 'warning' ? <Warning color="warning" fontSize="small" /> :
                     <Info color="info" fontSize="small" />}
                  </ListItemIcon>
                  <ListItemText
                    primary={log.message}
                    secondary={log.time.toLocaleTimeString()}
                    primaryTypographyProps={{ variant: 'body2' }}
                    secondaryTypographyProps={{ variant: 'caption' }}
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!session && (
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
          <Psychology sx={{ fontSize: 64, color: 'text.disabled' }} />
          <Typography variant="h6" color="text.secondary">
            No active content generation
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Start a new generation from the Roblox Control Panel
          </Typography>
        </Box>
      )}
    </Box>
  );
};

// Add missing import
import { Switch, FormControlLabel } from '@mui/material';