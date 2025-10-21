/**
 * Clerk Authentication Context Provider (2025)
 * Manages user authentication state using Clerk
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  useAuth as useClerkAuth,
  useUser,
  useSession,
  SignIn,
  SignUp,
  UserButton,
  SignOutButton
} from '@clerk/clerk-react';
import { type User } from '../types/api';
import type { UserRole } from '../types/roles';
import { getUserConfig } from '@/config/users.ts';
import { store } from '../store';
import { addNotification } from '../store/slices/uiSlice';
import { signInSuccess, signOut as signOutAction } from '../store/slices/userSlice';
import { logger } from '../utils/logger';

interface ClerkAuthContextType {
  user: User | null;
  clerkUser: any;
  userConfig: ReturnType<typeof getUserConfig> | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (userData: any) => Promise<void>;
  updateProfile: (updates: Partial<User>) => Promise<void>;
  checkPermission: (permission: string) => boolean;
  switchRole: (role: UserRole) => void;
  // Clerk-specific exports
  SignIn: typeof SignIn;
  SignUp: typeof SignUp;
  UserButton: typeof UserButton;
  SignOutButton: typeof SignOutButton;
}

const ClerkAuthContext = createContext<ClerkAuthContextType | undefined>(undefined);

// Export the context for use in unified auth hook
export { ClerkAuthContext };

export const useAuth = () => {
  const context = useContext(ClerkAuthContext);
  // Don't throw error - return null if provider is missing
  // This allows useUnifiedAuth to conditionally use the correct auth provider
  return context || null;
};

export const ClerkAuthProvider: React.FunctionComponent<{ children: React.ReactNode }> = ({ children }) => {
  const { isLoaded, userId, sessionId, getToken, signOut } = useClerkAuth();
  const { user: clerkUser, isLoaded: userLoaded } = useUser();
  const { session } = useSession();
  const navigate = useNavigate();

  const [user, setUser] = useState<User | null>(null);
  const [userConfig, setUserConfig] = useState<ReturnType<typeof getUserConfig> | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Map Clerk user to application User type
  useEffect(() => {
    if (isLoaded && userLoaded) {
      if (clerkUser) {
        // Map Clerk user to our User type
        const mappedUser: User = {
          id: clerkUser.id,
          email: clerkUser.primaryEmailAddress?.emailAddress || '',
          username: clerkUser.username || clerkUser.firstName || 'User',
          firstName: clerkUser.firstName || '',
          lastName: clerkUser.lastName || '',
          displayName: `${clerkUser.firstName || ''} ${clerkUser.lastName || ''}`.trim() || clerkUser.username || 'User',
          avatarUrl: clerkUser.imageUrl || undefined,
          role: (clerkUser.publicMetadata?.role as UserRole) || 'student',
          schoolId: clerkUser.publicMetadata?.schoolId as string | undefined,
          schoolName: clerkUser.publicMetadata?.schoolName as string | undefined,
          classIds: clerkUser.publicMetadata?.classIds as string[] | undefined,
          parentIds: clerkUser.publicMetadata?.parentIds as string[] | undefined,
          childIds: clerkUser.publicMetadata?.childIds as string[] | undefined,
          isActive: true,
          isVerified: clerkUser.primaryEmailAddress?.verification?.status === 'verified' || false,
          totalXP: (clerkUser.publicMetadata?.totalXP as number) || 0,
          level: (clerkUser.publicMetadata?.level as number) || 1,
          lastLogin: new Date().toISOString(),
          createdAt: clerkUser.createdAt ? new Date(clerkUser.createdAt).toISOString() : new Date().toISOString(),
          updatedAt: clerkUser.updatedAt ? new Date(clerkUser.updatedAt).toISOString() : new Date().toISOString(),
          status: 'active' as const
        };

        setUser(mappedUser);
        const config = getUserConfig(mappedUser.role as UserRole);
        setUserConfig(config);

        // Dispatch to Redux store
        store.dispatch(signInSuccess({
          user: mappedUser,
          token: sessionId || '',
          refreshToken: ''
        }));
      } else {
        setUser(null);
        setUserConfig(null);
      }
      setIsLoading(false);
    }
  }, [isLoaded, userLoaded, clerkUser, sessionId]);

  // Login function - Clerk handles authentication
  const login = useCallback(async (email: string, password: string) => {
    // This is handled by Clerk's SignIn component
    // Adding notification for compatibility
    store.dispatch(addNotification({
      type: 'info',
      message: 'Please use the sign-in form to authenticate',
      autoHide: true,
    }));
  }, []);

  // Logout function
  const logout = useCallback(async () => {
    try {
      await signOut();
      store.dispatch(signOutAction());
      navigate('/');
      store.dispatch(addNotification({
        type: 'success',
        message: 'Successfully logged out',
        autoHide: true,
      }));
    } catch (error) {
      logger.error('Logout error:', error);
      store.dispatch(addNotification({
        type: 'error',
        message: 'Logout failed',
        autoHide: false,
      }));
    }
  }, [signOut, navigate]);

  // Register function - Clerk handles registration
  const register = useCallback(async (userData: any) => {
    // This is handled by Clerk's SignUp component
    store.dispatch(addNotification({
      type: 'info',
      message: 'Please use the sign-up form to register',
      autoHide: true,
    }));
  }, []);

  // Update profile function
  const updateProfile = useCallback(async (updates: Partial<User>) => {
    if (!clerkUser) return;

    try {
      await clerkUser.update({
        firstName: updates.firstName,
        lastName: updates.lastName,
        username: updates.username,
        publicMetadata: {
          ...clerkUser.publicMetadata,
          role: updates.role
        }
      });

      store.dispatch(addNotification({
        type: 'success',
        message: 'Profile updated successfully',
        autoHide: true,
      }));
    } catch (error) {
      logger.error('Profile update error:', error);
      store.dispatch(addNotification({
        type: 'error',
        message: 'Failed to update profile',
        autoHide: false,
      }));
    }
  }, [clerkUser]);

  // Check permission
  const checkPermission = useCallback((permission: string) => {
    if (!userConfig) return false;
    return userConfig.permissions.includes(permission);
  }, [userConfig]);

  // Switch role (for development/testing)
  const switchRole = useCallback((role: UserRole) => {
    if (!user) return;

    const updatedUser = { ...user, role };
    setUser(updatedUser);
    const config = getUserConfig(role);
    setUserConfig(config);

    store.dispatch(addNotification({
      type: 'info',
      message: `Switched to ${role} role (dev mode)`,
      autoHide: true,
    }));
  }, [user]);

  const value: ClerkAuthContextType = {
    user,
    clerkUser,
    userConfig,
    isAuthenticated: !!userId,
    isLoading: !isLoaded || !userLoaded || isLoading,
    login,
    logout,
    register,
    updateProfile,
    checkPermission,
    switchRole,
    // Export Clerk components for use in the app
    SignIn,
    SignUp,
    UserButton,
    SignOutButton
  };

  return (
    <ClerkAuthContext.Provider value={value}>
      {children}
    </ClerkAuthContext.Provider>
  );
};