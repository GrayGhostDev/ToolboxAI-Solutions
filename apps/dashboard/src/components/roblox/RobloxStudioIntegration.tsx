/**
 * RobloxStudioIntegration Component
 * 
 * Main integration component that combines the AI chat interface with
 * Roblox Studio plugin communication and environment management.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Button,
  Alert,
  Chip,
  Stack,
  Card,
  CardContent,
  CardActions,
  IconButton,
  Tooltip,
  LinearProgress,
  Divider,
  useTheme
} from '@mui/material';
import {
  PlayArrow,
  Download,
  Share,
  Refresh,
  Settings,
  Code,
  Visibility,
  CloudUpload,
  CheckCircle,
  Error as ErrorIcon,
  Warning
} from '@mui/icons-material';

import { RobloxAIChat } from './RobloxAIChat';
import { useAppSelector } from '../../store';
import { api } from '../../services/api';
import { pusherService } from '../../services/pusher';
import { WebSocketMessageType } from '../../types/websocket';

interface PluginStatus {
  connected: boolean;
  version?: string;
  studioVersion?: string;
  lastHeartbeat?: string;
}

interface GeneratedEnvironment {
  id: string;
  name: string;
  status: 'generating' | 'ready' | 'error';
  progress?: number;
  previewUrl?: string;
  downloadUrl?: string;
  deployUrl?: string;
  error?: string;
  metadata?: {
    theme: string;
    mapType: string;
    learningObjectives: string[];
    difficulty: string;
  };
}

export const RobloxStudioIntegration: React.FC = () => {
  const theme = useTheme();
  const currentUser = useAppSelector(state => state.user);
  
  // State
  const [pluginStatus, setPluginStatus] = useState<PluginStatus>({ connected: false });
  const [environments, setEnvironments] = useState<GeneratedEnvironment[]>([]);
  const [isCheckingPlugin, setIsCheckingPlugin] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedEnvironment, setSelectedEnvironment] = useState<string | null>(null);
  
  // Check plugin status
  const checkPluginStatus = useCallback(async () => {
    setIsCheckingPlugin(true);
    try {
      const status = await api.checkRobloxPluginStatus();
      setPluginStatus(status);
      setError(null);
    } catch (err) {
      console.error('Failed to check plugin status:', err);
      setPluginStatus({ connected: false });
      setError('Unable to connect to Roblox Studio plugin. Please ensure the plugin is installed and Studio is running.');
    } finally {
      setIsCheckingPlugin(false);
    }
  }, []);
  
  // Load environments
  const loadEnvironments = useCallback(async () => {
    try {
      const worlds = await api.listRobloxWorlds();
      const mappedEnvironments: GeneratedEnvironment[] = worlds.map(world => ({
        id: world.id,
        name: world.name || 'Untitled Environment',
        status: world.status === 'published' ? 'ready' : world.status === 'draft' ? 'generating' : 'ready',
        previewUrl: world.previewUrl,
        downloadUrl: world.downloadUrl,
        metadata: {
          theme: world.theme || 'Unknown',
          mapType: world.mapType || 'classroom',
          learningObjectives: world.learningObjectives || [],
          difficulty: world.difficulty || 'medium'
        }
      }));
      setEnvironments(mappedEnvironments);
    } catch (err) {
      console.error('Failed to load environments:', err);
    }
  }, []);
  
  // Initialize
  useEffect(() => {
    checkPluginStatus();
    loadEnvironments();
    
    // Set up periodic plugin status checks
    const interval = setInterval(checkPluginStatus, 30000); // Check every 30 seconds
    
    return () => clearInterval(interval);
  }, [checkPluginStatus, loadEnvironments]);
  
  // Handle environment generation completion
  useEffect(() => {
    const handleEnvironmentReady = (data: any) => {
      const { environmentId, previewUrl, downloadUrl } = data;
      
      setEnvironments(prev => prev.map(env => 
        env.id === environmentId 
          ? { ...env, status: 'ready', previewUrl, downloadUrl }
          : env
      ));
    };
    
    const handleEnvironmentError = (data: any) => {
      const { requestId, error } = data;
      
      setEnvironments(prev => prev.map(env => 
        env.id === requestId 
          ? { ...env, status: 'error', error }
          : env
      ));
    };
    
    // Subscribe to environment events
    const subscriptionId = pusherService.subscribe(
      'roblox-environments',
      (message: any) => {
        switch (message.type) {
          case WebSocketMessageType.ROBLOX_ENV_READY:
            handleEnvironmentReady(message.payload);
            break;
          case WebSocketMessageType.ROBLOX_ENV_ERROR:
            handleEnvironmentError(message.payload);
            break;
        }
      }
    );
    
    return () => {
      pusherService.unsubscribe(subscriptionId);
    };
  }, []);
  
  // Deploy to Roblox Studio
  const deployToStudio = useCallback(async (environmentId: string) => {
    if (!pluginStatus.connected) {
      setError('Roblox Studio plugin is not connected. Please ensure Studio is running and the plugin is installed.');
      return;
    }
    
    try {
      await api.deployToRoblox(environmentId);
      
      // Show success message
      setError(null);
      
      // Optionally refresh environments
      loadEnvironments();
    } catch (err) {
      console.error('Failed to deploy to Studio:', err);
      setError('Failed to deploy environment to Roblox Studio. Please try again.');
    }
  }, [pluginStatus.connected, loadEnvironments]);
  
  // Download environment
  const downloadEnvironment = useCallback(async (environmentId: string) => {
    try {
      const response = await api.exportRobloxEnvironment(environmentId);
      
      // Create download link
      const blob = new Blob([response], { type: 'application/octet-stream' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `roblox-environment-${environmentId}.rbxl`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download environment:', err);
      setError('Failed to download environment. Please try again.');
    }
  }, []);
  
  // Share environment
  const shareEnvironment = useCallback(async (environment: GeneratedEnvironment) => {
    if (navigator.share && environment.previewUrl) {
      try {
        await navigator.share({
          title: environment.name,
          text: `Check out this Roblox educational environment: ${environment.name}`,
          url: environment.previewUrl
        });
      } catch (err) {
        // Fallback to clipboard
        navigator.clipboard?.writeText(environment.previewUrl);
      }
    } else if (environment.previewUrl) {
      // Fallback to clipboard
      navigator.clipboard?.writeText(environment.previewUrl);
      // Could show a toast notification here
    }
  }, []);
  
  // Install plugin
  const installPlugin = useCallback(async () => {
    try {
      const installInfo = await api.getRobloxPluginInstallInfo();
      
      if (installInfo.installUrl) {
        window.open(installInfo.installUrl, '_blank');
      }
    } catch (err) {
      console.error('Failed to get plugin install info:', err);
      setError('Failed to get plugin installation information.');
    }
  }, []);

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper elevation={1} sx={{ p: 2, mb: 2 }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography variant="h5" gutterBottom>
              Roblox Studio Integration
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Create, manage, and deploy educational Roblox environments
            </Typography>
          </Box>
          
          {/* Plugin Status */}
          <Stack direction="row" alignItems="center" spacing={2}>
            <Chip
              icon={pluginStatus.connected ? <CheckCircle /> : <ErrorIcon />}
              label={pluginStatus.connected ? 'Plugin Connected' : 'Plugin Disconnected'}
              color={pluginStatus.connected ? 'success' : 'error'}
              variant="outlined"
            />
            
            <Button
              variant="outlined"
              onClick={checkPluginStatus}
              disabled={isCheckingPlugin}
              startIcon={<Refresh />}
            >
              {isCheckingPlugin ? 'Checking...' : 'Refresh'}
            </Button>
            
            {!pluginStatus.connected && (
              <Button
                variant="contained"
                onClick={installPlugin}
                startIcon={<CloudUpload />}
              >
                Install Plugin
              </Button>
            )}
          </Stack>
        </Stack>
        
        {/* Plugin Status Details */}
        {pluginStatus.connected && pluginStatus.version && (
          <Box sx={{ mt: 1 }}>
            <Typography variant="caption" color="text.secondary">
              Plugin Version: {pluginStatus.version}
              {pluginStatus.studioVersion && ` | Studio Version: ${pluginStatus.studioVersion}`}
            </Typography>
          </Box>
        )}
      </Paper>
      
      {/* Error Alert */}
      {error && (
        <Alert 
          severity="error" 
          onClose={() => setError(null)}
          sx={{ mb: 2 }}
        >
          {error}
        </Alert>
      )}
      
      {/* Main Content */}
      <Grid container spacing={2} sx={{ flex: 1 }}>
        {/* AI Chat Interface */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ height: '100%' }}>
            <RobloxAIChat />
          </Paper>
        </Grid>
        
        {/* Environment Management */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}` }}>
              <Typography variant="h6">Generated Environments</Typography>
              <Typography variant="body2" color="text.secondary">
                Manage and deploy your AI-generated Roblox worlds
              </Typography>
            </Box>
            
            <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
              {environments.length === 0 ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body1" color="text.secondary" gutterBottom>
                    No environments generated yet
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Use the AI chat to create your first Roblox environment
                  </Typography>
                </Box>
              ) : (
                <Stack spacing={2}>
                  {environments.map((environment) => (
                    <Card 
                      key={environment.id}
                      variant="outlined"
                      sx={{
                        cursor: 'pointer',
                        '&:hover': { bgcolor: 'action.hover' },
                        border: selectedEnvironment === environment.id ? 2 : 1,
                        borderColor: selectedEnvironment === environment.id 
                          ? theme.palette.primary.main 
                          : theme.palette.divider
                      }}
                      onClick={() => setSelectedEnvironment(environment.id)}
                    >
                      <CardContent>
                        <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
                          <Typography variant="h6" noWrap>
                            {environment.name}
                          </Typography>
                          
                          <Chip
                            size="small"
                            label={environment.status}
                            color={
                              environment.status === 'ready' ? 'success' :
                              environment.status === 'error' ? 'error' : 'warning'
                            }
                            icon={
                              environment.status === 'ready' ? <CheckCircle /> :
                              environment.status === 'error' ? <ErrorIcon /> : <Warning />
                            }
                          />
                        </Stack>
                        
                        {environment.metadata && (
                          <Box sx={{ mb: 2 }}>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                              Theme: {environment.metadata.theme} | Type: {environment.metadata.mapType}
                            </Typography>
                            {environment.metadata.learningObjectives.length > 0 && (
                              <Typography variant="body2" color="text.secondary">
                                Objectives: {environment.metadata.learningObjectives.join(', ')}
                              </Typography>
                            )}
                          </Box>
                        )}
                        
                        {environment.status === 'generating' && environment.progress !== undefined && (
                          <Box sx={{ mb: 2 }}>
                            <LinearProgress 
                              variant="determinate" 
                              value={environment.progress} 
                              sx={{ mb: 1 }}
                            />
                            <Typography variant="caption" color="text.secondary">
                              Generating... {environment.progress}%
                            </Typography>
                          </Box>
                        )}
                        
                        {environment.status === 'error' && environment.error && (
                          <Alert severity="error" sx={{ mb: 2 }}>
                            {environment.error}
                          </Alert>
                        )}
                      </CardContent>
                      
                      {environment.status === 'ready' && (
                        <CardActions>
                          <Button
                            size="small"
                            startIcon={<PlayArrow />}
                            onClick={(e) => {
                              e.stopPropagation();
                              deployToStudio(environment.id);
                            }}
                            disabled={!pluginStatus.connected}
                          >
                            Deploy to Studio
                          </Button>
                          
                          <Button
                            size="small"
                            startIcon={<Download />}
                            onClick={(e) => {
                              e.stopPropagation();
                              downloadEnvironment(environment.id);
                            }}
                          >
                            Download
                          </Button>
                          
                          {environment.previewUrl && (
                            <Button
                              size="small"
                              startIcon={<Visibility />}
                              onClick={(e) => {
                                e.stopPropagation();
                                window.open(environment.previewUrl, '_blank');
                              }}
                            >
                              Preview
                            </Button>
                          )}
                          
                          <Tooltip title="Share">
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation();
                                shareEnvironment(environment);
                              }}
                            >
                              <Share />
                            </IconButton>
                          </Tooltip>
                        </CardActions>
                      )}
                    </Card>
                  ))}
                </Stack>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default RobloxStudioIntegration;