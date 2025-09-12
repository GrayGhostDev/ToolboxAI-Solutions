/**
 * WebSocket Type Definitions for ToolboxAI Dashboard
 * 
 * Provides comprehensive type definitions for WebSocket communication
 * between the Dashboard and Backend services.
 */

// Connection States
export enum WebSocketState {
  CONNECTING = 'CONNECTING',
  CONNECTED = 'CONNECTED',
  DISCONNECTING = 'DISCONNECTING',
  DISCONNECTED = 'DISCONNECTED',
  RECONNECTING = 'RECONNECTING',
  ERROR = 'ERROR'
}

// Message Types
export enum WebSocketMessageType {
  // Connection Management
  CONNECT = 'connect',
  DISCONNECT = 'disconnect',
  PING = 'ping',
  PONG = 'pong',
  ERROR = 'error',
  
  // Subscription Management
  SUBSCRIBE = 'subscribe',
  UNSUBSCRIBE = 'unsubscribe',
  SUBSCRIBED = 'subscribed',
  UNSUBSCRIBED = 'unsubscribed',
  
  // Content Generation
  CONTENT_REQUEST = 'content_request',
  CONTENT_RESPONSE = 'content_response',
  CONTENT_UPDATE = 'content_update',
  CONTENT_PROGRESS = 'content_progress',
  CONTENT_COMPLETE = 'content_complete',
  CONTENT_CANCEL = 'content_cancel',
  CONTENT_ERROR = 'content_error',
  
  // Quiz Events
  QUIZ_START = 'quiz_start',
  QUIZ_RESPONSE = 'quiz_response',
  QUIZ_FEEDBACK = 'quiz_feedback',
  QUIZ_EVENT = 'quiz_event',
  QUIZ_COMPLETE = 'quiz_complete',
  QUIZ_RESULTS = 'quiz_results',
  QUIZ_UPDATE = 'quiz_update',
  REQUEST_QUIZ_RESULTS = 'request_quiz_results',
  
  // Progress Tracking
  PROGRESS_UPDATE = 'progress_update',
  STUDENT_PROGRESS = 'student_progress',
  CLASS_PROGRESS = 'class_progress',
  
  // Collaboration
  USER_JOIN = 'user_join',
  USER_LEAVE = 'user_leave',
  USER_MESSAGE = 'user_message',
  CURSOR_UPDATE = 'cursor_update',
  CONTENT_EDIT = 'content_edit',
  
  // Roblox Events
  ROBLOX_EVENT = 'roblox_event',
  ENVIRONMENT_UPDATE = 'environment_update',
  ASSET_LOADED = 'asset_loaded',
  ASSET_UPDATE = 'asset_update',
  PREVIEW_READY = 'preview_ready',
  LOAD_ENVIRONMENT = 'load_environment',
  TOGGLE_ASSET = 'toggle_asset',
  EXPORT_ENVIRONMENT = 'export_environment',
  SHARE_ENVIRONMENT = 'share_environment',
  
  // Student/Teacher Events
  STUDENT_STATUS = 'student_status',
  CLASS_METRICS = 'class_metrics',
  REQUEST_PROGRESS = 'request_progress',
  TEACHER_MESSAGE = 'teacher_message',
  TEACHER_INTERVENTION = 'teacher_intervention',
  
  // Session Events
  SESSION_UPDATE = 'session_update',
  SESSION_STATUS = 'session_status',
  REQUEST_SESSIONS = 'request_sessions',
  CREATE_SESSION = 'create_session',
  SESSION_CONTROL = 'session_control',
  DELETE_SESSION = 'delete_session',
  
  // Plugin Events
  PLUGIN_STATUS_REQUEST = 'plugin_status_request',
  GET_ACTIVE_SESSIONS = 'get_active_sessions',
  CONTENT_GENERATION_REQUEST = 'content_generation_request',
  
  // Broadcast Messages
  BROADCAST = 'broadcast',
  BROADCAST_SENT = 'broadcast_sent',
  
