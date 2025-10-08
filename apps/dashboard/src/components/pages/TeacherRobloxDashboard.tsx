import { Box, Text, Paper, Stack, Card, CardContent, Chip, Badge, Alert, Tabs, Tab, useTheme, alpha, AlertTitle, SimpleGrid, IconButton } from '../../utils/mui-imports';
/**
 * TeacherRobloxDashboard Page
 *
 * Main dashboard for teachers to manage Roblox educational content and sessions
 * Combines all Roblox components into a unified interface
 */

import React, { useState, useEffect } from 'react';
import {
  IconSparkles,
  IconCircle,
  IconDashboard,
  IconDeviceGamepad2,
  IconUsers,
  IconHelp,
  IconBrain,
  IconClipboardList,
  IconRefresh,
  IconMountain
} from '@tabler/icons-react';
import { useAppSelector, useAppDispatch } from '../../store';
import { usePusherContext } from '../../contexts/PusherContext';
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
import RobloxEnvironmentPreview from '../roblox/RobloxEnvironmentPreview';
import { RobloxAIAssistant } from '../roblox/RobloxAIAssistant';

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
      style={{ height: '100%' }}
    >
      {value === index && (
        <Box style={{ height: '100%', pt: 2 }}>
          {children}
        </Box>
      )}
    </Box>
  );
}

