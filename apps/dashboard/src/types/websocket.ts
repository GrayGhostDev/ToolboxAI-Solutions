/**
 * WebSocket Type Definitions
 *
 * These types provide backward compatibility while migrating to Pusher.
 * They map WebSocket concepts to Pusher equivalents.
 */

// WebSocket State enum for backward compatibility (maps to Pusher connection states)
export enum WebSocketState {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTING = 'disconnecting',
  DISCONNECTED = 'disconnected',
  RECONNECTING = 'reconnecting',
  ERROR = 'failed',
  FAILED = 'failed',
}

// WebSocket message types (mapped to Pusher events)
export enum WebSocketMessageType {
  CONTENT_PROGRESS = 'content-progress',
  CONTENT_COMPLETE = 'content-complete',
  CONTENT_ERROR = 'content-error',
  CONTENT_UPDATE = 'content-update',
  STREAM_START = 'stream-start',
  STREAM_DATA = 'stream-data',
  STREAM_END = 'stream-end',
  STREAM_ERROR = 'stream-error',
  HEARTBEAT = 'heartbeat',
  HEARTBEAT_ACK = 'heartbeat-ack',
  SUBSCRIPTION_CONFIRMED = 'subscription-confirmed',
  SUBSCRIPTION_REJECTED = 'subscription-rejected',
  // Additional message types for quiz, user, system, etc.
  QUIZ_UPDATE = 'quiz-update',
  QUIZ_RESULTS = 'quiz-results',
  USER_STATUS = 'user-status',
  SYSTEM_NOTIFICATION = 'system-notification',
  ROBLOX_UPDATE = 'roblox-update',
  ENVIRONMENT_SYNC = 'environment-sync',
  ANALYTICS_UPDATE = 'analytics-update',
  METRICS_UPDATE = 'metrics-update',
  PROGRESS_UPDATE = 'progress-update',
  AGENT_STATUS = 'agent-status',
  AGENT_TASK = 'agent-task',
  AGENT_RESULT = 'agent-result',
}

// WebSocket channels (mapped to Pusher channels)
export enum WebSocketChannel {
  // Public channels
  SYSTEM = 'public',
  DASHBOARD = 'dashboard-updates',
  CONTENT_UPDATES = 'content-generation',
  ANALYTICS = 'analytics',

  // Feature-specific channels
  QUIZ_EVENTS = 'quiz-updates',
  ROBLOX_EVENTS = 'roblox-updates',
  STUDENT_PROGRESS = 'student-progress',
  AGENT_STATUS = 'agent-status',

  // Private channels (user-specific)
  USER_NOTIFICATIONS = 'private-notifications',
  USER_CONTENT = 'private-content',

  // Presence channels (for collaboration)
  CLASSROOM = 'presence-classroom',
  ENVIRONMENT = 'presence-environment',
}

// WebSocket message structure
export interface WebSocketMessage<T = any> {
  id?: string;
  type: WebSocketMessageType;
  channel?: WebSocketChannel | string;
  data: T;
  timestamp?: number;
  userId?: string;
  metadata?: Record<string, any>;
}

// Connection states
export type WebSocketConnectionState =
  | 'connecting'
  | 'connected'
  | 'disconnected'
  | 'reconnecting'
  | 'failed';

// WebSocket event handler type
export type WebSocketEventHandler<T = any> = (data: T) => void;

// WebSocket state change handler
export type WebSocketStateHandler = (state: WebSocketState, previousState?: WebSocketState) => void;

// WebSocket error handler
export type WebSocketErrorHandler = (error: WebSocketError) => void;

// WebSocket configuration
export interface WebSocketConfig {
  url?: string;
  autoConnect?: boolean;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  debug?: boolean;
  onConnect?: () => void;
  onDisconnect?: (reason?: string) => void;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: WebSocketError) => void;
  heartbeatInterval?: number;
}

// WebSocket connection options (maps to Pusher config)
export interface WebSocketConnectionOptions {
  url?: string;
  autoConnect?: boolean;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  debug?: boolean;
  onConnect?: () => void;
  onDisconnect?: (reason?: string) => void;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: WebSocketError) => void;
  heartbeatInterval?: number;
}

// WebSocket subscription interface
export interface WebSocketSubscription {
  channel: string;
  handler: WebSocketEventHandler;
  filter?: (message: WebSocketMessage) => boolean;
  subscriptionId?: string;
}

// WebSocket error interface
export interface WebSocketError {
  code: string;
  message: string;
  timestamp: string;
  recoverable?: boolean;
  details?: any;
}

// WebSocket stats interface
export interface WebSocketStats {
  connectionState: WebSocketState;
  messagesSent: number;
  messagesReceived: number;
  reconnectAttempts: number;
  bytesReceived?: number;
  bytesSent?: number;
  connectedAt?: string;
  lastMessageAt?: string;
  latency?: number;
}

// Message acknowledgment interface
export interface MessageAcknowledgment {
  ok: boolean;
  receivedAt: string;
  [key: string]: any;
}

