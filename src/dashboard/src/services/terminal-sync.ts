/**
 * Terminal Synchronization Service
 * 
 * Manages real-time communication between Terminal 2 (Dashboard) and other terminals
 * Handles message routing, offline queuing, and cross-terminal coordination
 * 
 * @fileoverview Production-ready terminal sync service with Socket.io integration
 * @version 1.0.0
 */

import { io, Socket } from 'socket.io-client';
import { WS_URL, API_BASE_URL, AUTH_TOKEN_KEY } from '../config';
import axios, { AxiosInstance } from 'axios';

// Browser-compatible EventEmitter implementation
class EventEmitter {
  private events: Map<string, Set<Function>> = new Map();
  private maxListeners: number = 10;

  on(event: string, listener: Function): this {
    if (!this.events.has(event)) {
      this.events.set(event, new Set());
    }
    this.events.get(event)!.add(listener);
    return this;
  }

  off(event: string, listener: Function): this {
    const listeners = this.events.get(event);
    if (listeners) {
      listeners.delete(listener);
    }
    return this;
  }

  emit(event: string, ...args: any[]): boolean {
    const listeners = this.events.get(event);
    if (!listeners || listeners.size === 0) {
      return false;
    }
    
    listeners.forEach(listener => {
      try {
        listener(...args);
      } catch (error) {
        console.error(`Error in event listener for ${event}:`, error);
      }
    });
    return true;
  }

  removeAllListeners(event?: string): this {
    if (event) {
      this.events.delete(event);
    } else {
      this.events.clear();
    }
    return this;
  }

  setMaxListeners(n: number): this {
    this.maxListeners = n;
    return this;
  }

  getMaxListeners(): number {
    return this.maxListeners;
  }

  listenerCount(event: string): number {
    const listeners = this.events.get(event);
    return listeners ? listeners.size : 0;
  }
}

// ================================
// TYPE DEFINITIONS
// ================================

export interface TerminalMessage {
  id: string;
  from: 'terminal1' | 'terminal2' | 'terminal3' | 'debugger';
  to: 'terminal1' | 'terminal2' | 'terminal3' | 'debugger' | 'all';
  type: string;
  payload: any;
  timestamp: string;
  priority: 'low' | 'normal' | 'high' | 'critical';
  ttl?: number; // Time to live in milliseconds
  requiresAck?: boolean;
}

export interface TerminalConnection {
  id: string;
  socket: Socket | WebSocket | null;
  status: 'connected' | 'disconnected' | 'connecting' | 'error';
  lastSeen: string;
  messageQueue: TerminalMessage[];
  retryCount: number;
  endpoint: string;
}

export interface SyncStats {
  messagesReceived: number;
  messagesSent: number;
  messagesQueued: number;
  connectionStatus: Record<string, string>;
  lastActivity: string;
  errors: string[];
}

// ================================
// TERMINAL SYNC SERVICE
// ================================

export class TerminalSyncService extends EventEmitter {
  private static instance: TerminalSyncService | null = null;
  private connections: Map<string, TerminalConnection> = new Map();
  private messageQueue: TerminalMessage[] = [];
  private isOnline: boolean = true;
  private syncTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private stats: SyncStats;
  private apiClient: AxiosInstance;
  private isInitialized: boolean = false;

  // Terminal endpoints configuration
  private readonly terminalEndpoints = {
    terminal1: {
      socketio: WS_URL,
      websocket: 'ws://localhost:8008/ws',
      http: API_BASE_URL
    },
    terminal3: {
      websocket: 'ws://localhost:5001/roblox',
      http: 'http://localhost:5001'
    },
    debugger: {
      socketio: 'http://localhost:8008/debug',
      http: 'http://localhost:8008/debug'
    }
  };

