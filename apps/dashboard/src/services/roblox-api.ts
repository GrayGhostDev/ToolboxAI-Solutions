/**
 * Roblox API Service for Dashboard
 * Handles all Roblox-related API calls including OAuth2, conversation flow, and Rojo management
 */

import axios, { AxiosInstance } from 'axios';
import pusher from './pusher';
import { Channel } from 'pusher-js';

// Types
export interface ConversationStartResponse {
  success: boolean;
  session_id: string;
  current_stage: string;
  pusher_channel: string;
  initial_result?: any;
}

export interface ConversationInputResponse {
  success: boolean;
  result: {
    current_stage: string;
    result: any;
    next_stage: string;
    progress: number;
  };
}

export interface RobloxAuthResponse {
  success: boolean;
  authorization_url: string;
  state: string;
  expires_at: string;
}

export interface RojoProject {
  project_id: string;
  name: string;
  path: string;
  port: number;
  status: 'stopped' | 'starting' | 'running' | 'error';
  created_at: string;
  updated_at: string;
  user_id: string;
}

export interface RojoSyncStatus {
  connected: boolean;
  session_id?: string;
  project_name?: string;
  client_count: number;
  last_sync?: string;
  errors: string[];
}

export interface AssetUploadRequest {
  asset_type: 'Model' | 'Decal' | 'Audio' | 'Mesh' | 'Animation' | 'Plugin' | 'FontFamily' | 'Video';
  display_name: string;
  description: string;
  file_content_base64: string;
}

export interface DataStoreEntry {
  key: string;
  value: any;
  metadata?: Record<string, any>;
  user_ids?: string[];
}

export interface EnvironmentGenerationResult {
  success: boolean;
  project_id: string;
  rojo_port: number;
  sync_url: string;
  files_generated: number;
}

class RobloxAPIService {
  private api: AxiosInstance;
  private conversationChannels: Map<string, Channel> = new Map();
  private authWindow: Window | null = null;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.VITE_API_BASE_URL || 'http://localhost:8008',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token to requests
    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  // ==================== OAuth2 Authentication ====================

  async initiateOAuth(additionalScopes: string[] = []): Promise<RobloxAuthResponse> {
    const response = await this.api.post<RobloxAuthResponse>('/api/v1/roblox/auth/initiate', {
      additional_scopes: additionalScopes,
    });
    return response.data;
  }

