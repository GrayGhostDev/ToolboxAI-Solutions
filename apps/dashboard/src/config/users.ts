/**
 * User Configuration for ToolBoxAI Dashboard
 * Comprehensive user role configurations, features, and settings
 */

import { type UserRole } from '../types/roles';

// User role configurations with all dashboard features
export interface UserRoleConfig {
  role: UserRole;
  displayName: string;
  description: string;
  defaultRoute: string;
  theme: {
    primaryColor: string;
    secondaryColor: string;
    dashboardLayout: 'grid' | 'list' | 'cards';
  };
  features: {
    dashboard: DashboardFeatures;
    navigation: NavigationItem[];
    widgets: WidgetConfig[];
    notifications: NotificationSettings;
  };
  api: {
    endpoints: string[];
    refreshInterval: number;
    cacheTimeout: number;
  };
  limits: {
    maxClasses?: number;
    maxStudents?: number;
    maxContentGeneration?: number;
    maxStorageGB?: number;
  };
}

interface DashboardFeatures {
  showWelcomeMessage: boolean;
  showQuickActions: boolean;
  showStatistics: boolean;
  showRecentActivity: boolean;
  showLeaderboard: boolean;
  showCalendar: boolean;
  showNotifications: boolean;
  showRobloxIntegration: boolean;
  showAIAssistant: boolean;
}

interface NavigationItem {
  id: string;
  label: string;
  icon: string;
  path: string;
  badge?: boolean;
  children?: NavigationItem[];
}

interface WidgetConfig {
  id: string;
  type: 'chart' | 'list' | 'card' | 'calendar' | 'progress' | 'feed';
  title: string;
  position: { x: number; y: number; w: number; h: number };
  refreshInterval?: number;
  dataSource: string;
}

interface NotificationSettings {
  enabled: boolean;
  types: string[];
  channels: ('email' | 'push' | 'inApp' | 'sms')[];
  frequency: 'realtime' | 'hourly' | 'daily' | 'weekly';
}

