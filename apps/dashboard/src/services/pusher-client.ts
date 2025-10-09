/**
 * Pusher Client Service
 * Manages real-time communication with exponential backoff and fallback to polling
 * @module pusher-client
 * @version 1.0.0
 * @since 2025-09-26
 */

import Pusher, { type Channel, type PresenceChannel } from 'pusher-js';
import { store } from '../store';
import { setConnectionStatus, setConnectionError } from '../store/slices/pusherSlice';
import { config } from '../config';

// Types
export interface PusherConfig {
  key: string;
  cluster: string;
  authEndpoint: string;
  enabledTransports?: ('ws' | 'wss' | 'xhr_polling' | 'xhr_streaming')[];
  disableStats?: boolean;
  forceTLS?: boolean;
}

export interface ConnectionState {
  isConnected: boolean;
  connectionAttempts: number;
  lastError?: string;
  fallbackToPolling: boolean;
}

export interface ChannelSubscription {
  channel: Channel | PresenceChannel;
  eventHandlers: Map<string, Set<(payload: unknown) => void>>;
  subscriptionCount: number;
}

/**
 * PusherClient - Singleton class managing Pusher connections
 */
class PusherClient {
  private static instance: PusherClient;
  private pusher: Pusher | null = null;
  private channels: Map<string, ChannelSubscription> = new Map();
  private connectionState: ConnectionState = {
    isConnected: false,
    connectionAttempts: 0,
    fallbackToPolling: false,
  };
  private reconnectTimer: NodeJS.Timeout | null = null;
  private pollingInterval: NodeJS.Timeout | null = null;
  private maxReconnectAttempts = 5;
  private baseReconnectDelay = 1000; // 1 second
  private userId: string | null = null;

  private constructor() {
    // Private constructor for singleton pattern
  }

  /**
   * Get singleton instance
   */
  public static getInstance(): PusherClient {
    if (!PusherClient.instance) {
      PusherClient.instance = new PusherClient();
    }
    return PusherClient.instance;
  }

