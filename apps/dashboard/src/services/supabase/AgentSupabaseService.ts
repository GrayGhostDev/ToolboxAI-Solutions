/**
 * Agent Supabase Service
 *
 * Service layer for interacting with Supabase agent tables.
 * Provides methods for fetching agent instances, executions, metrics, and health data.
 *
 * @module services/supabase/AgentSupabaseService
 * @version 1.0.0
 */

import { supabase } from './client';
import type { RealtimeChannel } from '@supabase/supabase-js';

// Type definitions
export interface AgentInstance {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_type: string;
  status: 'idle' | 'busy' | 'error' | 'offline';
  health_status: 'healthy' | 'degraded' | 'unhealthy';
  created_at: string;
  updated_at: string;
  last_heartbeat: string;
  metadata?: Record<string, any>;
}

export interface AgentExecution {
  id: string;
  agent_instance_id: string;
  execution_id: string;
  task_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
  error_message?: string;
  result?: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface AgentMetrics {
  id: string;
  agent_instance_id: string;
  timestamp: string;
  cpu_usage: number;
  memory_usage: number;
  active_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  avg_response_time_ms: number;
  error_rate: number;
  metadata?: Record<string, any>;
}

export interface SystemHealth {
  id: string;
  timestamp: string;
  total_agents: number;
  healthy_agents: number;
  busy_agents: number;
  error_agents: number;
  offline_agents: number;
  total_executions: number;
  success_rate: number;
  avg_response_time_ms: number;
  error_rate: number;
  metadata?: Record<string, any>;
}

export interface AgentHealthSummary {
  total_agents: number;
  healthy_agents: number;
  busy_agents: number;
  error_agents: number;
  success_rate: number;
  avg_response_time: number;
}

/**
 * Agent Supabase Service Class
 *
 * Provides methods for interacting with agent-related Supabase tables.
 */
class AgentSupabaseServiceClass {
  /**
   * Get all agent instances
   * @returns {Promise<AgentInstance[]>} Array of agent instances
   */
  async getAgentInstances(): Promise<AgentInstance[]> {
    const { data, error } = await supabase
      .from('agent_instances')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) {
      console.error('Error fetching agent instances:', error);
      throw new Error(`Failed to fetch agent instances: ${error.message}`);
    }

    return data || [];
  }

  /**
   * Get agent executions
   * @param {string} [agentId] - Optional agent ID to filter by
   * @param {number} [limit=100] - Maximum number of executions to return
   * @returns {Promise<AgentExecution[]>} Array of executions
   */
  async getAgentExecutions(agentId?: string, limit: number = 100): Promise<AgentExecution[]> {
    let query = supabase
      .from('agent_executions')
      .select('*')
      .order('started_at', { ascending: false })
      .limit(limit);

    // Filter by agent if provided
    if (agentId) {
      // First get the agent instance ID from agent_id
      const { data: instances } = await supabase
        .from('agent_instances')
        .select('id')
        .eq('agent_id', agentId);

      if (instances && instances.length > 0) {
        const instanceIds = instances.map(i => i.id);
        query = query.in('agent_instance_id', instanceIds);
      }
    }

    const { data, error } = await query;

    if (error) {
      console.error('Error fetching agent executions:', error);
      throw new Error(`Failed to fetch agent executions: ${error.message}`);
    }

    return data || [];
  }

  /**
   * Get agent metrics
   * @param {string} [agentId] - Optional agent ID to filter by
   * @param {number} [hours=24] - Number of hours of metrics to fetch
   * @returns {Promise<AgentMetrics[]>} Array of metrics
   */
  async getAgentMetrics(agentId?: string, hours: number = 24): Promise<AgentMetrics[]> {
    const since = new Date();
    since.setHours(since.getHours() - hours);

    let query = supabase
      .from('agent_metrics')
      .select('*')
      .gte('timestamp', since.toISOString())
      .order('timestamp', { ascending: false });

    // Filter by agent if provided
    if (agentId) {
      const { data: instances } = await supabase
        .from('agent_instances')
        .select('id')
        .eq('agent_id', agentId);

      if (instances && instances.length > 0) {
        const instanceIds = instances.map(i => i.id);
        query = query.in('agent_instance_id', instanceIds);
      }
    }

    const { data, error } = await query;

    if (error) {
      console.error('Error fetching agent metrics:', error);
      throw new Error(`Failed to fetch agent metrics: ${error.message}`);
    }

    return data || [];
  }