// Admin Configuration
export const ADMIN_CONFIG: UserRoleConfig = {
  role: 'admin',
  displayName: 'Administrator',
  description: 'Full system access and management capabilities',
  defaultRoute: '/admin/dashboard',
  theme: {
    primaryColor: '#1976D2',
    secondaryColor: '#FFA726',
    dashboardLayout: 'grid',
  },
  features: {
    dashboard: {
      showWelcomeMessage: true,
      showQuickActions: true,
      showStatistics: true,
      showRecentActivity: true,
      showLeaderboard: true,
      showCalendar: true,
      showNotifications: true,
      showRobloxIntegration: true,
      showAIAssistant: true,
    },
    navigation: [
      { id: 'dashboard', label: 'Dashboard', icon: 'Dashboard', path: '/admin/dashboard' },
      { 
        id: 'users', 
        label: 'User Management', 
        icon: 'People', 
        path: '/admin/users',
        children: [
          { id: 'all-users', label: 'All Users', icon: 'Group', path: '/admin/users/all' },
          { id: 'teachers', label: 'Teachers', icon: 'School', path: '/admin/users/teachers' },
          { id: 'students', label: 'Students', icon: 'Face', path: '/admin/users/students' },
          { id: 'parents', label: 'Parents', icon: 'FamilyRestroom', path: '/admin/users/parents' },
          { id: 'roles', label: 'Roles & Permissions', icon: 'Security', path: '/admin/users/roles' },
        ]
      },
      { 
        id: 'schools', 
        label: 'Schools', 
        icon: 'Business', 
        path: '/admin/schools',
        children: [
          { id: 'all-schools', label: 'All Schools', icon: 'List', path: '/admin/schools/all' },
          { id: 'add-school', label: 'Add School', icon: 'Add', path: '/admin/schools/add' },
          { id: 'districts', label: 'Districts', icon: 'Map', path: '/admin/schools/districts' },
        ]
      },
      { 
        id: 'content', 
        label: 'Content Management', 
        icon: 'LibraryBooks', 
        path: '/admin/content',
        children: [
          { id: 'curriculum', label: 'Curriculum', icon: 'Book', path: '/admin/content/curriculum' },
          { id: 'assessments', label: 'Assessments', icon: 'Assignment', path: '/admin/content/assessments' },
          { id: 'roblox-worlds', label: 'Roblox Worlds', icon: 'Games', path: '/admin/content/roblox' },
        ]
      },
      { id: 'analytics', label: 'Analytics', icon: 'Analytics', path: '/admin/analytics', badge: true },
      { id: 'integrations', label: 'Integrations', icon: 'Extension', path: '/admin/integrations' },
      { id: 'settings', label: 'System Settings', icon: 'Settings', path: '/admin/settings' },
      { id: 'compliance', label: 'Compliance', icon: 'Policy', path: '/admin/compliance' },
      { id: 'support', label: 'Support Tickets', icon: 'Support', path: '/admin/support', badge: true },
    ],
    widgets: [
      { id: 'user-stats', type: 'card', title: 'User Statistics', position: { x: 0, y: 0, w: 3, h: 2 }, dataSource: '/api/admin/stats/users' },
      { id: 'system-health', type: 'chart', title: 'System Health', position: { x: 3, y: 0, w: 3, h: 2 }, dataSource: '/api/admin/health' },
      { id: 'recent-activity', type: 'feed', title: 'Recent Activity', position: { x: 6, y: 0, w: 3, h: 2 }, dataSource: '/api/admin/activity' },
      { id: 'revenue', type: 'chart', title: 'Revenue Analytics', position: { x: 9, y: 0, w: 3, h: 2 }, dataSource: '/api/admin/revenue' },
      { id: 'support-queue', type: 'list', title: 'Support Queue', position: { x: 0, y: 2, w: 4, h: 3 }, dataSource: '/api/admin/support/queue' },
      { id: 'server-metrics', type: 'chart', title: 'Server Metrics', position: { x: 4, y: 2, w: 4, h: 3 }, dataSource: '/api/admin/metrics' },
      { id: 'compliance-status', type: 'card', title: 'Compliance Status', position: { x: 8, y: 2, w: 4, h: 3 }, dataSource: '/api/admin/compliance/status' },
    ],
    notifications: {
      enabled: true,
      types: ['system', 'security', 'user', 'content', 'integration', 'compliance'],
      channels: ['email', 'push', 'inApp'],
      frequency: 'realtime',
    },
  },
  api: {
    endpoints: ['/api/admin/*', '/api/users/*', '/api/schools/*', '/api/analytics/*', '/api/system/*'],
    refreshInterval: 30000,
    cacheTimeout: 60000,
  },
  limits: {
    maxClasses: -1, // Unlimited
    maxStudents: -1,
    maxContentGeneration: -1,
    maxStorageGB: -1,
  },
};

