import React, { useState, useEffect, useCallback } from 'react';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import Avatar from '@mui/material/Avatar';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import ListItemAvatar from '@mui/material/ListItemAvatar';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import Alert from '@mui/material/Alert';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Paper from '@mui/material/Paper';
import Divider from '@mui/material/Divider';

import {
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  School as SchoolIcon,
  Assessment as AssessmentIcon,
  Settings as SettingsIcon,
  Security as SecurityIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
} from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '@/hooks/redux';
import { MetricCard } from '@/components/metrics/MetricCard';
import { ActivityFeed } from '@/components/activity/ActivityFeed';
import { SystemHealthMonitor } from '@/components/monitoring/SystemHealthMonitor';
import { UserManagementPanel } from '@/components/admin/UserManagementPanel';
import { ContentModerationPanel } from '@/components/admin/ContentModerationPanel';
import { SystemSettingsPanel } from '@/components/admin/SystemSettingsPanel';
import { api } from '@/services/api';
import { pusherService } from '@/services/pusher';
import { formatDistanceToNow } from 'date-fns';

interface AdminDashboardProps {
  section?: string;
}

interface SystemMetrics {
  totalUsers: number;
  activeUsers: number;
  totalCourses: number;
  activeSessions: number;
  contentGenerated: number;
  systemHealth: number;
  cpuUsage: number;
  memoryUsage: number;
  storageUsage: number;
  apiLatency: number;
}

