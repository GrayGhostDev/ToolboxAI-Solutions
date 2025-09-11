/**
 * WebSocket Service for ToolboxAI Dashboard
 *
 * Manages WebSocket connections, message handling, reconnection logic,
 * and provides a robust real-time communication layer.
 */

import { io, Socket } from 'socket.io-client';
import { AUTH_TOKEN_KEY, AUTH_REFRESH_TOKEN_KEY, WS_CONFIG, WS_URL } from '../config';
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

export class WebSocketService {
  private static instance: WebSocketService | null = null;
  private socket: Socket | null = null;
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
   * Get singleton instance of WebSocketService
   */
  public static getInstance(options?: Partial<WebSocketConnectionOptions>): WebSocketService {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService(options);
    }
    return WebSocketService.instance;
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
        if (!authToken) {
          this.log('No authentication token available');
          this.setState(WebSocketState.DISCONNECTED);
          reject(new Error('Authentication token required'));
          return;
        }
        
        this.currentToken = authToken;
        this.scheduleTokenRefresh(authToken);

        // Parse URL to separate protocol and host
        const url = new URL(this.options.url);
        const protocol = url.protocol === 'wss:' ? 'https:' : 'http:';
        const socketUrl = `${protocol}//${url.host}`;

        this.log(`Connecting to WebSocket at ${socketUrl} with token: ${authToken.substring(0, 20)}...`);

        // Create socket connection with JWT authentication
        this.socket = io(socketUrl, {
          path: '/socket.io/', // Match backend socketio_path (trailing slash)
          transports: ['websocket', 'polling'], // Allow fallback to polling
          auth: { 
            token: authToken,
            type: 'Bearer'
          },
          reconnection: false, // We handle reconnection manually for better control
          timeout: 10000,
          query: {
            token: authToken, // Include token in query params as backup
            clientId: this.generateClientId(),
            timestamp: Date.now().toString(),
          },
          extraHeaders: {
            Authorization: `Bearer ${authToken}`,
          },
        });

        // Setup event handlers
        this.setupSocketHandlers();

        // Connection success handler
        const connectHandler = () => {
          this.log('Connected successfully');
          this.setState(WebSocketState.CONNECTED);
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.flushMessageQueue();
          this.options.onConnect?.();
          this.socket?.off('connect', connectHandler);
          this.socket?.off('connect_error', errorHandler);
          resolve();
        };

