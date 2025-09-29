/**
 * Pusher React Hooks Export
 *
 * Central export point for all Pusher-related React hooks
 * providing real-time functionality to the application.
 */

// Channel subscription hooks
export {
  usePusherChannel,
  usePrivateChannel,
  usePresenceChannel,
  type UsePusherChannelOptions,
  type UsePusherChannelReturn
} from './usePusherChannel';

// Event subscription hooks
export {
  usePusherEvent,
  usePusherEvents,
  useContentGenerationEvents,
  useQuizEvents,
  useAgentEvents,
  useSystemEvents,
  type UsePusherEventOptions
} from './usePusherEvent';

// Presence and collaboration hooks
export {
  usePusherPresence,
  useUserActivity,
  useCollaboration,
  useOnlineStatus,
  type UsePresenceOptions,
  type UsePresenceReturn
} from './usePusherPresence';

// Re-export context hooks for convenience
export {
  usePusherContext,
  usePusherState,
  usePusherChannels,
  usePusherPresenceChannels,
  usePusherMessaging
} from '../../contexts/PusherContext';

/**
 * Common usage patterns:
 *
 * 1. Subscribe to a channel:
 * ```tsx
 * const { isSubscribed, trigger } = usePusherChannel('my-channel', {
 *   'my-event': (data) => console.log(data)
 * });
 * ```
 *
 * 2. Listen to specific events:
 * ```tsx
 * usePusherEvent('content-progress', (data) => {
 *   updateProgress(data.progress);
 * });
 * ```
 *
 * 3. Join a presence channel:
 * ```tsx
 * const { members, isJoined } = usePusherPresence('classroom-123', {
 *   userInfo: { name: 'John Doe', status: 'online' }
 * });
 * ```
 *
 * 4. Track user activity:
 * ```tsx
 * const { status, lastActivity } = useUserActivity();
 * ```
 *
 * 5. Real-time collaboration:
 * ```tsx
 * const { members, sendCursor, sendTyping } = useCollaboration('doc-456', userId);
 * ```
 */