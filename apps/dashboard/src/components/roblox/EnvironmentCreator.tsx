/**
 * Roblox Environment Creator Component
 * Allows users to create Roblox environments from natural language descriptions
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Chip,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Create as CreateIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Terrain as TerrainIcon,
  Home as HomeIcon,
  Lightbulb as LightbulbIcon,
  Computer as ComputerIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';

import {
  robloxEnvironmentService,
  EnvironmentCreationRequest,
  EnvironmentCreationResponse,
  EnvironmentStatusResponse,
  RojoConnectionResponse
} from '../../services/robloxEnvironment';

interface EnvironmentCreatorProps {
  onEnvironmentCreated?: (environment: EnvironmentCreationResponse) => void;
}

const EnvironmentCreator: React.FC<EnvironmentCreatorProps> = ({ onEnvironmentCreated }) => {
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
        name: formData.name || "Preview Environment",
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
          name: formData.name || "Preview Environment",
          visualization: {
            terrain: components.terrain.map((item: string) => ({
              type: item,
              position: { x: Math.random() * 100, y: 0, z: Math.random() * 100 },
              size: { x: 20, y: 10, z: 20 },
              color: "#4CAF50"
            })),
            buildings: components.buildings.map((item: string, index: number) => ({
              type: item,
              position: { x: index * 30, y: 0, z: 0 },
              size: { x: 25, y: 15, z: 25 },
              color: "#" + Math.floor(Math.random()*16777215).toString(16)
            })),
            objects: components.objects.map((item: string, index: number) => ({
              type: item,
              position: { x: Math.random() * 50, y: 0, z: Math.random() * 50 },
              size: { x: 5, y: 5, z: 5 },
              color: "#" + Math.floor(Math.random()*16777215).toString(16)
            })),
            lighting: {
              type: components.lighting,
              brightness: components.lighting === 'Bright/Sunny' ? 1.0 : 
                         components.lighting === 'Dark/Night' ? 0.3 : 0.7,
              color: components.lighting === 'Bright/Sunny' ? "#FFE4B5" :
                     components.lighting === 'Dark/Night' ? "#1A1A2E" : "#FFFFFF"
            },
            effects: components.effects.map((effect: string) => ({
              type: effect,
              intensity: 0.5,
              active: true
            }))
          }
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
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | any
  ) => {
    const value = event.target.value;
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

  const steps = [
    {
      label: 'Environment Details',
      description: 'Provide basic information about your environment'
    },
    {
      label: 'Preview & Create',
      description: 'Review your environment and create it'
    },
    {
      label: 'Result',
      description: 'View creation results and next steps'
    }
  ];

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Box sx={{ p: 2 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Environment Name"
                  value={formData.name}
                  onChange={handleInputChange('name')}
                  placeholder="e.g., Math Adventure World"
                  helperText="Choose a descriptive name for your environment"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Grade Level</InputLabel>
                  <Select
                    value={formData.grade_level}
                    onChange={handleInputChange('grade_level')}
                    label="Grade Level"
                  >
                    <MenuItem value="">Any Grade</MenuItem>
                    <MenuItem value="K-2">K-2 (Elementary)</MenuItem>
                    <MenuItem value="3-5">3-5 (Elementary)</MenuItem>
                    <MenuItem value="6-8">6-8 (Middle School)</MenuItem>
                    <MenuItem value="9-12">9-12 (High School)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Subject</InputLabel>
                  <Select
                    value={formData.subject}
                    onChange={handleInputChange('subject')}
                    label="Subject"
                  >
                    <MenuItem value="">Any Subject</MenuItem>
                    <MenuItem value="math">Mathematics</MenuItem>
                    <MenuItem value="science">Science</MenuItem>
                    <MenuItem value="history">History</MenuItem>
                    <MenuItem value="english">English/Language Arts</MenuItem>
                    <MenuItem value="art">Art</MenuItem>
                    <MenuItem value="music">Music</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Maximum Players"
                  type="number"
                  value={formData.max_players}
                  onChange={handleInputChange('max_players')}
                  inputProps={{ min: 1, max: 100 }}
                  helperText="Maximum number of students who can join"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label="Environment Description"
                  value={formData.description}
                  onChange={handleInputChange('description')}
                  placeholder="Describe your educational environment in natural language. For example: 'Create a math classroom with interactive whiteboards, student desks, and a cozy reading corner with books about numbers and shapes.'"
                  helperText="Be as detailed as possible. Include buildings, objects, terrain, lighting, and any special features."
                />
              </Grid>
            </Grid>

            {/* Environment Preview */}
            {environmentPreview && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Environment Preview
                </Typography>
                
                {isGeneratingPreview ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2 }}>
                    <CircularProgress size={20} />
                    <Typography variant="body2">Generating environment preview...</Typography>
                  </Box>
                ) : (
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle1" gutterBottom>
                        {environmentPreview.name}
                      </Typography>
                      
                      {/* 3D Environment Visualization */}
                      <Box sx={{ 
                        height: 300, 
                        backgroundColor: '#f5f5f5', 
                        borderRadius: 1, 
                        position: 'relative',
                        overflow: 'hidden',
                        border: '1px solid #e0e0e0'
                      }}>
                        {/* Terrain */}
                        {environmentPreview.structure.terrain.map((terrain: any, index: number) => (
                          <Box
                            key={`terrain-${index}`}
                            sx={{
                              position: 'absolute',
                              left: `${terrain.position.x}%`,
                              top: `${terrain.position.z}%`,
                              width: `${terrain.size.x}px`,
                              height: `${terrain.size.z}px`,
                              backgroundColor: '#4CAF50',
                              borderRadius: '50%',
                              opacity: 0.7,
                              border: '2px solid #2E7D32'
                            }}
                            title={terrain.type}
                          />
                        ))}
                        
                        {/* Buildings */}
                        {environmentPreview.structure.buildings.map((building: any, index: number) => (
                          <Box
                            key={`building-${index}`}
                            sx={{
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
                              fontWeight: 'bold',
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
                            sx={{
                              position: 'absolute',
                              left: `${object.position.x}%`,
                              top: `${object.position.z}%`,
                              width: `${object.size.x}px`,
                              height: `${object.size.z}px`,
                              backgroundColor: object.color,
                              border: '1px solid #666',
                              borderRadius: '2px',
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
                          sx={{
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
                        
                        {/* Effects */}
                        {environmentPreview.effects.map((effect: any, index: number) => (
                          <Box
                            key={`effect-${index}`}
                            sx={{
                              position: 'absolute',
                              top: 0,
                              left: 0,
                              right: 0,
                              bottom: 0,
                              background: effect.type === 'Rain/Storm' ? 
                                'repeating-linear-gradient(45deg, transparent, transparent 2px, rgba(0,100,255,0.1) 2px, rgba(0,100,255,0.1) 4px)' :
                                effect.type === 'Snow' ?
                                'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.3) 2px, rgba(255,255,255,0.3) 4px)' :
                                'none',
                              pointerEvents: 'none',
                              opacity: effect.intensity
                            }}
                          />
                        ))}
                        
                        {/* Legend */}
                        <Box sx={{ 
                          position: 'absolute', 
                          top: 8, 
                          left: 8, 
                          backgroundColor: 'rgba(255,255,255,0.9)', 
                          padding: 1, 
                          borderRadius: 1,
                          fontSize: '10px'
                        }}>
                          <Typography variant="caption" display="block">
                            🟢 Terrain &nbsp; 🏠 Buildings &nbsp; 📦 Objects
                          </Typography>
                        </Box>
                      </Box>
                      
                      {/* Environment Details */}
                      <Box sx={{ mt: 2 }}>
                        <Grid container spacing={2}>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              <strong>Lighting:</strong> {environmentPreview.lighting.type}
                            </Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              <strong>Effects:</strong> {environmentPreview.effects.length > 0 ? 
                                environmentPreview.effects.map((e: any) => e.type).join(', ') : 'None'}
                            </Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              <strong>Terrain:</strong> {environmentPreview.structure.terrain.length} areas
                            </Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="body2" color="text.secondary">
                              <strong>Buildings:</strong> {environmentPreview.structure.buildings.length} structures
                            </Typography>
                          </Grid>
                        </Grid>
                      </Box>
                    </CardContent>
                  </Card>
                )}
              </Box>
            )}
          </Box>
        );

      case 1:
        return (
          <Box sx={{ p: 2 }}>
            {/* Rojo Status */}
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Typography variant="h6">Roblox Studio Connection</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {isCheckingRojo ? (
                      <CircularProgress size={20} />
                    ) : (
                      <IconButton onClick={checkRojoConnection} size="small">
                        <RefreshIcon />
                      </IconButton>
                    )}
                  </Box>
                </Box>

                {rojoStatus && (
                  <Box sx={{ mt: 2 }}>
                    <Chip
                      icon={rojoStatus.rojo_connected ? <CheckCircleIcon /> : <ErrorIcon />}
                      label={rojoStatus.rojo_connected ? 'Connected to Roblox Studio' : 'Not Connected'}
                      color={rojoStatus.rojo_connected ? 'success' : 'error'}
                      sx={{ mb: 1 }}
                    />
                    {rojoStatus.rojo_url && (
                      <Typography variant="body2" color="text.secondary">
                        Rojo URL: {rojoStatus.rojo_url}
                      </Typography>
                    )}
                  </Box>
                )}
              </CardContent>
            </Card>

            {/* Environment Preview */}
            {previewComponents && (
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Environment Preview
                  </Typography>

                  <Grid container spacing={2}>
                    {previewComponents.terrain.length > 0 && (
                      <Grid item xs={12} sm={6} md={3}>
                        <Paper sx={{ p: 2, textAlign: 'center' }}>
                          <TerrainIcon color="primary" sx={{ mb: 1 }} />
                          <Typography variant="subtitle2">Terrain</Typography>
                          {previewComponents.terrain.map((item: string, index: number) => (
                            <Chip key={index} label={item} size="small" sx={{ m: 0.5 }} />
                          ))}
                        </Paper>
                      </Grid>
                    )}

                    {previewComponents.buildings.length > 0 && (
                      <Grid item xs={12} sm={6} md={3}>
                        <Paper sx={{ p: 2, textAlign: 'center' }}>
                          <HomeIcon color="primary" sx={{ mb: 1 }} />
                          <Typography variant="subtitle2">Buildings</Typography>
                          {previewComponents.buildings.map((item: string, index: number) => (
                            <Chip key={index} label={item} size="small" sx={{ m: 0.5 }} />
                          ))}
                        </Paper>
                      </Grid>
                    )}

                    {previewComponents.objects.length > 0 && (
                      <Grid item xs={12} sm={6} md={3}>
                        <Paper sx={{ p: 2, textAlign: 'center' }}>
                          <ComputerIcon color="primary" sx={{ mb: 1 }} />
                          <Typography variant="subtitle2">Objects</Typography>
                          {previewComponents.objects.map((item: string, index: number) => (
                            <Chip key={index} label={item} size="small" sx={{ m: 0.5 }} />
                          ))}
                        </Paper>
                      </Grid>
                    )}

                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <LightbulbIcon color="primary" sx={{ mb: 1 }} />
                        <Typography variant="subtitle2">Lighting</Typography>
                        <Chip label={previewComponents.lighting} size="small" sx={{ m: 0.5 }} />
                      </Paper>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            )}

            {/* Environment Summary */}
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Environment Summary
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText primary="Name" secondary={formData.name} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Grade Level" secondary={formData.grade_level || 'Any'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Subject" secondary={formData.subject || 'Any'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Max Players" secondary={formData.max_players} />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Box>
        );

      case 2:
        return (
          <Box sx={{ p: 2 }}>
            {creationResult && (
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    {creationResult.success ? (
                      <CheckCircleIcon color="success" sx={{ mr: 1 }} />
                    ) : (
                      <ErrorIcon color="error" sx={{ mr: 1 }} />
                    )}
                    <Typography variant="h6">
                      {creationResult.success ? 'Environment Created Successfully!' : 'Creation Failed'}
                    </Typography>
                  </Box>

                  {creationResult.success ? (
                    <Box>
                      <Typography variant="body1" paragraph>
                        Your environment "{creationResult.environment_name}" has been created and is ready in Roblox Studio.
                      </Typography>

                      {creationResult.rojo_url && (
                        <Alert severity="info" sx={{ mb: 2 }}>
                          <Typography variant="body2">
                            <strong>Rojo URL:</strong> {creationResult.rojo_url}
                          </Typography>
                          <Typography variant="body2">
                            Use this URL in Roblox Studio to sync your environment.
                          </Typography>
                        </Alert>
                      )}

                      <Box sx={{ mt: 2 }}>
                        <Button
                          variant="contained"
                          startIcon={<CreateIcon />}
                          onClick={handleReset}
                          sx={{ mr: 2 }}
                        >
                          Create Another Environment
                        </Button>
                      </Box>
                    </Box>
                  ) : (
                    <Box>
                      <Typography variant="body1" paragraph>
                        {creationResult.error || 'An unknown error occurred during creation.'}
                      </Typography>

                      <Button
                        variant="outlined"
                        onClick={() => setActiveStep(1)}
                        sx={{ mr: 2 }}
                      >
                        Try Again
                      </Button>
                      <Button
                        variant="text"
                        onClick={handleReset}
                      >
                        Start Over
                      </Button>
                    </Box>
                  )}
                </CardContent>
              </Card>
            )}
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Create Roblox Environment
      </Typography>

      <Typography variant="body1" color="text.secondary" paragraph>
        Use natural language to describe your educational environment, and we'll create it in Roblox Studio using Rojo API.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Card>
        <CardContent>
          <Stepper activeStep={activeStep} orientation="vertical">
            {steps.map((step, index) => (
              <Step key={step.label}>
                <StepLabel>
                  <Typography variant="h6">{step.label}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {step.description}
                  </Typography>
                </StepLabel>
                <StepContent>
                  {renderStepContent(index)}

                  <Box sx={{ mt: 2 }}>
                    {index === 0 && (
                      <Button
                        variant="contained"
                        onClick={() => setActiveStep(1)}
                        disabled={!formData.name || !formData.description}
                      >
                        Continue
                      </Button>
                    )}

                    {index === 1 && (
                      <Box sx={{ display: 'flex', gap: 2 }}>
                        <Button
                          variant="contained"
                          onClick={handleCreateEnvironment}
                          disabled={isCreating || !rojoStatus?.rojo_connected}
                          startIcon={isCreating ? <CircularProgress size={20} /> : <CreateIcon />}
                        >
                          {isCreating ? 'Creating...' : 'Create Environment'}
                        </Button>
                        <Button
                          variant="outlined"
                          onClick={() => setActiveStep(0)}
                        >
                          Back
                        </Button>
                      </Box>
                    )}

                    {index === 2 && (
                      <Button
                        variant="outlined"
                        onClick={handleReset}
                      >
                        Create New Environment
                      </Button>
                    )}
                  </Box>
                </StepContent>
              </Step>
            ))}
          </Stepper>
        </CardContent>
      </Card>
    </Box>
  );
};

export default EnvironmentCreator;
