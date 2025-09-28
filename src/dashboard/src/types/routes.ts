/**
 * Route Type Definitions for ToolboxAI Dashboard
 * 
 * Provides comprehensive type definitions for routing and navigation
 * in the ToolboxAI Dashboard application.
 * 
 * @version 2025
 */

import { RouteParams, QueryParams } from './utility-types';

// Route parameter types using proper object types instead of empty objects
export interface DashboardParams extends Record<string, never> {
  // Dashboard route has no parameters
}

export interface UserParams extends Record<string, string> {
  userId: string;
}

export interface ClassParams extends Record<string, string> {
  classId: string;
}

export interface LessonParams extends Record<string, string> {
  classId: string;
  lessonId: string;
}

export interface AssessmentParams extends Record<string, string> {
  classId: string;
  assessmentId: string;
}

export interface StudentParams extends Record<string, string> {
  studentId: string;
}

export interface SchoolParams extends Record<string, string> {
  schoolId: string;
}

export interface ReportParams extends Record<string, string> {
  reportId: string;
}

export interface AnalyticsParams extends Record<string, string> {
  analyticsId: string;
}

export interface SettingsParams extends Record<string, never> {
  // Settings route has no parameters
}

export interface ProfileParams extends Record<string, never> {
  // Profile route has no parameters
}

// Route path constants
export const ROUTES = {
  // Public routes
  HOME: '/',
  LOGIN: '/login',
  SIGNUP: '/signup',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',
  
  // Protected routes
  DASHBOARD: '/dashboard',
  
  // User management
  USERS: '/users',
  USER_PROFILE: '/users/:userId',
  USER_EDIT: '/users/:userId/edit',
  
  // Class management
  CLASSES: '/classes',
  CLASS_DETAIL: '/classes/:classId',
  CLASS_EDIT: '/classes/:classId/edit',
  CLASS_CREATE: '/classes/create',
  
  // Lesson management
  LESSONS: '/classes/:classId/lessons',
  LESSON_DETAIL: '/classes/:classId/lessons/:lessonId',
  LESSON_EDIT: '/classes/:classId/lessons/:lessonId/edit',
  LESSON_CREATE: '/classes/:classId/lessons/create',
  
  // Assessment management
  ASSESSMENTS: '/classes/:classId/assessments',
  ASSESSMENT_DETAIL: '/classes/:classId/assessments/:assessmentId',
  ASSESSMENT_EDIT: '/classes/:classId/assessments/:assessmentId/edit',
  ASSESSMENT_CREATE: '/classes/:classId/assessments/create',
  
  // Student management
  STUDENTS: '/students',
  STUDENT_DETAIL: '/students/:studentId',
  STUDENT_PROGRESS: '/students/:studentId/progress',
  
  // School management (admin only)
  SCHOOLS: '/schools',
  SCHOOL_DETAIL: '/schools/:schoolId',
  SCHOOL_EDIT: '/schools/:schoolId/edit',
  
  // Reports and Analytics
  REPORTS: '/reports',
  REPORT_DETAIL: '/reports/:reportId',
  ANALYTICS: '/analytics',
  ANALYTICS_DETAIL: '/analytics/:analyticsId',
  
  // Settings
  SETTINGS: '/settings',
  SETTINGS_PROFILE: '/settings/profile',
  SETTINGS_ACCOUNT: '/settings/account',
  SETTINGS_SECURITY: '/settings/security',
  SETTINGS_NOTIFICATIONS: '/settings/notifications',
  SETTINGS_PREFERENCES: '/settings/preferences',
  
  // Admin routes
  ADMIN: '/admin',
  ADMIN_USERS: '/admin/users',
  ADMIN_SCHOOLS: '/admin/schools',
  ADMIN_SYSTEM: '/admin/system',
  ADMIN_SETTINGS: '/admin/settings',
  
  // Roblox-specific routes
  ROBLOX: '/roblox',
  ROBLOX_STUDIO: '/roblox/studio',
  ROBLOX_ENVIRONMENTS: '/roblox/environments',
  ROBLOX_SESSIONS: '/roblox/sessions',
  ROBLOX_CONTENT: '/roblox/content',
  
  // Error routes
  NOT_FOUND: '/404',
  UNAUTHORIZED: '/401',
  FORBIDDEN: '/403',
  SERVER_ERROR: '/500',
} as const;

// Route metadata interface
export interface RouteMetadata {
  title: string;
  description?: string;
  requiresAuth: boolean;
  roles?: string[];
  breadcrumb?: string;
  icon?: string;
  hidden?: boolean;
  exact?: boolean;
}

// Route configuration type
export interface RouteConfig {
  path: string;
  component: React.ComponentType<any>;
  metadata: RouteMetadata;
  children?: RouteConfig[];
}

// Navigation item type
export interface NavigationItem {
  key: string;
  label: string;
  icon?: React.ComponentType<any>;
  path?: string;
  children?: NavigationItem[];
  disabled?: boolean;
  badge?: string | number;
  roles?: string[];
}