// Teacher Configuration
export const TEACHER_CONFIG: UserRoleConfig = {
  role: 'teacher',
  displayName: 'Teacher',
  description: 'Manage classes, create content, and track student progress',
  defaultRoute: '/teacher/dashboard',
  theme: {
    primaryColor: '#4CAF50',
    secondaryColor: '#FF9800',
    dashboardLayout: 'cards',
  },
  features: {
    dashboard: {
      showWelcomeMessage: true,
      showQuickActions: true,
      showStatistics: true,
      showRecentActivity: true,
      showLeaderboard: true,
      showCalendar: true,
      showNotifications: true,
      showRobloxIntegration: true,
      showAIAssistant: true,
    },
    navigation: [
      { id: 'dashboard', label: 'My Dashboard', icon: 'Dashboard', path: '/teacher/dashboard' },
      { 
        id: 'classes', 
        label: 'My Classes', 
        icon: 'Class', 
        path: '/teacher/classes',
        badge: true,
        children: [
          { id: 'manage', label: 'Manage Classes', icon: 'Edit', path: '/teacher/classes/manage' },
          { id: 'schedule', label: 'Schedule', icon: 'Schedule', path: '/teacher/classes/schedule' },
          { id: 'attendance', label: 'Attendance', icon: 'CheckCircle', path: '/teacher/classes/attendance' },
        ]
      },
      { 
        id: 'lessons', 
        label: 'Lessons', 
        icon: 'MenuBook', 
        path: '/teacher/lessons',
        children: [
          { id: 'create', label: 'Create Lesson', icon: 'Add', path: '/teacher/lessons/create' },
          { id: 'library', label: 'Lesson Library', icon: 'LibraryBooks', path: '/teacher/lessons/library' },
          { id: 'ai-generate', label: 'AI Generator', icon: 'AutoAwesome', path: '/teacher/lessons/ai-generate' },
        ]
      },
      { 
        id: 'assessments', 
        label: 'Assessments', 
        icon: 'Assignment', 
        path: '/teacher/assessments',
        children: [
          { id: 'create', label: 'Create Assessment', icon: 'Add', path: '/teacher/assessments/create' },
          { id: 'grade', label: 'Grade', icon: 'Grade', path: '/teacher/assessments/grade', badge: true },
          { id: 'results', label: 'Results', icon: 'Assessment', path: '/teacher/assessments/results' },
        ]
      },
      { 
        id: 'students', 
        label: 'Students', 
        icon: 'People', 
        path: '/teacher/students',
        children: [
          { id: 'roster', label: 'Class Roster', icon: 'List', path: '/teacher/students/roster' },
          { id: 'progress', label: 'Progress Tracking', icon: 'TrendingUp', path: '/teacher/students/progress' },
          { id: 'reports', label: 'Reports', icon: 'Description', path: '/teacher/students/reports' },
        ]
      },
      { id: 'roblox', label: 'Roblox Worlds', icon: 'Games', path: '/teacher/roblox' },
      { id: 'messages', label: 'Messages', icon: 'Message', path: '/teacher/messages', badge: true },
      { id: 'resources', label: 'Resources', icon: 'Folder', path: '/teacher/resources' },
      { id: 'settings', label: 'Settings', icon: 'Settings', path: '/teacher/settings' },
    ],
    widgets: [
      { id: 'class-overview', type: 'card', title: "Today's Classes", position: { x: 0, y: 0, w: 4, h: 2 }, dataSource: '/api/teacher/classes/today' },
      { id: 'student-progress', type: 'chart', title: 'Class Progress', position: { x: 4, y: 0, w: 4, h: 2 }, dataSource: '/api/teacher/progress' },
      { id: 'pending-grades', type: 'list', title: 'Pending Grades', position: { x: 8, y: 0, w: 4, h: 2 }, dataSource: '/api/teacher/grades/pending' },
      { id: 'calendar', type: 'calendar', title: 'Schedule', position: { x: 0, y: 2, w: 6, h: 3 }, dataSource: '/api/teacher/calendar' },
      { id: 'recent-submissions', type: 'feed', title: 'Recent Submissions', position: { x: 6, y: 2, w: 6, h: 3 }, dataSource: '/api/teacher/submissions' },
    ],
    notifications: {
      enabled: true,
      types: ['assignment', 'submission', 'message', 'announcement', 'reminder'],
      channels: ['email', 'inApp', 'push'],
      frequency: 'realtime',
    },
  },
  api: {
    endpoints: ['/api/teacher/*', '/api/classes/*', '/api/lessons/*', '/api/assessments/*', '/api/students/*'],
    refreshInterval: 60000,
    cacheTimeout: 120000,
  },
  limits: {
    maxClasses: 10,
    maxStudents: 300,
    maxContentGeneration: 100,
    maxStorageGB: 50,
  },
};

