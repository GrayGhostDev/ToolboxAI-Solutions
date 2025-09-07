/**
 * WebSocket Service for ToolboxAI Dashboard
 *
 * Manages WebSocket connections, message handling, reconnection logic,
 * and provides a robust real-time communication layer.
 */

import { io, Socket } from 'socket.io-client';
import { AUTH_TOKEN_KEY, WS_CONFIG } from '../config';
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

export class WebSocketService {
  private static instance: WebSocketService | null = null;
  private socket: Socket | null = null;
  private options: WebSocketConnectionOptions;
  private state: WebSocketState = WebSocketState.DISCONNECTED;
  private subscriptions: Map<string, Set<WebSocketSubscription>> = new Map();
  private messageQueue: QueuedMessage[] = [];
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private stats: WebSocketStats;
  private messageHandlers: Map<string, Set<WebSocketEventHandler>> = new Map();
  private stateHandlers: Set<WebSocketStateHandler> = new Set();
  private errorHandlers: Set<WebSocketErrorHandler> = new Set();
  private pendingAcknowledgments: Map<string, (ack: MessageAcknowledgment) => void> = new Map();

  constructor(options: Partial<WebSocketConnectionOptions> = {}) {
    this.options = {
      url: options.url || 'ws://localhost:8001',
      reconnect: options.reconnect !== false,
      reconnectInterval: options.reconnectInterval || WS_CONFIG.reconnectInterval,
      maxReconnectAttempts: options.maxReconnectAttempts || WS_CONFIG.maxReconnectAttempts,
      heartbeatInterval: options.heartbeatInterval || WS_CONFIG.heartbeatInterval,
      debug: options.debug || false,
      ...options,
    };

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
   * Connect to WebSocket server
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

        // Get authentication token
        const authToken = token || this.getAuthToken();

        // Parse URL to separate protocol and host
        const url = new URL(this.options.url);
        const protocol = url.protocol === 'wss:' ? 'https:' : 'http:';
        const socketUrl = `${protocol}//${url.host}`;

        // Create socket connection with authentication
        this.socket = io(socketUrl, {
          path: '/socket.io', // Match backend socketio_path
          transports: ['websocket', 'polling'], // Allow fallback to polling
          auth: authToken ? { token: authToken } : undefined,
          reconnection: false, // We handle reconnection manually
          timeout: 10000,
          query: {
            clientId: this.generateClientId(),
            timestamp: Date.now().toString(),
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
        const errorHandler = (error: Error) => {
          this.log('Connection failed:', error);
          this.socket?.off('connect', connectHandler);
          this.socket?.off('connect_error', errorHandler);
          this.handleError({
            code: 'CONNECTION_FAILED',
            message: error.message,
            timestamp: new Date().toISOString(),
            recoverable: true,
          });
          reject(error);
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
    const subscription: WebSocketSubscription = {
      channel,
      handler,
      filter,
      subscriptionId: this.generateSubscriptionId(),
    };

    if (!this.subscriptions.has(channel)) {
      this.subscriptions.set(channel, new Set());

      // Send subscription request to server
      if (this.state === WebSocketState.CONNECTED) {
        this.send(WebSocketMessageType.SUBSCRIBE, { channels: [channel] });
      }
    }

    const channelSubs = this.subscriptions.get(channel);
    if (channelSubs) {
      channelSubs.add(subscription);
    }
    this.log(`Subscribed to channel: ${channel}`);

    return subscription.subscriptionId!;
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
    this.socket.on('error', (error: Error) => {
      this.handleError({
        code: 'SOCKET_ERROR',
        message: error.message,
        timestamp: new Date().toISOString(),
        details: error,
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

    // Attempt reconnection if enabled
    if (
      this.options.reconnect &&
      previousState === WebSocketState.CONNECTED &&
      this.options.maxReconnectAttempts &&
      this.reconnectAttempts < this.options.maxReconnectAttempts
    ) {
      this.reconnect();
    } else {
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

  private reconnect(): void {
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
        await this.connect();
      } catch (error) {
        this.log('Reconnection failed:', error);
        if (this.reconnectAttempts < this.options.maxReconnectAttempts!) {
          this.reconnect();
        } else {
          this.setState(WebSocketState.ERROR);
        }
      }
    }, delay);
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
    }, this.options.heartbeatInterval!);
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
  }

  private getAuthToken(): string | undefined {
    // Get token from localStorage or session
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
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

  private log(...args: any[]): void {
    if (this.options.debug) {
      console.log('[WebSocket]', ...args);
    }
  }
}

// Create singleton instance
export const websocketService = new WebSocketService();

// Export convenience functions
export const connectWebSocket = (token?: string) => websocketService.connect(token);
export const disconnectWebSocket = (reason?: string) => websocketService.disconnect(reason);
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
