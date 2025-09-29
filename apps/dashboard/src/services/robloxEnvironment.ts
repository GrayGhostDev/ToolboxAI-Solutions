/**
 * Roblox Environment Service
 * Handles communication with backend for Roblox environment creation via Rojo API
 */

import ApiClient from './api';

export interface EnvironmentCreationRequest {
  name: string;
  description: string;
  grade_level?: string;
  subject?: string;
  max_players?: number;
  settings?: Record<string, any>;
}

export interface EnvironmentCreationResponse {
  success: boolean;
  environment_name: string;
  project_path?: string;
  rojo_url?: string;
  components?: Record<string, any>;
  error?: string;
  created_at: string;
}

export interface EnvironmentStatusResponse {
  environment_name: string;
  status: string;
  players: number;
  last_updated: string;
  rojo_connected: boolean;
  error?: string;
}

export interface RojoInfoResponse {
  success: boolean;
  rojo_info?: any;
  rojo_url?: string;
  error?: string;
  message?: string;
}

export interface RojoConnectionResponse {
  success: boolean;
  rojo_connected: boolean;
  rojo_host?: string;
  rojo_port?: number;
  rojo_url?: string;
  error?: string;
}

class RobloxEnvironmentService {
  private apiClient: ApiClient;

  constructor() {
    this.apiClient = new ApiClient();
  }

  /**
   * Generate a preview of the environment without creating it
   */
  async previewEnvironment(request: EnvironmentCreationRequest): Promise<any> {
    try {
      const response = await this.apiClient.post<any>(
        '/api/v1/roblox/environment/preview',
        request
      );
      return response;
    } catch (error) {
      console.error('Environment preview failed:', error);
      throw error;
    }
  }

  /**
   * Create a Roblox environment from natural language description
   */
  async createEnvironment(request: EnvironmentCreationRequest): Promise<EnvironmentCreationResponse> {
    try {
      const response = await this.apiClient.post<EnvironmentCreationResponse>(
        '/api/v1/roblox/environment/create',
        request
      );
      return response;
    } catch (error) {
      console.error('Environment creation failed:', error);
      throw error;
    }
  }

  /**
   * Get the status of a created environment
   */
  async getEnvironmentStatus(environmentName: string): Promise<EnvironmentStatusResponse> {
    try {
      const response = await this.apiClient.get<EnvironmentStatusResponse>(
        `/api/v1/roblox/environment/status/${encodeURIComponent(environmentName)}`
      );
      return response;
    } catch (error) {
      console.error('Failed to get environment status:', error);
      throw error;
    }
  }

  /**
   * Get Rojo server information
   */
  async getRojoInfo(): Promise<RojoInfoResponse> {
    try {
      const response = await this.apiClient.get<RojoInfoResponse>(
        '/api/v1/roblox/environment/rojo/info'
      );
      return response;
    } catch (error) {
      console.error('Failed to get Rojo info:', error);
      throw error;
    }
  }

  /**
   * Check if Rojo is running and accessible
   */
  async checkRojoConnection(): Promise<RojoConnectionResponse> {
    try {
      const response = await this.apiClient.post<RojoConnectionResponse>(
        '/api/v1/roblox/environment/rojo/check'
      );
      return response;
    } catch (error) {
      console.error('Failed to check Rojo connection:', error);
      throw error;
    }
  }

  /**
   * List environments created by the current user
   */
  async listUserEnvironments(): Promise<{ success: boolean; environments: any[] }> {
    try {
      const response = await this.apiClient.get<{ success: boolean; environments: any[] }>(
        '/api/v1/roblox/environment/list'
      );
      return response;
    } catch (error) {
      console.error('Failed to list environments:', error);
      throw error;
    }
  }