  constructor() {
    super();
    this.setMaxListeners(20); // Increase listener limit

    this.stats = {
      messagesReceived: 0,
      messagesSent: 0,
      messagesQueued: 0,
      connectionStatus: {},
      lastActivity: new Date().toISOString(),
      errors: []
    };

    this.apiClient = axios.create({
      timeout: 5000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    this.setupApiInterceptors();
  }

  // ================================
  // SINGLETON PATTERN
  // ================================

  public static getInstance(): TerminalSyncService {
    if (!TerminalSyncService.instance) {
      TerminalSyncService.instance = new TerminalSyncService();
    }
    return TerminalSyncService.instance;
  }

  // ================================
  // INITIALIZATION
  // ================================

  public async initialize(): Promise<void> {
    if (this.isInitialized) {
      console.warn('⚠️ Terminal sync service already initialized');
      return;
    }

    console.log('🔄 Initializing Terminal Sync Service');

    try {
      // Setup network monitoring
      this.setupNetworkMonitoring();
      
      // Connect to all terminals
      await this.connectToAllTerminals();
      
      // Start periodic sync and heartbeat
      this.startPeriodicSync();
      this.startHeartbeat();
      
      // Setup cleanup handlers
      this.setupCleanupHandlers();
      
      this.isInitialized = true;
      this.emit('initialized');
      
      console.log('✅ Terminal Sync Service initialized');
      
    } catch (error) {
      console.error('❌ Failed to initialize Terminal Sync Service:', error);
      this.addError(`Initialization failed: ${error}`);
      throw error;
    }
  }

  private setupApiInterceptors(): void {
    this.apiClient.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem(AUTH_TOKEN_KEY);
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
  }

  private setupNetworkMonitoring(): void {
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => this.handleOnline());
      window.addEventListener('offline', () => this.handleOffline());
      
      // Check initial network status
      this.isOnline = navigator.onLine;
    }
  }

  private setupCleanupHandlers(): void {
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => {
        this.shutdown();
      });
      
