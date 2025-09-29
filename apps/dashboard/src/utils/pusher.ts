/**
 * Pusher Utility Functions for ToolboxAI Dashboard
 *
 * Provides utility functions for common Pusher operations including
 * channel name generation, event name constants, message formatters,
 * and error handlers.
 */

import { logger } from './logger';
import {
  PusherChannelType,
  PusherChannels,
  PusherEvents,
  PusherMessage,
  PusherMember,
  formatChannelName,
  parseChannelName,
  isPusherMessage,
  isPusherMember
} from '../types/pusher';
import { WebSocketMessageType } from '../types/websocket';

// Channel Name Generators
export class ChannelNameGenerator {
  /**
   * Generate user-specific channel name
   */
  static user(userId: string, suffix?: string): string {
    const base = `user-${userId}`;
    return suffix ? `${base}-${suffix}` : base;
  }

  /**
   * Generate classroom-specific channel name
   */
  static classroom(classroomId: string, type: 'updates' | 'chat' | 'presence' = 'updates'): string {
    return `classroom-${classroomId}-${type}`;
  }

  /**
   * Generate content generation channel name
   */
  static contentGeneration(requestId?: string): string {
    return requestId ? `content-generation-${requestId}` : 'content-generation';
  }

  /**
   * Generate collaboration channel name
   */
  static collaboration(roomId: string, type: 'editing' | 'cursors' | 'chat' = 'editing'): string {
    return `collaboration-${roomId}-${type}`;
  }

  /**
   * Generate agent-specific channel name
   */
  static agent(agentId: string, action?: string): string {
    return action ? `agent-${agentId}-${action}` : `agent-${agentId}`;
  }

  /**
   * Generate quiz session channel name
   */
  static quizSession(sessionId: string): string {
    return `quiz-session-${sessionId}`;
  }

  /**
   * Generate private channel name
   */
  static private(baseName: string): string {
    return formatChannelName(baseName, PusherChannelType.PRIVATE);
  }

  /**
   * Generate presence channel name
   */
  static presence(baseName: string): string {
    return formatChannelName(baseName, PusherChannelType.PRESENCE);
  }
}

// Event Name Constants
export const EVENT_NAMES = {
  // Content generation events
  CONTENT_GENERATION: {
    STARTED: 'content-generation-started',
    PROGRESS: 'content-generation-progress',
    COMPLETED: 'content-generation-completed',
    FAILED: 'content-generation-failed',
    CANCELLED: 'content-generation-cancelled',
  },

  // User events
  USER: {
    NOTIFICATION: 'user-notification',
    ACHIEVEMENT: 'user-achievement',
    STATUS_UPDATE: 'user-status-update',
    PROFILE_UPDATE: 'user-profile-update',
  },

  // Collaboration events
  COLLABORATION: {
    USER_JOINED: 'collaboration-user-joined',
    USER_LEFT: 'collaboration-user-left',
    TYPING: 'collaboration-typing',
    CURSOR_MOVE: 'collaboration-cursor-move',
    DOCUMENT_EDIT: 'collaboration-document-edit',
    SELECTION_CHANGE: 'collaboration-selection-change',
  },

  // Quiz events
  QUIZ: {
    SESSION_STARTED: 'quiz-session-started',
    QUESTION_ANSWERED: 'quiz-question-answered',
    SESSION_COMPLETED: 'quiz-session-completed',
    RESULTS_AVAILABLE: 'quiz-results-available',
    TIME_WARNING: 'quiz-time-warning',
  },

  // Agent events
  AGENT: {
    STATUS_UPDATE: 'agent-status-update',
    RESPONSE_RECEIVED: 'agent-response-received',
    ERROR_OCCURRED: 'agent-error-occurred',
    TASK_COMPLETED: 'agent-task-completed',
  },

  // System events
  SYSTEM: {
    MAINTENANCE: 'system-maintenance',
    ALERT: 'system-alert',
    ANNOUNCEMENT: 'system-announcement',
    UPDATE_AVAILABLE: 'system-update-available',
  },

  // Presence events
  PRESENCE: {
    MEMBER_ADDED: 'presence-member-added',
    MEMBER_REMOVED: 'presence-member-removed',
    MEMBER_UPDATED: 'presence-member-updated',
  },
} as const;

// Message Formatters
export class MessageFormatter {
  /**
   * Format a standard Pusher message
   */
  static createMessage<T = any>(
    type: WebSocketMessageType | PusherEvents | string,
    data: T,
    options: {
      sender?: { id: string; name: string; avatar?: string };
      metadata?: Record<string, any>;
      channel?: string;
    } = {}
  ): PusherMessage<T> {
    return {
      type: type as WebSocketMessageType,
      payload: data,
      timestamp: new Date().toISOString(),
      messageId: generateMessageId(),
      sender: options.sender,
      metadata: options.metadata,
      pusherChannel: options.channel,
    };
  }

