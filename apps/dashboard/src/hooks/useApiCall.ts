/**
 * useApiCall Hook
 *
 * A centralized hook for making API calls with automatic mock data support,
 * loading states, and error handling.
 */

import { useState, useCallback, useEffect } from 'react';
import { AxiosError, AxiosResponse } from 'axios';
import { useAppDispatch } from '../store';
import { addNotification } from '../store/slices/uiSlice';
import { isBypassMode } from '../utils/axios-config';
import { logger } from '../utils/logger';
import {
  mockAssessments,
  mockMessages,
  mockReports,
  mockSettings,
  mockStudentData,
  mockSchools,
  mockUsers,
  mockDashboardOverview,
  mockAnalytics,
  mockGamification,
  mockComplianceStatus,
  mockUnreadMessages,
  mockClasses,
  mockLessons,
  mockDelay,
  mockSubscription,
  mockPaymentMethods,
  mockInvoices,
  mockBillingPlans
} from '../services/mock-data';

interface ApiCallState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseApiCallOptions {
  showNotification?: boolean;
  autoRetry?: boolean;
  retryDelay?: number;
  mockEndpoint?: string;
}

/**
 * Custom hook for making API calls with automatic state management
 * @param apiFunction - The API function to call (optional, can be provided later to execute)
 * @param options - Configuration options
 * @returns Object with execute function, data, loading, and error states
 */
export function useApiCall<T = any, P extends any[] = any[]>(
  apiFunction?: (...args: P) => Promise<AxiosResponse<T>>,
  options: UseApiCallOptions = {}
) {
  const [state, setState] = useState<ApiCallState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const dispatch = useAppDispatch();
  const { showNotification = false, autoRetry = false, retryDelay = 1000, mockEndpoint } = options;

  // Mock data mapping
  const getMockData = useCallback(async (endpoint?: string): Promise<T | null> => {
    if (!isBypassMode() || !endpoint) return null;

    await mockDelay();

    // Map endpoints to mock data
    const mockMap: Record<string, any> = {
      '/assessments': mockAssessments,
      '/messages': mockMessages,
      '/reports': mockReports,
      '/settings': mockSettings,
      '/student': mockStudentData,
      '/schools': mockSchools,
      '/users': mockUsers,
      '/dashboard/overview': mockDashboardOverview,
      '/analytics/weekly_xp': mockAnalytics.weeklyXP,
      '/analytics/subject_mastery': mockAnalytics.subjectMastery,
      '/gamification/leaderboard': mockGamification,
      '/compliance/status': mockComplianceStatus,
      '/messages/unread-count': mockUnreadMessages,
      '/classes': mockClasses,
      '/lessons': mockLessons,
      // Billing endpoints
      '/billing/subscription': mockSubscription,
      '/billing/payment-methods': mockPaymentMethods,
      '/billing/invoices': mockInvoices,
      '/billing/plans': mockBillingPlans,
    };

    // Find matching mock data
    for (const [pattern, data] of Object.entries(mockMap)) {
      if (endpoint.includes(pattern)) {
        return data as T;
      }
    }

    return null;
  }, []);

  const execute = useCallback(
    async (...args: P) => {
      // Validate apiFunction exists
      if (!apiFunction) {
        const errorMessage = 'No API function provided to useApiCall';
        logger.error(errorMessage);
        setState({ data: null, loading: false, error: errorMessage });

        if (showNotification) {
          dispatch(
            addNotification({
              message: errorMessage,
              type: 'error',
            })
          );
        }

        throw new TypeError(errorMessage);
      }

      setState((prev) => ({ ...prev, loading: true, error: null }));

      try {
        // Check for mock data in bypass mode
        if (isBypassMode() && mockEndpoint) {
          const mockData = await getMockData(mockEndpoint);
          if (mockData) {
            setState({ data: mockData, loading: false, error: null });

            if (showNotification) {
              dispatch(
                addNotification({
                  message: 'Data loaded successfully (mock mode)',
                  type: 'info',
                })
              );
            }

            return { data: mockData } as AxiosResponse<T>;
          }
        }

        // Make actual API call
        const response = await apiFunction(...args);
        setState({ data: response.data, loading: false, error: null });

        if (showNotification) {
          dispatch(
            addNotification({
              message: 'Request completed successfully',
              type: 'success',
            })
          );
        }

        return response;
      } catch (err) {
        const error = err as AxiosError;
        const errorMessage =
          (error.response?.data as { message?: string })?.message ||
          error.message ||
          'An error occurred';

        logger.error('API call failed:', errorMessage);
        setState({ data: null, loading: false, error: errorMessage });

        // Auto-retry logic
        if (autoRetry && !error.response) {
          setTimeout(() => {
            execute(...args);
          }, retryDelay);
        }

        if (showNotification) {
          dispatch(
            addNotification({
              message: errorMessage,
              type: 'error',
            })
          );
        }

        throw error;
      }
    },
    [apiFunction, dispatch, showNotification, autoRetry, retryDelay, mockEndpoint, getMockData]
  );

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    execute,
    reset,
    isSuccess: !state.loading && !state.error && state.data !== null,
    isError: !state.loading && state.error !== null,
  };
}

/**
 * Hook for API calls that should execute immediately on mount
 */
export function useApiCallOnMount<T = any>(
  apiFunction?: () => Promise<AxiosResponse<T>>,
  options: UseApiCallOptions = {}
) {
  const api = useApiCall(apiFunction, options);

  useEffect(() => {
    if (apiFunction) {
      api.execute();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return api;
}

/**
 * Hook for paginated API calls
 */
export function usePaginatedApiCall<T = any>(
  apiFunction: (page: number, pageSize: number) => Promise<AxiosResponse<T>>,
  initialPage = 1,
  initialPageSize = 10,
  options: UseApiCallOptions = {}
) {
  const [page, setPage] = useState(initialPage);
  const [pageSize, setPageSize] = useState(initialPageSize);

  const api = useApiCall(apiFunction, options);

  const fetchPage = useCallback(
    async (newPage?: number, newPageSize?: number) => {
      const currentPage = newPage ?? page;
      const currentPageSize = newPageSize ?? pageSize;

      if (newPage !== undefined) setPage(newPage);
      if (newPageSize !== undefined) setPageSize(newPageSize);

      return api.execute(currentPage, currentPageSize);
    },
    [api, page, pageSize]
  );

  const nextPage = useCallback(() => fetchPage(page + 1), [fetchPage, page]);
  const prevPage = useCallback(() => fetchPage(Math.max(1, page - 1)), [fetchPage, page]);
  const goToPage = useCallback((p: number) => fetchPage(p), [fetchPage]);

  return {
    ...api,
    page,
    pageSize,
    setPage,
    setPageSize,
    fetchPage,
    nextPage,
    prevPage,
    goToPage,
  };
}

/**
 * Hook for search/filter API calls with debouncing
 */
export function useSearchApiCall<T = any>(
  apiFunction: (query: string) => Promise<AxiosResponse<T>>,
  debounceMs = 300,
  options: UseApiCallOptions = {}
) {
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');

  const api = useApiCall(apiFunction, options);

  // Debounce the query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [query, debounceMs]);

  // Execute search when debounced query changes
  useEffect(() => {
    if (debouncedQuery) {
      api.execute(debouncedQuery);
    } else {
      api.reset();
    }
  }, [debouncedQuery]); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    ...api,
    query,
    setQuery,
    debouncedQuery,
  };
}