// Student Configuration
export const STUDENT_CONFIG: UserRoleConfig = {
  role: 'student',
  displayName: 'Student',
  description: 'Learn, play, and track your progress',
  defaultRoute: '/student/dashboard',
  theme: {
    primaryColor: '#9C27B0',
    secondaryColor: '#00BCD4',
    dashboardLayout: 'cards',
  },
  features: {
    dashboard: {
      showWelcomeMessage: true,
      showQuickActions: true,
      showStatistics: true,
      showRecentActivity: true,
      showLeaderboard: true,
      showCalendar: false,
      showNotifications: true,
      showRobloxIntegration: true,
      showAIAssistant: false,
    },
    navigation: [
      { id: 'dashboard', label: 'My Learning', icon: 'School', path: '/student/dashboard' },
      { id: 'classes', label: 'My Classes', icon: 'Class', path: '/student/classes' },
      { id: 'lessons', label: 'Lessons', icon: 'MenuBook', path: '/student/lessons', badge: true },
      { id: 'assignments', label: 'Assignments', icon: 'Assignment', path: '/student/assignments', badge: true },
      { id: 'roblox', label: 'Play & Learn', icon: 'Games', path: '/student/roblox' },
      { id: 'progress', label: 'My Progress', icon: 'TrendingUp', path: '/student/progress' },
      { id: 'achievements', label: 'Achievements', icon: 'EmojiEvents', path: '/student/achievements' },
      { id: 'leaderboard', label: 'Leaderboard', icon: 'Leaderboard', path: '/student/leaderboard' },
      { id: 'profile', label: 'My Profile', icon: 'Person', path: '/student/profile' },
    ],
    widgets: [
      { id: 'xp-progress', type: 'progress', title: 'Level Progress', position: { x: 0, y: 0, w: 3, h: 2 }, dataSource: '/api/student/xp' },
      { id: 'assignments-due', type: 'list', title: 'Due Soon', position: { x: 3, y: 0, w: 3, h: 2 }, dataSource: '/api/student/assignments/due' },
      { id: 'recent-achievements', type: 'card', title: 'Recent Badges', position: { x: 6, y: 0, w: 3, h: 2 }, dataSource: '/api/student/achievements/recent' },
      { id: 'class-rank', type: 'card', title: 'Class Rank', position: { x: 9, y: 0, w: 3, h: 2 }, dataSource: '/api/student/rank' },
      { id: 'learning-path', type: 'progress', title: 'Learning Path', position: { x: 0, y: 2, w: 6, h: 3 }, dataSource: '/api/student/path' },
      { id: 'roblox-worlds', type: 'list', title: 'Available Worlds', position: { x: 6, y: 2, w: 6, h: 3 }, dataSource: '/api/student/roblox/worlds' },
    ],
    notifications: {
      enabled: true,
      types: ['assignment', 'achievement', 'reminder', 'game', 'feedback'],
      channels: ['inApp', 'push'],
      frequency: 'realtime',
    },
  },
  api: {
    endpoints: ['/api/student/*', '/api/assignments/*', '/api/progress/*', '/api/achievements/*', '/api/roblox/*'],
    refreshInterval: 120000,
    cacheTimeout: 180000,
  },
  limits: {
    maxClasses: 8,
    maxContentGeneration: 0,
    maxStorageGB: 5,
  },
};

