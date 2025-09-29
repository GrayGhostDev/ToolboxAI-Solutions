/**
 * Pusher-Specific Type Definitions for ToolboxAI Dashboard
 *
 * This file provides specific type definitions for Pusher Channels
 * features including presence channels, authentication, and events.
 */

import { Channel, PresenceChannel } from 'pusher-js';
import { WebSocketMessage, WebSocketMessageType, UserPresence } from './websocket';

// Pusher Channel Types
export enum PusherChannelType {
  PUBLIC = 'public',
  PRIVATE = 'private',
  PRESENCE = 'presence'
}

// Pusher Channel Names (following Pusher naming conventions)
export enum PusherChannels {
  // Public channels
  DASHBOARD_UPDATES = 'dashboard-updates',
  CONTENT_GENERATION = 'content-generation',
  AGENT_STATUS = 'agent-status',
  SYSTEM_ANNOUNCEMENTS = 'system-announcements',

  // Private channels (require authentication)
  PRIVATE_CONTENT_UPDATES = 'private-content-updates',
  PRIVATE_USER_NOTIFICATIONS = 'private-user-notifications',

  // Presence channels (show who's online)
  PRESENCE_CLASSROOM = 'presence-classroom',
  PRESENCE_COLLABORATION = 'presence-collaboration',
  PRESENCE_GLOBAL = 'presence-global'
}

// Pusher Event Names
export enum PusherEvents {
  // Content generation events
  CONTENT_PROGRESS = 'content-progress',
  CONTENT_COMPLETE = 'content-complete',
  CONTENT_ERROR = 'content-error',

  // Agent events
  AGENT_STATUS_UPDATE = 'agent-status-update',
  AGENT_RESPONSE = 'agent-response',

  // User events
  USER_NOTIFICATION = 'user-notification',
  USER_ACHIEVEMENT = 'user-achievement',

  // Collaboration events
  USER_TYPING = 'user-typing',
  CURSOR_MOVE = 'cursor-move',
  DOCUMENT_EDIT = 'document-edit',

  // System events
  SYSTEM_MAINTENANCE = 'system-maintenance',
  SYSTEM_ALERT = 'system-alert',

  // Quiz events
  QUIZ_START = 'quiz-start',
  QUIZ_SUBMIT = 'quiz-submit',
  QUIZ_RESULT = 'quiz-result',

  // Pusher built-in events
  PUSHER_SUBSCRIPTION_SUCCEEDED = 'pusher:subscription_succeeded',
  PUSHER_SUBSCRIPTION_ERROR = 'pusher:subscription_error',
  PUSHER_MEMBER_ADDED = 'pusher:member_added',
  PUSHER_MEMBER_REMOVED = 'pusher:member_removed'
}

// Pusher Connection States (mirroring pusher-js states)
export enum PusherConnectionState {
  INITIALIZED = 'initialized',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  UNAVAILABLE = 'unavailable',
  FAILED = 'failed',
  DISCONNECTED = 'disconnected'
}

// Pusher Authentication Interface
export interface PusherAuthData {
  channel: string;
  socket_id: string;
  user_id?: string;
  user_info?: {
    id: string;
    name: string;
    email?: string;
    avatar?: string;
    role?: string;
  };
}

// Pusher Authentication Response
export interface PusherAuthResponse {
  auth: string;
  channel_data?: string; // For presence channels
}

// Pusher Channel Subscription Options
export interface PusherChannelOptions {
  autoSubscribe?: boolean;
  enableLogging?: boolean;
  onSubscribed?: (channel: Channel) => void;
  onError?: (error: any) => void;
  onMemberAdded?: (member: PusherMember) => void;
  onMemberRemoved?: (member: PusherMember) => void;
}

// Pusher Member (for presence channels)
export interface PusherMember {
  id: string;
  info: {
    name: string;
    email?: string;
    avatar?: string;
    role?: string;
    status?: 'online' | 'away' | 'busy';
    lastActivity?: string;
  };
}

// Pusher Message Payload
export interface PusherMessagePayload<T = any> {
  type: WebSocketMessageType | PusherEvents;
  data: T;
  timestamp: string;
  sender?: {
    id: string;
    name: string;
    avatar?: string;
  };
  metadata?: Record<string, any>;
}

// Enhanced WebSocket Message for Pusher
export interface PusherMessage<T = any> extends WebSocketMessage<T> {
  pusherChannel?: string;
  pusherEvent?: PusherEvents;
  socketId?: string;
}

// Pusher Service Configuration
export interface PusherServiceConfig {
  key: string;
  cluster: string;
  authEndpoint: string;
  forceTLS?: boolean;
  enabledTransports?: string[];
  disableStats?: boolean;
  debug?: boolean;
  authorizer?: (channel: Channel, options: any) => any;
}

