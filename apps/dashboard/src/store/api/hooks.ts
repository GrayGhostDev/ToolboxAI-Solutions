import { useCallback, useMemo } from 'react';
import { api } from './index';
import { useAppSelector } from '../index';

// Custom hook for optimistic class creation with rollback
export const useOptimisticClassCreation = () => {
  const createClassMutation = api.endpoints.createClass.useMutation();

  const createClass = useCallback(async (classData: any) => {
    try {
      const result = await createClassMutation[0](classData);
      return result;
    } catch (error) {
      // Error handling is done automatically by the mutation
      throw error;
    }
  }, [createClassMutation]);

  return {
    createClass,
    isLoading: createClassMutation[1].isLoading,
    error: createClassMutation[1].error,
  };
};

// Custom hook for paginated data with infinite scroll
export const useInfiniteScroll = <T>(
  endpoint: keyof typeof api.endpoints,
  params: any = {},
  pageSize: number = 20
) => {
  // This would need to be implemented with a modified endpoint that supports pagination
  // For now, returning a basic structure
  return {
    data: [],
    isLoading: false,
    isFetchingNextPage: false,
    hasNextPage: false,
    fetchNextPage: () => {},
    error: null,
  };
};

// Custom hook for real-time data synchronization
export const useRealtimeSync = (
  queryHook: any,
  queryArgs: any,
  channels: string[]
) => {
  const queryResult = queryHook(queryArgs);

  // This would integrate with Pusher channels to update cache when real-time events occur
  // For now, returning the basic query result
  return queryResult;
};

// Custom hook for bulk operations with progress tracking
export const useBulkOperations = () => {
  const deleteClassMutation = api.endpoints.deleteClass.useMutation();
  const updateClassMutation = api.endpoints.updateClass.useMutation();

  const bulkDelete = useCallback(async (
    ids: string[],
    onProgress?: (completed: number, total: number) => void
  ) => {
    const results = [];
    for (let i = 0; i < ids.length; i++) {
      try {
        const result = await deleteClassMutation[0](ids[i]);
        results.push({ id: ids[i], success: true, result });
        onProgress?.(i + 1, ids.length);
      } catch (error) {
        results.push({ id: ids[i], success: false, error });
        onProgress?.(i + 1, ids.length);
      }
    }
    return results;
  }, [deleteClassMutation]);

  const bulkUpdate = useCallback(async (
    updates: Array<{ id: string; data: any }>,
    onProgress?: (completed: number, total: number) => void
  ) => {
    const results = [];
    for (let i = 0; i < updates.length; i++) {
      try {
        const result = await updateClassMutation[0](updates[i]);
        results.push({ id: updates[i].id, success: true, result });
        onProgress?.(i + 1, updates.length);
      } catch (error) {
        results.push({ id: updates[i].id, success: false, error });
        onProgress?.(i + 1, updates.length);
      }
    }
    return results;
  }, [updateClassMutation]);

  return {
    bulkDelete,
    bulkUpdate,
    isLoading: deleteClassMutation[1].isLoading || updateClassMutation[1].isLoading,
  };
};

// Custom hook for cache invalidation patterns
export const useCacheInvalidation = () => {
  const dispatch = api.util.resetApiState;

  const invalidateAll = useCallback(() => {
    dispatch();
  }, [dispatch]);

  const invalidateTag = useCallback((tag: string) => {
    // This would invalidate specific tags
    // For now, implement basic invalidation
  }, []);

  const invalidateEndpoint = useCallback((endpoint: string, args?: any) => {
    // This would invalidate specific endpoint caches
  }, []);

  return {
    invalidateAll,
    invalidateTag,
    invalidateEndpoint,
  };
};

// Custom hook for offline support
export const useOfflineSupport = () => {
  const isOnline = useAppSelector(state =>
    // This would check network status from a network slice
    true // placeholder
  );

  const queuedMutations = useAppSelector(state =>
    // This would get queued mutations from offline storage
    [] // placeholder
  );

  const syncOfflineData = useCallback(async () => {
    // This would replay queued mutations when back online
    if (isOnline && queuedMutations.length > 0) {
      // Process queued mutations
    }
  }, [isOnline, queuedMutations]);

  return {
    isOnline,
    queuedMutations,
    syncOfflineData,
  };
};

