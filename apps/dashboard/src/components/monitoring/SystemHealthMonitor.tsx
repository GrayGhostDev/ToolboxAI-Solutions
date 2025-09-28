/**
 * SystemHealthMonitor Component
 * Real-time monitoring of system health metrics
 */
import { memo, useEffect, useState, useMemo } from 'react';
import {
  Card,
  Grid,
  Stack,
  Progress,
  Badge,
  ActionIcon,
  Tooltip,
  Alert,
  Button,
  Collapse,
  List,
  Group,
  Text,
  Title,
  useMantineTheme,
  alpha,
  Paper,
  Box,
} from '@mantine/core';

import {
  IconCpu as CPUIcon,
  IconMemory as MemoryIcon,
  IconHdd as StorageIcon,
  IconCloud as NetworkIcon,
  IconDatabase as DatabaseIcon,
  IconApi as APIIcon,
  IconCircleCheck as HealthyIcon,
  IconAlertTriangle as WarningIcon,
  IconX as ErrorIcon,
  IconRefresh as RefreshIcon,
  IconChevronDown as ExpandIcon,
  IconChevronUp as CollapseIcon,
  IconTrendingUp,
  IconTrendingDown,
} from '@tabler/icons-react';
import { AreaChart, Area, Tooltip as ResponsiveContainer } from 'recharts';
import { motion } from 'framer-motion';
import { usePusher } from '@/hooks/usePusher';
export interface SystemMetric {
  name: string;
  value: number;
  unit: string;
  status: 'healthy' | 'warning' | 'critical';
  threshold?: {
    warning: number;
    critical: number;
  };
  history?: Array<{ time: string; value: number }>;
}
export interface ServiceStatus {
  name: string;
  status: 'online' | 'offline' | 'degraded';
  uptime?: string;
  lastCheck: string;
  responseTime?: number;
  error?: string;
}
export interface SystemHealthMonitorProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
  showCharts?: boolean;
  compact?: boolean;
  onMetricClick?: (metric: SystemMetric) => void;
  onServiceClick?: (service: ServiceStatus) => void;
}
const MotionPaper = motion(Paper);
export const SystemHealthMonitor = memo<SystemHealthMonitorProps>(({
  autoRefresh = true,
  refreshInterval = 30000, // 30 seconds
  showCharts = true,
  compact = false,
  onMetricClick,
  onServiceClick,
}) => {
  const theme = useMantineTheme();
  const [expanded, setExpanded] = useState(!compact);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  // System metrics
  const [metrics, setMetrics] = useState<Record<string, SystemMetric>>({
    cpu: {
      name: 'CPU Usage',
      value: 45,
      unit: '%',
      status: 'healthy',
      threshold: { warning: 70, critical: 90 },
      history: Array.from({ length: 10 }, (_, i) => ({
        time: `${i}m ago`,
        value: 40 + Math.random() * 20,
      })),
    },
    memory: {
      name: 'Memory',
      value: 62,
      unit: '%',
      status: 'warning',
      threshold: { warning: 60, critical: 80 },
      history: Array.from({ length: 10 }, (_, i) => ({
        time: `${i}m ago`,
        value: 55 + Math.random() * 15,
      })),
    },
    storage: {
      name: 'Storage',
      value: 35,
      unit: '%',
      status: 'healthy',
      threshold: { warning: 70, critical: 85 },
      history: Array.from({ length: 10 }, (_, i) => ({
        time: `${i}m ago`,
        value: 30 + Math.random() * 10,
      })),
    },
    network: {
      name: 'Network I/O',
      value: 120,
      unit: 'Mbps',
      status: 'healthy',
      history: Array.from({ length: 10 }, (_, i) => ({
        time: `${i}m ago`,
        value: 100 + Math.random() * 50,
      })),
    },
  });
  // Service statuses
  const [services, setServices] = useState<ServiceStatus[]>([
    {
      name: 'Database',
      status: 'online',
      uptime: '99.95%',
      lastCheck: new Date().toISOString(),
      responseTime: 12,
    },
    {
      name: 'Redis Cache',
      status: 'online',
      uptime: '99.99%',
      lastCheck: new Date().toISOString(),
      responseTime: 2,
    },
    {
      name: 'API Gateway',
      status: 'online',
      uptime: '99.90%',
      lastCheck: new Date().toISOString(),
      responseTime: 45,
    },
    {
      name: 'Pusher Realtime',
      status: 'online',
      uptime: '99.87%',
      lastCheck: new Date().toISOString(),
      responseTime: 8,
    },
    {
      name: 'Storage Service',
      status: 'degraded',
      uptime: '98.50%',
      lastCheck: new Date().toISOString(),
      responseTime: 250,
      error: 'High latency detected',
    },
  ]);
  // Setup Pusher for real-time updates
  const { service: pusherService, isConnected } = usePusher();
  useEffect(() => {
    const channel = 'system-health';
    const handleMetricUpdate = (data: { metric: string; value: SystemMetric }) => {
      setMetrics(prev => ({
        ...prev,
        [data.metric]: data.value,
      }));
    };
    const handleServiceUpdate = (data: ServiceStatus[]) => {
      setServices(data);
    };
    if (!isConnected) return;

    const subscriptions = [
      pusherService.subscribe(channel, (message) => {
        if (message.type === 'metric-update') {
          handleMetricUpdate(message.payload);
        } else if (message.type === 'service-status') {
          handleServiceUpdate(message.payload);
        }
      })
    ];

    return () => {
      subscriptions.forEach(id => pusherService.unsubscribe(id));
    };
  }, [pusherService, isConnected]);
  // Auto-refresh
  useEffect(() => {
    if (autoRefresh) {
      const fetchHealthData = async () => {
        try {
          setLoading(true);
          // In a real app, this would fetch from the API
          // const response = await api.get('/admin/system-health');
          // setMetrics(response.data.metrics);
          // setServices(response.data.services);
          setLastUpdate(new Date());
        } catch (err) {
          setError('Failed to fetch system health data');
        } finally {
          setLoading(false);
        }
      };
      fetchHealthData();
      const interval = setInterval(fetchHealthData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);
  const overallHealth = useMemo(() => {
    const criticalCount = Object.values(metrics).filter(m => m.status === 'critical').length;
    const warningCount = Object.values(metrics).filter(m => m.status === 'warning').length;
    const offlineCount = services.filter(s => s.status === 'offline').length;
    const degradedCount = services.filter(s => s.status === 'degraded').length;
    if (criticalCount > 0 || offlineCount > 0) {
      return 'critical';
    }
    if (warningCount > 0 || degradedCount > 0) {
      return 'warning';
    }
    return 'healthy';
  }, [metrics, services]);
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'online':
        return theme.colors.green[6];
      case 'warning':
      case 'degraded':
        return theme.colors.yellow[6];
      case 'critical':
      case 'offline':
        return theme.colors.red[6];
      default:
        return theme.colors.gray[6];
    }
  };
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'online':
        return <HealthyIcon size={16} />;
      case 'warning':
      case 'degraded':
        return <WarningIcon size={16} />;
      case 'critical':
      case 'offline':
        return <ErrorIcon size={16} />;
      default:
        return null;
    }
  };
  const getMetricIcon = (metric: string) => {
    switch (metric) {
      case 'cpu':
        return <CPUIcon />;
      case 'memory':
        return <MemoryIcon />;
      case 'storage':
        return <StorageIcon />;
      case 'network':
        return <NetworkIcon />;
      default:
        return <DatabaseIcon />;
    }
  };
  const handleRefresh = async () => {
    setLoading(true);
    try {
      // Fetch latest data
      setLastUpdate(new Date());
    } catch (err) {
      setError('Failed to refresh');
    } finally {
      setLoading(false);
    }
  };
  return (
    <MotionPaper
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
    >
      {/* Header */}
      <Box p="md" style={{ borderBottom: `1px solid ${theme.colors.gray[3]}` }}>
        <Group justify="space-between">
          <Group>
            <Title order={4}>
              System Health
            </Title>
            <Badge
              color={
                overallHealth === 'healthy'
                  ? 'green'
                  : overallHealth === 'warning'
                  ? 'yellow'
                  : 'red'
              }
              leftSection={getStatusIcon(overallHealth)}
            >
              {overallHealth.toUpperCase()}
            </Badge>
          </Group>
          <Group gap="xs">
            <Tooltip label="Last updated">
              <Text size="xs" c="dimmed">
                {lastUpdate.toLocaleTimeString()}
              </Text>
            </Tooltip>
            <ActionIcon size="sm" onClick={handleRefresh} disabled={loading}>
              <RefreshIcon size={16} />
            </ActionIcon>
            <ActionIcon size="sm" onClick={() => setExpanded(!expanded)}>
              {expanded ? <CollapseIcon size={16} /> : <ExpandIcon size={16} />}
            </ActionIcon>
          </Group>
        </Group>
      </Box>
      <Collapse in={expanded}>
        <Box p="md" style={{ flex: 1, overflow: 'auto' }}>
          {error && (
            <Alert color="red" mb="md">
              {error}
            </Alert>
          )}
          {/* System Metrics */}
          <Text fw={600} mb="md">
            System Metrics
          </Text>
          <Grid mb="lg">
            {Object.entries(metrics).map(([key, metric]) => (
              <Grid.Col span={{ base: 12, sm: 6, md: 3 }} key={key}>
                <Card
                  padding="md"
                  withBorder
                  style={{
                    cursor: onMetricClick ? 'pointer' : 'default',
                    borderLeft: `4px solid ${getStatusColor(metric.status)}`,
                  }}
                  onClick={() => onMetricClick?.(metric)}
                >
                  <Stack gap="xs">
                    <Group gap="xs">
                      <Box style={{ color: getStatusColor(metric.status) }}>
                        {getMetricIcon(key)}
                      </Box>
                      <Text size="sm" c="dimmed">
                        {metric.name}
                      </Text>
                    </Group>
                    <Group gap="xs" align="baseline">
                      <Text size="xl" fw={700}>
                        {metric.value}
                      </Text>
                      <Text size="sm" c="dimmed">
                        {metric.unit}
                      </Text>
                    </Group>
                    {metric.threshold && (
                      <Progress
                        value={(metric.value / metric.threshold.critical) * 100}
                        color={
                          metric.status === 'healthy'
                            ? 'green'
                            : metric.status === 'warning'
                            ? 'yellow'
                            : 'red'
                        }
                        size="sm"
                        radius="xs"
                      />
                    )}
                    {showCharts && metric.history && (
                      <Box style={{ height: 60, marginTop: 8 }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={metric.history}>
                            <Area
                              type="monotone"
                              dataKey="value"
                              stroke={getStatusColor(metric.status)}
                              fill={alpha(getStatusColor(metric.status), 0.2)}
                              strokeWidth={2}
                            />
                          </AreaChart>
                        </ResponsiveContainer>
                      </Box>
                    )}
                  </Stack>
                </Card>
              </Grid.Col>
            ))}
          </Grid>
          {/* Service Status */}
          <Text fw={600} mb="md">
            Service Status
          </Text>
          <Stack gap="xs">
            {services.map(service => (
              <Card
                key={service.name}
                padding="md"
                withBorder
                style={{
                  cursor: onServiceClick ? 'pointer' : 'default',
                  backgroundColor:
                    service.status === 'offline'
                      ? alpha(theme.colors.red[6], 0.05)
                      : service.status === 'degraded'
                      ? alpha(theme.colors.yellow[6], 0.05)
                      : 'transparent',
                }}
                onClick={() => onServiceClick?.(service)}
              >
                <Group gap="md" align="flex-start">
                  <Box style={{ color: getStatusColor(service.status) }}>
                    {getStatusIcon(service.status)}
                  </Box>
                  <Stack gap="xs" style={{ flex: 1 }}>
                    <Text fw={500}>{service.name}</Text>
                    <Group gap="md">
                      <Text size="xs" c="dimmed">
                        Status: {service.status}
                      </Text>
                      {service.uptime && (
                        <Text size="xs" c="dimmed">
                          Uptime: {service.uptime}
                        </Text>
                      )}
                      {service.responseTime && (
                        <Text size="xs" c="dimmed">
                          Response: {service.responseTime}ms
                        </Text>
                      )}
                      {service.error && (
                        <Text size="xs" c="red">
                          {service.error}
                        </Text>
                      )}
                    </Group>
                  </Stack>
                </Group>
              </Card>
            ))}
          </Stack>
        </Box>
      </Collapse>
    </MotionPaper>
  );
});
SystemHealthMonitor.displayName = 'SystemHealthMonitor';
export default SystemHealthMonitor;