  // System Notifications
  SYSTEM_NOTIFICATION = 'system_notification',
  SYSTEM_ALERT = 'system_alert',
  
  // Analytics
  ANALYTICS_EVENT = 'analytics_event',
  METRICS_UPDATE = 'metrics_update',
  
  // Notification & Achievement Events (from RealtimeToast.tsx)
  CLASS_ONLINE = 'class_online',
  ACHIEVEMENT_UNLOCKED = 'achievement_unlocked',
  ASSIGNMENT_REMINDER = 'assignment_reminder',
  
  // Leaderboard Events (from Leaderboard.tsx)
  REQUEST_LEADERBOARD = 'request_leaderboard',
  LEADERBOARD_UPDATE = 'leaderboard_update',
  XP_GAINED = 'xp_gained',
  BADGE_EARNED = 'badge_earned'
}

// Channel Types
export enum WebSocketChannel {
  CONTENT_UPDATES = 'content_updates',
  QUIZ_EVENTS = 'quiz_events',
  TEACHER_UPDATES = 'teacher_updates',
  STUDENT_UPDATES = 'student_updates',
  ROBLOX_EVENTS = 'roblox_events',
  SYSTEM_EVENTS = 'system',
  ANALYTICS = 'analytics'
}

// Base Message Interface
export interface WebSocketMessage<T = any> {
  type: WebSocketMessageType;
  payload?: T;
  channel?: string;
  timestamp: string;
  messageId?: string;
  correlationId?: string;
  sender?: string;
  metadata?: Record<string, any>;
}

// Response Message
export interface WebSocketResponse<T = any> extends WebSocketMessage<T> {
  success: boolean;
  error?: string;
  statusCode?: number;
}

// Connection Options
export interface WebSocketConnectionOptions {
  url: string;
  token?: string;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
  debug?: boolean;
  onConnect?: () => void;
  onDisconnect?: (reason?: string) => void;
  onError?: (error: WebSocketError) => void;
  onMessage?: (message: WebSocketMessage) => void;
}

// Error Types
export interface WebSocketError {
  code: string;
  message: string;
  timestamp: string;
  details?: any;
  recoverable?: boolean;
}

// Subscription
export interface WebSocketSubscription {
  channel: string;
  handler: (message: WebSocketMessage) => void;
  filter?: (message: WebSocketMessage) => boolean;
  subscriptionId?: string;
}

// Content Generation Messages
export interface ContentGenerationRequest {
  subject: string;
  gradeLevel: number;
  learningObjectives: string[];
  environmentType: string;
  includeQuiz?: boolean;
  difficultyLevel?: string;
  requestId: string;
  userId: string;
}

export interface ContentGenerationProgress {
  requestId: string;
  stage: 'initializing' | 'analyzing' | 'generating' | 'optimizing' | 'finalizing';
  percentage: number;
  currentAgent?: string;
  message?: string;
  estimatedTimeRemaining?: number;
  artifacts?: {
    scripts?: string[];
    terrain?: any;
    assets?: string[];
    quiz?: any;
  };
  // Legacy/alternate fields used by components
  agentId?: string;
  status?: string;
  progress?: number;
  currentTask?: string;
  metrics?: any;
  sessionStatus?: string;
}

export interface ContentGenerationResponse {
  requestId: string;
  status: 'completed' | 'failed' | 'cancelled';
  content?: {
    scripts: string[];
    terrain: any;
    assets: string[];
    quiz: any;
    metadata: Record<string, any>;
  };
  error?: string;
  duration?: number;
}

// Quiz Messages
export interface QuizMessage {
  quizId: string;
  studentId: string;
  action: 'start' | 'answer' | 'skip' | 'complete' | 'timeout';
  questionId?: string;
  answer?: any;
  score?: number;
  timeSpent?: number;
}

export interface QuizFeedback {
  quizId: string;
  questionId: string;
  correct: boolean;
  score: number;
  feedback: string;
  explanation?: string;
  nextQuestion?: any;
}

