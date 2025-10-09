/**
 * Roblox AI Service
 *
 * Handles communication with the Roblox AI agent backend.
 * Provides methods for chat interactions and environment generation.
 */

import { api } from './api';
import { pusherService } from './pusher';
import {
  WebSocketMessageType,
  type AgentChatUserMessage,
  type RobloxAgentRequest,
  type FollowupFieldType
} from '../types/websocket';

export interface RobloxSpec {
  environment_name?: string;
  theme?: string;
  map_type?: 'obby' | 'open_world' | 'dungeon' | 'lab' | 'classroom' | 'puzzle' | 'arena';
  terrain?: string;
  npc_count?: number;
  difficulty?: 'easy' | 'medium' | 'hard';
  learning_objectives?: string[];
  age_range?: string;
  assets?: string[];
  scripting?: string[];
  lighting?: string;
  weather?: string;
  notes?: string;
}

export interface ConversationStatus {
  conversation_id: string;
  spec: RobloxSpec;
  missing_fields: FollowupFieldType[];
  ready_for_generation: boolean;
}

export interface ChatResponse {
  success: boolean;
  message: string;
  conversation_id: string;
}

export interface GenerationResponse {
  success: boolean;
  request_id: string;
  message: string;
}

class RobloxAIService {
  /**
   * Send a chat message to the AI agent
   */
  async sendChatMessage(
    conversationId: string,
    message: string,
    context?: Record<string, any>
  ): Promise<ChatResponse> {
    try {
      const response = await api.request<ChatResponse>({
        method: 'POST',
        url: '/roblox-ai/chat',
        data: {
          conversation_id: conversationId,
          message,
          context
        }
      });

      return response;
    } catch (error) {
      console.error('Failed to send chat message:', error);
      throw new Error('Failed to send message to AI agent');
    }
  }

  /**
   * Send chat message via WebSocket (alternative method)
   */
  async sendChatMessageWS(
    conversationId: string,
    message: string,
    context?: Record<string, any>
  ): Promise<void> {
    try {
      await pusherService.send(
        WebSocketMessageType.AGENT_CHAT_USER,
        {
          conversationId,
          text: message,
          context
        } as AgentChatUserMessage,
        {
          channel: `agent-chat-${conversationId}`
        }
      );
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
      throw new Error('Failed to send message via WebSocket');
    }
  }

  /**
   * Generate Roblox environment
   */
  async generateEnvironment(
    conversationId: string,
    spec: RobloxSpec
  ): Promise<GenerationResponse> {
    try {
      const response = await api.request<GenerationResponse>({
        method: 'POST',
        url: '/roblox-ai/generate',
        data: {
          conversation_id: conversationId,
          spec
        }
      });

      return response;
    } catch (error) {
      console.error('Failed to generate environment:', error);
      throw new Error('Failed to start environment generation');
    }
  }

  /**
   * Generate environment via WebSocket (alternative method)
   */
  async generateEnvironmentWS(
    conversationId: string,
    spec: RobloxSpec
  ): Promise<void> {
    try {
      const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

      await pusherService.send(
        WebSocketMessageType.ROBLOX_AGENT_REQUEST,
        {
          conversationId,
          requestId,
          spec
        } as RobloxAgentRequest,
        {
          channel: `agent-chat-${conversationId}`
        }
      );
    } catch (error) {
      console.error('Failed to generate environment via WebSocket:', error);
      throw new Error('Failed to start environment generation');
    }
  }

  /**
   * Get conversation status
   */
  async getConversationStatus(conversationId: string): Promise<ConversationStatus> {
    try {
      const response = await api.request<ConversationStatus>({
        method: 'GET',
        url: `/roblox-ai/conversation/${conversationId}/status`
      });

      return response;
    } catch (error) {
      console.error('Failed to get conversation status:', error);
      throw new Error('Failed to get conversation status');
    }
  }

  /**
   * Clear conversation
   */
  async clearConversation(conversationId: string): Promise<void> {
    try {
      await api.request({
        method: 'DELETE',
        url: `/roblox-ai/conversation/${conversationId}`
      });
    } catch (error) {
      console.error('Failed to clear conversation:', error);
      throw new Error('Failed to clear conversation');
    }
  }

  /**
   * Subscribe to conversation events
   */
  subscribeToConversation(
    conversationId: string,
    onMessage: (message: any) => void
  ): string {
    return pusherService.subscribe(
      `agent-chat-${conversationId}`,
      onMessage
    );
  }

  /**
   * Unsubscribe from conversation events
   */
  unsubscribeFromConversation(subscriptionId: string): void {
    pusherService.unsubscribe(subscriptionId);
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return pusherService.isConnected();
  }

