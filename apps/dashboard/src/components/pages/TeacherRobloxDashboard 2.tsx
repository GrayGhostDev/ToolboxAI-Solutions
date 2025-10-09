import { Box, Button, Text, Paper, Stack, Grid, Container, IconButton, Avatar, Card, CardContent, CardActions, List, ListItem, ListItemText, Divider, TextField, Select, MenuItem, Chip, Badge, Alert, CircularProgress, LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions, Drawer, AppBar, Toolbar, Tabs, Tab, Menu, Tooltip, Checkbox, Radio, RadioGroup, FormControl, FormControlLabel, InputLabel, Switch, Slider, Rating, Autocomplete, Skeleton, Table } from '../../utils/mui-imports';
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
  IconInfoCircle, IconAlertTriangle, IconCircleX, IconCircleCheck,
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
import { IconAutoAwesome, IconBell, IconCircle, IconDashboard, IconGames, IconGroups, IconHelp, IconPsychology, IconQuiz, IconRefresh, IconSettings, IconTerrain } from '@tabler/icons-react';

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
      <Paper style={{ p: 2, mb: 2 }}>
        <SimpleGrid spacing={2} alignItems="center">
          <Box xs={12} md={6}>
            <Box style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <IconGames color="blue" style={{ fontSize: 40 }} />
              <Box>
                <Text order={4}>Roblox Studio Integration</Text>
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
              <IconButton onClick={(e: React.MouseEvent) => handleRefresh} size="small">
                <IconRefresh />
              </IconButton>
              <IconButton onClick={(e: React.MouseEvent) => () => setShowHelp(!showHelp)} size="small">
                <IconHelp />
              </IconButton>
            </Stack>
          </Box>
        </SimpleGrid>

        {/* Quick Stats */}
        <SimpleGrid spacing={2} style={{ mt: 1 }}>
          <Box xs={6} sm={3}>
            <Card style={{ bgcolor: alpha(theme.palette.primary.main, 0.1) }}>
              <CardContent style={{ py: 1 }}>
                <Stack direction="row" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Text order={5}>{stats.activeGenerations}</Text>
                    <Text variant="caption" color="text.secondary">
                      Active Generations
                    </Text>
                  </Box>
                  <IconPsychology color="blue" />
                </Stack>
              </CardContent>
            </Card>
          </Box>

          <Box xs={6} sm={3}>
            <Card style={{ bgcolor: alpha(theme.palette.success.main, 0.1) }}>
              <CardContent style={{ py: 1 }}>
                <Stack direction="row" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Text order={5}>{stats.activeSessions}</Text>
                    <Text variant="caption" color="text.secondary">
                      Active Sessions
                    </Text>
                  </Box>
                  <IconGames color="green" />
                </Stack>
              </CardContent>
            </Card>
          </Box>

          <Box xs={6} sm={3}>
            <Card style={{ bgcolor: alpha(theme.palette.info.main, 0.1) }}>
              <CardContent style={{ py: 1 }}>
                <Stack direction="row" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Text order={5}>{stats.onlineStudents}</Text>
                    <Text variant="caption" color="text.secondary">
                      Online Students
                    </Text>
                  </Box>
                  <IconGroups color="cyan" />
                </Stack>
              </CardContent>
            </Card>
          </Box>

          <Box xs={6} sm={3}>
            <Card style={{ bgcolor: alpha(theme.palette.warning.main, 0.1) }}>
              <CardContent style={{ py: 1 }}>
                <Stack direction="row" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Text order={5}>{stats.totalStudents}</Text>
                    <Text variant="caption" color="text.secondary">
                      Total Students
                    </Text>
                  </Box>
                  <Badge badgeContent={stats.onlineStudents} color="green">
                    <IconGroups color="yellow" />
                  </Badge>
                </Stack>
              </CardContent>
            </Card>
          </Box>
        </SimpleGrid>
      </Paper>

      {/* IconHelp Alert */}
      {showHelp && (
        <Alert
          severity="info"
          onClose={() => setShowHelp(false)}
          style={{ mb: 2 }}
        >
          <AlertTitle>Roblox Studio Integration IconHelp</AlertTitle>
          <Text size="sm">
            • <strong>AI Assistant:</strong> Chat with AI to create educational content effortlessly<br />
            • <strong>Control Panel:</strong> Connect to Roblox Studio plugin and generate content<br />
            • <strong>Content Monitor:</strong> Track AI agent progress during content generation<br />
            • <strong>Student Progress:</strong> Monitor real-time student activity and performance<br />
            • <strong>Session Manager:</strong> Create and manage educational game sessions<br />
            • <strong>IconQuiz Analytics:</strong> Analyze quiz results and identify learning gaps<br />
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
          <Tab
            icon={<IconAutoAwesome />}
            label="AI Assistant"
            id="roblox-tab-0"
            aria-controls="roblox-tabpanel-0"
          />
          <Tab
            icon={<IconDashboard />}
            label="Control Panel"
            id="roblox-tab-1"
            aria-controls="roblox-tabpanel-1"
          />
          <Tab
            icon={<IconPsychology />}
            label="Content Monitor"
            id="roblox-tab-2"
            aria-controls="roblox-tabpanel-2"
          />
          <Tab
            icon={<IconGroups />}
            label="Student Progress"
            id="roblox-tab-3"
            aria-controls="roblox-tabpanel-3"
          />
          <Tab
            icon={<IconGames />}
            label="Sessions"
            id="roblox-tab-4"
            aria-controls="roblox-tabpanel-4"
          />
          <Tab
            icon={<IconQuiz />}
            label="IconQuiz Analytics"
            id="roblox-tab-5"
            aria-controls="roblox-tabpanel-5"
          />
          <Tab
            icon={<IconTerrain />}
            label="Environment Preview"
            id="roblox-tab-6"
            aria-controls="roblox-tabpanel-6"
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
