/**
 * Authentication Synchronization Service
 *
 * Manages secure token handling, session monitoring, and authentication state
 * synchronization between Dashboard and Backend services
 *
 * @fileoverview Production-ready auth sync with JWT management and session control
 * @version 1.0.0
 */

import { AUTH_TOKEN_KEY, AUTH_REFRESH_TOKEN_KEY, API_BASE_URL } from '../config';
import { store } from '../store';
import { signInSuccess as loginSuccess, signOut as logout, updateToken } from '../store/slices/userSlice';
import { addNotification } from '../store/slices/uiSlice';
import { pusherService } from '../services/pusher';

// Timer type definitions for cross-platform compatibility
type TimerId = ReturnType<typeof setTimeout>;
type IntervalId = ReturnType<typeof setInterval>;

// ================================
// TYPE DEFINITIONS
// ================================

export interface AuthToken {
  token: string;
  expiresAt: number;
  refreshToken?: string;
  refreshExpiresAt?: number;
}

export interface SessionInfo {
  userId: string;
  sessionId: string;
  startTime: number;
  lastActivity: number;
  isActive: boolean;
  deviceInfo?: {
    userAgent: string;
    platform: string;
    language: string;
  };
}

export interface AuthSyncConfig {
  tokenRefreshThreshold: number; // Minutes before expiry to refresh
  sessionTimeout: number; // Minutes of inactivity before timeout
  inactivityWarning: number; // Minutes before showing warning
  enableAutoRefresh: boolean;
  enableSessionMonitoring: boolean;
  syncWithBackend: boolean;
}

export interface AuthEvent {
  type: 'login' | 'logout' | 'refresh' | 'timeout' | 'force_logout' | 'permission_change';
  timestamp: string;
  userId?: string;
  sessionId?: string;
  reason?: string;
  metadata?: Record<string, unknown>;
}

// ================================
// AUTHENTICATION SYNC SERVICE
// ================================

export class AuthSyncService {
  private static instance: AuthSyncService | null = null;
  private config: AuthSyncConfig;
  private tokenRefreshTimer: TimerId | null = null;
  private sessionMonitor: IntervalId | null = null;
  private inactivityTimer: TimerId | null = null;
  private currentSession: SessionInfo | null = null;
  private lastActivity: number = Date.now();
  private isInitialized: boolean = false;
  private authEvents: AuthEvent[] = [];

  constructor(config: Partial<AuthSyncConfig> = {}) {
    this.config = {
      tokenRefreshThreshold: 5, // 5 minutes before expiry
      sessionTimeout: 30, // 30 minutes timeout
      inactivityWarning: 25, // Warning at 25 minutes
      enableAutoRefresh: true,
      enableSessionMonitoring: true,
      syncWithBackend: true,
      ...config
    };
  }

  // ================================
  // SINGLETON PATTERN
  // ================================

  public static getInstance(config?: Partial<AuthSyncConfig>): AuthSyncService {
    if (!AuthSyncService.instance) {
      AuthSyncService.instance = new AuthSyncService(config);
    }
    return AuthSyncService.instance;
  }

  // ================================
  // INITIALIZATION
  // ================================

  public async initialize(): Promise<void> {
    if (this.isInitialized) {
      console.warn('⚠️ Auth sync service already initialized');
      return;
    }

    if (import.meta.env.DEV) {
      console.log('🔐 Initializing Authentication Sync Service');
    }

    try {
      // Check for existing token
      const existingToken = this.getStoredToken();
      if (existingToken) {
        await this.validateAndRefreshToken(existingToken);
      }

      // Setup monitoring
      if (this.config.enableAutoRefresh) {
        this.setupTokenRefresh();
      }

      if (this.config.enableSessionMonitoring) {
        this.setupSessionMonitor();
        this.setupActivityTracking();
      }

      // Setup cleanup handlers
      this.setupCleanupHandlers();

      // Setup cross-tab synchronization (2025 best practice)
      this.setupCrossTabSync();

      this.isInitialized = true;
      if (import.meta.env.DEV) {
        console.log('✅ Auth sync service initialized with cross-tab sync');
      }

    } catch (error) {
      console.error('❌ Failed to initialize auth sync:', error);
      throw error;
    }
  }

  // ================================
  // TOKEN MANAGEMENT
  // ================================