// Parent Configuration
export const PARENT_CONFIG: UserRoleConfig = {
  role: 'parent',
  displayName: 'Parent/Guardian',
  description: "Monitor your child's progress and communicate with teachers",
  defaultRoute: '/parent/dashboard',
  theme: {
    primaryColor: '#FF5722',
    secondaryColor: '#607D8B',
    dashboardLayout: 'list',
  },
  features: {
    dashboard: {
      showWelcomeMessage: true,
      showQuickActions: false,
      showStatistics: true,
      showRecentActivity: true,
      showLeaderboard: false,
      showCalendar: true,
      showNotifications: true,
      showRobloxIntegration: false,
      showAIAssistant: false,
    },
    navigation: [
      { id: 'dashboard', label: 'Overview', icon: 'Dashboard', path: '/parent/dashboard' },
      { id: 'children', label: 'My Children', icon: 'ChildCare', path: '/parent/children' },
      { id: 'progress', label: 'Progress Reports', icon: 'Assessment', path: '/parent/progress' },
      { id: 'attendance', label: 'Attendance', icon: 'EventAvailable', path: '/parent/attendance' },
      { id: 'assignments', label: 'Assignments', icon: 'Assignment', path: '/parent/assignments' },
      { id: 'messages', label: 'Messages', icon: 'Message', path: '/parent/messages', badge: true },
      { id: 'teachers', label: 'Teachers', icon: 'School', path: '/parent/teachers' },
      { id: 'calendar', label: 'School Calendar', icon: 'CalendarToday', path: '/parent/calendar' },
      { id: 'settings', label: 'Settings', icon: 'Settings', path: '/parent/settings' },
    ],
    widgets: [
      { id: 'children-overview', type: 'card', title: 'Children Overview', position: { x: 0, y: 0, w: 4, h: 2 }, dataSource: '/api/parent/children/overview' },
      { id: 'recent-grades', type: 'list', title: 'Recent Grades', position: { x: 4, y: 0, w: 4, h: 2 }, dataSource: '/api/parent/grades/recent' },
      { id: 'upcoming-events', type: 'list', title: 'Upcoming Events', position: { x: 8, y: 0, w: 4, h: 2 }, dataSource: '/api/parent/events' },
      { id: 'attendance-summary', type: 'chart', title: 'Attendance', position: { x: 0, y: 2, w: 6, h: 3 }, dataSource: '/api/parent/attendance/summary' },
      { id: 'progress-chart', type: 'chart', title: 'Academic Progress', position: { x: 6, y: 2, w: 6, h: 3 }, dataSource: '/api/parent/progress/chart' },
    ],
    notifications: {
      enabled: true,
      types: ['grade', 'attendance', 'message', 'announcement', 'emergency'],
      channels: ['email', 'sms', 'inApp'],
      frequency: 'daily',
    },
  },
  api: {
    endpoints: ['/api/parent/*', '/api/children/*', '/api/progress/*', '/api/messages/*'],
    refreshInterval: 300000,
    cacheTimeout: 600000,
  },
  limits: {
    maxClasses: 0,
    maxStudents: 0,
    maxContentGeneration: 0,
    maxStorageGB: 1,
  },
};

// Role configuration map
export const USER_ROLE_CONFIGS: Record<UserRole, UserRoleConfig> = {
  admin: ADMIN_CONFIG,
  teacher: TEACHER_CONFIG,
  student: STUDENT_CONFIG,
  parent: PARENT_CONFIG,
};

// Helper function to get user configuration
export function getUserConfig(role: UserRole): UserRoleConfig {
  return USER_ROLE_CONFIGS[role] || STUDENT_CONFIG;
}

// Authentication should be handled by the backend
// Never store credentials in frontend code
// Use the authentication service to validate users
export const AUTH_CONFIG = {
  loginEndpoint: '/api/v1/auth/login',
  refreshEndpoint: '/api/v1/auth/refresh',
  logoutEndpoint: '/api/v1/auth/logout',
  tokenKey: 'toolboxai_auth_token',
  refreshTokenKey: 'toolboxai_refresh_token',

  // Password requirements for validation
  passwordRequirements: {
    minLength: 12,
    requireUppercase: true,
    requireLowercase: true,
    requireNumbers: true,
    requireSpecialChars: true,
    specialChars: '!@#$%^&*()_+-=[]{}|;:,.<>?',
  },

  // Session configuration
  sessionTimeout: 1800000, // 30 minutes
  rememberMeDuration: 604800000, // 7 days
  maxLoginAttempts: 5,
  lockoutDuration: 900000, // 15 minutes
};

// Default dashboard settings
export const DEFAULT_DASHBOARD_SETTINGS = {
  refreshInterval: 60000,
  autoSave: true,
  darkMode: false,
  language: 'en',
  timezone: 'America/New_York',
  dateFormat: 'MM/DD/YYYY',
  timeFormat: '12h',
  currency: 'USD',
  notifications: {
    sound: true,
    desktop: true,
    email: true,
  },
  accessibility: {
    highContrast: false,
    fontSize: 'medium',
    reducedMotion: false,
    screenReader: false,
  },
};