/**
 * TeacherRobloxDashboard Page
 *
 * Main dashboard for teachers to manage Roblox educational content and sessions
 * Combines all Roblox components into a unified interface
 */

import React, { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Badge from '@mui/material/Badge';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import { useTheme, alpha } from '@mui/material/styles';
import {
  Dashboard,
  Psychology,
  Groups,
  Games,
  Quiz,
  Terrain,
  Settings,
  Notifications,
  Help,
  Refresh,
  Circle,
  AutoAwesome
} from '@mui/icons-material';
import { useAppSelector, useAppDispatch } from '../../store';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import {
  selectPluginStatus,
  selectContentGeneration,
  selectSessions,
  selectStudentProgress,
  setPluginStatus
} from '../../store/slices/robloxSlice';

// Import Roblox components
import { RobloxControlPanel } from '../roblox/RobloxControlPanel';
import { ContentGenerationMonitor } from '../roblox/ContentGenerationMonitor';
import { StudentProgressDashboard } from '../roblox/StudentProgressDashboard';
import { RobloxSessionManager } from '../roblox/RobloxSessionManager';
import { QuizResultsAnalytics } from '../roblox/QuizResultsAnalytics';
import { RobloxEnvironmentPreview } from '../roblox/RobloxEnvironmentPreview';
import { RobloxAIAssistant } from '../roblox/RobloxAIAssistant';
import { AIAssistantTest } from '../test/AIAssistantTest';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <Box
      role="tabpanel"
      hidden={value !== index}
      id={`roblox-tabpanel-${index}`}
      aria-labelledby={`roblox-tab-${index}`}
      {...other}
      sx={{ height: '100%' }}
    >
      {value === index && (
        <Box sx={{ height: '100%', pt: 2 }}>
          {children}
        </Box>
      )}
    </Box>
  );
}

