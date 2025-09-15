/**
 * Roblox Sync Service
 * 
 * Manages synchronization between Dashboard, Backend, and Roblox environments.
 * Handles environment generation, status tracking, and real-time updates.
 */

import { api } from './api';
import { pusherService } from './pusher';
import { authSync } from './auth-sync';
import { store } from '../store';
import { addNotification } from '../store/slices/uiSlice';
import { 
  setRobloxEnvironments, 
  updateRobloxEnvironment, 
  setGenerationStatus 
} from '../store/slices/robloxSlice';

export interface RobloxEnvironment {
  id: string;
  name: string;
  theme: string;
  mapType: string;
  status: 'draft' | 'generating' | 'ready' | 'deployed' | 'error';
  spec: RobloxSpec;
  generatedAt?: string;
  downloadUrl?: string;
  previewUrl?: string;
  userId: string;
  conversationId?: string;
}

export interface RobloxSpec {
  environment_name: string;
  theme: string;
  map_type: 'obby' | 'open_world' | 'dungeon' | 'lab' | 'classroom' | 'puzzle' | 'arena';
  terrain?: string;
  npc_count?: number;
  difficulty?: 'easy' | 'medium' | 'hard';
  learning_objectives: string[];
  age_range?: string;
  assets?: string[];
  scripting?: string[];
  lighting?: string;
  weather?: string;
  notes?: string;
}

export interface GenerationProgress {
  requestId: string;
  stage: string;
  percentage: number;
  message: string;
  timestamp: number;
}

class RobloxSyncService {
  private static instance: RobloxSyncService | null = null;
  private subscriptions: Set<string> = new Set();
  private isInitialized = false;

  public static getInstance(): RobloxSyncService {
    if (!RobloxSyncService.instance) {
      RobloxSyncService.instance = new RobloxSyncService();
    }
    return RobloxSyncService.instance;
  }

  public async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      // Ensure auth and pusher are initialized
      await authSync.initialize();
      await pusherService.connect();

      // Load user's environments
      await this.loadUserEnvironments();

      this.isInitialized = true;
      console.log('✅ Roblox sync service initialized');
    } catch (error) {
      console.error('❌ Failed to initialize Roblox sync:', error);
      throw error;
    }
  }

  // Environment Management
  public async loadUserEnvironments(): Promise<void> {
    try {
      const response = await api.request<RobloxEnvironment[]>({
        method: 'GET',
        url: '/api/v1/roblox/environments'
      });

      store.dispatch(setRobloxEnvironments(response));
    } catch (error) {
      console.error('Failed to load environments:', error);
      store.dispatch(addNotification({
        type: 'error',
        message: 'Failed to load Roblox environments'
      }));
    }
  }

  public async createEnvironment(spec: RobloxSpec): Promise<string> {
    try {
      const response = await api.request<{ id: string; conversationId: string }>({
        method: 'POST',
        url: '/api/v1/roblox/environments',
        data: { spec }
      });

      // Subscribe to updates for this environment
      this.subscribeToEnvironment(response.conversationId);

      return response.id;
    } catch (error) {
      console.error('Failed to create environment:', error);
      throw new Error('Failed to create Roblox environment');
    }
  }

  public async generateEnvironment(environmentId: string): Promise<void> {
    try {
      const response = await api.request<{ requestId: string }>({
        method: 'POST',
        url: `/api/v1/roblox/environments/${environmentId}/generate`
      });

      store.dispatch(setGenerationStatus({
        environmentId,
        status: 'generating',
        requestId: response.requestId
      }));

      store.dispatch(addNotification({
        type: 'info',
        message: 'Environment generation started'
      }));
    } catch (error) {
      console.error('Failed to start generation:', error);
      store.dispatch(addNotification({
        type: 'error',
        message: 'Failed to start environment generation'
      }));
    }
  }

  // Real-time Synchronization
  public subscribeToEnvironment(conversationId: string): void {
    if (this.subscriptions.has(conversationId)) return;

    const subscription = pusherService.subscribe(
      `agent-chat-${conversationId}`,
      (message) => this.handleEnvironmentUpdate(conversationId, message)
    );

    this.subscriptions.add(subscription);
  }

  private handleEnvironmentUpdate(conversationId: string, message: any): void {
    try {
      const { type, payload } = message;

      switch (type) {
        case 'roblox_env_progress':
          this.handleGenerationProgress(payload);
          break;
        case 'roblox_env_ready':
          this.handleEnvironmentReady(payload);
          break;
        case 'roblox_env_error':
          this.handleEnvironmentError(payload);
          break;
        case 'agent_chat_token':
        case 'agent_chat_complete':
          this.handleAgentMessage(payload);
          break;
      }
    } catch (error) {
      console.error('Error handling environment update:', error);
    }
  }

  private handleGenerationProgress(payload: GenerationProgress): void {
    store.dispatch(setGenerationStatus({
      environmentId: payload.requestId,
      status: 'generating',
      progress: payload.percentage,
      stage: payload.stage,
      message: payload.message
    }));
  }

  private handleEnvironmentReady(payload: any): void {
    store.dispatch(updateRobloxEnvironment({
      id: payload.environmentId,
      status: 'ready',
      downloadUrl: payload.downloadUrl,
      previewUrl: payload.previewUrl
    }));

    store.dispatch(addNotification({
      type: 'success',
      message: 'Roblox environment is ready!'
    }));
  }

  private handleEnvironmentError(payload: any): void {
    store.dispatch(setGenerationStatus({
      environmentId: payload.requestId,
      status: 'error',
      error: payload.error
    }));

    store.dispatch(addNotification({
      type: 'error',
      message: `Generation failed: ${payload.error}`
    }));
  }

  private handleAgentMessage(payload: any): void {
    // Handle AI agent messages for UI updates
    store.dispatch(addNotification({
      type: 'info',
      message: payload.content || 'AI agent is responding...'
    }));
  }

  // Environment Operations
  public async deployEnvironment(environmentId: string): Promise<void> {
    try {
      await api.request({
        method: 'POST',
        url: `/api/v1/roblox/environments/${environmentId}/deploy`
      });

      store.dispatch(updateRobloxEnvironment({
        id: environmentId,
        status: 'deployed'
      }));

      store.dispatch(addNotification({
        type: 'success',
        message: 'Environment deployed to Roblox!'
      }));
    } catch (error) {
      console.error('Failed to deploy environment:', error);
      store.dispatch(addNotification({
        type: 'error',
        message: 'Failed to deploy environment'
      }));
    }
  }

  public async deleteEnvironment(environmentId: string): Promise<void> {
    try {
      await api.request({
        method: 'DELETE',
        url: `/api/v1/roblox/environments/${environmentId}`
      });

      await this.loadUserEnvironments();

      store.dispatch(addNotification({
        type: 'success',
        message: 'Environment deleted'
      }));
    } catch (error) {
      console.error('Failed to delete environment:', error);
      store.dispatch(addNotification({
        type: 'error',
        message: 'Failed to delete environment'
      }));
    }
  }

  // Utility Methods
  public isEnvironmentReady(environment: RobloxEnvironment): boolean {
    return environment.status === 'ready' && !!environment.downloadUrl;
  }

  public canDeploy(environment: RobloxEnvironment): boolean {
    return this.isEnvironmentReady(environment) && environment.status !== 'deployed';
  }

  public cleanup(): void {
    // Unsubscribe from all channels
    this.subscriptions.forEach(subscription => {
      pusherService.unsubscribe(subscription);
    });
    this.subscriptions.clear();
    this.isInitialized = false;
  }
}

export const robloxSync = RobloxSyncService.getInstance();
export default RobloxSyncService;
