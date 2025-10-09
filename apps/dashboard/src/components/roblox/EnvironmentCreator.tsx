/**
 * Roblox Environment Creator Component
 * Allows users to create Roblox environments from natural language descriptions
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  Text,
  TextInput,
  Button,
  Alert,
  Loader,
  Badge,
  Grid,
  Select,
  Stepper,
  Paper,
  List,
  ActionIcon,
  Tooltip,
  Group,
  useMantineTheme,
  Stack,
  Textarea,
  NumberInput,
  Title,
  Divider,
  SimpleGrid
} from '@mantine/core';
import {
  IconPlus,
  IconCircleCheck,
  IconX,
  IconInfoCircle,
  IconMountain,
  IconHome,
  IconBulb,
  IconDeviceDesktop,
  IconTrash,
  IconRefresh
} from '@tabler/icons-react';

import {
  robloxEnvironmentService,
  type EnvironmentCreationRequest,
  type EnvironmentCreationResponse,
  EnvironmentStatusResponse,
  type RojoConnectionResponse
} from '../../services/robloxEnvironment';

interface EnvironmentCreatorProps {
  onEnvironmentCreated?: (environment: EnvironmentCreationResponse) => void;
}

const EnvironmentCreator: React.FunctionComponent<EnvironmentCreatorProps> = ({ onEnvironmentCreated }) => {
  const theme = useMantineTheme();

  // Form state
  const [formData, setFormData] = useState<EnvironmentCreationRequest>({
    name: '',
    description: '',
    grade_level: '',
    subject: '',
    max_players: 20,
    settings: {}
  });

  // UI state
  const [activeStep, setActiveStep] = useState(0);
  const [isCreating, setIsCreating] = useState(false);
  const [isCheckingRojo, setIsCheckingRojo] = useState(false);
  const [rojoStatus, setRojoStatus] = useState<RojoConnectionResponse | null>(null);
  const [creationResult, setCreationResult] = useState<EnvironmentCreationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [previewComponents, setPreviewComponents] = useState<any>(null);
  const [environmentPreview, setEnvironmentPreview] = useState<any>(null);
  const [isGeneratingPreview, setIsGeneratingPreview] = useState(false);

  // Check Rojo connection on component mount
  useEffect(() => {
    checkRojoConnection();
  }, []);

  // Update preview when description changes
  useEffect(() => {
    if (formData.description) {
      const components = robloxEnvironmentService.parseDescription(formData.description);
      setPreviewComponents(components);
      generateEnvironmentPreview(components);
    } else {
      setPreviewComponents(null);
      setEnvironmentPreview(null);
    }
  }, [formData.description]);

  const generateEnvironmentPreview = async (components: any) => {
    setIsGeneratingPreview(true);

    try {
      // Call backend API to generate detailed preview
      const previewRequest = {
        name: formData.name || 'Preview Environment',
        description: formData.description,
        grade_level: formData.grade_level,
        subject: formData.subject,
        max_players: formData.max_players,
        settings: formData.settings
      };

      const response = await robloxEnvironmentService.previewEnvironment(previewRequest);

      if (response.success && response.preview) {
        setEnvironmentPreview(response.preview);
      } else {
        // Fallback to client-side preview if backend fails
        const fallbackPreview = {
          name: formData.name || 'Preview Environment',
          structure: {
            terrain: components.terrain.map((item: string) => ({
              type: item,
              position: { x: Math.random() * 100, y: 0, z: Math.random() * 100 },
              size: { x: 20, y: 10, z: 20 },
              color: '#4CAF50'
            })),
            buildings: components.buildings.map((item: string, index: number) => ({
              type: item,
              position: { x: index * 30, y: 0, z: 0 },
              size: { x: 25, y: 15, z: 25 },
              color: '#' + Math.floor(Math.random()*16777215).toString(16)
            })),
            objects: components.objects.map((item: string, index: number) => ({
              type: item,
              position: { x: Math.random() * 50, y: 0, z: Math.random() * 50 },
              size: { x: 5, y: 5, z: 5 },
              color: '#' + Math.floor(Math.random()*16777215).toString(16)
            }))
          },
          lighting: {
            type: components.lighting,
            brightness: components.lighting === 'Bright/Sunny' ? 1.0 :
                       components.lighting === 'Dark/Night' ? 0.3 : 0.7,
            color: components.lighting === 'Bright/Sunny' ? '#FFE4B5' :
                   components.lighting === 'Dark/Night' ? '#1A1A2E' : '#FFFFFF'
          },
          effects: components.effects.map((effect: string) => ({
            type: effect,
            intensity: 0.5,
            active: true
          }))
        };
        setEnvironmentPreview(fallbackPreview);
      }
    } catch (error) {
      console.error('Failed to generate environment preview:', error);
      // Show error but don't break the UI
      setError('Failed to generate preview, but you can still create the environment');
    } finally {
      setIsGeneratingPreview(false);
    }
  };

  const checkRojoConnection = async () => {
    setIsCheckingRojo(true);
    setError(null);

    try {
      const status = await robloxEnvironmentService.checkRojoConnection();
      setRojoStatus(status);
    } catch (err) {
      setError('Failed to check Rojo connection');
      console.error('Rojo connection check failed:', err);
    } finally {
      setIsCheckingRojo(false);
    }
  };

  const handleInputChange = (field: keyof EnvironmentCreationRequest) => (
    value: string | number
  ) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleCreateEnvironment = async () => {
    // Validate form
    const validation = robloxEnvironmentService.validateRequest(formData);
    if (!validation.valid) {
      setError(validation.errors.join(', '));
      return;
    }

    setIsCreating(true);
    setError(null);
    setCreationResult(null);

    try {
      const result = await robloxEnvironmentService.createEnvironment(formData);
      setCreationResult(result);

      if (result.success && onEnvironmentCreated) {
        onEnvironmentCreated(result);
      }

      if (result.success) {
        setActiveStep(2); // Move to success step
      } else {
        setError(result.error || 'Environment creation failed');
      }
    } catch (err) {
      setError('Failed to create environment');
      console.error('Environment creation failed:', err);
    } finally {
      setIsCreating(false);
    }
  };

  const handleReset = () => {
    setFormData({
      name: '',
      description: '',
      grade_level: '',
      subject: '',
      max_players: 20,
      settings: {}
    });
    setActiveStep(0);
    setCreationResult(null);
    setError(null);
    setPreviewComponents(null);
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Stack spacing="md">
            <Grid>
              <Grid.Col span={12} md={6}>
                <TextInput
                  label="Environment Name"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name')(e.target.value)}
                  placeholder="e.g., Math Adventure World"
                  description="Choose a descriptive name for your environment"
                />
              </Grid.Col>
              <Grid.Col span={12} md={6}>
                <Select
                  label="Grade Level"
                  value={formData.grade_level}
                  onChange={(value) => handleInputChange('grade_level')(value || '')}
                  data={[
                    { value: '', label: 'Any Grade' },
                    { value: 'K-2', label: 'K-2 (Elementary)' },
                    { value: '3-5', label: '3-5 (Elementary)' },
                    { value: '6-8', label: '6-8 (Middle School)' },
                    { value: '9-12', label: '9-12 (High School)' }
                  ]}
                />
              </Grid.Col>
              <Grid.Col span={12} md={6}>
                <Select
                  label="Subject"
                  value={formData.subject}
                  onChange={(value) => handleInputChange('subject')(value || '')}
                  data={[
                    { value: '', label: 'Any Subject' },
                    { value: 'math', label: 'Mathematics' },
                    { value: 'science', label: 'Science' },
                    { value: 'history', label: 'History' },
                    { value: 'english', label: 'English/Language Arts' },
                    { value: 'art', label: 'Art' },
                    { value: 'music', label: 'Music' }
                  ]}
                />
              </Grid.Col>
              <Grid.Col span={12} md={6}>
                <NumberInput
                  label="Maximum Players"
                  value={formData.max_players}
                  onChange={(value) => handleInputChange('max_players')(value || 20)}
                  min={1}
                  max={100}
                  description="Maximum number of students who can join"
                />
              </Grid.Col>
              <Grid.Col span={12}>
                <Textarea
                  label="Environment Description"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description')(e.target.value)}
                  placeholder="Describe your educational environment in natural language. For example: 'Create a math classroom with interactive whiteboards, student desks, and a cozy reading corner with books about numbers and shapes.'"
                  description="Be as detailed as possible. Include buildings, objects, terrain, lighting, and any special features."
                  minRows={4}
                />
              </Grid.Col>
            </Grid>

            {/* Environment Preview */}
            {environmentPreview && (
              <Box mt="lg">
                <Title order={4} mb="md">Environment Preview</Title>

                {isGeneratingPreview ? (
                  <Group spacing="md" style={{ padding: theme.spacing.md }}>
                    <Loader size={20} />
                    <Text size="sm">Generating environment preview...</Text>
                  </Group>
                ) : (
                  <Card withBorder>
                    <Title order={5} mb="md">
                      {environmentPreview.name}
                    </Title>

                    {/* 3D Environment Visualization */}
                    <Box style={{
                      height: 300,
                      backgroundColor: theme.colors.gray[1],
                      borderRadius: theme.radius.sm,
                      position: 'relative',
                      overflow: 'hidden',
                      border: `1px solid ${theme.colors.gray[3]}`
                    }}>
                      {/* Terrain */}
                      {environmentPreview.structure.terrain.map((terrain: any, index: number) => (
                        <Box
                          key={`terrain-${index}`}
                          style={{
                            position: 'absolute',
                            left: `${terrain.position.x}%`,
                            top: `${terrain.position.z}%`,
                            width: `${terrain.size.x}px`,
                            height: `${terrain.size.z}px`,
                            backgroundColor: theme.colors.green[5],
                            borderRadius: '50%',
                            opacity: 0.7,
                            border: `2px solid ${theme.colors.green[7]}`
                          }}
                          title={terrain.type}
                        />
                      ))}

                      {/* Buildings */}
                      {environmentPreview.structure.buildings.map((building: any, index: number) => (
                        <Box
                          key={`building-${index}`}
                          style={{
                            position: 'absolute',
                            left: `${building.position.x}%`,
                            top: `${building.position.z}%`,
                            width: `${building.size.x}px`,
                            height: `${building.size.z}px`,
                            backgroundColor: building.color,
                            border: '2px solid #333',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '10px',
                            fontWeight: 700,
                            color: 'white',
                            textShadow: '1px 1px 1px rgba(0,0,0,0.5)'
                          }}
                          title={building.type}
                        >
                          {building.type.split('/')[0]}
                        </Box>
                      ))}

                      {/* Objects */}
                      {environmentPreview.structure.objects.map((object: any, index: number) => (
                        <Box
                          key={`object-${index}`}
                          style={{
                            position: 'absolute',
                            left: `${object.position.x}%`,
                            top: `${object.position.z}%`,
                            width: `${object.size.x}px`,
                            height: `${object.size.z}px`,
                            backgroundColor: object.color,
                            border: '1px solid #666',
                            borderRadius: theme.radius.xs,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '8px',
                            color: 'white',
                            textShadow: '1px 1px 1px rgba(0,0,0,0.5)'
                          }}
                          title={object.type}
                        >
                          {object.type.split('/')[0]}
                        </Box>
                      ))}

                      {/* Lighting Overlay */}
                      <Box
                        style={{
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          right: 0,
                          bottom: 0,
                          backgroundColor: environmentPreview.lighting.color,
                          opacity: 1 - environmentPreview.lighting.brightness,
                          pointerEvents: 'none'
                        }}
                      />

                      {/* Legend */}
                      <Box style={{
                        position: 'absolute',
                        top: 8,
                        left: 8,
                        backgroundColor: 'rgba(255,255,255,0.9)',
                        padding: theme.spacing.xs,
                        borderRadius: theme.radius.sm,
                        fontSize: '10px'
                      }}>
                        <Text size="xs">
                          🟢 Terrain   🏠 Buildings   📦 Objects
                        </Text>
                      </Box>
                    </Box>

                    {/* Environment Details */}
                    <Box mt="md">
                      <SimpleGrid cols={2} spacing="md">
                        <Text size="sm" color="dimmed">
                          <strong>Lighting:</strong> {environmentPreview.lighting.type}
                        </Text>
                        <Text size="sm" color="dimmed">
                          <strong>Effects:</strong> {environmentPreview.effects.length > 0 ?
                            environmentPreview.effects.map((e: any) => e.type).join(', ') : 'None'}
                        </Text>
                        <Text size="sm" color="dimmed">
                          <strong>Terrain:</strong> {environmentPreview.structure.terrain.length} areas
                        </Text>
                        <Text size="sm" color="dimmed">
                          <strong>Buildings:</strong> {environmentPreview.structure.buildings.length} structures
                        </Text>
                      </SimpleGrid>
                    </Box>
                  </Card>
                )}
              </Box>
            )}
          </Stack>
        );

      case 1:
        return (
          <Stack spacing="md">
            {/* Rojo Status */}
            <Card withBorder>
              <Group position="apart" align="center" mb="md">
                <Text weight={600} size="lg">Roblox Studio Connection</Text>
                <Group spacing="xs">
                  {isCheckingRojo ? (
                    <Loader size={20} />
                  ) : (
                    <Tooltip label="Refresh connection">
                      <ActionIcon onClick={checkRojoConnection} size="sm">
                        <IconRefresh />
                      </ActionIcon>
                    </Tooltip>
                  )}
                </Group>
              </Group>

              {rojoStatus && (
                <Box>
                  <Badge
                    leftSection={rojoStatus.rojo_connected ? <IconCircleCheck size={14} /> : <IconX size={14} />}
                    color={rojoStatus.rojo_connected ? 'green' : 'red'}
                    variant="outline"
                    mb="xs"
                  >
                    {rojoStatus.rojo_connected ? 'Connected to Roblox Studio' : 'Not Connected'}
                  </Badge>
                  {rojoStatus.rojo_url && (
                    <Text size="sm" color="dimmed">
                      Rojo URL: {rojoStatus.rojo_url}
                    </Text>
                  )}
                </Box>
              )}
            </Card>

            {/* Environment Preview */}
            {previewComponents && (
              <Card withBorder>
                <Text weight={600} size="lg" mb="md">
                  Environment Preview
                </Text>

                <SimpleGrid cols={4} spacing="md">
                  {previewComponents.terrain.length > 0 && (
                    <Paper style={{ padding: theme.spacing.md, textAlign: 'center' }}>
                      <IconMountain color={theme.colors.blue[6]} style={{ marginBottom: theme.spacing.xs }} />
                      <Text weight={600} size="sm" mb="xs">Terrain</Text>
                      <Stack spacing={4}>
                        {previewComponents.terrain.map((item: string, index: number) => (
                          <Badge key={index} size="sm">{item}</Badge>
                        ))}
                      </Stack>
                    </Paper>
                  )}

                  {previewComponents.buildings.length > 0 && (
                    <Paper style={{ padding: theme.spacing.md, textAlign: 'center' }}>
                      <IconHome color={theme.colors.blue[6]} style={{ marginBottom: theme.spacing.xs }} />
                      <Text weight={600} size="sm" mb="xs">Buildings</Text>
                      <Stack spacing={4}>
                        {previewComponents.buildings.map((item: string, index: number) => (
                          <Badge key={index} size="sm">{item}</Badge>
                        ))}
                      </Stack>
                    </Paper>
                  )}

                  {previewComponents.objects.length > 0 && (
                    <Paper style={{ padding: theme.spacing.md, textAlign: 'center' }}>
                      <IconDeviceDesktop color={theme.colors.blue[6]} style={{ marginBottom: theme.spacing.xs }} />
                      <Text weight={600} size="sm" mb="xs">Objects</Text>
                      <Stack spacing={4}>
                        {previewComponents.objects.map((item: string, index: number) => (
                          <Badge key={index} size="sm">{item}</Badge>
                        ))}
                      </Stack>
                    </Paper>
                  )}

                  <Paper style={{ padding: theme.spacing.md, textAlign: 'center' }}>
                    <IconBulb color={theme.colors.blue[6]} style={{ marginBottom: theme.spacing.xs }} />
                    <Text weight={600} size="sm" mb="xs">Lighting</Text>
                    <Badge size="sm">{previewComponents.lighting}</Badge>
                  </Paper>
                </SimpleGrid>
              </Card>
            )}

            {/* Environment Summary */}
            <Card withBorder>
              <Text weight={600} size="lg" mb="md">
                Environment Summary
              </Text>
              <Stack spacing="xs">
                <Group position="apart">
                  <Text size="sm">Name</Text>
                  <Text size="sm" color="dimmed">{formData.name}</Text>
                </Group>
                <Group position="apart">
                  <Text size="sm">Grade Level</Text>
                  <Text size="sm" color="dimmed">{formData.grade_level || 'Any'}</Text>
                </Group>
                <Group position="apart">
                  <Text size="sm">Subject</Text>
                  <Text size="sm" color="dimmed">{formData.subject || 'Any'}</Text>
                </Group>
                <Group position="apart">
                  <Text size="sm">Max Players</Text>
                  <Text size="sm" color="dimmed">{formData.max_players}</Text>
                </Group>
              </Stack>
            </Card>
          </Stack>
        );

      case 2:
        return (
          <Box>
            {creationResult && (
              <Card withBorder>
                <Group align="center" mb="md">
                  {creationResult.success ? (
                    <IconCircleCheck color={theme.colors.green[6]} />
                  ) : (
                    <IconX color={theme.colors.red[6]} />
                  )}
                  <Text weight={600} size="lg">
                    {creationResult.success ? 'Environment Created Successfully!' : 'Creation Failed'}
                  </Text>
                </Group>

                {creationResult.success ? (
                  <Box>
                    <Text mb="md">
                      Your environment "{creationResult.environment_name}" has been created and is ready in Roblox Studio.
                    </Text>

                    {creationResult.rojo_url && (
                      <Alert color="blue" mb="md">
                        <Text size="sm" weight={600}>
                          Rojo URL: {creationResult.rojo_url}
                        </Text>
                        <Text size="sm">
                          Use this URL in Roblox Studio to sync your environment.
                        </Text>
                      </Alert>
                    )}

                    <Box mt="lg">
                      <Button
                        leftIcon={<IconPlus />}
                        onClick={handleReset}
                      >
                        Create Another Environment
                      </Button>
                    </Box>
                  </Box>
                ) : (
                  <Box>
                    <Text mb="md">
                      {creationResult.error || 'An unknown error occurred during creation.'}
                    </Text>

                    <Group spacing="md">
                      <Button
                        variant="outline"
                        onClick={() => setActiveStep(1)}
                      >
                        Try Again
                      </Button>
                      <Button
                        variant="subtle"
                        onClick={handleReset}
                      >
                        Start Over
                      </Button>
                    </Group>
                  </Box>
                )}
              </Card>
            )}
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Box style={{ maxWidth: 800, margin: '0 auto', padding: theme.spacing.lg }}>
      <Title order={2} mb="sm">
        Create Roblox Environment
      </Title>

      <Text color="dimmed" mb="xl">
        Use natural language to describe your educational environment, and we'll create it in Roblox Studio using Rojo API.
      </Text>

      {error && (
        <Alert color="red" mb="lg" onClose={() => setError(null)} withCloseButton>
          {error}
        </Alert>
      )}

      <Card withBorder>
        <Stepper active={activeStep} orientation="vertical" size="sm">
          <Stepper.Step
            label="Environment Details"
            description="Provide basic information about your environment"
          >
            {renderStepContent(0)}

            <Group mt="xl">
              <Button
                onClick={() => setActiveStep(1)}
                disabled={!formData.name || !formData.description}
              >
                Continue
              </Button>
            </Group>
          </Stepper.Step>

          <Stepper.Step
            label="Preview & Create"
            description="Review your environment and create it"
          >
            {renderStepContent(1)}

            <Group mt="xl" spacing="md">
              <Button
                onClick={handleCreateEnvironment}
                disabled={isCreating || !rojoStatus?.rojo_connected}
                leftIcon={isCreating ? <Loader size={20} /> : <IconPlus />}
              >
                {isCreating ? 'Creating...' : 'Create Environment'}
              </Button>
              <Button
                variant="outline"
                onClick={() => setActiveStep(0)}
              >
                Back
              </Button>
            </Group>
          </Stepper.Step>

          <Stepper.Step
            label="Result"
            description="View creation results and next steps"
          >
            {renderStepContent(2)}

            <Group mt="xl">
              <Button
                variant="outline"
                onClick={handleReset}
              >
                Create New Environment
              </Button>
            </Group>
          </Stepper.Step>
        </Stepper>
      </Card>
    </Box>
  );
};

export default EnvironmentCreator;