import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { ReactNode } from 'react';
import {
  useApiData,
  useApiMutation,
  usePaginatedApiData,
} from '../useApiData';
import uiReducer from '../../store/slices/uiSlice';

describe('useApiData', () => {
  let store: ReturnType<typeof configureStore>;

  const createMockStore = () => {
    return configureStore({
      reducer: {
        ui: uiReducer,
      },
    });
  };

  const createWrapper = (testStore: typeof store) => {
    return ({ children }: { children: ReactNode }) => (
      <Provider store={testStore}>{children}</Provider>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
    store = createMockStore();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Basic Functionality', () => {
    it('should fetch data successfully', async () => {
      const mockData = { id: 1, name: 'Test' };
      const mockApiCall = vi.fn().mockResolvedValue(mockData);

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => useApiData(mockApiCall), { wrapper });

      expect(result.current.loading).toBe(true);
      expect(result.current.data).toBeNull();

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.data).toEqual(mockData);
      expect(result.current.error).toBeNull();
      expect(mockApiCall).toHaveBeenCalledTimes(1);
    });

    it('should handle API errors', async () => {
      const mockError = {
        response: { data: { detail: 'Not found' } },
      };
      const mockApiCall = vi.fn().mockRejectedValue(mockError);

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => useApiData(mockApiCall), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Not found');
      expect(result.current.data).toBeNull();
    });

    it('should handle errors without response data', async () => {
      const mockError = new Error('Network error');
      const mockApiCall = vi.fn().mockRejectedValue(mockError);

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => useApiData(mockApiCall), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Network error');
    });

    it('should handle unknown errors', async () => {
      const mockApiCall = vi.fn().mockRejectedValue({});

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => useApiData(mockApiCall), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('An unexpected error occurred');
    });
  });

  describe('Options', () => {
    it('should not show error notification when disabled', async () => {
      const mockError = new Error('Test error');
      const mockApiCall = vi.fn().mockRejectedValue(mockError);

      const wrapper = createWrapper(store);

      renderHook(
        () => useApiData(mockApiCall, { showErrorNotification: false }),
        { wrapper }
      );

      await waitFor(() => {
        const state = store.getState();
        expect(state.ui.notifications).toEqual([]);
      });
    });

    it('should use initial data', () => {
      const initialData = { id: 1, name: 'Initial' };
      const mockApiCall = vi.fn().mockResolvedValue({ id: 2, name: 'New' });

      const wrapper = createWrapper(store);

      const { result } = renderHook(
        () => useApiData(mockApiCall, { initialData }),
        { wrapper }
      );

      expect(result.current.data).toEqual(initialData);
    });

    it('should refetch when dependencies change', async () => {
      const mockApiCall = vi.fn()
        .mockResolvedValueOnce({ id: 1 })
        .mockResolvedValueOnce({ id: 2 });

      const wrapper = createWrapper(store);

      const { rerender } = renderHook(
        ({ deps }) => useApiData(mockApiCall, { dependencies: deps }),
        {
          wrapper,
          initialProps: { deps: [1] },
        }
      );

      await waitFor(() => {
        expect(mockApiCall).toHaveBeenCalledTimes(1);
      });

      rerender({ deps: [2] });

      await waitFor(() => {
        expect(mockApiCall).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Refetch', () => {
    it('should refetch data manually', async () => {
      const mockApiCall = vi.fn()
        .mockResolvedValueOnce({ id: 1 })
        .mockResolvedValueOnce({ id: 2 });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => useApiData(mockApiCall), { wrapper });

      await waitFor(() => {
        expect(result.current.data).toEqual({ id: 1 });
      });

      await act(async () => {
        await result.current.refetch();
      });

      expect(result.current.data).toEqual({ id: 2 });
      expect(mockApiCall).toHaveBeenCalledTimes(2);
    });
  });

  describe('SetData', () => {
    it('should allow manual data updates', async () => {
      const mockApiCall = vi.fn().mockResolvedValue({ id: 1 });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => useApiData(mockApiCall), { wrapper });

      await waitFor(() => {
        expect(result.current.data).toEqual({ id: 1 });
      });

      act(() => {
        result.current.setData({ id: 2 });
      });

      expect(result.current.data).toEqual({ id: 2 });
    });

    it('should allow clearing data', async () => {
      const mockApiCall = vi.fn().mockResolvedValue({ id: 1 });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => useApiData(mockApiCall), { wrapper });

      await waitFor(() => {
        expect(result.current.data).toEqual({ id: 1 });
      });

      act(() => {
        result.current.setData(null);
      });

      expect(result.current.data).toBeNull();
    });
  });
});

