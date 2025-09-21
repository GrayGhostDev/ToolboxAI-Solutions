/**
 * Agent System Dashboard
 *
 * Admin-only dashboard for monitoring and controlling the AI agent system.
 * Admins can enable access for teachers through settings.
 */
import React, { useState, useEffect, useCallback } from 'react';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import IconButton from '@mui/material/IconButton';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import CircularProgress from '@mui/material/CircularProgress';
import Tooltip from '@mui/material/Tooltip';
import Badge from '@mui/material/Badge';
import Divider from '@mui/material/Divider';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';
import {
  SmartToy as AgentIcon,
  Memory as ResourceIcon,
  Assignment as TaskIcon,
  Speed as PerformanceIcon,
  Refresh as RefreshIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Settings as SettingsIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  CloudQueue as QueueIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import { useAuth } from '../hooks/useAuth';
import { orchestratorApi } from '../services/orchestratorApi';
import { pusherService } from '../services/pusher';
import { Chart as ChartJS, ArcElement, Tooltip as ChartTooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement, BarElement } from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';
// Register Chart.js components
ChartJS.register(ArcElement, ChartTooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement, BarElement);
interface AgentInfo {
  name: string;
  category: string;
  description: string;
  capabilities: string[];
  status: string;
  metrics: Record<string, any>;
}
interface SystemStatus {
  orchestrator: {
    is_running: boolean;
    uptime: number;
    total_processed: number;
  };
  agents: Record<string, number>;
  tasks: {
    pending: number;
    active: number;
    completed: number;
    failed: number;
  };
  resources: {
    cpu_percent: number;
    memory_percent: number;
    memory_used_mb: number;
    memory_available_mb: number;
    disk_usage_percent: number;
    disk_free_gb: number;
    network_sent_mb: number;
    network_recv_mb: number;
    process_count: number;
  };
  worktrees?: any;
}
interface TaskInfo {
  task_id: string;
  status: string;
  agent_type: string;
  created_at: string;
  message?: string;
  result?: any;
}
const AgentDashboard: React.FunctionComponent<Record<string, any>> = () => {
  const navigate = useNavigate();
  const { user, hasRole } = useAuth();
  const settings = useSelector((state: RootState) => state.settings);
  // State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [recentTasks, setRecentTasks] = useState<TaskInfo[]>([]);
  const [selectedTab, setSelectedTab] = useState(0);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000);
  // Check access permissions
  const canAccess = useCallback(() => {
    if (hasRole('admin')) return true;
    if (hasRole('teacher') && settings?.agentDashboard?.teacherAccess) return true;
    return false;
  }, [hasRole, settings]);
  // Redirect if no access
  useEffect(() => {
    if (!canAccess()) {
      navigate('/dashboard');
    }
  }, [canAccess, navigate]);
  // Fetch agents
  const fetchAgents = useCallback(async () => {
    try {
      const data = await orchestratorApi.listAgents();
      setAgents(data);
    } catch (err) {
      console.error('Failed to fetch agents:', err);
    }
  }, []);
  // Fetch system status
  const fetchSystemStatus = useCallback(async () => {
    try {
      const data = await orchestratorApi.getSystemStatus();
      setSystemStatus(data);
    } catch (err) {
      console.error('Failed to fetch system status:', err);
    }
  }, []);
  // Initial load
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        await Promise.all([
          fetchAgents(),
          fetchSystemStatus(),
        ]);
      } catch (err) {
        setError('Failed to load agent system data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [fetchAgents, fetchSystemStatus]);
  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      fetchSystemStatus();
    }, refreshInterval);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchSystemStatus]);
  // Subscribe to Pusher for real-time updates
  useEffect(() => {
    const channel = pusherService.subscribe('agent-system');
    channel.bind('task-update', (data: any) => {
      // Update task in recentTasks if it exists
      setRecentTasks(prev => {
        const index = prev.findIndex(t => t.task_id === data.task_id);
        if (index !== -1) {
          const updated = [...prev];
          updated[index] = { ...updated[index], ...data };
          return updated;
        }
        return [data, ...prev].slice(0, 10); // Keep last 10 tasks
      });
    });
    channel.bind('agent-status', (data: any) => {
      // Update agent status
      setAgents(prev => {
        const index = prev.findIndex(a => a.name === data.agent_name);
        if (index !== -1) {
          const updated = [...prev];
          updated[index] = { ...updated[index], status: data.status };
          return updated;
        }
        return prev;
      });
    });
    channel.bind('system-metrics', (data: any) => {
      // Update system metrics
      setSystemStatus(prev => prev ? { ...prev, ...data } : null);
    });
    return () => {
      pusherService.unsubscribe('agent-system');
    };
  }, []);
  // Submit test task
  const submitTestTask = async () => {
    try {
      const result = await orchestratorApi.submitTask({
        agent_type: 'content',
        task_data: {
          action: 'test',
          timestamp: new Date().toISOString(),
        },
        priority: 3,
      });
      // Add to recent tasks
      setRecentTasks(prev => [result, ...prev].slice(0, 10));
    } catch (err) {
      console.error('Failed to submit test task:', err);
    }
  };
  // Format uptime
  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours}h ${minutes}m ${secs}s`;
  };
  // Get status color
  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'running':
      case 'available':
      case 'completed':
        return 'success';
      case 'pending':
      case 'queued':
        return 'info';
      case 'failed':
      case 'error':
        return 'error';
      case 'busy':
      case 'in_progress':
        return 'warning';
      default:
        return 'default';
    }
  };
  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'running':
      case 'available':
      case 'completed':
        return <SuccessIcon fontSize="small" />;
      case 'failed':
      case 'error':
        return <ErrorIcon fontSize="small" />;
      case 'pending':
      case 'queued':
        return <InfoIcon fontSize="small" />;
      case 'busy':
      case 'in_progress':
        return <WarningIcon fontSize="small" />;
      default:
        return null;
    }
  };
  // Prepare chart data
  const agentDistributionData = systemStatus ? {
    labels: Object.keys(systemStatus.agents),
    datasets: [{
      data: Object.values(systemStatus.agents),
      backgroundColor: [
        '#FF6384',
        '#36A2EB',
        '#FFCE56',
        '#4BC0C0',
        '#9966FF',
        '#FF9F40',
      ],
    }],
  } : null;
  const taskStatusData = systemStatus ? {
    labels: ['Pending', 'Active', 'Completed', 'Failed'],
    datasets: [{
      label: 'Tasks',
      data: [
        systemStatus.tasks.pending,
        systemStatus.tasks.active,
        systemStatus.tasks.completed,
        systemStatus.tasks.failed,
      ],
      backgroundColor: ['#36A2EB', '#FFCE56', '#4BC0C0', '#FF6384'],
    }],
  } : null;
  const resourceUsageData = systemStatus ? {
    labels: ['CPU', 'Memory', 'Disk'],
    datasets: [{
      label: 'Usage %',
      data: [
        systemStatus.resources.cpu_percent,
        systemStatus.resources.memory_percent,
        systemStatus.resources.disk_usage_percent,
      ],
      backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56'],
      borderWidth: 1,
    }],
  } : null;
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }
  if (error) {
    return (
      <Alert severity="error">
        <AlertTitle>Error</AlertTitle>
        {error}
      </Alert>
    );
  }
  return (
    <Box>
      {/* Header */}
      <Box mb={3} display="flex" justifyContent="space-between" alignItems="center">
        <Typography variant="h4" component="h1">
          <AgentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Agent System Dashboard
        </Typography>
        <Box display="flex" gap={2} alignItems="center">
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
            }
            label="Auto-refresh"
          />
          <IconButton onClick={(e: React.MouseEvent) => fetchSystemStatus} title="Refresh">
            <RefreshIcon />
          </IconButton>
          {hasRole('admin') && (
            <IconButton onClick={(e: React.MouseEvent) => () => navigate('/settings/agents')} title="Settings">
              <SettingsIcon />
            </IconButton>
          )}
        </Box>
      </Box>
      {/* System Overview */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                System Status
              </Typography>
              <Box display="flex" alignItems="center">
                {systemStatus?.orchestrator.is_running ? (
                  <>
                    <SuccessIcon color="success" sx={{ mr: 1 }} />
                    <Typography variant="h6" color="success.main">
                      Running
                    </Typography>
                  </>
                ) : (
                  <>
                    <ErrorIcon color="error" sx={{ mr: 1 }} />
                    <Typography variant="h6" color="error.main">
                      Stopped
                    </Typography>
                  </>
                )}
              </Box>
              <Typography variant="body2" color="textSecondary" mt={1}>
                Uptime: {formatUptime(systemStatus?.orchestrator.uptime || 0)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Agents
              </Typography>
              <Typography variant="h4">
                {agents.length}
              </Typography>
              <Typography variant="body2" color="textSecondary" mt={1}>
                Across {Object.keys(systemStatus?.agents || {}).length} categories
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Tasks Processed
              </Typography>
              <Typography variant="h4">
                {systemStatus?.orchestrator.total_processed || 0}
              </Typography>
              <Box display="flex" gap={1} mt={1}>
                <Chip
                  size="small"
                  label={`${systemStatus?.tasks.active || 0} active`}
                  color="warning"
                />
                <Chip
                  size="small"
                  label={`${systemStatus?.tasks.pending || 0} pending`}
                  color="info"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Resource Usage
              </Typography>
              <Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2">CPU</Typography>
                  <Typography variant="body2">
                    {systemStatus?.resources.cpu_percent.toFixed(1)}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={systemStatus?.resources.cpu_percent || 0}
                  sx={{ my: 0.5 }}
                />
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2">Memory</Typography>
                  <Typography variant="body2">
                    {systemStatus?.resources.memory_percent.toFixed(1)}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={systemStatus?.resources.memory_percent || 0}
                  color="secondary"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={selectedTab} onChange={(e, v) => setSelectedTab(v)}>
          <Tab label="Agents" icon={<AgentIcon />} iconPosition="start" />
          <Tab label="Tasks" icon={<TaskIcon />} iconPosition="start" />
          <Tab label="Resources" icon={<ResourceIcon />} iconPosition="start" />
          <Tab label="Analytics" icon={<PerformanceIcon />} iconPosition="start" />
        </Tabs>
        <Box p={3}>
          {/* Agents Tab */}
          {selectedTab === 0 && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={8}>
                <Typography variant="h6" gutterBottom>
                  Registered Agents
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Agent</TableCell>
                        <TableCell>Category</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Capabilities</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {agents.slice(0, 10).map((agent) => (
                        <TableRow key={agent.name}>
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium">
                              {agent.name}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              size="small"
                              label={agent.category}
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>
                            <Chip
                              size="small"
                              label={agent.status}
                              color={getStatusColor(agent.status) as any}
                              icon={getStatusIcon(agent.status) as any}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="caption" color="textSecondary">
                              {agent.capabilities.length || 0} capabilities
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
              <Grid item xs={12} md={4}>
                <Typography variant="h6" gutterBottom>
                  Agent Distribution
                </Typography>
                {agentDistributionData && (
                  <Doughnut
                    data={agentDistributionData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'bottom',
                        },
                      },
                    }}
                    height={300}
                  />
                )}
              </Grid>
            </Grid>
          )}
          {/* Tasks Tab */}
          {selectedTab === 1 && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={8}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">
                    Recent Tasks
                  </Typography>
                  <Button
                    variant="outlined"
                    startIcon={<PlayArrow />}
                    onClick={(e: React.MouseEvent) => submitTestTask}
                  >
                    Submit Test Task
                  </Button>
                </Box>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Task ID</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Created</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {recentTasks.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={4} align="center">
                            <Typography variant="body2" color="textSecondary">
                              No recent tasks
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ) : (
                        recentTasks.map((task) => (
                          <TableRow key={task.task_id}>
                            <TableCell>
                              <Typography variant="caption" fontFamily="monospace">
                                {task.task_id.substring(0, 8)}...
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip
                                size="small"
                                label={task.agent_type}
                                variant="outlined"
                              />
                            </TableCell>
                            <TableCell>
                              <Chip
                                size="small"
                                label={task.status}
                                color={getStatusColor(task.status) as any}
                                icon={getStatusIcon(task.status) as any}
                              />
                            </TableCell>
                            <TableCell>
                              <Typography variant="caption">
                                {new Date(task.created_at).toLocaleTimeString()}
                              </Typography>
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
              <Grid item xs={12} md={4}>
                <Typography variant="h6" gutterBottom>
                  Task Status
                </Typography>
                {taskStatusData && (
                  <Bar
                    data={taskStatusData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          display: false,
                        },
                      },
                    }}
                    height={300}
                  />
                )}
              </Grid>
            </Grid>
          )}
          {/* Resources Tab */}
          {selectedTab === 2 && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Resource Utilization
                </Typography>
                {resourceUsageData && (
                  <Bar
                    data={resourceUsageData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      scales: {
                        y: {
                          beginAtZero: true,
                          max: 100,
                        },
                      },
                      plugins: {
                        legend: {
                          display: false,
                        },
                      },
                    }}
                    height={300}
                  />
                )}
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  System Metrics
                </Typography>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="textSecondary">
                        Processes
                      </Typography>
                      <Typography variant="h6">
                        {systemStatus?.resources.process_count || 0}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="textSecondary">
                        Network Sent
                      </Typography>
                      <Typography variant="h6">
                        {(systemStatus?.resources.network_sent_mb || 0).toFixed(2)} MB
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="textSecondary">
                        Network Received
                      </Typography>
                      <Typography variant="h6">
                        {(systemStatus?.resources.network_recv_mb || 0).toFixed(2)} MB
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="textSecondary">
                        Free Disk
                      </Typography>
                      <Typography variant="h6">
                        {(systemStatus?.resources.disk_free_gb || 0).toFixed(1)} GB
                      </Typography>
                    </Grid>
                  </Grid>
                </Paper>
              </Grid>
            </Grid>
          )}
          {/* Analytics Tab */}
          {selectedTab === 3 && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Alert severity="info">
                  <AlertTitle>Analytics Dashboard</AlertTitle>
                  Advanced analytics and performance metrics will be available in the next update.
                  This will include:
                  <ul>
                    <li>Task completion rates by agent type</li>
                    <li>Average processing times</li>
                    <li>Error rates and patterns</li>
                    <li>Resource optimization suggestions</li>
                    <li>Historical trends and predictions</li>
                  </ul>
                </Alert>
              </Grid>
            </Grid>
          )}
        </Box>
      </Paper>
    </Box>
  );
};
export default AgentDashboard;