// Queued message interface
export interface QueuedMessage {
  message: WebSocketMessage;
  timestamp: number;
  attempts: number;
  maxAttempts: number;
  onSuccess?: () => void;
  onFailure?: (error: Error) => void;
}

// User presence interface
export interface UserPresence {
  id: string;
  name: string;
  status: 'online' | 'away' | 'busy' | 'offline';
  lastSeen?: string;
  avatar?: string;
  role?: string;
}

// Content generation request interface
export interface ContentGenerationRequest {
  type: 'lesson' | 'quiz' | 'assessment' | 'content';
  subject: string;
  grade: number;
  topic: string;
  difficulty: 'easy' | 'medium' | 'hard';
  length?: number;
  customInstructions?: string;
}

// Content generation specific types
export interface ContentProgressMessage {
  taskId: string;
  progress: number;
  message?: string;
  status: 'pending' | 'processing' | 'complete' | 'error';
}

export interface ContentCompleteMessage {
  taskId: string;
  result: any;
  duration?: number;
}

export interface ContentErrorMessage {
  taskId: string;
  error: string;
  code?: string;
  details?: any;
}

// Quiz and assessment types
export interface QuizUpdateMessage {
  quizId: string;
  action: 'start' | 'submit' | 'grade' | 'review';
  data: any;
}

export interface QuizResultsMessage {
  quizId: string;
  userId: string;
  score: number;
  answers: any[];
  feedback?: string;
}

// User event types
export interface UserStatusMessage {
  userId: string;
  status: 'online' | 'away' | 'busy' | 'offline';
  lastSeen?: number;
}

// System notification types
export interface SystemNotificationMessage {
  level: 'info' | 'warning' | 'error' | 'success';
  title?: string;
  message: string;
  actions?: Array<{
    label: string;
    action: string;
  }>;
}

// Roblox environment types
export interface RobloxUpdateMessage {
  environmentId: string;
  type: 'sync' | 'update' | 'command' | 'state';
  data: any;
}

export interface EnvironmentSyncMessage {
  environmentId: string;
  components: any[];
  state: any;
  timestamp: number;
}

// Analytics types
export interface AnalyticsUpdateMessage {
  metric: string;
  value: number;
  trend?: 'up' | 'down' | 'stable';
  comparison?: {
    period: string;
    value: number;
    change: number;
  };
}

export interface MetricsUpdateMessage {
  metrics: Record<string, number>;
  period: string;
  timestamp: number;
}

// Progress tracking types
export interface ProgressUpdateMessage {
  userId?: string;
  classId?: string;
  subject?: string;
  progress: number;
  milestones?: any[];
}

// Agent system types
export interface AgentStatusMessage {
  agentId: string;
  status: 'idle' | 'working' | 'complete' | 'error';
  task?: string;
  progress?: number;
}

export interface AgentTaskMessage {
  agentId: string;
  taskId: string;
  type: string;
  parameters: any;
}

export interface AgentResultMessage {
  agentId: string;
  taskId: string;
  result: any;
  success: boolean;
  error?: string;
}

// Helper type for typed message handlers
export type TypedMessageHandler<T extends WebSocketMessageType> =
  T extends WebSocketMessageType.CONTENT_PROGRESS ? WebSocketEventHandler<ContentProgressMessage> :
  T extends WebSocketMessageType.CONTENT_COMPLETE ? WebSocketEventHandler<ContentCompleteMessage> :
  T extends WebSocketMessageType.CONTENT_ERROR ? WebSocketEventHandler<ContentErrorMessage> :
  T extends WebSocketMessageType.QUIZ_UPDATE ? WebSocketEventHandler<QuizUpdateMessage> :
  T extends WebSocketMessageType.QUIZ_RESULTS ? WebSocketEventHandler<QuizResultsMessage> :
  T extends WebSocketMessageType.USER_STATUS ? WebSocketEventHandler<UserStatusMessage> :
  T extends WebSocketMessageType.SYSTEM_NOTIFICATION ? WebSocketEventHandler<SystemNotificationMessage> :
  T extends WebSocketMessageType.ROBLOX_UPDATE ? WebSocketEventHandler<RobloxUpdateMessage> :
  T extends WebSocketMessageType.ENVIRONMENT_SYNC ? WebSocketEventHandler<EnvironmentSyncMessage> :
  T extends WebSocketMessageType.ANALYTICS_UPDATE ? WebSocketEventHandler<AnalyticsUpdateMessage> :
  T extends WebSocketMessageType.METRICS_UPDATE ? WebSocketEventHandler<MetricsUpdateMessage> :
  T extends WebSocketMessageType.PROGRESS_UPDATE ? WebSocketEventHandler<ProgressUpdateMessage> :
  T extends WebSocketMessageType.AGENT_STATUS ? WebSocketEventHandler<AgentStatusMessage> :
  T extends WebSocketMessageType.AGENT_TASK ? WebSocketEventHandler<AgentTaskMessage> :
  T extends WebSocketMessageType.AGENT_RESULT ? WebSocketEventHandler<AgentResultMessage> :
  WebSocketEventHandler<any>;

// Note: WebSocketEventHandler and WebSocketConnectionState are already exported above
