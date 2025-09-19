/**
 * Authentication Context Provider
 * Manages user authentication state and role-based access
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, AuthResponse } from '../types/api';
import { UserRole } from '../types/roles';
import { getUserConfig, AUTH_CONFIG } from '../config/users';
import ApiClient, { getMyProfile, updateUser as apiUpdateUser } from '../services/api';
import { store } from '../store';
import { addNotification } from '../store/slices/uiSlice';
import { signInSuccess, signOut } from '../store/slices/userSlice';
import { AUTH_TOKEN_KEY, AUTH_REFRESH_TOKEN_KEY } from '../config';

interface AuthContextType {
  user: User | null;
  userConfig: ReturnType<typeof getUserConfig> | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (userData: any) => Promise<void>;
  updateProfile: (updates: Partial<User>) => Promise<void>;
  refreshAuth: () => Promise<AuthResponse>;
  checkPermission: (permission: string) => boolean;
  switchRole: (role: UserRole) => void; // For development/testing
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [userConfig, setUserConfig] = useState<ReturnType<typeof getUserConfig> | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [tokenRefreshTimer, setTokenRefreshTimer] = useState<NodeJS.Timeout | null>(null);
  const navigate = useNavigate();
  const apiClient = new ApiClient();

  // Initialize authentication from stored token
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem(AUTH_TOKEN_KEY);
      if (token) {
        try {
          // Verify token and get user data
          const response = await getMyProfile();
          if (response) {
            setUser(response);
            const config = getUserConfig(response.role as UserRole);
            setUserConfig(config);
          }
        } catch (error) {
          console.error('Failed to restore authentication:', error);
          localStorage.removeItem(AUTH_TOKEN_KEY);
          localStorage.removeItem(AUTH_REFRESH_TOKEN_KEY);
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  // Login function - secure authentication via backend
  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    try {
      // Validate password meets requirements before sending
      if (password.length < AUTH_CONFIG.passwordRequirements.minLength) {
        throw new Error(`Password must be at least ${AUTH_CONFIG.passwordRequirements.minLength} characters`);
      }

      // All authentication is handled by the backend
      // Never validate credentials on the frontend
      const response = await apiClient.login(email, password);
      handleAuthSuccess(response);
    } catch (error: any) {
      store.dispatch(addNotification({
        type: 'error',
        message: error.message || 'Login failed. Please check your credentials.',
        autoHide: false,
      }));
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [apiClient, navigate]);

  // Schedule automatic token refresh
  const scheduleTokenRefresh = useCallback((accessToken: string) => {
    // Clear existing timer
    if (tokenRefreshTimer) {
      clearTimeout(tokenRefreshTimer);
    }
    
    try {
      // Parse JWT to get expiry time
      const payload = JSON.parse(atob(accessToken.split('.')[1]));
      const expiryTime = payload.exp * 1000; // Convert to milliseconds
      
      // Schedule refresh 5 minutes before expiry
      const refreshTime = expiryTime - Date.now() - (5 * 60 * 1000);
      
      if (refreshTime > 0) {
        const timer = setTimeout(async () => {
          try {
            await refreshAuth();
          } catch (error) {
            console.error('Automatic token refresh failed:', error);
          }
        }, refreshTime);
        
        setTokenRefreshTimer(timer);
        console.log(`Token refresh scheduled for ${new Date(expiryTime - 5 * 60 * 1000).toISOString()}`);
      }
    } catch (error) {
      console.error('Failed to schedule token refresh:', error);
    }
  }, [tokenRefreshTimer]);
  
  // Handle successful authentication
  const handleAuthSuccess = useCallback((response: AuthResponse) => {
    const { user, accessToken, refreshToken } = response;

    // Store tokens
    localStorage.setItem(AUTH_TOKEN_KEY, accessToken);
    localStorage.setItem(AUTH_REFRESH_TOKEN_KEY, refreshToken);

    // Schedule automatic token refresh
    scheduleTokenRefresh(accessToken);

    // Set user state in React context
    setUser(user);
    const config = getUserConfig(user.role as UserRole);
    setUserConfig(config);

    // CRITICAL: Also update Redux store to maintain consistency
    store.dispatch(signInSuccess({
      userId: user.id,
      email: user.email,
      displayName: user.displayName || user.firstName || user.username,
      avatarUrl: user.avatarUrl,
      role: user.role as any,
      token: accessToken,
      refreshToken: refreshToken,
      schoolId: user.schoolId,
      classIds: user.classIds || [],
    }));

    // Navigate to appropriate dashboard
    navigate(config.defaultRoute);

    // Show success notification
    store.dispatch(addNotification({
      type: 'success',
      message: `Welcome back, ${user.displayName || user.firstName}!`,
      autoHide: true,
    }));
  }, [navigate, scheduleTokenRefresh]);

  // Logout function
  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      await apiClient.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear token refresh timer
      if (tokenRefreshTimer) {
        clearTimeout(tokenRefreshTimer);
        setTokenRefreshTimer(null);
      }
      
      // Clear local state and storage
      setUser(null);
      setUserConfig(null);
      localStorage.removeItem(AUTH_TOKEN_KEY);
      localStorage.removeItem(AUTH_REFRESH_TOKEN_KEY);

      // Also clear Redux store
      store.dispatch(signOut());

      // Navigate to login
      navigate('/login');
      
      // Show notification
      store.dispatch(addNotification({
        type: 'info',
        message: 'You have been logged out successfully.',
        autoHide: true,
      }));
      
      setIsLoading(false);
    }
  }, [apiClient, navigate, tokenRefreshTimer]);

  // Register function
  const register = useCallback(async (userData: any) => {
    setIsLoading(true);
    try {
      const response = await apiClient.register(userData);
      handleAuthSuccess(response);
      
      // Show welcome notification
      store.dispatch(addNotification({
        type: 'success',
        message: 'Registration successful! Welcome to ToolBoxAI.',
        autoHide: true,
      }));
    } catch (error: any) {
      store.dispatch(addNotification({
        type: 'error',
        message: error.message || 'Registration failed. Please try again.',
        autoHide: false,
      }));
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [apiClient]);

  // Update user profile
const updateProfile = useCallback(async (updates: Partial<User>) => {
    if (!user) return;
    
    setIsLoading(true);
    try {
      const updatedUser = await apiUpdateUser(user.id, updates);
      setUser(updatedUser);
      
      store.dispatch(addNotification({
        type: 'success',
        message: 'Profile updated successfully.',
        autoHide: true,
      }));
    } catch (error: any) {
      store.dispatch(addNotification({
        type: 'error',
        message: error.message || 'Failed to update profile.',
        autoHide: false,
      }));
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [user, apiClient]);

  // Refresh authentication
  const refreshAuth = useCallback(async () => {
    const refreshToken = localStorage.getItem(AUTH_REFRESH_TOKEN_KEY);
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    
    try {
      const response = await apiClient.refreshToken(refreshToken);
      handleAuthSuccess(response);
      
      // Also refresh WebSocket connection with new token
      const { websocketService } = await import('../services/websocket');
      if (websocketService.isConnected()) {
        await websocketService.refreshToken(response.accessToken);
      }
      
      return response;
    } catch (error) {
      await logout();
      throw error;
    }
  }, [apiClient, handleAuthSuccess, logout]);

// Check permission based on user role
  const checkPermission = useCallback((permission: string): boolean => {
    if (!userConfig) return false;
    
    const permissions = {
      'view.dashboard': userConfig.features.dashboard.showWelcomeMessage,
      'view.analytics': userConfig.features.dashboard.showStatistics,
      'view.leaderboard': userConfig.features.dashboard.showLeaderboard,
      'view.calendar': userConfig.features.dashboard.showCalendar,
      'use.ai': userConfig.features.dashboard.showAIAssistant,
      'play.roblox': userConfig.features.dashboard.showRobloxIntegration,
      'send.messages': userConfig.features.notifications.types.includes('message'),
      // Add more permission mappings as needed
    } as Record<string, boolean>;
    
    return Boolean(permissions[permission]);
  }, [userConfig]);

  // Switch role (for development/testing)
  const switchRole = useCallback((role: UserRole) => {
    if (process.env.NODE_ENV !== 'development') {
      console.warn('Role switching is only available in development mode');
      return;
    }
    
    const testUser = Object.values(TEST_USERS).find(u => u.role === role);
    if (testUser) {
      login(testUser.email, testUser.password);
    }
  }, [login]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (tokenRefreshTimer) {
        clearTimeout(tokenRefreshTimer);
      }
    };
  }, [tokenRefreshTimer]);
  
// Initialize WebSocket connection when authenticated
  useEffect(() => {
    const initWebSocket = async () => {
      const isAuth = !!user;
      if (user && isAuth) {
        const token = localStorage.getItem(AUTH_TOKEN_KEY);
        if (token) {
          const { websocketService } = await import('../services/websocket');
          try {
            await websocketService.connect(token);
            
            // Register token refresh callback
            websocketService.onTokenRefresh(() => {
              refreshAuth();
            });
          } catch (error) {
            console.error('Failed to connect WebSocket:', error);
          }
        }
      }
    };
    
    initWebSocket();
  }, [user, refreshAuth]);

  const value = {
    user,
    userConfig,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    register,
    updateProfile,
    refreshAuth,
    checkPermission,
    switchRole,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};