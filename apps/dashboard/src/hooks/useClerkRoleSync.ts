/**
 * Custom hook to sync and manage user roles with Clerk
 */

import { useEffect, useState } from 'react';
import { useUser } from '@clerk/clerk-react';
import { useAppDispatch, useAppSelector } from '../store';
import { setRole } from '../store/slices/userSlice';
import { getUserRoleFromClerk } from '../utils/auth-utils';
import { logger } from '../utils/logger';
import type { UserRole } from '../types/roles';

/**
 * Hook to sync user role from Clerk to Redux store
 * Also ensures a default role is set if none exists
 */
export function useClerkRoleSync() {
  const { user: clerkUser, isLoaded } = useUser();
  const [syncError, setSyncError] = useState<Error | null>(null);

  // Safely access Redux with error handling
  let dispatch: any;
  let reduxRole: UserRole = 'student';

  try {
    dispatch = useAppDispatch();
    reduxRole = useAppSelector((s) => s.user.role);
  } catch (error) {
    // Redux store not available yet - use default
    logger.warn('Redux store not available during role sync initialization');
    setSyncError(error as Error);
  }

  useEffect(() => {
    // Skip if Redux not available or Clerk not loaded
    if (!dispatch || !isLoaded || !clerkUser) return;

    try {
      // Get role from Clerk metadata
      const clerkRole = getUserRoleFromClerk(clerkUser);

      // If Clerk metadata doesn't have a role, set default to student
      if (!clerkUser.publicMetadata?.role) {
        logger.info('No role found in Clerk metadata, setting default to student');

        // Update Clerk user metadata with default role
        clerkUser.update({
          publicMetadata: {
            ...clerkUser.publicMetadata,
            role: 'student',
          },
        }).catch(error => {
          logger.error('Failed to set default role in Clerk:', error);
        });
      }

      // Sync role to Redux if different
      if (clerkRole !== reduxRole) {
        logger.info(`Syncing role from Clerk to Redux: ${clerkRole}`);
        dispatch(setRole(clerkRole));
      }
    } catch (error) {
      logger.error('Error during role sync:', error);
      setSyncError(error as Error);
    }
  }, [isLoaded, clerkUser, reduxRole, dispatch]);

  return {
    role: clerkUser ? getUserRoleFromClerk(clerkUser) : reduxRole,
    isLoading: !isLoaded,
    error: syncError,
  };
}

/**
 * Hook to update user role in Clerk
 */
export function useUpdateClerkRole() {
  const { user: clerkUser } = useUser();
  const dispatch = useAppDispatch();

  const updateRole = async (newRole: UserRole) => {
    if (!clerkUser) {
      logger.error('Cannot update role: No Clerk user found');
      return false;
    }

    try {
      logger.info(`Updating user role to: ${newRole}`);

      await clerkUser.update({
        publicMetadata: {
          ...clerkUser.publicMetadata,
          role: newRole,
        },
      });

      // Update Redux store
      dispatch(setRole(newRole));

      logger.info('Role updated successfully');
      return true;
    } catch (error) {
      logger.error('Failed to update role:', error);
      return false;
    }
  };

  return { updateRole };
}

