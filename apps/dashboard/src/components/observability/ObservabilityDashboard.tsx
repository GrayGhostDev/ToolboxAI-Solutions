import { Box, Button, Text, Paper, Stack, Grid, Container, IconButton, Avatar, Card, CardContent, CardActions, List, ListItem, ListItemText, Divider, TextField, Select, MenuItem, Chip, Badge, Alert, CircularProgress, LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions, Drawer, AppBar, Toolbar, Tabs, Tab, Menu, Tooltip, Checkbox, Radio, RadioGroup, FormControl, FormControlLabel, InputLabel, Switch, Slider, Rating, Autocomplete, Skeleton, Table } from '../../utils/mui-imports';
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
import { IconAlertTriangle, IconBell, IconBugReport, IconChevronDown, IconChevronUp, IconCircleCheck, IconCircleX, IconCloudQueue, IconCode, IconFilter, IconHub, IconMemory, IconNetworkCheck, IconRefresh, IconReportAnalytics, IconSearch, IconSpeed, IconStorage, IconTimeline, IconTrendingDown, IconTrendingUp } from '@tabler/icons-react';

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

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

// Custom components
const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`observability-tabpanel-${index}`}
      aria-labelledby={`observability-tab-${index}`}
      {...other}
    >
      {value === index && <Box style={{ p: 3 }}>{children}</Box>}
    </div>
  );
};

