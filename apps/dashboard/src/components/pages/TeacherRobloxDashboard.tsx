import {
  Box, Button, Text, Title, Paper, SimpleGrid, Container, ActionIcon, Avatar, Card,
  Group, List, Divider, TextInput, Select, Badge, Alert, Loader, Grid,
  Progress, Modal, Drawer, Tabs, Menu, Tooltip, Checkbox, Radio,
  Switch, Slider, Rating, Skeleton, Table, useMantineTheme
} from '@mantine/core';

// Helper function for color transparency (replaces MUI alpha)
const alpha = (color: string, opacity: number) => {
  if (color.startsWith('#')) {
    const hex = color.slice(1);
    const r = parseInt(hex.slice(0, 2), 16);
    const g = parseInt(hex.slice(2, 4), 16);
    const b = parseInt(hex.slice(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
  }
  return color;
};
/**
 * TeacherRobloxDashboard Page
 *
 * Main dashboard for teachers to manage Roblox educational content and sessions
 * Combines all Roblox components into a unified interface
 */

import React, { useState, useEffect } from 'react';
import {
  IconHome, IconUser, IconSettings, IconLogout, IconChevronDown,
  IconChevronUp, IconChevronLeft, IconChevronRight, IconMenu,
  IconX, IconCheck, IconPlus, IconMinus, IconEdit, IconTrash,
  IconSearch, IconFilter, IconDownload, IconUpload, IconEye,
  IconEyeOff, IconBell, IconMessage, IconStar, IconHeart,
  IconShare, IconRefresh, IconLogin, IconSchool, IconBook,
  IconChartBar, IconPalette, IconMoon, IconSun, IconPlayerPlay,
  IconPlayerPause, IconPlayerStop, IconVolume, IconVolumeOff,
  IconInfoCircle, IconAlertTriangle, IconCircleCheck,
  IconArrowLeft, IconArrowRight, IconSend, IconDeviceFloppy,
  IconPrinter, IconHelp, IconHelpCircle, IconLock, IconLockOpen,
  IconMail, IconPhone, IconMapPin, IconMap, IconCalendar, IconClock,
  IconWifi, IconWifiOff, IconBluetooth, IconBattery, IconCamera,
  IconMicrophone, IconMicrophoneOff, IconVideo, IconVideoOff,
  IconPhoto, IconPaperclip, IconCloud, IconCloudUpload,
  IconCloudDownload, IconFolder, IconFolderOpen, IconFolderPlus,
  IconFile, IconFileText, IconClipboard, IconBan, IconFlag,
  IconBookmark, IconShoppingCart, IconUserCircle, IconMoodSmile,
  IconMoodSad, IconThumbUp, IconThumbDown, IconMessages,
  IconMessageQuestion, IconSpeakerphone, IconBellRinging,
  IconBellOff, IconCalendarEvent, IconCalendarStats, IconAlarm,
  IconAlarmOff, IconHistory, IconRefreshOff, IconRefreshAlert,
  IconDashboard, IconUsers, IconDotsVertical, IconDots,
  IconReportAnalytics
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

// Lazy load Roblox components for optimal performance
const RobloxAIAssistant = React.lazy(() => import('../roblox/RobloxAIAssistant').then(m => ({ default: m.RobloxAIAssistant })));
const RobloxControlPanel = React.lazy(() => import('../roblox/RobloxControlPanel').then(m => ({ default: m.RobloxControlPanel })));
const ContentGenerationMonitor = React.lazy(() => import('../roblox/ContentGenerationMonitor').then(m => ({ default: m.ContentGenerationMonitor })));
const StudentProgressDashboard = React.lazy(() => import('../roblox/StudentProgressDashboard').then(m => ({ default: m.StudentProgressDashboard })));
const RobloxSessionManager = React.lazy(() => import('../roblox/RobloxSessionManager').then(m => ({ default: m.RobloxSessionManager })));
const QuizResultsAnalytics = React.lazy(() => import('../roblox/QuizResultsAnalytics').then(m => ({ default: m.QuizResultsAnalytics })));
const RobloxEnvironmentPreview = React.lazy(() => import('../roblox/RobloxEnvironmentPreview'));
// import { AIAssistantTest } from '../test/AIAssistantTest'; // File does not exist
import { IconSparkles, IconCircle, IconDeviceGamepad, IconBrain, IconWorld, IconClipboardCheck } from '@tabler/icons-react';
import { api } from '../../services/api';

type TabKey =
  | 'ai-assistant'
  | 'control-panel'
  | 'content-monitor'
  | 'student-progress'
  | 'sessions'
  | 'quiz-analytics'
  | 'environment-preview';

interface TabPanelProps {
  children?: React.ReactNode;
  activeValue: TabKey;
  tabValue: TabKey;
}

function TabPanel({ children, activeValue, tabValue, ...other }: TabPanelProps) {
  const isActive = activeValue === tabValue;

  return (
    <Box
      role="tabpanel"
      hidden={!isActive}
      id={`roblox-tabpanel-${tabValue}`}
      aria-labelledby={`roblox-tab-${tabValue}`}
      {...other}
      style={{ height: '100%' }}
    >
      {isActive && (
        <Box style={{ height: '100%', paddingTop: 8 }}>
          {children}
        </Box>
      )}
    </Box>
  );
}

export default function TeacherRobloxDashboard() {
  const theme = useMantineTheme();
  const dispatch = useAppDispatch();
  const { isConnected } = usePusherContext();

  // Bypass mode configuration
  const bypassAuth = import.meta.env.VITE_BYPASS_AUTH === 'true';
  const useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true';

  const [activeTab, setActiveTab] = useState<TabKey>('ai-assistant');
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
    // Skip plugin status checks if in bypass mode
    if (bypassAuth || useMockData) {
      // Set a static mock status for tests
      const mockStatus = {
        connected: true,
        version: '1.0.0',
        lastHeartbeat: new Date().toISOString(),
        capabilities: ['content-generation', 'real-time-sync', 'quiz-management']
      };
      dispatch(setPluginStatus(mockStatus));
      return;
    }

    let isMounted = true;

    const defaultCapabilities = ['content-generation', 'real-time-sync', 'quiz-management'];

    const fetchPluginStatus = async () => {
      try {
        const status = await api.checkRobloxPluginStatus();
        if (!isMounted) return;

        dispatch(
          setPluginStatus({
            connected: Boolean(status.connected),
            version: status.version,
            lastHeartbeat: new Date().toISOString(),
            capabilities: (status as any).capabilities ?? defaultCapabilities
          })
        );
      } catch (err) {
        if (!isMounted) return;

        dispatch(
          setPluginStatus({
            connected: false,
            version: undefined,
            lastHeartbeat: new Date().toISOString(),
            capabilities: defaultCapabilities
          })
        );
      }
    };

    void fetchPluginStatus();
    const interval = setInterval(fetchPluginStatus, 30000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [dispatch, bypassAuth, useMockData]);

  const handleTabChange = (newValue: string | null) => {
    if (!newValue) {
      return;
    }
    setActiveTab(newValue as TabKey);
  };

  const handleRefresh = () => {
    // Trigger refresh for current tab
    window.location.reload(); // Simple refresh for now
  };

  return (
    <Box style={{ height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper p="md" mb="md">
        <Grid align="center">
          <Grid.Col span={{ base: 12, md: 6 }}>
            <Group align="flex-start" gap="sm">
              <IconDeviceGamepad size={36} color={theme.colors.brand?.[6] || theme.colors.blue[6]} />
              <Box>
                <Title order={4}>Roblox Studio Integration</Title>
                <Text size="sm" c="dimmed">
                  Manage educational content and monitor student progress in real-time
                </Text>
              </Box>
            </Group>
          </Grid.Col>

          <Grid.Col span={{ base: 12, md: 6 }}>
            <Group justify="flex-end" gap="sm" wrap="wrap">
              <Badge
                variant="light"
                color={isConnected ? 'green' : 'red'}
                leftSection={<IconCircle size={12} />}
              >
                {isConnected ? 'Realtime Connected' : 'Realtime Offline'}
              </Badge>
              <Badge
                variant="light"
                color={stats.pluginConnected ? 'green' : 'red'}
                leftSection={<IconCircle size={12} />}
              >
                {stats.pluginConnected ? 'Plugin Connected' : 'Plugin Offline'}
              </Badge>
              <Group gap="xs">
                <ActionIcon onClick={handleRefresh} size="sm" variant="light">
                  <IconRefresh size={16} />
                </ActionIcon>
                <ActionIcon onClick={() => setShowHelp(!showHelp)} size="sm" variant="light">
                  <IconHelp size={16} />
                </ActionIcon>
              </Group>
            </Group>
          </Grid.Col>
        </Grid>

        {/* Quick Stats */}
        <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }} spacing="sm" mt="sm">
          <Card style={{ backgroundColor: alpha(theme.colors.brand[6], 0.1) }} p="sm">
            <Group align="center" justify="space-between">
              <Box>
                <Title order={5}>{stats.activeGenerations}</Title>
                <Text size="xs" c="dimmed">
                  Active Generations
                </Text>
              </Box>
              <IconBrain color={theme.colors.brand[6]} />
            </Group>
          </Card>

          <Card style={{ backgroundColor: alpha(theme.colors.green[6], 0.1) }} p="sm">
            <Group align="center" justify="space-between">
              <Box>
                <Title order={5}>{stats.activeSessions}</Title>
                <Text size="xs" c="dimmed">
                  Active Sessions
                </Text>
              </Box>
              <IconDeviceGamepad color={theme.colors.green[6]} />
            </Group>
          </Card>

          <Card style={{ backgroundColor: alpha(theme.colors.blue[6], 0.1) }} p="sm">
            <Group align="center" justify="space-between">
              <Box>
                <Title order={5}>{stats.onlineStudents}</Title>
                <Text size="xs" c="dimmed">
                  Online Students
                </Text>
              </Box>
              <IconUsers color={theme.colors.blue[6]} />
            </Group>
          </Card>

          <Card style={{ backgroundColor: alpha(theme.colors.orange[6], 0.1) }} p="sm">
            <Group align="center" justify="space-between">
              <Box>
                <Title order={5}>{stats.totalStudents}</Title>
                <Text size="xs" c="dimmed">
                  Total Students
                </Text>
              </Box>
              <Group gap={4} align="center">
                <Text fw={600}>{stats.onlineStudents}</Text>
                <IconUsers size={16} color={theme.colors.orange[6]} />
              </Group>
            </Group>
          </Card>
        </SimpleGrid>
      </Paper>

      {/* IconHelp Alert */}
      {showHelp && (
        <Alert
          color="blue"
          onClose={() => setShowHelp(false)}
          withCloseButton
          style={{ marginBottom: 16 }}
        >
          <Alert.Title>Roblox Studio Integration Help</Alert.Title>
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
      <Paper style={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          aria-label="Roblox dashboard tabs"
        >
          <Tabs.Tab
            id="roblox-tab-ai-assistant"
            icon={<IconSparkles />}
            label="AI Assistant"
            value="ai-assistant"
          />
          <Tabs.Tab
            id="roblox-tab-control-panel"
            icon={<IconDashboard />}
            label="Control Panel"
            value="control-panel"
          />
          <Tabs.Tab
            id="roblox-tab-content-monitor"
            icon={<IconBrain />}
            label="Content Monitor"
            value="content-monitor"
          />
          <Tabs.Tab
            id="roblox-tab-student-progress"
            icon={<IconUsers />}
            label="Student Progress"
            value="student-progress"
          />
          <Tabs.Tab
            id="roblox-tab-sessions"
            icon={<IconDeviceGamepad />}
            label="Sessions"
            value="sessions"
          />
          <Tabs.Tab
            id="roblox-tab-quiz-analytics"
            icon={<IconClipboardCheck />}
            label="Quiz Analytics"
            value="quiz-analytics"
          />
          <Tabs.Tab
            id="roblox-tab-environment-preview"
            icon={<IconWorld />}
            label="Environment Preview"
            value="environment-preview"
          />
          {/* Removed AI Test tab - component does not exist */}
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <Box style={{ flex: 1, overflow: 'hidden' }}>
        <TabPanel activeValue={activeTab} tabValue="ai-assistant">
          <React.Suspense fallback={<Box p="lg"><Loader size="lg" /><Text size="sm" c="dimmed" mt="md">Loading AI Assistant...</Text></Box>}>
            <RobloxAIAssistant />
          </React.Suspense>
        </TabPanel>

        <TabPanel activeValue={activeTab} tabValue="control-panel">
          <React.Suspense fallback={<Box p="lg"><Loader size="lg" /><Text size="sm" c="dimmed" mt="md">Loading Control Panel...</Text></Box>}>
            <RobloxControlPanel />
          </React.Suspense>
        </TabPanel>

        <TabPanel activeValue={activeTab} tabValue="content-monitor">
          <React.Suspense fallback={<Box p="lg"><Loader size="lg" /><Text size="sm" c="dimmed" mt="md">Loading Content Monitor...</Text></Box>}>
            <ContentGenerationMonitor />
          </React.Suspense>
        </TabPanel>

        <TabPanel activeValue={activeTab} tabValue="student-progress">
          <React.Suspense fallback={<Box p="lg"><Loader size="lg" /><Text size="sm" c="dimmed" mt="md">Loading Student Progress...</Text></Box>}>
            <StudentProgressDashboard />
          </React.Suspense>
        </TabPanel>

        <TabPanel activeValue={activeTab} tabValue="sessions">
          <React.Suspense fallback={<Box p="lg"><Loader size="lg" /><Text size="sm" c="dimmed" mt="md">Loading Session Manager...</Text></Box>}>
            <RobloxSessionManager />
          </React.Suspense>
        </TabPanel>

        <TabPanel activeValue={activeTab} tabValue="quiz-analytics">
          <React.Suspense fallback={<Box p="lg"><Loader size="lg" /><Text size="sm" c="dimmed" mt="md">Loading Quiz Analytics...</Text></Box>}>
            <QuizResultsAnalytics />
          </React.Suspense>
        </TabPanel>

        <TabPanel activeValue={activeTab} tabValue="environment-preview">
          <React.Suspense fallback={<Box p="lg"><Loader size="lg" /><Text size="sm" c="dimmed" mt="md">Loading Environment Preview...</Text></Box>}>
            <RobloxEnvironmentPreview />
          </React.Suspense>
        </TabPanel>
      </Box>
    </Box>
  );
}
