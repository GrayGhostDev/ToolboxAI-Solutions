/**
 * Task Progress Toast Component
 *
 * Provides toast notifications for Celery task status updates
 * using Mantine notifications system.
 */

import { notifications } from '@mantine/notifications';
import { IconCheck, IconX, IconLoader, IconAlertCircle } from '@tabler/icons-react';
import type { CeleryTaskProgress } from '../../hooks/pusher/useCeleryTaskProgress';

export interface TaskProgressToastOptions {
  autoClose?: number | false;
  withCloseButton?: boolean;
}

/**
 * Show a toast notification for task started
 */
export function showTaskStartedToast(
  taskType: string,
  options: TaskProgressToastOptions = {}
) {
  notifications.show({
    id: `task-started-${Date.now()}`,
    title: `${taskType} Started`,
    message: 'Your task has been queued and will begin processing shortly.',
    color: 'blue',
    icon: <IconLoader size={18} />,
    autoClose: options.autoClose ?? 3000,
    withCloseButton: options.withCloseButton ?? true,
    styles: (theme) => ({
      root: {
        backgroundColor: theme.colors.dark[6],
        borderColor: theme.colors.blue[6]
      },
      title: {
        color: theme.colors.blue[4]
      },
      description: {
        color: theme.white
      }
    })
  });
}

/**
 * Show or update a toast notification for task progress
 */
export function showTaskProgressToast(
  taskId: string,
  taskType: string,
  progress: number,
  message?: string,
  options: TaskProgressToastOptions = {}
) {
  const toastId = `task-progress-${taskId}`;

  notifications.show({
    id: toastId,
    title: `${taskType} (${progress}%)`,
    message: message || 'Processing your request...',
    color: 'blue',
    icon: <IconLoader size={18} className="animate-spin" />,
    loading: true,
    autoClose: false,
    withCloseButton: options.withCloseButton ?? false,
    styles: (theme) => ({
      root: {
        backgroundColor: theme.colors.dark[6],
        borderColor: theme.colors.blue[6]
      },
      title: {
        color: theme.colors.blue[4]
      },
      description: {
        color: theme.white
      }
    })
  });
}

/**
 * Show a toast notification for task completion
 */
export function showTaskCompletedToast(
  taskId: string,
  taskType: string,
  message?: string,
  options: TaskProgressToastOptions = {}
) {
  const toastId = `task-progress-${taskId}`;

  // Update existing notification if it exists, otherwise create new one
  notifications.update({
    id: toastId,
    title: `${taskType} Completed`,
    message: message || 'Your task has been completed successfully!',
    color: 'green',
    icon: <IconCheck size={18} />,
    loading: false,
    autoClose: options.autoClose ?? 5000,
    withCloseButton: options.withCloseButton ?? true,
    styles: (theme) => ({
      root: {
        backgroundColor: theme.colors.dark[6],
        borderColor: theme.colors.green[6]
      },
      title: {
        color: theme.colors.green[4]
      },
      description: {
        color: theme.white
      }
    })
  });
}

/**
 * Show a toast notification for task failure
 */
export function showTaskFailedToast(
  taskId: string,
  taskType: string,
  error?: string,
  options: TaskProgressToastOptions = {}
) {
  const toastId = `task-progress-${taskId}`;

  // Update existing notification if it exists, otherwise create new one
  notifications.update({
    id: toastId,
    title: `${taskType} Failed`,
    message: error || 'An error occurred while processing your task.',
    color: 'red',
    icon: <IconX size={18} />,
    loading: false,
    autoClose: options.autoClose ?? 7000,
    withCloseButton: options.withCloseButton ?? true,
    styles: (theme) => ({
      root: {
        backgroundColor: theme.colors.dark[6],
        borderColor: theme.colors.red[6]
      },
      title: {
        color: theme.colors.red[4]
      },
      description: {
        color: theme.white
      }
    })
  });
}

/**
 * Show a generic task notification based on task status
 */
export function showTaskNotification(
  task: CeleryTaskProgress,
  taskType: string,
  options: TaskProgressToastOptions = {}
) {
  switch (task.status) {
    case 'queued':
      showTaskStartedToast(taskType, options);
      break;
    case 'processing':
      showTaskProgressToast(
        task.taskId,
        taskType,
        task.progress,
        task.message,
        options
      );
      break;
    case 'completed':
      showTaskCompletedToast(
        task.taskId,
        taskType,
        task.message,
        options
      );
      break;
    case 'failed':
      showTaskFailedToast(
        task.taskId,
        taskType,
        task.error,
        options
      );
      break;
  }
}

/**
 * Clear task progress notification
 */
export function clearTaskNotification(taskId: string) {
  notifications.hide(`task-progress-${taskId}`);
}

/**
 * Clear all task notifications
 */
export function clearAllTaskNotifications() {
  notifications.clean();
}

export default {
  showTaskStartedToast,
  showTaskProgressToast,
  showTaskCompletedToast,
  showTaskFailedToast,
  showTaskNotification,
  clearTaskNotification,
  clearAllTaskNotifications
};