// Breadcrumb item type
export interface BreadcrumbItem {
  label: string;
  path?: string;
  icon?: React.ComponentType<any>;
  active?: boolean;
}

// Route guard types
export type RouteGuard = (
  to: string,
  from?: string,
  params?: RouteParams,
  query?: QueryParams
) => boolean | Promise<boolean>;

export interface RouteGuardConfig {
  name: string;
  guard: RouteGuard;
  redirectTo?: string;
  message?: string;
}

// Route transition types
export type RouteTransition = 'fade' | 'slide' | 'scale' | 'none';

export interface RouteTransitionConfig {
  enter: RouteTransition;
  exit: RouteTransition;
  duration?: number;
}

// Route error types
export interface RouteError {
  statusCode: number;
  message: string;
  details?: string;
  timestamp: Date;
  path: string;
  userId?: string;
}

// Route analytics types
export interface RouteAnalytics {
  path: string;
  visits: number;
  uniqueVisitors: number;
  averageTimeSpent: number;
  bounceRate: number;
  lastVisited: Date;
  userRoles: string[];
}

// Query parameter schemas for type safety
export interface DashboardQuery extends Record<string, string | undefined> {
  view?: 'grid' | 'list' | 'compact';
  sort?: 'name' | 'date' | 'status';
  filter?: string;
  search?: string;
}

export interface ClassQuery extends Record<string, string | undefined> {
  tab?: 'overview' | 'students' | 'lessons' | 'assessments' | 'settings';
  studentId?: string;
  lessonId?: string;
}

export interface ReportQuery extends Record<string, string | undefined> {
  period?: 'day' | 'week' | 'month' | 'quarter' | 'year';
  format?: 'chart' | 'table' | 'export';
  comparison?: 'previous' | 'year-over-year';
}

export interface SettingsQuery extends Record<string, string | undefined> {
  section?: 'general' | 'security' | 'notifications' | 'advanced';
  changed?: 'true' | 'false';
}

// Route state types for navigation
export interface RouteState {
  from?: string;
  returnUrl?: string;
  data?: Record<string, any>;
  preserveScroll?: boolean;
}

// Route loading states
export interface RouteLoadingState {
  isLoading: boolean;
  progress?: number;
  stage?: 'resolving' | 'loading' | 'rendering';
  error?: RouteError;
}

// Route cache types
export interface RouteCacheConfig {
  ttl: number; // Time to live in milliseconds
  maxSize: number;
  strategy: 'lru' | 'fifo' | 'lfu';
}

export interface CachedRoute {
  path: string;
  component: React.ComponentType<any>;
  data?: any;
  timestamp: number;
  hits: number;
}

// Route helper functions
export const buildPath = (template: string, params: RouteParams): string => {
  return Object.entries(params).reduce(
    (path, [key, value]) => path.replace(`:${key}`, encodeURIComponent(value)),
    template
  );
};

export const parsePath = (template: string, path: string): RouteParams | null => {
  const templateParts = template.split('/');
  const pathParts = path.split('/');
  
  if (templateParts.length !== pathParts.length) {
    return null;
  }
  
  const params: RouteParams = {};
  
  for (let i = 0; i < templateParts.length; i++) {
    const templatePart = templateParts[i];
    const pathPart = pathParts[i];
    
    if (templatePart.startsWith(':')) {
      const paramName = templatePart.slice(1);
      params[paramName] = decodeURIComponent(pathPart);
    } else if (templatePart !== pathPart) {
      return null;
    }
  }
  
  return params;
};

export const isRouteActive = (currentPath: string, routePath: string, exact = false): boolean => {
  if (exact) {
    return currentPath === routePath;
  }
  return currentPath.startsWith(routePath);
};

export const getRouteBreadcrumbs = (path: string): BreadcrumbItem[] => {
  const parts = path.split('/').filter(Boolean);
  const breadcrumbs: BreadcrumbItem[] = [
    { label: 'Home', path: '/' }
  ];
  
  let currentPath = '';
  
  for (const part of parts) {
    currentPath += `/${part}`;
    breadcrumbs.push({
      label: part.charAt(0).toUpperCase() + part.slice(1),
      path: currentPath
    });
  }
  
  if (breadcrumbs.length > 1) {
    breadcrumbs[breadcrumbs.length - 1].active = true;
  }
  
  return breadcrumbs;
};

// Type guards
export const isValidRoute = (path: string): boolean => {
  return Object.values(ROUTES).includes(path as any);
};

export const requiresAuthentication = (path: string): boolean => {
  const publicRoutes = [
    ROUTES.HOME,
    ROUTES.LOGIN,
    ROUTES.SIGNUP,
    ROUTES.FORGOT_PASSWORD,
    ROUTES.RESET_PASSWORD
  ];
  
  return !publicRoutes.includes(path as any);
};

// Route parameter extraction utility
export type ExtractParams<T extends string> = 
  T extends `${infer _Start}:${infer Param}/${infer Rest}`
    ? { [K in Param]: string } & ExtractParams<Rest>
    : T extends `${infer _Start}:${infer Param}`
    ? { [K in Param]: string }
    : Record<string, never>;