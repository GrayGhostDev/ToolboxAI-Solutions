/**
 * Agent API Hook
 * 
 * Custom hook for interacting with the agent system API endpoints.
 * Provides methods for agent management, task execution, and monitoring.
 * 
 * @author ToolboxAI Team
 * @created 2025-09-21
 * @version 1.0.0
 */

import { useState, useCallback } from 'react';

interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

interface TaskRequest {
  agent_type: string;
  task_type: string;
  task_data: Record<string, any>;
  user_id?: string;
}

interface TaskResult {
  success: boolean;
  task_id?: string;
  result?: any;
  execution_time?: number;
  error?: string;
}

export const useAgentAPI = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8009';

  const makeAPICall = useCallback(async <T = any>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<APIResponse<T>> => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${apiBaseUrl}/api/v1${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return { success: true, data };

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl]);

  // Agent status methods
  const getAgentsStatus = useCallback(async () => {
    return makeAPICall('/agents/status');
  }, [makeAPICall]);

  const getAgentStatus = useCallback(async (agentId: string) => {
    return makeAPICall(`/agents/status/${agentId}`);
  }, [makeAPICall]);

  const getSystemMetrics = useCallback(async () => {
    return makeAPICall('/agents/metrics');
  }, [makeAPICall]);

  const getAgentHealth = useCallback(async () => {
    return makeAPICall('/agents/health');
  }, [makeAPICall]);

  // Task execution methods
  const executeContentGeneration = useCallback(async (taskData: {
    subject: string;
    grade_level: number;
    objectives: string[];
    context?: Record<string, any>;
  }) => {
    return makeAPICall('/agents/content/generate', {
      method: 'POST',
      body: JSON.stringify(taskData),
    });
  }, [makeAPICall]);

  const executeQuizGeneration = useCallback(async (taskData: {
    subject: string;
    objectives: string[];
    num_questions: number;
    difficulty: string;
    context?: Record<string, any>;
  }) => {
    return makeAPICall('/agents/quiz/generate', {
      method: 'POST',
      body: JSON.stringify(taskData),
    });
  }, [makeAPICall]);

  const executeTerrainGeneration = useCallback(async (taskData: {
    subject: string;
    terrain_type: string;
    complexity: string;
    features: string[];
    context?: Record<string, any>;
  }) => {
    return makeAPICall('/agents/terrain/generate', {
      method: 'POST',
      body: JSON.stringify(taskData),
    });
  }, [makeAPICall]);

  const executeScriptGeneration = useCallback(async (taskData: {
    script_type: string;
    functionality: string;
    requirements: string[];
    context?: Record<string, any>;
  }) => {
    return makeAPICall('/agents/script/generate', {
      method: 'POST',
      body: JSON.stringify(taskData),
    });
  }, [makeAPICall]);

  const executeCodeReview = useCallback(async (taskData: {
    code: string;
    language: string;
    review_type: string;
    context?: Record<string, any>;
  }) => {
    return makeAPICall('/agents/code/review', {
      method: 'POST',
      body: JSON.stringify(taskData),
    });
  }, [makeAPICall]);

  const executeRobloxAssetManagement = useCallback(async (taskData: {
    asset_type: string;
    action: string;
    asset_data: Record<string, any>;
    context?: Record<string, any>;
  }) => {
    return makeAPICall('/agents/roblox/asset', {
      method: 'POST',
      body: JSON.stringify(taskData),
    });
  }, [makeAPICall]);

  const executeRobloxTesting = useCallback(async (taskData: {
    test_type: string;
    test_data: Record<string, any>;
    context?: Record<string, any>;
  }) => {
    return makeAPICall('/agents/roblox/test', {
      method: 'POST',
      body: JSON.stringify(taskData),
    });
  }, [makeAPICall]);

  const executeRobloxAnalytics = useCallback(async (taskData: {
    data_type: string;
    analysis_data: Record<string, any>;
    context?: Record<string, any>;
  }) => {
    return makeAPICall('/agents/roblox/analytics', {
      method: 'POST',
      body: JSON.stringify(taskData),
    });
  }, [makeAPICall]);

  // Generic task execution method
  const executeTask = useCallback(async (taskRequest: TaskRequest): Promise<TaskResult> => {
    const { agent_type, task_type, task_data } = taskRequest;

    // Route to specific endpoint based on agent type and task type
    let endpoint = '';
    const requestData = task_data;

    switch (agent_type) {
      case 'content':
        if (task_type === 'generate_content') {
          endpoint = '/agents/content/generate';
        }
        break;
      case 'quiz':
        if (task_type === 'generate_quiz') {
          endpoint = '/agents/quiz/generate';
        }
        break;
      case 'terrain':
        if (task_type === 'generate_terrain') {
          endpoint = '/agents/terrain/generate';
        }
        break;
      case 'script':
        if (task_type === 'generate_script') {
          endpoint = '/agents/script/generate';
        }
        break;
      case 'code_review':
        if (task_type === 'review_code') {
          endpoint = '/agents/code/review';
        }
        break;
      case 'roblox_asset':
        if (task_type === 'manage_asset') {
          endpoint = '/agents/roblox/asset';
        }
        break;
      case 'roblox_testing':
        if (task_type === 'run_tests') {
          endpoint = '/agents/roblox/test';
        }
        break;
      case 'roblox_analytics':
        if (task_type === 'analyze_data') {
          endpoint = '/agents/roblox/analytics';
        }
        break;
      default:
        return {
          success: false,
          error: `Unknown agent type: ${agent_type}`
        };
    }

    if (!endpoint) {
      return {
        success: false,
        error: `Unknown task type: ${task_type} for agent: ${agent_type}`
      };
    }

    const response = await makeAPICall(endpoint, {
      method: 'POST',
      body: JSON.stringify(requestData),
    });

    if (response.success) {
      return {
        success: true,
        task_id: response.data?.task_id,
        result: response.data?.result,
        execution_time: response.data?.execution_time
      };
    } else {
      return {
        success: false,
        error: response.error || response.message || 'Task execution failed'
      };
    }
  }, [makeAPICall]);

  // Task status methods
  const getTaskStatus = useCallback(async (taskId: string) => {
    return makeAPICall(`/agents/tasks/${taskId}`);
  }, [makeAPICall]);

  return {
    loading,
    error,
    
    // Agent status
    getAgentsStatus,
    getAgentStatus,
    getSystemMetrics,
    getAgentHealth,
    
    // Task execution
    executeTask,
    executeContentGeneration,
    executeQuizGeneration,
    executeTerrainGeneration,
    executeScriptGeneration,
    executeCodeReview,
    executeRobloxAssetManagement,
    executeRobloxTesting,
    executeRobloxAnalytics,
    
    // Task management
    getTaskStatus,
  };
};

export default useAgentAPI;
