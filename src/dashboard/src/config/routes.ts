/**
 * Centralized routing configuration for the ToolBoxAI Dashboard
 * This file contains all route definitions and helper functions for navigation
 * 
 * @version 2025
 */

import React from 'react';

// Enhanced route parameter types
export interface DashboardParams {
  // Dashboard route has no parameters
}

export interface UserParams extends Record<string, string> {
  userId: string;
}

export interface ClassParams extends Record<string, string> {
  id: string;
}

export interface LessonParams extends Record<string, string> {
  id: string;
}

export interface AssessmentParams extends Record<string, string> {
  id: string;
}

export interface MissionParams extends Record<string, string> {
  id: string;
}

export interface RewardParams extends Record<string, string> {
  id: string;
}

export interface MessageParams extends Record<string, string> {
  id: string;
}

export interface SchoolParams extends Record<string, string> {
  id: string;
}

export interface IntegrationParams extends Record<string, string> {
  id: string;
}

export interface ChildProgressParams extends Record<string, string> {
  childId: string;
}

export interface RobloxSessionParams extends Record<string, string> {
  id: string;
}

export interface RobloxPreviewParams extends Record<string, string> {
  id: string;
}

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

export const ROUTES = {
  // Authentication routes
  LOGIN: '/login',
  REGISTER: '/register',
  PASSWORD_RESET: '/password-reset',
  
  // Dashboard
  DASHBOARD: '/',
  HOME: '/',
  
  // Teacher routes
  CLASSES: '/classes',
  CLASS_DETAILS: '/classes/:id',
  CLASS_CREATE: '/classes/create',
  LESSONS: '/lessons',
  LESSON_DETAILS: '/lessons/:id',
  LESSON_CREATE: '/lessons/create',
  ASSESSMENTS: '/assessments',
  ASSESSMENT_DETAILS: '/assessments/:id',
  ASSESSMENT_CREATE: '/assessments/create',
  
  // Student routes
  MISSIONS: '/missions',
  MISSION_DETAILS: '/missions/:id',
  REWARDS: '/rewards',
  REWARD_DETAILS: '/rewards/:id',
  AVATAR: '/avatar',
  PLAY: '/play',
  LEADERBOARD: '/leaderboard',
  
  // Shared routes
  PROGRESS: '/progress',
  REPORTS: '/reports',
  MESSAGES: '/messages',
  MESSAGE_COMPOSE: '/messages/compose',
  MESSAGE_THREAD: '/messages/:id',
  SETTINGS: '/settings',
  PROFILE: '/profile',
  
  // Admin routes
  SCHOOLS: '/schools',
  SCHOOL_DETAILS: '/schools/:id',
  USERS: '/users',
  USER_DETAILS: '/users/:id',
  ANALYTICS: '/analytics',
  COMPLIANCE: '/compliance',
  INTEGRATIONS: '/integrations',
  INTEGRATION_DETAILS: '/integrations/:id',
  
  // Parent routes (most are shared)
  CHILD_PROGRESS: '/progress/:childId',
  
  // Roblox routes
  ROBLOX_DASHBOARD: '/roblox',
  ROBLOX_SESSIONS: '/roblox/sessions',
  ROBLOX_SESSION_DETAIL: '/roblox/sessions/:id',
  ROBLOX_CONTENT: '/roblox/content',
  ROBLOX_ANALYTICS: '/roblox/analytics',
  ROBLOX_PREVIEW: '/roblox/preview/:id',
  ROBLOX_SETTINGS: '/roblox/settings',
} as const;

// Type for all routes
export type RouteKey = keyof typeof ROUTES;
export type RouteValue = typeof ROUTES[RouteKey];

/**
 * Helper functions for generating dynamic routes
 */

// Class routes
export const getClassDetailsRoute = (id: string): string => 
  ROUTES.CLASS_DETAILS.replace(':id', id);

export const getClassCreateRoute = (): string => 
  ROUTES.CLASS_CREATE;

// Lesson routes
export const getLessonDetailsRoute = (id: string): string => 
  ROUTES.LESSON_DETAILS.replace(':id', id);

export const getLessonCreateRoute = (): string => 
  ROUTES.LESSON_CREATE;

// Assessment routes
export const getAssessmentDetailsRoute = (id: string): string => 
  ROUTES.ASSESSMENT_DETAILS.replace(':id', id);

export const getAssessmentCreateRoute = (): string => 
  ROUTES.ASSESSMENT_CREATE;

// Mission routes
export const getMissionDetailsRoute = (id: string): string => 
  ROUTES.MISSION_DETAILS.replace(':id', id);

// Reward routes
export const getRewardDetailsRoute = (id: string): string => 
  ROUTES.REWARD_DETAILS.replace(':id', id);

// Message routes
export const getMessageThreadRoute = (id: string): string => 
  ROUTES.MESSAGE_THREAD.replace(':id', id);

