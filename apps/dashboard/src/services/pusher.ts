/**
 * Pusher Service for ToolboxAI Dashboard
 *
 * Manages Pusher connections, channel subscriptions, message handling,
 * reconnection logic, and provides a robust real-time communication layer.
 *
 * This service consolidates all real-time features using Pusher Channels,
 * replacing the legacy Socket.IO implementation.
 */
import Pusher, { Channel } from 'pusher-js';
import { AUTH_TOKEN_KEY, AUTH_REFRESH_TOKEN_KEY, WS_CONFIG, WS_URL, PUSHER_KEY, PUSHER_CLUSTER, PUSHER_AUTH_ENDPOINT } from '../config';
import { tokenRefreshManager } from '../utils/tokenRefreshManager';
import {
  MessageAcknowledgment,
  QueuedMessage,
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
import { logger } from '../utils/logger';
export class PusherService {
  private static instance: PusherService | null = null;
  private pusher: Pusher | null = null;
  private channels: Map<string, Channel> = new Map();
  private options: WebSocketConnectionOptions;
  private state: WebSocketState = WebSocketState.DISCONNECTED;
  private subscriptions: Map<string, Set<WebSocketSubscription>> = new Map();
  private messageQueue: QueuedMessage[] = [];
  private reconnectAttempts = 0;
  private reconnectTimer: number | null = null;
  private heartbeatTimer: number | null = null;
  private stats: WebSocketStats;
  private messageHandlers: Map<string, Set<WebSocketEventHandler>> = new Map();
  private stateHandlers: Set<WebSocketStateHandler> = new Set();
  private errorHandlers: Set<WebSocketErrorHandler> = new Set();
  private pendingAcknowledgments: Map<string, (ack: MessageAcknowledgment) => void> = new Map();
  private currentToken: string | undefined;
  private tokenRefreshCallbacks: Set<() => void> = new Set();
  private tokenRefreshTimer: number | null = null;
  private tokenExpiryTime: number | null = null;
  private apiClient: ApiClient | null = null;
  private connectionStatusCallbacks: Set<(status: WebSocketState) => void> = new Set();
  constructor(options: Partial<WebSocketConnectionOptions> = {}) {
    this.options = {
url: options.url || WS_URL,
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
    // Listen for token updates from the centralized token refresh manager
    tokenRefreshManager.addListener((newToken: string) => {
      this.handleTokenRefresh(newToken);
    });
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
   * Connect to WebSocket server with enhanced JWT authentication
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
        // In development mode, use a default token if none exists
        const isDevelopment = import.meta.env.MODE === 'development';
        const effectiveToken = authToken || (isDevelopment ? 'dev-token-' + Date.now() : null);
        if (!effectiveToken) {
          this.log('No authentication token available');
          this.setState(WebSocketState.DISCONNECTED);
          reject(new Error('Authentication token required'));
          return;
        }
        this.currentToken = effectiveToken;
        if (authToken) {
          this.scheduleTokenRefresh(authToken);
        }
        // Initialize Pusher (with fallback for missing config)
        if (!PUSHER_KEY || PUSHER_KEY === 'dummy-key-for-development') {
          this.log('Pusher not configured, skipping WebSocket connection');
          this.setState(WebSocketState.DISCONNECTED);
          resolve(); // Resolve without error to allow app to continue
          return;
        }
        this.pusher = new Pusher(PUSHER_KEY, {
          cluster: PUSHER_CLUSTER,
          forceTLS: true,
          authEndpoint: PUSHER_AUTH_ENDPOINT,
          auth: {
            headers: {
              Authorization: `Bearer ${effectiveToken}`,
            },
          },
          enabledTransports: ['ws', 'wss'],
          disableStats: true,
        });
        // Bind connection events
        this.pusher.connection.bind('connected', () => {
          this.log('Pusher connected');
          this.setState(WebSocketState.CONNECTED);
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.flushMessageQueue();
          this.resubscribeChannels();
          this.options.onConnect?.();
          resolve();
        });
        this.pusher.connection.bind('error', (error: any) => {
          let errorMessage = 'Connection failed';
          if (error && typeof error === 'object') {
            errorMessage = error?.error?.data?.message || error.message || error.description || 'Connection error';
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
        });
        this.pusher.connection.bind('disconnected', () => {
          this.handleDisconnect('disconnected');
        });
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
   * Disconnect from WebSocket server
   */
  public disconnect(reason?: string): void {
    this.log('Disconnecting:', reason);
    this.setState(WebSocketState.DISCONNECTING);
    this.stopHeartbeat();
    this.clearReconnectTimer();
    this.clearTokenRefreshTimer();
    // Unbind and disconnect pusher
    try {
      this.channels.forEach((ch) => ch.unbind_all());
      this.channels.clear();
      this.pusher?.unbind_all();
      this.pusher?.disconnect();
    } catch (e) {
      // ignore
    }
    this.pusher = null;
    this.setState(WebSocketState.DISCONNECTED);
    this.options.onDisconnect?.(reason);
  }
  /**
   * Send a message through WebSocket
   */
  public send<T = any>(
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
        // Queue message if not connected
        this.queueMessage(message, resolve, reject);
        return;
      }
      try {
        // With Pusher, client cannot emit arbitrary server events.
        // Use REST API endpoint to trigger the event on the server side.
        this.getApiClient()
          .realtimeTrigger({
            channel: options.channel || 'public',
            event: 'message',
            type,
            payload,
          })
          .then((ack: any) => {
            this.stats.messagesSent++;
            this.stats.bytesSent = (this.stats.bytesSent || 0) + JSON.stringify({ type, payload }).length;
            if (options.awaitAcknowledgment) {
              resolve({ ok: true, receivedAt: new Date().toISOString(), ...ack });
            } else {
              resolve();
            }
          })
          .catch((err) => {
            throw err;
          });
        // Handle timeout
        if (options.awaitAcknowledgment && options.timeout) {
          setTimeout(() => {
            reject(new Error(`Message timeout after ${options.timeout}ms`));
          }, options.timeout);
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
    // Validate and sanitize channel parameter
    const sanitizedChannel = this.sanitizeChannel(channel);
    const subscription: WebSocketSubscription = {
      channel: sanitizedChannel,
      handler,
      filter,
      subscriptionId: this.generateSubscriptionId(),
    };
    if (!this.subscriptions.has(sanitizedChannel)) {
      this.subscriptions.set(sanitizedChannel, new Set());
      // Subscribe to Pusher channel and bind unified 'message' event
      if (this.pusher) {
        // Check if we're already subscribed to this Pusher channel
        let ch = this.channels.get(sanitizedChannel);
        if (!ch) {
          // Check Pusher's internal channel registry first
          ch = this.pusher.channel(sanitizedChannel);
          if (!ch) {
            // Only subscribe if we don't have an existing channel
            ch = this.pusher.subscribe(sanitizedChannel);
            ch.bind('message', (data: any) => {
              // Expect server to send { type, payload, channel, timestamp }
              const msg: WebSocketMessage = {
                type: data?.type,
                payload: data?.payload,
                channel: sanitizedChannel,
                timestamp: data?.timestamp || new Date().toISOString(),
                messageId: data?.messageId || this.generateMessageId(),
              };
              this.handleMessage(msg);
            });
          }
          this.channels.set(sanitizedChannel, ch);
        }
      }
    }
    const channelSubs = this.subscriptions.get(sanitizedChannel);
    if (channelSubs) {
      channelSubs.add(subscription);
    }
    logger.debug('Subscribed to channel', { channel: sanitizedChannel });
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
          const ch = this.channels.get(channel);
          try {
            ch?.unbind('message');
          } catch (_) { /* noop */ }
          if (this.pusher) {
            this.pusher.unsubscribe(channel);
          }
          this.channels.delete(channel);
        }
        logger.debug('Unsubscribed from channel', { channel });
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
  // Private methods
  private setupSocketHandlers(): void {
    // Pusher channel/event bindings are set in subscribe
    if (!this.pusher) return;
    // Handle connection state changes
    this.pusher.connection.bind('state_change', (states: any) => {
      this.log('Pusher state change:', states?.current);
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
        logger.error('Error handler failed', e);
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
    // Exponential backoff with jitter (2025 Pusher 8.3.0 best practices)
    // Start at 1 second, double each time: 1s, 2s, 4s, 8s, 16s, max 30s
    const baseDelay = 1000; // Start at 1 second
    const maxDelay = 30000; // Max 30 seconds
    // Calculate exponential delay
    const exponentialDelay = Math.min(
      baseDelay * Math.pow(2, this.reconnectAttempts - 1),
      maxDelay
    );
    // Add jitter (±25%) to prevent thundering herd
    const jitter = exponentialDelay * 0.25 * (Math.random() * 2 - 1);
    const delay = Math.round(exponentialDelay + jitter);
    this.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}, base: ${exponentialDelay}ms, jitter: ${Math.round(jitter)}ms)`);
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
        } else if (this.options.maxReconnectAttempts && this.reconnectAttempts >= this.options.maxReconnectAttempts) {
          // Only stop if maxReconnectAttempts is explicitly set
          // Pusher 8.3.0 best practice: unlimited retries by default
          this.setState(WebSocketState.ERROR);
          this.handleError({
            code: 'MAX_RECONNECT_ATTEMPTS',
            message: 'Maximum reconnection attempts reached',
            timestamp: new Date().toISOString(),
            recoverable: false,
          });
        } else {
          // Continue reconnecting indefinitely (Pusher 8.3.0 behavior)
          this.reconnect();
        }
      }
    }, delay) as any;
  }
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
  private startHeartbeat(): void {
    this.stopHeartbeat();
    // Reduce heartbeat frequency to prevent excessive API calls
    this.heartbeatTimer = setInterval(() => {
      if (this.state === WebSocketState.CONNECTED) {
        // Only send heartbeat if really needed - Pusher handles this internally
        // const pingTime = Date.now();
        // this.send(WebSocketMessageType.PING, { timestamp: pingTime });
      }
    }, this.options.heartbeatInterval! * 10) as any; // 10x less frequent
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
    if (!this.pusher) return;
    const channels = Array.from(this.subscriptions.keys());
    channels.forEach((chName) => {
      // Check if we're already subscribed to this channel
      let ch = this.pusher!.channel(chName);
      if (!ch) {
        // Only subscribe if not already subscribed
        ch = this.pusher!.subscribe(chName);
        ch.bind('message', (data: any) => {
          const msg: WebSocketMessage = {
            type: data?.type,
            payload: data?.payload,
            channel: chName,
            timestamp: data?.timestamp || new Date().toISOString(),
            messageId: data?.messageId || this.generateMessageId(),
          };
          this.handleMessage(msg);
        });
      }
      this.channels.set(chName, ch);
    });
    if (channels.length > 0) {
      this.log(`Resubscribed to ${channels.length} channel(s)`);
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
      (async () => {
        try {
        this.currentToken = newToken;
        localStorage.setItem(AUTH_TOKEN_KEY, newToken);
        if (this.state === WebSocketState.CONNECTED) {
          this.disconnect('Token refreshed');
          await this.connect(newToken);
        }
        resolve();
        } catch (error) {
          reject(error as Error);
        }
      })();
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
   * Handle token refresh from the centralized token manager
   */
  private handleTokenRefresh(newToken: string): void {
    this.log('Token refreshed by token manager');
    this.currentToken = newToken;
    // Update Pusher auth headers if connected
    if (this.pusher && this.state === WebSocketState.CONNECTED) {
      // Pusher doesn't allow updating auth headers directly,
      // but we can update the auth endpoint headers for future channel subscriptions
      this.pusher.config.auth = {
        ...this.pusher.config.auth,
        headers: {
          Authorization: `Bearer ${newToken}`,
        },
      };
    }
    // Notify any listeners about the token update
    this.tokenRefreshCallbacks.forEach(callback => callback());
  }
  /**
   * Schedule automatic token refresh before expiry
   */
  private scheduleTokenRefresh(token: string): void {
    this.clearTokenRefreshTimer();
    // Skip token refresh for dev tokens
    if (token.startsWith('dev-token-')) {
      this.log('Development token detected, skipping refresh schedule');
      return;
    }
    try {
      // Parse JWT to get expiry time
      const parts = token.split('.');
      if (parts.length !== 3) {
        this.log('Invalid JWT token format');
        return;
      }
      const payload = JSON.parse(atob(parts[1]));
      const expiryTime = payload.exp * 1000; // Convert to milliseconds
      // Validate expiry time is reasonable (not in the far future)
      const now = Date.now();
      const maxReasonableExpiry = now + (365 * 24 * 60 * 60 * 1000); // 1 year from now
      if (expiryTime > maxReasonableExpiry) {
        this.log(`Token expiry time seems invalid: ${new Date(expiryTime).toISOString()}. Using default 30 minutes.`);
        // Use a reasonable default expiry time
        this.tokenExpiryTime = now + (30 * 60 * 1000); // 30 minutes from now
      } else {
        this.tokenExpiryTime = expiryTime;
      }
      // Schedule refresh 5 minutes before expiry
      const refreshTime = this.tokenExpiryTime - now - (5 * 60 * 1000);
      if (refreshTime > 0) {
        this.tokenRefreshTimer = setTimeout(() => {
          this.handleTokenExpiration();
        }, refreshTime) as any;
        this.log(`Token refresh scheduled for ${new Date(this.tokenExpiryTime - 5 * 60 * 1000).toISOString()}`);
      } else {
        this.log('Token is already expired or expires soon, refreshing immediately');
        this.handleTokenExpiration();
      }
    } catch (error) {
      this.log('Failed to parse token expiry:', error);
      // Set a reasonable default refresh time
      this.tokenExpiryTime = Date.now() + (30 * 60 * 1000); // 30 minutes from now
      const refreshTime = 25 * 60 * 1000; // 25 minutes
      this.tokenRefreshTimer = setTimeout(() => {
        this.handleTokenExpiration();
      }, refreshTime) as any;
      this.log(`Using default token refresh in 25 minutes`);
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
   * Manually refresh token and reconnect WebSocket
   */
  public async refreshTokenAndReconnect(): Promise<void> {
    this.log('Manual token refresh requested');
    const newToken = await this.refreshTokenWithAPI();
    if (newToken) {
      this.currentToken = newToken;
      if (this.isConnected()) {
        this.log('Reconnecting with new token...');
        this.disconnect('Token refreshed manually');
        await this.connect(newToken);
      }
    } else {
      this.log('Manual token refresh failed');
      throw new Error('Failed to refresh token');
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
  private log(...args: any[]): void {
    if (this.options.debug) {
      logger.debug('[WebSocket]', ...args);
    }
  }
}
// Create singleton instance with URL from config and debug enabled
export const pusherService = new PusherService({
  url: WS_URL,
  debug: true, // Enable debug logging
  reconnect: true,
  maxReconnectAttempts: undefined, // Unlimited retries (Pusher 8.3.0 best practice)
  reconnectInterval: 1000, // Start at 1s with exponential backoff
  heartbeatInterval: 30000
});
// Export backward-compatible alias
export const websocketService = pusherService;
export const WebSocketService = PusherService;
// Export convenience functions
export const connectWebSocket = (token?: string) => pusherService.connect(token);
export const disconnectWebSocket = (reason?: string) => pusherService.disconnect(reason);
export const refreshWebSocketToken = () => pusherService.refreshTokenAndReconnect();
export const sendWebSocketMessage = <T = any>(
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
  pusherService.onConnectionStatusChange(callback);