const MetricCard: React.FC<{
  title: string;
  value: number | string;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  color?: 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success';
  icon?: React.ReactElement;
}> = ({ title, value, unit, trend, color = 'primary', icon }) => {
  return (
    <Card style={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box>
            <Text color="textSecondary" gutterBottom size="sm">
              {title}
            </Text>
            <Text order={4} component="div" color={color}>
              {value}
              {unit && (
                <Text component="span" size="md" color="textSecondary">
                  {' ' + unit}
                </Text>
              )}
            </Text>
          </Box>
          <Box display="flex" flexDirection="column" alignItems="center">
            {icon && <Box mb={1}>{icon}</Box>}
            {trend && (
              <Box>
                {trend === 'up' && <IconTrendingUp color="green" />}
                {trend === 'down' && <IconTrendingDown color="red" />}
                {trend === 'stable' && <IconTrendingUp color="action" />}
              </Box>
            )}
          </Box>
        </Box>
      </CardContent>
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
    <Box key={trace.spanId} ml={depth * 4}>
      <Paper style={{ p: 2, mb: 1, backgroundColor: trace.status === 'ERROR' ? 'error.light' : 'background.paper' }}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box display="flex" alignItems="center">
            {trace.children && trace.children.length > 0 && (
              <IconButton size="small" onClick={() => toggleExpand(trace.spanId)}>
                {expanded.has(trace.spanId) ? <IconChevronUp /> : <IconChevronDown />}
              </IconButton>
            )}
            <Text size="sm" fontFamily="monospace">
              {trace.operationName}
            </Text>
            <Chip
              label={trace.serviceName}
              size="small"
              style={{ ml: 1 }}
              color={trace.status === 'ERROR' ? 'error' : 'primary'}
            />
          </Box>
          <Box display="flex" alignItems="center" gap={1}>
            <Text variant="caption" color="textSecondary">
              {trace.duration}ms
            </Text>
            {trace.status === 'ERROR' && <IconCircleX color="red" fontSize="small" />}
          </Box>
        </Box>
        {expanded.has(trace.spanId) && trace.children && (
          <Box mt={2}>
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
      setStreamingError((error instanceof IconCircleX) ? (error as IconCircleX).message : 'Failed to start streaming');
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

  return (
    <Box style={{ flexGrow: 1, p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Text order={4} component="h1">
          Observability Dashboard
        </Text>
        <Box display="flex" gap={2} alignItems="center">
          <FormControl size="small" style={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              label="Time Range"
              onChange={(e) => setTimeRange(e.target.value)}
            >
              <MenuItem value="5m">Last 5 min</MenuItem>
              <MenuItem value="15m">Last 15 min</MenuItem>
              <MenuItem value="1h">Last 1 hour</MenuItem>
              <MenuItem value="6h">Last 6 hours</MenuItem>
              <MenuItem value="24h">Last 24 hours</MenuItem>
            </Select>
          </FormControl>
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
            }
            label="Auto Refresh"
          />
          <FormControlLabel
            control={
              <Switch
                checked={isStreaming}
                onChange={(e) => {
                  if (e.target.checked) {
                    startStreaming();
                  } else {
                    stopStreaming();
                  }
                }}
                disabled={!autoRefresh}
                color="gray"
              />
            }
            label="Real-time Stream"
          />
          <IconButton onClick={fetchMetrics} disabled={loading}>
            <IconRefresh />
          </IconButton>
        </Box>
      </Box>

      {/* Loading indicator */}
      {loading && <LinearProgress style={{ mb: 2 }} />}

      {/* Streaming error alert */}
      {streamingError && (
        <Alert severity="error" style={{ mb: 2 }} onClose={() => setStreamingError(null)}>
          <AlertTitle>Streaming IconCircleX</AlertTitle>
          {streamingError}
        </Alert>
      )}

      {/* Alert banner for critical issues */}
      {summaryMetrics.activeAlerts > 0 && (
        <Alert severity="error" style={{ mb: 2 }}>
          <AlertTitle>Critical Alerts</AlertTitle>
          {summaryMetrics.activeAlerts} critical alerts require immediate attention
        </Alert>
      )}

      {/* Summary Cards */}
      <SimpleGrid spacing={3} mb={3}>
        <Box xs={12} sm={6} md={2}>
          <MetricCard
            title="Avg Latency"
            value={summaryMetrics.avgLatency}
            unit="ms"
            trend={summaryMetrics.avgLatency > 200 ? 'up' : 'stable'}
            color={summaryMetrics.avgLatency > 500 ? 'error' : 'primary'}
            icon={<IconSpeed />}
          />
        </Box>
        <Box xs={12} sm={6} md={2}>
          <MetricCard
            title="Throughput"
            value={summaryMetrics.totalRequests}
            unit="req/5m"
            trend="up"
            color="green"
            icon={<IconTimeline />}
          />
        </Box>
        <Box xs={12} sm={6} md={2}>
          <MetricCard
            title="IconCircleX Rate"
            value={summaryMetrics.errorRate}
            unit="%"
            trend={parseFloat(summaryMetrics.errorRate as string) > 1 ? 'up' : 'stable'}
            color={parseFloat(summaryMetrics.errorRate as string) > 5 ? 'error' : 'warning'}
            icon={<IconCircleX />}
          />
        </Box>
        <Box xs={12} sm={6} md={2}>
          <MetricCard
            title="Service Health"
            value={`${summaryMetrics.healthyServices}/${summaryMetrics.totalServices}`}
            trend="stable"
            color={summaryMetrics.healthyServices === summaryMetrics.totalServices ? 'success' : 'warning'}
            icon={<IconCircleCheck />}
          />
        </Box>
        <Box xs={12} sm={6} md={2}>
          <MetricCard
            title="Cache Hit Rate"
            value={cacheHitRate}
            unit="%"
            trend={cacheHitRate > 80 ? 'up' : 'down'}
            color={cacheHitRate > 80 ? 'success' : 'warning'}
            icon={<IconStorage />}
          />
        </Box>
        <Box xs={12} sm={6} md={2}>
          <MetricCard
            title="Active Alerts"
            value={summaryMetrics.activeAlerts}
            trend={summaryMetrics.activeAlerts > 0 ? 'up' : 'stable'}
            color={summaryMetrics.activeAlerts > 0 ? 'error' : 'success'}
            icon={<IconBell />}
          />
        </Box>
      </SimpleGrid>

      {/* Streaming Status Indicator */}
      {isStreaming && (
        <Box display="flex" alignItems="center" gap={1} mb={2}>
          <Box
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: 'success.main',
              animation: 'pulse 2s infinite'
            }}
          />
          <Text size="sm" color="success.main">
            Real-time streaming active
          </Text>
        </Box>
      )}

      {/* Main Content Tabs */}
      <Paper style={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          indicatorColor="primary"
          textColor="primary"
        >
          <Tab label="Metrics" icon={<IconReportAnalytics />} iconPosition="start" />
          <Tab label="Traces" icon={<IconTimeline />} iconPosition="start" />
          <Tab label="Load Balancing" icon={<IconHub />} iconPosition="start" />
          <Tab label="Anomalies" icon={<IconBugReport />} iconPosition="start" />
          <Tab label="System Health" icon={<IconNetworkCheck />} iconPosition="start" />
        </Tabs>

        {/* Metrics Tab */}
        <TabPanel value={tabValue} index={0}>
          <SimpleGrid spacing={3}>
            {/* Latency Chart */}
            <Box xs={12} md={6}>
              <Paper style={{ p: 2 }}>
                <Text order={6} gutterBottom>
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
            </Box>

            {/* Throughput Chart */}
            <Box xs={12} md={6}>
              <Paper style={{ p: 2 }}>
                <Text order={6} gutterBottom>
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
            </Box>

            {/* IconCircleX Rate Chart */}
            <Box xs={12} md={6}>
              <Paper style={{ p: 2 }}>
                <Text order={6} gutterBottom>
                  IconCircleX Rate
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
                      name="IconCircleX Rate (%)"
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Paper>
            </Box>

            {/* System Metrics */}
            <Box xs={12} md={6}>
              <Paper style={{ p: 2 }}>
                <Text order={6} gutterBottom>
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
            </Box>
          </SimpleGrid>
        </TabPanel>

        {/* Traces Tab */}
        <TabPanel value={tabValue} index={1}>
          <Box>
            <Text order={6} gutterBottom>
              Recent Traces
            </Text>
            <TraceTimeline traces={traces} />
          </Box>
        </TabPanel>

        {/* Load Balancing Tab */}
        <TabPanel value={tabValue} index={2}>
          <SimpleGrid spacing={3}>
            {/* Circuit Breakers */}
            <Box xs={12} md={6}>
              <Paper style={{ p: 2 }}>
                <Text order={6} gutterBottom>
                  Circuit Breaker States
                </Text>
                <List>
                  {Object.entries(circuitBreakerStates).map(([name, state]) => (
                    <ListItem key={name}>
                      <ListItemIcon>
                        {state === 'OPEN' && <IconCircleX color="red" />}
                        {state === 'HALF_OPEN' && <IconAlertTriangle color="yellow" />}
                        {state === 'CLOSED' && <IconCircleCheck color="green" />}
                      </ListItemIcon>
                      <ListItemText
                        primary={name}
                        secondary={`State: ${state}`}
                      />
                    </ListItem>
                  ))}
                </List>
              </Paper>
            </Box>

            {/* Rate Limiting */}
            <Box xs={12} md={6}>
              <Paper style={{ p: 2 }}>
                <Text order={6} gutterBottom>
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
            </Box>

            {/* Database Replicas */}
            <Box xs={12}>
              <Paper style={{ p: 2 }}>
                <Text order={6} gutterBottom>
                  Database Replica Health
                </Text>
                <SimpleGrid spacing={2}>
                  {Object.entries(replicaHealth).map(([replica, healthy]) => (
                    <Box xs={12} sm={6} md={3} key={replica}>
                      <Card style={{ backgroundColor: healthy ? 'success.light' : 'error.light' }}>
                        <CardContent>
                          <Text size="sm" color="textSecondary">
                            {replica}
                          </Text>
                          <Box display="flex" alignItems="center" gap={1}>
                            {healthy ? (
                              <IconCircleCheck color="green" />
                            ) : (
                              <IconCircleX color="red" />
                            )}
                            <Text order={6}>
                              {healthy ? 'Healthy' : 'Unhealthy'}
                            </Text>
                          </Box>
                        </CardContent>
                      </Card>
                    </Box>
                  ))}
                </SimpleGrid>
              </Paper>
            </Box>
          </SimpleGrid>
        </TabPanel>

        {/* Anomalies Tab */}
        <TabPanel value={tabValue} index={3}>
          <Box>
            <Text order={6} gutterBottom>
              Detected Anomalies
            </Text>
            <SimpleGrid spacing={2}>
              {anomalies.map((anomaly) => (
                <Box xs={12} key={anomaly.id}>
                  <Alert
                    severity={
                      anomaly.severity === 'critical' ? 'error' :
                      anomaly.severity === 'high' ? 'warning' :
                      'info'
                    }
                  >
                    <AlertTitle>{anomaly.metric}</AlertTitle>
                    {anomaly.message} - Value: {anomaly.value}, Expected: {anomaly.expected}
                    <Text variant="caption" display="block" mt={1}>
                      {format(new Date(anomaly.timestamp), 'PPpp')}
                    </Text>
                  </Alert>
                </Box>
              ))}
            </SimpleGrid>
          </Box>
        </TabPanel>

        {/* System Health Tab */}
        <TabPanel value={tabValue} index={4}>
          <SimpleGrid spacing={3}>
            {systemHealth.map((service) => (
              <Box xs={12} sm={6} md={4} key={service.service}>
                <Card>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                      <Text order={6}>
                        {service.service}
                      </Text>
                      <Chip
                        label={service.status}
                        color={
                          service.status === 'healthy' ? 'success' :
                          service.status === 'degraded' ? 'warning' :
                          'error'
                        }
                      />
                    </Box>
                    <SimpleGrid spacing={1}>
                      <Box xs={6}>
                        <Text size="sm" color="textSecondary">
                          CPU
                        </Text>
                        <LinearProgress
                          variant="determinate"
                          value={service.metrics.cpu}
                          color={service.metrics.cpu > 80 ? 'error' : 'primary'}
                        />
                      </Box>
                      <Box xs={6}>
                        <Text size="sm" color="textSecondary">
                          IconMemory
                        </Text>
                        <LinearProgress
                          variant="determinate"
                          value={service.metrics.memory}
                          color={service.metrics.memory > 80 ? 'error' : 'primary'}
                        />
                      </Box>
                      <Box xs={6}>
                        <Text size="sm" color="textSecondary">
                          Disk
                        </Text>
                        <LinearProgress
                          variant="determinate"
                          value={service.metrics.disk}
                          color={service.metrics.disk > 80 ? 'error' : 'primary'}
                        />
                      </Box>
                      <Box xs={6}>
                        <Text size="sm" color="textSecondary">
                          Network
                        </Text>
                        <LinearProgress
                          variant="determinate"
                          value={service.metrics.network}
                          color={service.metrics.network > 80 ? 'error' : 'primary'}
                        />
                      </Box>
                    </SimpleGrid>
                    <Text variant="caption" color="textSecondary" display="block" mt={2}>
                      Uptime: {Math.floor(service.uptime / 3600)}h {Math.floor((service.uptime % 3600) / 60)}m
                    </Text>
                  </CardContent>
                </Card>
              </Box>
            ))}
          </SimpleGrid>
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default ObservabilityDashboard;