// School routes
export const getSchoolDetailsRoute = (id: string): string => 
  ROUTES.SCHOOL_DETAILS.replace(':id', id);

// User routes
export const getUserDetailsRoute = (id: string): string => 
  ROUTES.USER_DETAILS.replace(':id', id);

// Integration routes
export const getIntegrationDetailsRoute = (id: string): string => 
  ROUTES.INTEGRATION_DETAILS.replace(':id', id);

// Parent routes
export const getChildProgressRoute = (childId: string): string => 
  ROUTES.CHILD_PROGRESS.replace(':childId', childId);

// Roblox routes
export const getRobloxSessionDetailRoute = (id: string): string => 
  ROUTES.ROBLOX_SESSION_DETAIL.replace(':id', id);

export const getRobloxPreviewRoute = (id: string): string => 
  ROUTES.ROBLOX_PREVIEW.replace(':id', id);

/**
 * Role-based navigation helpers
 */

export const getRoleDefaultRoute = (role: string): string => {
  switch (role) {
    case 'Teacher':
      return ROUTES.DASHBOARD;
    case 'Student':
      return ROUTES.DASHBOARD;
    case 'Admin':
      return ROUTES.DASHBOARD;
    case 'Parent':
      return ROUTES.DASHBOARD;
    default:
      return ROUTES.LOGIN;
  }
};

/**
 * Navigation guards - check if a user role can access a route
 */
export const canAccessRoute = (role: string, route: string): boolean => {
  const teacherRoutes = [
    ROUTES.CLASSES,
    ROUTES.LESSONS,
    ROUTES.ASSESSMENTS,
    ROUTES.REPORTS,
    ROUTES.MESSAGES,
    ROUTES.ROBLOX_DASHBOARD,
    ROUTES.ROBLOX_SESSIONS,
    ROUTES.ROBLOX_CONTENT,
    ROUTES.ROBLOX_ANALYTICS,
    ROUTES.ROBLOX_PREVIEW,
    ROUTES.ROBLOX_SETTINGS,
  ];
  
  const studentRoutes = [
    ROUTES.MISSIONS,
    ROUTES.REWARDS,
    ROUTES.AVATAR,
    ROUTES.PLAY,
    ROUTES.LEADERBOARD,
    ROUTES.PROGRESS,
  ];
  
  const adminRoutes = [
    ROUTES.SCHOOLS,
    ROUTES.USERS,
    ROUTES.ANALYTICS,
    ROUTES.COMPLIANCE,
    ROUTES.INTEGRATIONS,
  ];
  
  const parentRoutes = [
    ROUTES.PROGRESS,
    ROUTES.REPORTS,
    ROUTES.MESSAGES,
  ];
  
  const sharedRoutes = [
    ROUTES.DASHBOARD,
    ROUTES.SETTINGS,
    ROUTES.PROFILE,
  ];
  
  // Check shared routes first
  if (sharedRoutes.some(r => route.startsWith(r))) {
    return true;
  }
  
  // Check role-specific routes
  switch (role) {
    case 'Teacher':
      return teacherRoutes.some(r => route.startsWith(r));
    case 'Student':
      return studentRoutes.some(r => route.startsWith(r));
    case 'Admin':
      return [...adminRoutes, ...teacherRoutes].some(r => route.startsWith(r));
    case 'Parent':
      return parentRoutes.some(r => route.startsWith(r));
    default:
      return false;
  }
};

/**
 * Breadcrumb generator
 */
export const getBreadcrumbs = (pathname: string): { label: string; path: string }[] => {
  const breadcrumbs: { label: string; path: string }[] = [{ label: 'Home', path: ROUTES.DASHBOARD as string }];
  
  if (pathname.startsWith(ROUTES.CLASSES)) {
    breadcrumbs.push({ label: 'Classes', path: ROUTES.CLASSES as string });
    if (pathname.includes('/create')) {
      breadcrumbs.push({ label: 'Create', path: pathname });
    } else if (pathname !== ROUTES.CLASSES) {
      breadcrumbs.push({ label: 'Details', path: pathname });
    }
  } else if (pathname.startsWith(ROUTES.LESSONS)) {
    breadcrumbs.push({ label: 'Lessons', path: ROUTES.LESSONS as string });
    if (pathname.includes('/create')) {
      breadcrumbs.push({ label: 'Create', path: pathname });
    } else if (pathname !== ROUTES.LESSONS) {
      breadcrumbs.push({ label: 'Details', path: pathname });
    }
  } else if (pathname.startsWith(ROUTES.ASSESSMENTS)) {
    breadcrumbs.push({ label: 'Assessments', path: ROUTES.ASSESSMENTS as string });
    if (pathname.includes('/create')) {
      breadcrumbs.push({ label: 'Create', path: pathname });
    } else if (pathname !== ROUTES.ASSESSMENTS) {
      breadcrumbs.push({ label: 'Details', path: pathname });
    }
  }
  // Add more breadcrumb logic as needed
  
  return breadcrumbs;
};

export default ROUTES;