/**
 * Agent Dashboard Component
 * 
 * Main dashboard for monitoring and managing AI agents in the ToolBoxAI system.
 * Provides real-time status updates via Pusher integration.
 * 
 * Features:
 * - Real-time agent status monitoring
 * - Task execution interface
 * - Performance metrics display
 * - System health indicators
 * - Agent configuration management
 * 
 * @author ToolboxAI Team
 * @created 2025-09-21
 * @version 1.0.0
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Button,
  Chip,
  Alert,
  Skeleton,
  Tooltip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Badge,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Settings as SettingsIcon,
  Analytics as AnalyticsIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Memory as MemoryIcon,
  Speed as SpeedIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { usePusher } from '../../hooks/usePusher';
import { useAgentAPI } from '../../hooks/useAgentAPI';
import { useSupabaseAgent } from '../../hooks/useSupabaseAgent';
import { AgentCard } from './AgentCard';
import { AgentTaskDialog } from './AgentTaskDialog';
import { AgentMetricsPanel } from './AgentMetricsPanel';
import { SystemHealthIndicator } from './SystemHealthIndicator';

// Types
interface AgentStatus {
  agent_id: string;
  agent_type: string;
  status: 'initializing' | 'idle' | 'busy' | 'processing' | 'waiting' | 'error' | 'offline' | 'maintenance';
  current_task_id?: string;
  total_tasks_completed: number;
  total_tasks_failed: number;
  average_execution_time: number;
  last_activity: string;
  created_at: string;
  performance_metrics: {
    uptime: number;
    throughput: number;
    error_rate: number;
    success_rate: number;
  };
  resource_usage: {
    cpu_percent: number;
    memory_mb: number;
    gpu_percent: number;
  };
}

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
    status: 'healthy' | 'degraded' | 'error';
    uptime: string;
    last_updated: string;
  };
}

export const AgentDashboard= () => {
  // State
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<AgentStatus | null>(null);
  const [taskDialogOpen, setTaskDialogOpen] = useState(false);
  const [metricsDialogOpen, setMetricsDialogOpen] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Hooks
  const { isConnected, subscribe, unsubscribe } = usePusher();
  const {
    getAgentsStatus,
    getSystemMetrics,
    executeTask,
    getAgentStatus,
    loading: apiLoading
  } = useAgentAPI();
  
  // Supabase integration
  const {
    agents: supabaseAgents,
    executions: supabaseExecutions,
    metrics: supabaseMetrics,
    systemHealth: supabaseSystemHealth,
    healthSummary: supabaseHealthSummary,
    loading: supabaseLoading,
    error: supabaseError,
    configured: supabaseConfigured,
    actions: supabaseActions
  } = useSupabaseAgent({
    enableRealtime: true,
    refreshInterval: 30000,
    autoRefresh: autoRefresh
  });

  // Status color mapping
  const getStatusColor = useCallback((status: string) => {
    switch (status) {
      case 'idle': return 'success';
      case 'busy': 
      case 'processing': return 'primary';
      case 'waiting': return 'warning';
      case 'error': return 'error';
      case 'offline': 
      case 'maintenance': return 'default';
      case 'initializing': return 'info';
      default: return 'default';
    }
  }, []);

  // Status icon mapping
  const getStatusIcon = useCallback((status: string) => {
    switch (status) {
      case 'idle': return <CheckCircleIcon />;
      case 'busy': 
      case 'processing': return <PlayIcon />;
      case 'waiting': return <ScheduleIcon />;
      case 'error': return <ErrorIcon />;
      case 'offline': 
      case 'maintenance': return <StopIcon />;
      case 'initializing': return <RefreshIcon />;
      default: return <CheckCircleIcon />;
    }
  }, []);

  // Load initial data
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Load data from both API and Supabase
      const [agentsData, metricsData] = await Promise.all([
        getAgentsStatus(),
        getSystemMetrics()
      ]);

      // Use API data as primary source
      if (agentsData.success) {
        setAgents(agentsData.data || []);
      } else if (supabaseConfigured && supabaseAgents.length > 0) {
        // Fallback to Supabase data if API fails
        const convertedAgents: AgentStatus[] = supabaseAgents.map(agent => ({
          agent_id: agent.agent_id,
          agent_type: agent.agent_type,
          status: agent.status,
          current_task_id: agent.current_task_id,
          total_tasks_completed: agent.total_tasks_completed,
          total_tasks_failed: agent.total_tasks_failed,
          average_execution_time: agent.average_execution_time,
          last_activity: agent.last_activity,
          created_at: agent.created_at,
          performance_metrics: {
            uptime: 100, // Default values
            throughput: 0,
            error_rate: 0,
            success_rate: agent.total_tasks_completed > 0 ? 
              (agent.total_tasks_completed / (agent.total_tasks_completed + agent.total_tasks_failed)) * 100 : 100
          },
          resource_usage: {
            cpu_percent: 0,
            memory_mb: 0,
            gpu_percent: 0
          }
        }));
        setAgents(convertedAgents);
      } else {
        throw new Error(agentsData.message || 'Failed to load agents');
      }

      if (metricsData.success) {
        setSystemMetrics(metricsData.data);
      } else if (supabaseConfigured && supabaseHealthSummary) {
        // Fallback to Supabase health summary
        const fallbackMetrics: SystemMetrics = {
          agents: {
            total: supabaseHealthSummary.total_agents,
            idle: supabaseHealthSummary.total_agents - supabaseHealthSummary.busy_agents - supabaseHealthSummary.error_agents,
            busy: supabaseHealthSummary.busy_agents,
            error: supabaseHealthSummary.error_agents,
            utilization_rate: supabaseHealthSummary.total_agents > 0 ? 
              (supabaseHealthSummary.busy_agents / supabaseHealthSummary.total_agents) * 100 : 0
          },
          tasks: {
            total: 0, // Would need additional data from Supabase
            completed: 0,
            failed: 0,
            running: 0,
            queued: 0,
            success_rate: supabaseHealthSummary.success_rate
          },
          system: {
            status: supabaseHealthSummary.total_agents > 0 && supabaseHealthSummary.error_agents === 0 ? 'healthy' : 
                   supabaseHealthSummary.error_agents > 0 ? 'error' : 'degraded',
            uptime: '99.9%', // Default value
            last_updated: new Date().toISOString()
          }
        };
        setSystemMetrics(fallbackMetrics);
      } else {
        throw new Error(metricsData.message || 'Failed to load system metrics');
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
      console.error('Error loading agent data:', err);
    } finally {
      setLoading(false);
    }
  }, [getAgentsStatus, getSystemMetrics, supabaseConfigured, supabaseAgents, supabaseHealthSummary]);

  // Handle Pusher events
  const handleAgentUpdate = useCallback((data: any) => {
    const { agent_id, event_type, data: eventData } = data;
    
    setAgents(prev => prev.map(agent => {
      if (agent.agent_id === agent_id) {
        // Update agent based on event type
        switch (event_type) {
          case 'agent_idle':
            return { ...agent, status: 'idle' as const };
          case 'agent_busy':
            return { ...agent, status: 'busy' as const };
          case 'agent_error':
            return { ...agent, status: 'error' as const };
          case 'task_started':
            return { 
              ...agent, 
              status: 'busy' as const, 
              current_task_id: eventData.task_id 
            };
          case 'task_completed':
            return { 
              ...agent, 
              status: 'idle' as const, 
              current_task_id: undefined,
              total_tasks_completed: agent.total_tasks_completed + 1,
              average_execution_time: eventData.execution_time || agent.average_execution_time
            };
          case 'task_failed':
            return { 
              ...agent, 
              status: 'idle' as const, 
              current_task_id: undefined,
              total_tasks_failed: agent.total_tasks_failed + 1
            };
          default:
            return agent;
        }
      }
      return agent;
    }));
  }, []);

  const handleMetricsUpdate = useCallback((data: any) => {
    const { metrics } = data;
    setSystemMetrics(metrics);
  }, []);

  const handleHealthUpdate = useCallback((data: any) => {
    const { health } = data;
    setSystemMetrics(prev => prev ? { ...prev, system: health.system } : null);
  }, []);

  // Setup Pusher subscriptions
  useEffect(() => {
    if (!isConnected) return;

    // Subscribe to agent updates
    subscribe('agent-updates', 'agent.idle', handleAgentUpdate);
    subscribe('agent-updates', 'agent.busy', handleAgentUpdate);
    subscribe('agent-updates', 'agent.error', handleAgentUpdate);
    subscribe('agent-updates', 'task.started', handleAgentUpdate);
    subscribe('agent-updates', 'task.completed', handleAgentUpdate);
    subscribe('agent-updates', 'task.failed', handleAgentUpdate);

    // Subscribe to metrics updates
    subscribe('agent-metrics', 'metrics.updated', handleMetricsUpdate);
    subscribe('system-health', 'health.updated', handleHealthUpdate);

    return () => {
      unsubscribe('agent-updates', 'agent.idle');
      unsubscribe('agent-updates', 'agent.busy');
      unsubscribe('agent-updates', 'agent.error');
      unsubscribe('agent-updates', 'task.started');
      unsubscribe('agent-updates', 'task.completed');
      unsubscribe('agent-updates', 'task.failed');
      unsubscribe('agent-metrics', 'metrics.updated');
      unsubscribe('system-health', 'health.updated');
    };
  }, [
    isConnected, 
    subscribe, 
    unsubscribe, 
    handleAgentUpdate, 
    handleMetricsUpdate, 
    handleHealthUpdate
  ]);

  // Auto-refresh data
  useEffect(() => {
    loadData();
    
    if (autoRefresh) {
      const interval = setInterval(loadData, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [loadData, autoRefresh]);

  // Computed values
  const agentsByType = useMemo(() => {
    return agents.reduce((acc, agent) => {
      if (!acc[agent.agent_type]) {
        acc[agent.agent_type] = [];
      }
      acc[agent.agent_type].push(agent);
      return acc;
    }, {} as Record<string, AgentStatus[]>);
  }, [agents]);

  const healthyAgents = useMemo(() => 
    agents.filter(a => !['error', 'offline'].includes(a.status)).length
  , [agents]);

  // Handlers
  const handleRefresh = useCallback(() => {
    loadData();
  }, [loadData]);

  const handleAgentClick = useCallback((agent: AgentStatus) => {
    setSelectedAgent(agent);
  }, []);

  const handleTaskExecute = useCallback((agent: AgentStatus) => {
    setSelectedAgent(agent);
    setTaskDialogOpen(true);
  }, []);

  const handleShowMetrics = useCallback(() => {
    setMetricsDialogOpen(true);
  }, []);

  if (loading && agents.length === 0) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Agent Dashboard
        </Typography>
        <Grid container spacing={3}>
          {[1, 2, 3, 4].map(i => (
            <Grid item xs={12} sm={6} md={3} key={i}>
              <Card>
                <CardContent>
                  <Skeleton variant="text" width="60%" />
                  <Skeleton variant="rectangular" height={60} sx={{ my: 1 }} />
                  <Skeleton variant="text" width="40%" />
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Agent Dashboard
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <SystemHealthIndicator 
            status={systemMetrics?.system.status || 'error'} 
            isConnected={isConnected}
          />
          <Button
            variant="outlined"
            startIcon={<AnalyticsIcon />}
            onClick={handleShowMetrics}
          >
            Metrics
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={apiLoading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* System Overview Cards */}
      {systemMetrics && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <MemoryIcon color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6">Total Agents</Typography>
                </Box>
                <Typography variant="h3" color="primary">
                  {systemMetrics.agents.total}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {healthyAgents} healthy
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <SpeedIcon color="success" sx={{ mr: 1 }} />
                  <Typography variant="h6">Utilization</Typography>
                </Box>
                <Typography variant="h3" color="success.main">
                  {systemMetrics.agents.utilization_rate.toFixed(1)}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={systemMetrics.agents.utilization_rate} 
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <TrendingUpIcon color="info" sx={{ mr: 1 }} />
                  <Typography variant="h6">Success Rate</Typography>
                </Box>
                <Typography variant="h3" color="info.main">
                  {systemMetrics.tasks.success_rate.toFixed(1)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {systemMetrics.tasks.completed} completed
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <ScheduleIcon color="warning" sx={{ mr: 1 }} />
                  <Typography variant="h6">Queue</Typography>
                </Box>
                <Typography variant="h3" color="warning.main">
                  {systemMetrics.tasks.queued}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {systemMetrics.tasks.running} running
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Agents Grid */}
      <Typography variant="h5" gutterBottom>
        Active Agents
      </Typography>
      
      {agents.length === 0 ? (
        <Alert severity="info">
          No agents are currently registered. The agent service may be starting up.
        </Alert>
      ) : (
        <Grid container spacing={3}>
          {agents.map(agent => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={agent.agent_id}>
              <AgentCard
                agent={agent}
                onAgentClick={handleAgentClick}
                onTaskExecute={handleTaskExecute}
                getStatusColor={getStatusColor}
                getStatusIcon={getStatusIcon}
              />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Agents by Type */}
      {Object.keys(agentsByType).length > 1 && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h5" gutterBottom>
            Agents by Type
          </Typography>
          {Object.entries(agentsByType).map(([type, typeAgents]) => (
            <Card key={type} sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} 
                  <Chip 
                    label={typeAgents.length} 
                    size="small" 
                    sx={{ ml: 1 }} 
                  />
                </Typography>
                <Grid container spacing={2}>
                  {typeAgents.map(agent => (
                    <Grid item xs={12} sm={6} md={4} key={agent.agent_id}>
                      <Box sx={{ display: 'flex', alignItems: 'center', p: 1, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                        <Badge
                          color={getStatusColor(agent.status) as any}
                          variant="dot"
                          sx={{ mr: 1 }}
                        >
                          {getStatusIcon(agent.status)}
                        </Badge>
                        <Box sx={{ flexGrow: 1 }}>
                          <Typography variant="body2" noWrap>
                            {agent.agent_id}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {agent.total_tasks_completed} tasks
                          </Typography>
                        </Box>
                        <Tooltip title="Execute Task">
                          <IconButton 
                            size="small" 
                            onClick={() => handleTaskExecute(agent)}
                            disabled={agent.status !== 'idle'}
                          >
                            <PlayIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}

      {/* Task Execution Dialog */}
      <AgentTaskDialog
        open={taskDialogOpen}
        onClose={() => setTaskDialogOpen(false)}
        agent={selectedAgent}
        onExecute={executeTask}
      />

      {/* Metrics Dialog */}
      <AgentMetricsPanel
        open={metricsDialogOpen}
        onClose={() => setMetricsDialogOpen(false)}
        systemMetrics={systemMetrics}
        agents={agents}
      />
    </Box>
  );
};

export default AgentDashboard;