  /**
   * Delete an environment
   */
  async deleteEnvironment(environmentName: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await this.apiClient.delete<{ success: boolean; message: string }>(
        `/api/v1/roblox/environment/${encodeURIComponent(environmentName)}`
      );
      return response;
    } catch (error) {
      console.error('Failed to delete environment:', error);
      throw error;
    }
  }

  /**
   * Parse natural language description into structured components
   * This is a client-side helper for preview purposes
   */
  parseDescription(description: string): {
    terrain: string[];
    buildings: string[];
    objects: string[];
    lighting: string;
    effects: string[];
  } {
    const components = {
      terrain: [] as string[],
      buildings: [] as string[],
      objects: [] as string[],
      lighting: '',
      effects: [] as string[]
    };

    const desc = description.toLowerCase();

    // Terrain detection
    if (desc.includes('mountain') || desc.includes('hill')) {
      components.terrain.push('Mountains/Hills');
    }
    if (desc.includes('forest') || desc.includes('trees')) {
      components.terrain.push('Forest');
    }
    if (desc.includes('desert') || desc.includes('sand')) {
      components.terrain.push('Desert');
    }
    if (desc.includes('water') || desc.includes('ocean') || desc.includes('lake')) {
      components.terrain.push('Water');
    }

    // Building detection
    if (desc.includes('house') || desc.includes('home')) {
      components.buildings.push('House');
    }
    if (desc.includes('school') || desc.includes('classroom')) {
      components.buildings.push('School/Classroom');
    }
    if (desc.includes('lab') || desc.includes('laboratory')) {
      components.buildings.push('Laboratory');
    }
    if (desc.includes('library')) {
      components.buildings.push('Library');
    }

    // Object detection
    if (desc.includes('table') || desc.includes('desk')) {
      components.objects.push('Tables/Desks');
    }
    if (desc.includes('chair')) {
      components.objects.push('Chairs');
    }
    if (desc.includes('computer') || desc.includes('laptop')) {
      components.objects.push('Computers');
    }
    if (desc.includes('board') || desc.includes('whiteboard')) {
      components.objects.push('Boards');
    }

    // Lighting detection
    if (desc.includes('bright') || desc.includes('sunny')) {
      components.lighting = 'Bright/Sunny';
    } else if (desc.includes('dark') || desc.includes('night')) {
      components.lighting = 'Dark/Night';
    } else if (desc.includes('moonlight')) {
      components.lighting = 'Moonlight';
    } else {
      components.lighting = 'Standard';
    }

    // Effects detection
    if (desc.includes('rain') || desc.includes('storm')) {
      components.effects.push('Rain/Storm');
    }
    if (desc.includes('snow')) {
      components.effects.push('Snow');
    }
    if (desc.includes('fog')) {
      components.effects.push('Fog');
    }

    return components;
  }

  /**
   * Validate environment creation request
   */
  validateRequest(request: EnvironmentCreationRequest): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!request.name || request.name.trim().length === 0) {
      errors.push('Environment name is required');
    }

    if (!request.description || request.description.trim().length === 0) {
      errors.push('Environment description is required');
    }

    if (request.name && request.name.length > 50) {
      errors.push('Environment name must be 50 characters or less');
    }

    if (request.description && request.description.length > 1000) {
      errors.push('Environment description must be 1000 characters or less');
    }

    if (request.max_players && (request.max_players < 1 || request.max_players > 100)) {
      errors.push('Maximum players must be between 1 and 100');
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }
}

// Export singleton instance
export const robloxEnvironmentService = new RobloxEnvironmentService();

// Export convenience functions
export const createRobloxEnvironment = (request: EnvironmentCreationRequest) =>
  robloxEnvironmentService.createEnvironment(request);

export const getRobloxEnvironmentStatus = (environmentName: string) =>
  robloxEnvironmentService.getEnvironmentStatus(environmentName);

export const checkRojoConnection = () =>
  robloxEnvironmentService.checkRojoConnection();

export const getRojoInfo = () =>
  robloxEnvironmentService.getRojoInfo();

export const listUserEnvironments = () =>
  robloxEnvironmentService.listUserEnvironments();

export const deleteRobloxEnvironment = (environmentName: string) =>
  robloxEnvironmentService.deleteEnvironment(environmentName);