// Progress Messages
export interface ProgressUpdate {
  userId: string;
  lessonId?: string;
  classId?: string;
  progress: number;
  completedObjectives?: string[];
  achievements?: string[];
  xpEarned?: number;
  timeSpent?: number;
  metadata?: Record<string, any>;
}

// Collaboration Messages
export interface CollaborationMessage {
  roomId: string;
  userId: string;
  action: 'join' | 'leave' | 'edit' | 'cursor' | 'select';
  data?: any;
  position?: { x: number; y: number };
  selection?: { start: number; end: number };
  changes?: any[];
}

// Roblox Messages
export interface RobloxEventMessage {
  eventType: string;
  worldId?: string;
  playerId?: string;
  data: any;
  serverTime?: string;
  performance?: {
    fps?: number;
    ping?: number;
    memory?: number;
  };
}

// System Messages
export interface SystemNotification {
  id: string;
  type?: 'achievement' | 'quiz' | 'lesson' | 'system';
  level: 'info' | 'warning' | 'error' | 'success';
  severity?: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  dismissible?: boolean;
  duration?: number;
  action?: {
    label: string;
    handler: () => void;
  };
}

// Connection Statistics
export interface WebSocketStats {
  connectionState: WebSocketState;
  connectedAt?: string;
  lastMessageAt?: string;
  messagesSent: number;
  messagesReceived: number;
  reconnectAttempts: number;
  latency?: number;
  bytesReceived?: number;
  bytesSent?: number;
}

// Message Queue Item
export interface QueuedMessage {
  message: WebSocketMessage;
  timestamp: number;
  attempts: number;
  maxAttempts: number;
  onSuccess?: () => void;
  onFailure?: (error: Error) => void;
}

// Event Handler Types
export type WebSocketEventHandler<T = any> = (data: T) => void | Promise<void>;
export type WebSocketErrorHandler = (error: WebSocketError) => void;
export type WebSocketStateHandler = (state: WebSocketState, previousState?: WebSocketState) => void;

// Acknowledgment
export interface MessageAcknowledgment {
  messageId: string;
  status: 'received' | 'processing' | 'completed' | 'failed';
  timestamp: string;
  error?: string;
}

// Presence Information
export interface UserPresence {
  userId: string;
  username: string;
  avatar?: string;
  status: 'online' | 'away' | 'busy' | 'offline';
  lastActivity?: string;
  location?: string;
  metadata?: Record<string, any>;
}

// Channel Information
export interface ChannelInfo {
  name: string;
  subscribers: number;
  created?: string;
  metadata?: Record<string, any>;
}

// Export utility type for strongly typed messages
export type TypedWebSocketMessage<T extends WebSocketMessageType, P = any> = WebSocketMessage<P> & {
  type: T;
};

// Export type guards
export const isWebSocketMessage = (obj: any): obj is WebSocketMessage => {
  return obj && typeof obj.type === 'string' && typeof obj.timestamp === 'string';
};

export const isWebSocketError = (obj: any): obj is WebSocketError => {
  return obj && typeof obj.code === 'string' && typeof obj.message === 'string';
};

export const isContentGenerationProgress = (msg: WebSocketMessage): msg is TypedWebSocketMessage<WebSocketMessageType.CONTENT_PROGRESS, ContentGenerationProgress> => {
  return msg.type === WebSocketMessageType.CONTENT_PROGRESS;
};

export const isQuizMessage = (msg: WebSocketMessage): msg is TypedWebSocketMessage<WebSocketMessageType.QUIZ_EVENT, QuizMessage> => {
  return msg.type === WebSocketMessageType.QUIZ_EVENT;
};

export const isProgressUpdate = (msg: WebSocketMessage): msg is TypedWebSocketMessage<WebSocketMessageType.PROGRESS_UPDATE, ProgressUpdate> => {
  return msg.type === WebSocketMessageType.PROGRESS_UPDATE;
};