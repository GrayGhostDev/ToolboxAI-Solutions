/**
 * JWT Token Refresh Manager
 * Handles automatic token refresh to prevent unexpected logouts
 * Implements OAuth 3.0 best practices with 15-minute access tokens
 */

import { refreshToken as refreshTokenAPI } from '../services/api';
import { store } from '../store';
import { updateToken, signOut } from '../store/slices/userSlice';
import { AUTH_TOKEN_KEY, AUTH_REFRESH_TOKEN_KEY } from '../config';

interface TokenRefreshConfig {
  refreshThreshold: number; // Minutes before expiry to refresh
  maxRetries: number;
  retryDelay: number; // Base delay in ms
  enableAutoRefresh: boolean;
}

interface TokenInfo {
  token: string;
  refreshToken: string;
  expiresAt: number;
}

class TokenRefreshManager {
  private config: TokenRefreshConfig;
  private refreshTimer: NodeJS.Timeout | null = null;
  private isRefreshing = false;
  private refreshPromise: Promise<void> | null = null;
  private retryCount = 0;
  private listeners: Set<(token: string) => void> = new Set();

  constructor(config?: Partial<TokenRefreshConfig>) {
    this.config = {
      refreshThreshold: 5, // Refresh 5 minutes before expiry
      maxRetries: 3,
      retryDelay: 1000, // 1 second base delay
      enableAutoRefresh: true,
      ...config,
    };
  }

  /**
   * Initialize the token refresh manager
   */
  public initialize(): void {
    console.log('🔐 Token Refresh Manager initialized');

    // Check for existing tokens
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    const refreshToken = localStorage.getItem(AUTH_REFRESH_TOKEN_KEY);

    if (token && refreshToken) {
      const tokenInfo = this.parseToken(token);
      if (tokenInfo) {
        this.scheduleRefresh(tokenInfo.expiresAt);
      }
    }

    // Listen for storage events (cross-tab synchronization)
    window.addEventListener('storage', this.handleStorageChange);
  }

  /**
   * Parse JWT token to extract expiry time
   */
  private parseToken(token: string): { expiresAt: number } | null {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) return null;

      const payload = JSON.parse(atob(parts[1]));
      const expiresAt = payload.exp ? payload.exp * 1000 : Date.now() + 15 * 60 * 1000; // Default 15 minutes

