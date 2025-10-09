/**
 * React Hooks for Celery Task Progress Tracking
 *
 * Provides hooks for monitoring Celery background task progress
 * through Pusher real-time events.
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { usePusherEvent, usePusherEvents } from './usePusherEvent';
import { logger } from '../../utils/logger';

export interface CeleryTaskProgress {
  taskId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number; // 0-100
  message?: string;
  error?: string;
  result?: any;
  startedAt?: string;
  completedAt?: string;
}

export interface UseCeleryTaskProgressOptions {
  taskId: string;
  organizationId: string;
  onStarted?: (data: any) => void;
  onProgress?: (data: any) => void;
  onCompleted?: (data: any) => void;
  onFailed?: (data: any) => void;
}

/**
 * Hook for tracking a single Celery task's progress
 *
 * @param options - Task tracking options
 * @returns Task progress state and controls
 */
export function useCeleryTaskProgress(options: UseCeleryTaskProgressOptions) {
  const { taskId, organizationId, onStarted, onProgress, onCompleted, onFailed } = options;

  const [taskProgress, setTaskProgress] = useState<CeleryTaskProgress>({
    taskId,
    status: 'queued',
    progress: 0
  });

  const [error, setError] = useState<string | null>(null);
  const [isTracking, setIsTracking] = useState(true);

  // Handle task started
  const handleStarted = useCallback((data: any) => {
    logger.debug(`Task ${taskId} started:`, data);
    setTaskProgress(prev => ({
      ...prev,
      status: 'processing',
      startedAt: new Date().toISOString(),
      message: data.message || 'Task started'
    }));
    onStarted?.(data);
  }, [taskId, onStarted]);

  // Handle progress updates
  const handleProgress = useCallback((data: any) => {
    if (data.task_id !== taskId) return;

    logger.debug(`Task ${taskId} progress:`, data);
    setTaskProgress(prev => ({
      ...prev,
      status: 'processing',
      progress: data.progress || prev.progress,
      message: data.message || prev.message
    }));
    onProgress?.(data);
  }, [taskId, onProgress]);

  // Handle completion
  const handleCompleted = useCallback((data: any) => {
    if (data.task_id !== taskId) return;

    logger.info(`Task ${taskId} completed:`, data);
    setTaskProgress(prev => ({
      ...prev,
      status: 'completed',
      progress: 100,
      completedAt: new Date().toISOString(),
      result: data.result,
      message: data.message || 'Task completed successfully'
    }));
    setIsTracking(false);
    onCompleted?.(data);
  }, [taskId, onCompleted]);

  // Handle failure
  const handleFailed = useCallback((data: any) => {
    if (data.task_id !== taskId) return;

    logger.error(`Task ${taskId} failed:`, data);
    setTaskProgress(prev => ({
      ...prev,
      status: 'failed',
      completedAt: new Date().toISOString(),
      error: data.error || 'Task failed'
    }));
    setError(data.error || 'Task failed');
    setIsTracking(false);
    onFailed?.(data);
  }, [taskId, onFailed]);

  // Reset tracking
  const reset = useCallback(() => {
    setTaskProgress({
      taskId,
      status: 'queued',
      progress: 0
    });
    setError(null);
    setIsTracking(true);
  }, [taskId]);

  return {
    taskProgress,
    error,
    isTracking,
    reset,
    handlers: {
      handleStarted,
      handleProgress,
      handleCompleted,
      handleFailed
    }
  };
}

/**
 * Hook for tracking lesson content generation progress
 *
 * @param taskId - Celery task ID
 * @param organizationId - Organization ID for channel scoping
 * @param callbacks - Event callbacks
 */
export function useContentGenerationProgress(
  taskId: string,
  organizationId: string,
  callbacks?: {
    onStarted?: (data: any) => void;
    onProgress?: (data: any) => void;
    onCompleted?: (data: any) => void;
    onFailed?: (data: any) => void;
  }
) {
  const channel = `org-${organizationId}`;
  const { taskProgress, error, isTracking, reset, handlers } = useCeleryTaskProgress({
    taskId,
    organizationId,
    ...callbacks
  });

  // Subscribe to content generation events
  usePusherEvent('content-generation-started', handlers.handleStarted, { channel });
  usePusherEvent('content-generation-progress', handlers.handleProgress, { channel });
  usePusherEvent('content-generation-completed', handlers.handleCompleted, { channel });
  usePusherEvent('content-generation-failed', handlers.handleFailed, { channel });

  return {
    progress: taskProgress.progress,
    status: taskProgress.status,
    message: taskProgress.message,
    result: taskProgress.result,
    error,
    isTracking,
    reset
  };
}

/**
 * Hook for tracking quiz question generation progress
 *
 * @param taskId - Celery task ID
 * @param organizationId - Organization ID for channel scoping
 * @param callbacks - Event callbacks
 */
export function useQuizGenerationProgress(
  taskId: string,
  organizationId: string,
  callbacks?: {
    onStarted?: (data: any) => void;
    onProgress?: (data: any) => void;
    onCompleted?: (data: any) => void;
    onFailed?: (data: any) => void;
  }
) {
  const channel = `org-${organizationId}`;
  const { taskProgress, error, isTracking, reset, handlers } = useCeleryTaskProgress({
    taskId,
    organizationId,
    ...callbacks
  });

  // Subscribe to quiz generation events
  usePusherEvent('quiz-generation-started', handlers.handleStarted, { channel });
  usePusherEvent('quiz-generation-progress', handlers.handleProgress, { channel });
  usePusherEvent('quiz-generation-completed', handlers.handleCompleted, { channel });
  usePusherEvent('quiz-generation-failed', handlers.handleFailed, { channel });

  return {
    progress: taskProgress.progress,
    status: taskProgress.status,
    message: taskProgress.message,
    result: taskProgress.result,
    error,
    isTracking,
    reset
  };
}