export default function TeacherRobloxDashboard() {
  const theme = useTheme();
  const dispatch = useAppDispatch();
  const { isConnected } = usePusherContext();

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
    <Box style={{ height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper style={{ padding: 16, marginBottom: 16 }}>
        <SimpleGrid cols={2} spacing="md">
          <Box>
            <Box style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <IconDeviceGamepad2 size={40} color="blue" />
              <Box>
                <Text size="xl" weight={700}>Roblox Studio Integration</Text>
                <Text size="sm" color="dimmed">
                  Manage educational content and monitor student progress in real-time
                </Text>
              </Box>
            </Box>
          </Box>

          <Box>
            <Stack align="flex-end" spacing="xs">
              {/* Status Indicators */}
              <Box style={{ display: 'flex', gap: 8 }}>
                <Badge
                  color={isConnected ? 'green' : 'red'}
                  variant="filled"
                  leftSection={<IconCircle size={12} />}
                >
                  {isConnected ? 'Dashboard Connected' : 'Dashboard Offline'}
                </Badge>
                <Badge
                  color={stats.pluginConnected ? 'green' : 'red'}
                  variant="filled"
                  leftSection={<IconCircle size={12} />}
                >
                  {stats.pluginConnected ? 'Plugin Connected' : 'Plugin Offline'}
                </Badge>

                {/* Actions */}
                <IconButton onClick={handleRefresh} size="sm">
                  <IconRefresh size={18} />
                </IconButton>
                <IconButton onClick={() => setShowHelp(!showHelp)} size="sm">
                  <IconHelp size={18} />
                </IconButton>
              </Box>
            </Stack>
          </Box>
        </SimpleGrid>

        {/* Quick Stats */}
        <SimpleGrid cols={4} spacing="md" style={{ marginTop: 16 }}>
          <Card style={{ backgroundColor: alpha(theme.colors.blue?.[6] || '#228be6', 0.1) }}>
            <Box style={{ paddingTop: 8, paddingBottom: 8 }}>
              <Box style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Text size="xl" weight={700}>{stats.activeGenerations}</Text>
                  <Text size="xs" color="dimmed">
                    Active Generations
                  </Text>
                </Box>
                <IconBrain size={32} color="blue" />
              </Box>
            </Box>
          </Card>

          <Card style={{ backgroundColor: alpha(theme.colors.green?.[6] || '#40c057', 0.1) }}>
            <Box style={{ paddingTop: 8, paddingBottom: 8 }}>
              <Box style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Text size="xl" weight={700}>{stats.activeSessions}</Text>
                  <Text size="xs" color="dimmed">
                    Active Sessions
                  </Text>
                </Box>
                <IconDeviceGamepad2 size={32} color="green" />
              </Box>
            </Box>
          </Card>

          <Card style={{ backgroundColor: alpha(theme.colors.cyan?.[6] || '#15aabf', 0.1) }}>
            <Box style={{ paddingTop: 8, paddingBottom: 8 }}>
              <Box style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Text size="xl" weight={700}>{stats.onlineStudents}</Text>
                  <Text size="xs" color="dimmed">
                    Online Students
                  </Text>
                </Box>
                <IconUsers size={32} color="cyan" />
              </Box>
            </Box>
          </Card>

          <Card style={{ backgroundColor: alpha(theme.colors.yellow?.[6] || '#fab005', 0.1) }}>
            <Box style={{ paddingTop: 8, paddingBottom: 8 }}>
              <Box style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Text size="xl" weight={700}>{stats.totalStudents}</Text>
                  <Text size="xs" color="dimmed">
                    Total Students
                  </Text>
                </Box>
                <Badge color="green" size="sm" style={{ position: 'absolute', top: 8, right: 8 }}>
                  {stats.onlineStudents}
                </Badge>
                <IconUsers size={32} color="orange" />
              </Box>
            </Box>
          </Card>
        </SimpleGrid>
      </Paper>

      {/* Help Alert */}
      {showHelp && (
        <Alert
          icon={<IconHelp size={20} />}
          title="Roblox Studio Integration Help"
          color="blue"
          withCloseButton
          onClose={() => setShowHelp(false)}
          style={{ marginBottom: 16 }}
        >
          <Text size="sm">
            • <strong>AI Assistant:</strong> Chat with AI to create educational content effortlessly<br />
            • <strong>Control Panel:</strong> Connect to Roblox Studio plugin and generate content<br />
            • <strong>Content Monitor:</strong> Track AI agent progress during content generation<br />
            • <strong>Student Progress:</strong> Monitor real-time student activity and performance<br />
            • <strong>Session Manager:</strong> Create and manage educational game sessions<br />
            • <strong>Quiz Analytics:</strong> Analyze quiz results and identify learning gaps<br />
            • <strong>Environment Preview:</strong> Preview 3D environments before deployment
          </Text>
        </Alert>
      )}

      {/* Tab Navigation */}
      <Paper style={{ borderBottom: '1px solid #dee2e6' }}>
        <Tabs value={activeTab.toString()} onTabChange={(value) => setActiveTab(Number(value))}>
          <Tabs.List>
            <Tabs.Tab value="0" leftSection={<IconSparkles size={18} />}>
              AI Assistant
            </Tabs.Tab>
            <Tabs.Tab value="1" leftSection={<IconDashboard size={18} />}>
              Control Panel
            </Tabs.Tab>
            <Tabs.Tab value="2" leftSection={<IconBrain size={18} />}>
              Content Monitor
            </Tabs.Tab>
            <Tabs.Tab value="3" leftSection={<IconUsers size={18} />}>
              Student Progress
            </Tabs.Tab>
            <Tabs.Tab value="4" leftSection={<IconDeviceGamepad2 size={18} />}>
              Sessions
            </Tabs.Tab>
            <Tabs.Tab value="5" leftSection={<IconClipboardList size={18} />}>
              Quiz Analytics
            </Tabs.Tab>
            <Tabs.Tab value="6" leftSection={<IconMountain size={18} />}>
              Environment Preview
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="0" pt="md">
            <RobloxAIAssistant />
          </Tabs.Panel>

          <Tabs.Panel value="1" pt="md">
            <RobloxControlPanel />
          </Tabs.Panel>

          <Tabs.Panel value="2" pt="md">
            <ContentGenerationMonitor />
          </Tabs.Panel>

          <Tabs.Panel value="3" pt="md">
            <StudentProgressDashboard />
          </Tabs.Panel>

          <Tabs.Panel value="4" pt="md">
            <RobloxSessionManager />
          </Tabs.Panel>

          <Tabs.Panel value="5" pt="md">
            <QuizResultsAnalytics />
          </Tabs.Panel>

          <Tabs.Panel value="6" pt="md">
            <RobloxEnvironmentPreview />
          </Tabs.Panel>
        </Tabs>
      </Paper>
    </Box>
  );
}
