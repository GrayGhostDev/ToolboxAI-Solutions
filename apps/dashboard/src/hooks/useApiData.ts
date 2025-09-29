import { useState, useEffect, useCallback } from 'react';
import { useAppDispatch } from '../store';
import { addNotification } from '../store/slices/uiSlice';

interface UseApiDataOptions {
  showErrorNotification?: boolean;
  dependencies?: any[];
  initialData?: any;
}

interface UseApiDataReturn<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  setData: (data: T | null) => void;
}

/**
 * Custom hook for handling API calls with loading, error, and data states
 * @param apiCall - Function that returns a Promise with the API data
 * @param options - Configuration options for the hook
 * @returns Object with data, loading, error states and refetch function
 */
export function useApiData<T>(
  apiCall: () => Promise<T>,
  options: UseApiDataOptions = {}
): UseApiDataReturn<T> {
  const {
    showErrorNotification = true,
    dependencies = [],
    initialData = null
  } = options;

  const dispatch = useAppDispatch();
  const [data, setData] = useState<T | null>(initialData);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!apiCall) return;

    try {
      setLoading(true);
      setError(null);
      const result = await apiCall();
      setData(result);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 
                          err.message || 
                          'An unexpected error occurred';
      setError(errorMessage);
      
      if (showErrorNotification) {
        dispatch(
          addNotification({
            type: 'error',
            message: errorMessage,
          })
        );
      }
      
      console.error('API call failed:', err);
    } finally {
      setLoading(false);
    }
  }, [apiCall, dispatch, showErrorNotification]);

  useEffect(() => {
    fetchData();
  }, [...dependencies]);

  const refetch = useCallback(async () => {
    await fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    refetch,
    setData
  };
}

/**
 * Custom hook for handling API mutations (POST, PUT, DELETE)
 * @param mutationFn - Function that performs the mutation
 * @returns Object with mutation function, loading, error, and success states
 */
export function useApiMutation<TData = any, TVariables = any>(
  mutationFn: (variables: TVariables) => Promise<TData>
) {
  const dispatch = useAppDispatch();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<TData | null>(null);

  const mutate = useCallback(async (
    variables: TVariables,
    options?: {
      onSuccess?: (data: TData) => void;
      onError?: (error: string) => void;
      showSuccessNotification?: boolean;
      successMessage?: string;
      showErrorNotification?: boolean;
    }
  ) => {
    const {
      onSuccess,
      onError,
      showSuccessNotification = true,
      successMessage = 'Operation completed successfully',
      showErrorNotification = true
    } = options || {};

    try {
      setLoading(true);
      setError(null);
      const result = await mutationFn(variables);
      setData(result);

      if (showSuccessNotification) {
        dispatch(
          addNotification({
            type: 'success',
            message: successMessage,
          })
        );
      }

      if (onSuccess) {
        onSuccess(result);
      }

      return result;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 
                          err.message || 
                          'Operation failed';
      setError(errorMessage);

      if (showErrorNotification) {
        dispatch(
          addNotification({
            type: 'error',
            message: errorMessage,
          })
        );
      }

      if (onError) {
        onError(errorMessage);
      }

      throw err;
    } finally {
      setLoading(false);
    }
  }, [mutationFn, dispatch]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return {
    mutate,
    loading,
    error,
    data,
    reset
  };
}

/**
 * Custom hook for handling paginated API data
 */
export function usePaginatedApiData<T>(
  apiCall: (page: number, pageSize: number) => Promise<{ items: T[]; total: number }>,
  pageSize: number = 20
) {
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<T[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const dispatch = useAppDispatch();

  const fetchPage = useCallback(async (pageNumber: number) => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiCall(pageNumber, pageSize);
      setItems(result.items);
      setTotal(result.total);
      setPage(pageNumber);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to load data';
      setError(errorMessage);
      dispatch(
        addNotification({
          type: 'error',
          message: errorMessage,
        })
      );
    } finally {
      setLoading(false);
    }
  }, [apiCall, pageSize, dispatch]);

  useEffect(() => {
    fetchPage(1);
  }, []);

  const goToPage = (pageNumber: number) => {
    if (pageNumber < 1 || pageNumber > Math.ceil(total / pageSize)) return;
    fetchPage(pageNumber);
  };

  const nextPage = () => goToPage(page + 1);
  const prevPage = () => goToPage(page - 1);
  const refresh = () => fetchPage(page);

  return {
    items,
    total,
    page,
    pageSize,
    loading,
    error,
    totalPages: Math.ceil(total / pageSize),
    hasNextPage: page < Math.ceil(total / pageSize),
    hasPrevPage: page > 1,
    goToPage,
    nextPage,
    prevPage,
    refresh
  };
}