describe('useApiMutation', () => {
  let store: ReturnType<typeof configureStore>;

  const createMockStore = () => {
    return configureStore({
      reducer: {
        ui: uiReducer,
      },
    });
  };

  const createWrapper = (testStore: typeof store) => {
    return ({ children }: { children: ReactNode }) => (
      <Provider store={testStore}>{children}</Provider>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
    store = createMockStore();
  });

  describe('Basic Functionality', () => {
    it('should execute mutation successfully', async () => {
      const mockData = { id: 1, name: 'Created' };
      const mockMutationFn = vi.fn().mockResolvedValue(mockData);

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => useApiMutation(mockMutationFn), { wrapper });

      expect(result.current.loading).toBe(false);

      let returnedData: any;
      await act(async () => {
        returnedData = await result.current.mutate({ name: 'Test' });
      });

      expect(result.current.loading).toBe(false);
      expect(result.current.data).toEqual(mockData);
      expect(returnedData).toEqual(mockData);
      expect(result.current.error).toBeNull();
    });

    it('should handle mutation errors', async () => {
      const mockError = {
        response: { data: { detail: 'Validation failed' } },
      };
      const mockMutationFn = vi.fn().mockRejectedValue(mockError);

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => useApiMutation(mockMutationFn), { wrapper });

      await expect(async () => {
        await act(async () => {
          await result.current.mutate({ name: 'Test' });
        });
      }).rejects.toThrow();

      expect(result.current.error).toBe('Validation failed');
      expect(result.current.data).toBeNull();
    });
  });

  describe('Callbacks', () => {
    it('should call onSuccess callback', async () => {
      const mockData = { id: 1 };
      const mockMutationFn = vi.fn().mockResolvedValue(mockData);
      const onSuccess = vi.fn();

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => useApiMutation(mockMutationFn), { wrapper });

      await act(async () => {
        await result.current.mutate({ name: 'Test' }, { onSuccess });
      });

      expect(onSuccess).toHaveBeenCalledWith(mockData);
    });

    it('should call onError callback', async () => {
      const mockError = new Error('Mutation failed');
      const mockMutationFn = vi.fn().mockRejectedValue(mockError);
      const onError = vi.fn();

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => useApiMutation(mockMutationFn), { wrapper });

      await expect(async () => {
        await act(async () => {
          await result.current.mutate({ name: 'Test' }, { onError });
        });
      }).rejects.toThrow();

      expect(onError).toHaveBeenCalledWith('Mutation failed');
    });
  });

  describe('Notifications', () => {
    it('should show success notification by default', async () => {
      const mockMutationFn = vi.fn().mockResolvedValue({});

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => useApiMutation(mockMutationFn), { wrapper });

      await act(async () => {
        await result.current.mutate({});
      });

      const state = store.getState();
      expect(state.ui.notifications.length).toBeGreaterThan(0);
      expect(state.ui.notifications[0].type).toBe('success');
    });

    it('should allow custom success message', async () => {
      const mockMutationFn = vi.fn().mockResolvedValue({});

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => useApiMutation(mockMutationFn), { wrapper });

      await act(async () => {
        await result.current.mutate(
          {},
          { successMessage: 'Custom success message' }
        );
      });

      const state = store.getState();
      expect(state.ui.notifications[0].message).toBe('Custom success message');
    });

    it('should disable notifications when requested', async () => {
      const mockMutationFn = vi.fn().mockResolvedValue({});

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => useApiMutation(mockMutationFn), { wrapper });

      await act(async () => {
        await result.current.mutate(
          {},
          { showSuccessNotification: false, showErrorNotification: false }
        );
      });

      const state = store.getState();
      expect(state.ui.notifications).toEqual([]);
    });
  });

  describe('Reset', () => {
    it('should reset mutation state', async () => {
      const mockMutationFn = vi.fn().mockResolvedValue({ id: 1 });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => useApiMutation(mockMutationFn), { wrapper });

      await act(async () => {
        await result.current.mutate({});
      });

      expect(result.current.data).toEqual({ id: 1 });

      act(() => {
        result.current.reset();
      });

      expect(result.current.data).toBeNull();
      expect(result.current.error).toBeNull();
      expect(result.current.loading).toBe(false);
    });
  });
});

