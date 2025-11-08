/**
 * Authentication Utility Functions
 * Handles role-based routing and permission checking
 */

import { type UserRole } from '../types/roles';
import { logger } from './logger';

/**
 * Get the role from Clerk user metadata
 */
export function getUserRoleFromClerk(clerkUser: any): UserRole {
  const role = clerkUser?.publicMetadata?.role as UserRole | undefined;

  if (role && ['admin', 'teacher', 'student', 'parent'].includes(role)) {
    return role;
  }

  // Default to student if no role is set
  logger.warn('No valid role found in user metadata, defaulting to student');
  return 'student';
}

/**
 * Get the default route for a given role
 */
export function getDefaultRouteForRole(role: UserRole): string {
  const roleRoutes: Record<UserRole, string> = {
    admin: '/admin/overview',
    teacher: '/teacher/overview',
    student: '/student/overview',
    parent: '/parent/overview',
  };

  return roleRoutes[role] || '/';
}

/**
 * Check if a user has permission to access a route
 */
export function canAccessRoute(userRole: UserRole, allowedRoles: UserRole[]): boolean {
  return allowedRoles.includes(userRole);
}

/**
 * Get role display name
 */
export function getRoleDisplayName(role: UserRole): string {
  const displayNames: Record<UserRole, string> = {
    admin: 'Administrator',
    teacher: 'Teacher',
    student: 'Student',
    parent: 'Parent',
  };

  return displayNames[role] || role;
}

/**
 * Validate and normalize role
 */
export function normalizeRole(role: string | undefined | null): UserRole {
  const lowerRole = role?.toLowerCase();

  if (lowerRole && ['admin', 'teacher', 'student', 'parent'].includes(lowerRole)) {
    return lowerRole as UserRole;
  }

  return 'student';
}

/**
 * Check if role requires COPPA consent (for students under 13)
 */
export function requiresCOPPAConsent(role: UserRole): boolean {
  return role === 'student';
}

/**
 * Get onboarding route for role
 */
export function getOnboardingRoute(role: UserRole): string {
  const onboardingRoutes: Record<UserRole, string> = {
    admin: '/admin/setup',
    teacher: '/teacher/onboarding',
    student: '/student/welcome',
    parent: '/parent/setup',
  };

  return onboardingRoutes[role] || '/';
}

