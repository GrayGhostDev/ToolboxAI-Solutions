/**
 * Orchestrator API Service
 *
 * Provides API client for interacting with the agent orchestration system.
 */

import { api } from './api';

// Types
export interface AgentInfo {
  name: string;
  category: string;
  description: string;
  capabilities: string[];
  status: 'available' | 'busy' | 'offline';
  metrics?: {
    tasks_processed?: number;
    success_rate?: number;
    avg_processing_time?: number;
  };
}

export interface TaskInfo {
  task_id: string;
  status: 'pending' | 'queued' | 'assigned' | 'in_progress' | 'completed' | 'failed' | 'cancelled' | 'distributed' | 'unknown';
  agent_type: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  message?: string;
  result?: Record<string, any>;
  error?: string;
  priority?: 'critical' | 'high' | 'medium' | 'low' | 'deferred';
}

export interface SystemStatus {
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
    cpu_percent?: number;
    memory_percent?: number;
    disk_percent?: number;
    network?: {
      bytes_sent: number;
      bytes_recv: number;
    };
  };
  worktrees?: Record<string, any>;
}

export interface TaskSubmission {
  agent_type: string;
  task_data: Record<string, any>;
  priority?: 'critical' | 'high' | 'medium' | 'low' | 'deferred';
  metadata?: Record<string, any>;
}

export interface WorktreeTask {
  task_type: string;
  description: string;
  requirements?: string[];
  files?: string[];
  strategy?: 'capability_based' | 'load_balanced' | 'round_robin' | 'priority_based';
}

export interface ResourceSnapshot {
  timestamp: string;
  cpu_percent: number;
  memory_percent: number;
  disk_usage: {
    total: number;
    used: number;
    free: number;
    percent: number;
  };
  network: {
    bytes_sent: number;
    bytes_recv: number;
    packets_sent: number;
    packets_recv: number;
  };
  process_count: number;
  thread_count: number;
}

export interface ResourceAlert {
  id: string;
  type: 'cpu' | 'memory' | 'disk' | 'network' | 'process';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  threshold: number;
  current_value: number;
  timestamp: string;
  resolved: boolean;
}

// API Client
export const orchestratorApi = {
  /**
   * Get list of all registered agents
   */
  async getAgents(category?: string): Promise<AgentInfo[]> {
    const params = category ? { category } : {};
    const response = await api.get('/api/v1/orchestrator/agents', { params });
    return response.data;
  },

  /**
   * Submit a task to the orchestrator
   */
  async submitTask(submission: TaskSubmission): Promise<TaskInfo> {
    const response = await api.post('/api/v1/orchestrator/submit', submission);
    return response.data;
  },

  /**
   * Get status of a specific task
   */
  async getTaskStatus(taskId: string): Promise<TaskInfo> {
    const response = await api.get(`/api/v1/orchestrator/status/${taskId}`);
    return response.data;
  },

  /**
   * Get comprehensive system status
   */
  async getSystemStatus(): Promise<SystemStatus> {
    const response = await api.get('/api/v1/orchestrator/system/status');
    return response.data;
  },

  /**
   * Distribute a task across worktrees
   */
  async distributeWorktreeTask(task: WorktreeTask): Promise<TaskInfo> {
    const response = await api.post('/api/v1/orchestrator/worktree/distribute', task);
    return response.data;
  },

  /**
   * Get active worktree sessions
   */
  async getWorktreeSessions(): Promise<Record<string, any>> {
    const response = await api.get('/api/v1/orchestrator/worktree/sessions');
    return response.data;
  },

  /**
   * Monitor current resource utilization
   */
  async monitorResources(): Promise<ResourceSnapshot> {
    const response = await api.get('/api/v1/orchestrator/resources/monitor');
    return response.data;
  },

  /**
   * Get active resource alerts
   */
  async getResourceAlerts(): Promise<ResourceAlert[]> {
    const response = await api.get('/api/v1/orchestrator/resources/alerts');
    return response.data;
  },

  /**
   * Apply resource optimizations
   */
  async optimizeResources(): Promise<{
    optimizations_applied: string[];
    estimated_improvement: Record<string, number>;
    restart_required: boolean;
  }> {
    const response = await api.post('/api/v1/orchestrator/resources/optimize');
    return response.data;
  },

  /**
   * Shutdown the orchestrator gracefully
   */
  async shutdownOrchestrator(): Promise<{ message: string }> {
    const response = await api.delete('/api/v1/orchestrator/shutdown');
    return response.data;
  },

  /**
   * Get task history with optional filters
   */
  async getTaskHistory(filters?: {
    status?: string;
    agent_type?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }): Promise<TaskInfo[]> {
    const response = await api.get('/api/v1/orchestrator/tasks/history', { params: filters });
    return response.data;
  },

  /**
   * Cancel a running or pending task
   */
  async cancelTask(taskId: string): Promise<{ message: string }> {
    const response = await api.post(`/api/v1/orchestrator/tasks/${taskId}/cancel`);
    return response.data;
  },

  /**
   * Get agent metrics
   */
  async getAgentMetrics(agentName?: string): Promise<Record<string, any>> {
    const params = agentName ? { agent: agentName } : {};
    const response = await api.get('/api/v1/orchestrator/metrics/agents', { params });
    return response.data;
  },

  /**
   * Get task queue information
   */
  async getTaskQueue(): Promise<{
    size: number;
    tasks: Array<{
      task_id: string;
      priority: string;
      agent_type: string;
      created_at: string;
    }>;
  }> {
    const response = await api.get('/api/v1/orchestrator/queue');
    return response.data;
  },

  /**
   * Test orchestrator connectivity
   */
  async testConnection(): Promise<boolean> {
    try {
      const response = await api.get('/api/v1/orchestrator/agents');
      return response.status === 200;
    } catch {
      return false;
    }
  },

  /**
   * Get agent capabilities by category
   */
  async getCapabilities(category?: string): Promise<Record<string, string[]>> {
    const params = category ? { category } : {};
    const response = await api.get('/api/v1/orchestrator/capabilities', { params });
    return response.data;
  },

  /**
   * Scale agent pool
   */
  async scaleAgentPool(agentType: string, count: number): Promise<{
    success: boolean;
    message: string;
    current_count: number;
  }> {
    const response = await api.post('/api/v1/orchestrator/agents/scale', {
      agent_type: agentType,
      target_count: count,
    });
    return response.data;
  },

  /**
   * Get orchestrator configuration
   */
  async getConfiguration(): Promise<Record<string, any>> {
    const response = await api.get('/api/v1/orchestrator/config');
    return response.data;
  },

  /**
   * Update orchestrator configuration
   */
  async updateConfiguration(config: Record<string, any>): Promise<{
    success: boolean;
    message: string;
  }> {
    const response = await api.put('/api/v1/orchestrator/config', config);
    return response.data;
  },
};

// Export default for convenience
export default orchestratorApi;