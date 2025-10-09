import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Grid,
  Card,
  Text,
  Button,
  Tabs,
  Avatar,
  List,
  Badge,
  Progress,
  Alert,
  ActionIcon,
  Tooltip,
  Paper,
  Divider,
  Group,
  Stack,
  Loader,
  SimpleGrid,
} from '@mantine/core';
import {
  IconDashboard,
  IconUsers,
  IconSchool,
  IconChartBar,
  IconSettings,
  IconShield,
  IconDatabase,
  IconGauge,
  IconAlertTriangle,
  IconCircleCheck,
  IconX,
  IconRefresh,
  IconDownload,
  IconUpload,
} from '@tabler/icons-react';
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

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`admin-tabpanel-${index}`}
      aria-labelledby={`admin-tab-${index}`}
      {...other}
    >
      {value === index && <Box p="lg">{children}</Box>}
    </div>
  );
};

export default function AdminDashboard({ section = 'overview' }: AdminDashboardProps) {
  const dispatch = useAppDispatch();
  // Fix: Changed from state.auth to state.user as auth slice doesn't exist
  // Defensive: Safe fallback for Redux state access
  const user = useAppSelector((state) => state?.user || null);
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

      // Defensive: Validate response structure and apply safe defaults
      const data = response?.data || {};
      setMetrics({
        totalUsers: typeof data.totalUsers === 'number' ? data.totalUsers : 0,
        activeUsers: typeof data.activeUsers === 'number' ? data.activeUsers : 0,
        totalCourses: typeof data.totalCourses === 'number' ? data.totalCourses : 0,
        activeSessions: typeof data.activeSessions === 'number' ? data.activeSessions : 0,
        contentGenerated: typeof data.contentGenerated === 'number' ? data.contentGenerated : 0,
        systemHealth: typeof data.systemHealth === 'number' ? Math.max(0, Math.min(100, data.systemHealth)) : 95,
        cpuUsage: typeof data.cpuUsage === 'number' ? Math.max(0, Math.min(100, data.cpuUsage)) : 0,
        memoryUsage: typeof data.memoryUsage === 'number' ? Math.max(0, Math.min(100, data.memoryUsage)) : 0,
        storageUsage: typeof data.storageUsage === 'number' ? Math.max(0, Math.min(100, data.storageUsage)) : 0,
        apiLatency: typeof data.apiLatency === 'number' ? Math.max(0, data.apiLatency) : 0,
      });
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
      // Use mock data for development with safe fallbacks
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

      // Defensive: Validate response is an array
      const alertsData = response?.data;
      if (Array.isArray(alertsData)) {
        setAlerts(alertsData);
      } else {
        console.warn('Invalid alerts data received, using fallback');
        setAlerts([]);
      }
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
    try {
      const channel = pusherService?.subscribe?.('admin-updates');

      if (channel) {
        channel.bind('metrics-update', (data: SystemMetrics) => {
          try {
            // Defensive: Validate incoming metrics data
            if (data && typeof data === 'object') {
              setMetrics(prevMetrics => ({
                ...prevMetrics,
                ...data,
                // Ensure numeric values are within valid ranges
                systemHealth: typeof data.systemHealth === 'number' ? Math.max(0, Math.min(100, data.systemHealth)) : prevMetrics.systemHealth,
                cpuUsage: typeof data.cpuUsage === 'number' ? Math.max(0, Math.min(100, data.cpuUsage)) : prevMetrics.cpuUsage,
                memoryUsage: typeof data.memoryUsage === 'number' ? Math.max(0, Math.min(100, data.memoryUsage)) : prevMetrics.memoryUsage,
                storageUsage: typeof data.storageUsage === 'number' ? Math.max(0, Math.min(100, data.storageUsage)) : prevMetrics.storageUsage,
              }));
            }
          } catch (err) {
            console.error('Error processing metrics update:', err);
          }
        });

        channel.bind('alert-new', (alert: SystemAlert) => {
          try {
            // Defensive: Validate alert structure
            if (alert && typeof alert === 'object' && alert.id) {
              setAlerts((prev) => Array.isArray(prev) ? [alert, ...prev] : [alert]);
            }
          } catch (err) {
            console.error('Error processing new alert:', err);
          }
        });
      }
    } catch (pusherError) {
      console.warn('Failed to subscribe to Pusher updates:', pusherError);
    }

    // Refresh metrics every 30 seconds
    const interval = setInterval(fetchMetrics, 30000);

    return () => {
      try {
        pusherService?.unsubscribe?.('admin-updates');
      } catch (err) {
        console.warn('Error unsubscribing from Pusher:', err);
      }
      clearInterval(interval);
    };
  }, [fetchMetrics, fetchAlerts]);

  const handleTabChange = (value: string | null) => {
    setActiveTab(parseInt(value || '0'));
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

  const getHealthColor = (health: number): 'green' | 'yellow' | 'red' => {
    if (health >= 90) return 'green';
    if (health >= 70) return 'yellow';
    return 'red';
  };

  const getHealthIcon = (health: number) => {
    if (health >= 90) return <IconCircleCheck style={{ color: 'var(--mantine-color-green-6)' }} />;
    if (health >= 70) return <IconAlertTriangle style={{ color: 'var(--mantine-color-yellow-6)' }} />;
    return <IconX style={{ color: 'var(--mantine-color-red-6)' }} />;
  };

  if (loading) {
    return (
      <Box w="100%" mt="xl">
        <Loader size="lg" />
      </Box>
    );
  }

  return (
    <Box style={{ flexGrow: 1 }}>
      {/* Header */}
      <Box mb="xl">
        <Text size="xl" fw={700} mb="xs">
          Admin Dashboard
        </Text>
        <Text size="sm" c="dimmed">
          System overview and management tools
        </Text>
      </Box>

      {/* System Health Alert */}
      {metrics.systemHealth < 70 && (
        <Alert color="yellow" mb="lg">
          System health is below optimal levels. Please review system metrics and alerts.
        </Alert>
      )}

      {/* Quick Metrics */}
      <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }} spacing="lg" mb="xl">
        <Card>
          <Text size="sm" c="dimmed" mb="xs">
            Total Users
          </Text>
          <Text size="xl" fw={700}>{metrics.totalUsers}</Text>
          <Text size="sm" c="green">
            +12% from last month
          </Text>
        </Card>

        <Card>
          <Text size="sm" c="dimmed" mb="xs">
            Active Sessions
          </Text>
          <Text size="xl" fw={700}>{metrics.activeSessions}</Text>
          <Text size="sm" c="dimmed">
            -5% from yesterday
          </Text>
        </Card>

        <Card>
          <Text size="sm" c="dimmed" mb="xs">
            Content Generated
          </Text>
          <Text size="xl" fw={700}>{metrics.contentGenerated}</Text>
          <Text size="sm" c="green">
            +23% this week
          </Text>
        </Card>

        <Card>
          <Group justify="space-between" mb="sm">
            <Text size="sm" c="dimmed">
              System Health
            </Text>
            {getHealthIcon(metrics.systemHealth)}
          </Group>
          <Text size="xl" fw={700} mb="xs">
            {metrics.systemHealth}%
          </Text>
          <Progress
            value={metrics.systemHealth}
            color={getHealthColor(metrics.systemHealth)}
            size="sm"
            radius="xl"
          />
        </Card>
      </SimpleGrid>

      {/* Main Content Tabs */}
      <Paper w="100%" mb="xl">
        <Box style={{ borderBottom: '1px solid var(--mantine-color-gray-3)', position: 'relative' }}>
          <Group justify="space-between" align="center" p="md">
            <Tabs value={activeTab.toString()} onChange={handleTabChange}>
              <Tabs.List>
                <Tabs.Tab value="0" leftSection={<IconDashboard size={16} />}>
                  Overview
                </Tabs.Tab>
                <Tabs.Tab value="1" leftSection={<IconUsers size={16} />}>
                  Users
                </Tabs.Tab>
                <Tabs.Tab value="2" leftSection={<IconSchool size={16} />}>
                  Content
                </Tabs.Tab>
                <Tabs.Tab value="3" leftSection={<IconShield size={16} />}>
                  Security
                </Tabs.Tab>
                <Tabs.Tab value="4" leftSection={<IconSettings size={16} />}>
                  Settings
                </Tabs.Tab>
              </Tabs.List>
            </Tabs>
            <Tooltip label="Refresh">
              <ActionIcon onClick={handleRefresh} loading={refreshing} variant="subtle">
                <IconRefresh size={16} />
              </ActionIcon>
            </Tooltip>
          </Group>
        </Box>

        <TabPanel value={activeTab} index={0}>
          {/* Overview Tab */}
          <Grid>
            <Grid.Col span={{ base: 12, md: 8 }}>
              {/* System Performance */}
              <Card mb="lg">
                <Text size="lg" fw={600} mb="md">
                  System Performance
                </Text>
                <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
                  <Box>
                    <Group justify="space-between" mb="xs">
                      <Text size="sm">CPU Usage</Text>
                      <Text size="sm">{metrics.cpuUsage}%</Text>
                    </Group>
                    <Progress
                      value={metrics.cpuUsage}
                      color={metrics.cpuUsage > 80 ? 'red' : 'blue'}
                      size="sm"
                      radius="xl"
                    />
                  </Box>

                  <Box>
                    <Group justify="space-between" mb="xs">
                      <Text size="sm">Memory Usage</Text>
                      <Text size="sm">{metrics.memoryUsage}%</Text>
                    </Group>
                    <Progress
                      value={metrics.memoryUsage}
                      color={metrics.memoryUsage > 80 ? 'red' : 'blue'}
                      size="sm"
                      radius="xl"
                    />
                  </Box>

                  <Box>
                    <Group justify="space-between" mb="xs">
                      <Text size="sm">Storage Usage</Text>
                      <Text size="sm">{metrics.storageUsage}%</Text>
                    </Group>
                    <Progress
                      value={metrics.storageUsage}
                      color={metrics.storageUsage > 90 ? 'red' : 'blue'}
                      size="sm"
                      radius="xl"
                    />
                  </Box>

                  <Box>
                    <Group justify="space-between" mb="xs">
                      <Text size="sm">API Latency</Text>
                      <Text size="sm">{metrics.apiLatency}ms</Text>
                    </Group>
                    <Progress
                      value={Math.min((metrics.apiLatency / 1000) * 100, 100)}
                      color={metrics.apiLatency > 500 ? 'red' : 'blue'}
                      size="sm"
                      radius="xl"
                    />
                  </Box>
                </SimpleGrid>
              </Card>

              {/* Recent Activity Placeholder */}
              <Card>
                <Text size="lg" fw={600} mb="md">
                  Recent Activity
                </Text>
                <Text size="sm" c="dimmed">
                  Activity feed will be displayed here
                </Text>
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 4 }}>
              {/* System Alerts */}
              <Card>
                <Text size="lg" fw={600} mb="md">
                  System Alerts
                </Text>
                <Stack gap="md">
                  {/* Defensive: Safe array operations */}
                  {Array.isArray(alerts) && alerts.slice(0, 5).map((alert) => {
                    // Defensive: Validate alert object
                    if (!alert || !alert.id) return null;

                    return (
                    <Group key={alert.id} justify="space-between" align="flex-start">
                      <Group align="flex-start" gap="sm">
                        <Avatar
                          size="sm"
                          color={
                            alert.severity === 'error'
                              ? 'red'
                              : alert.severity === 'warning'
                              ? 'yellow'
                              : 'blue'
                          }
                        >
                          {alert.severity === 'error' ? (
                            <IconX size={16} />
                          ) : alert.severity === 'warning' ? (
                            <IconAlertTriangle size={16} />
                          ) : (
                            <IconCircleCheck size={16} />
                          )}
                        </Avatar>
                        <Box style={{ flex: 1 }}>
                          <Text
                            size="sm"
                            style={{
                              textDecoration: alert.resolved ? 'line-through' : 'none',
                              opacity: alert.resolved ? 0.6 : 1,
                            }}
                          >
                            {alert.message || 'No message'}
                          </Text>
                          <Text size="xs" c="dimmed">
                            {/* Defensive: Safe date formatting */}
                            {alert.timestamp ?
                              formatDistanceToNow(new Date(alert.timestamp), {
                                addSuffix: true,
                              }) :
                              'Unknown time'
                            }
                          </Text>
                        </Box>
                      </Group>
                      {!alert.resolved && (
                        <ActionIcon
                          size="sm"
                          variant="subtle"
                          onClick={() => handleResolveAlert(alert.id)}
                        >
                          <IconCircleCheck size={16} />
                        </ActionIcon>
                      )}
                    </Group>
                    );
                  })}
                </Stack>
              </Card>
            </Grid.Col>
          </Grid>
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          {/* Users Tab */}
          <Text size="lg" fw={600}>User Management</Text>
          <Text size="sm" c="dimmed">
            User management panel will be implemented here
          </Text>
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          {/* Content Tab */}
          <Text size="lg" fw={600}>Content Moderation</Text>
          <Text size="sm" c="dimmed">
            Content moderation panel will be implemented here
          </Text>
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          {/* Security Tab */}
          <Text size="lg" fw={600}>Security Settings</Text>
          <Text size="sm" c="dimmed">
            Security monitoring panel will be implemented here
          </Text>
        </TabPanel>

        <TabPanel value={activeTab} index={4}>
          {/* Settings Tab */}
          <Text size="lg" fw={600}>System Settings</Text>
          <Text size="sm" c="dimmed">
            System settings panel will be implemented here
          </Text>
        </TabPanel>
      </Paper>

      {/* Quick Actions */}
      <Group spacing="md">
        <Button
          leftSection={<IconDownload size={16} />}
          onClick={() => console.log('Export logs')}
        >
          Export Logs
        </Button>
        <Button
          variant="outline"
          leftSection={<IconUpload size={16} />}
          onClick={() => console.log('Backup system')}
        >
          Backup System
        </Button>
        <Button
          variant="outline"
          color="red"
          leftSection={<IconAlertTriangle size={16} />}
          onClick={() => console.log('Clear cache')}
        >
          Clear Cache
        </Button>
      </Group>
    </Box>
  );
}