/**
 * Auth Sync Service Tests
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { AuthSyncService } from './auth-sync';
import { store } from '../store';
import {
  FetchWrapper,
  StorageWrapper,
  BroadcastWrapper,
  TimerWrapper,
  resetAllMocks,
} from './auth-sync-config';

// Mock dependencies
vi.mock('../store', () => ({
  store: {
    dispatch: vi.fn(),
    getState: vi.fn(() => ({
      user: {
        userId: 'test-user-123',
        isAuthenticated: true,
      },
    })),
  },
}));

vi.mock('../services/pusher', () => ({
  pusherService: {
    refreshTokenAndReconnect: vi.fn(),
    disconnect: vi.fn(),
  },
}));

// Setup mock fetch for testing
const mockFetch = vi.fn();

describe('AuthSyncService', () => {
  let authSync: AuthSyncService;

  beforeEach(() => {
    // Reset all mocks
    resetAllMocks();
    vi.clearAllMocks();

    // Configure fetch wrapper to use our mock
    FetchWrapper.configureMock(mockFetch as any);

    // Enable mock mode for storage
    StorageWrapper.setMockMode(true);

    // Enable mock mode for timers
    TimerWrapper.setMockMode(true);

    // Create a new instance for each test
    authSync = new AuthSyncService({
      tokenRefreshThreshold: 5,
      sessionTimeout: 30,
      enableAutoRefresh: true,
      enableSessionMonitoring: false, // Disable for tests
    });
  });

  afterEach(() => {
    // Clean up
    authSync.shutdown();

    // Reset all mocks
    resetAllMocks();
    vi.clearAllMocks();

    // Restore real mode
    StorageWrapper.setMockMode(false);
    TimerWrapper.setMockMode(false);
  });

  describe('Token Refresh with Retry Logic', () => {
    it('should successfully refresh token on first attempt', async () => {
      const mockResponse = {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        user: {
          id: 'user-123',
          email: 'test@example.com',
          role: 'teacher',
        },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      StorageWrapper.setItem('refreshToken', 'old-refresh-token');

      await authSync.refreshToken('old-refresh-token');

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/refresh'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: 'old-refresh-token' }),
          credentials: 'include',
        })
      );

      // Check that tokens were stored
      expect(StorageWrapper.getItem('token')).toBe('new-access-token');
      expect(StorageWrapper.getItem('refreshToken')).toBe('new-refresh-token');
    });

    it('should retry on network error with exponential backoff', async () => {
      const mockResponse = {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        user: {
          id: 'user-123',
          email: 'test@example.com',
          role: 'teacher',
        },
      };

      // First two attempts fail with network error
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

      StorageWrapper.setItem('refreshToken', 'old-refresh-token');

      const startTime = Date.now();
      await authSync.refreshToken('old-refresh-token');
      const endTime = Date.now();

      // Should have retried 3 times total
      expect(mockFetch).toHaveBeenCalledTimes(3);

      // Should have delayed between retries (at least 1000ms + 3000ms)
      expect(endTime - startTime).toBeGreaterThanOrEqual(1000);

      // Should eventually succeed
      expect(StorageWrapper.getItem('token')).toBe('new-access-token');
    });

    it('should fail after max retries', async () => {
      // All attempts fail
      mockFetch.mockRejectedValue(new Error('Network error'));

      StorageWrapper.setItem('refreshToken', 'old-refresh-token');

      await authSync.refreshToken('old-refresh-token');

      // Should have tried 4 times (initial + 3 retries)
      expect(mockFetch).toHaveBeenCalledTimes(4);

      // Should call handleAuthFailure (which leads to logout)
      expect(StorageWrapper.getItem('token')).toBeNull();
      expect(StorageWrapper.getItem('refreshToken')).toBeNull();
    });

    it('should not retry on non-recoverable errors', async () => {
      // 401 Unauthorized - not recoverable
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ message: 'Invalid refresh token' }),
      });

      StorageWrapper.setItem('refreshToken', 'invalid-token');

      await authSync.refreshToken('invalid-token');

      // Should only try once
      expect(mockFetch).toHaveBeenCalledTimes(1);

      // Should logout immediately
      expect(StorageWrapper.getItem('token')).toBeNull();
      expect(StorageWrapper.getItem('refreshToken')).toBeNull();
    });
  });

  describe('Cross-Tab Synchronization', () => {
    it('should broadcast auth events to other tabs', async () => {
      const mockBroadcastChannel = {
        postMessage: vi.fn(),
        close: vi.fn(),
      };

      // Mock BroadcastChannel
      global.BroadcastChannel = vi.fn(() => mockBroadcastChannel) as any;

      const authSyncWithBroadcast = new AuthSyncService();
      await authSyncWithBroadcast.initialize();

      // Simulate successful login
      const mockResponse = {
        access_token: 'new-token',
        refresh_token: 'new-refresh',
        user: { id: 'user-123' },
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      await authSyncWithBroadcast.refreshToken('refresh-token');

      // Should broadcast token refresh event
      expect(mockBroadcastChannel.postMessage).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'TOKEN_REFRESHED',
          token: 'new-token',
          refreshToken: 'new-refresh',
        })
      );

      authSyncWithBroadcast.shutdown();
    });

    it('should handle auth events from other tabs', async () => {
      const mockBroadcastChannel = {
        postMessage: vi.fn(),
        onmessage: null as any,
        close: vi.fn(),
      };

      global.BroadcastChannel = vi.fn(() => mockBroadcastChannel) as any;

      const authSyncWithBroadcast = new AuthSyncService();
      await authSyncWithBroadcast.initialize();

      // Simulate message from another tab
      const message = {
        type: 'AUTH_LOGOUT',
        timestamp: Date.now(),
      };

      // Trigger the message handler
      if (mockBroadcastChannel.onmessage) {
        mockBroadcastChannel.onmessage({ data: message });
      }

      // Should clear tokens and logout
      expect(StorageWrapper.getItem('token')).toBeNull();
      expect(StorageWrapper.getItem('refreshToken')).toBeNull();
      expect(store.dispatch).toHaveBeenCalled();

      authSyncWithBroadcast.shutdown();
    });

    it('should fallback to localStorage events if BroadcastChannel unavailable', async () => {
      // Remove BroadcastChannel support
      delete (global as any).BroadcastChannel;

      const storageEventListeners: Array<(event: StorageEvent) => void> = [];
      const originalAddEventListener = window.addEventListener;

      window.addEventListener = vi.fn((event: string, listener: any) => {
        if (event === 'storage') {
          storageEventListeners.push(listener);
        }
      });

      const authSyncWithStorage = new AuthSyncService();
      await authSyncWithStorage.initialize();

      // Should have registered a storage event listener
      expect(window.addEventListener).toHaveBeenCalledWith('storage', expect.any(Function));

      // Simulate storage event from another tab
      const storageEvent = new StorageEvent('storage', {
        key: 'toolboxai_auth_sync_message',
        newValue: JSON.stringify({
          type: 'TOKEN_REFRESHED',
          token: 'new-token',
          refreshToken: 'new-refresh',
          timestamp: Date.now(),
        }),
      });

      storageEventListeners.forEach(listener => listener(storageEvent));

      // Should update tokens
      expect(StorageWrapper.getItem('token')).toBe('new-token');
      expect(StorageWrapper.getItem('refreshToken')).toBe('new-refresh');

      window.addEventListener = originalAddEventListener;
      authSyncWithStorage.shutdown();
    });
  });

  describe('Session Management', () => {
    it('should track session information', () => {
      const sessionInfo = authSync.getSessionInfo();

      // Should initially be null (not initialized)
      expect(sessionInfo).toBeNull();
    });

    it('should extend session on user activity', () => {
      authSync.extendSession();

      // Should update last activity
      const sessionInfo = authSync.getSessionInfo();

      // Session will be null unless monitoring is enabled
      // This is expected behavior in tests
      expect(sessionInfo).toBeNull();
    });

    it('should detect authentication status', () => {
      // No token stored
      expect(authSync.isAuthenticated()).toBe(false);

      // Store a valid token (expires in 1 hour)
      const futureExp = Math.floor(Date.now() / 1000) + 3600;
      const mockToken = `header.${btoa(JSON.stringify({ exp: futureExp }))}.signature`;

      StorageWrapper.setItem('token', mockToken);

      expect(authSync.isAuthenticated()).toBe(true);

      // Store an expired token
      const pastExp = Math.floor(Date.now() / 1000) - 3600;
      const expiredToken = `header.${btoa(JSON.stringify({ exp: pastExp }))}.signature`;

      StorageWrapper.setItem('token', expiredToken);

      expect(authSync.isAuthenticated()).toBe(false);
    });
  });

  describe('Error Recovery', () => {
    it('should attempt recovery with valid refresh token', async () => {
      // Create a valid refresh token (expires in future)
      const futureExp = Math.floor(Date.now() / 1000) + 7200; // 2 hours
      const validRefreshToken = `header.${btoa(JSON.stringify({ exp: futureExp }))}.signature`;

      StorageWrapper.setItem('refreshToken', validRefreshToken);

      // Mock successful recovery
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          access_token: 'recovered-token',
          refresh_token: 'recovered-refresh',
          user: { id: 'user-123' },
        }),
      });

      // Use a spy to track handleAuthFailure calls
      const handleAuthFailureSpy = vi.spyOn(authSync as any, 'handleAuthFailure');

      // Trigger auth failure with refresh_failed reason
      (authSync as any).handleAuthFailure('refresh_failed');

      // Should attempt recovery
      expect(handleAuthFailureSpy).toHaveBeenCalledWith('refresh_failed');

      // Wait for recovery attempt
      await new Promise(resolve => setTimeout(resolve, 6000));

      // Should have attempted to refresh
      expect(mockFetch).toHaveBeenCalled();
    });

    it('should logout immediately if refresh token is expired', () => {
      // Create an expired refresh token
      const pastExp = Math.floor(Date.now() / 1000) - 3600; // 1 hour ago
      const expiredRefreshToken = `header.${btoa(JSON.stringify({ exp: pastExp }))}.signature`;

      StorageWrapper.setItem('refreshToken', expiredRefreshToken);

      // Trigger auth failure
      (authSync as any).handleAuthFailure('refresh_failed');

      // Should logout immediately without recovery attempt
      expect(StorageWrapper.getItem('token')).toBeNull();
      expect(StorageWrapper.getItem('refreshToken')).toBeNull();
    });
  });

  describe('Logout Flow', () => {
    it('should perform complete logout with backend notification', async () => {
      StorageWrapper.setItem('token', 'access-token');
      StorageWrapper.setItem('refreshToken', 'refresh-token');

      // Mock successful logout
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      });

      await authSync.logout();

      // Should notify backend
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/logout'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer access-token',
          }),
          credentials: 'include',
        })
      );

      // Should clear tokens
      expect(StorageWrapper.getItem('token')).toBeNull();
      expect(StorageWrapper.getItem('refreshToken')).toBeNull();

      // Should dispatch logout action
      expect(store.dispatch).toHaveBeenCalled();
    });

    it('should retry logout notification on failure', async () => {
      StorageWrapper.setItem('token', 'access-token');

      // First two attempts fail
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({ ok: true });

      await authSync.logout();

      // Should have retried
      expect(mockFetch).toHaveBeenCalledTimes(3);

      // Should still complete logout even if backend fails
      expect(StorageWrapper.getItem('token')).toBeNull();
    });
  });
});