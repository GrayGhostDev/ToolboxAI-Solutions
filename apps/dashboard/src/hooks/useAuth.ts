import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../store";
import { signInSuccess, signOut, updateToken, setUser } from "../store/slices/userSlice";
import { refreshToken as refreshTokenAPI, logout as logoutAPI } from "../services/api";
import { AUTH_TOKEN_KEY, AUTH_REFRESH_TOKEN_KEY } from "../config";
import { authSync } from "../services/auth-sync";

export const useAuth = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { isAuthenticated, userId, email, displayName, avatarUrl, role, token, refreshToken, schoolId, classIds } = useAppSelector((state) => state.user);
  
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
      // Initialize auth sync service
      try {
        await authSync.initialize();
      } catch (error) {
        console.error("Failed to initialize auth sync:", error);
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
        // For now, just restore the saved tokens without refreshing
        // The API interceptor will handle refresh when needed
        try {
          // Parse JWT to get user info (if needed)
          const tokenParts = savedToken.split('.');
          if (tokenParts.length === 3) {
            const payload = JSON.parse(atob(tokenParts[1]));
            
            // Check if token is expired
            const now = Date.now() / 1000;
            if (payload.exp && payload.exp < now) {
              // Token expired, try to refresh
              try {
                const response = await refreshTokenAPI(savedRefreshToken);
                
                // Map response fields (handle both camelCase and snake_case)
                const accessToken = response.accessToken || (response as any).access_token;
                const refreshToken = response.refreshToken || (response as any).refresh_token;
                
                localStorage.setItem(AUTH_TOKEN_KEY, accessToken);
                localStorage.setItem(AUTH_REFRESH_TOKEN_KEY, refreshToken);
                
                dispatch(signInSuccess({
                  userId: response.user.id,
                  email: response.user.email,
                  displayName: response.user.displayName || response.user.username,
                  avatarUrl: response.user.avatarUrl,
                  role: response.user.role as any,
                  token: accessToken,
                  refreshToken: refreshToken,
                  schoolId: response.user.schoolId,
                  classIds: response.user.classIds,
                }));
              } catch (refreshError) {
                // Refresh failed, clear tokens
                localStorage.removeItem(AUTH_TOKEN_KEY);
                localStorage.removeItem(AUTH_REFRESH_TOKEN_KEY);
                dispatch(signOut());
              }
            } else {
              // Token still valid, just restore state
              dispatch(setUser({
                token: savedToken,
                refreshToken: savedRefreshToken,
                isAuthenticated: true,
              }));
            }
          }
        } catch (error) {
          console.error("Error initializing auth:", error);
          // Clear invalid tokens
          localStorage.removeItem(AUTH_TOKEN_KEY);
          localStorage.removeItem(AUTH_REFRESH_TOKEN_KEY);
          dispatch(signOut());
        }
      }
    };

    initializeAuth();
  }, [dispatch]);

  const logout = async () => {
    // Use auth sync service for coordinated logout
    await authSync.logout();
  };

  const refreshUserToken = async (): Promise<boolean> => {
    // Use auth sync service for coordinated token refresh with retry logic
    try {
      await authSync.refreshToken();
      return true;
    } catch (error) {
      console.error("Token refresh failed:", error);
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