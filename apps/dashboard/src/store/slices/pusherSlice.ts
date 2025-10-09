/**
 * Pusher Redux Slice
 * Manages Pusher-specific state for real-time communication
 * @module pusherSlice
 * @version 1.0.0
 * @since 2025-09-26
 */

import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

// Pusher connection states
export enum PusherConnectionState {
  UNINITIALIZED = 'uninitialized',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  FAILED = 'failed',
  UNAVAILABLE = 'unavailable',
  POLLING = 'polling', // Fallback mode
}

// Pusher channel types
export enum PusherChannelType {
  PUBLIC = 'public',
  PRIVATE = 'private',
  PRESENCE = 'presence',
  ENCRYPTED = 'encrypted',
}

// Channel subscription
export interface PusherChannelSubscription {
  name: string;
  type: PusherChannelType;
  subscribed: boolean;
  members?: number; // For presence channels
  events: string[]; // List of events subscribed to
}

// Pusher event
export interface PusherEvent {
  id: string;
  channel: string;
  event: string;
  data: any;
  timestamp: number;
  userId?: string; // For user events
}

// Connection metrics
export interface PusherMetrics {
  connectionAttempts: number;
  successfulConnections: number;
  failedConnections: number;
  messagesSent: number;
  messagesReceived: number;
  bytesReceived: number;
  averageLatency: number;
  lastLatency: number;
  reconnectCount: number;
  lastConnectedAt?: number;
  lastDisconnectedAt?: number;
}

// Error info
export interface PusherError {
  code: string;
  message: string;
  timestamp: number;
  recoverable: boolean;
}

// Pusher state
export interface PusherState {
  // Connection
  connectionState: PusherConnectionState;
  connectionError: PusherError | null;
  socketId: string | null;

  // Channels
  channels: Record<string, PusherChannelSubscription>;
  activeChannel: string | null;

  // Events
  events: PusherEvent[];
  eventQueue: PusherEvent[]; // Events waiting to be processed
  lastEventId: string | null;

  // Metrics
  metrics: PusherMetrics;

  // Configuration
  config: {
    enabled: boolean;
    cluster: string;
    forceTLS: boolean;
    authEndpoint: string;
    autoReconnect: boolean;
    reconnectDelay: number;
    maxReconnectAttempts: number;
  };

  // Fallback
  fallbackMode: boolean;
  pollingInterval: number | null;

  // UI
  showConnectionStatus: boolean;
  debugMode: boolean;
}

// Initial state
const initialState: PusherState = {
  connectionState: PusherConnectionState.UNINITIALIZED,
  connectionError: null,
  socketId: null,

  channels: {},
  activeChannel: null,

  events: [],
  eventQueue: [],
  lastEventId: null,

  metrics: {
    connectionAttempts: 0,
    successfulConnections: 0,
    failedConnections: 0,
    messagesSent: 0,
    messagesReceived: 0,
    bytesReceived: 0,
    averageLatency: 0,
    lastLatency: 0,
    reconnectCount: 0,
  },

  config: {
    enabled: true,
    cluster: 'us2',
    forceTLS: true,
    authEndpoint: '/api/v1/pusher/auth',
    autoReconnect: true,
    reconnectDelay: 1000,
    maxReconnectAttempts: 5,
  },

  fallbackMode: false,
  pollingInterval: null,

  showConnectionStatus: true,
  debugMode: process.env.NODE_ENV === 'development',
};