  /**
   * Connect WebSocket if not already connected
   */
  async ensureConnection(): Promise<void> {
    if (!this.isConnected()) {
      await pusherService.connect();
    }
  }

  /**
   * Validate specification completeness
   */
  validateSpec(spec: RobloxSpec): {
    isComplete: boolean;
    missingFields: FollowupFieldType[];
  } {
    const requiredFields: FollowupFieldType[] = [
      'environment_name',
      'theme',
      'map_type',
      'learning_objectives'
    ];

    const missingFields = requiredFields.filter(field => {
      const value = spec[field];
      if (Array.isArray(value)) {
        return value.length === 0;
      }
      return !value;
    });

    return {
      isComplete: missingFields.length === 0,
      missingFields
    };
  }

  /**
   * Extract structured data from user message (client-side helper)
   */
  extractSpecFromMessage(message: string): Partial<RobloxSpec> {
    const extracted: Partial<RobloxSpec> = {};
    const messageLower = message.toLowerCase();

    // Environment name extraction
    const nameMatch = message.match(/(?:call it|named?|title(?:d)?)\s+["']?([^"'.\\n]{3,40})["']?/i);
    if (nameMatch) {
      extracted.environment_name = nameMatch[1].trim();
    }

    // Theme extraction
    const themeMatch = message.match(/(?:theme|style|setting)\s*:?\s*([^.\n]{3,50})/i);
    if (themeMatch) {
      extracted.theme = themeMatch[1].trim();
    }

    // Map type extraction
    if (messageLower.includes('obby') || messageLower.includes('obstacle')) {
      extracted.map_type = 'obby';
    } else if (messageLower.includes('open world') || messageLower.includes('sandbox')) {
      extracted.map_type = 'open_world';
    } else if (messageLower.includes('dungeon') || messageLower.includes('maze')) {
      extracted.map_type = 'dungeon';
    } else if (messageLower.includes('lab') || messageLower.includes('laboratory')) {
      extracted.map_type = 'lab';
    } else if (messageLower.includes('classroom') || messageLower.includes('school')) {
      extracted.map_type = 'classroom';
    } else if (messageLower.includes('puzzle')) {
      extracted.map_type = 'puzzle';
    } else if (messageLower.includes('arena') || messageLower.includes('battle')) {
      extracted.map_type = 'arena';
    }

    // Difficulty extraction
    if (messageLower.includes('easy') || messageLower.includes('beginner')) {
      extracted.difficulty = 'easy';
    } else if (messageLower.includes('hard') || messageLower.includes('difficult') || messageLower.includes('advanced')) {
      extracted.difficulty = 'hard';
    } else if (messageLower.includes('medium') || messageLower.includes('intermediate')) {
      extracted.difficulty = 'medium';
    }

    // Learning objectives extraction
    const objectivePatterns = [
      /(?:learn|teach|objective|goal|topic)s?\s*:?\s*([^.\n]+)/gi,
      /\b(math|science|history|english|art|geography|physics|chemistry|biology)\b/gi
    ];

    const objectives: string[] = [];
    objectivePatterns.forEach(pattern => {
      const matches = message.match(pattern);
      if (matches) {
        matches.forEach(match => {
          const cleaned = match.replace(/^(?:learn|teach|objective|goal|topic)s?\s*:?\s*/i, '').trim();
          if (cleaned && !objectives.includes(cleaned)) {
            objectives.push(cleaned);
          }
        });
      }
    });

    if (objectives.length > 0) {
      extracted.learning_objectives = objectives;
    }

    // Age range extraction
    const ageMatch = message.match(/(?:age|grade)\s*(?:group|level)?\s*:?\s*(\d+(?:-\d+)?)/i);
    if (ageMatch) {
      extracted.age_range = ageMatch[1];
    }

    return extracted;
  }

  /**
   * Generate conversation ID
   */
  generateConversationId(): string {
    return `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Format spec for display
   */
  formatSpecForDisplay(spec: RobloxSpec): string {
    const parts: string[] = [];

    if (spec.environment_name) {
      parts.push(`**Name:** ${spec.environment_name}`);
    }
    if (spec.theme) {
      parts.push(`**Theme:** ${spec.theme}`);
    }
    if (spec.map_type) {
      parts.push(`**Type:** ${spec.map_type.replace('_', ' ')}`);
    }
    if (spec.learning_objectives && spec.learning_objectives.length > 0) {
      parts.push(`**Learning Objectives:** ${spec.learning_objectives.join(', ')}`);
    }
    if (spec.difficulty) {
      parts.push(`**Difficulty:** ${spec.difficulty}`);
    }
    if (spec.age_range) {
      parts.push(`**Age Range:** ${spec.age_range}`);
    }

    return parts.join('\n');
  }
}

// Export singleton instance
export const robloxAIService = new RobloxAIService();
export default robloxAIService;