        // Connection error handler
        const errorHandler = (error: any) => {
          this.log('Connection failed:', error);
          this.socket?.off('connect', connectHandler);
          this.socket?.off('connect_error', errorHandler);

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

        this.socket.once('connect', connectHandler);
        this.socket.once('connect_error', errorHandler);
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

    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }

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
        // Send message
        this.socket?.emit('message', message, (ack?: MessageAcknowledgment) => {
          this.stats.messagesSent++;
          this.stats.bytesSent = (this.stats.bytesSent || 0) + JSON.stringify(message).length;

          if (options.awaitAcknowledgment && ack) {
            resolve(ack);
          } else {
            resolve();
          }
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

      // Send subscription request to server
      if (this.state === WebSocketState.CONNECTED) {
        this.send(WebSocketMessageType.SUBSCRIBE, { channels: [sanitizedChannel] });
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

        // If no more subscriptions for this channel, unsubscribe from server
        if (subs.size === 0) {
          this.subscriptions.delete(channel);
          if (this.state === WebSocketState.CONNECTED) {
            this.send(WebSocketMessageType.UNSUBSCRIBE, { channels: [channel] });
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

  // Private methods

  private setupSocketHandlers(): void {
    if (!this.socket) return;

    // Handle incoming messages
    this.socket.on('message', (message: WebSocketMessage) => {
      this.handleMessage(message);
    });

    // Handle disconnection
    this.socket.on('disconnect', (reason: string) => {
      this.handleDisconnect(reason);
    });

    // Handle errors
    this.socket.on('error', (error: any) => {
      let errorMessage = 'Socket error';
      if (error && typeof error === 'object') {
        errorMessage = error.message || error.description || 'Unknown socket error';
      } else if (typeof error === 'string') {
        errorMessage = error;
      }

      this.handleError({
        code: 'SOCKET_ERROR',
        message: errorMessage,
        timestamp: new Date().toISOString(),
        details: error,
        recoverable: true,
      });
    });

    // Handle connect_error specifically
    this.socket.on('connect_error', (error: any) => {
      let errorMessage = 'Connection error';
      if (error && typeof error === 'object') {
        errorMessage = error.message || error.description || 'Failed to connect to server';
      } else if (typeof error === 'string') {
        errorMessage = error;
      }

      this.log('Connect error:', errorMessage);
      this.handleError({
        code: 'CONNECT_ERROR',
        message: errorMessage,
        timestamp: new Date().toISOString(),
        recoverable: true,
      });
    });

    // Handle reconnection events
    this.socket.on('reconnect', (attemptNumber: number) => {
      this.log(`Reconnected after ${attemptNumber} attempts`);
      this.setState(WebSocketState.CONNECTED);
      this.reconnectAttempts = 0;
      this.resubscribeChannels();
    });

    // Handle pong messages for heartbeat
    this.socket.on('pong', () => {
      this.updateLatency();
    });

    // Handle authentication events
    this.socket.on('auth_success', (data) => {
      this.log('Authentication successful:', data);
    });

    this.socket.on('auth_failed', async (error) => {
      this.log('Authentication failed:', error);
      
      // Try to refresh token and reconnect
      try {
        const newToken = await this.refreshTokenWithAPI();
        if (newToken) {
          this.log('Token refreshed after auth failure, reconnecting...');
          this.disconnect('Token refreshed');
          await this.connect(newToken);
        } else {
          throw new Error('Token refresh failed');
        }
      } catch (refreshError) {
        this.handleError({
          code: 'AUTH_FAILED',
          message: error.message || 'Authentication failed and token refresh failed',
          timestamp: new Date().toISOString(),
          recoverable: false,
        });
      }
    });

    // Handle token refresh events
    this.socket.on('token_refreshed', (data) => {
      this.log('Token refreshed:', data);
      this.tokenRefreshCallbacks.forEach((callback) => callback());
    });

    this.socket.on('token_expired', () => {
      this.log('Token expired, attempting refresh');
      this.handleTokenExpiration();
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

    this.heartbeatTimer = setInterval(() => {
      if (this.state === WebSocketState.CONNECTED) {
        const pingTime = Date.now();
        this.send(WebSocketMessageType.PING, { timestamp: pingTime });
      }
    }, this.options.heartbeatInterval!) as any;
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

      this.socket.emit('refresh_token', { token: newToken }, (ack: any) => {
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
        }, refreshTime) as any;
        
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
      console.log('[WebSocket]', ...args);
    }
  }
}

// Create singleton instance with URL from config and debug enabled
export const websocketService = new WebSocketService({ 
  url: WS_URL,
  debug: true, // Enable debug logging
  reconnect: true,
  maxReconnectAttempts: 5,
  reconnectInterval: 3000,
  heartbeatInterval: 30000
});

// Export convenience functions
export const connectWebSocket = (token?: string) => websocketService.connect(token);
export const disconnectWebSocket = (reason?: string) => websocketService.disconnect(reason);
export const refreshWebSocketToken = () => websocketService.refreshTokenAndReconnect();
export const sendWebSocketMessage = <T = any>(
  type: WebSocketMessageType,
  payload?: T,
  options?: { channel?: string; awaitAcknowledgment?: boolean; timeout?: number }
) => websocketService.send(type, payload, options);
export const subscribeToChannel = (
  channel: string | WebSocketChannel,
  handler: WebSocketEventHandler,
  filter?: (message: WebSocketMessage) => boolean
) => websocketService.subscribe(channel, handler, filter);
export const unsubscribeFromChannel = (subscriptionId: string) =>
  websocketService.unsubscribe(subscriptionId);
export const getWebSocketState = () => websocketService.getState();
export const isWebSocketConnected = () => websocketService.isConnected();
export const onWebSocketConnectionStatusChange = (callback: (status: WebSocketState) => void) => 
  websocketService.onConnectionStatusChange(callback);
