/**
 * React Hook for Supabase Agent Integration
 * 
 * This hook provides React integration for Supabase agent data,
 * including real-time updates and state management.
 * 
 * Compatible with React 19 concurrent features and strict mode.
 * 
 * Features:
 * - Agent instances management
 * - Task execution tracking
 * - Performance metrics
 * - Real-time subscriptions
 * - Error handling and loading states
 * 
 * @author ToolboxAI Team
 * @created 2025-09-21
 * @version 1.0.0
 */

import { useState, useEffect, useCallback, useRef, useMemo, startTransition } from 'react';
import { 
  type AgentInstance, 
  type AgentExecution, 
  type AgentMetrics, 
  type SystemHealth,
  AgentSupabaseService,
  isSupabaseConfigured 
} from '../lib/supabase';

export interface UseSupabaseAgentState {
  agents: AgentInstance[];
  executions: AgentExecution[];
  metrics: AgentMetrics[];
  systemHealth: SystemHealth[];
  healthSummary: {
    total_agents: number;
    healthy_agents: number;
    busy_agents: number;
    error_agents: number;
    success_rate: number;
    avg_response_time: number;
  };
  loading: {
    agents: boolean;
    executions: boolean;
    metrics: boolean;
    systemHealth: boolean;
    healthSummary: boolean;
  };
  error: {
    agents: string | null;
    executions: string | null;
    metrics: string | null;
    systemHealth: string | null;
    healthSummary: string | null;
  };
  configured: boolean;
}

export interface UseSupabaseAgentOptions {
  enableRealtime?: boolean;
  refreshInterval?: number;
  autoRefresh?: boolean;
  metricsHours?: number;
  healthHours?: number;
  executionLimit?: number;
}

const defaultOptions: UseSupabaseAgentOptions = {
  enableRealtime: true,
  refreshInterval: 30000, // 30 seconds
  autoRefresh: true,
  metricsHours: 24,
  healthHours: 24,
  executionLimit: 100
};

/**
 * Hook for managing Supabase agent data and real-time updates
 */
