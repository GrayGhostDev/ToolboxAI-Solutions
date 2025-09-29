/**
 * React Hook for Pusher Event Subscriptions
 *
 * Provides a simple way to listen to specific Pusher events
 * with automatic subscription management and cleanup.
 */

import { useEffect, useCallback, useRef } from 'react';
import { usePusherContext } from '../../contexts/PusherContext';
import { PusherEventHandler } from '../../types/pusher';
import { logger } from '../../utils/logger';

export interface UsePusherEventOptions {
  enabled?: boolean;
  channel?: string;
  onError?: (error: Error) => void;
}

/**
 * Hook for listening to a specific Pusher event
 *
 * @param eventName - Name of the event to listen to
 * @param handler - Handler function for the event
 * @param options - Event subscription options
 */
export function usePusherEvent(
  eventName: string,
  handler: PusherEventHandler,
  options: UsePusherEventOptions = {}
) {
  const { enabled = true, channel, onError } = options;
  const { on, off, subscribeToChannel, unsubscribeFromChannel } = usePusherContext();

  const handlerRef = useRef(handler);
  const subscriptionIdRef = useRef<string | null>(null);

  // Update handler ref when it changes
  useEffect(() => {
    handlerRef.current = handler;
  }, [handler]);

  // Wrapper handler that calls the latest handler
  const stableHandler = useCallback<PusherEventHandler>((data, metadata) => {
    try {
      handlerRef.current(data, metadata);
    } catch (error) {
      logger.error(`Error in event handler for ${eventName}:`, error);
      onError?.(error as Error);
    }
  }, [eventName, onError]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    // If channel is specified, subscribe to that channel
    if (channel) {
      try {
        subscriptionIdRef.current = subscribeToChannel(
          channel,
          { [eventName]: stableHandler },
          { autoSubscribe: true }
        );

        logger.debug(`Subscribed to event ${eventName} on channel ${channel}`);
      } catch (error) {
        logger.error(`Failed to subscribe to event ${eventName}:`, error);
        onError?.(error as Error);
      }

      return () => {
        if (subscriptionIdRef.current) {
          unsubscribeFromChannel(subscriptionIdRef.current);
          subscriptionIdRef.current = null;
        }
      };
    } else {
      // Global event listener
      const unsubscribe = on(eventName, stableHandler);

      logger.debug(`Listening to global event: ${eventName}`);

      return () => {
        unsubscribe();
        logger.debug(`Stopped listening to global event: ${eventName}`);
      };
    }
  }, [
    enabled,
    eventName,
    channel,
    stableHandler,
    on,
    subscribeToChannel,
    unsubscribeFromChannel,
    onError
  ]);
}

/**
 * Hook for listening to multiple Pusher events
 *
 * @param eventHandlers - Object mapping event names to handlers
 * @param options - Event subscription options
 */
export function usePusherEvents(
  eventHandlers: Record<string, PusherEventHandler>,
  options: UsePusherEventOptions = {}
) {
  const { enabled = true, channel, onError } = options;
  const { subscribeToChannel, unsubscribeFromChannel } = usePusherContext();

  const subscriptionIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!enabled || Object.keys(eventHandlers).length === 0) {
      return;
    }

    // If channel is specified, subscribe to that channel with all event handlers
    if (channel) {
      try {
        subscriptionIdRef.current = subscribeToChannel(
          channel,
          eventHandlers,
          { autoSubscribe: true }
        );

        logger.debug(`Subscribed to ${Object.keys(eventHandlers).length} events on channel ${channel}`);
      } catch (error) {
        logger.error(`Failed to subscribe to events on channel ${channel}:`, error);
        onError?.(error as Error);
      }

      return () => {
        if (subscriptionIdRef.current) {
          unsubscribeFromChannel(subscriptionIdRef.current);
          subscriptionIdRef.current = null;
        }
      };
    }
  }, [enabled, channel, eventHandlers, subscribeToChannel, unsubscribeFromChannel, onError]);
}

/**
 * Hook for handling content generation events
 *
 * @param onProgress - Handler for progress updates
 * @param onComplete - Handler for completion
 * @param onError - Handler for errors
 */
export function useContentGenerationEvents(
  onProgress?: (data: any) => void,
  onComplete?: (data: any) => void,
  onError?: (data: any) => void
) {
  const handlers: Record<string, PusherEventHandler> = {};

  if (onProgress) handlers['content-progress'] = onProgress;
  if (onComplete) handlers['content-complete'] = onComplete;
  if (onError) handlers['content-error'] = onError;

  usePusherEvents(handlers, { channel: 'content-generation' });
}

/**
 * Hook for handling quiz events
 *
 * @param onStart - Handler for quiz start
 * @param onSubmit - Handler for quiz submission
 * @param onResult - Handler for quiz results
 */
export function useQuizEvents(
  onStart?: (data: any) => void,
  onSubmit?: (data: any) => void,
  onResult?: (data: any) => void
) {
  const handlers: Record<string, PusherEventHandler> = {};

  if (onStart) handlers['quiz-start'] = onStart;
  if (onSubmit) handlers['quiz-submit'] = onSubmit;
  if (onResult) handlers['quiz-result'] = onResult;

  usePusherEvents(handlers, { channel: 'quiz-updates' });
}

/**
 * Hook for handling agent status events
 *
 * @param agentId - ID of the agent to monitor
 * @param onStatusUpdate - Handler for status updates
 * @param onResponse - Handler for agent responses
 */
export function useAgentEvents(
  agentId: string,
  onStatusUpdate?: (data: any) => void,
  onResponse?: (data: any) => void
) {
  const handlers: Record<string, PusherEventHandler> = {};

  if (onStatusUpdate) handlers['agent-status-update'] = onStatusUpdate;
  if (onResponse) handlers['agent-response'] = onResponse;

  usePusherEvents(handlers, { channel: `agent-${agentId}` });
}

/**
 * Hook for handling system notification events
 *
 * @param onNotification - Handler for notifications
 * @param onAlert - Handler for alerts
 * @param onMaintenance - Handler for maintenance notices
 */
export function useSystemEvents(
  onNotification?: (data: any) => void,
  onAlert?: (data: any) => void,
  onMaintenance?: (data: any) => void
) {
  const handlers: Record<string, PusherEventHandler> = {};

  if (onNotification) handlers['system-notification'] = onNotification;
  if (onAlert) handlers['system-alert'] = onAlert;
  if (onMaintenance) handlers['system-maintenance'] = onMaintenance;

  usePusherEvents(handlers, { channel: 'system-announcements' });
}

export default usePusherEvent;