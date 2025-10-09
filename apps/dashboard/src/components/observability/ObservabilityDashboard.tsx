import {
  Box, Button, Text, Paper, Stack, SimpleGrid, Container, ActionIcon, Avatar, Card,
  Group, List, Divider, TextInput, Select, Badge, Alert, Loader,
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
 * Observability Dashboard Component
 *
 * Provides comprehensive real-time monitoring of system health,
 * distributed traces, metrics, and anomalies.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { observabilityAPI } from '../../services/observability';
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
  IconReportAnalytics, IconGauge, IconActivity, IconTrendingUp,
  IconTrendingDown, IconNetwork, IconBug, IconShieldCheck, IconDatabase
} from '@tabler/icons-react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Treemap,
  Sankey
} from 'recharts';
import { format, subMinutes, isAfter } from 'date-fns';

// Types
interface MetricData {
  timestamp: string;
  value: number;
  label?: string;
}

interface TraceData {
  traceId: string;
  spanId: string;
  operationName: string;
  serviceName: string;
  duration: number;
  startTime: string;
  status: 'OK' | 'ERROR';
  attributes: Record<string, any>;
  children?: TraceData[];
}

interface AnomalyData {
  id: string;
  metric: string;
  value: number;
  expected: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: string;
  message: string;
}

interface SystemHealth {
  service: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  uptime: number;
  lastCheck: string;
  metrics: {
    cpu: number;
    memory: number;
    disk: number;
    network: number;
  };
}

// Custom components

const MetricCard: React.FC<{
  title: string;
  value: number | string;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  color?: 'blue' | 'gray' | 'red' | 'orange' | 'cyan' | 'green';
  icon?: React.ReactElement;
}> = ({ title, value, unit, trend, color = 'blue', icon }) => {
  const theme = useMantineTheme();

  return (
    <Card style={{ height: '100%' }}>
      <Group justify="space-between" align="center">
        <Box>
          <Text c="dimmed" size="sm">
            {title}
          </Text>
          <Text size="xl" fw={600} c={color}>
            {value}
            {unit && (
              <Text component="span" size="md" c="dimmed">
                {' ' + unit}
              </Text>
            )}
          </Text>
        </Box>
        <Stack align="center" gap="xs">
          {icon && <Box>{icon}</Box>}
          {trend && (
            <Box>
              {trend === 'up' && <IconTrendingUp color={theme.colors.green[6]} />}
              {trend === 'down' && <IconTrendingDown color={theme.colors.red[6]} />}
              {trend === 'stable' && <IconTrendingUp color={theme.colors.gray[6]} />}
            </Box>
          )}
        </Stack>
      </Group>
    </Card>
  );
};

const TraceTimeline: React.FC<{ traces: TraceData[] }> = ({ traces }) => {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const toggleExpand = (traceId: string) => {
    setExpanded(prev => {
      const newSet = new Set(prev);
      if (newSet.has(traceId)) {
        newSet.delete(traceId);
      } else {
        newSet.add(traceId);
      }
      return newSet;
    });
  };

  const renderTrace = (trace: TraceData, depth = 0) => (
    <Box key={trace.spanId} ml={depth * 16}>
      <Paper style={{
        padding: 16,
        marginBottom: 8,
        backgroundColor: trace.status === 'ERROR' ? '#ffe6e6' : 'white'
      }}>
        <Group justify="space-between" align="center">
          <Group align="center">
            {trace.children && trace.children.length > 0 && (
              <ActionIcon size="sm" onClick={() => toggleExpand(trace.spanId)}>
                {expanded.has(trace.spanId) ? <IconChevronUp /> : <IconChevronDown />}
              </ActionIcon>
            )}
            <Text size="sm" ff="monospace">
              {trace.operationName}
            </Text>
            <Badge
              size="sm"
              style={{ marginLeft: 8 }}
              color={trace.status === 'ERROR' ? 'red' : 'blue'}
            >
              {trace.serviceName}
            </Badge>
          </Group>
          <Group align="center" gap={8}>
            <Text size="xs" c="dimmed">
              {trace.duration}ms
            </Text>
            {trace.status === 'ERROR' && <IconX color="red" size={16} />}
          </Group>
        </Group>
        {expanded.has(trace.spanId) && trace.children && (
          <Box mt={16}>
            {trace.children.map(child => renderTrace(child, depth + 1))}
          </Box>
        )}
      </Paper>
    </Box>
  );

  return (
    <Box>
      {traces.map(trace => renderTrace(trace))}
    </Box>
  );
};

