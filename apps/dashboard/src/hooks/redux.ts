/**
 * Redux hooks with proper TypeScript typing
 * Provides type-safe access to the Redux store
 */

import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';
import type { store } from '@/store';

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

/**
 * Use throughout your app instead of plain `useDispatch`
 * Provides type safety for dispatching actions
 */
export const useAppDispatch: () => AppDispatch = useDispatch;

/**
 * Use throughout your app instead of plain `useSelector`
 * Provides type safety for selecting state
 */
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

/**
 * Custom hook for selecting user state
 */
export const useUserState = () => useAppSelector((state) => state.user);

/**
 * Custom hook for selecting dashboard state
 */
export const useDashboardState = () => useAppSelector((state) => state.dashboard);

/**
 * Custom hook for selecting UI state
 */
export const useUIState = () => useAppSelector((state) => state.ui);

/**
 * Custom hook for selecting gamification state
 */
export const useGamificationState = () => useAppSelector((state) => state.gamification);

/**
 * Custom hook for selecting classes state
 */
export const useClassesState = () => useAppSelector((state) => state.classes);

/**
 * Custom hook for selecting realtime state
 */
export const useRealtimeState = () => useAppSelector((state) => state.realtime);

/**
 * Custom hook for admin-specific state
 */
export const useAdminState = () => {
  const user = useUserState();
  const dashboard = useDashboardState();
  const analytics = useAppSelector((state) => state.analytics);
  const compliance = useAppSelector((state) => state.compliance);

  // Only allow admin access
  const isAdmin = user?.role === 'admin';

  return {
    isAdmin,
    user,
    dashboard,
    analytics,
    compliance,
    // Add more admin-specific state here
  };
};