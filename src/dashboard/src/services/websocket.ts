/**
 * Pusher Service for ToolboxAI Dashboard
 *
 * Manages Pusher connections, channel subscriptions, message handling,
 * and provides a robust real-time communication layer using Pusher.
 */

import Pusher, { Channel, PresenceChannel } from 'pusher-js';
import { AUTH_TOKEN_KEY, AUTH_REFRESH_TOKEN_KEY, WS_CONFIG, WS_URL } from '../config';
import {
  MessageAcknowledgment,
  WebSocketChannel,
  WebSocketConnectionOptions,
  WebSocketError,
  WebSocketErrorHandler,
  WebSocketEventHandler,
  WebSocketMessage,
  WebSocketMessageType,
  WebSocketState,
  WebSocketStateHandler,
  WebSocketStats,
  WebSocketSubscription,
} from '../types/websocket';
import ApiClient from './api';

export class PusherService {
  private static instance: PusherService | null = null;
  private pusher: Pusher | null = null;
  private options: WebSocketConnectionOptions;
  private state: WebSocketState = WebSocketState.DISCONNECTED;
  private channels: Map<string, Channel | PresenceChannel> = new Map();
  private subscriptions: Map<string, Set<WebSocketSubscription>> = new Map();
  private messageHandlers: Map<string, Set<WebSocketEventHandler>> = new Map();
  private stateHandlers: Set<WebSocketStateHandler> = new Set();
  private errorHandlers: Set<WebSocketErrorHandler> = new Set();
  private currentToken: string | undefined;
  private apiClient: ApiClient | null = null;
  private connectionStatusCallbacks: Set<(status: WebSocketState) => void> = new Set();
  private stats: WebSocketStats;

  constructor(options: Partial<WebSocketConnectionOptions> = {}) {
    this.options = {
      url: options.url || 'http://localhost:8008',
      reconnect: options.reconnect !== false,
      reconnectInterval: options.reconnectInterval || WS_CONFIG.reconnectInterval,
      maxReconnectAttempts: options.maxReconnectAttempts || WS_CONFIG.maxReconnectAttempts,
      heartbeatInterval: options.heartbeatInterval || WS_CONFIG.heartbeatInterval,
      debug: options.debug || false,
      ...options,
    };

    // Lazy initialization to avoid circular dependency issues in tests
    this.apiClient = null;

    this.stats = {
      connectionState: WebSocketState.DISCONNECTED,
      messagesSent: 0,
      messagesReceived: 0,
      reconnectAttempts: 0,
      bytesReceived: 0,
      bytesSent: 0,
    };
  }

  /**
   * Get singleton instance of PusherService
   */
  public static getInstance(options?: Partial<WebSocketConnectionOptions>): PusherService {
    if (!PusherService.instance) {
      PusherService.instance = new PusherService(options);
    }
    return PusherService.instance;
  }