      // Cleanup on page visibility change
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
          this.pauseConnections();
        } else if (document.visibilityState === 'visible') {
          this.resumeConnections();
        }
      });
    }
  }

  // ================================
  // CONNECTION MANAGEMENT
  // ================================

  private async connectToAllTerminals(): Promise<void> {
    const connectionPromises = [
      this.connectToTerminal1(),
      this.connectToTerminal3(),
      this.connectToDebugger()
    ];

    // Connect to terminals in parallel but don't fail if some connections fail
    const results = await Promise.allSettled(connectionPromises);
    
    results.forEach((result, index) => {
      const terminalNames = ['terminal1', 'terminal3', 'debugger'];
      const terminalName = terminalNames[index];
      
      if (result.status === 'fulfilled') {
        console.log(`✅ Connected to ${terminalName}`);
      } else {
        console.warn(`⚠️ Failed to connect to ${terminalName}:`, result.reason);
        this.addError(`Failed to connect to ${terminalName}: ${result.reason}`);
      }
    });
  }

  private async connectToTerminal1(): Promise<void> {
    const connectionId = 'terminal1';
    
    try {
      const token = localStorage.getItem(AUTH_TOKEN_KEY);
      const socket = io(this.terminalEndpoints.terminal1.socketio, {
        auth: { token },
        path: '/socket.io',
        transports: ['websocket', 'polling'],
        timeout: 10000,
        reconnection: true,
        reconnectionDelay: 2000,
        reconnectionAttempts: 5
      });

      const connection: TerminalConnection = {
        id: connectionId,
        socket,
        status: 'connecting',
        lastSeen: new Date().toISOString(),
        messageQueue: [],
        retryCount: 0,
        endpoint: this.terminalEndpoints.terminal1.socketio
      };

      this.connections.set(connectionId, connection);

      // Setup Socket.io event handlers
      socket.on('connect', () => {
        console.log('✅ Connected to Terminal 1 (Backend API)');
        connection.status = 'connected';
        connection.retryCount = 0;
        this.updateConnectionStatus(connectionId, 'connected');
        this.flushMessageQueue(connectionId);
        this.emit('terminal1:connected');
      });

      socket.on('disconnect', (reason) => {
        console.warn('⚠️ Disconnected from Terminal 1:', reason);
        connection.status = 'disconnected';
        this.updateConnectionStatus(connectionId, 'disconnected');
        this.emit('terminal1:disconnected', reason);
      });

      socket.on('connect_error', (error) => {
        console.error('❌ Terminal 1 connection error:', error);
        connection.status = 'error';
        connection.retryCount++;
        this.updateConnectionStatus(connectionId, 'error');
        this.addError(`Terminal 1 connection error: ${error.message}`);
        this.emit('terminal1:error', error);
      });

      // Handle incoming messages from Terminal 1
      socket.on('content_update', (data) => {
        this.handleIncomingMessage({
          id: this.generateMessageId(),
          from: 'terminal1',
          to: 'terminal2',
          type: 'content_update',
          payload: data,
          timestamp: new Date().toISOString(),
          priority: 'normal'
        });
      });

      socket.on('user_activity', (data) => {
        this.handleIncomingMessage({
          id: this.generateMessageId(),
          from: 'terminal1',
          to: 'terminal2',
          type: 'user_activity',
          payload: data,
          timestamp: new Date().toISOString(),
          priority: 'normal'
        });
      });

      socket.on('system_alert', (alert) => {
        this.handleIncomingMessage({
          id: this.generateMessageId(),
          from: 'terminal1',
          to: 'terminal2',
          type: 'system_alert',
          payload: alert,
          timestamp: new Date().toISOString(),
          priority: 'high'
        });
      });

      socket.on('terminal:message', (message: TerminalMessage) => {
        this.handleIncomingMessage(message);
      });

    } catch (error) {
      console.error('❌ Failed to setup Terminal 1 connection:', error);
      throw error;
    }
  }

  private async connectToTerminal3(): Promise<void> {
    const connectionId = 'terminal3';
    
    try {
      const robloxBridge = new WebSocket(this.terminalEndpoints.terminal3.websocket);
      
      const connection: TerminalConnection = {
        id: connectionId,
        socket: robloxBridge,
        status: 'connecting',
        lastSeen: new Date().toISOString(),
        messageQueue: [],
        retryCount: 0,
        endpoint: this.terminalEndpoints.terminal3.websocket
      };

      this.connections.set(connectionId, connection);

      robloxBridge.onopen = () => {
        console.log('✅ Connected to Terminal 3 (Roblox Bridge)');
        connection.status = 'connected';
        connection.retryCount = 0;
        this.updateConnectionStatus(connectionId, 'connected');
        this.flushMessageQueue(connectionId);
        this.emit('terminal3:connected');
      };

      robloxBridge.onclose = (event) => {
        console.warn('⚠️ Terminal 3 connection closed:', event.code, event.reason);
        connection.status = 'disconnected';
        this.updateConnectionStatus(connectionId, 'disconnected');
        this.emit('terminal3:disconnected', event);
        
        // Attempt reconnection after delay
        if (connection.retryCount < 5) {
          setTimeout(() => this.reconnectTerminal3(), 5000 * (connection.retryCount + 1));
        }
      };

      robloxBridge.onerror = (error) => {
        console.error('❌ Terminal 3 connection error:', error);
        connection.status = 'error';
        connection.retryCount++;
        this.updateConnectionStatus(connectionId, 'error');
        this.addError(`Terminal 3 connection error: ${error}`);
        this.emit('terminal3:error', error);
      };

      robloxBridge.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleIncomingMessage({
            id: data.id || this.generateMessageId(),
            from: 'terminal3',
            to: 'terminal2',
            type: data.type || 'roblox_event',
            payload: data,
            timestamp: new Date().toISOString(),
            priority: 'normal'
          });
        } catch (error) {
          console.error('❌ Failed to parse Terminal 3 message:', error);
          this.addError(`Failed to parse Terminal 3 message: ${error}`);
        }
      };

    } catch (error) {
      console.error('❌ Failed to setup Terminal 3 connection:', error);
      throw error;
    }
  }

  private async connectToDebugger(): Promise<void> {
    const connectionId = 'debugger';
    
    try {
      const token = localStorage.getItem(AUTH_TOKEN_KEY);
      const debugSocket = io(this.terminalEndpoints.debugger.socketio, {
        auth: { token },
        path: '/socket.io',
        namespace: '/debug',
        timeout: 10000
      });

      const connection: TerminalConnection = {
        id: connectionId,
        socket: debugSocket,
        status: 'connecting',
        lastSeen: new Date().toISOString(),
        messageQueue: [],
        retryCount: 0,
        endpoint: this.terminalEndpoints.debugger.socketio
      };

      this.connections.set(connectionId, connection);

      debugSocket.on('connect', () => {
        console.log('✅ Connected to Debugger Terminal');
        connection.status = 'connected';
        connection.retryCount = 0;
        this.updateConnectionStatus(connectionId, 'connected');
        this.flushMessageQueue(connectionId);
        this.emit('debugger:connected');
      });

      debugSocket.on('disconnect', (reason) => {
        console.warn('⚠️ Debugger disconnected:', reason);
        connection.status = 'disconnected';
        this.updateConnectionStatus(connectionId, 'disconnected');
        this.emit('debugger:disconnected', reason);
      });

      debugSocket.on('performance_alert', (alert) => {
        console.warn('⚠️ Performance Alert:', alert);
        this.handleIncomingMessage({
          id: this.generateMessageId(),
          from: 'debugger',
          to: 'terminal2',
          type: 'performance_alert',
          payload: alert,
          timestamp: new Date().toISOString(),
          priority: 'high'
        });
      });

      debugSocket.on('security_warning', (warning) => {
        console.error('🔒 Security Warning:', warning);
        this.handleIncomingMessage({
          id: this.generateMessageId(),
          from: 'debugger',
          to: 'terminal2',
          type: 'security_warning',
          payload: warning,
          timestamp: new Date().toISOString(),
          priority: 'critical'
        });
      });

    } catch (error) {
      console.error('❌ Failed to setup Debugger connection:', error);
      // Don't throw error for debugger - it's optional
      this.addError(`Debugger connection failed: ${error}`);
    }
  }

  // ================================
  // MESSAGE HANDLING
  // ================================

  public async sendToTerminal(terminalId: string, message: Omit<TerminalMessage, 'id' | 'from' | 'timestamp'>): Promise<boolean> {
    const fullMessage: TerminalMessage = {
      id: this.generateMessageId(),
      from: 'terminal2',
      timestamp: new Date().toISOString(),
      ...message
    };

    try {
      if (terminalId === 'all') {
        return this.broadcast(fullMessage);
      }

      const connection = this.connections.get(terminalId);
      if (!connection) {
        console.warn(`⚠️ No connection found for ${terminalId}`);
        return false;
      }

      if (connection.status === 'connected' && connection.socket) {
        return await this.sendMessage(connection, fullMessage);
      } else {
        // Queue message for later delivery
        connection.messageQueue.push(fullMessage);
        this.stats.messagesQueued++;
        console.log(`📮 Message queued for ${terminalId}: ${message.type}`);
        return true;
      }
    } catch (error) {
      console.error(`❌ Failed to send message to ${terminalId}:`, error);
      this.addError(`Send message failed: ${error}`);
      return false;
    }
  }

  private async sendMessage(connection: TerminalConnection, message: TerminalMessage): Promise<boolean> {
    try {
      if (connection.socket instanceof WebSocket) {
        // WebSocket connection (Terminal 3)
        if (connection.socket.readyState === WebSocket.OPEN) {
          connection.socket.send(JSON.stringify(message));
          this.stats.messagesSent++;
          return true;
        }
      } else if (connection.socket && 'emit' in connection.socket) {
        // Socket.io connection (Terminal 1, Debugger)
        const socket = connection.socket as Socket;
        if (socket.connected) {
          if (message.requiresAck) {
            return new Promise((resolve) => {
              socket.emit('terminal:message', message, (ack: any) => {
                this.stats.messagesSent++;
                resolve(ack?.success === true);
              });
              
              // Timeout acknowledgment after 5 seconds
              setTimeout(() => resolve(false), 5000);
            });
          } else {
            socket.emit('terminal:message', message);
            this.stats.messagesSent++;
            return true;
          }
        }
      }
      
      return false;
    } catch (error) {
      console.error(`❌ Failed to send message via ${connection.id}:`, error);
      throw error;
    }
  }

  private async broadcast(message: TerminalMessage): Promise<boolean> {
    const sendPromises = Array.from(this.connections.values()).map(connection => {
      if (connection.status === 'connected') {
        return this.sendMessage(connection, message);
      }
      return Promise.resolve(false);
    });

    const results = await Promise.allSettled(sendPromises);
    const successCount = results.filter(r => r.status === 'fulfilled' && r.value).length;
    
    console.log(`📡 Broadcast ${message.type} to ${successCount}/${this.connections.size} terminals`);
    return successCount > 0;
  }

  private handleIncomingMessage(message: TerminalMessage): void {
    this.stats.messagesReceived++;
    this.stats.lastActivity = new Date().toISOString();

    // Update last seen for the sender
    const connection = this.connections.get(message.from);
    if (connection) {
      connection.lastSeen = message.timestamp;
    }

    // Check message TTL
    if (message.ttl) {
      const messageAge = Date.now() - new Date(message.timestamp).getTime();
      if (messageAge > message.ttl) {
        console.warn(`⚠️ Message ${message.id} expired (TTL: ${message.ttl}ms)`);
        return;
      }
    }

    // Emit specific event based on message type and source
    this.emit(`message:${message.type}`, message.payload, message);
    this.emit(`${message.from}:${message.type}`, message.payload, message);
    this.emit('message', message);

    // Handle high priority messages
    if (message.priority === 'high' || message.priority === 'critical') {
      this.emit('priority_message', message);
    }

    console.log(`📨 Received ${message.type} from ${message.from}`, message.payload);
  }

  // ================================
  // QUEUE AND RETRY MANAGEMENT
  // ================================

  private flushMessageQueue(terminalId: string): void {
    const connection = this.connections.get(terminalId);
    if (!connection || connection.messageQueue.length === 0) {
      return;
    }

    console.log(`📤 Flushing ${connection.messageQueue.length} queued messages for ${terminalId}`);

    const messages = [...connection.messageQueue];
    connection.messageQueue = [];

    messages.forEach(async (message) => {
      try {
        const success = await this.sendMessage(connection, message);
        if (!success) {
          console.warn(`⚠️ Failed to flush message ${message.id}, re-queuing`);
          connection.messageQueue.push(message);
        } else {
          this.stats.messagesQueued = Math.max(0, this.stats.messagesQueued - 1);
        }
      } catch (error) {
        console.error(`❌ Error flushing message ${message.id}:`, error);
        connection.messageQueue.push(message);
      }
    });
  }

  private async reconnectTerminal3(): Promise<void> {
    const connection = this.connections.get('terminal3');
    if (!connection) return;

    try {
      connection.retryCount++;
      console.log(`🔄 Reconnecting to Terminal 3 (attempt ${connection.retryCount})`);
      
      // Close existing connection if any
      if (connection.socket && connection.socket instanceof WebSocket) {
        connection.socket.close();
      }
      
      // Create new connection
      await this.connectToTerminal3();
      
    } catch (error) {
      console.error('❌ Terminal 3 reconnection failed:', error);
      this.addError(`Terminal 3 reconnection failed: ${error}`);
    }
  }

  // ================================
  // NETWORK STATUS HANDLING
  // ================================

  private handleOnline(): void {
    console.log('🌐 Network connection restored');
    this.isOnline = true;
    this.emit('online');
    
    // Reconnect to all terminals
    this.connectToAllTerminals();
  }

  private handleOffline(): void {
    console.warn('🌐 Network connection lost');
    this.isOnline = false;
    this.emit('offline');
    
    // Update all connection statuses
    this.connections.forEach((connection, id) => {
      if (connection.status === 'connected') {
        connection.status = 'disconnected';
        this.updateConnectionStatus(id, 'disconnected');
      }
    });
  }

  // ================================
  // PERIODIC OPERATIONS
  // ================================

  private startPeriodicSync(): void {
    this.syncTimer = setInterval(() => {
      this.performPeriodicSync();
    }, 30000); // Every 30 seconds
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      this.sendHeartbeat();
    }, 60000); // Every minute
  }

  private performPeriodicSync(): void {
    // Send sync status to all terminals
    const syncMessage: Omit<TerminalMessage, 'id' | 'from' | 'timestamp'> = {
      to: 'all',
      type: 'sync_status',
      payload: {
        terminal: 'terminal2',
        status: this.getConnectionStatuses(),
        stats: this.stats,
        timestamp: new Date().toISOString()
      },
      priority: 'low'
    };

    this.broadcast(syncMessage as TerminalMessage);

    // Clean up expired messages and connections
    this.cleanupExpiredMessages();
    this.cleanupStaleConnections();
  }

  private sendHeartbeat(): void {
    const heartbeatMessage: Omit<TerminalMessage, 'id' | 'from' | 'timestamp'> = {
      to: 'all',
      type: 'heartbeat',
      payload: {
        terminal: 'terminal2',
        timestamp: new Date().toISOString(),
        isOnline: this.isOnline,
        activeConnections: Array.from(this.connections.keys()).filter(
          id => this.connections.get(id)?.status === 'connected'
        )
      },
      priority: 'low',
      ttl: 120000 // 2 minutes TTL
    };

    this.sendToTerminal('all', heartbeatMessage);
  }

  private cleanupExpiredMessages(): void {
    const now = Date.now();
    this.connections.forEach((connection) => {
      connection.messageQueue = connection.messageQueue.filter(message => {
        if (message.ttl) {
          const messageAge = now - new Date(message.timestamp).getTime();
          return messageAge < message.ttl;
        }
        return true;
      });
    });
  }

  private cleanupStaleConnections(): void {
    const staleThreshold = 5 * 60 * 1000; // 5 minutes
    const now = Date.now();
    
    this.connections.forEach((connection, id) => {
      const lastSeenAge = now - new Date(connection.lastSeen).getTime();
      if (lastSeenAge > staleThreshold && connection.status !== 'connected') {
        console.warn(`🧹 Cleaning up stale connection: ${id}`);
        connection.socket?.disconnect?.();
        connection.messageQueue = [];
      }
    });
  }

  // ================================
  // CONNECTION LIFECYCLE
  // ================================

  private pauseConnections(): void {
    console.log('⏸️ Pausing terminal connections');
    this.connections.forEach((connection) => {
      if (connection.socket && 'disconnect' in connection.socket) {
        (connection.socket as Socket).disconnect();
      }
    });
  }

  private resumeConnections(): void {
    console.log('▶️ Resuming terminal connections');
    this.connectToAllTerminals();
  }

  public shutdown(): void {
    console.log('🛑 Shutting down Terminal Sync Service');
    
    if (this.syncTimer) {
      clearInterval(this.syncTimer);
    }
    
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
    }

    // Disconnect all terminals
    this.connections.forEach((connection, id) => {
      console.log(`🔌 Disconnecting from ${id}`);
      if (connection.socket) {
        if ('disconnect' in connection.socket) {
          (connection.socket as Socket).disconnect();
        } else if ('close' in connection.socket) {
          (connection.socket as WebSocket).close();
        }
      }
    });

    this.connections.clear();
    this.messageQueue = [];
    this.isInitialized = false;
    
    this.emit('shutdown');
    console.log('✅ Terminal Sync Service shut down');
  }

  // ================================
  // UTILITY METHODS
  // ================================

  private updateConnectionStatus(terminalId: string, status: string): void {
    this.stats.connectionStatus[terminalId] = status;
    this.emit('connection_status_changed', { terminalId, status });
  }

  private addError(error: string): void {
    this.stats.errors.push(`[${new Date().toISOString()}] ${error}`);
    
    // Keep only last 20 errors
    if (this.stats.errors.length > 20) {
      this.stats.errors.shift();
    }
  }

  private generateMessageId(): string {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substring(2, 15);
    return `msg_${timestamp}_${random}`;
  }

  // ================================
  // PUBLIC API
  // ================================

  public getConnectionStatuses(): Record<string, string> {
    const statuses: Record<string, string> = {};
    this.connections.forEach((connection, id) => {
      statuses[id] = connection.status;
    });
    return statuses;
  }

  public getStats(): SyncStats {
    return { ...this.stats };
  }

  public isTerminalConnected(terminalId: string): boolean {
    const connection = this.connections.get(terminalId);
    return connection?.status === 'connected' || false;
  }

  public getQueuedMessageCount(): number {
    return Array.from(this.connections.values())
      .reduce((total, connection) => total + connection.messageQueue.length, 0);
  }

  public clearErrorLog(): void {
    this.stats.errors = [];
    console.log('🧹 Error log cleared');
  }

  public forceReconnectAll(): void {
    console.log('🔄 Force reconnecting all terminals');
    this.connectToAllTerminals();
  }
}

// ================================
// EXPORT SINGLETON
// ================================

export default TerminalSyncService;

// Create and export singleton instance
export const terminalSync = TerminalSyncService.getInstance();

// Global exposure for debugging
if (typeof window !== 'undefined') {
  (window as any).__TERMINAL_SYNC__ = terminalSync;
  
  // Auto-initialize in development mode
  if (import.meta.env.DEV) {
    console.log('🚀 Terminal sync service created');
    
    // Initialize after short delay
    setTimeout(() => {
      terminalSync.initialize().catch(error => {
        console.error('❌ Terminal sync initialization failed:', error);
      });
    }, 1000);
  }
}