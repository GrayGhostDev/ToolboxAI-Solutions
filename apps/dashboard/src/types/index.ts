export { type UserRole, type RolePermissions, ROLE_PERMISSIONS } from './roles';
export * from './api';

// Redux State Types
export interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  language: string;
  notifications: NotificationItem[];
}

export interface UserState {
  userId?: string;
  email?: string;
  displayName?: string;
  avatarUrl?: string;
  role: import('./roles').UserRole;
  isAuthenticated: boolean;
  token?: string;
  refreshToken?: string;
}

export interface DashboardState {
  loading: boolean;
  error: string | null;
  metrics: import('./api').DashboardMetrics | null;
  recentActivity: import('./api').Activity[];
  upcomingEvents: import('./api').Event[];
}

export interface GamificationState {
  xp: number;
  level: number;
  nextLevelXP: number;
  badges: import('./api').Badge[];
  leaderboard: import('./api').LeaderboardEntry[];
  recentXPTransactions: import('./api').XPTransaction[];
}

export interface NotificationItem {
  id: string;
  type: 'info' | 'warning' | 'success' | 'error';
  message: string;
  timestamp: number;
  autoHide?: boolean;
}