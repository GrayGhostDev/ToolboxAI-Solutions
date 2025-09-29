/**
 * Agent Coordinator Service Integration
 * Provides interface to AI agent coordination system
 * Updated for 2025 standards with Pusher integration
 */

import { pusherService } from './pusher';
import { WebSocketMessageType } from '../types/websocket';

export interface Agent {
  id: string;
  name: string;
  type: 'content' | 'analysis' | 'roblox' | 'general';
  status: 'idle' | 'busy' | 'error' | 'offline';
  capabilities: string[];
  currentTask?: string;
  performance: {
    tasksCompleted: number;
    averageTime: number;
    successRate: number;
  };
  lastActivity: string;
}

export interface AgentTask {
  id: string;
  agentId: string;
  type: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  priority: 'low' | 'normal' | 'high' | 'critical';
  progress: number;
  parameters: any;
  result?: any;
  error?: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  estimatedDuration?: number;
}

export interface AgentStats {
  totalAgents: number;
  activeAgents: number;
  queuedTasks: number;
  completedTasks: number;
  averageResponseTime: number;
  systemLoad: number;
}

class AgentService {
  private baseUrl: string;
  private isEnabled: boolean;

  constructor() {
    this.baseUrl = import.meta.env.VITE_AGENT_COORDINATOR_URL || 'http://localhost:8888';
    this.isEnabled = import.meta.env.VITE_ENABLE_AGENTS === 'true';
  }

  // Check if agent service is enabled
  isAvailable(): boolean {
    return this.isEnabled;
  }

  // Get all available agents
  async getAgents(): Promise<Agent[]> {
    if (!this.isEnabled) return [];
    
    try {
      const response = await fetch(`${this.baseUrl}/agents`);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch agents:', error);
      return [];
    }
  }

  // Get agent by ID
  async getAgent(agentId: string): Promise<Agent | null> {
    if (!this.isEnabled) return null;
    
    try {
      const response = await fetch(`${this.baseUrl}/agents/${agentId}`);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch agent:', error);
      return null;
    }
  }

  // Create new task
  async createTask(agentId: string, taskType: string, parameters: any, priority: string = 'normal'): Promise<AgentTask | null> {
    if (!this.isEnabled) return null;
    
    try {
      const response = await fetch(`${this.baseUrl}/tasks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agentId,
          type: taskType,
          parameters,
          priority,
        }),
      });
      
      const task = await response.json();
      
      // Subscribe to task updates via Pusher
      pusherService.subscribe('agent-tasks', (message: any) => {
        if (message.type === WebSocketMessageType.AGENT_TASK && message.data.taskId === task.id) {
          this.handleTaskUpdate(message.data);
        }
      });
      
      return task;
    } catch (error) {
      console.error('Failed to create agent task:', error);
      return null;
    }
  }

  // Get all tasks
  async getTasks(status?: string): Promise<AgentTask[]> {
    if (!this.isEnabled) return [];
    
    try {
      const url = status ? `${this.baseUrl}/tasks?status=${status}` : `${this.baseUrl}/tasks`;
      const response = await fetch(url);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch agent tasks:', error);
      return [];
    }
  }

  // Cancel task
  async cancelTask(taskId: string): Promise<boolean> {
    if (!this.isEnabled) return false;
    
    try {
      const response = await fetch(`${this.baseUrl}/tasks/${taskId}/cancel`, {
        method: 'POST',
      });
      return response.ok;
    } catch (error) {
      console.error('Failed to cancel agent task:', error);
      return false;
    }
  }

  // Get system statistics
  async getStats(): Promise<AgentStats | null> {
    if (!this.isEnabled) return null;
    
    try {
      const response = await fetch(`${this.baseUrl}/stats`);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch agent stats:', error);
      return null;
    }
  }

  // Handle real-time task updates
  private handleTaskUpdate(data: any) {
    // Emit custom event for components to listen to
    window.dispatchEvent(new CustomEvent('agent-task-update', { detail: data }));
  }

  // Subscribe to agent events
  subscribeToEvents(callback: (event: any) => void): () => void {
    if (!this.isEnabled) return () => {};
    
    const subscriptionId = pusherService.subscribe('agent-status', callback);
    return () => pusherService.unsubscribe(subscriptionId);
  }

  // Get service health
  async getHealth(): Promise<{ status: string; details?: any }> {
    if (!this.isEnabled) return { status: 'disabled' };
    
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      return await response.json();
    } catch (error) {
      return { status: 'error', details: error };
    }
  }
}

export const agentService = new AgentService();
export default agentService;
