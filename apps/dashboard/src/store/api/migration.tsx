/**
 * Migration utilities for transitioning from Redux slices to RTK Query
 *
 * This file provides compatibility layers and migration helpers to gradually
 * transition components from using traditional Redux slices to RTK Query
 * without breaking existing functionality.
 */

import React, { useCallback, useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../index';
import { api } from './index';
import {
  setClasses,
  setLoading as setClassesLoading,
  setError as setClassesError,
} from '../slices/classesSlice';
import {
  setMetrics,
  setLoading as setDashboardLoading,
  setError as setDashboardError,
} from '../slices/dashboardSlice';

// Migration hook for Dashboard slice
export const useDashboardMigration = () => {
  const dispatch = useAppDispatch();

  // RTK Query hook
  const {
    data: dashboardData,
    isLoading,
    error,
    refetch,
  } = api.useGetDashboardOverviewQuery();

  // Legacy slice state
  const legacyState = useAppSelector(state => state.dashboard);

  // Sync RTK Query data to legacy slice for backward compatibility
  useEffect(() => {
    if (dashboardData) {
      dispatch(setMetrics(dashboardData));
    }
  }, [dashboardData, dispatch]);

  useEffect(() => {
    dispatch(setDashboardLoading(isLoading));
  }, [isLoading, dispatch]);

  useEffect(() => {
    if (error) {
      dispatch(setDashboardError(error.toString()));
    } else {
      dispatch(setDashboardError(null));
    }
  }, [error, dispatch]);

  // Return both new and legacy interfaces
  return {
    // RTK Query interface (recommended for new code)
    rtk: {
      data: dashboardData,
      isLoading,
      error,
      refetch,
    },
    // Legacy interface (for existing components)
    legacy: {
      metrics: legacyState.metrics,
      loading: legacyState.loading,
      error: legacyState.error,
      recentActivity: legacyState.recentActivity,
      upcomingEvents: legacyState.upcomingEvents,
      lastUpdated: legacyState.lastUpdated,
    },
    // Helper to check if component should use RTK Query data
    useRtkData: Boolean(dashboardData),
  };
};

// Migration hook for Classes slice
export const useClassesMigration = () => {
  const dispatch = useAppDispatch();

  // RTK Query hooks
  const {
    data: classesData,
    isLoading,
    error,
    refetch,
  } = api.useGetClassesQuery();

  const [createClass] = api.useCreateClassMutation();
  const [updateClass] = api.useUpdateClassMutation();
  const [deleteClass] = api.useDeleteClassMutation();

  // Legacy slice state
  const legacyState = useAppSelector(state => state.classes);

  // Sync RTK Query data to legacy slice
  useEffect(() => {
    if (classesData) {
      dispatch(setClasses(classesData as any));
    }
  }, [classesData, dispatch]);

  useEffect(() => {
    dispatch(setClassesLoading(isLoading));
  }, [isLoading, dispatch]);

  useEffect(() => {
    if (error) {
      dispatch(setClassesError(error.toString()));
    } else {
      dispatch(setClassesError(null));
    }
  }, [error, dispatch]);

  // Legacy-compatible mutation wrappers
  const legacyCreateClass = useCallback(async (classData: any) => {
    try {
      const result = await createClass(classData).unwrap();
      return result;
    } catch (error) {
      throw error;
    }
  }, [createClass]);

  const legacyUpdateClass = useCallback(async (id: string, data: any) => {
    try {
      const result = await updateClass({ id, data }).unwrap();
      return result;
    } catch (error) {
      throw error;
    }
  }, [updateClass]);

  const legacyDeleteClass = useCallback(async (id: string) => {
    try {
      await deleteClass(id).unwrap();
    } catch (error) {
      throw error;
    }
  }, [deleteClass]);

  return {
    // RTK Query interface
    rtk: {
      data: classesData,
      isLoading,
      error,
      refetch,
      createClass,
      updateClass,
      deleteClass,
    },
    // Legacy interface
    legacy: {
      list: legacyState.list,
      selectedClass: legacyState.selectedClass,
      loading: legacyState.loading,
      error: legacyState.error,
      lastFetch: legacyState.lastFetch,
      // Legacy-compatible mutation functions
      createClass: legacyCreateClass,
      updateClass: legacyUpdateClass,
      deleteClass: legacyDeleteClass,
    },
    useRtkData: Boolean(classesData),
  };
};

// Higher-order component for migrating components gradually
export const withRtkQueryMigration = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  migrationConfig: {
    useRtkQuery?: boolean;
    fallbackToLegacy?: boolean;
    debugMode?: boolean;
  } = {}
): React.ComponentType<P> => {
  const {
    useRtkQuery = true,
    fallbackToLegacy = true,
    debugMode = false,
  } = migrationConfig;

  return (props: P) => {
    if (debugMode) {
      console.log(`Migration HOC: useRtkQuery=${useRtkQuery}, fallbackToLegacy=${fallbackToLegacy}`);
    }

    // This would inject RTK Query hooks or legacy slice data
    // based on configuration
    return <WrappedComponent {...props} />;
  };
};

