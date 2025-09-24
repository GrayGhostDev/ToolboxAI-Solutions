/**
 * SystemHealthDashboard - Comprehensive System Health Monitoring Page
 * Combines all health monitoring components for administrators
 */
import { memo, useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Paper,
  Tabs,
  Tab,
  Stack,
  Alert,
  AlertTitle,
  Button,
  IconButton,
  Tooltip,
  Chip,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Switch,
  FormControlLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';

import {
  Dashboard as DashboardIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Download as ExportIcon,
  Notifications as AlertsIcon,
  Timeline as MetricsIcon,
  Security as SecurityIcon,
  Speed as PerformanceIcon,
  Api as IntegrationIcon,
  Storage as DatabaseIcon,
  Games as RobloxIcon,
  Hub as AgentIcon,
  Stream as RealtimeIcon,
  Warning as WarningIcon,
  CheckCircle as HealthyIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';

import { motion } from 'framer-motion';
import SystemHealthMonitor from '../monitoring/SystemHealthMonitor';
import IntegrationHealthMonitor from '../monitoring/IntegrationHealthMonitor';
import { api } from '@/services/api';
import { usePusher } from '@/hooks/usePusher';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`health-tabpanel-${index}`}
      aria-labelledby={`health-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export interface SystemHealthDashboardProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const MotionContainer = motion(Container);

export const SystemHealthDashboard = memo<SystemHealthDashboardProps>(({
  autoRefresh = true,
  refreshInterval = 30000,
}) => {
  const theme = useTheme();
  const [currentTab, setCurrentTab] = useState(0);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(autoRefresh);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [alertsEnabled, setAlertsEnabled] = useState(true);
  const [lastSystemRefresh, setLastSystemRefresh] = useState(new Date());
  const [systemOverallHealth, setSystemOverallHealth] = useState<string>('unknown');

  // Setup Pusher for system-wide health alerts
  const { subscribe, unsubscribe } = usePusher();

  useEffect(() => {
    const channel = 'system-health';

    const handleSystemAlert = (data: { level: string; message: string; timestamp: string }) => {
      if (alertsEnabled && data.level === 'critical') {
        // You could trigger notifications here
        console.warn('System Health Alert:', data);
      }
    };

    const handleOverallHealthUpdate = (data: { status: string; timestamp: string }) => {
      setSystemOverallHealth(data.status);
      setLastSystemRefresh(new Date(data.timestamp));
    };

    subscribe(channel, 'system-alert', handleSystemAlert);
    subscribe(channel, 'overall-health', handleOverallHealthUpdate);

    return () => {
      unsubscribe(channel, 'system-alert', handleSystemAlert);
      unsubscribe(channel, 'overall-health', handleOverallHealthUpdate);
    };
  }, [subscribe, unsubscribe, alertsEnabled]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const handleGlobalRefresh = async () => {
    try {
      // Trigger a refresh on all health monitoring components
      setLastSystemRefresh(new Date());

      // You could also trigger a manual refresh of all services here
      await api.post('/api/v1/health/refresh-all');
    } catch (error) {
      console.error('Failed to refresh system health:', error);
    }
  };

  const handleExportHealth = async () => {
    try {
      const response = await api.get('/api/v1/health/export', {
        responseType: 'blob',
      });

      const blob = new Blob([response.data], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `system-health-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setExportOpen(false);
    } catch (error) {
      console.error('Failed to export health data:', error);
    }
  };

  const getOverallStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return theme.palette.success.main;
      case 'degraded':
        return theme.palette.warning.main;
      case 'unhealthy':
        return theme.palette.error.main;
      default:
        return theme.palette.text.secondary;
    }
  };

  const getOverallStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <HealthyIcon fontSize="small" />;
      case 'degraded':
        return <WarningIcon fontSize="small" />;
      case 'unhealthy':
        return <ErrorIcon fontSize="small" />;
      default:
        return <WarningIcon fontSize="small" />;
    }
  };

  const tabs = [
    {
      label: 'Overview',
      icon: <DashboardIcon />,
      description: 'System metrics and resource monitoring',
    },
    {
      label: 'Integrations',
      icon: <IntegrationIcon />,
      description: 'External API and service health',
    },
    {
      label: 'Database',
      icon: <DatabaseIcon />,
      description: 'PostgreSQL and Redis connectivity',
    },
    {
      label: 'Real-time',
      icon: <RealtimeIcon />,
      description: 'Pusher and WebSocket services',
    },
    {
      label: 'Agents',
      icon: <AgentIcon />,
      description: 'AI agent orchestration status',
    },
    {
      label: 'Roblox',
      icon: <RobloxIcon />,
      description: 'Roblox integration services',
    },
  ];

  return (
    <MotionContainer
      maxWidth="xl"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Stack spacing={3} sx={{ py: 3 }}>
        {/* Header */}
        <Paper sx={{ p: 3 }}>
          <Stack direction="row" alignItems="center" justifyContent="space-between">
            <Stack spacing={1}>
              <Typography variant="h4" fontWeight="bold">
                System Health Dashboard
              </Typography>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Typography variant="body2" color="text.secondary">
                  Real-time monitoring and diagnostics for all system components
                </Typography>
                <Chip
                  label={`System: ${systemOverallHealth.toUpperCase()}`}
                  size="small"
                  color={
                    systemOverallHealth === 'healthy'
                      ? 'success'
                      : systemOverallHealth === 'degraded'
                      ? 'warning'
                      : 'error'
                  }
                  icon={getOverallStatusIcon(systemOverallHealth)}
                />
              </Stack>
            </Stack>

            <Stack direction="row" spacing={1}>
              <FormControlLabel
                control={
                  <Switch
                    checked={autoRefreshEnabled}
                    onChange={(e) => setAutoRefreshEnabled(e.target.checked)}
                    size="small"
                  />
                }
                label="Auto-refresh"
              />

              <Tooltip title="Refresh all health checks">
                <IconButton onClick={handleGlobalRefresh} color="primary">
                  <RefreshIcon />
                </IconButton>
              </Tooltip>

              <Tooltip title="Export health data">
                <IconButton onClick={() => setExportOpen(true)} color="primary">
                  <ExportIcon />
                </IconButton>
              </Tooltip>

              <Tooltip title="Settings">
                <IconButton onClick={() => setSettingsOpen(true)} color="primary">
                  <SettingsIcon />
                </IconButton>
              </Tooltip>
            </Stack>
          </Stack>
        </Paper>

        {/* Health Status Alert */}
        {systemOverallHealth === 'unhealthy' && (
          <Alert severity="error">
            <AlertTitle>System Health Warning</AlertTitle>
            One or more critical system components are experiencing issues. Check the detailed tabs below for more information.
          </Alert>
        )}

        {systemOverallHealth === 'degraded' && (
          <Alert severity="warning">
            <AlertTitle>System Performance Degraded</AlertTitle>
            Some system components are not performing optimally. Monitor the situation and consider taking action if performance continues to degrade.
          </Alert>
        )}

        {/* Navigation Tabs */}
        <Paper>
          <Tabs
            value={currentTab}
            onChange={handleTabChange}
            variant="scrollable"
            scrollButtons="auto"
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            {tabs.map((tab, index) => (
              <Tab
                key={index}
                label={tab.label}
                icon={tab.icon}
                iconPosition="start"
                sx={{ minHeight: 72 }}
              />
            ))}
          </Tabs>

          {/* Tab Panels */}
          <TabPanel value={currentTab} index={0}>
            <SystemHealthMonitor
              autoRefresh={autoRefreshEnabled}
              refreshInterval={refreshInterval}
              showCharts={true}
              compact={false}
            />
          </TabPanel>

          <TabPanel value={currentTab} index={1}>
            <IntegrationHealthMonitor
              autoRefresh={autoRefreshEnabled}
              refreshInterval={refreshInterval}
              showDetails={true}
            />
          </TabPanel>

          <TabPanel value={currentTab} index={2}>
            <Card>
              <CardHeader title="Database Health" subheader="PostgreSQL and Redis connection monitoring" />
              <CardContent>
                <Typography>
                  Detailed database health monitoring will be displayed here.
                  This would include connection pools, query performance, and cache hit rates.
                </Typography>
              </CardContent>
            </Card>
          </TabPanel>

          <TabPanel value={currentTab} index={3}>
            <Card>
              <CardHeader title="Real-time Services" subheader="Pusher Channels and WebSocket monitoring" />
              <CardContent>
                <Typography>
                  Real-time service monitoring including Pusher channel health,
                  WebSocket connection counts, and message throughput.
                </Typography>
              </CardContent>
            </Card>
          </TabPanel>

          <TabPanel value={currentTab} index={4}>
            <Card>
              <CardHeader title="Agent Orchestration" subheader="AI agent system monitoring" />
              <CardContent>
                <Typography>
                  Agent system health including MCP server status, agent coordinator health,
                  and SPARC framework monitoring.
                </Typography>
              </CardContent>
            </Card>
          </TabPanel>

          <TabPanel value={currentTab} index={5}>
            <Card>
              <CardHeader title="Roblox Integration" subheader="Roblox-specific service monitoring" />
              <CardContent>
                <Typography>
                  Roblox integration health including Flask bridge status,
                  plugin communication, and content generation services.
                </Typography>
              </CardContent>
            </Card>
          </TabPanel>
        </Paper>
      </Stack>

      {/* Settings Dialog */}
      <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Health Monitoring Settings</DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ pt: 1 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={alertsEnabled}
                  onChange={(e) => setAlertsEnabled(e.target.checked)}
                />
              }
              label="Enable critical alerts"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={autoRefreshEnabled}
                  onChange={(e) => setAutoRefreshEnabled(e.target.checked)}
                />
              }
              label="Auto-refresh enabled"
            />

            <Typography variant="body2" color="text.secondary">
              Refresh interval: {refreshInterval / 1000} seconds
            </Typography>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Export Dialog */}
      <Dialog open={exportOpen} onClose={() => setExportOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Export Health Data</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary">
            Export comprehensive system health data as JSON for analysis or reporting.
            This includes all current health metrics, integration statuses, and system performance data.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportOpen(false)}>Cancel</Button>
          <Button onClick={handleExportHealth} variant="contained">
            Export
          </Button>
        </DialogActions>
      </Dialog>
    </MotionContainer>
  );
});

SystemHealthDashboard.displayName = 'SystemHealthDashboard';
export default SystemHealthDashboard;