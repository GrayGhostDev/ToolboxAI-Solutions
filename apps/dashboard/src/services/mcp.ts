/**
 * MCP (Model Context Protocol) Service Integration
 * Provides interface to MCP server for AI model management
 * Updated for 2025 standards with Pusher integration
 */

import { pusherService } from './pusher';
import { WebSocketMessageType } from '../types/websocket';

export interface MCPModel {
  id: string;
  name: string;
  provider: string;
  status: 'available' | 'busy' | 'offline';
  capabilities: string[];
  performance: {
    latency: number;
    throughput: number;
    errorRate: number;
  };
}

export interface MCPContext {
  id: string;
  name: string;
  type: 'conversation' | 'document' | 'code' | 'data';
  size: number;
  lastUsed: string;
  models: string[];
}

export interface MCPTask {
  id: string;
  modelId: string;
  contextId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  result?: any;
  error?: string;
  createdAt: string;
  completedAt?: string;
}

class MCPService {
  private baseUrl: string;
  private isEnabled: boolean;

  constructor() {
    this.baseUrl = import.meta.env.VITE_MCP_SERVER_URL || 'http://localhost:9877';
    this.isEnabled = import.meta.env.VITE_ENABLE_MCP === 'true';
  }

  // Check if MCP is enabled
  isAvailable(): boolean {
    return this.isEnabled;
  }

  // Get available models
  async getModels(): Promise<MCPModel[]> {
    if (!this.isEnabled) return [];
    
    try {
      const response = await fetch(`${this.baseUrl}/models`);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch MCP models:', error);
      return [];
    }
  }

  // Get available contexts
  async getContexts(): Promise<MCPContext[]> {
    if (!this.isEnabled) return [];
    
    try {
      const response = await fetch(`${this.baseUrl}/contexts`);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch MCP contexts:', error);
      return [];
    }
  }

  // Create new task
  async createTask(modelId: string, contextId: string, prompt: string): Promise<MCPTask | null> {
    if (!this.isEnabled) return null;
    
    try {
      const response = await fetch(`${this.baseUrl}/tasks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          modelId,
          contextId,
          prompt,
        }),
      });
      
      const task = await response.json();
      
      // Subscribe to task updates via Pusher
      pusherService.subscribe('mcp-tasks', (message: any) => {
        if (message.type === 'MCP_TASK_UPDATE' && message.data.taskId === task.id) {
          // Handle task update
          this.handleTaskUpdate(message.data);
        }
      });
      
      return task;
    } catch (error) {
      console.error('Failed to create MCP task:', error);
      return null;
    }
  }

  // Get task status
  async getTask(taskId: string): Promise<MCPTask | null> {
    if (!this.isEnabled) return null;
    
    try {
      const response = await fetch(`${this.baseUrl}/tasks/${taskId}`);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch MCP task:', error);
      return null;
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
      console.error('Failed to cancel MCP task:', error);
      return false;
    }
  }

  // Handle real-time task updates
  private handleTaskUpdate(data: any) {
    // Emit custom event for components to listen to
    window.dispatchEvent(new CustomEvent('mcp-task-update', { detail: data }));
  }

  // Subscribe to MCP events
  subscribeToEvents(callback: (event: any) => void): () => void {
    if (!this.isEnabled) return () => {};
    
    const subscriptionId = pusherService.subscribe('mcp-events', callback);
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

export const mcpService = new MCPService();
export default mcpService;