// Hook to gradually migrate from legacy API calls to RTK Query
export const useApiMigration = () => {
  const dispatch = useAppDispatch();

  // Check if RTK Query is available and working
  const isRtkQueryReady = useAppSelector(state => {
    const apiState = (state as any).api;
    return Boolean(apiState && Object.keys(apiState.queries || {}).length > 0);
  });

  // Migration strategy selector
  const shouldUseRtkQuery = useCallback((endpoint: string) => {
    // Define which endpoints have been migrated
    const migratedEndpoints = [
      'getDashboardOverview',
      'getClasses',
      'createClass',
      'updateClass',
      'deleteClass',
      'getLessons',
      'getAssessments',
      'getMessages',
    ];

    return isRtkQueryReady && migratedEndpoints.includes(endpoint);
  }, [isRtkQueryReady]);

  // Wrapper function that decides between RTK Query and legacy API
  const apiCall = useCallback(async (
    endpoint: string,
    params?: any,
    options?: { forceRtk?: boolean; forceLegacy?: boolean }
  ) => {
    const useRtk = options?.forceRtk ||
                   (!options?.forceLegacy && shouldUseRtkQuery(endpoint));

    if (useRtk) {
      // Use RTK Query
      switch (endpoint) {
        case 'getDashboardOverview':
          return dispatch(api.endpoints.getDashboardOverview.initiate());
        case 'getClasses':
          return dispatch(api.endpoints.getClasses.initiate());
        // Add more cases as needed
        default:
          throw new Error(`RTK Query endpoint ${endpoint} not implemented`);
      }
    } else {
      // Fall back to legacy API
      const { apiClient } = await import('../../services/api');

      switch (endpoint) {
        case 'getDashboardOverview':
          return apiClient.getDashboardOverview(params?.role);
        case 'getClasses':
          return apiClient.listClasses();
        // Add more legacy cases
        default:
          throw new Error(`Legacy API endpoint ${endpoint} not implemented`);
      }
    }
  }, [dispatch, shouldUseRtkQuery]);

  return {
    apiCall,
    shouldUseRtkQuery,
    isRtkQueryReady,
    migrationStatus: {
      dashboard: shouldUseRtkQuery('getDashboardOverview'),
      classes: shouldUseRtkQuery('getClasses'),
      lessons: shouldUseRtkQuery('getLessons'),
      assessments: shouldUseRtkQuery('getAssessments'),
      messages: shouldUseRtkQuery('getMessages'),
    },
  };
};

// Hook for monitoring migration progress
export const useMigrationProgress = () => {
  const rtk = useAppSelector(state => (state as any).api);
  const legacy = useAppSelector(state => ({
    dashboard: state.dashboard,
    classes: state.classes,
    lessons: state.lessons,
    assessments: state.assessments,
    messages: state.messages,
  }));

  const progress = {
    rtkQueries: Object.keys(rtk?.queries || {}).length,
    rtkMutations: Object.keys(rtk?.mutations || {}).length,
    legacySlicesActive: Object.values(legacy).filter(slice =>
      slice && typeof slice === 'object' && 'loading' in slice
    ).length,
    cacheHitRatio: rtk?.queries ?
      Object.values(rtk.queries).filter((q: any) => q.status === 'fulfilled').length /
      Object.keys(rtk.queries).length * 100 : 0,
  };

  return {
    ...progress,
    migrationComplete: progress.rtkQueries > 5 && progress.legacySlicesActive === 0,
    cacheEfficiency: progress.cacheHitRatio > 70 ? 'excellent' :
                    progress.cacheHitRatio > 50 ? 'good' : 'needs improvement',
  };
};

// Performance comparison between RTK Query and legacy approaches
export const usePerformanceComparison = () => {
  const startTime = Date.now();

  const rtkMetrics = useAppSelector(state => {
    const api = (state as any).api;
    if (!api) return null;

    const queries = Object.values(api.queries || {});
    const totalResponseTime = queries.reduce((sum: number, query: any) => {
      if (query.startedTimeStamp && query.fulfilledTimeStamp) {
        return sum + (query.fulfilledTimeStamp - query.startedTimeStamp);
      }
      return sum;
    }, 0);

    return {
      totalQueries: queries.length,
      averageResponseTime: queries.length > 0 ? totalResponseTime / queries.length : 0,
      cacheHits: queries.filter((q: any) => q.status === 'fulfilled').length,
      errors: queries.filter((q: any) => q.status === 'rejected').length,
    };
  });

  const legacyMetrics = {
    // These would be tracked manually in legacy implementation
    totalRequests: 0,
    averageResponseTime: 0,
    cacheHits: 0,
    errors: 0,
  };

  return {
    rtk: rtkMetrics,
    legacy: legacyMetrics,
    comparison: rtkMetrics ? {
      responseTimeImprovement: legacyMetrics.averageResponseTime > 0 ?
        ((legacyMetrics.averageResponseTime - rtkMetrics.averageResponseTime) /
         legacyMetrics.averageResponseTime * 100) : 0,
      cacheEfficiencyImprovement: rtkMetrics.totalQueries > 0 ?
        (rtkMetrics.cacheHits / rtkMetrics.totalQueries * 100) : 0,
    } : null,
  };
};

// Debugging utilities for migration
export const useMigrationDebugger = () => {
  const state = useAppSelector(state => state);

  const debugInfo = {
    rtkQueryState: (state as any).api,
    legacySlicesState: {
      dashboard: state.dashboard,
      classes: state.classes,
      lessons: state.lessons,
      assessments: state.assessments,
      messages: state.messages,
    },
    stateSize: JSON.stringify(state).length,
    timestamp: new Date().toISOString(),
  };

  const logMigrationState = useCallback(() => {
    console.group('🔄 RTK Query Migration Debug');
    console.log('Current State:', debugInfo);
    console.log('RTK Query Cache:', debugInfo.rtkQueryState?.queries);
    console.log('Legacy Slices:', debugInfo.legacySlicesState);
    console.groupEnd();
  }, [debugInfo]);

  return {
    debugInfo,
    logMigrationState,
  };
};

export default {
  useDashboardMigration,
  useClassesMigration,
  withRtkQueryMigration,
  useApiMigration,
  useMigrationProgress,
  usePerformanceComparison,
  useMigrationDebugger,
};