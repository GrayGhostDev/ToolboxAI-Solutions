/**
 * API Response Type Definitions
 * Fixes API response property access errors
 */

// Base API Response Structure
export interface ApiResponse<T = unknown> {
  data?: T;
  result?: T;
  error?: string | ErrorDetails;
  success: boolean;
  message?: string;
  status?: number;
  statusText?: string;
}

export interface ErrorDetails {
  code: string;
  message: string;
  details?: unknown;
  stack?: string;
}

// Paginated Responses
export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
    hasNext?: boolean;
    hasPrev?: boolean;
  };
}

// Environment and System Responses
export interface EnvironmentStatusResponse {
  status: 'active' | 'inactive' | 'error' | 'pending';
  message: string;
  data?: {
    uptime?: number;
    version?: string;
    health?: 'good' | 'warning' | 'critical';
  };
}

export interface SystemHealthResponse {
  status: 'healthy' | 'degraded' | 'down';
  services: Record<string, ServiceStatus>;
  timestamp: number;
}

export interface ServiceStatus {
  status: 'up' | 'down' | 'degraded';
  responseTime?: number;
  lastCheck: number;
  error?: string;
}

// Authentication Responses
export interface AuthResponse {
  token: string;
  refreshToken?: string;
  user: UserInfo;
  expiresIn: number;
  permissions?: string[];
}

export interface UserInfo {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  avatar?: string;
  settings?: UserSettings;
}

export interface UserSettings {
  theme?: 'light' | 'dark' | 'auto';
  language?: string;
  notifications?: boolean;
  timezone?: string;
}

export type UserRole = 'student' | 'teacher' | 'parent' | 'admin' | 'super_admin';

// Dashboard and Analytics Responses
export interface DashboardOverviewResponse {
  summary: {
    totalStudents: number;
    totalLessons: number;
    totalAssessments: number;
    averageScore: number;
  };
  recentActivity: ActivityItem[];
  performance: PerformanceMetrics;
}

export interface ActivityItem {
  id: string;
  type: 'lesson' | 'assessment' | 'achievement' | 'message';
  title: string;
  description?: string;
  timestamp: number;
  userId?: string;
  metadata?: Record<string, unknown>;
}

export interface PerformanceMetrics {
  scores: ScoreData[];
  engagement: EngagementData[];
  progression: ProgressionData[];
}

export interface ScoreData {
  date: string;
  score: number;
  subject?: string;
  assessmentId?: string;
}

export interface EngagementData {
  date: string;
  timeSpent: number;
  interactions: number;
  completionRate: number;
}

export interface ProgressionData {
  subject: string;
  level: number;
  xp: number;
  badgesEarned: number;
  lessonsCompleted: number;
}

// Roblox-specific Response Types
export interface RobloxEnvironmentResponse {
  environmentId: string;
  name: string;
  description?: string;
  status: 'active' | 'inactive' | 'building' | 'error';
  playerCount?: number;
  maxPlayers?: number;
  gameData?: RobloxGameData;
}

export interface RobloxGameData {
  worlds?: World[];
  characters?: Character[];
  assets?: Asset[];
  scripts?: Script[];
}

export interface World {
  id: string;
  name: string;
  terrain?: TerrainData;
  objects?: GameObject[];
}

export interface TerrainData {
  type: 'grass' | 'water' | 'sand' | 'rock' | 'snow';
  elevation: number;
  texture?: string;
}

export interface GameObject {
  id: string;
  type: string;
  position: Vector3;
  rotation: Vector3;
  scale: Vector3;
  properties?: Record<string, unknown>;
}

export interface Vector3 {
  x: number;
  y: number;
  z: number;
}

export interface Character {
  id: string;
  name: string;
  model?: string;
  accessories?: string[];
  animations?: Animation[];
}

export interface Animation {
  id: string;
  name: string;
  duration: number;
  keyframes: AnimationKeyframe[];
}

export interface AnimationKeyframe {
  time: number;
  position?: Vector3;
  rotation?: Vector3;
  scale?: Vector3;
}

export interface Asset {
  id: string;
  name: string;
  type: 'model' | 'texture' | 'sound' | 'script' | 'animation';
  url?: string;
  metadata?: AssetMetadata;
}

export interface AssetMetadata {
  size?: number;
  format?: string;
  resolution?: string;
  duration?: number;
  creator?: string;
  tags?: string[];
}

export interface Script {
  id: string;
  name: string;
  language: 'lua' | 'typescript';
  content: string;
  dependencies?: string[];
}

// WebSocket Response Types
export interface WebSocketResponse<T = unknown> {
  event: string;
  data: T;
  channel?: string;
  timestamp: number;
  messageId?: string;
}

export interface RealtimeUpdate<T = unknown> {
  type: string;
  payload: T;
  userId?: string;
  sessionId?: string;
  timestamp: number;
}