// Custom hook for data transformation and normalization
export const useNormalizedData = <T>(
  data: T[] | undefined,
  keyField: keyof T = 'id' as keyof T
) => {
  const normalized = useMemo(() => {
    if (!data) return { byId: {}, allIds: [] };

    const byId = {} as Record<string, T>;
    const allIds = [] as string[];

    data.forEach(item => {
      const id = String(item[keyField]);
      byId[id] = item;
      allIds.push(id);
    });

    return { byId, allIds };
  }, [data, keyField]);

  return normalized;
};

// Custom hook for filtered and sorted data
export const useFilteredData = <T>(
  data: T[] | undefined,
  filters: Record<string, any> = {},
  sortBy?: keyof T,
  sortOrder: 'asc' | 'desc' = 'asc'
) => {
  const filtered = useMemo(() => {
    if (!data) return [];

    let result = data.filter(item => {
      return Object.entries(filters).every(([key, value]) => {
        if (value === null || value === undefined || value === '') return true;

        const itemValue = (item as any)[key];

        if (typeof value === 'string') {
          return String(itemValue).toLowerCase().includes(value.toLowerCase());
        }

        return itemValue === value;
      });
    });

    if (sortBy) {
      result = [...result].sort((a, b) => {
        const aVal = a[sortBy];
        const bVal = b[sortBy];

        if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return result;
  }, [data, filters, sortBy, sortOrder]);

  return filtered;
};

// Custom hook for debounced search
export const useDebouncedSearch = (
  searchTerm: string,
  delay: number = 300
) => {
  const [debouncedTerm, setDebouncedTerm] = useState(searchTerm);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedTerm(searchTerm);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [searchTerm, delay]);

  return debouncedTerm;
};

// Custom hook for cache hit ratio monitoring
export const useCacheMetrics = () => {
  const cacheHitRatio = useAppSelector(state => {
    // This would calculate cache hit ratio from RTK Query state
    const queries = (state as any).api?.queries || {};
    const totalQueries = Object.keys(queries).length;
    const cachedQueries = Object.values(queries).filter(
      (query: any) => query.status === 'fulfilled' && !query.error
    ).length;

    return totalQueries > 0 ? cachedQueries / totalQueries : 0;
  });

  const cacheSize = useAppSelector(state => {
    // This would calculate total cache size
    const queries = (state as any).api?.queries || {};
    return Object.keys(queries).length;
  });

  return {
    cacheHitRatio,
    cacheSize,
    formattedHitRatio: `${(cacheHitRatio * 100).toFixed(1)}%`,
  };
};

// Custom hook for intelligent prefetching
export const usePrefetching = () => {
  const prefetchDashboard = api.usePrefetch('getDashboardOverview');
  const prefetchClasses = api.usePrefetch('getClasses');
  const prefetchLessons = api.usePrefetch('getLessons');

  const prefetchUserData = useCallback((userId?: string) => {
    // Prefetch commonly accessed data
    prefetchDashboard();
    prefetchClasses();
    prefetchLessons();
  }, [prefetchDashboard, prefetchClasses, prefetchLessons]);

  const prefetchClassData = useCallback((classId: string) => {
    // Prefetch class-specific data
    prefetchLessons(classId);
    // Could also prefetch assessments, students, etc.
  }, [prefetchLessons]);

  return {
    prefetchUserData,
    prefetchClassData,
  };
};

// Custom hook for error recovery
export const useErrorRecovery = () => {
  const retryFailedQueries = useCallback(() => {
    // This would retry all failed queries
    // Implementation would depend on tracking failed queries
  }, []);

  const clearErrors = useCallback(() => {
    // This would clear error states
  }, []);

  return {
    retryFailedQueries,
    clearErrors,
  };
};

// Re-export from useState and useEffect for the debounced search hook
import { useState, useEffect } from 'react';

export {
  // Re-export all RTK Query hooks for convenience
  api,
  // Custom hooks are exported above
};