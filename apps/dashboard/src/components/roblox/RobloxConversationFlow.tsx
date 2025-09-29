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

            {Object.entries(context?.stageData || {}).map(([stage, data]: [string, any]) => (
              <Box key={stage} mb="md">
                <Text size="sm" weight={600} color="blue" mb="xs">
                  {stages.find(s => s.id === stage)?.name}
                </Text>

                <Group spacing="xs" mb="xs">
                  {/* Display key data points */}
                  {data.subject_area && (
                    <Badge size="sm" variant="outline">Subject: {data.subject_area}</Badge>
                  )}
                  {data.grade_level && (
                    <Badge size="sm" variant="outline">Grade: {data.grade_level}</Badge>
                  )}
                  {data.environment_type && (
                    <Badge size="sm" variant="outline">Environment: {data.environment_type}</Badge>
                  )}
                  {data.visual_style && (
                    <Badge size="sm" variant="outline">Style: {data.visual_style}</Badge>
                  )}
                  {data.max_players && (
                    <Badge size="sm" variant="outline">Players: {data.max_players}</Badge>
                  )}
                </Group>
              </Box>
            ))}

            {/* Validation Scores */}
            {context?.stageData?.validation?.validation_scores && (
              <Box mt="lg">
                <Text weight={600} size="sm" mb="md">
                  Quality Scores
                </Text>
                {Object.entries(context.stageData.validation.validation_scores).map(([key, value]: [string, any]) => (
                  <Box key={key} mb="md">
                    <Group position="apart" mb="xs">
                      <Text size="xs">
                        {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </Text>
                      <Text size="xs" color={value >= 0.85 ? 'green' : 'orange'}>
                        {Math.round(value * 100)}%
                      </Text>
                    </Group>
                    <Progress
                      value={value * 100}
                      color={value >= 0.85 ? 'green' : 'orange'}
                      size="sm"
                    />
                  </Box>
                ))}
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