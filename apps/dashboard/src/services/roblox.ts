/**
 * Roblox Integration Service
 * Provides interface to Roblox bridge for educational content
 * Updated for 2025 standards with Pusher integration
 */

import { pusherService } from './pusher';
import { WebSocketMessageType } from '../types/websocket';

export interface RobloxWorld {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'inactive' | 'maintenance';
  playerCount: number;
  maxPlayers: number;
  educationalContent: {
    subject: string;
    grade: number;
    objectives: string[];
  };
  createdAt: string;
  updatedAt: string;
}

export interface RobloxStudent {
  id: string;
  username: string;
  displayName: string;
  currentWorld?: string;
  progress: {
    level: number;
    xp: number;
    completedObjectives: number;
    totalObjectives: number;
  };
  status: 'online' | 'offline' | 'in-game';
  lastActivity: string;
}

export interface RobloxSession {
  id: string;
  studentId: string;
  worldId: string;
  status: 'active' | 'paused' | 'completed';
  startTime: string;
  endTime?: string;
  objectives: {
    id: string;
    description: string;
    completed: boolean;
    completedAt?: string;
  }[];
  metrics: {
    timeSpent: number;
    actionsPerformed: number;
    hintsUsed: number;
    errorsCount: number;
  };
}

class RobloxService {
  private baseUrl: string;
  private isEnabled: boolean;

  constructor() {
    this.baseUrl = import.meta.env.VITE_ROBLOX_BRIDGE_URL || 'http://localhost:5001';
    this.isEnabled = import.meta.env.VITE_ENABLE_ROBLOX === 'true';
  }

  // Check if Roblox integration is enabled
  isAvailable(): boolean {
    return this.isEnabled;
  }

  // Get all worlds
  async getWorlds(): Promise<RobloxWorld[]> {
    if (!this.isEnabled) return [];
    
    try {
      const response = await fetch(`${this.baseUrl}/worlds`);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch Roblox worlds:', error);
      return [];
    }
  }

  // Get world by ID
  async getWorld(worldId: string): Promise<RobloxWorld | null> {
    if (!this.isEnabled) return null;
    
    try {
      const response = await fetch(`${this.baseUrl}/worlds/${worldId}`);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch Roblox world:', error);
      return null;
    }
  }

  // Get students in a world
  async getStudents(worldId?: string): Promise<RobloxStudent[]> {
    if (!this.isEnabled) return [];
    
    try {
      const url = worldId ? `${this.baseUrl}/students?worldId=${worldId}` : `${this.baseUrl}/students`;
      const response = await fetch(url);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch Roblox students:', error);
      return [];
    }
  }

  // Get active sessions
  async getSessions(worldId?: string): Promise<RobloxSession[]> {
    if (!this.isEnabled) return [];
    
    try {
      const url = worldId ? `${this.baseUrl}/sessions?worldId=${worldId}` : `${this.baseUrl}/sessions`;
      const response = await fetch(url);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch Roblox sessions:', error);
      return [];
    }
  }

  // Start a session for a student
  async startSession(studentId: string, worldId: string): Promise<RobloxSession | null> {
    if (!this.isEnabled) return null;
    
    try {
      const response = await fetch(`${this.baseUrl}/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          studentId,
          worldId,
        }),
      });
      
      const session = await response.json();
      
      // Notify via Pusher
      pusherService.send(WebSocketMessageType.ROBLOX_UPDATE, {
        type: 'session_started',
        sessionId: session.id,
        studentId,
        worldId,
      }, { channel: 'roblox-events' });
      
      return session;
    } catch (error) {
      console.error('Failed to start Roblox session:', error);
      return null;
    }
  }

  // End a session
  async endSession(sessionId: string): Promise<boolean> {
    if (!this.isEnabled) return false;
    
    try {
      const response = await fetch(`${this.baseUrl}/sessions/${sessionId}/end`, {
        method: 'POST',
      });
      
      if (response.ok) {
        // Notify via Pusher
        pusherService.send(WebSocketMessageType.ROBLOX_UPDATE, {
          type: 'session_ended',
          sessionId,
        }, { channel: 'roblox-events' });
      }
      
      return response.ok;
    } catch (error) {
      console.error('Failed to end Roblox session:', error);
      return false;
    }
  }

  // Subscribe to Roblox events
  subscribeToEvents(callback: (event: any) => void): () => void {
    if (!this.isEnabled) return () => {};
    
    const subscriptionId = pusherService.subscribe('roblox-events', callback);
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

export const robloxService = new RobloxService();
export default robloxService;
