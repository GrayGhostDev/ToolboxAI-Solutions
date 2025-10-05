import { Box, Button, Text, Paper, Stack, Grid, Container, IconButton, Avatar, Card, CardContent, CardActions, List, ListItem, ListItemText, Divider, TextField, Select, MenuItem, Chip, Badge, Alert, CircularProgress, LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions, Drawer, AppBar, Toolbar, Tabs, Tab, Menu, Tooltip, Checkbox, Radio, RadioGroup, FormControl, FormControlLabel, InputLabel, Switch, Slider, Rating, Autocomplete, Skeleton, Table } from '../../utils/mui-imports';
/**
 * GPT-4.1 Migration Monitoring Dashboard
 *
 * Comprehensive dashboard for monitoring the GPT-4.1 migration progress,
 * including real-time metrics, cost tracking, performance monitoring,
 * and alert management.
 */

import React, { useState, useEffect, useCallback } from 'react';
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
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import { IconAlertTriangle, IconAttachMoney, IconCircleCheck, IconCircleX, IconClipboard, IconInfoCircle, IconRefresh, IconSettings, IconSpeed, IconTimeline, IconTrendingDown, IconTrendingUp } from '@tabler/icons-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement,
  BarElement
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement,
  BarElement
);

// Types
interface MigrationMetrics {
  progress_percentage: number;
  days_remaining: number;
  current_phase: string;
  urgency_level: string;
  on_track: boolean;
  deadline: string;
}

interface CostMetrics {
  current_monthly_cost: number;
  projected_monthly_total: number;
  daily_average: number;
  budget_utilization: number;
  weekly_total: number;
  trend_percentage: number;
}

interface PerformanceMetrics {
  score: number;
  status: string;
  anomaly_count: number;
  metrics: {
    [key: string]: number;
  };
}

interface Alert {
  id: string;
  title: string;
  message: string;
  severity: 'info' | 'warning' | 'critical' | 'emergency';
  category: string;
  timestamp: string;
  acknowledged: boolean;
  escalation_level: number;
}

interface DashboardData {
  layout: {
    name: string;
    description: string;
    auto_refresh: boolean;
    refresh_interval: number;
  };
  widgets: {
    [key: string]: any;
  };
  metadata: {
    generated_at: string;
    layout_name: string;
    data_freshness: {
      [key: string]: string;
    };
  };
}

