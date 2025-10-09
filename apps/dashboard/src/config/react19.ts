import React from 'react';

// React 19 Feature Configuration
export const REACT_19_FEATURES = {
  // Enable React 19 Actions API
  useActions: true,

  // Enable improved Suspense features
  useSuspenseList: true,

  // Enable concurrent features by default
  concurrentFeatures: {
    useTransition: true,
    useDeferredValue: true,
    useId: true,
  },

  // Server Components configuration
  serverComponents: {
    enabled: false, // Enable when ready
    apiRoute: '/rsc',
  },

  // Improved error handling
  errorBoundaryFallback: true,

  // Asset loading optimization
  assetLoading: {
    prefetch: true,
    preload: true,
  },
};

// React 19 Actions API helper
export function useAction<T extends (...args: any[]) => any>(
  action: T,
  onSuccess?: (result: Awaited<ReturnType<T>>) => void,
  onError?: (error: Error) => void
) {
  const [isPending, setIsPending] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);

  const execute = React.useCallback(
    async (...args: Parameters<T>) => {
      setIsPending(true);
      setError(null);
      try {
        const result = await action(...args);
        onSuccess?.(result);
        return result;
      } catch (err) {
        const error = err as Error;
        setError(error);
        onError?.(error);
        throw error;
      } finally {
        setIsPending(false);
      }
    },
    [action, onSuccess, onError]
  );

  return {
    execute,
    isPending,
    error,
  };
}

// React 19 optimistic updates
export function useOptimistic<T>(
  initialValue: T,
  updateFn: (currentState: T, optimisticValue: any) => T
) {
  const [value, setValue] = React.useState(initialValue);
  const [isPending, setIsPending] = React.useState(false);

  const updateOptimistically = React.useCallback(
    (optimisticValue: any) => {
      setIsPending(true);
      setValue(current => updateFn(current, optimisticValue));
    },
    [updateFn]
  );

  return [value, updateOptimistically, isPending] as const;
}

// Export for use in components
export default REACT_19_FEATURES;
