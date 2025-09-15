import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  Paper,
  Typography,
  TextField,
  CircularProgress,
  Alert,
  Chip,
  LinearProgress,
  Card,
  CardContent,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider
} from '@mui/material';
import {
  CheckCircle,
  RadioButtonUnchecked,
  School,
  Psychology,
  Settings,
  Palette,
  Create,
  Stars,
  VerifiedUser,
  CloudUpload
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import api from '../../services/api';
import pusher from '../../services/pusher';

interface ConversationStage {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  status: 'pending' | 'active' | 'completed';
  data?: any;
}

interface ConversationContext {
  sessionId: string;
  currentStage: string;
  progress: number;
  stageData: Record<string, any>;
  robloxData?: {
    projectId?: string;
    rojoPort?: number;
    syncUrl?: string;
  };
}

const CONVERSATION_STAGES: ConversationStage[] = [
  {
    id: 'greeting',
    name: 'Welcome',
    description: 'Introduction and understanding your goals',
    icon: <School />,
    status: 'pending'
  },
  {
    id: 'discovery',
    name: 'Discovery',
    description: 'Exploring learning objectives',
    icon: <Psychology />,
    status: 'pending'
  },
  {
    id: 'requirements',
    name: 'Requirements',
    description: 'Gathering technical requirements',
    icon: <Settings />,
    status: 'pending'
  },
  {
    id: 'personalization',
    name: 'Personalization',
    description: 'Customizing the experience',
    icon: <Palette />,
    status: 'pending'
  },
  {
    id: 'content_design',
    name: 'Content Design',
    description: 'Designing educational content',
    icon: <Create />,
    status: 'pending'
  },
  {
    id: 'uniqueness_enhancement',
    name: 'Uniqueness',
    description: 'Adding creative elements',
    icon: <Stars />,
    status: 'pending'
  },
  {
    id: 'validation',
    name: 'Validation',
    description: 'Quality and safety checks',
    icon: <VerifiedUser />,
    status: 'pending'
  },
  {
    id: 'generation_and_review',
    name: 'Generation',
    description: 'Creating your Roblox environment',
    icon: <CloudUpload />,
    status: 'pending'
  }
];

const RobloxConversationFlow: React.FC = () => {
  const [stages, setStages] = useState<ConversationStage[]>(CONVERSATION_STAGES);
  const [activeStep, setActiveStep] = useState(0);
  const [context, setContext] = useState<ConversationContext | null>(null);
  const [userInput, setUserInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiResponse, setAiResponse] = useState<string | null>(null);
  const [generationStatus, setGenerationStatus] = useState<string | null>(null);

  const user = useSelector((state: RootState) => state.auth.user);

  // Initialize conversation
  const startConversation = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/api/v1/roblox/conversation/start', {
        initial_message: 'I want to create an educational Roblox experience'
      });

      if (response.data.success) {
        setContext({
          sessionId: response.data.session_id,
          currentStage: response.data.current_stage,
          progress: 0,
          stageData: {}
        });

        // Subscribe to Pusher channel for real-time updates
        const channel = pusher.subscribe(`conversation-${response.data.session_id}`);

        channel.bind('stage_processed', (data: any) => {
          handleStageUpdate(data);
        });

        channel.bind('stage_transition', (data: any) => {
          handleStageTransition(data);
        });

        channel.bind('generation_complete', (data: any) => {
          handleGenerationComplete(data);
        });

        channel.bind('assets_uploaded', (data: any) => {
          setGenerationStatus('Assets uploaded successfully!');
        });
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start conversation');
    } finally {
      setLoading(false);
    }
  }, []);

  // Process user input for current stage
  const processUserInput = useCallback(async () => {
    if (!context || !userInput.trim()) return;

    setLoading(true);
    setError(null);
    setAiResponse(null);

    try {
      const response = await api.post('/api/v1/roblox/conversation/input', {
        session_id: context.sessionId,
        user_input: userInput
      });

      if (response.data.success) {
        const result = response.data.result;
        setAiResponse(result.result.response || 'Processing complete');

        // Update context with new data
        setContext(prev => ({
          ...prev!,
          stageData: {
            ...prev!.stageData,
            [result.current_stage]: result.result
          },
          progress: result.progress
        }));

        // Clear input
        setUserInput('');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process input');
    } finally {
      setLoading(false);
    }
  }, [context, userInput]);

  // Advance to next stage
  const advanceStage = useCallback(async () => {
    if (!context) return;

    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/api/v1/roblox/conversation/advance', null, {
        params: { session_id: context.sessionId }
      });

      if (response.data.success) {
        const nextStageIndex = stages.findIndex(s => s.id === response.data.current_stage);
        if (nextStageIndex !== -1) {
          setActiveStep(nextStageIndex);
          updateStageStatus(nextStageIndex);
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to advance stage');
    } finally {
      setLoading(false);
    }
  }, [context, stages]);

  // Generate Roblox environment
  const generateEnvironment = useCallback(async () => {
    if (!context) return;

    setLoading(true);
    setError(null);
    setGenerationStatus('Starting generation...');

    try {
      const response = await api.post('/api/v1/roblox/conversation/generate', null, {
        params: { session_id: context.sessionId }
      });

      if (response.data.success) {
        setGenerationStatus('Environment generated successfully!');

        // Update context with Roblox data
        setContext(prev => ({
          ...prev!,
          robloxData: {
            projectId: response.data.generation_result.project_id,
            rojoPort: response.data.generation_result.rojo_port,
            syncUrl: response.data.rojo_connect_url
          }
        }));
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate environment');
      setGenerationStatus(null);
    } finally {
      setLoading(false);
    }
  }, [context]);

  // Handle real-time updates
  const handleStageUpdate = (data: any) => {
    setAiResponse(data.result.response || 'Stage completed');
    setContext(prev => ({
      ...prev!,
      stageData: {
        ...prev!.stageData,
        [data.stage]: data.result
      }
    }));
  };

  const handleStageTransition = (data: any) => {
    const nextStageIndex = stages.findIndex(s => s.id === data.to);
    if (nextStageIndex !== -1) {
      setActiveStep(nextStageIndex);
      updateStageStatus(nextStageIndex);
    }

    setContext(prev => ({
      ...prev!,
      currentStage: data.to,
      progress: data.progress
    }));
  };

  const handleGenerationComplete = (data: any) => {
    setGenerationStatus('Environment ready for Roblox Studio!');
    setContext(prev => ({
      ...prev!,
      robloxData: {
        projectId: data.project_id,
        rojoPort: data.rojo_port,
        syncUrl: `http://localhost:${data.rojo_port}`
      }
    }));
  };

  const updateStageStatus = (currentIndex: number) => {
    setStages(prev => prev.map((stage, index) => ({
      ...stage,
      status: index < currentIndex ? 'completed' :
              index === currentIndex ? 'active' : 'pending'
    })));
  };

  // Start conversation on mount if not started
  useEffect(() => {
    if (!context) {
      startConversation();
    }

    return () => {
      if (context) {
        pusher.unsubscribe(`conversation-${context.sessionId}`);
      }
    };
  }, [context, startConversation]);

  return (
    <Box sx={{ width: '100%', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Create Your Educational Roblox Experience
      </Typography>

      {/* Progress Bar */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="body2" color="text.secondary">
          Overall Progress: {Math.round(context?.progress || 0)}%
        </Typography>
        <LinearProgress
          variant="determinate"
          value={context?.progress || 0}
          sx={{ height: 8, borderRadius: 4 }}
        />
      </Box>

      <Grid container spacing={3}>
        {/* Conversation Stepper */}
        <Grid item xs={12} md={8}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Stepper activeStep={activeStep} orientation="vertical">
              {stages.map((stage, index) => (
                <Step key={stage.id} completed={stage.status === 'completed'}>
                  <StepLabel
                    optional={
                      <Typography variant="caption">{stage.description}</Typography>
                    }
                    icon={stage.status === 'completed' ? <CheckCircle color="success" /> :
                          stage.status === 'active' ? stage.icon : <RadioButtonUnchecked />}
                  >
                    {stage.name}
                  </StepLabel>
                  <StepContent>
                    {/* AI Response */}
                    {aiResponse && activeStep === index && (
                      <Alert severity="info" sx={{ mb: 2 }}>
                        {aiResponse}
                      </Alert>
                    )}

                    {/* User Input */}
                    {stage.status === 'active' && stage.id !== 'generation_and_review' && (
                      <Box sx={{ mb: 2 }}>
                        <TextField
                          fullWidth
                          multiline
                          rows={3}
                          value={userInput}
                          onChange={(e) => setUserInput(e.target.value)}
                          placeholder="Type your response here..."
                          disabled={loading}
                          onKeyPress={(e) => {
                            if (e.key === 'Enter' && e.shiftKey === false) {
                              e.preventDefault();
                              processUserInput();
                            }
                          }}
                        />
                        <Box sx={{ mt: 2 }}>
                          <Button
                            variant="contained"
                            onClick={processUserInput}
                            disabled={loading || !userInput.trim()}
                            sx={{ mr: 1 }}
                          >
                            {loading ? <CircularProgress size={24} /> : 'Send'}
                          </Button>
                          <Button
                            variant="outlined"
                            onClick={advanceStage}
                            disabled={loading}
                          >
                            Skip to Next
                          </Button>
                        </Box>
                      </Box>
                    )}

                    {/* Generation Stage */}
                    {stage.id === 'generation_and_review' && stage.status === 'active' && (
                      <Box>
                        <Button
                          variant="contained"
                          color="primary"
                          onClick={generateEnvironment}
                          disabled={loading}
                          startIcon={<CloudUpload />}
                          sx={{ mb: 2 }}
                        >
                          Generate Roblox Environment
                        </Button>

                        {generationStatus && (
                          <Alert severity="success" sx={{ mb: 2 }}>
                            {generationStatus}
                          </Alert>
                        )}

                        {context?.robloxData && (
                          <Card sx={{ mb: 2 }}>
                            <CardContent>
                              <Typography variant="h6" gutterBottom>
                                Roblox Studio Connection
                              </Typography>
                              <List dense>
                                <ListItem>
                                  <ListItemText
                                    primary="Project ID"
                                    secondary={context.robloxData.projectId}
                                  />
                                </ListItem>
                                <ListItem>
                                  <ListItemText
                                    primary="Rojo Port"
                                    secondary={context.robloxData.rojoPort}
                                  />
                                </ListItem>
                                <ListItem>
                                  <ListItemText
                                    primary="Sync URL"
                                    secondary={context.robloxData.syncUrl}
                                  />
                                </ListItem>
                              </List>
                              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                                Open Roblox Studio and connect to this URL using the Rojo plugin
                              </Typography>
                            </CardContent>
                          </Card>
                        )}
                      </Box>
                    )}
                  </StepContent>
                </Step>
              ))}
            </Stepper>
          </Paper>
        </Grid>

        {/* Stage Data Summary */}
        <Grid item xs={12} md={4}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Your Choices
            </Typography>
            <Divider sx={{ mb: 2 }} />

            {Object.entries(context?.stageData || {}).map(([stage, data]: [string, any]) => (
              <Box key={stage} sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="primary" gutterBottom>
                  {stages.find(s => s.id === stage)?.name}
                </Typography>

                {/* Display key data points */}
                {data.subject_area && (
                  <Chip label={`Subject: ${data.subject_area}`} size="small" sx={{ mr: 1, mb: 1 }} />
                )}
                {data.grade_level && (
                  <Chip label={`Grade: ${data.grade_level}`} size="small" sx={{ mr: 1, mb: 1 }} />
                )}
                {data.environment_type && (
                  <Chip label={`Environment: ${data.environment_type}`} size="small" sx={{ mr: 1, mb: 1 }} />
                )}
                {data.visual_style && (
                  <Chip label={`Style: ${data.visual_style}`} size="small" sx={{ mr: 1, mb: 1 }} />
                )}
                {data.max_players && (
                  <Chip label={`Players: ${data.max_players}`} size="small" sx={{ mr: 1, mb: 1 }} />
                )}
              </Box>
            ))}

            {/* Validation Scores */}
            {context?.stageData?.validation?.validation_scores && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Quality Scores
                </Typography>
                {Object.entries(context.stageData.validation.validation_scores).map(([key, value]: [string, any]) => (
                  <Box key={key} sx={{ mb: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">
                        {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </Typography>
                      <Typography variant="body2" color={value >= 0.85 ? 'success.main' : 'warning.main'}>
                        {Math.round(value * 100)}%
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={value * 100}
                      color={value >= 0.85 ? 'success' : 'warning'}
                      sx={{ height: 4, borderRadius: 2 }}
                    />
                  </Box>
                ))}
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
    </Box>
  );
};

export default RobloxConversationFlow;