const GPT4MigrationDashboard= () => {
  const theme = useTheme();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [currentLayout, setCurrentLayout] = useState('executive');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Fetch dashboard data
  const fetchDashboardData = useCallback(async (forceRefresh = false) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `/api/v1/gpt4-migration/dashboard/${currentLayout}?force_refresh=${forceRefresh}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setDashboardData(data);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch dashboard data');
    } finally {
      setLoading(false);
    }
  }, [currentLayout]);

  // Auto-refresh effect
  useEffect(() => {
    if (autoRefresh && dashboardData?.layout.auto_refresh) {
      const interval = setInterval(() => {
        fetchDashboardData();
      }, (dashboardData.layout.refresh_interval || 30) * 1000);

      return () => clearInterval(interval);
    }
  }, [autoRefresh, dashboardData?.layout, fetchDashboardData]);

  // Initial load
  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Utility functions
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'emergency': return 'error';
      case 'critical': return 'error';
      case 'warning': return 'warning';
      case 'info': return 'info';
      default: return 'default';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'emergency': return <IconCircleX />;
      case 'critical': return <IconCircleX />;
      case 'warning': return <IconAlertTriangle />;
      case 'info': return <IconInfoCircle />;
      default: return <IconCircleCheck />;
    }
  };

  // Render migration progress widget
  const renderMigrationProgress = () => {
    const widget = dashboardData?.widgets?.migration_progress;
    if (!widget?.data) return null;

    const progress: MigrationMetrics = widget.data;

    return (
      <Card>
        <CardContent>
          <Text order={6} gutterBottom>
            Migration Progress
          </Text>
          <Box display="flex" alignItems="center" mb={2}>
            <Box position="relative" display="inline-flex">
              <CircularProgress
                variant="determinate"
                value={progress.progress_percentage}
                size={80}
                thickness={4}
                color={progress.on_track ? 'primary' : 'warning'}
              />
              <Box
                position="absolute"
                top={0}
                left={0}
                bottom={0}
                right={0}
                display="flex"
                alignItems="center"
                justifyContent="center"
              >
                <Text order={6} component="div" color="text.secondary">
                  {formatPercentage(progress.progress_percentage)}
                </Text>
              </Box>
            </Box>
            <Box ml={2}>
              <Text size="sm" color="text.secondary">
                Phase: {progress.current_phase}
              </Text>
              <Text size="sm" color="text.secondary">
                Days remaining: {progress.days_remaining}
              </Text>
              <Chip
                label={progress.urgency_level}
                color={progress.urgency_level === 'low' ? 'success' : 'warning'}
                size="small"
              />
            </Box>
          </Box>
          <Text size="sm" color="text.secondary">
            Deadline: {new Date(progress.deadline).toLocaleDateString()}
          </Text>
        </CardContent>
      </Card>
    );
  };

  // Render cost summary widget
  const renderCostSummary = () => {
    const widget = dashboardData?.widgets?.cost_summary;
    if (!widget?.data) return null;

    const cost: CostMetrics = widget.data;

    return (
      <Card>
        <CardContent>
          <Text order={6} gutterBottom>
            Cost Summary
          </Text>
          <SimpleGrid spacing={2}>
            <Box xs={6}>
              <Text order={4} color="blue">
                {formatCurrency(cost.current_monthly_cost)}
              </Text>
              <Text size="sm" color="text.secondary">
                Current Month
              </Text>
            </Box>
            <Box xs={6}>
              <Text order={4} color="gray">
                {formatCurrency(cost.projected_monthly_total)}
              </Text>
              <Text size="sm" color="text.secondary">
                Projected Total
              </Text>
            </Box>
            <Box xs={12}>
              <Box display="flex" alignItems="center" mt={1}>
                <Text size="sm" color="text.secondary" mr={1}>
                  Budget utilization:
                </Text>
                <LinearProgress
                  variant="determinate"
                  value={Math.min(cost.budget_utilization, 100)}
                  color={cost.budget_utilization > 80 ? 'warning' : 'primary'}
                  style={{ flexGrow: 1, mr: 1 }}
                />
                <Text size="sm">
                  {formatPercentage(cost.budget_utilization)}
                </Text>
              </Box>
            </Box>
            <Box xs={12}>
              <Box display="flex" alignItems="center">
                {cost.trend_percentage > 0 ? (
                  <IconTrendingUp color="red" />
                ) : (
                  <IconTrendingDown color="green" />
                )}
                <Text
                  size="sm"
                  color={cost.trend_percentage > 0 ? 'error' : 'success'}
                  ml={0.5}
                >
                  {cost.trend_percentage > 0 ? '+' : ''}{formatPercentage(cost.trend_percentage)} vs last week
                </Text>
              </Box>
            </Box>
          </SimpleGrid>
        </CardContent>
      </Card>
    );
  };

  // Render performance score widget
  const renderPerformanceScore = () => {
    const widget = dashboardData?.widgets?.performance_score;
    if (!widget?.data) return null;

    const performance: PerformanceMetrics = widget.data;

    const getScoreColor = (score: number) => {
      if (score >= 85) return 'success';
      if (score >= 70) return 'warning';
      return 'error';
    };

    return (
      <Card>
        <CardContent>
          <Text order={6} gutterBottom>
            Performance Score
          </Text>
          <Box display="flex" alignItems="center" mb={2}>
            <Box position="relative" display="inline-flex">
              <CircularProgress
                variant="determinate"
                value={performance.score}
                size={80}
                thickness={4}
                color={getScoreColor(performance.score)}
              />
              <Box
                position="absolute"
                top={0}
                left={0}
                bottom={0}
                right={0}
                display="flex"
                alignItems="center"
                justifyContent="center"
              >
                <Text order={6} component="div" color="text.secondary">
                  {performance.score.toFixed(0)}
                </Text>
              </Box>
            </Box>
            <Box ml={2}>
              <Text size="md" fontWeight="bold">
                {performance.status.toUpperCase()}
              </Text>
              <Text size="sm" color="text.secondary">
                {performance.anomaly_count} anomalies detected
              </Text>
            </Box>
          </Box>
          <SimpleGrid spacing={1}>
            {Object.entries(performance.metrics).map(([key, value]) => (
              <Box xs={6} key={key}>
                <Text size="sm" color="text.secondary">
                  {key.replace('_', ' ')}: {typeof value === 'number' ? value.toFixed(2) : value}
                </Text>
              </Box>
            ))}
          </SimpleGrid>
        </CardContent>
      </Card>
    );
  };

  // Render active alerts widget
  const renderActiveAlerts = () => {
    const widget = dashboardData?.widgets?.active_alerts;
    if (!widget?.data) return null;

    const alerts: Alert[] = widget.data.alerts || [];

    return (
      <Card>
        <CardContent>
          <Text order={6} gutterBottom>
            Active Alerts
          </Text>
          {alerts.length === 0 ? (
            <Box display="flex" alignItems="center" py={2}>
              <IconCircleCheck color="green" style={{ mr: 1 }} />
              <Text size="sm" color="text.secondary">
                No active alerts
              </Text>
            </Box>
          ) : (
            <Box maxHeight={300} overflow="auto">
              {alerts.map((alert) => (
                <Alert
                  key={alert.id}
                  severity={getSeverityColor(alert.severity) as any}
                  icon={getSeverityIcon(alert.severity)}
                  style={{ mb: 1 }}
                >
                  <AlertTitle>{alert.title}</AlertTitle>
                  <Text size="sm">{alert.message}</Text>
                  <Box display="flex" alignItems="center" mt={1}>
                    <Chip
                      label={alert.category}
                      size="small"
                      style={{ mr: 1 }}
                    />
                    <Text variant="caption" color="text.secondary">
                      {new Date(alert.timestamp).toLocaleString()}
                    </Text>
                  </Box>
                </Alert>
              ))}
            </Box>
          )}
        </CardContent>
      </Card>
    );
  };

  // Render cost trends chart
  const renderCostTrends = () => {
    const widget = dashboardData?.widgets?.cost_projection;
    if (!widget?.data?.series) return null;

    const chartData = {
      labels: widget.data.series[0].data.map((point: any) =>
        new Date(point.date).toLocaleDateString()
      ),
      datasets: [
        {
          label: 'Daily Cost',
          data: widget.data.series[0].data.map((point: any) => point.cost),
          borderColor: theme.palette.primary.main,
          backgroundColor: theme.palette.primary.light,
          tension: 0.4,
          fill: false
        },
        ...(widget.data.budget_line ? [{
          label: 'Budget Line',
          data: Array(widget.data.series[0].data.length).fill(widget.data.budget_line),
          borderColor: theme.palette.warning.main,
          backgroundColor: theme.palette.warning.light,
          borderDash: [5, 5],
          fill: false
        }] : [])
      ]
    };

    const options = {
      responsive: true,
      plugins: {
        legend: {
          position: 'top' as const,
        },
        title: {
          display: true,
          text: 'Cost Trends'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function(value: any) {
              return '$' + value;
            }
          }
        }
      }
    };

    return (
      <Card>
        <CardContent>
          <Text order={6} gutterBottom>
            Cost Projection
          </Text>
          <Box height={300}>
            <Line data={chartData} options={options} />
          </Box>
        </CardContent>
      </Card>
    );
  };

  // Settings dialog
  const renderSettingsDialog = () => (
    <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)}>
      <DialogTitle>Dashboard Settings</DialogTitle>
      <DialogContent>
        <TextField
          select
          label="Layout"
          value={currentLayout}
          onChange={(e) => setCurrentLayout(e.target.value)}
          fullWidth
          margin="normal"
        >
          <MenuItem value="executive">Executive Summary</MenuItem>
          <MenuItem value="technical">Technical Operations</MenuItem>
          <MenuItem value="cost">Cost Management</MenuItem>
        </TextField>
        <Box mt={2}>
          <Text variant="subtitle2" gutterBottom>
            Auto Refresh
          </Text>
          <Box display="flex" alignItems="center">
            <Button
              variant={autoRefresh ? "contained" : "outlined"}
              onClick={() => setAutoRefresh(!autoRefresh)}
              size="small"
            >
              {autoRefresh ? 'Enabled' : 'Disabled'}
            </Button>
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setSettingsOpen(false)}>Close</Button>
      </DialogActions>
    </Dialog>
  );

  if (loading && !dashboardData) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">
          <AlertTitle>Error loading dashboard</AlertTitle>
          {error}
        </Alert>
        <Button
          variant="filled"
          onClick={() => fetchDashboardData()}
          style={{ mt: 2 }}
          startIcon={<IconRefresh />}
        >
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box p={3}>
      {/* Header */}
      <Box display="flex" justifyContent="between" alignItems="center" mb={3}>
        <Box>
          <Text order={4} gutterBottom>
            GPT-4.1 Migration Dashboard
          </Text>
          <Text size="sm" color="text.secondary">
            {dashboardData?.layout.description} • Last updated: {lastUpdated?.toLocaleTimeString()}
          </Text>
        </Box>
        <Box>
          <Tooltip title="Refresh Dashboard">
            <IconButton
              onClick={() => fetchDashboardData(true)}
              disabled={loading}
            >
              <IconRefresh />
            </IconButton>
          </Tooltip>
          <Tooltip title="Settings">
            <IconButton onClick={() => setSettingsOpen(true)}>
              <IconSettings />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Dashboard Grid */}
      <SimpleGrid spacing={3}>
        {/* First Row - Key Metrics */}
        <Box xs={12} md={4}>
          {renderMigrationProgress()}
        </Box>
        <Box xs={12} md={4}>
          {renderCostSummary()}
        </Box>
        <Box xs={12} md={4}>
          {renderPerformanceScore()}
        </Box>

        {/* Second Row - Charts and Alerts */}
        <Box xs={12} md={8}>
          {renderCostTrends()}
        </Box>
        <Box xs={12} md={4}>
          {renderActiveAlerts()}
        </Box>
      </SimpleGrid>

      {/* Settings Dialog */}
      {renderSettingsDialog()}

      {/* Floating Action Button for quick actions */}
      <Fab
        color="blue"
        style={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={() => fetchDashboardData(true)}
      >
        <IconRefresh />
      </Fab>
    </Box>
  );
};

export default GPT4MigrationDashboard;