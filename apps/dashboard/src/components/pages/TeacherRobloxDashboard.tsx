import {
  Box, Button, Text, Title, Paper, Stack, SimpleGrid, Container, ActionIcon, Avatar, Card,
  Group, List, Divider, TextInput, Select, Badge, Alert, Loader,
  Progress, Modal, Drawer, Tabs, Menu, Tooltip, Checkbox, Radio,
  Switch, Slider, Rating, Skeleton, Table, useMantineTheme, Chip
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

// Import Roblox components
import { RobloxControlPanel } from '../roblox/RobloxControlPanel';
import { ContentGenerationMonitor } from '../roblox/ContentGenerationMonitor';
import { StudentProgressDashboard } from '../roblox/StudentProgressDashboard';
import { RobloxSessionManager } from '../roblox/RobloxSessionManager';
import { QuizResultsAnalytics } from '../roblox/QuizResultsAnalytics';
import RobloxEnvironmentPreview from '../roblox/RobloxEnvironmentPreview';
import { RobloxAIAssistant } from '../roblox/RobloxAIAssistant';
// import { AIAssistantTest } from '../test/AIAssistantTest'; // File does not exist
import { IconSparkles, IconCircle, IconDeviceGamepad, IconBrain, IconWorld, IconClipboardCheck } from '@tabler/icons-react';

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
  const theme = useMantineTheme();
  const dispatch = useAppDispatch();
  const { isConnected } = usePusherContext();

  // Bypass mode configuration
  const bypassAuth = import.meta.env.VITE_BYPASS_AUTH === 'true';
  const useMockData = import.meta.env.VITE_USE_MOCK_DATA === 'true';

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
  }, [dispatch, bypassAuth, useMockData]);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleRefresh = () => {
    // Trigger refresh for current tab
    window.location.reload(); // Simple refresh for now
  };

  return (
    <Box style={{ height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper style={{ p: 2, mb: 2 }}>
        <SimpleGrid spacing={2} alignItems="center">
          <Box xs={12} md={6}>
            <Box style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <IconDeviceGamepad color="blue" style={{ fontSize: 40 }} />
              <Box>
                <Title order={4}>Roblox Studio Integration</Title>
                <Text size="sm" color="text.secondary">
                  Manage educational content and monitor student progress in real-time
                </Text>
              </Box>
            </Box>
          </Box>

          <Box xs={12} md={6}>
            <Stack direction="row" spacing={2} justifyContent="flex-end">
              {/* Status Indicators */}
              <Chip
                icon={<IconCircle style={{ fontSize: 12 }} />}
                label={isConnected ? 'IconDashboard Connected' : 'IconDashboard Offline'}
                color={isConnected ? 'success' : 'error'}
                size="small"
              />
              <Chip
                icon={<IconCircle style={{ fontSize: 12 }} />}
                label={stats.pluginConnected ? 'Plugin Connected' : 'Plugin Offline'}
                color={stats.pluginConnected ? 'success' : 'error'}
                size="small"
              />

              {/* Actions */}
              <ActionIcon onClick={() => handleRefresh()} size="sm">
                <IconRefresh />
              </ActionIcon>
              <ActionIcon onClick={() => setShowHelp(!showHelp)} size="sm">
                <IconHelp />
              </ActionIcon>
            </Stack>
          </Box>
        </SimpleGrid>

        {/* Quick Stats */}
        <SimpleGrid spacing={2} style={{ mt: 1 }}>
          <Box xs={6} sm={3}>
            <Card style={{ backgroundColor: alpha(theme.colors.brand[6], 0.1), padding: 8 }}>
              <Group align="center" justify="space-between">
                <Box>
                  <Title order={5}>{stats.activeGenerations}</Title>
                  <Text size="xs" c="dimmed">
                    Active Generations
                  </Text>
                </Box>
                <IconBrain color="blue" />
              </Group>
            </Card>
          </Box>

          <Box xs={6} sm={3}>
            <Card style={{ backgroundColor: alpha(theme.colors.green[6], 0.1), padding: 8 }}>
              <Group align="center" justify="space-between">
                <Box>
                  <Title order={5}>{stats.activeSessions}</Title>
                  <Text size="xs" c="dimmed">
                    Active Sessions
                  </Text>
                </Box>
                <IconDeviceGamepad color="green" />
              </Group>
            </Card>
          </Box>

          <Box xs={6} sm={3}>
            <Card style={{ backgroundColor: alpha(theme.colors.blue[6], 0.1), padding: 8 }}>
              <Group align="center" justify="space-between">
                <Box>
                  <Title order={5}>{stats.onlineStudents}</Title>
                  <Text size="xs" c="dimmed">
                    Online Students
                  </Text>
                </Box>
                <IconUsers color="cyan" />
              </Group>
            </Card>
          </Box>

          <Box xs={6} sm={3}>
            <Card style={{ backgroundColor: alpha(theme.colors.orange[6], 0.1), padding: 8 }}>
              <Group align="center" justify="space-between">
                <Box>
                  <Title order={5}>{stats.totalStudents}</Title>
                  <Text size="xs" c="dimmed">
                    Total Students
                  </Text>
                </Box>
                <Badge color="green" size="lg">
                  {stats.onlineStudents}
                  <IconUsers color="yellow" style={{ marginLeft: 4 }} />
                </Badge>
              </Group>
            </Card>
          </Box>
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
          variant="scrollable"
          scrollButtons="auto"
          aria-label="Roblox dashboard tabs"
        >
          <Tabs.Tab
            icon={<IconSparkles />}
            label="AI Assistant"
            value="0"
          />
          <Tabs.Tab
            icon={<IconDashboard />}
            label="Control Panel"
            value="1"
          />
          <Tabs.Tab
            icon={<IconBrain />}
            label="Content Monitor"
            value="2"
          />
          <Tabs.Tab
            icon={<IconUsers />}
            label="Student Progress"
            value="3"
          />
          <Tabs.Tab
            icon={<IconDeviceGamepad />}
            label="Sessions"
            value="4"
          />
          <Tabs.Tab
            icon={<IconClipboardCheck />}
            label="Quiz Analytics"
            value="5"
          />
          <Tabs.Tab
            icon={<IconWorld />}
            label="Environment Preview"
            value="6"
          />
          {/* Removed AI Test tab - component does not exist */}
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <Box style={{ flex: 1, overflow: 'hidden' }}>
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
      </Box>
    </Box>
  );
}