  private getStoredToken(): AuthToken | null {
    try {
      const token = localStorage.getItem(AUTH_TOKEN_KEY);
      const refreshToken = localStorage.getItem(AUTH_REFRESH_TOKEN_KEY);

      if (!token) return null;

      // Decode JWT to get expiry
      const payload = this.decodeJWT(token);
      if (!payload || !payload.exp) return null;

      const refreshPayload = refreshToken ? this.decodeJWT(refreshToken) : null;

      return {
        token,
        expiresAt: payload.exp * 1000, // Convert to milliseconds
        refreshToken: refreshToken || undefined,
        refreshExpiresAt: refreshPayload?.exp ? refreshPayload.exp * 1000 : undefined
      };
    } catch (error) {
      console.error('❌ Failed to get stored token:', error);
      return null;
    }
  }

  private decodeJWT(token: string): { exp?: number; [key: string]: unknown } | null {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) return null;

      const payload = parts[1];
      const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
      return JSON.parse(decoded);
    } catch (error) {
      console.error('❌ Failed to decode JWT:', error);
      return null;
    }
  }

  private async validateAndRefreshToken(authToken: AuthToken): Promise<void> {
    const now = Date.now();
    const timeUntilExpiry = authToken.expiresAt - now;
    const thresholdMs = this.config.tokenRefreshThreshold * 60 * 1000;

    // Token is still valid
    if (timeUntilExpiry > thresholdMs) {
      if (import.meta.env.DEV) {
        console.log(`✅ Token valid for ${Math.round(timeUntilExpiry / 60000)} minutes`);
      }
      this.scheduleTokenRefresh(authToken);
      return;
    }

    // Token needs refresh
    if (timeUntilExpiry > 0 && authToken.refreshToken) {
      if (import.meta.env.DEV) {
        console.log('🔄 Token expiring soon, refreshing...');
      }
      await this.refreshToken(authToken.refreshToken);
    } else if (timeUntilExpiry <= 0) {
      console.warn('⚠️ Token expired, logging out...');
      this.handleAuthFailure('token_expired');
    }
  }

  private setupTokenRefresh(): void {
    const checkTokenExpiry = () => {
      const authToken = this.getStoredToken();
      if (!authToken) {
        if (import.meta.env.DEV) {
          console.log('No token found, stopping refresh timer');
        }
        this.clearTokenRefreshTimer();
        return;
      }

      const now = Date.now();
      const timeUntilExpiry = authToken.expiresAt - now;
      const thresholdMs = this.config.tokenRefreshThreshold * 60 * 1000;

      if (timeUntilExpiry < thresholdMs && timeUntilExpiry > 0) {
        if (authToken.refreshToken) {
          void this.refreshToken(authToken.refreshToken);
        } else {
          console.warn('⚠️ No refresh token available');
          this.handleAuthFailure('no_refresh_token');
        }
      }

      // Schedule next check
      const nextCheckIn = Math.max(
        Math.min(timeUntilExpiry - thresholdMs, 60000), // Check at least every minute
        10000 // But no more frequently than every 10 seconds
      );

      this.tokenRefreshTimer = setTimeout(checkTokenExpiry, nextCheckIn);
    };

    checkTokenExpiry();
  }

  private scheduleTokenRefresh(authToken: AuthToken): void {
    if (!this.config.enableAutoRefresh) return;

    const now = Date.now();
    const timeUntilExpiry = authToken.expiresAt - now;
    const thresholdMs = this.config.tokenRefreshThreshold * 60 * 1000;
    const refreshIn = Math.max(timeUntilExpiry - thresholdMs, 0);

    if (import.meta.env.DEV) {
      console.log(`⏰ Scheduling token refresh in ${Math.round(refreshIn / 60000)} minutes`);
    }

    this.clearTokenRefreshTimer();
    this.tokenRefreshTimer = setTimeout(() => {
      if (authToken.refreshToken) {
        void this.refreshToken(authToken.refreshToken);
      }
    }, refreshIn);
  }

  private clearTokenRefreshTimer(): void {
    if (this.tokenRefreshTimer) {
      clearTimeout(this.tokenRefreshTimer);
      this.tokenRefreshTimer = null;
    }
  }

  public async refreshToken(refreshToken?: string): Promise<void> {
    try {
      const token = refreshToken || localStorage.getItem(AUTH_REFRESH_TOKEN_KEY);
      if (!token) {
        throw new Error('No refresh token available');
      }

      if (import.meta.env.DEV) {
        console.log('🔄 Refreshing authentication token...');
      }

      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ refresh_token: token })
      });

      if (response.ok) {
        const data = await response.json();

        // Store new tokens
        localStorage.setItem(AUTH_TOKEN_KEY, data.access_token);
        if (data.refresh_token) {
          localStorage.setItem(AUTH_REFRESH_TOKEN_KEY, data.refresh_token);
        }

        // Broadcast token refresh to other tabs (2025 cross-tab sync)
        this.broadcastAuthEvent('TOKEN_REFRESHED', {
          token: data.access_token,
          refreshToken: data.refresh_token
        });

        // Update Redux store
        if (data.user) {
          store.dispatch(loginSuccess({
            userId: data.user?.id,
            email: data.user?.email,
            displayName: data.user?.display_name || data.user?.username || 'User',
            avatarUrl: data.user?.avatar_url,
            role: (data.user?.role || 'teacher') as 'admin' | 'teacher' | 'student',
            token: data.access_token,
            refreshToken: data.refresh_token,
            schoolId: data.user?.school_id,
            classIds: data.user?.class_ids || [],
          }));
        }

        // Record event
        this.recordAuthEvent({
          type: 'refresh',
          timestamp: new Date().toISOString(),
          userId: data.user?.id,
          sessionId: this.currentSession?.sessionId
        });

        // Schedule next refresh
        const newAuthToken = this.getStoredToken();
        if (newAuthToken) {
          this.scheduleTokenRefresh(newAuthToken);
        }

        // Ensure realtime layer picks up the new token
        try {
          await pusherService.refreshTokenAndReconnect();
        } catch (e) {
          console.warn('⚠️ Failed to refresh realtime connection token:', e);
        }

        if (import.meta.env.DEV) {
          console.log('✅ Token refreshed successfully');
        }

      } else {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || 'Token refresh failed');
      }

    } catch (error) {
      console.error('❌ Token refresh failed:', error);
      this.handleAuthFailure('refresh_failed');
    }
  }

  // ================================
  // SESSION MONITORING
  // ================================

  private setupSessionMonitor(): void {
    // Create new session
    this.currentSession = {
      userId: this.getCurrentUserId(),
      sessionId: this.generateSessionId(),
      startTime: Date.now(),
      lastActivity: Date.now(),
      isActive: true,
      deviceInfo: this.getDeviceInfo()
    };

    // Start monitoring
    this.sessionMonitor = setInterval(() => {
      this.checkSessionStatus();
    }, 60000); // Check every minute

    if (import.meta.env.DEV) {
      console.log('📊 Session monitoring started');
    }
  }

  private setupActivityTracking(): void {
    const updateActivity = () => {
      this.lastActivity = Date.now();

      if (this.currentSession) {
        this.currentSession.lastActivity = this.lastActivity;
      }

      // Clear any existing inactivity timer
      if (this.inactivityTimer) {
        clearTimeout(this.inactivityTimer);
      }

      // Set new inactivity timer
      this.setupInactivityTimer();
    };

    // Track user activity
    const events = ['mousedown', 'keydown', 'scroll', 'touchstart', 'click'];
    events.forEach(event => {
      document.addEventListener(event, updateActivity, { passive: true });
    });
  }

  private setupInactivityTimer(): void {
    const warningTime = this.config.inactivityWarning * 60 * 1000;
    const timeoutTime = this.config.sessionTimeout * 60 * 1000;

    // Set warning timer
    this.inactivityTimer = setTimeout(() => {
      this.showInactivityWarning();

      // Set final timeout
      this.inactivityTimer = setTimeout(() => {
        this.handleSessionTimeout();
      }, (timeoutTime - warningTime));

    }, warningTime);
  }

  private checkSessionStatus(): void {
    if (!this.currentSession) return;

    const now = Date.now();
    const inactiveTime = now - this.lastActivity;
    const inactiveMinutes = Math.floor(inactiveTime / 60000);

    // Update session
    this.currentSession.lastActivity = this.lastActivity;
    this.currentSession.isActive = inactiveMinutes < this.config.sessionTimeout;

    // Check for timeout
    if (inactiveMinutes >= this.config.sessionTimeout) {
      this.handleSessionTimeout();
    }
  }

  // ================================
  // EVENT HANDLERS
  // ================================

  private showInactivityWarning(): void {
    const remainingMinutes = this.config.sessionTimeout - this.config.inactivityWarning;

store.dispatch(addNotification({
      type: 'warning',
      message: `Your session will expire in ${remainingMinutes} minutes due to inactivity`,
      autoHide: false
    }));

    console.warn(`⚠️ Inactivity warning: ${remainingMinutes} minutes until timeout`);
  }

  private handleSessionTimeout(): void {
    console.warn('⏰ Session timeout - logging out');

    this.recordAuthEvent({
      type: 'timeout',
      timestamp: new Date().toISOString(),
      userId: this.currentSession?.userId,
      sessionId: this.currentSession?.sessionId,
      reason: 'inactivity_timeout'
    });

    this.performLogout('session_timeout');
  }

  private handleForceLogout(reason?: string): void {
    console.warn('🔒 Force logout:', reason);

    this.recordAuthEvent({
      type: 'force_logout',
      timestamp: new Date().toISOString(),
      userId: this.currentSession?.userId,
      sessionId: this.currentSession?.sessionId,
      reason
    });

    this.performLogout('force_logout');
  }

  private handleSessionUpdate(data: { terminate?: boolean; extend?: boolean }): void {
    if (data.terminate) {
      this.handleForceLogout('session_terminated_by_admin');
    } else if (data.extend) {
      this.lastActivity = Date.now();
      if (import.meta.env.DEV) {
        console.log('✅ Session extended by backend');
      }
    }
  }

  private handlePermissionChange(data: { permissions?: string[] }): void {
    if (import.meta.env.DEV) {
      console.log('🔐 Permission change detected:', data);
    }

    store.dispatch(addNotification({
      type: 'info',
      message: 'Your permissions have been updated. Some features may have changed.',
      autoHide: false
    }));

    // Refresh user data
    void this.refreshUserData();
  }

  private handleAuthFailure(reason: string): void {
    console.error('❌ Authentication failure:', reason);

    this.recordAuthEvent({
      type: 'logout',
      timestamp: new Date().toISOString(),
      userId: this.currentSession?.userId,
      sessionId: this.currentSession?.sessionId,
      reason
    });

    this.performLogout(reason);
  }

  // ================================
  // LOGOUT HANDLING
  // ================================

  private performLogout(reason: string): void {
    // Clear tokens
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_REFRESH_TOKEN_KEY);

    // Clear timers
    this.clearTokenRefreshTimer();
    if (this.sessionMonitor) {
      clearInterval(this.sessionMonitor);
      this.sessionMonitor = null;
    }
    if (this.inactivityTimer) {
      clearTimeout(this.inactivityTimer);
      this.inactivityTimer = null;
    }

    // Clear session
    this.currentSession = null;

    // Broadcast logout to other tabs (2025 cross-tab sync)
    this.broadcastAuthEvent('AUTH_LOGOUT');

    // Update Redux store
    store.dispatch(logout());

    // Disconnect realtime layer
    try {
      pusherService.disconnect('auth_logout');
    } catch (e) {
      console.warn('⚠️ Realtime disconnect on logout failed:', e);
    }

    // Show notification
    const messages: Record<string, string> = {
      session_timeout: 'Your session has expired due to inactivity',
      force_logout: 'You have been logged out by an administrator',
      token_expired: 'Your authentication has expired',
      refresh_failed: 'Failed to refresh authentication',
      token_invalidated: 'Your session has been invalidated'
    };

    store.dispatch(addNotification({
      type: 'warning',
      message: messages[reason] || 'You have been logged out',
      autoHide: false
    }));

    // Redirect to login
    setTimeout(() => {
      window.location.href = '/login';
    }, 2000);
  }

  public async logout(): Promise<void> {
    if (import.meta.env.DEV) {
      console.log('👋 User initiated logout');
    }

    try {
      // Notify backend
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem(AUTH_TOKEN_KEY)}`,
          'Content-Type': 'application/json'
        }
      });
    } catch (error) {
      console.warn('⚠️ Backend logout notification failed:', error);
    }

    this.recordAuthEvent({
      type: 'logout',
      timestamp: new Date().toISOString(),
      userId: this.currentSession?.userId,
      sessionId: this.currentSession?.sessionId,
      reason: 'user_initiated'
    });

    this.performLogout('user_initiated');
  }

  // ================================
  // UTILITY METHODS
  // ================================

  private async refreshUserData(): Promise<void> {
    try {
      const token = localStorage.getItem(AUTH_TOKEN_KEY);
      if (!token) return;

      const response = await fetch(`${API_BASE_URL}/api/v1/users/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const userData = await response.json();
        // Update Redux store with fresh user data
        store.dispatch(loginSuccess({
          userId: userData?.id,
          email: userData?.email,
          displayName: userData?.display_name || userData?.username || 'User',
          avatarUrl: userData?.avatar_url,
          role: (userData?.role || 'teacher') as 'admin' | 'teacher' | 'student',
          token: token,
          refreshToken: localStorage.getItem(AUTH_REFRESH_TOKEN_KEY) || '',
          schoolId: userData?.school_id,
          classIds: userData?.class_ids || [],
        }));
      }
    } catch (error) {
      console.error('❌ Failed to refresh user data:', error);
    }
  }

  private getCurrentUserId(): string {
    const state = store.getState();
    return state.user?.userId || 'unknown';
  }

  private generateSessionId(): string {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substring(2, 15);
    return `session_${timestamp}_${random}`;
  }

  private getDeviceInfo(): SessionInfo['deviceInfo'] {
    return {
      userAgent: navigator.userAgent,
      platform: navigator.userAgent.includes('Mobile') ? 'Mobile' : 'Desktop',
      language: navigator.language
    };
  }

  private recordAuthEvent(event: AuthEvent): void {
    this.authEvents.push(event);

    // Keep only last 100 events
    if (this.authEvents.length > 100) {
      this.authEvents.shift();
    }

    // Log to console in development
    if (import.meta.env.DEV) {
      console.log('📝 Auth event:', event);
    }
  }

  // ================================
  // CLEANUP
  // ================================

  private setupCleanupHandlers(): void {
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => {
        this.cleanup();
      });
    }
  }

  private cleanup(): void {
    if (import.meta.env.DEV) {
      console.log('🧹 Cleaning up auth sync service');
    }

    this.clearTokenRefreshTimer();

    if (this.sessionMonitor) {
      clearInterval(this.sessionMonitor);
      this.sessionMonitor = null;
    }

    if (this.inactivityTimer) {
      clearTimeout(this.inactivityTimer);
      this.inactivityTimer = null;
    }
  }

  public shutdown(): void {
    this.cleanup();
    this.isInitialized = false;
    if (import.meta.env.DEV) {
      console.log('✅ Auth sync service shut down');
    }
  }

  // ================================
  // PUBLIC API
  // ================================

  public isAuthenticated(): boolean {
    const token = this.getStoredToken();
    return token !== null && token.expiresAt > Date.now();
  }

  public getSessionInfo(): SessionInfo | null {
    return this.currentSession ? { ...this.currentSession } : null;
  }

  public getAuthEvents(limit: number = 20): AuthEvent[] {
    return this.authEvents.slice(-limit);
  }

  public updateConfig(newConfig: Partial<AuthSyncConfig>): void {
    this.config = { ...this.config, ...newConfig };
    if (import.meta.env.DEV) {
      console.log('⚙️ Auth sync config updated:', this.config);
    }

    // Restart monitoring with new config
    if (this.isInitialized) {
      this.cleanup();
      void this.initialize();
    }
  }

  public extendSession(): void {
    this.lastActivity = Date.now();
    this.setupInactivityTimer();
    if (import.meta.env.DEV) {
      console.log('✅ Session extended manually');
    }
  }

  public isInitializedStatus(): boolean {
    return this.isInitialized;
  }

  // ================================
  // CROSS-TAB SYNCHRONIZATION (2025 BEST PRACTICE)
  // ================================

  private setupCrossTabSync(): void {
    if (typeof window === 'undefined') return;

    // Try to use BroadcastChannel API (modern browsers)
    if ('BroadcastChannel' in window) {
      try {
        const broadcastChannel = new BroadcastChannel('toolboxai_auth_sync');

        // Listen for messages from other tabs
        broadcastChannel.onmessage = (event) => {
          this.handleCrossTabMessage(event.data);
        };

        // Store reference for cleanup
        (this as any).broadcastChannel = broadcastChannel;

        if (import.meta.env.DEV) {
          console.log('✅ BroadcastChannel initialized for cross-tab sync');
        }
      } catch (error) {
        console.warn('BroadcastChannel not available, falling back to localStorage events');
        this.setupStorageEventListener();
      }
    } else {
      // Fallback to localStorage events for older browsers
      this.setupStorageEventListener();
    }
  }

  private setupStorageEventListener(): void {
    // Listen for localStorage changes from other tabs
    const storageEventListener = (event: StorageEvent) => {
      if (event.key === 'toolboxai_auth_sync_message' && event.newValue) {
        try {
          const message = JSON.parse(event.newValue);
          this.handleCrossTabMessage(message);
        } catch (error) {
          console.error('Failed to parse cross-tab message:', error);
        }
      }
    };

    window.addEventListener('storage', storageEventListener);

    // Store reference for cleanup
    (this as any).storageEventListener = storageEventListener;

    if (import.meta.env.DEV) {
      console.log('✅ Storage event listener initialized for cross-tab sync');
    }
  }

  private updateTokens(token: string, refreshToken: string): void {
    // Update tokens in storage and state
    this.setStoredToken(token);
    this.setStoredRefreshToken(refreshToken);

    // Update Redux store with existing user details and new tokens
    this.updateReduxTokens(token, refreshToken);

    // Reschedule token refresh
    if (this.config.enableAutoRefresh) {
      const authToken = this.getStoredToken();
      if (authToken) {
        this.scheduleTokenRefresh(authToken);
      }
    }
  }

  private setStoredToken(token: string): void {
    try {
      localStorage.setItem(AUTH_TOKEN_KEY, token);
    } catch (e) {
      console.error('Failed to store auth token:', e);
    }
  }

  private setStoredRefreshToken(refreshToken: string): void {
    try {
      localStorage.setItem(AUTH_REFRESH_TOKEN_KEY, refreshToken);
    } catch (e) {
      console.error('Failed to store refresh token:', e);
    }
  }

  private clearStoredTokens(): void {
    try {
      localStorage.removeItem(AUTH_TOKEN_KEY);
      localStorage.removeItem(AUTH_REFRESH_TOKEN_KEY);
    } catch (e) {
      console.error('Failed to clear stored tokens:', e);
    }
  }

  private updateReduxTokens(token: string, refreshToken: string): void {
    try {
      const state: any = store.getState();
      const current = state?.user || {};
      store.dispatch(updateToken({
        token,
        refreshToken
      }));
    } catch (e) {
      console.warn('Failed to update Redux tokens:', e);
    }
  }

  private forceLogout(reason: string): void {
    // Clear tokens
    this.clearStoredTokens();

    // Clear session
    this.currentSession = null;

    // Cancel timers
    if (this.tokenRefreshTimer) {
      clearTimeout(this.tokenRefreshTimer);
      this.tokenRefreshTimer = null;
    }

    // Dispatch logout
    store.dispatch(logout());

    // Show notification
    store.dispatch(addNotification({
      message: reason,
      type: 'warning'
    }));
  }

  private handleCrossTabMessage(message: any): void {
    if (!message || !message.type) return;

    switch (message.type) {
      case 'AUTH_LOGIN':
        // Another tab logged in
        if (message.token && message.refreshToken) {
          this.updateTokens(message.token, message.refreshToken);
          store.dispatch(loginSuccess(message.user));
          store.dispatch(addNotification({
            message: 'Logged in from another tab',
            type: 'info'
          }));
        }
        break;

      case 'AUTH_LOGOUT':
        // Another tab logged out
        this.forceLogout('Logged out from another tab');
        break;

      case 'TOKEN_REFRESHED':
        // Another tab refreshed the token
        if (message.token && message.refreshToken) {
          this.updateTokens(message.token, message.refreshToken);
        }
        break;

      case 'SESSION_EXPIRED':
        // Another tab detected session expiry
        this.forceLogout('Session expired in another tab');
        break;
    }
  }

  private broadcastAuthEvent(type: string, data?: any): void {
    const message = {
      type,
      timestamp: Date.now(),
      ...data
    };

    // Try BroadcastChannel first
    const broadcastChannel = (this as any).broadcastChannel;
    if (broadcastChannel) {
      try {
        broadcastChannel.postMessage(message);
      } catch (error) {
        console.error('Failed to broadcast via BroadcastChannel:', error);
      }
    }

    // Also use localStorage for fallback (will trigger storage event in other tabs)
    try {
      localStorage.setItem('toolboxai_auth_sync_message', JSON.stringify(message));
      // Clear after a short delay to prevent accumulation
      setTimeout(() => {
        localStorage.removeItem('toolboxai_auth_sync_message');
      }, 100);
    } catch (error) {
      console.error('Failed to broadcast via localStorage:', error);
    }
  }
}

// ================================
// EXPORT SINGLETON
// ================================

// Create and export singleton instance
export const authSync = AuthSyncService.getInstance();

// Global exposure for debugging
if (typeof window !== 'undefined') {
  (window as unknown as Record<string, unknown>).__AUTH_SYNC__ = authSync;

  // Auto-initialize in production mode (in dev, wait for user action)
  if (!import.meta.env.DEV) {
    setTimeout(() => {
      authSync.initialize().catch(error => {
        console.error('❌ Auth sync initialization failed:', error);
      });
    }, 1000);
  }
}

export default AuthSyncService;