export const useSupabaseAgent = (options: UseSupabaseAgentOptions = {}) => {
  const opts = { ...defaultOptions, ...options };
  const subscriptionRef = useRef<any>(null);
  const healthSubscriptionRef = useRef<any>(null);
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const [state, setState] = useState<UseSupabaseAgentState>({
    agents: [],
    executions: [],
    metrics: [],
    systemHealth: [],
    healthSummary: {
      total_agents: 0,
      healthy_agents: 0,
      busy_agents: 0,
      error_agents: 0,
      success_rate: 0,
      avg_response_time: 0
    },
    loading: {
      agents: false,
      executions: false,
      metrics: false,
      systemHealth: false,
      healthSummary: false
    },
    error: {
      agents: null,
      executions: null,
      metrics: null,
      systemHealth: null,
      healthSummary: null
    },
    configured: isSupabaseConfigured()
  });

  // Helper function to update loading state (React 19 compatible)
  const setLoading = useCallback((key: keyof UseSupabaseAgentState['loading'], value: boolean) => {
    startTransition(() => {
      setState(prev => ({
        ...prev,
        loading: {
          ...prev.loading,
          [key]: value
        }
      }));
    });
  }, []);

  // Helper function to update error state (React 19 compatible)
  const setError = useCallback((key: keyof UseSupabaseAgentState['error'], value: string | null) => {
    startTransition(() => {
      setState(prev => ({
        ...prev,
        error: {
          ...prev.error,
          [key]: value
        }
      }));
    });
  }, []);

  // Fetch agent instances
  const fetchAgents = useCallback(async () => {
    if (!state.configured) return;

    setLoading('agents', true);
    setError('agents', null);

    try {
      const agents = await AgentSupabaseService.getAgentInstances();
      startTransition(() => {
        setState(prev => ({
          ...prev,
          agents
        }));
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch agents';
      setError('agents', errorMessage);
      console.error('Error fetching agents:', error);
    } finally {
      setLoading('agents', false);
    }
  }, [state.configured, setLoading, setError]);

  // Fetch agent executions
  const fetchExecutions = useCallback(async (agentId?: string) => {
    if (!state.configured) return;

    setLoading('executions', true);
    setError('executions', null);

    try {
      const executions = await AgentSupabaseService.getAgentExecutions(agentId, opts.executionLimit);
      startTransition(() => {
        setState(prev => ({
          ...prev,
          executions
        }));
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch executions';
      setError('executions', errorMessage);
      console.error('Error fetching executions:', error);
    } finally {
      setLoading('executions', false);
    }
  }, [state.configured, opts.executionLimit, setLoading, setError]);

  // Fetch agent metrics
  const fetchMetrics = useCallback(async (agentId?: string) => {
    if (!state.configured) return;

    setLoading('metrics', true);
    setError('metrics', null);

    try {
      const metrics = await AgentSupabaseService.getAgentMetrics(agentId, opts.metricsHours);
      startTransition(() => {
        setState(prev => ({
          ...prev,
          metrics
        }));
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch metrics';
      setError('metrics', errorMessage);
      console.error('Error fetching metrics:', error);
    } finally {
      setLoading('metrics', false);
    }
  }, [state.configured, opts.metricsHours, setLoading, setError]);

  // Fetch system health
  const fetchSystemHealth = useCallback(async () => {
    if (!state.configured) return;

    setLoading('systemHealth', true);
    setError('systemHealth', null);

    try {
      const systemHealth = await AgentSupabaseService.getSystemHealth(opts.healthHours);
      startTransition(() => {
        setState(prev => ({
          ...prev,
          systemHealth
        }));
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch system health';
      setError('systemHealth', errorMessage);
      console.error('Error fetching system health:', error);
    } finally {
      setLoading('systemHealth', false);
    }
  }, [state.configured, opts.healthHours, setLoading, setError]);

  // Fetch health summary
  const fetchHealthSummary = useCallback(async () => {
    if (!state.configured) return;

    setLoading('healthSummary', true);
    setError('healthSummary', null);

    try {
      const healthSummary = await AgentSupabaseService.getAgentHealthSummary();
      startTransition(() => {
        setState(prev => ({
          ...prev,
          healthSummary
        }));
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch health summary';
      setError('healthSummary', errorMessage);
      console.error('Error fetching health summary:', error);
    } finally {
      setLoading('healthSummary', false);
    }
  }, [state.configured, setLoading, setError]);

  // Fetch all data
  const fetchAll = useCallback(async (agentId?: string) => {
    await Promise.all([
      fetchAgents(),
      fetchExecutions(agentId),
      fetchMetrics(agentId),
      fetchSystemHealth(),
      fetchHealthSummary()
    ]);
  }, [fetchAgents, fetchExecutions, fetchMetrics, fetchSystemHealth, fetchHealthSummary]);

  // Setup real-time subscriptions
  const setupRealtime = useCallback(() => {
    if (!state.configured || !opts.enableRealtime) return;

    // Clean up existing subscriptions
    if (subscriptionRef.current) {
      subscriptionRef.current.unsubscribe();
    }
    if (healthSubscriptionRef.current) {
      healthSubscriptionRef.current.unsubscribe();
    }

    try {
      // Subscribe to agent updates (React 19 compatible)
      subscriptionRef.current = AgentSupabaseService.subscribeToAgentUpdates((payload) => {
        console.log('Agent update received:', payload);
        
        // Use startTransition for non-urgent updates
        startTransition(() => {
          // Refresh relevant data based on the update
          if (payload.table === 'agent_instances') {
            fetchAgents();
            fetchHealthSummary();
          } else if (payload.table === 'agent_executions') {
            fetchExecutions();
            fetchHealthSummary();
          }
        });
      });

      // Subscribe to system health updates (React 19 compatible)
      healthSubscriptionRef.current = AgentSupabaseService.subscribeToSystemHealth((payload) => {
        console.log('System health update received:', payload);
        startTransition(() => {
          fetchSystemHealth();
        });
      });

      console.log('Real-time subscriptions established');
    } catch (error) {
      console.error('Failed to setup real-time subscriptions:', error);
    }
  }, [state.configured, opts.enableRealtime, fetchAgents, fetchExecutions, fetchHealthSummary, fetchSystemHealth]);

  // Setup auto-refresh interval
  const setupAutoRefresh = useCallback(() => {
    if (!state.configured || !opts.autoRefresh || !opts.refreshInterval) return;

    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
    }

    refreshIntervalRef.current = setInterval(() => {
      console.log('Auto-refreshing agent data');
      fetchAll();
    }, opts.refreshInterval);

    console.log(`Auto-refresh enabled with ${opts.refreshInterval}ms interval`);
  }, [state.configured, opts.autoRefresh, opts.refreshInterval, fetchAll]);

  // Initialize data and subscriptions (React 19 compatible)
  useEffect(() => {
    let mounted = true; // Track component mount status for React 19 strict mode
    
    if (!state.configured) {
      console.warn('Supabase not configured, agent hook disabled');
      return;
    }

    // Initial data fetch with mount check
    const initializeData = async () => {
      if (!mounted) return;
      await fetchAll();
    };

    // Setup services with mount check
    const initializeServices = () => {
      if (!mounted) return;
      setupRealtime();
      setupAutoRefresh();
    };

    // Execute initialization
    initializeData().then(() => {
      if (mounted) {
        initializeServices();
      }
    });

    // Cleanup function (React 19 compatible)
    return () => {
      mounted = false; // Mark as unmounted
      
      if (subscriptionRef.current) {
        try {
          subscriptionRef.current.unsubscribe();
        } catch (error) {
          console.warn('Error unsubscribing from agent updates:', error);
        }
      }
      if (healthSubscriptionRef.current) {
        try {
          healthSubscriptionRef.current.unsubscribe();
        } catch (error) {
          console.warn('Error unsubscribing from health updates:', error);
        }
      }
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [state.configured]); // Simplified dependencies for React 19

  // Return state and actions
  return {
    ...state,
    actions: {
      fetchAll,
      fetchAgents,
      fetchExecutions,
      fetchMetrics,
      fetchSystemHealth,
      fetchHealthSummary,
      refresh: fetchAll
    }
  };
};

/**
 * Hook for a specific agent's data
 */
export const useSupabaseAgentById = (agentId: string, options: UseSupabaseAgentOptions = {}) => {
  const hook = useSupabaseAgent(options);
  
  // Filter data for specific agent
  const agentData = {
    ...hook,
    agent: hook.agents.find(a => a.agent_id === agentId),
    executions: hook.executions.filter(e => {
      // Find executions for this agent
      const agent = hook.agents.find(a => a.agent_id === agentId);
      return agent ? e.agent_instance_id === agent.id : false;
    }),
    metrics: hook.metrics.filter(m => {
      // Find metrics for this agent
      const agent = hook.agents.find(a => a.agent_id === agentId);
      return agent ? m.agent_instance_id === agent.id : false;
    }),
    actions: {
      ...hook.actions,
      fetchExecutions: () => hook.actions.fetchExecutions(agentId),
      fetchMetrics: () => hook.actions.fetchMetrics(agentId),
      refresh: () => hook.actions.fetchAll(agentId)
    }
  };

  return agentData;
};

/**
 * Hook for system-wide health monitoring
 */
export const useSupabaseSystemHealth = (options: Omit<UseSupabaseAgentOptions, 'executionLimit'> = {}) => {
  const opts = { ...defaultOptions, ...options };
  const hook = useSupabaseAgent(opts);

  return {
    systemHealth: hook.systemHealth,
    healthSummary: hook.healthSummary,
    loading: {
      systemHealth: hook.loading.systemHealth,
      healthSummary: hook.loading.healthSummary
    },
    error: {
      systemHealth: hook.error.systemHealth,
      healthSummary: hook.error.healthSummary
    },
    configured: hook.configured,
    actions: {
      fetchSystemHealth: hook.actions.fetchSystemHealth,
      fetchHealthSummary: hook.actions.fetchHealthSummary,
      refresh: () => Promise.all([
        hook.actions.fetchSystemHealth(),
        hook.actions.fetchHealthSummary()
      ])
    }
  };
};

export default useSupabaseAgent;
