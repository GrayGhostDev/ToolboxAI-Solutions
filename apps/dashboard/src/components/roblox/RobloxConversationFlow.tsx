import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Stepper,
  Paper,
  Text,
  TextInput,
  Button,
  Alert,
  Badge,
  Progress,
  Card,
  Grid,
  Stack,
  Group,
  Divider,
  useMantineTheme,
  Title,
  Textarea,
  Loader
} from '@mantine/core';
import {
  IconCircleCheck,
  IconCircle,
  IconSchool,
  IconBrain,
  IconSettings,
  IconPalette,
  IconEdit,
  IconStar,
  IconShieldCheck,
  IconCloudUpload
} from '@tabler/icons-react';
import { useSelector } from 'react-redux';
import { type RootState } from '../../store';
import api from '../../services/api';
import { pusherService } from '../../services/pusher';

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
    icon: <IconSchool />,
    status: 'pending'
  },
  {
    id: 'discovery',
    name: 'Discovery',
    description: 'Exploring learning objectives',
    icon: <IconBrain />,
    status: 'pending'
  },
  {
    id: 'requirements',
    name: 'Requirements',
    description: 'Gathering technical requirements',
    icon: <IconSettings />,
    status: 'pending'
  },
  {
    id: 'personalization',
    name: 'Personalization',
    description: 'Customizing the experience',
    icon: <IconPalette />,
    status: 'pending'
  },
  {
    id: 'content_design',
    name: 'Content Design',
    description: 'Designing educational content',
    icon: <IconEdit />,
    status: 'pending'
  },
  {
    id: 'uniqueness_enhancement',
    name: 'Uniqueness',
    description: 'Adding creative elements',
    icon: <IconStar />,
    status: 'pending'
  },
  {
    id: 'validation',
    name: 'Validation',
    description: 'Quality and safety checks',
    icon: <IconShieldCheck />,
    status: 'pending'
  },
  {
    id: 'generation_and_review',
    name: 'Generation',
    description: 'Creating your Roblox environment',
    icon: <IconCloudUpload />,
    status: 'pending'
  }
];

