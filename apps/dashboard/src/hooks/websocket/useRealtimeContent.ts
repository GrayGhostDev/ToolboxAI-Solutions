/**
 * Real-time content generation hook
 * Tracks content generation requests and progress
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { useWebSocket } from './useWebSocket';
import { 
  ContentGenerationRequest,
  ContentGenerationProgress,
  ContentGenerationComplete,
  WebSocketMessageType,
  WebSocketChannel
} from '../../types/websocket';

export interface ContentGenerationState {
  requestId: string;
  status: 'idle' | 'pending' | 'processing' | 'completed' | 'error';
  progress: ContentGenerationProgress | null;
  result: ContentGenerationComplete | null;
  error: string | null;
}

export interface UseRealtimeContentOptions {
  onProgress?: (progress: ContentGenerationProgress) => void;
  onComplete?: (result: ContentGenerationComplete) => void;
  onError?: (error: string) => void;
  autoCleanup?: boolean;
  cleanupDelay?: number;
}

export interface UseRealtimeContentReturn {
  state: ContentGenerationState;
  isGenerating: boolean;
  generateContent: (request: Omit<ContentGenerationRequest, 'requestId'>) => Promise<void>;
  cancelGeneration: () => void;
  reset: () => void;
}

const initialState: ContentGenerationState = {
  requestId: '',
  status: 'idle',
  progress: null,
  result: null,
  error: null
};

export function useRealtimeContent(
  options: UseRealtimeContentOptions = {}
): UseRealtimeContentReturn {
  const { 
    requestContent, 
    onContentProgress, 
    onContentComplete,
    sendMessage,
    isConnected 
  } = useWebSocket();
  
  const {
    onProgress,
    onComplete,
    onError,
    autoCleanup = true,
    cleanupDelay = 30000 // 30 seconds
  } = options;
  
  const [state, setState] = useState<ContentGenerationState>(initialState);
  const cleanupTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  // Store callbacks in refs
  const onProgressRef = useRef(onProgress);
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);
  
  onProgressRef.current = onProgress;
  onCompleteRef.current = onComplete;
  onErrorRef.current = onError;
  
  // Generate unique request ID
  const generateRequestId = useCallback(() => {
    return `content_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);
  
  // Handle progress updates
  const handleProgress = useCallback((progress: ContentGenerationProgress) => {
    if (progress.requestId !== state.requestId) return;
    
    setState(prev => ({
      ...prev,
      status: 'processing',
      progress
    }));
    
    if (onProgressRef.current) {
      onProgressRef.current(progress);
    }
  }, [state.requestId]);
  
  // Handle completion
  const handleComplete = useCallback((result: ContentGenerationComplete) => {
    if (result.requestId !== state.requestId) return;
    
    setState(prev => ({
      ...prev,
      status: 'completed',
      result
    }));
    
    if (onCompleteRef.current) {
      onCompleteRef.current(result);
    }
    
    // Auto cleanup after delay
    if (autoCleanup) {
      cleanupTimerRef.current = setTimeout(() => {
        reset();
      }, cleanupDelay);
    }
  }, [state.requestId, autoCleanup, cleanupDelay]);
  
  // Handle error
  const handleError = useCallback((error: string) => {
    setState(prev => ({
      ...prev,
      status: 'error',
      error
    }));
    
    if (onErrorRef.current) {
      onErrorRef.current(error);
    }
  }, []);
  
  // Generate content
  const generateContent = useCallback(async (
    request: Omit<ContentGenerationRequest, 'requestId'>
  ) => {
    if (!isConnected) {
      handleError('Not connected to WebSocket server');
      return;
    }
    
    // Clear any existing cleanup timer
    if (cleanupTimerRef.current) {
      clearTimeout(cleanupTimerRef.current);
      cleanupTimerRef.current = null;
    }
    
    const requestId = generateRequestId();
    const fullRequest: ContentGenerationRequest = {
      ...request,
      requestId
    };
    
    setState({
      requestId,
      status: 'pending',
      progress: null,
      result: null,
      error: null
    });
    
    try {
      await requestContent(fullRequest);
      setState(prev => ({ ...prev, status: 'processing' }));
    } catch (error) {
      handleError(error instanceof Error ? error.message : 'Failed to request content');
    }
  }, [isConnected, requestContent, generateRequestId, handleError]);
  
  // Cancel generation
  const cancelGeneration = useCallback(() => {
    if (!state.requestId || state.status === 'completed') return;
    
    sendMessage(
      WebSocketMessageType.CANCEL_CONTENT_GENERATION,
      { requestId: state.requestId },
      { channel: WebSocketChannel.CONTENT_GENERATION }
    );
    
    setState(prev => ({
      ...prev,
      status: 'idle',
      error: 'Generation cancelled'
    }));
  }, [state.requestId, state.status, sendMessage]);
  
  // Reset state
  const reset = useCallback(() => {
    if (cleanupTimerRef.current) {
      clearTimeout(cleanupTimerRef.current);
      cleanupTimerRef.current = null;
    }
    setState(initialState);
  }, []);
  
  // Subscribe to progress and completion events
  useEffect(() => {
    if (!state.requestId || state.status === 'idle') return;
    
    const unsubscribeProgress = onContentProgress(handleProgress);
    const unsubscribeComplete = onContentComplete(handleComplete);
    
    return () => {
      unsubscribeProgress();
      unsubscribeComplete();
    };
  }, [state.requestId, state.status, onContentProgress, onContentComplete, handleProgress, handleComplete]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (cleanupTimerRef.current) {
        clearTimeout(cleanupTimerRef.current);
      }
    };
  }, []);
  
  return {
    state,
    isGenerating: state.status === 'pending' || state.status === 'processing',
    generateContent,
    cancelGeneration,
    reset
  };
}

/**
 * Hook for tracking multiple content generation requests
 */