  /**
   * Initialize Pusher connection
   */
  public initialize(userId: string, authToken: string): void {
    if (this.pusher && this.userId === userId) {
      console.log('Pusher already initialized for user:', userId);
      return;
    }

    this.userId = userId;
    this.disconnect(); // Clean up any existing connection

    const pusherConfig: PusherConfig = {
      key: config.pusher.key,
      cluster: config.pusher.cluster,
      authEndpoint: config.pusher.authEndpoint,
      enabledTransports: ['ws', 'wss', 'xhr_polling'],
      disableStats: true,
      forceTLS: true,
    };

    try {
      this.pusher = new Pusher(pusherConfig.key, {
        cluster: pusherConfig.cluster,
        auth: {
          endpoint: pusherConfig.authEndpoint,
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json',
          },
        },
        enabledTransports: pusherConfig.enabledTransports,
        disableStats: pusherConfig.disableStats,
        forceTLS: pusherConfig.forceTLS,
      });

      this.setupConnectionHandlers();
      this.subscribeToUserChannel(userId);

    } catch (error) {
      console.error('Failed to initialize Pusher:', error);
      this.handleConnectionError(error);
    }
  }

  /**
   * Setup connection event handlers
   */
  private setupConnectionHandlers(): void {
    if (!this.pusher) return;

    // Connection successful
    this.pusher.connection.bind('connected', () => {
      console.log('✅ Pusher connected successfully');
      this.connectionState.isConnected = true;
      this.connectionState.connectionAttempts = 0;
      this.connectionState.fallbackToPolling = false;

      store.dispatch(setConnectionStatus('connected'));

      // Clear any reconnect timers
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }

      // Stop polling if it was active
      this.stopPolling();
    });

    // Connection failed
    this.pusher.connection.bind('failed', () => {
      console.error('❌ Pusher connection failed');
      this.handleConnectionError(new Error('Connection failed'));
    });

    // Connection error
    this.pusher.connection.bind('error', (error: any) => {
      console.error('⚠️ Pusher connection error:', error);
      this.handleConnectionError(error);
    });

    // Disconnected
    this.pusher.connection.bind('disconnected', () => {
      console.log('🔌 Pusher disconnected');
      this.connectionState.isConnected = false;
      store.dispatch(setConnectionStatus('disconnected'));
      this.attemptReconnect();
    });

    // State change
    this.pusher.connection.bind('state_change', (states: any) => {
      console.log('Pusher state change:', states.previous, '→', states.current);
      store.dispatch(setConnectionStatus(states.current));
    });
  }

  /**
   * Handle connection errors with exponential backoff
   */
  private handleConnectionError(error: any): void {
    this.connectionState.isConnected = false;
    this.connectionState.lastError = error?.message || 'Unknown error';

    store.dispatch(setConnectionError(this.connectionState.lastError));

    // Increment connection attempts
    this.connectionState.connectionAttempts++;

    if (this.connectionState.connectionAttempts >= this.maxReconnectAttempts) {
      console.warn('Max reconnection attempts reached. Falling back to polling.');
      this.fallbackToPolling();
    } else {
      this.attemptReconnect();
    }
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  private attemptReconnect(): void {
    if (this.reconnectTimer) return; // Already attempting to reconnect

    const delay = Math.min(
      this.baseReconnectDelay * Math.pow(2, this.connectionState.connectionAttempts),
      30000 // Max 30 seconds
    );

    console.log(`Attempting reconnection in ${delay}ms (attempt ${this.connectionState.connectionAttempts + 1}/${this.maxReconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      if (this.pusher && !this.connectionState.isConnected) {
        this.pusher.connect();
      }
    }, delay);
  }

  /**
   * Fallback to polling mechanism when Pusher fails
   */
  private fallbackToPolling(): void {
    console.warn('📊 Falling back to polling mechanism');
    this.connectionState.fallbackToPolling = true;
    store.dispatch(setConnectionStatus('polling'));

    // Stop trying to reconnect via Pusher
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    // Start polling for updates
    this.startPolling();
  }

  /**
   * Start polling for updates (fallback mechanism)
   */
  private startPolling(): void {
    if (this.pollingInterval) return;

    const pollInterval = 5000; // Poll every 5 seconds

    this.pollingInterval = setInterval(async () => {
      try {
        const response = await fetch('/api/v1/realtime/poll', {
          headers: {
            'Authorization': `Bearer ${store.getState().auth.token}`,
          },
        });

        if (response.ok) {
          const updates = await response.json();
          this.processPolledUpdates(updates);
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, pollInterval);

    // Also attempt to reconnect Pusher periodically
    setTimeout(() => {
      if (this.connectionState.fallbackToPolling && this.pusher) {
        console.log('Attempting to restore Pusher connection...');
        this.connectionState.connectionAttempts = 0;
        this.pusher.connect();
      }
    }, 60000); // Try every minute
  }

  /**
   * Stop polling
   */
  private stopPolling(): void {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
  }

  /**
   * Process updates received from polling
   */
  private processPolledUpdates(updates: any[]): void {
    updates.forEach(update => {
      const { channel, event, data } = update;
      const subscription = this.channels.get(channel);

      if (subscription) {
        const handlers = subscription.eventHandlers.get(event);
        if (handlers) {
          handlers.forEach(handler => {
            try {
              handler(data);
            } catch (error) {
              console.error('Error processing polled update:', error);
            }
          });
        }
      }
    });
  }

  /**
   * Subscribe to a channel
   */
  public subscribe(channelName: string): Channel | PresenceChannel | null {
    if (!this.pusher) {
      console.error('Pusher not initialized');
      return null;
    }

    // Check if already subscribed
    let subscription = this.channels.get(channelName);

    if (subscription) {
      subscription.subscriptionCount++;
      return subscription.channel;
    }

    // Subscribe to new channel
    try {
      const channel = channelName.startsWith('presence-')
        ? this.pusher.subscribe(channelName) as PresenceChannel
        : this.pusher.subscribe(channelName);

      subscription = {
        channel,
        eventHandlers: new Map(),
        subscriptionCount: 1,
      };

      this.channels.set(channelName, subscription);

      // Handle subscription success
      channel.bind('pusher:subscription_succeeded', () => {
        console.log(`✅ Subscribed to channel: ${channelName}`);
      });

      // Handle subscription error
      channel.bind('pusher:subscription_error', (error: any) => {
        console.error(`❌ Failed to subscribe to channel ${channelName}:`, error);
      });

      return channel;

    } catch (error) {
      console.error(`Failed to subscribe to channel ${channelName}:`, error);
      return null;
    }
  }

  /**
   * Unsubscribe from a channel
   */
  public unsubscribe(channelName: string): void {
    const subscription = this.channels.get(channelName);

    if (!subscription) return;

    subscription.subscriptionCount--;

    if (subscription.subscriptionCount <= 0) {
      // Unbind all events
      subscription.eventHandlers.forEach((handlers, event) => {
        handlers.forEach(handler => {
          subscription.channel.unbind(event, handler as any);
        });
      });

      // Unsubscribe from channel
      if (this.pusher) {
        this.pusher.unsubscribe(channelName);
      }

      // Remove from channels map
      this.channels.delete(channelName);

      console.log(`📤 Unsubscribed from channel: ${channelName}`);
    }
  }

  /**
   * Bind event handler to a channel
   */
  public bind(channelName: string, eventName: string, callback: (payload: unknown) => void): void {
    const subscription = this.channels.get(channelName);

    if (!subscription) {
      console.error(`Not subscribed to channel: ${channelName}`);
      return;
    }

    // Store event handler
    if (!subscription.eventHandlers.has(eventName)) {
      subscription.eventHandlers.set(eventName, new Set());
    }
    const handlers = subscription.eventHandlers.get(eventName)!;
    handlers.add(callback);
    subscription.eventHandlers.set(eventName, handlers);

    // Bind to Pusher channel
    subscription.channel.bind(eventName, callback as any);
  }

  /**
   * Unbind event handler from a channel
   */
  public unbind(channelName: string, eventName: string, callback: (payload: unknown) => void): void {
    const subscription = this.channels.get(channelName);

    if (!subscription) return;

    // Remove from stored handlers
    const handlers = subscription.eventHandlers.get(eventName);
    if (handlers) {
      handlers.delete(callback);
      if (handlers.size === 0) {
        subscription.eventHandlers.delete(eventName);
      }
    }

    // Unbind from Pusher channel
    subscription.channel.unbind(eventName, callback as any);
  }

  /**
   * Subscribe to user-specific channel
   */
  private subscribeToUserChannel(userId: string): void {
    const userChannel = `private-user-${userId}`;
    const channel = this.subscribe(userChannel);

    if (channel) {
      // Bind to user-specific events
      this.bind(userChannel, 'notification', (data: any) => {
        console.log('User notification:', data);
        // Dispatch notification to store
        store.dispatch({ type: 'notifications/add', payload: data });
      });

      this.bind(userChannel, 'update', (data: any) => {
        console.log('User update:', data);
        // Dispatch update to store
        store.dispatch({ type: 'user/update', payload: data });
      });
    }
  }

  /**
   * Trigger an event (for testing or client-side events)
   */
  public trigger(channelName: string, eventName: string, data: any): void {
    const subscription = this.channels.get(channelName);

    if (subscription && subscription.channel) {
      // Note: Client-side triggering only works for client events (prefixed with 'client-')
      if (eventName.startsWith('client-')) {
        (subscription.channel as any).trigger(eventName, data);
      } else {
        console.warn('Can only trigger client events from client side');
      }
    }
  }

  /**
   * Get connection state
   */
  public getConnectionState(): string {
    if (this.connectionState.fallbackToPolling) return 'polling';
    if (!this.pusher) return 'uninitialized';
    return this.pusher.connection.state;
  }

  /**
   * Check if connected
   */
  public isConnected(): boolean {
    return this.connectionState.isConnected || this.connectionState.fallbackToPolling;
  }

  /**
   * Disconnect and cleanup
   */
  public disconnect(): void {
    // Clear all timers
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    this.stopPolling();

    // Unsubscribe from all channels
    this.channels.forEach((subscription, channelName) => {
      if (this.pusher) {
        this.pusher.unsubscribe(channelName);
      }
    });

    this.channels.clear();

    // Disconnect Pusher
    if (this.pusher) {
      this.pusher.disconnect();
      this.pusher = null;
    }

    // Reset state
    this.connectionState = {
      isConnected: false,
      connectionAttempts: 0,
      fallbackToPolling: false,
    };

    this.userId = null;

    console.log('🔌 Pusher client disconnected and cleaned up');
  }

  /**
   * Get debug information
   */
  public getDebugInfo(): any {
    return {
      isConnected: this.connectionState.isConnected,
      connectionAttempts: this.connectionState.connectionAttempts,
      fallbackToPolling: this.connectionState.fallbackToPolling,
      lastError: this.connectionState.lastError,
      activeChannels: Array.from(this.channels.keys()),
      pusherState: this.pusher?.connection.state,
      userId: this.userId,
    };
  }
}

// Export singleton instance
export const pusherClient = PusherClient.getInstance();

// Export for testing
export { PusherClient };