const RobloxConversationFlow: React.FunctionComponent<Record<string, any>> = () => {
  const theme = useMantineTheme();
  const [stages, setStages] = useState<ConversationStage[]>(CONVERSATION_STAGES);
  const [activeStep, setActiveStep] = useState(0);
  const [context, setContext] = useState<ConversationContext | null>(null);
  const [userInput, setUserInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiResponse, setAiResponse] = useState<string | null>(null);
  const [generationStatus, setGenerationStatus] = useState<string | null>(null);

  // Fix: Changed from state.auth.user to state.user as auth slice doesn't exist
  // Defensive: Safe fallback for Redux state access
  const user = useSelector((state: RootState) => state?.user || null);

  // Initialize conversation
  const startConversation = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/api/v1/roblox/conversation/start', {
        initial_message: 'I want to create an educational Roblox experience'
      });

      // Defensive: Validate response structure
      if (response?.data?.success && response.data.session_id) {
        setContext({
          sessionId: response.data.session_id,
          currentStage: response.data.current_stage || 'greeting',
          progress: response.data.progress || 0,
          stageData: {}
        });

        // Subscribe to Pusher channel for real-time updates
        try {
          const channel = pusher?.subscribe?.(`conversation-${response.data.session_id}`);

          if (channel) {
            channel.bind('stage_processed', (data: any) => {
              try {
                handleStageUpdate(data);
              } catch (err) {
                console.error('Error handling stage update:', err);
              }
            });

            channel.bind('stage_transition', (data: any) => {
              try {
                handleStageTransition(data);
              } catch (err) {
                console.error('Error handling stage transition:', err);
              }
            });

            channel.bind('generation_complete', (data: any) => {
              try {
                handleGenerationComplete(data);
              } catch (err) {
                console.error('Error handling generation complete:', err);
              }
            });

            channel.bind('assets_uploaded', (data: any) => {
              try {
                setGenerationStatus('Assets uploaded successfully!');
              } catch (err) {
                console.error('Error handling assets uploaded:', err);
              }
            });
          }
        } catch (pusherErr) {
          console.warn('Pusher subscription failed, continuing without real-time updates:', pusherErr);
        }
      } else {
        throw new Error('Invalid response from conversation start endpoint');
      }
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to start conversation';
      setError(errorMessage);
      console.error('Error starting conversation:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Process user input for current stage
  const processUserInput = useCallback(async () => {
    // Defensive: Validate inputs before processing
    if (!context?.sessionId || !userInput?.trim()) return;

    setLoading(true);
    setError(null);
    setAiResponse(null);

    try {
      const response = await api.post('/api/v1/roblox/conversation/input', {
        session_id: context.sessionId,
        user_input: userInput.trim()
      });

      // Defensive: Validate response structure
      if (response?.data?.success && response.data.result) {
        const result = response.data.result;
        const responseText = result?.result?.response || result?.response || 'Processing complete';
        setAiResponse(responseText);

        // Update context with new data
        setContext(prev => {
          if (!prev) return prev;

          return {
            ...prev,
            stageData: {
              ...prev.stageData,
              [result.current_stage || prev.currentStage]: result.result || result
            },
            progress: typeof result.progress === 'number' ? result.progress : prev.progress
          };
        });

        // Clear input
        setUserInput('');
      } else {
        throw new Error('Invalid response from conversation input endpoint');
      }
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to process input';
      setError(errorMessage);
      console.error('Error processing user input:', err);
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
    try {
      // Defensive: Validate data structure
      if (!data) return;

      const responseText = data?.result?.response || data?.response || 'Stage completed';
      setAiResponse(responseText);

      setContext(prev => {
        if (!prev) return prev;

        return {
          ...prev,
          stageData: {
            ...prev.stageData,
            [data.stage || 'unknown']: data.result || data
          }
        };
      });
    } catch (err) {
      console.error('Error in handleStageUpdate:', err);
    }
  };

  const handleStageTransition = (data: any) => {
    try {
      // Defensive: Validate data and find stage
      if (!data?.to || !Array.isArray(stages)) return;

      const nextStageIndex = stages.findIndex(s => s?.id === data.to);
      if (nextStageIndex !== -1) {
        setActiveStep(nextStageIndex);
        updateStageStatus(nextStageIndex);
      }

      setContext(prev => {
        if (!prev) return prev;

        return {
          ...prev,
          currentStage: data.to,
          progress: typeof data.progress === 'number' ? data.progress : prev.progress
        };
      });
    } catch (err) {
      console.error('Error in handleStageTransition:', err);
    }
  };

  const handleGenerationComplete = (data: any) => {
    try {
      // Defensive: Validate data structure
      if (!data) return;

      setGenerationStatus('Environment ready for Roblox Studio!');

      setContext(prev => {
        if (!prev) return prev;

        return {
          ...prev,
          robloxData: {
            projectId: data.project_id || 'unknown',
            rojoPort: data.rojo_port || 34872,
            syncUrl: data.rojo_port ? `http://localhost:${data.rojo_port}` : 'http://localhost:34872'
          }
        };
      });
    } catch (err) {
      console.error('Error in handleGenerationComplete:', err);
    }
  };

  const updateStageStatus = (currentIndex: number) => {
    // Defensive: Validate currentIndex is a valid number
    if (typeof currentIndex !== 'number' || currentIndex < 0) return;

    setStages(prev => {
      // Defensive: Ensure prev is an array
      if (!Array.isArray(prev)) return prev;

      return prev.map((stage, index) => {
        // Defensive: Validate stage object
        if (!stage) return stage;

        return {
          ...stage,
          status: index < currentIndex ? 'completed' :
                  index === currentIndex ? 'active' : 'pending'
        };
      });
    });
  };

  // Start conversation on mount if not started
  useEffect(() => {
    if (!context) {
      startConversation();
    }

    return () => {
      if (context?.sessionId) {
        try {
          pusher?.unsubscribe?.(`conversation-${context.sessionId}`);
        } catch (err) {
          console.warn('Error unsubscribing from Pusher:', err);
        }
      }
    };
  }, [context, startConversation]);

  return (
    <Box style={{ width: '100%', padding: theme.spacing.lg }}>
      <Title order={2} mb="lg">
        Create Your Educational Roblox Experience
      </Title>

      {/* Progress Bar */}
      <Box mb="lg">
        <Text size="sm" color="dimmed" mb="xs">
          Overall Progress: {Math.round(context?.progress || 0)}%
        </Text>
        <Progress
          value={context?.progress || 0}
          size="lg"
          radius="xl"
        />
      </Box>

      <Grid>
        {/* Conversation Stepper */}
        <Grid.Col span={12} md={8}>
          <Paper shadow="md" style={{ padding: theme.spacing.lg }}>
            <Stepper active={activeStep} orientation="vertical" size="sm">
              {stages.map((stage, index) => (
                <Stepper.Step
                  key={stage.id}
                  icon={
                    stage.status === 'completed' ? <IconCircleCheck color={theme.colors.green[6]} /> :
                    stage.status === 'active' ? stage.icon : <IconCircle />
                  }
                  label={stage.name}
                  description={stage.description}
                >
                  {/* AI Response */}
                  {aiResponse && activeStep === index && (
                    <Alert color="blue" mb="md">
                      {aiResponse}
                    </Alert>
                  )}

                  {/* User Input */}
                  {stage.status === 'active' && stage.id !== 'generation_and_review' && (
                    <Box mb="md">
                      <Textarea
                        value={userInput}
                        onChange={(e) => setUserInput(e.target.value)}
                        placeholder="Type your response here..."
                        disabled={loading}
                        minRows={3}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && e.shiftKey === false) {
                            e.preventDefault();
                            processUserInput();
                          }
                        }}
                      />
                      <Group mt="md">
                        <Button
                          onClick={processUserInput}
                          disabled={loading || !userInput.trim()}
                          leftIcon={loading ? <Loader size={16} /> : undefined}
                        >
                          {loading ? 'Sending...' : 'Send'}
                        </Button>
                        <Button
                          variant="outline"
                          onClick={advanceStage}
                          disabled={loading}
                        >
                          Skip to Next
                        </Button>
                      </Group>
                    </Box>
                  )}

                  {/* Generation Stage */}
                  {stage.id === 'generation_and_review' && stage.status === 'active' && (
                    <Box>
                      <Button
                        color="blue"
                        onClick={generateEnvironment}
                        disabled={loading}
                        leftIcon={<IconCloudUpload />}
                        mb="md"
                      >
                        Generate Roblox Environment
                      </Button>

                      {generationStatus && (
                        <Alert color="green" mb="md">
                          {generationStatus}
                        </Alert>
                      )}

                      {context?.robloxData && (
                        <Card withBorder mb="md">
                          <Title order={4} mb="md">
                            Roblox Studio Connection
                          </Title>
                          <Stack spacing="xs">
                            <Group position="apart">
                              <Text size="sm" weight={500}>Project ID</Text>
                              <Text size="sm" color="dimmed">{context.robloxData.projectId}</Text>
                            </Group>
                            <Group position="apart">
                              <Text size="sm" weight={500}>Rojo Port</Text>
                              <Text size="sm" color="dimmed">{context.robloxData.rojoPort}</Text>
                            </Group>
                            <Group position="apart">
                              <Text size="sm" weight={500}>Sync URL</Text>
                              <Text size="sm" color="dimmed">{context.robloxData.syncUrl}</Text>
                            </Group>
                          </Stack>
                          <Text size="sm" color="dimmed" mt="md">
                            Open Roblox Studio and connect to this URL using the Rojo plugin
                          </Text>
                        </Card>
                      )}
                    </Box>
                  )}
                </Stepper.Step>
              ))}
            </Stepper>
          </Paper>
        </Grid.Col>

        {/* Stage Data Summary */}
        <Grid.Col span={12} md={4}>
          <Paper shadow="md" style={{ padding: theme.spacing.lg }}>
            <Title order={4} mb="md">
              Your Choices
            </Title>
            <Divider mb="md" />

            {Object.entries(context?.stageData || {}).map(([stage, data]: [string, any]) => {
              // Defensive: Validate stage and data
              if (!stage || !data) return null;

              return (
              <Box key={stage} mb="md">
                <Text size="sm" fw={600} c="blue" mb="xs">
                  {/* Defensive: Safe stage name lookup */}
                  {Array.isArray(stages) ? stages.find(s => s?.id === stage)?.name || stage : stage}
                </Text>

                <Group gap="xs" mb="xs">
                  {/* Display key data points with defensive checks */}
                  {data?.subject_area && (
                    <Badge size="sm" variant="outline">Subject: {data.subject_area}</Badge>
                  )}
                  {data?.grade_level && (
                    <Badge size="sm" variant="outline">Grade: {data.grade_level}</Badge>
                  )}
                  {data?.environment_type && (
                    <Badge size="sm" variant="outline">Environment: {data.environment_type}</Badge>
                  )}
                  {data?.visual_style && (
                    <Badge size="sm" variant="outline">Style: {data.visual_style}</Badge>
                  )}
                  {data?.max_players && (
                    <Badge size="sm" variant="outline">Players: {data.max_players}</Badge>
                  )}
                </Group>
              </Box>
              );
            })}

            {/* Validation Scores */}
            {context?.stageData?.validation?.validation_scores && (
              <Box mt="lg">
                <Text fw={600} size="sm" mb="md">
                  Quality Scores
                </Text>
                {/* Defensive: Safe object entries with validation */}
                {Object.entries(context.stageData.validation.validation_scores || {}).map(([key, value]: [string, any]) => {
                  // Defensive: Validate key and value
                  if (!key || typeof value !== 'number') return null;

                  const percentage = Math.round(Math.max(0, Math.min(1, value)) * 100);
                  const isGood = value >= 0.85;

                  return (
                  <Box key={key} mb="md">
                    <Group justify="space-between" mb="xs">
                      <Text size="xs">
                        {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </Text>
                      <Text size="xs" c={isGood ? 'green' : 'orange'}>
                        {percentage}%
                      </Text>
                    </Group>
                    <Progress
                      value={percentage}
                      color={isGood ? 'green' : 'orange'}
                      size="sm"
                    />
                  </Box>
                  );
                })}
              </Box>
            )}
          </Paper>
        </Grid.Col>
      </Grid>

      {/* Error Display */}
      {error && (
        <Alert color="red" mt="md" onClose={() => setError(null)} withCloseButton>
          {error}
        </Alert>
      )}
    </Box>
  );
};

export default RobloxConversationFlow;