/**
 * Hook for tracking Roblox script optimization progress
 *
 * @param taskId - Celery task ID
 * @param organizationId - Organization ID for channel scoping
 * @param callbacks - Event callbacks
 */
export function useRobloxOptimizationProgress(
  taskId: string,
  organizationId: string,
  callbacks?: {
    onStarted?: (data: any) => void;
    onProgress?: (data: any) => void;
    onCompleted?: (data: any) => void;
    onFailed?: (data: any) => void;
  }
) {
  const channel = `org-${organizationId}`;
  const { taskProgress, error, isTracking, reset, handlers } = useCeleryTaskProgress({
    taskId,
    organizationId,
    ...callbacks
  });

  // Subscribe to script optimization events
  usePusherEvent('script-optimization-started', handlers.handleStarted, { channel });
  usePusherEvent('script-optimization-progress', handlers.handleProgress, { channel });
  usePusherEvent('script-optimization-completed', handlers.handleCompleted, { channel });
  usePusherEvent('script-optimization-failed', handlers.handleFailed, { channel });

  return {
    progress: taskProgress.progress,
    status: taskProgress.status,
    message: taskProgress.message,
    result: taskProgress.result,
    error,
    isTracking,
    reset
  };
}

/**
 * Hook for tracking multiple Celery tasks simultaneously
 *
 * @param organizationId - Organization ID for channel scoping
 * @returns Task tracking state and controls
 */
export function useMultipleCeleryTasks(organizationId: string) {
  const [tasks, setTasks] = useState<Map<string, CeleryTaskProgress>>(new Map());
  const channel = `org-${organizationId}`;

  const addTask = useCallback((taskId: string, taskType: string) => {
    setTasks(prev => {
      const newTasks = new Map(prev);
      newTasks.set(taskId, {
        taskId,
        status: 'queued',
        progress: 0
      });
      return newTasks;
    });
  }, []);

  const removeTask = useCallback((taskId: string) => {
    setTasks(prev => {
      const newTasks = new Map(prev);
      newTasks.delete(taskId);
      return newTasks;
    });
  }, []);

  const updateTaskProgress = useCallback((taskId: string, update: Partial<CeleryTaskProgress>) => {
    setTasks(prev => {
      const newTasks = new Map(prev);
      const existingTask = newTasks.get(taskId);
      if (existingTask) {
        newTasks.set(taskId, { ...existingTask, ...update });
      }
      return newTasks;
    });
  }, []);

  // Generic handlers for all task types
  const handleStarted = useCallback((data: any) => {
    const taskId = data.task_id;
    if (taskId && tasks.has(taskId)) {
      updateTaskProgress(taskId, {
        status: 'processing',
        startedAt: new Date().toISOString(),
        message: data.message
      });
    }
  }, [tasks, updateTaskProgress]);

  const handleProgress = useCallback((data: any) => {
    const taskId = data.task_id;
    if (taskId && tasks.has(taskId)) {
      updateTaskProgress(taskId, {
        status: 'processing',
        progress: data.progress,
        message: data.message
      });
    }
  }, [tasks, updateTaskProgress]);

  const handleCompleted = useCallback((data: any) => {
    const taskId = data.task_id;
    if (taskId && tasks.has(taskId)) {
      updateTaskProgress(taskId, {
        status: 'completed',
        progress: 100,
        completedAt: new Date().toISOString(),
        result: data.result,
        message: data.message
      });
    }
  }, [tasks, updateTaskProgress]);

  const handleFailed = useCallback((data: any) => {
    const taskId = data.task_id;
    if (taskId && tasks.has(taskId)) {
      updateTaskProgress(taskId, {
        status: 'failed',
        completedAt: new Date().toISOString(),
        error: data.error
      });
    }
  }, [tasks, updateTaskProgress]);

  // Subscribe to all task event types
  const eventHandlers = {
    // Content generation
    'content-generation-started': handleStarted,
    'content-generation-progress': handleProgress,
    'content-generation-completed': handleCompleted,
    'content-generation-failed': handleFailed,
    // Quiz generation
    'quiz-generation-started': handleStarted,
    'quiz-generation-progress': handleProgress,
    'quiz-generation-completed': handleCompleted,
    'quiz-generation-failed': handleFailed,
    // Script optimization
    'script-optimization-started': handleStarted,
    'script-optimization-progress': handleProgress,
    'script-optimization-completed': handleCompleted,
    'script-optimization-failed': handleFailed
  };

  usePusherEvents(eventHandlers, { channel });

  return {
    tasks: Array.from(tasks.values()),
    tasksMap: tasks,
    addTask,
    removeTask,
    updateTaskProgress,
    getTask: (taskId: string) => tasks.get(taskId),
    hasTask: (taskId: string) => tasks.has(taskId),
    activeTasks: Array.from(tasks.values()).filter(t => t.status === 'processing'),
    completedTasks: Array.from(tasks.values()).filter(t => t.status === 'completed'),
    failedTasks: Array.from(tasks.values()).filter(t => t.status === 'failed')
  };
}

export default useCeleryTaskProgress;