  /**
   * Get system health records
   * @param {number} [hours=24] - Number of hours of health data to fetch
   * @returns {Promise<SystemHealth[]>} Array of system health records
   */
  async getSystemHealth(hours: number = 24): Promise<SystemHealth[]> {
    const since = new Date();
    since.setHours(since.getHours() - hours);

    const { data, error } = await supabase
      .from('system_health')
      .select('*')
      .gte('timestamp', since.toISOString())
      .order('timestamp', { ascending: false });

    if (error) {
      console.error('Error fetching system health:', error);
      throw new Error(`Failed to fetch system health: ${error.message}`);
    }

    return data || [];
  }

  /**
   * Get aggregated agent health summary
   * @returns {Promise<AgentHealthSummary>} Health summary object
   */
  async getAgentHealthSummary(): Promise<AgentHealthSummary> {
    // Get all agents
    const { data: agents, error: agentsError } = await supabase
      .from('agent_instances')
      .select('status, health_status');

    if (agentsError) {
      console.error('Error fetching agents for summary:', agentsError);
      throw new Error(`Failed to fetch agent health summary: ${agentsError.message}`);
    }

    // Get recent executions for success rate (last 24 hours)
    const since = new Date();
    since.setHours(since.getHours() - 24);

    const { data: executions, error: executionsError } = await supabase
      .from('agent_executions')
      .select('status, duration_ms')
      .gte('started_at', since.toISOString());

    if (executionsError) {
      console.error('Error fetching executions for summary:', executionsError);
    }

    // Calculate summary
    const total_agents = agents?.length || 0;
    const healthy_agents = agents?.filter(a => a.health_status === 'healthy').length || 0;
    const busy_agents = agents?.filter(a => a.status === 'busy').length || 0;
    const error_agents = agents?.filter(a => a.health_status === 'unhealthy' || a.status === 'error').length || 0;

    const total_executions = executions?.length || 0;
    const successful_executions = executions?.filter(e => e.status === 'completed').length || 0;
    const success_rate = total_executions > 0 ? (successful_executions / total_executions) * 100 : 0;

    const avg_response_time = total_executions > 0
      ? (executions?.reduce((sum, e) => sum + (e.duration_ms || 0), 0) || 0) / total_executions
      : 0;

    return {
      total_agents,
      healthy_agents,
      busy_agents,
      error_agents,
      success_rate: Math.round(success_rate * 100) / 100,
      avg_response_time: Math.round(avg_response_time),
    };
  }

  /**
   * Subscribe to real-time agent updates
   * @param {Function} callback - Callback function for updates
   * @returns {RealtimeChannel} Subscription channel
   */
  subscribeToAgentUpdates(callback: (payload: any) => void): RealtimeChannel {
    const channel = supabase
      .channel('agent-updates')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'agent_instances',
        },
        (payload) => callback({ ...payload, table: 'agent_instances' })
      )
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'agent_executions',
        },
        (payload) => callback({ ...payload, table: 'agent_executions' })
      )
      .subscribe();

    return channel;
  }

  /**
   * Subscribe to real-time system health updates
   * @param {Function} callback - Callback function for updates
   * @returns {RealtimeChannel} Subscription channel
   */
  subscribeToSystemHealth(callback: (payload: any) => void): RealtimeChannel {
    const channel = supabase
      .channel('system-health-updates')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'system_health',
        },
        callback
      )
      .subscribe();

    return channel;
  }
}

// Export singleton instance
export const AgentSupabaseService = new AgentSupabaseServiceClass();

// Export helper function
export { isSupabaseConfigured } from './client';

export default AgentSupabaseService;
