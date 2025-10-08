
import { Box, Button, Typography, Card, CardContent, Grid, Container, Chip, Alert, CircularProgress, Tab, Tabs } from '../../../utils/mui-imports';
/**
 * SystemHealthDashboard - Comprehensive System Health Monitoring Page
 * Combines all health monitoring components for administrators
 */
import { memo, useState, useEffect } from 'react';
import {
  IconDashboard,
  IconRefresh,
  IconSettings,
  IconDownload,
  IconBell,
  IconAlertTriangle,
  IconCircleCheck,
  IconCircleX,
} from '@tabler/icons-react';
import { motion } from 'framer-motion';
import SystemHealthMonitor from '../../monitoring/SystemHealthMonitor';
import IntegrationHealthMonitor from '../../monitoring/IntegrationHealthMonitor';
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
      {value === index && <Box style={{ p: 3 }}>{children}</Box>}
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

  // Auto-refresh logic
  useEffect(() => {
    if (!autoRefreshEnabled) return;

    const interval = setInterval(() => {
      setLastSystemRefresh(new Date());
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefreshEnabled, refreshInterval]);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const handleRefresh = () => {
    setLastSystemRefresh(new Date());
  };

  const getHealthColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'good':
        return 'success';
      case 'warning':
      case 'degraded':
        return 'warning';
      case 'critical':
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getHealthIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'good':
        return <IconCircleCheck />;
      case 'warning':
      case 'degraded':
        return <IconAlertTriangle />;
      case 'critical':
      case 'error':
        return <IconCircleX />;
      default:
        return <IconDashboard />;
    }
  };

  return (
    <MotionContainer
      maxWidth="xl"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <Box sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h4" gutterBottom>
              System Health Dashboard
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Real-time monitoring and health status of all system components
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Chip
              icon={getHealthIcon(systemOverallHealth)}
              label={`Overall: ${systemOverallHealth}`}
              color={getHealthColor(systemOverallHealth) as any}
              variant="filled"
            />
            <Button
              startIcon={<IconRefresh />}
              onClick={handleRefresh}
              variant="outlined"
            >
              Refresh
            </Button>
            <Button
              startIcon={<IconBell />}
              onClick={() => setAlertsEnabled(!alertsEnabled)}
              variant={alertsEnabled ? 'contained' : 'outlined'}
            >
              Alerts
            </Button>
            <Button
              startIcon={<IconSettings />}
              onClick={() => setSettingsOpen(true)}
              variant="outlined"
            >
              Settings
            </Button>
          </Box>
        </Box>

        {/* Last Updated Info */}
        <Alert severity="info" sx={{ mb: 3 }}>
          Last updated: {lastSystemRefresh.toLocaleTimeString()} |
          Auto-refresh: {autoRefreshEnabled ? 'Enabled' : 'Disabled'}
        </Alert>

        {/* Tabs */}
        <Card>
          <Tabs value={currentTab} onChange={handleTabChange} aria-label="health monitoring tabs">
            <Tab label="System Health" />
            <Tab label="Integration Health" />
            <Tab label="Performance Metrics" />
            <Tab label="Alerts & Logs" />
          </Tabs>

          <TabPanel value={currentTab} index={0}>
            <SystemHealthMonitor autoRefresh={autoRefreshEnabled} />
          </TabPanel>

          <TabPanel value={currentTab} index={1}>
            <IntegrationHealthMonitor autoRefresh={autoRefreshEnabled} />
          </TabPanel>

          <TabPanel value={currentTab} index={2}>
            <Typography>Performance metrics coming soon...</Typography>
          </TabPanel>

          <TabPanel value={currentTab} index={3}>
            <Typography>Alerts and logs coming soon...</Typography>
          </TabPanel>
        </Card>
      </Box>
    </MotionContainer>
  );
});

SystemHealthDashboard.displayName = 'SystemHealthDashboard';
export default SystemHealthDashboard;
