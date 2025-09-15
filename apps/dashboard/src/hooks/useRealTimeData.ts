/**
 * Real-time data hook for automatic CRUD operations refresh
 * Provides optimistic updates with WebSocket fallback
 */

import { useState, useEffect, useCallback } from 'react';
import { useWebSocketContext } from '../contexts/WebSocketContext';
import { addNotification } from '../store/slices/uiSlice';
import { useAppDispatch } from '../store';

interface UseRealTimeDataOptions<T> {
  /** Function to fetch data from API */
  fetchFn: () => Promise<T[]>;
  /** Function to create new item */
  createFn?: (data: any) => Promise<T>;
  /** Function to update existing item */
  updateFn?: (id: string, data: any) => Promise<T>;
  /** Function to delete item */
  deleteFn?: (id: string) => Promise<void>;
  /** WebSocket channel to listen for updates */
  channel?: string;
  /** Transform function for new items */
  transformFn?: (item: any) => T;
  /** Auto-fetch on mount */
  autoFetch?: boolean;
  /** Optional periodic refresh interval in ms */
  refreshInterval?: number;
}

interface UseRealTimeDataReturn<T> {
  data: T[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  refetch: () => Promise<void>;
  create: (itemData: any) => Promise<T | null>;
  update: (id: string, itemData: any) => Promise<T | null>;
  remove: (id: string) => Promise<boolean>;
  setData: React.Dispatch<React.SetStateAction<T[]>>;
  setLoading: React.Dispatch<React.SetStateAction<boolean>>;
  setError: React.Dispatch<React.SetStateAction<string | null>>;
}

// Overload to support (channel, options) signature
export function useRealTimeData<T extends { id: string }>(
  options: UseRealTimeDataOptions<T>
): UseRealTimeDataReturn<T>;
export function useRealTimeData<T extends { id: string }>(
  channel: string,
  options?: Partial<UseRealTimeDataOptions<T>>
): UseRealTimeDataReturn<T>;
export function useRealTimeData<T extends { id: string }>(
  arg1: any,
  arg2?: any
): UseRealTimeDataReturn<T> {
  const options: UseRealTimeDataOptions<T> = typeof arg1 === 'string'
    ? ({ channel: arg1, autoFetch: true, fetchFn: async () => [], ...(arg2 || {}) } as UseRealTimeDataOptions<T>)
    : (arg1 as UseRealTimeDataOptions<T>);

  const {
    fetchFn,
    createFn,
    updateFn,
    deleteFn,
    channel,
    transformFn,
    autoFetch = true,
    refreshInterval
  } = options;

  const dispatch = useAppDispatch();
  const { isConnected, subscribe, unsubscribe } = useWebSocketContext();

  const [data, setData] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch data from API - memoized without fetchFn dependency to avoid loops
  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchFn();
      setData(result);
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to load data';
      setError(errorMessage);
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  }, []); // Empty deps - fetchFn is passed in and doesn't change

  // Create new item with optimistic update
  const create = useCallback(async (itemData: any): Promise<T | null> => {
    if (!createFn) {
      console.warn('Create function not provided');
      return null;
    }

    setLoading(true);
    setError(null);
    
    try {
      const newItem = await createFn(itemData);
      const transformedItem = transformFn ? transformFn(newItem) : newItem;
      
      // Optimistic update
      setData(prev => [transformedItem, ...prev]);
      
      // Refresh to ensure consistency
      setTimeout(() => refresh(), 100);
      
      return transformedItem;
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to create item';
      setError(errorMessage);
      dispatch(addNotification({
        type: 'error',
        message: errorMessage
      }));
      console.error('Error creating item:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [createFn, transformFn, dispatch]); // Remove refresh to avoid circular deps

  // Update existing item with optimistic update
  const update = useCallback(async (id: string, itemData: any): Promise<T | null> => {
    if (!updateFn) {
      console.warn('Update function not provided');
      return null;
    }

    setLoading(true);
    setError(null);
    
    try {
      const updatedItem = await updateFn(id, itemData);
      const transformedItem = transformFn ? transformFn(updatedItem) : updatedItem;
      
      // Optimistic update
      setData(prev => prev.map(item => 
        item.id === id ? transformedItem : item
      ));
      
      // Refresh to ensure consistency
      setTimeout(() => refresh(), 100);
      
      return transformedItem;
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to update item';
      setError(errorMessage);
      dispatch(addNotification({
        type: 'error',
        message: errorMessage
      }));
      console.error('Error updating item:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [updateFn, transformFn, dispatch]); // Remove refresh to avoid circular deps

  // Delete item with optimistic update
  const remove = useCallback(async (id: string): Promise<boolean> => {
    if (!deleteFn) {
      console.warn('Delete function not provided');
      return false;
    }

    if (!window.confirm('Are you sure you want to delete this item?')) {
      return false;
    }

    setLoading(true);
    setError(null);
    
    try {
      await deleteFn(id);
      
      // Optimistic update
      setData(prev => prev.filter(item => item.id !== id));
      
      // Refresh to ensure consistency
      setTimeout(() => refresh(), 100);
      
      return true;
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || err?.message || 'Failed to delete item';
      setError(errorMessage);
      dispatch(addNotification({
        type: 'error',
        message: errorMessage
      }));
      console.error('Error deleting item:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [deleteFn, dispatch]); // Remove refresh to avoid circular deps

  // Auto-fetch on mount
  useEffect(() => {
    if (autoFetch) {
      refresh();
    }
  }, [autoFetch]); // Remove refresh from deps to avoid loops

  // Optional polling
  useEffect(() => {
    if (!refreshInterval || refreshInterval <= 0) return;
    const id = setInterval(() => {
      refresh();
    }, refreshInterval);
    return () => clearInterval(id);
  }, [refreshInterval]); // Remove refresh from deps to avoid loops

  // WebSocket subscription for real-time updates
  useEffect(() => {
    if (!channel || !isConnected) return;

    const subscriptionId = subscribe(channel, (message: any) => {
      console.log(`[Real-time] Received update on ${channel}:`, message);
      
      // Handle different types of real-time updates
      switch (message.type) {
        case 'ITEM_CREATED':
          if (message.payload && transformFn) {
            const newItem = transformFn(message.payload);
            setData(prev => {
              // Avoid duplicates
              if (prev.some(item => item.id === newItem.id)) {
                return prev;
              }
              return [newItem, ...prev];
            });
          } else {
            // If no transform function, just refresh
            refresh();
          }
          break;
          
        case 'ITEM_UPDATED':
          if (message.payload && transformFn) {
            const updatedItem = transformFn(message.payload);
            setData(prev => prev.map(item => 
              item.id === updatedItem.id ? updatedItem : item
            ));
          } else {
            refresh();
          }
          break;
          
        case 'ITEM_DELETED':
          if (message.payload?.id) {
            setData(prev => prev.filter(item => item.id !== message.payload.id));
          } else {
            refresh();
          }
          break;
          
        default:
          // For any other updates, just refresh
          refresh();
          break;
      }
    });

    return () => {
      unsubscribe(subscriptionId);
    };
  }, [channel, isConnected, subscribe, unsubscribe, transformFn]); // Remove refresh to avoid loops

  return {
    data,
    loading,
    error,
    refresh,
    refetch: refresh,
    create,
    update,
    remove,
    setData,
    setLoading,
    setError
  };
}

export default useRealTimeData;