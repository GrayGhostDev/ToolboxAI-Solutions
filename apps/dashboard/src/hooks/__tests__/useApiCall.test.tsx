import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { ReactNode } from 'react';
import {
  useApiCall,
  useApiCallOnMount,
  usePaginatedApiCall,
  useSearchApiCall,
} from '../useApiCall';
import uiReducer from '../../store/slices/uiSlice';
import * as axiosConfig from '../../utils/axios-config';

// Mock axios-config
vi.mock('../../utils/axios-config', () => ({
  isBypassMode: vi.fn(() => false),
}));

// Mock logger
vi.mock('../../utils/logger', () => ({
  logger: {
    debug: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
  },
}));

// Mock delay
vi.mock('../../services/mock-data', () => ({
  mockDelay: vi.fn(() => Promise.resolve()),
  mockAssessments: [{ id: 1, name: 'Test Assessment' }],
  mockMessages: [{ id: 1, text: 'Test Message' }],
  mockDashboardOverview: { totalStudents: 100 },
}));

describe('useApiCall', () => {
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
    vi.mocked(axiosConfig.isBypassMode).mockReturnValue(false);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Basic Functionality', () => {
    it('should execute API call successfully', async () => {
      const mockData = { id: 1, name: 'Test' };
      const mockApiFunction = vi.fn().mockResolvedValue({ data: mockData });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => useApiCall(mockApiFunction), { wrapper });

      expect(result.current.loading).toBe(false);
      expect(result.current.data).toBeNull();

      await act(async () => {
        await result.current.execute();
      });

      expect(result.current.loading).toBe(false);
      expect(result.current.data).toEqual(mockData);
      expect(result.current.error).toBeNull();
      expect(result.current.isSuccess).toBe(true);
      expect(result.current.isError).toBe(false);
    });

    it('should handle API errors', async () => {
      const mockError = {
        response: { data: { message: 'Not found' } },
        message: 'Request failed',
      };
      const mockApiFunction = vi.fn().mockRejectedValue(mockError);

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => useApiCall(mockApiFunction), { wrapper });

      await expect(async () => {
        await act(async () => {
          await result.current.execute();
        });
      }).rejects.toThrow();

      expect(result.current.error).toBe('Not found');
      expect(result.current.data).toBeNull();
      expect(result.current.isSuccess).toBe(false);
      expect(result.current.isError).toBe(true);
    });

    it('should handle errors without response', async () => {
      const mockError = { message: 'Network error' };
      const mockApiFunction = vi.fn().mockRejectedValue(mockError);

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => useApiCall(mockApiFunction), { wrapper });

      await expect(async () => {
        await act(async () => {
          await result.current.execute();
        });
      }).rejects.toThrow();

      expect(result.current.error).toBe('Network error');
    });

    it('should pass arguments to API function', async () => {
      const mockApiFunction = vi.fn().mockResolvedValue({ data: {} });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => useApiCall(mockApiFunction), { wrapper });

      await act(async () => {
        await result.current.execute('arg1', 123, { key: 'value' });
      });

      expect(mockApiFunction).toHaveBeenCalledWith('arg1', 123, { key: 'value' });
    });
  });

  describe('Mock Data Support', () => {
    it('should use mock data in bypass mode', async () => {
      vi.mocked(axiosConfig.isBypassMode).mockReturnValue(true);

      const mockApiFunction = vi.fn();

      const wrapper = createWrapper(store);

      const { result } = renderHook(
        () => useApiCall(mockApiFunction, { mockEndpoint: '/assessments' }),
        { wrapper }
      );

      await act(async () => {
        await result.current.execute();
      });

      expect(result.current.data).toEqual([{ id: 1, name: 'Test Assessment' }]);
      expect(mockApiFunction).not.toHaveBeenCalled();
    });

    it('should use real API when not in bypass mode', async () => {
      vi.mocked(axiosConfig.isBypassMode).mockReturnValue(false);

      const mockData = { id: 1 };
      const mockApiFunction = vi.fn().mockResolvedValue({ data: mockData });

      const wrapper = createWrapper(store);

      const { result } = renderHook(
        () => useApiCall(mockApiFunction, { mockEndpoint: '/assessments' }),
        { wrapper }
      );

      await act(async () => {
        await result.current.execute();
      });

      expect(result.current.data).toEqual(mockData);
      expect(mockApiFunction).toHaveBeenCalled();
    });

    it('should fallback to real API when mock not found', async () => {
      vi.mocked(axiosConfig.isBypassMode).mockReturnValue(true);

      const mockData = { id: 1 };
      const mockApiFunction = vi.fn().mockResolvedValue({ data: mockData });

      const wrapper = createWrapper(store);

      const { result } = renderHook(
        () => useApiCall(mockApiFunction, { mockEndpoint: '/unknown-endpoint' }),
        { wrapper }
      );

      await act(async () => {
        await result.current.execute();
      });

      expect(result.current.data).toEqual(mockData);
      expect(mockApiFunction).toHaveBeenCalled();
    });
  });

  describe('Notifications', () => {
    it('should not show notification by default', async () => {
      const mockApiFunction = vi.fn().mockResolvedValue({ data: {} });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => useApiCall(mockApiFunction), { wrapper });

      await act(async () => {
        await result.current.execute();
      });

      const state = store.getState();
      expect(state.ui.notifications).toEqual([]);
    });

    it('should show success notification when requested', async () => {
      const mockApiFunction = vi.fn().mockResolvedValue({ data: {} });

      const wrapper = createWrapper(store);

      const { result } = renderHook(
        () => useApiCall(mockApiFunction, { showNotification: true }),
        { wrapper }
      );

      await act(async () => {
        await result.current.execute();
      });

      const state = store.getState();
      expect(state.ui.notifications.length).toBeGreaterThan(0);
      expect(state.ui.notifications[0].type).toBe('success');
    });

    it('should show error notification when requested', async () => {
      const mockApiFunction = vi.fn().mockRejectedValue({ message: 'Error' });

      const wrapper = createWrapper(store);

      const { result } = renderHook(
        () => useApiCall(mockApiFunction, { showNotification: true }),
        { wrapper }
      );

      await expect(async () => {
        await act(async () => {
          await result.current.execute();
        });
      }).rejects.toThrow();

      const state = store.getState();
      expect(state.ui.notifications.length).toBeGreaterThan(0);
      expect(state.ui.notifications[0].type).toBe('error');
    });
  });

  describe('Auto Retry', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('should auto-retry on network errors', async () => {
      const mockApiFunction = vi.fn()
        .mockRejectedValueOnce({ message: 'Network error' })
        .mockResolvedValueOnce({ data: { id: 1 } });

      const wrapper = createWrapper(store);

      const { result } = renderHook(
        () => useApiCall(mockApiFunction, { autoRetry: true, retryDelay: 1000 }),
        { wrapper }
      );

      act(() => {
        result.current.execute().catch(() => {});
      });

      await waitFor(() => {
        expect(mockApiFunction).toHaveBeenCalledTimes(1);
      });

      act(() => {
        vi.advanceTimersByTime(1000);
      });

      await waitFor(() => {
        expect(mockApiFunction).toHaveBeenCalledTimes(2);
      });
    });

    it('should not retry on response errors', async () => {
      const mockApiFunction = vi.fn().mockRejectedValue({
        response: { data: { message: 'Validation error' } },
        message: 'Error',
      });

      const wrapper = createWrapper(store);

      const { result } = renderHook(
        () => useApiCall(mockApiFunction, { autoRetry: true }),
        { wrapper }
      );

      await expect(async () => {
        await act(async () => {
          await result.current.execute();
        });
      }).rejects.toThrow();

      // Should not retry on response errors
      expect(mockApiFunction).toHaveBeenCalledTimes(1);
    });
  });

  describe('Reset', () => {
    it('should reset state', async () => {
      const mockApiFunction = vi.fn().mockResolvedValue({ data: { id: 1 } });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => useApiCall(mockApiFunction), { wrapper });

      await act(async () => {
        await result.current.execute();
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

describe('useApiCallOnMount', () => {
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

  it('should execute API call on mount', async () => {
    const mockApiFunction = vi.fn().mockResolvedValue({ data: { id: 1 } });

    const wrapper = createWrapper(store);

    const { result } = renderHook(() => useApiCallOnMount(mockApiFunction), { wrapper });

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(mockApiFunction).toHaveBeenCalledTimes(1);
    });

    await waitFor(() => {
      expect(result.current.data).toEqual({ id: 1 });
    });
  });

  it('should not execute again on re-render', async () => {
    const mockApiFunction = vi.fn().mockResolvedValue({ data: { id: 1 } });

    const wrapper = createWrapper(store);

    const { rerender } = renderHook(() => useApiCallOnMount(mockApiFunction), { wrapper });

    await waitFor(() => {
      expect(mockApiFunction).toHaveBeenCalledTimes(1);
    });

    rerender();

    expect(mockApiFunction).toHaveBeenCalledTimes(1);
  });
});

describe('usePaginatedApiCall', () => {
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
    it('should initialize with default page and pageSize', () => {
      const mockApiFunction = vi.fn().mockResolvedValue({ data: [] });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => usePaginatedApiCall(mockApiFunction), { wrapper });

      expect(result.current.page).toBe(1);
      expect(result.current.pageSize).toBe(10);
    });

    it('should accept custom initial values', () => {
      const mockApiFunction = vi.fn().mockResolvedValue({ data: [] });

      const wrapper = createWrapper(store);

      const { result } = renderHook(
        () => usePaginatedApiCall(mockApiFunction, 3, 25),
        { wrapper }
      );

      expect(result.current.page).toBe(3);
      expect(result.current.pageSize).toBe(25);
    });

    it('should fetch page with correct params', async () => {
      const mockApiFunction = vi.fn().mockResolvedValue({ data: { items: [] } });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => usePaginatedApiCall(mockApiFunction), { wrapper });

      await act(async () => {
        await result.current.fetchPage();
      });

      expect(mockApiFunction).toHaveBeenCalledWith(1, 10);
    });
  });

  describe('Navigation', () => {
    it('should navigate to next page', async () => {
      const mockApiFunction = vi.fn()
        .mockResolvedValueOnce({ data: { items: [] } })
        .mockResolvedValueOnce({ data: { items: [] } });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => usePaginatedApiCall(mockApiFunction), { wrapper });

      await act(async () => {
        await result.current.nextPage();
      });

      expect(result.current.page).toBe(2);
      expect(mockApiFunction).toHaveBeenCalledWith(2, 10);
    });

    it('should navigate to previous page', async () => {
      const mockApiFunction = vi.fn()
        .mockResolvedValue({ data: { items: [] } });

      const wrapper = createWrapper(store);

      const { result } = renderHook(
        () => usePaginatedApiCall(mockApiFunction, 3, 10),
        { wrapper }
      );

      await act(async () => {
        await result.current.prevPage();
      });

      expect(result.current.page).toBe(2);
      expect(mockApiFunction).toHaveBeenCalledWith(2, 10);
    });

    it('should not go below page 1', async () => {
      const mockApiFunction = vi.fn().mockResolvedValue({ data: { items: [] } });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => usePaginatedApiCall(mockApiFunction), { wrapper });

      await act(async () => {
        await result.current.prevPage();
      });

      expect(result.current.page).toBe(1);
    });

    it('should go to specific page', async () => {
      const mockApiFunction = vi.fn().mockResolvedValue({ data: { items: [] } });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => usePaginatedApiCall(mockApiFunction), { wrapper });

      await act(async () => {
        await result.current.goToPage(5);
      });

      expect(result.current.page).toBe(5);
      expect(mockApiFunction).toHaveBeenCalledWith(5, 10);
    });
  });

  describe('Page Size Updates', () => {
    it('should update page size', async () => {
      const mockApiFunction = vi.fn().mockResolvedValue({ data: { items: [] } });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => usePaginatedApiCall(mockApiFunction), { wrapper });

      act(() => {
        result.current.setPageSize(25);
      });

      expect(result.current.pageSize).toBe(25);

      await act(async () => {
        await result.current.fetchPage();
      });

      expect(mockApiFunction).toHaveBeenCalledWith(1, 25);
    });

    it('should fetch with new page size', async () => {
      const mockApiFunction = vi.fn().mockResolvedValue({ data: { items: [] } });

      const wrapper = createWrapper(store);

      const { result } = renderHook(() => usePaginatedApiCall(mockApiFunction), { wrapper });

      await act(async () => {
        await result.current.fetchPage(1, 50);
      });

      expect(result.current.pageSize).toBe(50);
      expect(mockApiFunction).toHaveBeenCalledWith(1, 50);
    });
  });
});

