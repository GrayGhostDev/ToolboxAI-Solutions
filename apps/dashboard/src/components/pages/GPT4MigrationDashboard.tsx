/**
 * GPT-4.1 Migration Monitoring Dashboard
 *
 * Comprehensive dashboard for monitoring the GPT-4.1 migration progress,
 * including real-time metrics, cost tracking, performance monitoring,
 * and alert management.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  CircularProgress,
  Grid,
  Typography,
  Alert,
  AlertTitle,
  Chip,
  LinearProgress,
  IconButton,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tooltip,
  useTheme
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon,
  Assignment as AssignmentIcon,
  AttachMoney as AttachMoneyIcon,
  Speed as SpeedIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
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
      case 'emergency': return <ErrorIcon />;
      case 'critical': return <ErrorIcon />;
      case 'warning': return <WarningIcon />;
      case 'info': return <InfoIcon />;
      default: return <CheckCircleIcon />;
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
          <Typography variant="h6" gutterBottom>
            Migration Progress
          </Typography>
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
                <Typography variant="h6" component="div" color="text.secondary">
                  {formatPercentage(progress.progress_percentage)}
                </Typography>
              </Box>
            </Box>
            <Box ml={2}>
              <Typography variant="body2" color="text.secondary">
                Phase: {progress.current_phase}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Days remaining: {progress.days_remaining}
              </Typography>
              <Chip
                label={progress.urgency_level}
                color={progress.urgency_level === 'low' ? 'success' : 'warning'}
                size="small"
              />
            </Box>
          </Box>
          <Typography variant="body2" color="text.secondary">
            Deadline: {new Date(progress.deadline).toLocaleDateString()}
          </Typography>
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
          <Typography variant="h6" gutterBottom>
            Cost Summary
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography variant="h4" color="primary">
                {formatCurrency(cost.current_monthly_cost)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Current Month
              </Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="h4" color="secondary">
                {formatCurrency(cost.projected_monthly_total)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Projected Total
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <Box display="flex" alignItems="center" mt={1}>
                <Typography variant="body2" color="text.secondary" mr={1}>
                  Budget utilization:
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={Math.min(cost.budget_utilization, 100)}
                  color={cost.budget_utilization > 80 ? 'warning' : 'primary'}
                  sx={{ flexGrow: 1, mr: 1 }}
                />
                <Typography variant="body2">
                  {formatPercentage(cost.budget_utilization)}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12}>
              <Box display="flex" alignItems="center">
                {cost.trend_percentage > 0 ? (
                  <TrendingUpIcon color="error" />
                ) : (
                  <TrendingDownIcon color="success" />
                )}
                <Typography
                  variant="body2"
                  color={cost.trend_percentage > 0 ? 'error' : 'success'}
                  ml={0.5}
                >
                  {cost.trend_percentage > 0 ? '+' : ''}{formatPercentage(cost.trend_percentage)} vs last week
                </Typography>
              </Box>
            </Grid>
          </Grid>
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
          <Typography variant="h6" gutterBottom>
            Performance Score
          </Typography>
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
                <Typography variant="h6" component="div" color="text.secondary">
                  {performance.score.toFixed(0)}
                </Typography>
              </Box>
            </Box>
            <Box ml={2}>
              <Typography variant="body1" fontWeight="bold">
                {performance.status.toUpperCase()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {performance.anomaly_count} anomalies detected
              </Typography>
            </Box>
          </Box>
          <Grid container spacing={1}>
            {Object.entries(performance.metrics).map(([key, value]) => (
              <Grid item xs={6} key={key}>
                <Typography variant="body2" color="text.secondary">
                  {key.replace('_', ' ')}: {typeof value === 'number' ? value.toFixed(2) : value}
                </Typography>
              </Grid>
            ))}
          </Grid>
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
          <Typography variant="h6" gutterBottom>
            Active Alerts
          </Typography>
          {alerts.length === 0 ? (
            <Box display="flex" alignItems="center" py={2}>
              <CheckCircleIcon color="success" sx={{ mr: 1 }} />
              <Typography variant="body2" color="text.secondary">
                No active alerts
              </Typography>
            </Box>
          ) : (
            <Box maxHeight={300} overflow="auto">
              {alerts.map((alert) => (
                <Alert
                  key={alert.id}
                  severity={getSeverityColor(alert.severity) as any}
                  icon={getSeverityIcon(alert.severity)}
                  sx={{ mb: 1 }}
                >
                  <AlertTitle>{alert.title}</AlertTitle>
                  <Typography variant="body2">{alert.message}</Typography>
                  <Box display="flex" alignItems="center" mt={1}>
                    <Chip
                      label={alert.category}
                      size="small"
                      sx={{ mr: 1 }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {new Date(alert.timestamp).toLocaleString()}
                    </Typography>
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
          <Typography variant="h6" gutterBottom>
            Cost Projection
          </Typography>
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
          <Typography variant="subtitle2" gutterBottom>
            Auto Refresh
          </Typography>
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
          variant="contained"
          onClick={() => fetchDashboardData()}
          sx={{ mt: 2 }}
          startIcon={<RefreshIcon />}
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
          <Typography variant="h4" gutterBottom>
            GPT-4.1 Migration Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {dashboardData?.layout.description} • Last updated: {lastUpdated?.toLocaleTimeString()}
          </Typography>
        </Box>
        <Box>
          <Tooltip title="Refresh Dashboard">
            <IconButton
              onClick={() => fetchDashboardData(true)}
              disabled={loading}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Settings">
            <IconButton onClick={() => setSettingsOpen(true)}>
              <SettingsIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Dashboard Grid */}
      <Grid container spacing={3}>
        {/* First Row - Key Metrics */}
        <Grid item xs={12} md={4}>
          {renderMigrationProgress()}
        </Grid>
        <Grid item xs={12} md={4}>
          {renderCostSummary()}
        </Grid>
        <Grid item xs={12} md={4}>
          {renderPerformanceScore()}
        </Grid>

        {/* Second Row - Charts and Alerts */}
        <Grid item xs={12} md={8}>
          {renderCostTrends()}
        </Grid>
        <Grid item xs={12} md={4}>
          {renderActiveAlerts()}
        </Grid>
      </Grid>

      {/* Settings Dialog */}
      {renderSettingsDialog()}

      {/* Floating Action Button for quick actions */}
      <Fab
        color="primary"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={() => fetchDashboardData(true)}
      >
        <RefreshIcon />
      </Fab>
    </Box>
  );
};

export default GPT4MigrationDashboard;