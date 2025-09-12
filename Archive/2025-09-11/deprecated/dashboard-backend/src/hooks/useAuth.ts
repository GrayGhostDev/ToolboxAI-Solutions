import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../store";
import { signInSuccess, signOut, updateToken, setUser } from "../store/slices/userSlice";
import { refreshToken as refreshTokenAPI, logout as logoutAPI } from "../services/api";
import { AUTH_TOKEN_KEY, AUTH_REFRESH_TOKEN_KEY } from "../config";

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
      const savedToken = localStorage.getItem(AUTH_TOKEN_KEY);
      const savedRefreshToken = localStorage.getItem(AUTH_REFRESH_TOKEN_KEY);

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
    try {
      // Call logout API to invalidate server-side session
      if (refreshToken) {
        await logoutAPI();
      }
    } catch (error) {
      // Continue with logout even if API call fails
      console.warn("Logout API call failed:", error);
    } finally {
      // Clear local storage and Redux state
      localStorage.removeItem(AUTH_TOKEN_KEY);
      localStorage.removeItem(AUTH_REFRESH_TOKEN_KEY);
      dispatch(signOut());
      navigate("/login");
    }
  };

  const refreshUserToken = async (): Promise<boolean> => {
    const savedRefreshToken = localStorage.getItem(AUTH_REFRESH_TOKEN_KEY);
    
    if (!savedRefreshToken) {
      logout();
      return false;
    }

    try {
      const response = await refreshTokenAPI(savedRefreshToken);
      
      // Update tokens
      localStorage.setItem(AUTH_TOKEN_KEY, response.accessToken);
      localStorage.setItem(AUTH_REFRESH_TOKEN_KEY, response.refreshToken);
      
      // Update Redux state
      dispatch(updateToken({
        token: response.accessToken,
        refreshToken: response.refreshToken,
      }));
      
      return true;
    } catch (error) {
      // Refresh failed, logout user
      logout();
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