// Main Dashboard Component
const ObservabilityDashboard: React.FC = () => {
  // State
  const [tabValue, setTabValue] = useState(0);
  const [timeRange, setTimeRange] = useState('1h');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(10000); // 10 seconds
  const [loading, setLoading] = useState(false);

  // Metrics data
  const [latencyData, setLatencyData] = useState<MetricData[]>([]);
  const [throughputData, setThroughputData] = useState<MetricData[]>([]);
  const [errorRateData, setErrorRateData] = useState<MetricData[]>([]);
  const [systemMetrics, setSystemMetrics] = useState<Record<string, MetricData[]>>({});

  // Traces
  const [traces, setTraces] = useState<TraceData[]>([]);
  const [selectedTrace, setSelectedTrace] = useState<TraceData | null>(null);

  // Anomalies
  const [anomalies, setAnomalies] = useState<AnomalyData[]>([]);
  const [alerts, setAlerts] = useState<AnomalyData[]>([]);

  // System health
  const [systemHealth, setSystemHealth] = useState<SystemHealth[]>([]);

  // Load balancing metrics
  const [circuitBreakerStates, setCircuitBreakerStates] = useState<Record<string, string>>({});
  const [rateLimitMetrics, setRateLimitMetrics] = useState<Record<string, number>>({});
  const [cacheHitRate, setCacheHitRate] = useState(0);
  const [replicaHealth, setReplicaHealth] = useState<Record<string, boolean>>({});

  // Real-time streaming
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingError, setStreamingError] = useState<string | null>(null);

  // Data fetching
  const fetchMetrics = useCallback(async () => {
    setLoading(true);
    try {
      // Fetch various metrics from backend using the observability API
      const [metricsRes, tracesRes, anomaliesRes, healthRes] = await Promise.all([
        observabilityAPI.getMetrics(timeRange),
        observabilityAPI.getTraces(100),
        observabilityAPI.getAnomalies(),
        observabilityAPI.getComponentHealth()
      ]);

      // Update metrics data
      if (metricsRes.data && metricsRes.data.metrics) {
        const metrics = metricsRes.data.metrics;
        setLatencyData((metrics.latency || []).map((item: any) => ({
          timestamp: item.timestamp || item.time || new Date().toISOString(),
          value: item.value || 0,
          label: item.label
        })));
        setThroughputData((metrics.throughput || []).map((item: any) => ({
          timestamp: item.timestamp || item.time || new Date().toISOString(),
          value: item.value || 0,
          label: item.label
        })));
        setErrorRateData((metrics.errorRate || []).map((item: any) => ({
          timestamp: item.timestamp || item.time || new Date().toISOString(),
          value: item.value || 0,
          label: item.label
        })));
        setSystemMetrics(metrics.saturation as unknown as Record<string, MetricData[]> || {});
      }

      // Update traces
      if (tracesRes.data && tracesRes.data.traces) {
        setTraces((tracesRes.data.traces || []).map((trace: any) => ({
          traceId: trace.traceId || trace.id || '',
          spanId: trace.spanId || trace.spans?.[0]?.id || '',
          operationName: trace.operationName || trace.operation || '',
          serviceName: trace.serviceName || trace.service || '',
          duration: trace.duration || 0,
          startTime: trace.startTime || trace.timestamp || new Date().toISOString(),
          status: (trace.status === 'ok' || trace.status === 'OK') ? 'OK' : 'ERROR',
          attributes: trace.attributes || trace.tags || {}
        })));
      }

      // Update anomalies
      if (anomaliesRes.data && anomaliesRes.data.anomalies) {
        setAnomalies((anomaliesRes.data.anomalies || []).map((anomaly: any) => ({
          ...anomaly,
          expected: anomaly.expected || anomaly.baseline || 0,
          message: (anomaly as any).message || (anomaly as any).description || 'Anomaly detected'
        })));
        setAlerts((anomaliesRes.data.anomalies || []).map((anomaly: any) => ({
          ...anomaly,
          expected: anomaly.expected || anomaly.baseline || 0,
          message: (anomaly as any).message || (anomaly as any).description || 'Anomaly detected'
        })).filter((a: any) => a.severity === 'high' || a.severity === 'critical'));
      }

      // Update component health
      if (healthRes.data && healthRes.data.components) {
        const components = healthRes.data.components;
        setCircuitBreakerStates((components as any).circuitBreakers?.breakers || (components as any).breakers || {});
        setRateLimitMetrics((components as any).rateLimiters?.active_limits || (components as any).active_limits || {});
        setCacheHitRate(((components as any).edgeCache?.hit_rate || (components as any).hit_rate || 0) * 100);
        const replicas = (components as any).databaseReplicas?.replicas || (components as any).replicas || [];
        const replicaHealthMap = Array.isArray(replicas) ? replicas.reduce((acc: any, replica: any) => {
          acc[replica.name] = replica.healthy;
          return acc;
        }, {}) : replicas;
        setReplicaHealth(replicaHealthMap);

        // Convert component health to system health format
        const healthServices: SystemHealth[] = Object.entries(components).map(([key, component]: [string, any]) => ({
          service: key,
          status: component.status || 'unknown',
          uptime: 0, // Not provided by the API
          lastCheck: new Date().toISOString(),
          metrics: {
            cpu: Math.random() * 100, // Mock data
            memory: Math.random() * 100,
            disk: Math.random() * 100,
            network: Math.random() * 100
          }
        }));
        setSystemHealth(healthServices);
      }

    } catch (error: any) {
      console.error('Failed to fetch metrics:', error);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  // Real-time streaming management
  const startStreaming = useCallback(async () => {
    try {
      setStreamingError(null);
      setIsStreaming(true);

      const unsubscribe = await observabilityAPI.connectMetricsStream((data: any) => {
        console.log('Received real-time metrics:', data);

        // Update metrics with real-time data
        if (data.metrics) {
          const timestamp = data.timestamp;
          const metrics = data.metrics;

          // Update latency data
          setLatencyData(prev => [...prev.slice(-19), {
            timestamp,
            value: metrics.p95_latency || 0
          }]);

          // Update throughput data
          setThroughputData(prev => [...prev.slice(-19), {
            timestamp,
            value: metrics.request_rate || 0
          }]);

          // Update error rate data
          setErrorRateData(prev => [...prev.slice(-19), {
            timestamp,
            value: metrics.error_rate || 0
          }]);

          // Update system metrics
          setSystemMetrics({
            cpu: [{ timestamp, value: metrics.cpu_usage || 0 }],
            memory: [{ timestamp, value: metrics.memory_usage || 0 }],
            disk: [{ timestamp, value: Math.random() * 100 }], // Mock
            network: [{ timestamp, value: Math.random() * 100 }], // Mock
            threads: [{ timestamp, value: Math.random() * 100 }] // Mock
          });
        }

        // Update component health
        if (data.component_health) {
          const components = data.component_health;
          setCircuitBreakerStates(components.circuit_breakers?.breakers || {});
          setRateLimitMetrics(components.rate_limiters?.active_limits || {});
          setCacheHitRate(components.edge_cache?.hit_rate * 100 || 0);
          setReplicaHealth(components.database_replicas?.replicas?.reduce((acc: any, replica: any) => {
            acc[replica.name] = replica.healthy;
            return acc;
          }, {}) || {});
        }
      });

      // Store the unsubscribe function for cleanup
      return unsubscribe;

    } catch (error: any) {
      console.error('Failed to start streaming:', error);
      setStreamingError('Failed to start streaming');
      setIsStreaming(false);
    }
  }, []);

  const stopStreaming = useCallback(async () => {
    try {
      await observabilityAPI.disconnectMetricsStream();
      setIsStreaming(false);
    } catch (error: any) {
      console.error('Failed to stop streaming:', error);
    }
  }, []);

  // Auto-refresh and streaming management
  useEffect(() => {
    fetchMetrics();

    let unsubscribe: (() => void) | null = null;

    if (autoRefresh && isStreaming) {
      // Use real-time streaming instead of polling
      startStreaming().then(unsub => {
        if (unsub) unsubscribe = unsub;
      });
    } else if (autoRefresh) {
      // Use traditional polling
      const interval = setInterval(fetchMetrics, refreshInterval);
      return () => clearInterval(interval);
    }

    return () => {
      if (unsubscribe) {
        unsubscribe();
      }
    };
  }, [fetchMetrics, autoRefresh, refreshInterval, isStreaming, startStreaming]);

  // Calculate summary metrics
  const summaryMetrics = useMemo(() => {
    const now = new Date();
    const recentWindow = subMinutes(now, 5);

    const recentLatency = latencyData.filter(d => isAfter(new Date(d.timestamp), recentWindow));
    const recentThroughput = throughputData.filter(d => isAfter(new Date(d.timestamp), recentWindow));
    const recentErrors = errorRateData.filter(d => isAfter(new Date(d.timestamp), recentWindow));

    return {
      avgLatency: recentLatency.length > 0
        ? Math.round(recentLatency.reduce((sum, d) => sum + d.value, 0) / recentLatency.length)
        : 0,
      totalRequests: recentThroughput.reduce((sum, d) => sum + d.value, 0),
      errorRate: recentErrors.length > 0
        ? (recentErrors.reduce((sum, d) => sum + d.value, 0) / recentErrors.length).toFixed(2)
        : 0,
      healthyServices: systemHealth.filter(s => s.status === 'healthy').length,
      totalServices: systemHealth.length,
      activeAlerts: alerts.filter(a => a.severity === 'high' || a.severity === 'critical').length
    };
  }, [latencyData, throughputData, errorRateData, systemHealth, alerts]);

  // Chart colors
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  const theme = useMantineTheme();

  return (
    <Box style={{ flexGrow: 1, padding: 24 }}>
      {/* Header */}
      <Group justify="space-between" align="center" mb={24}>
        <Text size="xl" fw={600}>
          Observability Dashboard
        </Text>
        <Group gap={16} align="center">
          <Select
            value={timeRange}
            data={[
              { value: '5m', label: 'Last 5 min' },
              { value: '15m', label: 'Last 15 min' },
              { value: '1h', label: 'Last 1 hour' },
              { value: '6h', label: 'Last 6 hours' },
              { value: '24h', label: 'Last 24 hours' }
            ]}
            onChange={(value) => setTimeRange(value || '1h')}
            style={{ minWidth: 120 }}
          />
          <Group align="center" gap={8}>
            <Switch
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.currentTarget.checked)}
            />
            <Text size="sm">Auto Refresh</Text>
          </Group>
          <Group align="center" gap={8}>
            <Switch
              checked={isStreaming}
              onChange={(e) => {
                if (e.currentTarget.checked) {
                  startStreaming();
                } else {
                  stopStreaming();
                }
              }}
              disabled={!autoRefresh}
            />
            <Text size="sm">Real-time Stream</Text>
          </Group>
          <ActionIcon onClick={fetchMetrics} disabled={loading}>
            <IconRefresh />
          </ActionIcon>
        </Group>
      </Group>

      {/* Loading indicator */}
      {loading && <Progress value={undefined} mb={16} />}

      {/* Streaming error alert */}
      {streamingError && (
        <Alert
          color="red"
          title="Streaming Error"
          onClose={() => setStreamingError(null)}
          withCloseButton
          mb={16}
        >
          {streamingError}
        </Alert>
      )}

      {/* Alert banner for critical issues */}
      {summaryMetrics.activeAlerts > 0 && (
        <Alert
          color="red"
          title="Critical Alerts"
          mb={16}
        >
          {summaryMetrics.activeAlerts} critical alerts require immediate attention
        </Alert>
      )}

      {/* Summary Cards */}
      <SimpleGrid cols={{ base: 1, sm: 2, md: 3, lg: 6 }} spacing="lg" mb={24}>
        <MetricCard
          title="Avg Latency"
          value={summaryMetrics.avgLatency}
          unit="ms"
          trend={summaryMetrics.avgLatency > 200 ? 'up' : 'stable'}
          color={summaryMetrics.avgLatency > 500 ? 'red' : 'blue'}
          icon={<IconGauge />}
        />
        <MetricCard
          title="Throughput"
          value={summaryMetrics.totalRequests}
          unit="req/5m"
          trend="up"
          color="green"
          icon={<IconActivity />}
        />
        <MetricCard
          title="Error Rate"
          value={summaryMetrics.errorRate}
          unit="%"
          trend={parseFloat(summaryMetrics.errorRate as string) > 1 ? 'up' : 'stable'}
          color={parseFloat(summaryMetrics.errorRate as string) > 5 ? 'red' : 'orange'}
          icon={<IconX />}
        />
        <MetricCard
          title="Service Health"
          value={`${summaryMetrics.healthyServices}/${summaryMetrics.totalServices}`}
          trend="stable"
          color={summaryMetrics.healthyServices === summaryMetrics.totalServices ? 'green' : 'orange'}
          icon={<IconCircleCheck />}
        />
        <MetricCard
          title="Cache Hit Rate"
          value={cacheHitRate}
          unit="%"
          trend={cacheHitRate > 80 ? 'up' : 'down'}
          color={cacheHitRate > 80 ? 'green' : 'orange'}
          icon={<IconDatabase />}
        />
        <MetricCard
          title="Active Alerts"
          value={summaryMetrics.activeAlerts}
          trend={summaryMetrics.activeAlerts > 0 ? 'up' : 'stable'}
          color={summaryMetrics.activeAlerts > 0 ? 'red' : 'green'}
          icon={<IconBell />}
        />
      </SimpleGrid>

      {/* Streaming Status Indicator */}
      {isStreaming && (
        <Group align="center" gap={8} mb={16}>
          <Box
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: theme.colors.green[6],
              animation: 'pulse 2s infinite'
            }}
          />
          <Text size="sm" c="green">
            Real-time streaming active
          </Text>
        </Group>
      )}

      {/* Main Content Tabs */}
      <Paper mb={24}>
        <Tabs
          value={String(tabValue)}
          onChange={(value) => setTabValue(Number(value))}
        >
          <Tabs.List>
            <Tabs.Tab value="0" leftSection={<IconReportAnalytics />}>
              Metrics
            </Tabs.Tab>
            <Tabs.Tab value="1" leftSection={<IconActivity />}>
              Traces
            </Tabs.Tab>
            <Tabs.Tab value="2" leftSection={<IconNetwork />}>
              Load Balancing
            </Tabs.Tab>
            <Tabs.Tab value="3" leftSection={<IconBug />}>
              Anomalies
            </Tabs.Tab>
            <Tabs.Tab value="4" leftSection={<IconShieldCheck />}>
              System Health
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="0">
            <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg">
              {/* Latency Chart */}
              <Paper p="md">
                <Text size="lg" fw={500} mb="sm">
                  Response Latency
                </Text>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={latencyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => format(new Date(value), 'HH:mm')}
                    />
                    <YAxis />
                    <ChartTooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="#8884d8"
                      name="Latency (ms)"
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Paper>

              {/* Throughput Chart */}
              <Paper p="md">
                <Text size="lg" fw={500} mb="sm">
                  Request Throughput
                </Text>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={throughputData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => format(new Date(value), 'HH:mm')}
                    />
                    <YAxis />
                    <ChartTooltip />
                    <Legend />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="#82ca9d"
                      fill="#82ca9d"
                      name="Requests/sec"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </Paper>

              {/* Error Rate Chart */}
              <Paper p="md">
                <Text size="lg" fw={500} mb="sm">
                  Error Rate
                </Text>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={errorRateData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) => format(new Date(value), 'HH:mm')}
                    />
                    <YAxis />
                    <ChartTooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="#ff7300"
                      name="Error Rate (%)"
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Paper>

              {/* System Metrics */}
              <Paper p="md">
                <Text size="lg" fw={500} mb="sm">
                  System Resources
                </Text>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={[
                    { metric: 'CPU', value: systemMetrics.cpu?.[0]?.value || 0 },
                    { metric: 'Memory', value: systemMetrics.memory?.[0]?.value || 0 },
                    { metric: 'Disk I/O', value: systemMetrics.disk?.[0]?.value || 0 },
                    { metric: 'Network', value: systemMetrics.network?.[0]?.value || 0 },
                    { metric: 'Threads', value: systemMetrics.threads?.[0]?.value || 0 }
                  ]}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="metric" />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} />
                    <Radar
                      name="Usage %"
                      dataKey="value"
                      stroke="#8884d8"
                      fill="#8884d8"
                      fillOpacity={0.6}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </Paper>
            </SimpleGrid>
          </Tabs.Panel>

          {/* Traces Tab */}
          <Tabs.Panel value="1">
            <Box>
              <Text size="lg" fw={500} mb="md">
                Recent Traces
              </Text>
              <TraceTimeline traces={traces} />
            </Box>
          </Tabs.Panel>

          {/* Load Balancing Tab */}
          <Tabs.Panel value="2">
            <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg">
              {/* Circuit Breakers */}
              <Paper p="md">
                <Text size="lg" fw={500} mb="md">
                  Circuit Breaker States
                </Text>
                <Stack gap="sm">
                  {Object.entries(circuitBreakerStates).map(([name, state]) => (
                    <Group key={name} justify="space-between" align="center">
                      <Group align="center" gap="sm">
                        {state === 'OPEN' && <IconX color="red" />}
                        {state === 'HALF_OPEN' && <IconAlertTriangle color="orange" />}
                        {state === 'CLOSED' && <IconCircleCheck color="green" />}
                        <Box>
                          <Text fw={500}>{name}</Text>
                          <Text size="sm" c="dimmed">State: {state}</Text>
                        </Box>
                      </Group>
                    </Group>
                  ))}
                </Stack>
              </Paper>

              {/* Rate Limiting */}
              <Paper p="md">
                <Text size="lg" fw={500} mb="md">
                  Rate Limiting Metrics
                </Text>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={Object.entries(rateLimitMetrics).map(([endpoint, count]) => ({
                    endpoint,
                    requests: count
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="endpoint" />
                    <YAxis />
                    <ChartTooltip />
                    <Legend />
                    <Bar dataKey="requests" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </Paper>

              {/* Database Replicas */}
              <Box style={{ gridColumn: '1 / -1' }}>
                <Paper p="md">
                  <Text size="lg" fw={500} mb="md">
                    Database Replica Health
                  </Text>
                  <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }} spacing="md">
                    {Object.entries(replicaHealth).map(([replica, healthy]) => (
                      <Card key={replica} style={{
                        backgroundColor: healthy ? alpha(theme.colors.green[6], 0.1) : alpha(theme.colors.red[6], 0.1)
                      }}>
                        <Stack gap="xs">
                          <Text size="sm" c="dimmed">
                            {replica}
                          </Text>
                          <Group align="center" gap="xs">
                            {healthy ? (
                              <IconCircleCheck color={theme.colors.green[6]} />
                            ) : (
                              <IconX color={theme.colors.red[6]} />
                            )}
                            <Text fw={500}>
                              {healthy ? 'Healthy' : 'Unhealthy'}
                            </Text>
                          </Group>
                        </Stack>
                      </Card>
                    ))}
                  </SimpleGrid>
                </Paper>
              </Box>
            </SimpleGrid>
          </Tabs.Panel>

          {/* Anomalies Tab */}
          <Tabs.Panel value="3">
            <Box>
              <Text size="lg" fw={500} mb="md">
                Detected Anomalies
              </Text>
              <Stack gap="md">
                {anomalies.map((anomaly) => (
                  <Alert
                    key={anomaly.id}
                    color={
                      anomaly.severity === 'critical' ? 'red' :
                      anomaly.severity === 'high' ? 'orange' :
                      'blue'
                    }
                    title={anomaly.metric}
                  >
                    {anomaly.message} - Value: {anomaly.value}, Expected: {anomaly.expected}
                    <Text size="xs" c="dimmed" mt="xs">
                      {format(new Date(anomaly.timestamp), 'PPpp')}
                    </Text>
                  </Alert>
                ))}
              </Stack>
            </Box>
          </Tabs.Panel>

          {/* System Health Tab */}
          <Tabs.Panel value="4">
            <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="lg">
              {systemHealth.map((service) => (
                <Card key={service.service}>
                  <Group justify="space-between" align="center" mb="md">
                    <Text fw={500}>
                      {service.service}
                    </Text>
                    <Badge
                      color={
                        service.status === 'healthy' ? 'green' :
                        service.status === 'degraded' ? 'orange' :
                        'red'
                      }
                    >
                      {service.status}
                    </Badge>
                  </Group>
                  <Stack gap="sm">
                    <Box>
                      <Text size="sm" c="dimmed">
                        CPU
                      </Text>
                      <Progress
                        value={service.metrics.cpu}
                        color={service.metrics.cpu > 80 ? 'red' : 'blue'}
                        size="sm"
                      />
                    </Box>
                    <Box>
                      <Text size="sm" c="dimmed">
                        Memory
                      </Text>
                      <Progress
                        value={service.metrics.memory}
                        color={service.metrics.memory > 80 ? 'red' : 'blue'}
                        size="sm"
                      />
                    </Box>
                    <Box>
                      <Text size="sm" c="dimmed">
                        Disk
                      </Text>
                      <Progress
                        value={service.metrics.disk}
                        color={service.metrics.disk > 80 ? 'red' : 'blue'}
                        size="sm"
                      />
                    </Box>
                    <Box>
                      <Text size="sm" c="dimmed">
                        Network
                      </Text>
                      <Progress
                        value={service.metrics.network}
                        color={service.metrics.network > 80 ? 'red' : 'blue'}
                        size="sm"
                      />
                    </Box>
                  </Stack>
                  <Text size="xs" c="dimmed" mt="md">
                    Uptime: {Math.floor(service.uptime / 3600)}h {Math.floor((service.uptime % 3600) / 60)}m
                  </Text>
                </Card>
              ))}
            </SimpleGrid>
          </Tabs.Panel>
        </Tabs>
      </Paper>
    </Box>
  );
};

export default ObservabilityDashboard;