describe('usePaginatedApiData', () => {
  let store: ReturnType<typeof configureStore>;

  const createMockStore = () => {
    return configureStore({
      reducer: {
        ui: uiReducer,
      },
    });
  };

  const createWrapper = (testStore: typeof store) => {
    return ({ children }: { children: ReactNode }) => (
      <Provider store={testStore}>{children}</Provider>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
    store = createMockStore();
  });

  describe('Basic Functionality', () => {
    it('should fetch first page on mount', async () => {
      const mockApiCall = vi.fn().mockResolvedValue({
        items: [{ id: 1 }, { id: 2 }],
        total: 100,
      });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => usePaginatedApiData(mockApiCall, 20), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.items).toEqual([{ id: 1 }, { id: 2 }]);
      expect(result.current.total).toBe(100);
      expect(result.current.page).toBe(1);
      expect(result.current.totalPages).toBe(5);
      expect(mockApiCall).toHaveBeenCalledWith(1, 20);
    });

    it('should calculate pagination correctly', async () => {
      const mockApiCall = vi.fn().mockResolvedValue({
        items: [],
        total: 47,
      });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => usePaginatedApiData(mockApiCall, 10), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.totalPages).toBe(5);
      expect(result.current.hasNextPage).toBe(true);
      expect(result.current.hasPrevPage).toBe(false);
    });
  });

  describe('Navigation', () => {
    it('should navigate to next page', async () => {
      const mockApiCall = vi.fn()
        .mockResolvedValueOnce({ items: [{ id: 1 }], total: 100 })
        .mockResolvedValueOnce({ items: [{ id: 2 }], total: 100 });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => usePaginatedApiData(mockApiCall, 20), { wrapper });

      await waitFor(() => {
        expect(result.current.page).toBe(1);
      });

      act(() => {
        result.current.nextPage();
      });

      await waitFor(() => {
        expect(result.current.page).toBe(2);
      });

      expect(mockApiCall).toHaveBeenCalledWith(2, 20);
    });

    it('should navigate to previous page', async () => {
      const mockApiCall = vi.fn()
        .mockResolvedValueOnce({ items: [{ id: 1 }], total: 100 })
        .mockResolvedValueOnce({ items: [{ id: 2 }], total: 100 })
        .mockResolvedValueOnce({ items: [{ id: 1 }], total: 100 });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => usePaginatedApiData(mockApiCall, 20), { wrapper });

      await waitFor(() => {
        expect(result.current.page).toBe(1);
      });

      act(() => {
        result.current.nextPage();
      });

      await waitFor(() => {
        expect(result.current.page).toBe(2);
      });

      act(() => {
        result.current.prevPage();
      });

      await waitFor(() => {
        expect(result.current.page).toBe(1);
      });
    });

    it('should go to specific page', async () => {
      const mockApiCall = vi.fn()
        .mockResolvedValueOnce({ items: [{ id: 1 }], total: 100 })
        .mockResolvedValueOnce({ items: [{ id: 3 }], total: 100 });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => usePaginatedApiData(mockApiCall, 20), { wrapper });

      await waitFor(() => {
        expect(result.current.page).toBe(1);
      });

      act(() => {
        result.current.goToPage(3);
      });

      await waitFor(() => {
        expect(result.current.page).toBe(3);
      });

      expect(mockApiCall).toHaveBeenCalledWith(3, 20);
    });

    it('should not navigate beyond bounds', async () => {
      const mockApiCall = vi.fn().mockResolvedValue({
        items: [{ id: 1 }],
        total: 20,
      });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => usePaginatedApiData(mockApiCall, 20), { wrapper });

      await waitFor(() => {
        expect(result.current.page).toBe(1);
      });

      act(() => {
        result.current.goToPage(10); // Beyond max page
      });

      // Should stay on page 1
      expect(result.current.page).toBe(1);

      act(() => {
        result.current.goToPage(0); // Below min page
      });

      expect(result.current.page).toBe(1);
    });
  });

  describe('Refresh', () => {
    it('should refresh current page', async () => {
      const mockApiCall = vi.fn()
        .mockResolvedValueOnce({ items: [{ id: 1 }], total: 100 })
        .mockResolvedValueOnce({ items: [{ id: 2 }], total: 100 });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => usePaginatedApiData(mockApiCall, 20), { wrapper });

      await waitFor(() => {
        expect(result.current.items).toEqual([{ id: 1 }]);
      });

      act(() => {
        result.current.refresh();
      });

      await waitFor(() => {
        expect(result.current.items).toEqual([{ id: 2 }]);
      });

      expect(mockApiCall).toHaveBeenCalledTimes(2);
      expect(result.current.page).toBe(1);
    });
  });

  describe('Error Handling', () => {
    it('should handle pagination errors', async () => {
      const mockApiCall = vi.fn().mockRejectedValue({
        response: { data: { detail: 'Page not found' } },
      });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => usePaginatedApiData(mockApiCall, 20), { wrapper });

      await waitFor(() => {
        expect(result.current.error).toBe('Page not found');
      });
    });
  });
});