// Pusher Channel Subscription
export interface PusherSubscription {
  id: string;
  channel: string;
  channelType: PusherChannelType;
  eventHandlers: Map<string, Set<(data: any) => void>>;
  options: PusherChannelOptions;
  pusherChannel?: Channel | PresenceChannel;
  isSubscribed: boolean;
  subscriptionError?: Error;
}

// Pusher Service State
export interface PusherServiceState {
  connectionState: PusherConnectionState;
  isConnected: boolean;
  isConnecting: boolean;
  subscriptions: Map<string, PusherSubscription>;
  activeMembers: Map<string, PusherMember[]>; // channel -> members
  connectionStats: {
    connectedAt?: Date;
    reconnectAttempts: number;
    messagesReceived: number;
    messagesSent: number;
    lastError?: Error;
  };
}

// Pusher Event Handler Types
export type PusherEventHandler<T = any> = (data: T, metadata?: { channel: string; event: string }) => void;
export type PusherConnectionHandler = (state: PusherConnectionState) => void;
export type PusherSubscriptionHandler = (subscription: PusherSubscription) => void;
export type PusherErrorHandler = (error: Error, context?: string) => void;

// Pusher Presence Channel Data
export interface PusherPresenceChannelData {
  user_id: string;
  user_info: {
    name: string;
    email?: string;
    avatar?: string;
    role?: string;
    status?: 'online' | 'away' | 'busy';
  };
}

// Pusher Realtime Features
export interface PusherRealtimeFeatures {
  // Content Generation
  subscribeToContentGeneration: (onProgress: (data: any) => void) => () => void;
  triggerContentRequest: (request: any) => Promise<void>;

  // User Notifications
  subscribeToUserNotifications: (userId: string, onNotification: (data: any) => void) => () => void;
  sendUserNotification: (userId: string, notification: any) => Promise<void>;

  // Presence Features
  joinPresenceChannel: (channelName: string, userInfo: PusherPresenceChannelData['user_info']) => Promise<PresenceChannel>;
  leavePresenceChannel: (channelName: string) => void;
  getPresenceMembers: (channelName: string) => PusherMember[];

  // Collaboration
  subscribeToCollaboration: (roomId: string, handlers: {
    onUserTyping?: (data: any) => void;
    onCursorMove?: (data: any) => void;
    onDocumentEdit?: (data: any) => void;
  }) => () => void;

  // System Events
  subscribeToSystemEvents: (onEvent: (data: any) => void) => () => void;
}

// Pusher Channel Factory Function Type
export type PusherChannelFactory = (channelName: string, channelType: PusherChannelType) => Channel | PresenceChannel;

// Pusher Hook Configuration
export interface PusherHookConfig {
  autoConnect?: boolean;
  autoSubscribe?: boolean;
  reconnectOnFocus?: boolean;
  enablePresence?: boolean;
  debugMode?: boolean;
}

// Type Guards
export const isPusherMessage = (obj: any): obj is PusherMessage => {
  return obj && typeof obj === 'object' && 'type' in obj && 'timestamp' in obj;
};

export const isPresenceChannel = (channel: Channel): channel is PresenceChannel => {
  return 'members' in channel;
};

export const isPusherMember = (obj: any): obj is PusherMember => {
  return obj && typeof obj === 'object' && 'id' in obj && 'info' in obj;
};

// Utility Functions for Channel Names
export const formatChannelName = (base: string, type: PusherChannelType, suffix?: string): string => {
  const prefix = type === PusherChannelType.PRIVATE ? 'private-' :
                 type === PusherChannelType.PRESENCE ? 'presence-' : '';
  return `${prefix}${base}${suffix ? `-${suffix}` : ''}`;
};

export const parseChannelName = (channelName: string): {
  type: PusherChannelType;
  baseName: string;
  isPrivate: boolean;
  isPresence: boolean;
} => {
  const isPrivate = channelName.startsWith('private-');
  const isPresence = channelName.startsWith('presence-');
  const type = isPrivate ? PusherChannelType.PRIVATE :
               isPresence ? PusherChannelType.PRESENCE :
               PusherChannelType.PUBLIC;

  const baseName = channelName
    .replace(/^private-/, '')
    .replace(/^presence-/, '');

  return {
    type,
    baseName,
    isPrivate,
    isPresence
  };
};

// Common Channel Configurations
export const COMMON_CHANNEL_CONFIGS: Record<string, PusherChannelOptions> = {
  contentGeneration: {
    autoSubscribe: true,
    enableLogging: true
  },
  userNotifications: {
    autoSubscribe: true,
    enableLogging: false
  },
  collaboration: {
    autoSubscribe: false,
    enableLogging: true
  },
  presence: {
    autoSubscribe: false,
    enableLogging: true
  }
};

export default {
  PusherChannelType,
  PusherChannels,
  PusherEvents,
  PusherConnectionState,
  formatChannelName,
  parseChannelName,
  isPusherMessage,
  isPresenceChannel,
  isPusherMember,
  COMMON_CHANNEL_CONFIGS
};