interface SystemAlert {
  id: string;
  severity: 'error' | 'warning' | 'info' | 'success';
  message: string;
  timestamp: Date;
  resolved: boolean;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FunctionComponent<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`admin-tabpanel-${index}`}
      aria-labelledby={`admin-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
};

export default function AdminDashboard({ section = 'overview' }: AdminDashboardProps) {
  const dispatch = useAppDispatch();
  const { isAuthenticated, ...user } = useAppSelector((state) => state.user);
  const [activeTab, setActiveTab] = useState(0);
  const [metrics, setMetrics] = useState<SystemMetrics>({
    totalUsers: 0,
    activeUsers: 0,
    totalCourses: 0,
    activeSessions: 0,
    contentGenerated: 0,
    systemHealth: 95,
    cpuUsage: 45,
    memoryUsage: 62,
    storageUsage: 38,
    apiLatency: 120,
  });
  const [alerts, setAlerts] = useState<SystemAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Fetch system metrics
  const fetchMetrics = useCallback(async () => {
    try {
      setRefreshing(true);
      const response = await api.get('/api/v1/admin/metrics');
      setMetrics(response.data);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
      // Use mock data for development
      setMetrics({
        totalUsers: 1247,
        activeUsers: 342,
        totalCourses: 89,
        activeSessions: 156,
        contentGenerated: 3421,
        systemHealth: 95,
        cpuUsage: 45,
        memoryUsage: 62,
        storageUsage: 38,
        apiLatency: 120,
      });
    } finally {
      setRefreshing(false);
      setLoading(false);
    }
  }, []);

  // Fetch system alerts
  const fetchAlerts = useCallback(async () => {
    try {
      const response = await api.get('/api/v1/admin/alerts');
      setAlerts(response.data);
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
      // Use mock data for development
      setAlerts([
        {
          id: '1',
          severity: 'warning',
          message: 'High memory usage detected on worker node 3',
          timestamp: new Date(Date.now() - 3600000),
          resolved: false,
        },
        {
          id: '2',
          severity: 'info',
          message: 'Scheduled maintenance window starts in 24 hours',
          timestamp: new Date(Date.now() - 7200000),
          resolved: false,
        },
        {
          id: '3',
          severity: 'success',
          message: 'Database backup completed successfully',
          timestamp: new Date(Date.now() - 14400000),
          resolved: true,
        },
      ]);
    }
  }, []);

  // Subscribe to real-time updates
  useEffect(() => {
    fetchMetrics();
    fetchAlerts();

    // Subscribe to Pusher channels for real-time updates
    const subscriptionId = pusherService.subscribe('admin-updates', (message) => {
      if (message.type === 'metrics-update') {
        setMetrics(message.payload);
      } else if (message.type === 'alert-new') {
        setAlerts((prev) => [message.payload, ...prev]);
      }
    });

    // Refresh metrics every 30 seconds
    const interval = setInterval(fetchMetrics, 30000);

    return () => {
      pusherService.unsubscribe(subscriptionId);
      clearInterval(interval);
    };
  }, [fetchMetrics, fetchAlerts]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleRefresh = () => {
    fetchMetrics();
    fetchAlerts();
  };

  const handleResolveAlert = async (alertId: string) => {
    try {
      await api.patch(`/api/v1/admin/alerts/${alertId}/resolve`);
      setAlerts((prev) =>
        prev.map((alert) =>
          alert.id === alertId ? { ...alert, resolved: true } : alert
        )
      );
    } catch (error) {
      console.error('Failed to resolve alert:', error);
    }
  };

  const getHealthColor = (health: number): 'success' | 'warning' | 'error' => {
    if (health >= 90) return 'success';
    if (health >= 70) return 'warning';
    return 'error';
  };

  const getHealthIcon = (health: number) => {
    if (health >= 90) return <CheckCircleIcon color="success" />;
    if (health >= 70) return <WarningIcon color="warning" />;
    return <ErrorIcon color="error" />;
  };

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 4 }}>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Admin Dashboard
        </Typography>
        <Typography variant="body2" color="text.secondary">
          System overview and management tools
        </Typography>
      </Box>

      {/* System Health Alert */}
      {metrics.systemHealth < 70 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          System health is below optimal levels. Please review system metrics and alerts.
        </Alert>
      )}

      {/* Quick Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Total Users
              </Typography>
              <Typography variant="h4">{metrics.totalUsers}</Typography>
              <Typography variant="body2" color="success.main">
                +12% from last month
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Active Sessions
              </Typography>
              <Typography variant="h4">{metrics.activeSessions}</Typography>
              <Typography variant="body2" color="text.secondary">
                -5% from yesterday
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Content Generated
              </Typography>
              <Typography variant="h4">{metrics.contentGenerated}</Typography>
              <Typography variant="body2" color="success.main">
                +23% this week
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Typography variant="subtitle2" color="text.secondary" sx={{ flexGrow: 1 }}>
                  System Health
                </Typography>
                {getHealthIcon(metrics.systemHealth)}
              </Box>
              <Typography variant="h4" component="div" gutterBottom>
                {metrics.systemHealth}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={metrics.systemHealth}
                color={getHealthColor(metrics.systemHealth)}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content Tabs */}
      <Paper sx={{ width: '100%', mb: 4 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider', position: 'relative' }}>
          <Tabs value={activeTab} onChange={handleTabChange} aria-label="admin tabs">
            <Tab icon={<DashboardIcon />} label="Overview" />
            <Tab icon={<PeopleIcon />} label="Users" />
            <Tab icon={<SchoolIcon />} label="Content" />
            <Tab icon={<SecurityIcon />} label="Security" />
            <Tab icon={<SettingsIcon />} label="Settings" />
          </Tabs>
          <Box sx={{ position: 'absolute', right: 16, top: 8 }}>
            <Tooltip title="Refresh">
              <IconButton onClick={handleRefresh} disabled={refreshing}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        <TabPanel value={activeTab} index={0}>
          {/* Overview Tab */}
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              {/* System Performance */}
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    System Performance
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Box sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">CPU Usage</Typography>
                          <Typography variant="body2">{metrics.cpuUsage}%</Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={metrics.cpuUsage}
                          color={metrics.cpuUsage > 80 ? 'error' : 'primary'}
                        />
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Box sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">Memory Usage</Typography>
                          <Typography variant="body2">{metrics.memoryUsage}%</Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={metrics.memoryUsage}
                          color={metrics.memoryUsage > 80 ? 'error' : 'primary'}
                        />
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Box sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">Storage Usage</Typography>
                          <Typography variant="body2">{metrics.storageUsage}%</Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={metrics.storageUsage}
                          color={metrics.storageUsage > 90 ? 'error' : 'primary'}
                        />
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Box sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">API Latency</Typography>
                          <Typography variant="body2">{metrics.apiLatency}ms</Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={Math.min((metrics.apiLatency / 1000) * 100, 100)}
                          color={metrics.apiLatency > 500 ? 'error' : 'primary'}
                        />
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>

              {/* Recent Activity Placeholder */}
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Recent Activity
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Activity feed will be displayed here
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              {/* System Alerts */}
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    System Alerts
                  </Typography>
                  <List>
                    {alerts.slice(0, 5).map((alert) => (
                      <ListItem
                        key={alert.id}
                        secondaryAction={
                          !alert.resolved && (
                            <IconButton
                              edge="end"
                              aria-label="resolve"
                              onClick={() => handleResolveAlert(alert.id)}
                            >
                              <CheckCircleIcon />
                            </IconButton>
                          )
                        }
                      >
                        <ListItemAvatar>
                          <Avatar
                            sx={{
                              bgcolor:
                                alert.severity === 'error'
                                  ? 'error.main'
                                  : alert.severity === 'warning'
                                  ? 'warning.main'
                                  : 'info.main',
                            }}
                          >
                            {alert.severity === 'error' ? (
                              <ErrorIcon />
                            ) : alert.severity === 'warning' ? (
                              <WarningIcon />
                            ) : (
                              <CheckCircleIcon />
                            )}
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={alert.message}
                          secondary={formatDistanceToNow(new Date(alert.timestamp), {
                            addSuffix: true,
                          })}
                          sx={{
                            textDecoration: alert.resolved ? 'line-through' : 'none',
                            opacity: alert.resolved ? 0.6 : 1,
                          }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          {/* Users Tab */}
          <Typography variant="h6">User Management</Typography>
          <Typography variant="body2" color="text.secondary">
            User management panel will be implemented here
          </Typography>
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          {/* Content Tab */}
          <Typography variant="h6">Content Moderation</Typography>
          <Typography variant="body2" color="text.secondary">
            Content moderation panel will be implemented here
          </Typography>
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          {/* Security Tab */}
          <Typography variant="h6">Security Settings</Typography>
          <Typography variant="body2" color="text.secondary">
            Security monitoring panel will be implemented here
          </Typography>
        </TabPanel>

        <TabPanel value={activeTab} index={4}>
          {/* Settings Tab */}
          <Typography variant="h6">System Settings</Typography>
          <Typography variant="body2" color="text.secondary">
            System settings panel will be implemented here
          </Typography>
        </TabPanel>
      </Paper>

      {/* Quick Actions */}
      <Grid container spacing={2}>
        <Grid item>
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            onClick={() => console.log('Export logs')}
          >
            Export Logs
          </Button>
        </Grid>
        <Grid item>
          <Button
            variant="outlined"
            startIcon={<UploadIcon />}
            onClick={() => console.log('Backup system')}
          >
            Backup System
          </Button>
        </Grid>
        <Grid item>
          <Button
            variant="outlined"
            color="error"
            startIcon={<WarningIcon />}
            onClick={() => console.log('Clear cache')}
          >
            Clear Cache
          </Button>
        </Grid>
      </Grid>
    </Box>
  );
}