export function useMultipleContentGeneration(
  maxConcurrent: number = 3
): {
  requests: Map<string, ContentGenerationState>;
  activeCount: number;
  canGenerate: boolean;
  generateContent: (request: Omit<ContentGenerationRequest, 'requestId'>) => Promise<string | null>;
  cancelGeneration: (requestId: string) => void;
  clearCompleted: () => void;
} {
  const [requests, setRequests] = useState<Map<string, ContentGenerationState>>(new Map());
  const { requestContent, onContentProgress, onContentComplete, isConnected } = useWebSocket();
  
  const activeCount = Array.from(requests.values()).filter(
    r => r.status === 'pending' || r.status === 'processing'
  ).length;
  
  const canGenerate = isConnected && activeCount < maxConcurrent;
  
  const generateContent = useCallback(async (
    request: Omit<ContentGenerationRequest, 'requestId'>
  ): Promise<string | null> => {
    if (!canGenerate) return null;
    
    const requestId = `multi_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const fullRequest: ContentGenerationRequest = {
      ...request,
      requestId
    };
    
    setRequests(prev => new Map(prev).set(requestId, {
      requestId,
      status: 'pending',
      progress: null,
      result: null,
      error: null
    }));
    
    try {
      await requestContent(fullRequest);
      return requestId;
    } catch (error) {
      setRequests(prev => {
        const next = new Map(prev);
        const state = next.get(requestId);
        if (state) {
          state.status = 'error';
          state.error = error instanceof Error ? error.message : 'Failed to request content';
        }
        return next;
      });
      return null;
    }
  }, [canGenerate, requestContent]);
  
  const cancelGeneration = useCallback((requestId: string) => {
    setRequests(prev => {
      const next = new Map(prev);
      const state = next.get(requestId);
      if (state && (state.status === 'pending' || state.status === 'processing')) {
        state.status = 'error';
        state.error = 'Cancelled';
      }
      return next;
    });
  }, []);
  
  const clearCompleted = useCallback(() => {
    setRequests(prev => {
      const next = new Map(prev);
      Array.from(next.entries()).forEach(([id, state]) => {
        if (state.status === 'completed' || state.status === 'error') {
          next.delete(id);
        }
      });
      return next;
    });
  }, []);
  
  // Subscribe to progress and completion events
  useEffect(() => {
    const handleProgress = (progress: ContentGenerationProgress) => {
      setRequests(prev => {
        const next = new Map(prev);
        const state = next.get(progress.requestId);
        if (state) {
          state.status = 'processing';
          state.progress = progress;
        }
        return next;
      });
    };
    
    const handleComplete = (result: ContentGenerationComplete) => {
      setRequests(prev => {
        const next = new Map(prev);
        const state = next.get(result.requestId);
        if (state) {
          state.status = 'completed';
          state.result = result;
        }
        return next;
      });
    };
    
    const unsubscribeProgress = onContentProgress(handleProgress);
    const unsubscribeComplete = onContentComplete(handleComplete);
    
    return () => {
      unsubscribeProgress();
      unsubscribeComplete();
    };
  }, [onContentProgress, onContentComplete]);
  
  return {
    requests,
    activeCount,
    canGenerate,
    generateContent,
    cancelGeneration,
    clearCompleted
  };
}