  /**
   * Connect to Pusher with enhanced JWT authentication
   */
  public async connect(token?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        if (this.state === WebSocketState.CONNECTED) {
          this.log('Already connected');
          resolve();
          return;
        }

        this.setState(WebSocketState.CONNECTING);

        // Get authentication token and validate
        const authToken = token || this.getAuthToken();
        if (!authToken) {
          this.log('No authentication token available');
          this.setState(WebSocketState.DISCONNECTED);
          reject(new Error('Authentication token required'));
          return;
        }

        this.currentToken = authToken;
        this.scheduleTokenRefresh(authToken);

        this.log(`Connecting to Pusher with token: ${authToken.substring(0, 20)}...`);

        // Initialize Pusher with configuration
        this.pusher = new Pusher(process.env.VITE_PUSHER_KEY || 'your-pusher-key', {
          wsHost: process.env.VITE_PUSHER_HOST || 'localhost',
          wsPort: parseInt(process.env.VITE_PUSHER_PORT || '6001'),
          wssPort: parseInt(process.env.VITE_PUSHER_PORT || '6001'),
          forceTLS: process.env.VITE_PUSHER_SCHEME === 'https',
          enabledTransports: ['ws', 'wss'],
          disabledTransports: [],
          cluster: process.env.VITE_PUSHER_CLUSTER || 'mt1',
          authEndpoint: `${this.options.url}/api/broadcasting/auth`,
          auth: {
            headers: {
              Authorization: `Bearer ${authToken}`,
            },
          },
        });

        // Setup Pusher event handlers
        this.setupPusherHandlers();

        // Connection success handler
        const connectHandler = () => {
          this.log('Connected successfully to Pusher');
          this.setState(WebSocketState.CONNECTED);
          this.stats.reconnectAttempts = 0;
          this.options.onConnect?.();
          resolve();
        };

        // Connection error handler
        const errorHandler = (error: Error | unknown) => {
          this.log('Pusher connection failed:', error);
          this.pusher?.unbind('pusher:connection_established', connectHandler);
          this.pusher?.unbind('pusher:error', errorHandler);

          // Handle different types of errors
          let errorMessage = 'Connection failed';
          if (error && typeof error === 'object') {
            if (error.message) {
              errorMessage = error.message;
            } else if (error.description) {
              errorMessage = error.description;
            } else if (error.type) {
              errorMessage = `Connection error: ${error.type}`;
            }
          } else if (typeof error === 'string') {
            errorMessage = error;
          }

          this.handleError({
            code: 'CONNECTION_FAILED',
            message: errorMessage,
            timestamp: new Date().toISOString(),
            recoverable: true,
          });
          reject(new Error(errorMessage));
        };

        this.pusher.bind('pusher:connection_established', connectHandler);
        this.pusher.bind('pusher:error', errorHandler);
      } catch (error) {
        this.handleError({
          code: 'CONNECTION_ERROR',
          message: error instanceof Error ? error.message : 'Unknown error',
          timestamp: new Date().toISOString(),
          recoverable: true,
        });
        reject(error);
      }
    });
  }

  /**
   * Disconnect from Pusher
   */
  public disconnect(reason?: string): void {
    this.log('Disconnecting:', reason);
    this.setState(WebSocketState.DISCONNECTING);

    // Unbind all Pusher events and disconnect
    if (this.pusher) {
      this.pusher.unbind_all();
      this.pusher.disconnect();
      this.pusher = null;
    }

    // Clear all channels
    this.channels.clear();

    this.setState(WebSocketState.DISCONNECTED);
    this.options.onDisconnect?.(reason);
  }

  /**
   * Send a message through Pusher channel
   */
  public send<T = unknown>(
    type: WebSocketMessageType,
    payload?: T,
    options: {
      channel?: string;
      awaitAcknowledgment?: boolean;
      timeout?: number;
    } = {}
  ): Promise<MessageAcknowledgment | void> {
    return new Promise((resolve, reject) => {
      const message: WebSocketMessage<T> = {
        type,
        payload,
        channel: options.channel,
        timestamp: new Date().toISOString(),
        messageId: this.generateMessageId(),
      };

      if (this.state !== WebSocketState.CONNECTED) {
        this.log('Not connected, cannot send message:', message);
        reject(new Error('Not connected to Pusher'));
        return;
      }

      try {
        const channelName = options.channel || 'general';
        const channel = this.getChannel(channelName);

        if (!channel) {
          reject(new Error(`Channel ${channelName} not subscribed`));
          return;
        }

        // For Pusher, we trigger client events or make HTTP requests to server
        // This example uses client events for private/presence channels
        if (channelName.startsWith('private-') || channelName.startsWith('presence-')) {
          (channel as Channel).trigger(`client-${type}`, {
            ...message,
            payload
          });

          this.stats.messagesSent++;
          this.stats.bytesSent = (this.stats.bytesSent || 0) + JSON.stringify(message).length;

          resolve();
        } else {
          // For public channels, we need to make HTTP request to server to trigger event
          this.sendToServer(message).then(() => {
            this.stats.messagesSent++;
            this.stats.bytesSent = (this.stats.bytesSent || 0) + JSON.stringify(message).length;
            resolve();
          }).catch(reject);
        }
      } catch (error) {
        this.handleError({
          code: 'SEND_ERROR',
          message: error instanceof Error ? error.message : 'Failed to send message',
          timestamp: new Date().toISOString(),
          details: { message, error },
          recoverable: true,
        });
        reject(error);
      }
    });
  }

  /**
   * Subscribe to a channel
   */
  public subscribe(
    channel: string | WebSocketChannel,
    handler: WebSocketEventHandler,
    filter?: (message: WebSocketMessage) => boolean
  ): string {
    // Validate and sanitize channel parameter to prevent NoSQL injection
    const sanitizedChannel = this.sanitizeChannel(channel);

    const subscription: WebSocketSubscription = {
      channel: sanitizedChannel,
      handler,
      filter,
      subscriptionId: this.generateSubscriptionId(),
    };

    if (!this.subscriptions.has(sanitizedChannel)) {
      this.subscriptions.set(sanitizedChannel, new Set());

      // Subscribe to Pusher channel
      if (this.state === WebSocketState.CONNECTED && this.pusher) {
        const pusherChannel = this.getChannel(sanitizedChannel);
        if (pusherChannel) {
          // Bind to all events on this channel
          pusherChannel.bind_global((eventName: string, data: unknown) => {
            const message: WebSocketMessage = {
              type: eventName as WebSocketMessageType,
              payload: data,
              channel: sanitizedChannel,
              timestamp: new Date().toISOString(),
            };

            // Handle message with all subscriptions for this channel
            const subs = this.subscriptions.get(sanitizedChannel);
            if (subs) {
              for (const sub of subs) {
                if (!sub.filter || sub.filter(message)) {
                  sub.handler(data);
                  this.stats.messagesReceived++;
                }
              }
            }
          });
        }
      }
    }

    const channelSubs = this.subscriptions.get(sanitizedChannel);
    if (channelSubs) {
      channelSubs.add(subscription);
    }
    this.log(`Subscribed to channel: ${sanitizedChannel}`);

    return subscription.subscriptionId!;
  }

  private sanitizeChannel(channel: string | WebSocketChannel): string {
    const channelStr = String(channel);
    // Remove potentially dangerous characters and limit length
    return channelStr.replace(/[^a-zA-Z0-9_-]/g, '').substring(0, 100);
  }

  /**
   * Unsubscribe from a channel
   */
  public unsubscribe(subscriptionId: string): void {
    for (const [channel, subs] of this.subscriptions.entries()) {
      const subscription = Array.from(subs).find((s) => s.subscriptionId === subscriptionId);
      if (subscription) {
        subs.delete(subscription);

        // If no more subscriptions for this channel, unsubscribe from Pusher
        if (subs.size === 0) {
          this.subscriptions.delete(channel);
          if (this.state === WebSocketState.CONNECTED && this.pusher) {
            const pusherChannel = this.channels.get(channel);
            if (pusherChannel) {
              this.pusher.unsubscribe(channel);
              this.channels.delete(channel);
            }
          }
        }

        this.log(`Unsubscribed from channel: ${channel}`);
        return;
      }
    }
  }

  /**
   * Register a message type handler
   */
  public on(type: WebSocketMessageType | string, handler: WebSocketEventHandler): void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, new Set());
    }
    const handlers = this.messageHandlers.get(type);
    if (handlers) {
      handlers.add(handler);
    }
  }

  /**
   * Remove a message type handler
   */
  public off(type: WebSocketMessageType | string, handler: WebSocketEventHandler): void {
    this.messageHandlers.get(type)?.delete(handler);
  }

  /**
   * Register a state change handler
   */
  public onStateChange(handler: WebSocketStateHandler): () => void {
    this.stateHandlers.add(handler);
    return () => this.stateHandlers.delete(handler);
  }

  /**
   * Register an error handler
   */
  public onError(handler: WebSocketErrorHandler): () => void {
    this.errorHandlers.add(handler);
    return () => this.errorHandlers.delete(handler);
  }

  /**
   * Get current connection state
   */
  public getState(): WebSocketState {
    return this.state;
  }

  /**
   * Get connection statistics
   */
  public getStats(): WebSocketStats {
    return { ...this.stats };
  }

  /**
   * Check if connected
   */
  public isConnected(): boolean {
    return this.state === WebSocketState.CONNECTED;
  }


  /**
   * Refresh token and reconnect
   */
  public async refreshTokenAndReconnect(): Promise<void> {
    try {
      const newToken = await this.refreshTokenWithAPI();
      if (newToken) {
        this.disconnect('Token refresh');
        await this.connect(newToken);
      }
    } catch (error) {
      this.log('Token refresh failed:', error);
      throw error;
    }
  }

  // Private methods

  private setupPusherHandlers(): void {
    if (!this.pusher) return;

    // Connection state handlers
    this.pusher.connection.bind('state_change', (states: { previous: string; current: string }) => {
      this.log(`Pusher connection state changed: ${states.previous} -> ${states.current}`);

      switch (states.current) {
        case 'connected':
          this.setState(WebSocketState.CONNECTED);
          this.resubscribeChannels();
          break;
        case 'connecting':
          this.setState(WebSocketState.CONNECTING);
          break;
        case 'disconnected':
          this.setState(WebSocketState.DISCONNECTED);
          break;
        case 'unavailable':
          this.setState(WebSocketState.ERROR);
          break;
      }
    });

    // Connection established
    this.pusher.connection.bind('connected', () => {
      this.log('Pusher connected successfully');
      this.stats.reconnectAttempts = 0;
      this.setState(WebSocketState.CONNECTED);
    });

    // Connection errors
    this.pusher.connection.bind('error', (error: { type: string; error: { message: string } }) => {
      this.log('Pusher connection error:', error);
      this.handleError({
        code: 'PUSHER_ERROR',
        message: error.error?.message || 'Pusher connection error',
        timestamp: new Date().toISOString(),
        recoverable: true,
      });
    });

    // Disconnected
    this.pusher.connection.bind('disconnected', () => {
      this.log('Pusher disconnected');
      this.setState(WebSocketState.DISCONNECTED);
    });

    // Failed to connect
    this.pusher.connection.bind('failed', () => {
      this.log('Pusher connection failed');
      this.setState(WebSocketState.ERROR);
      this.handleError({
        code: 'CONNECTION_FAILED',
        message: 'Failed to connect to Pusher',
        timestamp: new Date().toISOString(),
        recoverable: true,
      });
    });
  }

  private handleMessage(message: WebSocketMessage): void {
    this.stats.messagesReceived++;
    this.stats.lastMessageAt = new Date().toISOString();
    this.stats.bytesReceived = (this.stats.bytesReceived || 0) + JSON.stringify(message).length;

    this.log('Received message:', message.type);

    // Handle by message type
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(message.payload);
        } catch (error) {
          this.log('Handler error:', error);
        }
      });
    }

    // Handle channel subscriptions
    if (message.channel) {
      const subscriptions = this.subscriptions.get(message.channel);
      if (subscriptions) {
        subscriptions.forEach((sub) => {
          if (!sub.filter || sub.filter(message)) {
            try {
              sub.handler(message);
            } catch (error) {
              this.log('Subscription handler error:', error);
            }
          }
        });
      }
    }

    // Trigger general message handler
    this.options.onMessage?.(message);
  }

  private handleDisconnect(reason: string): void {
    this.log('Disconnected:', reason);
    const previousState = this.state;
    this.setState(WebSocketState.DISCONNECTED);
    this.stopHeartbeat();

    // Check if disconnection was due to authentication failure
    const isAuthError = reason === 'io server disconnect' ||
                        reason.includes('auth') ||
                        reason.includes('unauthorized') ||
                        reason.includes('401');

    this.log(`Disconnect reason: ${reason}, isAuthError: ${isAuthError}`);

    // Attempt reconnection if enabled and not an auth error
    if (
      this.options.reconnect &&
      !isAuthError &&
      previousState === WebSocketState.CONNECTED &&
      this.options.maxReconnectAttempts &&
      this.reconnectAttempts < this.options.maxReconnectAttempts
    ) {
      this.log('Attempting normal reconnection...');
      this.reconnect();
    } else if (isAuthError) {
      // Try to refresh token and reconnect
      this.log('Authentication error detected, attempting token refresh...');
      this.handleTokenExpiration();
    } else {
      this.log('Not attempting reconnection');
      this.options.onDisconnect?.(reason);
    }
  }

  private handleError(error: WebSocketError): void {
    this.log('Error:', error);

    // Notify error handlers
    this.errorHandlers.forEach((handler) => {
      try {
        handler(error);
      } catch (e) {
        console.error('Error handler failed:', e);
      }
    });

    // Trigger options error handler
    this.options.onError?.(error);

    // Attempt recovery if error is recoverable
    if (error.recoverable && this.options.reconnect) {
      this.reconnect();
    }
  }

  private async reconnect(): Promise<void> {
    if (this.reconnectTimer) return;

    this.reconnectAttempts++;
    this.setState(WebSocketState.RECONNECTING);

    const delay = Math.min(
      (this.options.reconnectInterval || 5000) * Math.pow(2, this.reconnectAttempts - 1),
      30000 // Max 30 seconds
    );

    this.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimer = setTimeout(async () => {
      this.reconnectTimer = null;
      try {
        // Try to refresh token before reconnecting
        const newToken = await this.refreshTokenBeforeReconnect();
        if (newToken) {
          await this.connect(newToken);
        } else {
          await this.connect();
        }
      } catch (error) {
        this.log('Reconnection failed:', error);
        if (this.reconnectAttempts < this.options.maxReconnectAttempts!) {
          this.reconnect();
        } else {
          this.setState(WebSocketState.ERROR);
          this.handleError({
            code: 'MAX_RECONNECT_ATTEMPTS',
            message: 'Maximum reconnection attempts reached',
            timestamp: new Date().toISOString(),
            recoverable: false,
          });
        }
      }
    }, delay) as unknown;
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();

    this.heartbeatTimer = setInterval(() => {
      if (this.state === WebSocketState.CONNECTED) {
        const pingTime = Date.now();
        this.send(WebSocketMessageType.PING, { timestamp: pingTime });
      }
    }, this.options.heartbeatInterval!) as unknown;
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private updateLatency(): void {
    // This would be implemented with actual ping/pong timing
    this.stats.latency = 0;
  }

  private queueMessage(
    message: WebSocketMessage,
    onSuccess?: () => void,
    onFailure?: (error: Error) => void
  ): void {
    this.messageQueue.push({
      message,
      timestamp: Date.now(),
      attempts: 0,
      maxAttempts: 3,
      onSuccess,
      onFailure,
    });

    this.log(`Message queued (${this.messageQueue.length} in queue)`);
  }

  private async flushMessageQueue(): Promise<void> {
    if (this.messageQueue.length === 0) return;

    this.log(`Flushing ${this.messageQueue.length} queued messages`);
    const queue = [...this.messageQueue];
    this.messageQueue = [];

    for (const item of queue) {
      try {
        await this.send(item.message.type, item.message.payload, {
          channel: item.message.channel,
        });
        item.onSuccess?.();
      } catch (error) {
        item.attempts++;
        if (item.attempts < item.maxAttempts) {
          this.messageQueue.push(item);
        } else {
          item.onFailure?.(error as Error);
        }
      }
    }
  }

  private resubscribeChannels(): void {
    const channels = Array.from(this.subscriptions.keys());
    if (channels.length > 0) {
      this.send(WebSocketMessageType.SUBSCRIBE, { channels });
      this.log(`Resubscribed to ${channels.length} channels`);
    }
  }

  private setState(newState: WebSocketState): void {
    const previousState = this.state;
    if (previousState === newState) return;

    this.state = newState;
    this.stats.connectionState = newState;

    if (newState === WebSocketState.CONNECTED) {
      this.stats.connectedAt = new Date().toISOString();
      this.stats.reconnectAttempts = this.reconnectAttempts;
    }

    // Notify state handlers
    this.stateHandlers.forEach((handler) => {
      try {
        handler(newState, previousState);
      } catch (error) {
        this.log('State handler error:', error);
      }
    });

    // Notify connection status callbacks
    this.connectionStatusCallbacks.forEach((callback) => {
      try {
        callback(newState);
      } catch (error) {
        this.log('Connection status callback error:', error);
      }
    });
  }

  private getAuthToken(): string | undefined {
    // Get token from localStorage using the AUTH_TOKEN_KEY constant
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    this.log(`Retrieved auth token from localStorage (${AUTH_TOKEN_KEY}):`, token ? `${token.substring(0, 20)}...` : 'null');
    return token || undefined;
  }

  private generateClientId(): string {
    return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateMessageId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateSubscriptionId(): string {
    return `sub_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private async handleTokenExpiration(): Promise<void> {
    this.log('Token expired, attempting to refresh');

    try {
      // Try to refresh the token using the refresh token
      const newToken = await this.refreshTokenWithAPI();

      if (newToken) {
        this.currentToken = newToken;
        localStorage.setItem(AUTH_TOKEN_KEY, newToken);

        // Reconnect with new token
        this.disconnect('Token refreshed');
        await this.connect(newToken);

        // Notify callbacks
        this.tokenRefreshCallbacks.forEach((callback) => callback());
      } else {
        throw new Error('Failed to refresh token');
      }
    } catch (error) {
      this.log('Token refresh failed:', error);
      this.handleError({
        code: 'TOKEN_REFRESH_FAILED',
        message: 'Authentication token refresh failed. Please login again.',
        timestamp: new Date().toISOString(),
        recoverable: false,
      });

      // Clear tokens and redirect to login
      localStorage.removeItem(AUTH_TOKEN_KEY);
      localStorage.removeItem(AUTH_REFRESH_TOKEN_KEY);
      setTimeout(() => {
        window.location.href = '/login';
      }, 2000);
    }
  }

  public refreshToken(newToken: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.socket || this.state !== WebSocketState.CONNECTED) {
        reject(new Error('Not connected'));
        return;
      }

      this.currentToken = newToken;

      this.socket.emit('refresh_token', { token: newToken }, (ack: { success?: boolean; error?: string }) => {
        if (ack?.success) {
          this.log('Token refresh successful');
          resolve();
        } else {
          this.log('Token refresh failed:', ack?.error);
          reject(new Error(ack?.error || 'Token refresh failed'));
        }
      });
    });
  }

  public onTokenRefresh(callback: () => void): () => void {
    this.tokenRefreshCallbacks.add(callback);
    return () => this.tokenRefreshCallbacks.delete(callback);
  }

  /**
   * Register a connection status callback
   */
  public onConnectionStatusChange(callback: (status: WebSocketState) => void): () => void {
    this.connectionStatusCallbacks.add(callback);
    // Immediately call with current status
    callback(this.state);
    return () => this.connectionStatusCallbacks.delete(callback);
  }

  /**
   * Schedule automatic token refresh before expiry
   */
  private scheduleTokenRefresh(token: string): void {
    this.clearTokenRefreshTimer();

    try {
      // Parse JWT to get expiry time
      const payload = JSON.parse(atob(token.split('.')[1]));
      const expiryTime = payload.exp * 1000; // Convert to milliseconds
      this.tokenExpiryTime = expiryTime;

      // Schedule refresh 5 minutes before expiry
      const refreshTime = expiryTime - Date.now() - (5 * 60 * 1000);

      if (refreshTime > 0) {
        this.tokenRefreshTimer = setTimeout(() => {
          this.handleTokenExpiration();
        }, refreshTime) as unknown;

        this.log(`Token refresh scheduled for ${new Date(expiryTime - 5 * 60 * 1000).toISOString()}`);
      }
    } catch (error) {
      this.log('Failed to parse token expiry:', error);
    }
  }

  /**
   * Clear token refresh timer
   */
  private clearTokenRefreshTimer(): void {
    if (this.tokenRefreshTimer) {
      clearTimeout(this.tokenRefreshTimer);
      this.tokenRefreshTimer = null;
    }
  }

  /**
   * Get or create API client instance
   */
  private getApiClient(): ApiClient {
    if (!this.apiClient) {
      this.apiClient = new ApiClient();
    }
    return this.apiClient;
  }

  /**
   * Refresh token using the API client
   */
  private async refreshTokenWithAPI(): Promise<string | null> {
    try {
      const refreshToken = localStorage.getItem(AUTH_REFRESH_TOKEN_KEY);
      this.log(`Attempting token refresh with refresh token: ${refreshToken ? `${refreshToken.substring(0, 20)}...` : 'null'}`);

      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await this.getApiClient().refreshToken(refreshToken);
      this.log('Token refresh response:', response);

      if (response && response.accessToken) {
        localStorage.setItem(AUTH_TOKEN_KEY, response.accessToken);
        if (response.refreshToken) {
          localStorage.setItem(AUTH_REFRESH_TOKEN_KEY, response.refreshToken);
        }
        this.log(`Token refreshed successfully: ${response.accessToken.substring(0, 20)}...`);
        return response.accessToken;
      }
      this.log('Token refresh failed: no access token in response');
      return null;
    } catch (error) {
      this.log('API token refresh failed:', error);
      return null;
    }
  }


  /**
   * Refresh token before reconnection attempt
   */
  private async refreshTokenBeforeReconnect(): Promise<string | null> {
    // Check if current token is still valid
    if (this.tokenExpiryTime && Date.now() < this.tokenExpiryTime - 60000) {
      return this.currentToken || null;
    }

    // Try to refresh the token
    return await this.refreshTokenWithAPI();
  }

  /**
   * Get or create a Pusher channel
   */
  private getChannel(channelName: string): Channel | PresenceChannel | null {
    if (!this.pusher) return null;

    if (this.channels.has(channelName)) {
      return this.channels.get(channelName)!;
    }

    let channel: Channel | PresenceChannel;
    if (channelName.startsWith('presence-')) {
      channel = this.pusher.subscribe(channelName) as PresenceChannel;
    } else {
      channel = this.pusher.subscribe(channelName);
    }

    this.channels.set(channelName, channel);
    return channel;
  }

  /**
   * Send message to server via HTTP endpoint
   */
  private async sendToServer(message: WebSocketMessage): Promise<void> {
    if (!this.apiClient) {
      this.apiClient = new ApiClient();
    }

    try {
      await this.apiClient.request({
        method: 'POST',
        url: '/api/pusher/trigger',
        data: message,
        headers: {
          'Authorization': `Bearer ${this.currentToken}`,
          'Content-Type': 'application/json',
        },
      });
    } catch (error) {
      throw new Error(`Failed to send message to server: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }



  private log(...args: unknown[]): void {
    if (this.options.debug) {
      console.error('[Pusher]', ...args);
    }
  }
}

// Create singleton instance with URL from config and debug enabled
export const pusherService = new PusherService({
  url: WS_URL,
  debug: true, // Enable debug logging
  reconnect: true,
  maxReconnectAttempts: 5,
  reconnectInterval: 3000,
  heartbeatInterval: 30000
});

// Export convenience functions (backward compatibility with WebSocket naming)
export const connectWebSocket = (token?: string) => pusherService.connect(token);
export const disconnectWebSocket = (reason?: string) => pusherService.disconnect(reason);
export const refreshWebSocketToken = () => pusherService.refreshTokenAndReconnect();
export const sendWebSocketMessage = <T = unknown>(
  type: WebSocketMessageType,
  payload?: T,
  options?: { channel?: string; awaitAcknowledgment?: boolean; timeout?: number }
) => pusherService.send(type, payload, options);
export const subscribeToChannel = (
  channel: string | WebSocketChannel,
  handler: WebSocketEventHandler,
  filter?: (message: WebSocketMessage) => boolean
) => pusherService.subscribe(channel, handler, filter);
export const unsubscribeFromChannel = (subscriptionId: string) =>
  pusherService.unsubscribe(subscriptionId);
export const getWebSocketState = () => pusherService.getState();
export const isWebSocketConnected = () => pusherService.isConnected();
export const onWebSocketConnectionStatusChange = (callback: (status: WebSocketState) => void) =>
<<<<<<< Current (Your changes)
  websocketService.onConnectionStatusChange(callback);
=======
  pusherService.onConnectionStatusChange(callback);

// Export both for backward compatibility
export const websocketService = pusherService;
export const WebSocketService = PusherService;

export default pusherService;
>>>>>>> Incoming (Background Agent changes)
