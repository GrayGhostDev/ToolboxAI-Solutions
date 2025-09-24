/**
 * Agent Card Component
 * 
 * Individual agent status card with real-time updates and actions.
 * 
 * @author ToolboxAI Team
 * @created 2025-09-21
 * @version 1.0.0
 */

import React from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Chip,
  Button,
  Box,
  LinearProgress,
  Tooltip,
  IconButton,
  Badge,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Settings as SettingsIcon,
  Analytics as AnalyticsIcon,
  Memory as MemoryIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';

interface AgentStatus {
  agent_id: string;
  agent_type: string;
  status: string;
  current_task_id?: string;
  total_tasks_completed: number;
  total_tasks_failed: number;
  average_execution_time: number;
  last_activity: string;
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

interface AgentCardProps {
  agent: AgentStatus;
  onAgentClick: (agent: AgentStatus) => void;
  onTaskExecute: (agent: AgentStatus) => void;
  getStatusColor: (status: string) => string;
  getStatusIcon: (status: string) => React.ReactNode;
}

export const AgentCard = ({
  agent,
  onAgentClick,
  onTaskExecute,
  getStatusColor,
  getStatusIcon,
}: AgentCardProps) => {
  const formatAgentType = (type: string) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const formatLastActivity = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return `${Math.floor(diffMins / 1440)}d ago`;
  };

  const getResourceColor = (percent: number) => {
    if (percent < 50) return 'success';
    if (percent < 80) return 'warning';
    return 'error';
  };

  return (
    <Card 
      sx={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        cursor: 'pointer',
        '&:hover': {
          boxShadow: 3,
          transform: 'translateY(-2px)',
          transition: 'all 0.2s ease-in-out'
        }
      }}
      onClick={() => onAgentClick(agent)}
    >
      <CardContent sx={{ flexGrow: 1 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Typography variant="h6" component="div" noWrap>
              {formatAgentType(agent.agent_type)}
            </Typography>
            <Typography variant="body2" color="text.secondary" noWrap>
              {agent.agent_id}
            </Typography>
          </Box>
          <Badge
            color={getStatusColor(agent.status) as any}
            variant="dot"
            sx={{ mt: 0.5 }}
          >
            {getStatusIcon(agent.status)}
          </Badge>
        </Box>

        {/* Status */}
        <Box sx={{ mb: 2 }}>
          <Chip
            label={agent.status.toUpperCase()}
            color={getStatusColor(agent.status) as any}
            size="small"
            sx={{ mb: 1 }}
          />
          {agent.current_task_id && (
            <Typography variant="caption" display="block" color="text.secondary">
              Running: {agent.current_task_id.substring(0, 8)}...
            </Typography>
          )}
        </Box>

        {/* Performance Stats */}
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2">
              Tasks: {agent.total_tasks_completed}
            </Typography>
            <Typography variant="body2" color={agent.total_tasks_failed > 0 ? 'error.main' : 'text.secondary'}>
              Failed: {agent.total_tasks_failed}
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2">
              Success Rate: {agent.performance_metrics.success_rate.toFixed(1)}%
            </Typography>
            <Typography variant="body2">
              Avg Time: {agent.average_execution_time.toFixed(1)}s
            </Typography>
          </Box>
        </Box>

        {/* Resource Usage */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" gutterBottom>
            Resource Usage
          </Typography>
          
          <Box sx={{ mb: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
              <Typography variant="caption">CPU</Typography>
              <Typography variant="caption">{agent.resource_usage.cpu_percent.toFixed(1)}%</Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={agent.resource_usage.cpu_percent}
              color={getResourceColor(agent.resource_usage.cpu_percent) as any}
              sx={{ height: 4, borderRadius: 2 }}
            />
          </Box>

          <Box sx={{ mb: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
              <Typography variant="caption">Memory</Typography>
              <Typography variant="caption">{agent.resource_usage.memory_mb}MB</Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={Math.min((agent.resource_usage.memory_mb / 1024) * 100, 100)}
              color={getResourceColor((agent.resource_usage.memory_mb / 1024) * 100) as any}
              sx={{ height: 4, borderRadius: 2 }}
            />
          </Box>
        </Box>

        {/* Last Activity */}
        <Typography variant="caption" color="text.secondary">
          Last activity: {formatLastActivity(agent.last_activity)}
        </Typography>
      </CardContent>

      <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
        <Box>
          <Tooltip title="View Metrics">
            <IconButton size="small" onClick={(e) => { e.stopPropagation(); /* Handle metrics view */ }}>
              <AnalyticsIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Settings">
            <IconButton size="small" onClick={(e) => { e.stopPropagation(); /* Handle settings */ }}>
              <SettingsIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
        
        <Button
          variant="contained"
          size="small"
          startIcon={<PlayIcon />}
          disabled={agent.status !== 'idle'}
          onClick={(e) => {
            e.stopPropagation();
            onTaskExecute(agent);
          }}
        >
          Execute
        </Button>
      </CardActions>
    </Card>
  );
};

export default AgentCard;