describe('useSearchApiCall', () => {
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
    vi.useFakeTimers();
    store = createMockStore();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Debouncing', () => {
    it('should debounce search queries', async () => {
      const mockApiFunction = vi.fn().mockResolvedValue({ data: [] });

      const wrapper = createWrapper(store);

      const { result } = renderHook(
        () => useSearchApiCall(mockApiFunction, 300),
        { wrapper }
      );

      act(() => {
        result.current.setQuery('te');
      });

      expect(mockApiFunction).not.toHaveBeenCalled();

      act(() => {
        vi.advanceTimersByTime(150);
      });

      act(() => {
        result.current.setQuery('tes');
      });

      act(() => {
        vi.advanceTimersByTime(150);
      });

      // Should not have called yet
      expect(mockApiFunction).not.toHaveBeenCalled();

      act(() => {
        vi.advanceTimersByTime(150);
      });

      await waitFor(() => {
        expect(mockApiFunction).toHaveBeenCalledTimes(1);
        expect(mockApiFunction).toHaveBeenCalledWith('tes');
      });
    });

    it('should execute search after debounce delay', async () => {
      const mockApiFunction = vi.fn().mockResolvedValue({ data: [{ id: 1 }] });

      const wrapper = createWrapper(store);

      const { result } = renderHook(
        () => useSearchApiCall(mockApiFunction, 300),
        { wrapper }
      );

      act(() => {
        result.current.setQuery('test');
      });

      act(() => {
        vi.advanceTimersByTime(300);
      });

      await waitFor(() => {
        expect(mockApiFunction).toHaveBeenCalledWith('test');
      });
    });

    it('should reset data on empty query', async () => {
      const mockApiFunction = vi.fn().mockResolvedValue({ data: [{ id: 1 }] });

      const wrapper = createWrapper(store);

      const { result } = renderHook(
        () => useSearchApiCall(mockApiFunction, 300),
        { wrapper }
      );

      act(() => {
        result.current.setQuery('test');
      });

      act(() => {
        vi.advanceTimersByTime(300);
      });

      await waitFor(() => {
        expect(result.current.data).toEqual([{ id: 1 }]);
      });

      act(() => {
        result.current.setQuery('');
      });

      act(() => {
        vi.advanceTimersByTime(300);
      });

      expect(result.current.data).toBeNull();
    });
  });

  describe('Query State', () => {
    it('should track query and debouncedQuery separately', () => {
      const mockApiFunction = vi.fn().mockResolvedValue({ data: [] });

      const wrapper = createWrapper(store);

      const { result } = renderHook(
        () => useSearchApiCall(mockApiFunction, 300),
        { wrapper }
      );

      act(() => {
        result.current.setQuery('test');
      });

      expect(result.current.query).toBe('test');
      expect(result.current.debouncedQuery).toBe('');

      act(() => {
        vi.advanceTimersByTime(300);
      });

      expect(result.current.debouncedQuery).toBe('test');
    });
  });
});
