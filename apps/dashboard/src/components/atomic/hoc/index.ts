/**
 * Higher-Order Components (HOCs)
 *
 * Reusable component enhancement patterns for common functionality
 * like authentication, loading states, error boundaries, and analytics.
 */

// Authentication HOCs
export { default as withAuth } from './withAuth';
export { default as withRole } from './withRole';

// State Management HOCs
export { default as withLoading } from './withLoading';
export { default as withError } from './withError';
export { default as withAsyncData } from './withAsyncData';

// UI Enhancement HOCs
export { default as withTheme } from './withTheme';
export { default as withResponsive } from './withResponsive';
export { default as withAnimations } from './withAnimations';

// Performance HOCs
export { default as withLazyLoading } from './withLazyLoading';
export { default as withMemoization } from './withMemoization';
export { default as withVirtualization } from './withVirtualization';

// Analytics HOCs
export { default as withTracking } from './withTracking';
export { default as withPerformanceMonitoring } from './withPerformanceMonitoring';

// Gaming/Roblox HOCs
export { default as withGameState } from './withGameState';
export { default as withPlayerData } from './withPlayerData';
export { default as withAchievements } from './withAchievements';

// Utility HOCs
export { default as withErrorBoundary } from './withErrorBoundary';
export { default as withPortal } from './withPortal';
export { default as withClickOutside } from './withClickOutside';

// Type exports
export type { WithAuthProps } from './withAuth';
export type { WithRoleProps } from './withRole';
export type { WithLoadingProps } from './withLoading';
export type { WithErrorProps } from './withError';
export type { WithAsyncDataProps } from './withAsyncData';
export type { WithThemeProps } from './withTheme';
export type { WithResponsiveProps } from './withResponsive';
export type { WithAnimationsProps } from './withAnimations';
export type { WithLazyLoadingProps } from './withLazyLoading';
export type { WithMemoizationProps } from './withMemoization';
export type { WithVirtualizationProps } from './withVirtualization';
export type { WithTrackingProps } from './withTracking';
export type { WithPerformanceMonitoringProps } from './withPerformanceMonitoring';
export type { WithGameStateProps } from './withGameState';
export type { WithPlayerDataProps } from './withPlayerData';
export type { WithAchievementsProps } from './withAchievements';
export type { WithErrorBoundaryProps } from './withErrorBoundary';
export type { WithPortalProps } from './withPortal';
export type { WithClickOutsideProps } from './withClickOutside';

// Grouped exports for convenience
export const authHOCs = {
  withAuth,
  withRole
};

export const stateHOCs = {
  withLoading,
  withError,
  withAsyncData
};

export const uiHOCs = {
  withTheme,
  withResponsive,
  withAnimations
};

export const performanceHOCs = {
  withLazyLoading,
  withMemoization,
  withVirtualization
};

export const analyticsHOCs = {
  withTracking,
  withPerformanceMonitoring
};

export const gamingHOCs = {
  withGameState,
  withPlayerData,
  withAchievements
};

export const utilityHOCs = {
  withErrorBoundary,
  withPortal,
  withClickOutside
};