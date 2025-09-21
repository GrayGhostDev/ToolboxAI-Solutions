import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../store";
import { signOut, setUser } from "../store/slices/userSlice";
import { refreshToken as refreshTokenAPI, logout as logoutAPI } from "../services/api";
import { AUTH_TOKEN_KEY, AUTH_REFRESH_TOKEN_KEY } from "../config";
import { authSync } from "../services/auth-sync";
import { tokenRefreshManager } from "../utils/tokenRefreshManager";
import { logger } from "../utils/logger";
export const useAuth = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { isAuthenticated, userId, email, displayName, avatarUrl, role, token, refreshToken, schoolId, classIds } = useAppSelector((state) => state.user);
  const isInitializedRef = useRef(false);
  const user = {
    id: userId,
    email,
    displayName,
    avatarUrl,
    role,
    schoolId,
    classIds,
  };
  // Initialize authentication from localStorage on app start
  useEffect(() => {
    const initializeAuth = async () => {
      // Skip if already initialized (prevents React StrictMode double initialization)
      if (isInitializedRef.current) {
        return;
      }
      isInitializedRef.current = true;
      // Initialize both auth sync and token refresh manager
      try {
        await authSync.initialize();
        tokenRefreshManager.initialize();
      } catch (error) {
        logger.error("Failed to initialize auth services", error);
      }
      const savedToken = localStorage.getItem(AUTH_TOKEN_KEY);
      const savedRefreshToken = localStorage.getItem(AUTH_REFRESH_TOKEN_KEY);
      // Clear invalid or test tokens
      if (savedToken === 'undefined' || savedToken === 'null' || savedToken === '') {
        localStorage.removeItem(AUTH_TOKEN_KEY);
        localStorage.removeItem(AUTH_REFRESH_TOKEN_KEY);
        return;
      }
      if (savedToken && savedRefreshToken) {
        try {
          // Parse JWT to get user info
          const tokenParts = savedToken.split('.');
          if (tokenParts.length === 3) {
            const payload = JSON.parse(atob(tokenParts[1]));
            // Extract user info from JWT payload
            const userRole = payload.role || 'student';
            const userSub = payload.sub || payload.username || '';
            const userId = payload.user_id || payload.id || '1';
            const userEmail = payload.email || payload.sub || '';
            const schoolId = payload.school_id || payload.schoolId || null;
            const classIds = payload.class_ids || payload.classIds || [];
            logger.info('Restoring auth from token', { role: userRole, userId });
            // Check if token needs refresh
            if (tokenRefreshManager.needsRefresh()) {
              // Let the token refresh manager handle it
              await tokenRefreshManager.refreshToken();
            } else {
              // Token still valid, restore state and schedule refresh
              dispatch(setUser({
                token: savedToken,
                refreshToken: savedRefreshToken,
                isAuthenticated: true,
                role: userRole,
                userId: userId,
                displayName: userSub,
                email: userEmail,
                schoolId: schoolId,
                classIds: classIds,
              }));
              // Update token refresh manager
              tokenRefreshManager.updateToken(savedToken, savedRefreshToken);
            }
          }
        } catch (error) {
          logger.error("Error initializing auth", error);
          // Clear invalid tokens
          localStorage.removeItem(AUTH_TOKEN_KEY);
          localStorage.removeItem(AUTH_REFRESH_TOKEN_KEY);
          dispatch(signOut());
        }
      }
    };
    initializeAuth();
    // Cleanup on unmount
    return () => {
      // Don't cleanup token refresh manager here as it's global
    };
  }, [dispatch]);
  const logout = async () => {
    // Clean up token refresh manager
    tokenRefreshManager.cleanup();
    // Use auth sync service for coordinated logout
    await authSync.logout();
  };
  const refreshUserToken = async (): Promise<boolean> => {
    // Use token refresh manager for coordinated refresh
    try {
      await tokenRefreshManager.forceRefresh();
      return true;
    } catch (error) {
      logger.error("Token refresh failed", error);
      return false;
    }
  };
  const requireAuth = () => {
    if (!isAuthenticated) {
      navigate("/login");
      return false;
    }
    return true;
  };
  const requireRole = (requiredRoles: string[] | string) => {
    if (!isAuthenticated || !userId) {
      navigate("/login");
      return false;
    }
    const roles = Array.isArray(requiredRoles) ? requiredRoles : [requiredRoles];
    if (!roles.includes(role)) {
      navigate("/unauthorized");
      return false;
    }
    return true;
  };
  const hasPermission = (requiredRoles: string[] | string): boolean => {
    if (!isAuthenticated || !userId) return false;
    const roles = Array.isArray(requiredRoles) ? requiredRoles : [requiredRoles];
    return roles.includes(role);
  };
  return {
    // State
    isAuthenticated,
    user,
    token,
    refreshToken,
    // Actions
    logout,
    refreshUserToken,
    // Guards
    requireAuth,
    requireRole,
    hasPermission,
  };
};