      return { expiresAt };
    } catch (error) {
      console.error('Failed to parse token:', error);
      return null;
    }
  }

  /**
   * Schedule automatic token refresh
   */
  private scheduleRefresh(expiresAt: number): void {
    if (!this.config.enableAutoRefresh) return;

    // Clear existing timer
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    const now = Date.now();
    const refreshThresholdMs = this.config.refreshThreshold * 60 * 1000;
    const refreshAt = expiresAt - refreshThresholdMs;
    const delay = Math.max(0, refreshAt - now);

    if (delay > 0) {
      console.log(`⏰ Token refresh scheduled in ${Math.round(delay / 1000)} seconds`);

      this.refreshTimer = setTimeout(() => {
        this.refreshToken();
      }, delay);
    } else if (expiresAt > now) {
      // Token expires soon, refresh immediately
      console.log('⚠️ Token expires soon, refreshing immediately');
      this.refreshToken();
    } else {
      // Token already expired
      console.log('❌ Token expired, user needs to re-authenticate');
      this.handleRefreshFailure();
    }
  }

  /**
   * Refresh the JWT token
   */
  public async refreshToken(): Promise<void> {
    // If already refreshing, wait for the existing refresh
    if (this.isRefreshing && this.refreshPromise) {
      return this.refreshPromise;
    }

    this.isRefreshing = true;
    this.refreshPromise = this.performRefresh();

    try {
      await this.refreshPromise;
    } finally {
      this.isRefreshing = false;
      this.refreshPromise = null;
    }
  }

  /**
   * Perform the actual token refresh
   */
  private async performRefresh(): Promise<void> {
    const currentRefreshToken = localStorage.getItem(AUTH_REFRESH_TOKEN_KEY);

    if (!currentRefreshToken) {
      console.error('No refresh token available');
      this.handleRefreshFailure();
      return;
    }

    try {
      console.log('🔄 Refreshing token...');

      const response = await refreshTokenAPI(currentRefreshToken);

      // Handle different response formats (access_token vs accessToken)
      const newAccessToken = response.access_token || response.accessToken;
      const newRefreshToken = response.refresh_token || response.refreshToken || currentRefreshToken;

      if (newAccessToken) {
        // Update tokens in localStorage
        localStorage.setItem(AUTH_TOKEN_KEY, newAccessToken);
        localStorage.setItem(AUTH_REFRESH_TOKEN_KEY, newRefreshToken);

        // Update tokens in Redux store
        store.dispatch(updateToken({
          token: newAccessToken,
          refreshToken: newRefreshToken,
        }));

        // Parse new token and schedule next refresh
        const tokenInfo = this.parseToken(newAccessToken);
        if (tokenInfo) {
          this.scheduleRefresh(tokenInfo.expiresAt);
        }

        // Notify listeners
        this.notifyListeners(newAccessToken);

        // Reset retry count on success
        this.retryCount = 0;

        console.log('✅ Token refreshed successfully');
      } else {
        throw new Error('Invalid refresh response');
      }
    } catch (error) {
      console.error('Token refresh failed:', error);

      // Retry with exponential backoff
      if (this.retryCount < this.config.maxRetries) {
        this.retryCount++;
        const delay = this.config.retryDelay * Math.pow(2, this.retryCount - 1);

        console.log(`🔁 Retrying token refresh (attempt ${this.retryCount}/${this.config.maxRetries}) in ${delay}ms`);

        await new Promise(resolve => setTimeout(resolve, delay));
        return this.performRefresh();
      } else {
        this.handleRefreshFailure();
      }
    }
  }

  /**
   * Handle refresh failure
   */
  private handleRefreshFailure(): void {
    console.error('❌ Token refresh failed permanently');

    // Clear tokens
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_REFRESH_TOKEN_KEY);

    // Sign out user
    store.dispatch(signOut());

    // Clear refresh timer
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }

    // Notify user (you might want to show a toast notification)
    if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
      window.location.href = '/login?reason=session_expired';
    }
  }

  /**
   * Handle storage changes (cross-tab synchronization)
   */
  private handleStorageChange = (event: StorageEvent): void => {
    if (event.key === AUTH_TOKEN_KEY && event.newValue) {
      // Another tab refreshed the token
      const tokenInfo = this.parseToken(event.newValue);
      if (tokenInfo) {
        console.log('🔄 Token updated from another tab');
        this.scheduleRefresh(tokenInfo.expiresAt);
        this.notifyListeners(event.newValue);
      }
    } else if (event.key === AUTH_TOKEN_KEY && !event.newValue) {
      // Token was removed (logout in another tab)
      console.log('👋 User logged out in another tab');
      this.cleanup();
      store.dispatch(signOut());
    }
  };

  /**
   * Add a listener for token updates
   */
  public addListener(listener: (token: string) => void): void {
    this.listeners.add(listener);
  }

  /**
   * Remove a listener
   */
  public removeListener(listener: (token: string) => void): void {
    this.listeners.delete(listener);
  }

  /**
   * Notify all listeners of token update
   */
  private notifyListeners(token: string): void {
    this.listeners.forEach(listener => {
      try {
        listener(token);
      } catch (error) {
        console.error('Error in token listener:', error);
      }
    });
  }

  /**
   * Manually trigger a token refresh
   */
  public async forceRefresh(): Promise<void> {
    console.log('🔄 Force refreshing token...');
    this.retryCount = 0; // Reset retry count for manual refresh
    await this.refreshToken();
  }

  /**
   * Update token and schedule refresh
   */
  public updateToken(token: string, refreshToken: string): void {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
    localStorage.setItem(AUTH_REFRESH_TOKEN_KEY, refreshToken);

    const tokenInfo = this.parseToken(token);
    if (tokenInfo) {
      this.scheduleRefresh(tokenInfo.expiresAt);
    }
  }

  /**
   * Check if token needs refresh
   */
  public needsRefresh(): boolean {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (!token) return false;

    const tokenInfo = this.parseToken(token);
    if (!tokenInfo) return false;

    const now = Date.now();
    const refreshThresholdMs = this.config.refreshThreshold * 60 * 1000;

    return (tokenInfo.expiresAt - now) < refreshThresholdMs;
  }

  /**
   * Get time until token expiry in milliseconds
   */
  public getTimeUntilExpiry(): number {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (!token) return 0;

    const tokenInfo = this.parseToken(token);
    if (!tokenInfo) return 0;

    return Math.max(0, tokenInfo.expiresAt - Date.now());
  }

  /**
   * Clean up resources
   */
  public cleanup(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }

    window.removeEventListener('storage', this.handleStorageChange);
    this.listeners.clear();
    this.isRefreshing = false;
    this.refreshPromise = null;
  }

  /**
   * Get manager status for debugging
   */
  public getStatus(): {
    isRefreshing: boolean;
    hasToken: boolean;
    timeUntilExpiry: number;
    needsRefresh: boolean;
    retryCount: number;
  } {
    return {
      isRefreshing: this.isRefreshing,
      hasToken: !!localStorage.getItem(AUTH_TOKEN_KEY),
      timeUntilExpiry: this.getTimeUntilExpiry(),
      needsRefresh: this.needsRefresh(),
      retryCount: this.retryCount,
    };
  }
}

// Export singleton instance
export const tokenRefreshManager = new TokenRefreshManager();

// Auto-initialize in browser environment
if (typeof window !== 'undefined') {
  tokenRefreshManager.initialize();
}

// Export for testing
export { TokenRefreshManager };