  /**
   * Format a content generation progress message
   */
  static contentProgress(
    requestId: string,
    stage: string,
    percentage: number,
    message?: string,
    artifacts?: any
  ) {
    return this.createMessage(EVENT_NAMES.CONTENT_GENERATION.PROGRESS, {
      requestId,
      stage,
      percentage,
      message,
      artifacts,
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Format a user notification message
   */
  static userNotification(
    title: string,
    message: string,
    type: 'info' | 'success' | 'warning' | 'error' = 'info',
    actionUrl?: string
  ) {
    return this.createMessage(EVENT_NAMES.USER.NOTIFICATION, {
      id: generateId(),
      title,
      message,
      type,
      actionUrl,
      timestamp: new Date().toISOString(),
      read: false,
    });
  }

  /**
   * Format a collaboration event message
   */
  static collaboration(
    roomId: string,
    action: keyof typeof EVENT_NAMES.COLLABORATION,
    data: any,
    user: { id: string; name: string; avatar?: string }
  ) {
    return this.createMessage(EVENT_NAMES.COLLABORATION[action], {
      roomId,
      action: action.toLowerCase(),
      data,
      timestamp: new Date().toISOString(),
    }, { sender: user });
  }

  /**
   * Format a quiz event message
   */
  static quizEvent(
    sessionId: string,
    event: keyof typeof EVENT_NAMES.QUIZ,
    data: any
  ) {
    return this.createMessage(EVENT_NAMES.QUIZ[event], {
      sessionId,
      event: event.toLowerCase(),
      data,
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Format a system event message
   */
  static systemEvent(
    type: keyof typeof EVENT_NAMES.SYSTEM,
    title: string,
    message: string,
    severity: 'low' | 'medium' | 'high' = 'medium',
    metadata?: Record<string, any>
  ) {
    return this.createMessage(EVENT_NAMES.SYSTEM[type], {
      title,
      message,
      severity,
      timestamp: new Date().toISOString(),
    }, { metadata });
  }
}

// Error Handlers
export class PusherErrorHandler {
  /**
   * Handle connection errors
   */
  static handleConnectionError(error: any): {
    userMessage: string;
    shouldRetry: boolean;
    retryDelay?: number;
  } {
    logger.error('Pusher connection error:', error);

    if (error?.code === 4001) {
      return {
        userMessage: 'Application key not found. Please check your configuration.',
        shouldRetry: false,
      };
    }

    if (error?.code === 4004) {
      return {
        userMessage: 'Application is over connection quota. Please try again later.',
        shouldRetry: true,
        retryDelay: 30000, // 30 seconds
      };
    }

    if (error?.code === 4100) {
      return {
        userMessage: 'Connection limit exceeded. Please try again later.',
        shouldRetry: true,
        retryDelay: 10000, // 10 seconds
      };
    }

    if (error?.code >= 4200 && error?.code <= 4299) {
      return {
        userMessage: 'Authentication failed. Please log in again.',
        shouldRetry: false,
      };
    }

    return {
      userMessage: 'Connection failed. Please check your internet connection.',
      shouldRetry: true,
      retryDelay: 5000, // 5 seconds
    };
  }

  /**
   * Handle subscription errors
   */
  static handleSubscriptionError(error: any, channelName: string): {
    userMessage: string;
    canRetry: boolean;
  } {
    logger.error(`Pusher subscription error for channel ${channelName}:`, error);

    if (error?.status === 403) {
      return {
        userMessage: 'Access denied to this channel. Please check your permissions.',
        canRetry: false,
      };
    }

    if (error?.status === 401) {
      return {
        userMessage: 'Authentication required. Please log in again.',
        canRetry: false,
      };
    }

    return {
      userMessage: 'Failed to subscribe to updates. Please try again.',
      canRetry: true,
    };
  }

  /**
   * Handle general Pusher errors
   */
  static handleGenericError(error: any, context?: string): void {
    const errorMessage = error?.message || error?.description || 'Unknown error';
    const errorCode = error?.code || 'UNKNOWN';
    
    logger.error(`Pusher error${context ? ` (${context})` : ''}:`, {
      code: errorCode,
      message: errorMessage,
      error,
    });
  }
}

// Connection State Utilities
export class ConnectionStateUtils {
  /**
   * Check if connection state allows sending messages
   */
  static canSendMessages(state: string): boolean {
    return state === 'connected';
  }

  /**
   * Check if connection state allows subscribing to channels
   */
  static canSubscribe(state: string): boolean {
    return state === 'connected';
  }

  /**
   * Get user-friendly connection status
   */
  static getStatusMessage(state: string): string {
    switch (state) {
      case 'initialized':
        return 'Initializing connection...';
      case 'connecting':
        return 'Connecting to server...';
      case 'connected':
        return 'Connected';
      case 'unavailable':
        return 'Connection unavailable';
      case 'failed':
        return 'Connection failed';
      case 'disconnected':
        return 'Disconnected';
      default:
        return 'Unknown status';
    }
  }

  /**
   * Get connection status color for UI
   */
  static getStatusColor(state: string): 'success' | 'warning' | 'error' | 'info' {
    switch (state) {
      case 'connected':
        return 'success';
      case 'connecting':
      case 'initialized':
        return 'info';
      case 'unavailable':
        return 'warning';
      case 'failed':
      case 'disconnected':
        return 'error';
      default:
        return 'info';
    }
  }
}

// Presence Utilities
export class PresenceUtils {
  /**
   * Format presence member data
   */
  static formatMember(
    userId: string,
    userInfo: {
      name: string;
      email?: string;
      avatar?: string;
      role?: string;
      status?: 'online' | 'away' | 'busy';
    }
  ): PusherMember {
    return {
      id: userId,
      info: {
        name: userInfo.name,
        email: userInfo.email,
        avatar: userInfo.avatar,
        role: userInfo.role,
        status: userInfo.status || 'online',
        lastActivity: new Date().toISOString(),
      },
    };
  }

  /**
   * Filter members by status
   */
  static filterMembersByStatus(
    members: PusherMember[],
    status: 'online' | 'away' | 'busy'
  ): PusherMember[] {
    return members.filter(member => member.info.status === status);
  }

  /**
   * Sort members by activity
   */
  static sortMembersByActivity(members: PusherMember[]): PusherMember[] {
    return [...members].sort((a, b) => {
      const aTime = new Date(a.info.lastActivity || 0).getTime();
      const bTime = new Date(b.info.lastActivity || 0).getTime();
      return bTime - aTime; // Most recent first
    });
  }

  /**
   * Get member count by role
   */
  static getCountByRole(members: PusherMember[]): Record<string, number> {
    const counts: Record<string, number> = {};
    members.forEach(member => {
      const role = member.info.role || 'unknown';
      counts[role] = (counts[role] || 0) + 1;
    });
    return counts;
  }
}

// Data Validation Utilities
export class ValidationUtils {
  /**
   * Validate channel name
   */
  static isValidChannelName(channelName: string): boolean {
    // Pusher channel names can be up to 200 characters
    // and can contain letters, numbers, dashes, underscores, and dots
    const channelRegex = /^[a-zA-Z0-9_.-]{1,200}$/;
    return channelRegex.test(channelName);
  }

  /**
   * Validate event name
   */
  static isValidEventName(eventName: string): boolean {
    // Event names can't start with 'pusher:'
    if (eventName.startsWith('pusher:')) {
      return false;
    }
    // Should be reasonable length and contain safe characters
    const eventRegex = /^[a-zA-Z0-9_.-]{1,100}$/;
    return eventRegex.test(eventName);
  }

  /**
   * Validate message payload size
   */
  static isValidPayloadSize(payload: any): boolean {
    try {
      const jsonString = JSON.stringify(payload);
      // Pusher has a 10KB message size limit
      return new Blob([jsonString]).size <= 10 * 1024;
    } catch (error) {
      return false;
    }
  }

  /**
   * Sanitize channel name
   */
  static sanitizeChannelName(channelName: string): string {
    return channelName
      .replace(/[^a-zA-Z0-9_.-]/g, '')
      .substring(0, 200)
      .toLowerCase();
  }

  /**
   * Sanitize event name
   */
  static sanitizeEventName(eventName: string): string {
    return eventName
      .replace(/[^a-zA-Z0-9_.-]/g, '')
      .substring(0, 100)
      .toLowerCase();
  }
}

// Rate Limiting Utilities
export class RateLimitUtils {
  private static messageTimestamps: Map<string, number[]> = new Map();
  private static readonly MAX_MESSAGES_PER_MINUTE = 100;
  private static readonly WINDOW_SIZE = 60000; // 1 minute

  /**
   * Check if sending a message would exceed rate limits
   */
  static canSendMessage(channelName: string): boolean {
    const now = Date.now();
    const timestamps = this.messageTimestamps.get(channelName) || [];
    
    // Remove timestamps older than the window
    const validTimestamps = timestamps.filter(timestamp => now - timestamp < this.WINDOW_SIZE);
    
    // Check if we're under the limit
    if (validTimestamps.length >= this.MAX_MESSAGES_PER_MINUTE) {
      return false;
    }
    
    // Add current timestamp and update the map
    validTimestamps.push(now);
    this.messageTimestamps.set(channelName, validTimestamps);
    
    return true;
  }

  /**
   * Get remaining messages for the current window
   */
  static getRemainingMessages(channelName: string): number {
    const now = Date.now();
    const timestamps = this.messageTimestamps.get(channelName) || [];
    const validTimestamps = timestamps.filter(timestamp => now - timestamp < this.WINDOW_SIZE);
    
    return Math.max(0, this.MAX_MESSAGES_PER_MINUTE - validTimestamps.length);
  }

  /**
   * Clear rate limit data for a channel
   */
  static clearRateLimit(channelName: string): void {
    this.messageTimestamps.delete(channelName);
  }
}

// Helper Functions
function generateId(): string {
  return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function generateMessageId(): string {
  return `msg_${generateId()}`;
}

// Export all utilities
export default {
  ChannelNameGenerator,
  EVENT_NAMES,
  MessageFormatter,
  PusherErrorHandler,
  ConnectionStateUtils,
  PresenceUtils,
  ValidationUtils,
  RateLimitUtils,
  generateId,
  generateMessageId,
};