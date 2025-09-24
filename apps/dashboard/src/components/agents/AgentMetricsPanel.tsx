/**
 * Agent Metrics Panel Component
 * 
 * Comprehensive metrics display for agent system performance monitoring.
 * 
 * @author ToolboxAI Team
 * @created 2025-09-21
 * @version 1.0.0
 */

import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Divider,
  List,
  ListItem,
  ListItemText,
  LinearProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import {
  Close as CloseIcon,
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  Memory as MemoryIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';

interface SystemMetrics {
  agents: {
    total: number;
    idle: number;
    busy: number;
    error: number;
    utilization_rate: number;
  };
  tasks: {
    total: number;
    completed: number;
    failed: number;
    running: number;
    queued: number;
    success_rate: number;
  };
  system: {
    status: string;
    uptime: string;
    last_updated: string;
  };
}

interface AgentStatus {
  agent_id: string;
  agent_type: string;
  status: string;
  total_tasks_completed: number;
  total_tasks_failed: number;
  average_execution_time: number;
  performance_metrics: {
    success_rate: number;
    error_rate: number;
    throughput: number;
    uptime: number;
  };
  resource_usage: {
    cpu_percent: number;
    memory_mb: number;
    gpu_percent: number;
  };
}

interface AgentMetricsPanelProps {
  open: boolean;
  onClose: () => void;
  systemMetrics: SystemMetrics | null;
  agents: AgentStatus[];
}

export const AgentMetricsPanel = ({
  open,
  onClose,
  systemMetrics,
  agents,
}: AgentMetricsPanelProps) => {
  const formatUptime = (uptime: number) => {
    return `${uptime.toFixed(1)}%`;
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
    return `${(seconds / 3600).toFixed(1)}h`;
  };

  const getPerformanceColor = (value: number, threshold: number = 80) => {
    if (value >= threshold) return 'success';
    if (value >= threshold * 0.7) return 'warning';
    return 'error';
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { height: '80vh' }
      }}
    >
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6">Agent System Metrics</Typography>
        <Typography variant="body2" color="text.secondary">
          Last updated: {systemMetrics?.system.last_updated ? 
            new Date(systemMetrics.system.last_updated).toLocaleString() : 'Never'}
        </Typography>
      </DialogTitle>

      <DialogContent>
        {!systemMetrics ? (
          <Typography>No metrics data available</Typography>
        ) : (
          <Grid container spacing={3}>
            {/* System Overview */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    System Overview
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box textAlign="center">
                        <Typography variant="h4" color="primary">
                          {systemMetrics.agents.total}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Total Agents
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box textAlign="center">
                        <Typography variant="h4" color="success.main">
                          {systemMetrics.agents.utilization_rate.toFixed(1)}%
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Utilization
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box textAlign="center">
                        <Typography variant="h4" color="info.main">
                          {systemMetrics.tasks.success_rate.toFixed(1)}%
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Success Rate
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box textAlign="center">
                        <Typography variant="h4" color="warning.main">
                          {systemMetrics.tasks.queued}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Queued Tasks
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            {/* Agent Status Breakdown */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Agent Status Breakdown
                  </Typography>
                  <List>
                    <ListItem>
                      <ListItemText 
                        primary={`Idle: ${systemMetrics.agents.idle}`}
                        secondary="Available for tasks"
                      />
                      <Chip 
                        icon={<CheckCircleIcon />} 
                        label={systemMetrics.agents.idle} 
                        color="success" 
                        size="small" 
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary={`Busy: ${systemMetrics.agents.busy}`}
                        secondary="Currently processing tasks"
                      />
                      <Chip 
                        icon={<SpeedIcon />} 
                        label={systemMetrics.agents.busy} 
                        color="primary" 
                        size="small" 
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary={`Error: ${systemMetrics.agents.error}`}
                        secondary="Agents with errors"
                      />
                      <Chip 
                        icon={<ErrorIcon />} 
                        label={systemMetrics.agents.error} 
                        color="error" 
                        size="small" 
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>

            {/* Task Statistics */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Task Statistics
                  </Typography>
                  <List>
                    <ListItem>
                      <ListItemText 
                        primary={`Completed: ${systemMetrics.tasks.completed}`}
                        secondary="Successfully completed tasks"
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary={`Failed: ${systemMetrics.tasks.failed}`}
                        secondary="Failed task executions"
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary={`Running: ${systemMetrics.tasks.running}`}
                        secondary="Currently executing"
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary={`Queued: ${systemMetrics.tasks.queued}`}
                        secondary="Waiting for execution"
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>

            {/* Individual Agent Performance */}
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Individual Agent Performance
                  </Typography>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Agent ID</TableCell>
                          <TableCell>Type</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell align="right">Tasks</TableCell>
                          <TableCell align="right">Success Rate</TableCell>
                          <TableCell align="right">Avg Time</TableCell>
                          <TableCell align="right">CPU</TableCell>
                          <TableCell align="right">Memory</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {agents.map((agent) => (
                          <TableRow key={agent.agent_id}>
                            <TableCell>
                              <Typography variant="body2" noWrap>
                                {agent.agent_id.substring(0, 12)}...
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {agent.agent_type.replace(/_/g, ' ')}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip
                                label={agent.status}
                                color={
                                  agent.status === 'idle' ? 'success' :
                                  agent.status === 'busy' ? 'primary' :
                                  agent.status === 'error' ? 'error' : 'default'
                                }
                                size="small"
                              />
                            </TableCell>
                            <TableCell align="right">
                              <Typography variant="body2">
                                {agent.total_tasks_completed}
                                {agent.total_tasks_failed > 0 && (
                                  <Typography component="span" color="error.main" sx={{ ml: 1 }}>
                                    ({agent.total_tasks_failed} failed)
                                  </Typography>
                                )}
                              </Typography>
                            </TableCell>
                            <TableCell align="right">
                              <Typography 
                                variant="body2" 
                                color={getPerformanceColor(agent.performance_metrics.success_rate) + '.main'}
                              >
                                {agent.performance_metrics.success_rate.toFixed(1)}%
                              </Typography>
                            </TableCell>
                            <TableCell align="right">
                              <Typography variant="body2">
                                {formatDuration(agent.average_execution_time)}
                              </Typography>
                            </TableCell>
                            <TableCell align="right">
                              <Box sx={{ display: 'flex', alignItems: 'center', minWidth: 60 }}>
                                <LinearProgress
                                  variant="determinate"
                                  value={agent.resource_usage.cpu_percent}
                                  color={getPerformanceColor(100 - agent.resource_usage.cpu_percent) as any}
                                  sx={{ flexGrow: 1, mr: 1, height: 6 }}
                                />
                                <Typography variant="caption">
                                  {agent.resource_usage.cpu_percent.toFixed(0)}%
                                </Typography>
                              </Box>
                            </TableCell>
                            <TableCell align="right">
                              <Typography variant="body2">
                                {agent.resource_usage.memory_mb}MB
                              </Typography>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} startIcon={<CloseIcon />}>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AgentMetricsPanel;