export default function TeacherRobloxDashboard() {
  const theme = useTheme();
  const dispatch = useAppDispatch();
  const { isConnected } = useWebSocketContext();

  const [activeTab, setActiveTab] = useState(0);
  const [showHelp, setShowHelp] = useState(false);

  // Redux state
  const pluginStatus = useAppSelector(selectPluginStatus);
  const contentGeneration = useAppSelector(selectContentGeneration);
  const sessions = useAppSelector(selectSessions);
  const studentProgress = useAppSelector(selectStudentProgress);

  // Calculate statistics
  const stats = {
    pluginConnected: pluginStatus.connected,
    activeGenerations: contentGeneration.isGenerating ? 1 : 0,
    activeSessions: sessions.active.filter(s => s.status === 'active').length,
    onlineStudents: studentProgress.students.filter(s => s.status === 'online' || s.status === 'active').length,
    totalStudents: studentProgress.students.length
  };

  // Check plugin connection periodically
  useEffect(() => {
    const checkPluginStatus = () => {
      // This would normally make an API call to check plugin status
      // For now, we'll simulate it
      const mockStatus = {
        connected: Math.random() > 0.3, // 70% chance of being connected
        version: '1.0.0',
        lastHeartbeat: new Date().toISOString(),
        capabilities: ['content-generation', 'real-time-sync', 'quiz-management']
      };
      dispatch(setPluginStatus(mockStatus));
    };

    checkPluginStatus();
    const interval = setInterval(checkPluginStatus, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, [dispatch]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleRefresh = () => {
    // Trigger refresh for current tab
    window.location.reload(); // Simple refresh for now
  };

  return (
    <Box sx={{ height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Games color="primary" sx={{ fontSize: 40 }} />
              <Box>
                <Typography variant="h4">Roblox Studio Integration</Typography>
                <Typography variant="body2" color="text.secondary">
                  Manage educational content and monitor student progress in real-time
                </Typography>
              </Box>
            </Box>
          </Grid>

          <Grid item xs={12} md={6}>
            <Stack direction="row" spacing={2} justifyContent="flex-end">
              {/* Status Indicators */}
              <Chip
                icon={<Circle sx={{ fontSize: 12 }} />}
                label={isConnected ? 'Dashboard Connected' : 'Dashboard Offline'}
                color={isConnected ? 'success' : 'error'}
                size="small"
              />
              <Chip
                icon={<Circle sx={{ fontSize: 12 }} />}
                label={stats.pluginConnected ? 'Plugin Connected' : 'Plugin Offline'}
                color={stats.pluginConnected ? 'success' : 'error'}
                size="small"
              />

              {/* Actions */}
              <IconButton onClick={(e: React.MouseEvent) => handleRefresh} size="small">
                <Refresh />
              </IconButton>
              <IconButton onClick={(e: React.MouseEvent) => () => setShowHelp(!showHelp)} size="small">
                <Help />
              </IconButton>
            </Stack>
          </Grid>
        </Grid>

        {/* Quick Stats */}
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={6} sm={3}>
            <Card sx={{ bgcolor: alpha(theme.palette.primary.main, 0.1) }}>
              <CardContent sx={{ py: 1 }}>
                <Stack direction="row" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography variant="h5">{stats.activeGenerations}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Active Generations
                    </Typography>
                  </Box>
                  <Psychology color="primary" />
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={6} sm={3}>
            <Card sx={{ bgcolor: alpha(theme.palette.success.main, 0.1) }}>
              <CardContent sx={{ py: 1 }}>
                <Stack direction="row" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography variant="h5">{stats.activeSessions}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Active Sessions
                    </Typography>
                  </Box>
                  <Games color="success" />
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={6} sm={3}>
            <Card sx={{ bgcolor: alpha(theme.palette.info.main, 0.1) }}>
              <CardContent sx={{ py: 1 }}>
                <Stack direction="row" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography variant="h5">{stats.onlineStudents}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Online Students
                    </Typography>
                  </Box>
                  <Groups color="info" />
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={6} sm={3}>
            <Card sx={{ bgcolor: alpha(theme.palette.warning.main, 0.1) }}>
              <CardContent sx={{ py: 1 }}>
                <Stack direction="row" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography variant="h5">{stats.totalStudents}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Total Students
                    </Typography>
                  </Box>
                  <Badge badgeContent={stats.onlineStudents} color="success">
                    <Groups color="warning" />
                  </Badge>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Help Alert */}
      {showHelp && (
        <Alert
          severity="info"
          onClose={() => setShowHelp(false)}
          sx={{ mb: 2 }}
        >
          <AlertTitle>Roblox Studio Integration Help</AlertTitle>
          <Typography variant="body2">
            • <strong>AI Assistant:</strong> Chat with AI to create educational content effortlessly<br />
            • <strong>Control Panel:</strong> Connect to Roblox Studio plugin and generate content<br />
            • <strong>Content Monitor:</strong> Track AI agent progress during content generation<br />
            • <strong>Student Progress:</strong> Monitor real-time student activity and performance<br />
            • <strong>Session Manager:</strong> Create and manage educational game sessions<br />
            • <strong>Quiz Analytics:</strong> Analyze quiz results and identify learning gaps<br />
            • <strong>Environment Preview:</strong> Preview 3D environments before deployment
          </Typography>
        </Alert>
      )}

      {/* Tab Navigation */}
      <Paper sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          aria-label="Roblox dashboard tabs"
        >
          <Tab
            icon={<AutoAwesome />}
            label="AI Assistant"
            id="roblox-tab-0"
            aria-controls="roblox-tabpanel-0"
          />
          <Tab
            icon={<Dashboard />}
            label="Control Panel"
            id="roblox-tab-1"
            aria-controls="roblox-tabpanel-1"
          />
          <Tab
            icon={<Psychology />}
            label="Content Monitor"
            id="roblox-tab-2"
            aria-controls="roblox-tabpanel-2"
          />
          <Tab
            icon={<Groups />}
            label="Student Progress"
            id="roblox-tab-3"
            aria-controls="roblox-tabpanel-3"
          />
          <Tab
            icon={<Games />}
            label="Sessions"
            id="roblox-tab-4"
            aria-controls="roblox-tabpanel-4"
          />
          <Tab
            icon={<Quiz />}
            label="Quiz Analytics"
            id="roblox-tab-5"
            aria-controls="roblox-tabpanel-5"
          />
          <Tab
            icon={<Terrain />}
            label="Environment Preview"
            id="roblox-tab-6"
            aria-controls="roblox-tabpanel-6"
          />
          <Tab
            icon={<AutoAwesome />}
            label="AI Test"
            id="roblox-tab-7"
            aria-controls="roblox-tabpanel-7"
          />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        <TabPanel value={activeTab} index={0}>
          <RobloxAIAssistant />
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <RobloxControlPanel />
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <ContentGenerationMonitor />
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          <StudentProgressDashboard />
        </TabPanel>

        <TabPanel value={activeTab} index={4}>
          <RobloxSessionManager />
        </TabPanel>

        <TabPanel value={activeTab} index={5}>
          <QuizResultsAnalytics />
        </TabPanel>

        <TabPanel value={activeTab} index={6}>
          <RobloxEnvironmentPreview />
        </TabPanel>

        <TabPanel value={activeTab} index={7}>
          <AIAssistantTest />
        </TabPanel>
      </Box>
    </Box>
  );
}