  async openOAuthWindow(authUrl: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.authWindow = window.open(
        authUrl,
        'roblox-auth',
        'width=600,height=800,left=200,top=100'
      );

      if (!this.authWindow) {
        reject(new Error('Failed to open authentication window'));
        return;
      }

      // Check if window is closed
      const checkInterval = setInterval(() => {
        if (this.authWindow?.closed) {
          clearInterval(checkInterval);
          resolve();
        }
      }, 1000);

      // Timeout after 5 minutes
      setTimeout(() => {
        clearInterval(checkInterval);
        if (this.authWindow && !this.authWindow.closed) {
          this.authWindow.close();
        }
        reject(new Error('Authentication timeout'));
      }, 300000);
    });
  }

  async refreshToken(): Promise<{ access_token: string; expires_in: number }> {
    const response = await this.api.post('/api/v1/roblox/auth/refresh');
    return response.data;
  }

  async revokeToken(): Promise<void> {
    await this.api.post('/api/v1/roblox/auth/revoke');
  }

  // ==================== Conversation Flow ====================

  async startConversation(initialMessage?: string): Promise<ConversationStartResponse> {
    const response = await this.api.post<ConversationStartResponse>(
      '/api/v1/roblox/conversation/start',
      {
        initial_message: initialMessage || 'I want to create an educational Roblox experience',
      }
    );

    // Subscribe to Pusher channel for real-time updates
    if (response.data.pusher_channel) {
      this.subscribeToConversation(response.data.session_id, response.data.pusher_channel);
    }

    return response.data;
  }

  async processConversationInput(
    sessionId: string,
    userInput: string
  ): Promise<ConversationInputResponse> {
    const response = await this.api.post<ConversationInputResponse>(
      '/api/v1/roblox/conversation/input',
      {
        session_id: sessionId,
        user_input: userInput,
      }
    );
    return response.data;
  }

  async advanceConversationStage(sessionId: string): Promise<{ current_stage: string; progress: number }> {
    const response = await this.api.post('/api/v1/roblox/conversation/advance', null, {
      params: { session_id: sessionId },
    });
    return response.data;
  }

  async generateRobloxEnvironment(sessionId: string): Promise<EnvironmentGenerationResult> {
    const response = await this.api.post<{ success: boolean; generation_result: EnvironmentGenerationResult }>(
      '/api/v1/roblox/conversation/generate',
      null,
      {
        params: { session_id: sessionId },
      }
    );
    return response.data.generation_result;
  }

  private subscribeToConversation(sessionId: string, channelName: string): Channel {
    const channel = pusher.subscribe(channelName);
    this.conversationChannels.set(sessionId, channel);
    return channel;
  }

  unsubscribeFromConversation(sessionId: string): void {
    const channel = this.conversationChannels.get(sessionId);
    if (channel) {
      pusher.unsubscribe(channel.name);
      this.conversationChannels.delete(sessionId);
    }
  }

  getConversationChannel(sessionId: string): Channel | undefined {
    return this.conversationChannels.get(sessionId);
  }

  // ==================== Rojo Management ====================

  async checkRojoInstallation(): Promise<{ rojo_installed: boolean; base_port: number; max_projects: number }> {
    const response = await this.api.get('/api/v1/roblox/rojo/check');
    return response.data;
  }

  async listRojoProjects(): Promise<RojoProject[]> {
    const response = await this.api.get<{ projects: RojoProject[] }>('/api/v1/roblox/rojo/projects');
    return response.data.projects;
  }

  async getRojoProject(projectId: string): Promise<{ project: RojoProject; sync_status?: RojoSyncStatus }> {
    const response = await this.api.get(`/api/v1/roblox/rojo/project/${projectId}`);
    return response.data;
  }

  async startRojoProject(projectId: string): Promise<{ sync_status: RojoSyncStatus; connect_url: string }> {
    const response = await this.api.post(`/api/v1/roblox/rojo/project/${projectId}/start`);
    return response.data;
  }

  async stopRojoProject(projectId: string): Promise<boolean> {
    const response = await this.api.post(`/api/v1/roblox/rojo/project/${projectId}/stop`);
    return response.data.success;
  }

  async buildRojoProject(projectId: string): Promise<{ output_path: string; file_size: number }> {
    const response = await this.api.post(`/api/v1/roblox/rojo/project/${projectId}/build`);
    return response.data;
  }

  async deleteRojoProject(projectId: string): Promise<boolean> {
    const response = await this.api.delete(`/api/v1/roblox/rojo/project/${projectId}`);
    return response.data.success;
  }

  // ==================== Open Cloud API ====================

  async uploadAsset(asset: AssetUploadRequest): Promise<{ asset_id: string; asset_url: string }> {
    const response = await this.api.post('/api/v1/roblox/assets/upload', asset);
    return response.data;
  }

  async getAsset(assetId: string): Promise<any> {
    const response = await this.api.get(`/api/v1/roblox/assets/${assetId}`);
    return response.data.asset;
  }

  async setDataStoreEntry(
    universeId: string,
    datastoreName: string,
    entry: DataStoreEntry
  ): Promise<any> {
    const response = await this.api.post('/api/v1/roblox/datastore/set', {
      universe_id: universeId,
      datastore_name: datastoreName,
      key: entry.key,
      value: entry.value,
      metadata: entry.metadata,
    });
    return response.data.result;
  }

  async getDataStoreEntry(
    universeId: string,
    datastoreName: string,
    key: string
  ): Promise<DataStoreEntry> {
    const response = await this.api.get('/api/v1/roblox/datastore/get', {
      params: {
        universe_id: universeId,
        datastore_name: datastoreName,
        key,
      },
    });
    return response.data.entry;
  }

  async publishMessage(
    universeId: string,
    topic: string,
    message: Record<string, any>
  ): Promise<any> {
    const response = await this.api.post('/api/v1/roblox/messaging/publish', {
      universe_id: universeId,
      topic,
      message,
    });
    return response.data.result;
  }

  // ==================== Utility Methods ====================

  async fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const base64 = reader.result as string;
        // Remove data URL prefix
        const base64Content = base64.split(',')[1];
        resolve(base64Content);
      };
      reader.onerror = (error) => reject(error);
    });
  }

  async downloadRobloxProject(projectId: string, fileName: string): Promise<void> {
    const { output_path } = await this.buildRojoProject(projectId);

    // Create download link
    const link = document.createElement('a');
    link.href = output_path;
    link.download = fileName || 'project.rbxl';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  getRojoConnectUrl(port: number = 34872): string {
    // Default Rojo server for ToolboxAI-Solutions at localhost:34872
    return `http://localhost:${port}`;
  }

  // ==================== Environment Preview ====================

  async getEnvironmentPreview(sessionId: string): Promise<any> {
    const response = await this.api.post('/api/v1/roblox/environment/preview', {
      session_id: sessionId,
    });
    return response.data.preview;
  }

  async updateEnvironmentPreview(sessionId: string, updates: any): Promise<any> {
    const response = await this.api.patch('/api/v1/roblox/environment/preview', {
      session_id: sessionId,
      updates,
    });
    return response.data.preview;
  }

  // ==================== Status Monitoring ====================

  async getSystemStatus(): Promise<{
    rojo_available: boolean;
    oauth_configured: boolean;
    pusher_connected: boolean;
    active_projects: number;
  }> {
    try {
      const [rojoCheck, pusherStatus] = await Promise.all([
        this.checkRojoInstallation(),
        this.checkPusherConnection(),
      ]);

      const projects = await this.listRojoProjects();
      const activeProjects = projects.filter(p => p.status === 'running').length;

      return {
        rojo_available: rojoCheck.rojo_installed,
        oauth_configured: !!localStorage.getItem('roblox_auth_token'),
        pusher_connected: pusherStatus,
        active_projects: activeProjects,
      };
    } catch (error) {
      console.error('Error getting system status:', error);
      return {
        rojo_available: false,
        oauth_configured: false,
        pusher_connected: false,
        active_projects: 0,
      };
    }
  }

  private checkPusherConnection(): boolean {
    return pusher.connection.state === 'connected';
  }

  // ==================== Error Handling ====================

  handleError(error: any): string {
    if (error.response) {
      // Server responded with error
      return error.response.data.detail || error.response.data.message || 'An error occurred';
    } else if (error.request) {
      // Request made but no response
      return 'Unable to connect to server. Please check your connection.';
    } else {
      // Something else happened
      return error.message || 'An unexpected error occurred';
    }
  }
}

// Export singleton instance
const robloxAPI = new RobloxAPIService();
export default robloxAPI;