// Create slice
const pusherSlice = createSlice({
  name: 'pusher',
  initialState,
  reducers: {
    // Connection actions
    setConnectionStatus: (state, action: PayloadAction<PusherConnectionState>) => {
      state.connectionState = action.payload;

      // Update metrics
      if (action.payload === PusherConnectionState.CONNECTED) {
        state.metrics.successfulConnections++;
        state.metrics.lastConnectedAt = Date.now();
        state.connectionError = null;
        state.fallbackMode = false;
      } else if (action.payload === PusherConnectionState.DISCONNECTED) {
        state.metrics.lastDisconnectedAt = Date.now();
        state.socketId = null;
      }
    },

    setConnectionError: (state, action: PayloadAction<string>) => {
      state.connectionError = {
        code: 'CONNECTION_ERROR',
        message: action.payload,
        timestamp: Date.now(),
        recoverable: true,
      };
      state.connectionState = PusherConnectionState.FAILED;
      state.metrics.failedConnections++;
    },

    setSocketId: (state, action: PayloadAction<string>) => {
      state.socketId = action.payload;
    },

    // Channel actions
    subscribeToChannel: (state, action: PayloadAction<{
      name: string;
      type: PusherChannelType;
    }>) => {
      const { name, type } = action.payload;
      state.channels[name] = {
        name,
        type,
        subscribed: false,
        events: [],
      };
    },

    channelSubscribed: (state, action: PayloadAction<{
      name: string;
      members?: number;
    }>) => {
      const { name, members } = action.payload;
      if (state.channels[name]) {
        state.channels[name].subscribed = true;
        if (members !== undefined) {
          state.channels[name].members = members;
        }
      }
    },

    channelUnsubscribed: (state, action: PayloadAction<string>) => {
      delete state.channels[action.payload];
      if (state.activeChannel === action.payload) {
        state.activeChannel = null;
      }
    },

    setActiveChannel: (state, action: PayloadAction<string | null>) => {
      state.activeChannel = action.payload;
    },

    addChannelEvent: (state, action: PayloadAction<{
      channel: string;
      event: string;
    }>) => {
      const { channel, event } = action.payload;
      if (state.channels[channel] && !state.channels[channel].events.includes(event)) {
        state.channels[channel].events.push(event);
      }
    },

    // Event actions
    addEvent: (state, action: PayloadAction<Omit<PusherEvent, 'id'>>) => {
      const event: PusherEvent = {
        ...action.payload,
        id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      };

      state.events.unshift(event);
      state.lastEventId = event.id;
      state.metrics.messagesReceived++;

      // Keep only last 100 events
      if (state.events.length > 100) {
        state.events = state.events.slice(0, 100);
      }
    },

    queueEvent: (state, action: PayloadAction<PusherEvent>) => {
      state.eventQueue.push(action.payload);
    },

    processEventQueue: (state) => {
      state.events.unshift(...state.eventQueue);
      state.eventQueue = [];

      // Keep only last 100 events
      if (state.events.length > 100) {
        state.events = state.events.slice(0, 100);
      }
    },

    clearEvents: (state, action: PayloadAction<string | undefined>) => {
      if (action.payload) {
        // Clear events for specific channel
        state.events = state.events.filter(e => e.channel !== action.payload);
      } else {
        // Clear all events
        state.events = [];
      }
    },

    // Metrics actions
    updateMetrics: (state, action: PayloadAction<Partial<PusherMetrics>>) => {
      state.metrics = {
        ...state.metrics,
        ...action.payload,
      };

      // Calculate average latency
      if (action.payload.lastLatency !== undefined) {
        const count = state.metrics.messagesReceived || 1;
        state.metrics.averageLatency =
          (state.metrics.averageLatency * (count - 1) + action.payload.lastLatency) / count;
      }
    },

    incrementConnectionAttempts: (state) => {
      state.metrics.connectionAttempts++;
    },

    incrementReconnectCount: (state) => {
      state.metrics.reconnectCount++;
    },

    incrementMessagesSent: (state) => {
      state.metrics.messagesSent++;
    },

    // Configuration actions
    updateConfig: (state, action: PayloadAction<Partial<PusherState['config']>>) => {
      state.config = {
        ...state.config,
        ...action.payload,
      };
    },

    toggleConnectionStatus: (state) => {
      state.showConnectionStatus = !state.showConnectionStatus;
    },

    toggleDebugMode: (state) => {
      state.debugMode = !state.debugMode;
    },

    // Fallback actions
    enableFallbackMode: (state, action: PayloadAction<number>) => {
      state.fallbackMode = true;
      state.pollingInterval = action.payload;
      state.connectionState = PusherConnectionState.POLLING;
    },

    disableFallbackMode: (state) => {
      state.fallbackMode = false;
      state.pollingInterval = null;
    },

    // Presence channel actions
    updatePresenceMembers: (state, action: PayloadAction<{
      channel: string;
      count: number;
    }>) => {
      const { channel, count } = action.payload;
      if (state.channels[channel]) {
        state.channels[channel].members = count;
      }
    },

    // Reset actions
    resetPusherState: () => initialState,

    resetMetrics: (state) => {
      state.metrics = initialState.metrics;
    },
  },
});

// Export actions
export const {
  setConnectionStatus,
  setConnectionError,
  setSocketId,
  subscribeToChannel,
  channelSubscribed,
  channelUnsubscribed,
  setActiveChannel,
  addChannelEvent,
  addEvent,
  queueEvent,
  processEventQueue,
  clearEvents,
  updateMetrics,
  incrementConnectionAttempts,
  incrementReconnectCount,
  incrementMessagesSent,
  updateConfig,
  toggleConnectionStatus,
  toggleDebugMode,
  enableFallbackMode,
  disableFallbackMode,
  updatePresenceMembers,
  resetPusherState,
  resetMetrics,
} = pusherSlice.actions;

// Export reducer
export default pusherSlice.reducer;

// Selectors
export const selectPusherState = (state: { pusher: PusherState }) => state.pusher;
export const selectConnectionState = (state: { pusher: PusherState }) => state.pusher.connectionState;
export const selectIsConnected = (state: { pusher: PusherState }) =>
  state.pusher.connectionState === PusherConnectionState.CONNECTED;
export const selectConnectionError = (state: { pusher: PusherState }) => state.pusher.connectionError;
export const selectSocketId = (state: { pusher: PusherState }) => state.pusher.socketId;
export const selectChannels = (state: { pusher: PusherState }) => state.pusher.channels;
export const selectActiveChannel = (state: { pusher: PusherState }) => {
  const channelName = state.pusher.activeChannel;
  return channelName ? state.pusher.channels[channelName] : null;
};
export const selectEvents = (state: { pusher: PusherState }) => state.pusher.events;
export const selectEventQueue = (state: { pusher: PusherState }) => state.pusher.eventQueue;
export const selectMetrics = (state: { pusher: PusherState }) => state.pusher.metrics;
export const selectConfig = (state: { pusher: PusherState }) => state.pusher.config;
export const selectIsFallbackMode = (state: { pusher: PusherState }) => state.pusher.fallbackMode;
export const selectShowConnectionStatus = (state: { pusher: PusherState }) => state.pusher.showConnectionStatus;
export const selectDebugMode = (state: { pusher: PusherState }) => state.pusher.debugMode;

// Computed selectors
export const selectConnectionHealth = (state: { pusher: PusherState }) => {
  const { metrics } = state.pusher;
  const successRate = metrics.connectionAttempts > 0
    ? metrics.successfulConnections / metrics.connectionAttempts
    : 0;

  return {
    successRate,
    isHealthy: successRate > 0.8,
    averageLatency: metrics.averageLatency,
    reconnectCount: metrics.reconnectCount,
  };
};

export const selectSubscribedChannels = (state: { pusher: PusherState }) =>
  Object.values(state.pusher.channels).filter(channel => channel.subscribed);

export const selectChannelByName = (channelName: string) => (state: { pusher: PusherState }) =>
  state.pusher.channels[channelName] || null;