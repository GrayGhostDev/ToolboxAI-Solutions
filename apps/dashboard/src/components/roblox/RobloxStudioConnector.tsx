import React, { useState, useEffect, useCallback } from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardActions from '@mui/material/CardActions';
import Grid from '@mui/material/Grid';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import ListItemIcon from '@mui/material/ListItemIcon';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Stepper from '@mui/material/Stepper';
import Step from '@mui/material/Step';
import StepLabel from '@mui/material/StepLabel';
import StepContent from '@mui/material/StepContent';
import CircularProgress from '@mui/material/CircularProgress';
import Tooltip from '@mui/material/Tooltip';
import TextField from '@mui/material/TextField';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormControlLabel from '@mui/material/FormControlLabel';
import {
  CloudUpload,
  CloudDownload,
  PlayArrow,
  Stop,
  Refresh,
  Settings,
  Link,
  LinkOff,
  Security,
  CheckCircle,
  Error as ErrorIcon,
  Warning,
  Info,
  ContentCopy,
  OpenInNew,
  Build,
  Delete
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import api from '../../services/api';
import pusher from '../../services/pusher';

interface RojoProject {
  project_id: string;
  name: string;
  path: string;
  port: number;
  status: 'stopped' | 'starting' | 'running' | 'error';
  created_at: string;
  updated_at: string;
  user_id: string;
}

interface RojoSyncStatus {
  connected: boolean;
  session_id?: string;
  project_name?: string;
  client_count: number;
  last_sync?: string;
  errors: string[];
}

interface OAuthStatus {
  authenticated: boolean;
  roblox_user_id?: string;
  username?: string;
  expires_at?: string;
}

const RobloxStudioConnector: React.FunctionComponent<Record<string, any>> = () => {
  const [projects, setProjects] = useState<RojoProject[]>([]);
  const [selectedProject, setSelectedProject] = useState<RojoProject | null>(null);
  const [syncStatus, setSyncStatus] = useState<RojoSyncStatus | null>(null);
  const [oauthStatus, setOAuthStatus] = useState<OAuthStatus>({ authenticated: false });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rojoInstalled, setRojoInstalled] = useState<boolean | null>(null);
  const [authDialogOpen, setAuthDialogOpen] = useState(false);
  const [connectionDialogOpen, setConnectionDialogOpen] = useState(false);
  const [autoSync, setAutoSync] = useState(true);

  const user = useSelector((state: RootState) => state.auth.user);

  // Check Rojo installation
  const checkRojoInstallation = useCallback(async () => {
    try {
      const response = await api.get('/api/v1/roblox/rojo/check');
      setRojoInstalled(response.data.rojo_installed);
    } catch (err) {
      setRojoInstalled(false);
    }
  }, []);

  // Load user's Rojo projects
  const loadProjects = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/v1/roblox/rojo/projects');
      setProjects(response.data.projects || []);
    } catch (err: any) {
      setError('Failed to load projects');
    } finally {
      setLoading(false);
    }
  }, []);

  // Check OAuth status
  const checkOAuthStatus = useCallback(async () => {
    try {
      // This would check if user has valid Roblox OAuth tokens
      // For now, we'll mock this
      const hasToken = localStorage.getItem('roblox_auth_token');
      if (hasToken) {
        setOAuthStatus({
          authenticated: true,
          roblox_user_id: 'mock_user_id',
          username: 'RobloxUser'
        });
      }
    } catch (err) {
      setOAuthStatus({ authenticated: false });
    }
  }, []);

  // Initiate OAuth2 flow
  const initiateOAuth = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/api/v1/roblox/auth/initiate', {
        additional_scopes: ['universe-messaging-service:publish']
      });

      if (response.data.success) {
        // Open OAuth window
        const authWindow = window.open(
          response.data.authorization_url,
          'roblox-auth',
          'width=600,height=800'
        );

        // Listen for OAuth completion
        const checkAuth = setInterval(() => {
          if (authWindow?.closed) {
            clearInterval(checkAuth);
            checkOAuthStatus();
            setAuthDialogOpen(false);
          }
        }, 1000);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to initiate authentication');
    } finally {
      setLoading(false);
    }
  };

  // Start Rojo server for project
  const startProject = async (projectId: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post(`/api/v1/roblox/rojo/project/${projectId}/start`);

      if (response.data.success) {
        setSyncStatus(response.data.sync_status);

        // Update project status
        setProjects(prev => prev.map(p =>
          p.project_id === projectId ? { ...p, status: 'running' } : p
        ));

        // Show connection instructions
        if (response.data.sync_status.connected) {
          setConnectionDialogOpen(true);
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start project');
    } finally {
      setLoading(false);
    }
  };

  // Stop Rojo server for project
  const stopProject = async (projectId: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post(`/api/v1/roblox/rojo/project/${projectId}/stop`);

      if (response.data.success) {
        setSyncStatus(null);

        // Update project status
        setProjects(prev => prev.map(p =>
          p.project_id === projectId ? { ...p, status: 'stopped' } : p
        ));
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to stop project');
    } finally {
      setLoading(false);
    }
  };

  // Build project to .rbxl file
  const buildProject = async (projectId: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post(`/api/v1/roblox/rojo/project/${projectId}/build`);

      if (response.data.success) {
        // Download the built file
        const link = document.createElement('a');
        link.href = response.data.output_path;
        link.download = `${selectedProject?.name || 'project'}.rbxl`;
        link.click();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to build project');
    } finally {
      setLoading(false);
    }
  };

  // Delete project
  const deleteProject = async (projectId: string) => {
    if (!confirm('Are you sure you want to delete this project?')) return;

    setLoading(true);
    setError(null);

    try {
      const response = await api.delete(`/api/v1/roblox/rojo/project/${projectId}`);

      if (response.data.success) {
        setProjects(prev => prev.filter(p => p.project_id !== projectId));
        setSelectedProject(null);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete project');
    } finally {
      setLoading(false);
    }
  };

  // Check sync status periodically
  useEffect(() => {
    if (selectedProject?.status === 'running' && autoSync) {
      const interval = setInterval(async () => {
        try {
          const response = await api.get(`/api/v1/roblox/rojo/project/${selectedProject.project_id}`);
          if (response.data.sync_status) {
            setSyncStatus(response.data.sync_status);
          }
        } catch (err) {
          // Ignore errors in background sync check
        }
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [selectedProject, autoSync]);

  // Initialize on mount
  useEffect(() => {
    checkRojoInstallation();
    checkOAuthStatus();
    loadProjects();
  }, [checkRojoInstallation, checkOAuthStatus, loadProjects]);

  // Copy to clipboard helper
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <Box sx={{ width: '100%', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Roblox Studio Connector
      </Typography>

      {/* Status Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Settings sx={{ mr: 1 }} />
                <Typography variant="h6">Rojo Status</Typography>
              </Box>
              {rojoInstalled === null ? (
                <CircularProgress size={20} />
              ) : rojoInstalled ? (
                <Chip
                  icon={<CheckCircle />}
                  label="Installed"
                  color="success"
                  size="small"
                />
              ) : (
                <Chip
                  icon={<ErrorIcon />}
                  label="Not Installed"
                  color="error"
                  size="small"
                />
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Security sx={{ mr: 1 }} />
                <Typography variant="h6">Authentication</Typography>
              </Box>
              {oauthStatus.authenticated ? (
                <Box>
                  <Chip
                    icon={<CheckCircle />}
                    label={`Connected as ${oauthStatus.username}`}
                    color="success"
                    size="small"
                  />
                </Box>
              ) : (
                <Button
                  variant="outlined"
                  size="small"
                  onClick={(e: React.MouseEvent) => () => setAuthDialogOpen(true)}
                  startIcon={<Link />}
                >
                  Connect Roblox
                </Button>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                {syncStatus?.connected ? <Link sx={{ mr: 1 }} /> : <LinkOff sx={{ mr: 1 }} />}
                <Typography variant="h6">Sync Status</Typography>
              </Box>
              {syncStatus ? (
                <Box>
                  <Chip
                    icon={syncStatus.connected ? <CheckCircle /> : <ErrorIcon />}
                    label={syncStatus.connected ? 'Connected' : 'Disconnected'}
                    color={syncStatus.connected ? 'success' : 'default'}
                    size="small"
                  />
                  {syncStatus.client_count > 0 && (
                    <Typography variant="caption" sx={{ ml: 1 }}>
                      {syncStatus.client_count} client(s)
                    </Typography>
                  )}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No active sync
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Project List */}
      <Paper elevation={3} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Your Projects</Typography>
          <FormControlLabel
            control={<Switch checked={autoSync} onChange={(e) => setAutoSync(e.target.checked)} />}
            label="Auto-sync"
          />
        </Box>

        {loading && projects.length === 0 ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : projects.length === 0 ? (
          <Alert severity="info">
            No projects found. Create one from the Conversation Flow.
          </Alert>
        ) : (
          <Grid container spacing={2}>
            {projects.map((project) => (
              <Grid item xs={12} md={6} lg={4} key={project.project_id}>
                <Card
                  sx={{
                    cursor: 'pointer',
                    border: selectedProject?.project_id === project.project_id ? 2 : 0,
                    borderColor: 'primary.main'
                  }}
                  onClick={(e: React.MouseEvent) => () => setSelectedProject(project)}
                >
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {project.name}
                    </Typography>
                    <List dense>
                      <ListItem>
                        <ListItemText
                          primary="Port"
                          secondary={project.port}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText
                          primary="Status"
                          secondary={
                            <Chip
                              label={project.status}
                              color={
                                project.status === 'running' ? 'success' :
                                project.status === 'error' ? 'error' : 'default'
                              }
                              size="small"
                            />
                          }
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText
                          primary="Created"
                          secondary={new Date(project.created_at).toLocaleString()}
                        />
                      </ListItem>
                    </List>
                  </CardContent>
                  <CardActions>
                    {project.status === 'stopped' ? (
                      <Button
                        size="small"
                        startIcon={<PlayArrow />}
                        onClick={(e: React.MouseEvent) => (e) => {
                          e.stopPropagation();
                          startProject(project.project_id);
                        }}
                      >
                        Start
                      </Button>
                    ) : project.status === 'running' ? (
                      <Button
                        size="small"
                        startIcon={<Stop />}
                        onClick={(e: React.MouseEvent) => (e) => {
                          e.stopPropagation();
                          stopProject(project.project_id);
                        }}
                      >
                        Stop
                      </Button>
                    ) : null}
                    <Button
                      size="small"
                      startIcon={<Build />}
                      onClick={(e: React.MouseEvent) => (e) => {
                        e.stopPropagation();
                        buildProject(project.project_id);
                      }}
                    >
                      Build
                    </Button>
                    <IconButton
                      size="small"
                      onClick={(e: React.MouseEvent) => (e) => {
                        e.stopPropagation();
                        deleteProject(project.project_id);
                      }}
                    >
                      <Delete />
                    </IconButton>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Paper>

      {/* OAuth Dialog */}
      <Dialog open={authDialogOpen} onClose={() => setAuthDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Connect to Roblox</DialogTitle>
        <DialogContent>
          <Typography variant="body2" paragraph>
            To use all features, you need to authenticate with your Roblox account.
            This will allow you to:
          </Typography>
          <List>
            <ListItem>
              <ListItemIcon><CheckCircle color="primary" /></ListItemIcon>
              <ListItemText primary="Upload assets directly to Roblox" />
            </ListItem>
            <ListItem>
              <ListItemIcon><CheckCircle color="primary" /></ListItemIcon>
              <ListItemText primary="Publish places and games" />
            </ListItem>
            <ListItem>
              <ListItemIcon><CheckCircle color="primary" /></ListItemIcon>
              <ListItemText primary="Access DataStore and messaging services" />
            </ListItem>
          </List>
          <Alert severity="info" sx={{ mt: 2 }}>
            You will be redirected to Roblox to authorize the connection.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={(e: React.MouseEvent) => () => setAuthDialogOpen(false)}>Cancel</Button>
          <Button onClick={(e: React.MouseEvent) => initiateOAuth} variant="contained" disabled={loading}>
            {loading ? <CircularProgress size={24} /> : 'Connect'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Connection Instructions Dialog */}
      <Dialog open={connectionDialogOpen} onClose={() => setConnectionDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Connect Roblox Studio</DialogTitle>
        <DialogContent>
          <Stepper orientation="vertical" activeStep={-1}>
            <Step active>
              <StepLabel>Open Roblox Studio</StepLabel>
              <StepContent>
                <Typography variant="body2">
                  Launch Roblox Studio and open a new or existing place.
                </Typography>
              </StepContent>
            </Step>
            <Step active>
              <StepLabel>Install Rojo Plugin</StepLabel>
              <StepContent>
                <Typography variant="body2">
                  If not installed, get the Rojo plugin from the Roblox Studio marketplace.
                </Typography>
                <Button
                  size="small"
                  startIcon={<OpenInNew />}
                  href="https://www.roblox.com/library/13916111412/Rojo"
                  target="_blank"
                  sx={{ mt: 1 }}
                >
                  Get Rojo Plugin
                </Button>
              </StepContent>
            </Step>
            <Step active>
              <StepLabel>Connect to Server</StepLabel>
              <StepContent>
                <Typography variant="body2" paragraph>
                  In the Rojo plugin panel, click "Connect" and enter this URL:
                </Typography>
                <Paper sx={{ p: 2, bgcolor: 'grey.100' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography variant="body1" fontFamily="monospace">
                      http://localhost:{selectedProject?.port || '34872'}
                    </Typography>
                    <IconButton
                      size="small"
                      onClick={(e: React.MouseEvent) => () => copyToClipboard(`http://localhost:${selectedProject?.port || '34872'}`)}
                    >
                      <ContentCopy />
                    </IconButton>
                  </Box>
                </Paper>
              </StepContent>
            </Step>
            <Step active>
              <StepLabel>Start Syncing</StepLabel>
              <StepContent>
                <Typography variant="body2">
                  Once connected, Rojo will sync your educational content to Roblox Studio in real-time.
                </Typography>
              </StepContent>
            </Step>
          </Stepper>
        </DialogContent>
        <DialogActions>
          <Button onClick={(e: React.MouseEvent) => () => setConnectionDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
    </Box>
  );
};

export default RobloxStudioConnector;