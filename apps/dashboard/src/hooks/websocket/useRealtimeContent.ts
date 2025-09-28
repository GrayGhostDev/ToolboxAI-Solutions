/**
 * Realtime Content Hook (Pusher Implementation)
 * Provides real-time content generation monitoring using Pusher
 * Updated for 2025 standards
 */

import { useState, useEffect, useCallback } from 'react';
import { pusherService } from '../../services/pusher';
import {
  WebSocketMessageType,
  ContentProgressMessage,
  ContentCompleteMessage,
  ContentErrorMessage
} from '../../types/websocket';

export interface ContentGenerationState {
  taskId?: string;
  status: 'idle' | 'generating' | 'complete' | 'error';
  progress: number;
  message?: string;
  result?: any;
  error?: string;
}

export interface UseRealtimeContentOptions {
  taskId?: string;
  autoSubscribe?: boolean;
  onProgress?: (data: ContentProgressMessage) => void;
  onComplete?: (data: ContentCompleteMessage) => void;
  onError?: (data: ContentErrorMessage) => void;
}

export interface UseRealtimeContentReturn {
  state: ContentGenerationState;
  isGenerating: boolean;
  subscribe: (taskId: string) => void;
  unsubscribe: () => void;
  reset: () => void;
}

export function useRealtimeContent(options: UseRealtimeContentOptions = {}): UseRealtimeContentReturn {
  const { taskId, autoSubscribe = true, onProgress, onComplete, onError } = options;

  const [state, setState] = useState<ContentGenerationState>({
    status: 'idle',
    progress: 0,
  });

  const [subscriptionId, setSubscriptionId] = useState<string | null>(null);

  const subscribe = useCallback((targetTaskId: string) => {
    if (subscriptionId) {
      pusherService.unsubscribe(subscriptionId);
    }

    const id = pusherService.subscribe(
      'content-generation',
      (message: any) => {
        if (message.data?.taskId !== targetTaskId) return;

        switch (message.type) {
          case WebSocketMessageType.CONTENT_PROGRESS: {
            const progressData = message.data as ContentProgressMessage;
            setState(prev => ({
              ...prev,
              taskId: targetTaskId,
              status: 'generating',
              progress: progressData.progress,
              message: progressData.message,
            }));
            onProgress?.(progressData);
            break;
          }

          case WebSocketMessageType.CONTENT_COMPLETE: {
            const completeData = message.data as ContentCompleteMessage;
            setState(prev => ({
              ...prev,
              status: 'complete',
              progress: 100,
              result: completeData.result,
            }));
            onComplete?.(completeData);
            break;
          }

          case WebSocketMessageType.CONTENT_ERROR: {
            const errorData = message.data as ContentErrorMessage;
            setState(prev => ({
              ...prev,
              status: 'error',
              error: errorData.error,
            }));
            onError?.(errorData);
            break;
          }

          default:
            break;
        }
      },
      (message) =>
        [
          WebSocketMessageType.CONTENT_PROGRESS,
          WebSocketMessageType.CONTENT_COMPLETE,
          WebSocketMessageType.CONTENT_ERROR,
        ].includes(message.type) && message.data?.taskId === targetTaskId
    );

    setSubscriptionId(id);
    setState(prev => ({ ...prev, taskId: targetTaskId }));
  }, [onProgress, onComplete, onError, subscriptionId]);

  const unsubscribe = useCallback(() => {
    if (subscriptionId) {
      pusherService.unsubscribe(subscriptionId);
      setSubscriptionId(null);
    }
  }, [subscriptionId]);

  const reset = useCallback(() => {
    setState({
      status: 'idle',
      progress: 0,
    });
  }, []);

  useEffect(() => {
    if (autoSubscribe && taskId) {
      subscribe(taskId);
    }

    return () => {
      unsubscribe();
    };
  }, [autoSubscribe, taskId, subscribe, unsubscribe]);

  return {
    state,
    isGenerating: state.status === 'generating',
    subscribe,
    unsubscribe,
    reset,
  };
}

export function useMultipleContentGeneration(taskIds: string[]) {
  const [states, setStates] = useState<Record<string, ContentGenerationState>>({});

  useEffect(() => {
    const subscriptions: string[] = [];

    taskIds.forEach(taskId => {
      const id = pusherService.subscribe('content-generation', (message: any) => {
        if (message.data?.taskId !== taskId) return;

        setStates(prev => ({
          ...prev,
          [taskId]: {
            ...prev[taskId],
            taskId,
            status: message.type === WebSocketMessageType.CONTENT_COMPLETE ? 'complete' :
                   message.type === WebSocketMessageType.CONTENT_ERROR ? 'error' : 'generating',
            progress: message.data?.progress || prev[taskId]?.progress || 0,
            message: message.data?.message,
            result: message.data?.result,
            error: message.data?.error,
          }
        }));
      }, (message) => {
        return [
          WebSocketMessageType.CONTENT_PROGRESS,
          WebSocketMessageType.CONTENT_COMPLETE,
          WebSocketMessageType.CONTENT_ERROR,
        ].includes(message.type) && message.data?.taskId === taskId;
      });

      subscriptions.push(id);
    });

    return () => {
      subscriptions.forEach(id => pusherService.unsubscribe(id));
    };
  }, [taskIds]);

  return {
    states,
    getState: (taskId: string) => states[taskId] || { status: 'idle', progress: 0 },
    isAnyGenerating: Object.values(states).some(state => state.status === 'generating'),
  };
}
