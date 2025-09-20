/**
 * SystemHealthMonitor Component
 * Real-time monitoring of system health metrics
 */

import React, { memo, useEffect, useState, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Stack,
  LinearProgress,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  AlertTitle,
  Button,
  Collapse,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  useTheme,
  alpha,
} from '@mui/material';
import {
  Speed as CPUIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  CloudQueue as NetworkIcon,
  DataUsage as DatabaseIcon,
  Api as APIIcon,
  CheckCircle as HealthyIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  TrendingUp,
  TrendingDown,
} from '@mui/icons-material';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, Tooltip as ChartTooltip, ResponsiveContainer } from 'recharts';
import { motion } from 'framer-motion';
import { api } from '@/services/api';
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
  const theme = useTheme();
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
  const { subscribe, unsubscribe } = usePusher();

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

    subscribe(channel, 'metric-update', handleMetricUpdate);
    subscribe(channel, 'service-status', handleServiceUpdate);

    return () => {
      unsubscribe(channel, 'metric-update', handleMetricUpdate);
      unsubscribe(channel, 'service-status', handleServiceUpdate);
    };
  }, [subscribe, unsubscribe]);

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
        return theme.palette.success.main;
      case 'warning':
      case 'degraded':
        return theme.palette.warning.main;
      case 'critical':
      case 'offline':
        return theme.palette.error.main;
      default:
        return theme.palette.text.secondary;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'online':
        return <HealthyIcon fontSize="small" />;
      case 'warning':
      case 'degraded':
        return <WarningIcon fontSize="small" />;
      case 'critical':
      case 'offline':
        return <ErrorIcon fontSize="small" />;
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
        return <DataUsage Icon />;
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
      sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}
    >
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Stack direction="row" alignItems="center" spacing={2}>
            <Typography variant="h6" fontWeight="bold">
              System Health
            </Typography>
            <Chip
              label={overallHealth.toUpperCase()}
              size="small"
              color={
                overallHealth === 'healthy'
                  ? 'success'
                  : overallHealth === 'warning'
                  ? 'warning'
                  : 'error'
              }
              icon={getStatusIcon(overallHealth)}
            />
          </Stack>
          <Stack direction="row" spacing={1}>
            <Tooltip title="Last updated">
              <Typography variant="caption" color="text.secondary">
                {lastUpdate.toLocaleTimeString()}
              </Typography>
            </Tooltip>
            <IconButton size="small" onClick={handleRefresh} disabled={loading}>
              <RefreshIcon />
            </IconButton>
            <IconButton size="small" onClick={() => setExpanded(!expanded)}>
              {expanded ? <CollapseIcon /> : <ExpandIcon />}
            </IconButton>
          </Stack>
        </Stack>
      </Box>

      <Collapse in={expanded}>
        <Box sx={{ p: 2, flex: 1, overflow: 'auto' }}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {/* System Metrics */}
          <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 2 }}>
            System Metrics
          </Typography>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            {Object.entries(metrics).map(([key, metric]) => (
              <Grid item xs={12} sm={6} md={3} key={key}>
                <Paper
                  variant="outlined"
                  sx={{
                    p: 2,
                    cursor: onMetricClick ? 'pointer' : 'default',
                    borderLeft: `4px solid ${getStatusColor(metric.status)}`,
                    '&:hover': onMetricClick
                      ? {
                          backgroundColor: alpha(theme.palette.primary.main, 0.05),
                        }
                      : {},
                  }}
                  onClick={() => onMetricClick?.(metric)}
                >
                  <Stack spacing={1}>
                    <Stack direction="row" alignItems="center" spacing={1}>
                      <Box sx={{ color: getStatusColor(metric.status) }}>
                        {getMetricIcon(key)}
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        {metric.name}
                      </Typography>
                    </Stack>
                    <Typography variant="h5" fontWeight="bold">
                      {metric.value}
                      <Typography component="span" variant="body2" color="text.secondary">
                        {metric.unit}
                      </Typography>
                    </Typography>
                    {metric.threshold && (
                      <LinearProgress
                        variant="determinate"
                        value={(metric.value / metric.threshold.critical) * 100}
                        sx={{
                          height: 6,
                          borderRadius: 1,
                          backgroundColor: alpha(getStatusColor(metric.status), 0.2),
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: getStatusColor(metric.status),
                          },
                        }}
                      />
                    )}
                    {showCharts && metric.history && (
                      <Box sx={{ height: 60, mt: 1 }}>
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
                </Paper>
              </Grid>
            ))}
          </Grid>

          {/* Service Status */}
          <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 2 }}>
            Service Status
          </Typography>
          <List sx={{ p: 0 }}>
            {services.map(service => (
              <ListItem
                key={service.name}
                button={!!onServiceClick}
                onClick={() => onServiceClick?.(service)}
                sx={{
                  mb: 1,
                  border: 1,
                  borderColor: 'divider',
                  borderRadius: 1,
                  backgroundColor:
                    service.status === 'offline'
                      ? alpha(theme.palette.error.main, 0.05)
                      : service.status === 'degraded'
                      ? alpha(theme.palette.warning.main, 0.05)
                      : 'transparent',
                }}
              >
                <ListItemIcon>
                  <Box sx={{ color: getStatusColor(service.status) }}>
                    {getStatusIcon(service.status)}
                  </Box>
                </ListItemIcon>
                <ListItemText
                  primary={service.name}
                  secondary={
                    <Stack direction="row" spacing={2}>
                      <Typography variant="caption">
                        Status: {service.status}
                      </Typography>
                      {service.uptime && (
                        <Typography variant="caption">
                          Uptime: {service.uptime}
                        </Typography>
                      )}
                      {service.responseTime && (
                        <Typography variant="caption">
                          Response: {service.responseTime}ms
                        </Typography>
                      )}
                      {service.error && (
                        <Typography variant="caption" color="error">
                          {service.error}
                        </Typography>
                      )}
                    </Stack>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Box>
      </Collapse>
    </MotionPaper>
  );
});

SystemHealthMonitor.displayName = 'SystemHealthMonitor';

export default SystemHealthMonitor;