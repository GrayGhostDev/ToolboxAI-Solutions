/**
 * Clerk Role Guard Component (2025)
 * Role-based access control with Clerk authentication
 */

import React from 'react';
import { useUser } from '@clerk/clerk-react';
import { Box, Alert, Text, Button } from '@mantine/core';
import { IconShield, IconArrowLeft } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import type { UserRole } from '../../types/roles';
import { ROLE_PERMISSIONS } from '../../types/roles';

interface ClerkRoleGuardProps {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
  requiredPermissions?: string[];
  fallback?: React.ReactNode;
  redirectTo?: string;
}

export const ClerkRoleGuard = ({
  children,
  allowedRoles,
  requiredPermissions,
  fallback,
  redirectTo = '/dashboard'
}: ClerkRoleGuardProps) => {
  const { user, isLoaded } = useUser();
  const navigate = useNavigate();

  // Show loading state while user data is loading
  if (!isLoaded) {
    return (
      <Box
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: 200
        }}
      >
        <Text>Loading...</Text>
      </Box>
    );
  }

  // User not signed in
  if (!user) {
    return (
      <Box
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          padding: '1.5rem',
          textAlign: 'center'
        }}
      >
        <Alert color="yellow" title="Authentication Required" style={{ maxWidth: 500 }}>
          <Text size="sm">
            You need to be signed in to access this content.
          </Text>
        </Alert>
      </Box>
    );
  }

  // Get user role from Clerk metadata
  const userRole = (user.publicMetadata?.role as UserRole) || 'student';
  const userPermissions = ROLE_PERMISSIONS[userRole];

  // Check role-based access
  if (allowedRoles && !allowedRoles.includes(userRole)) {
    const accessDeniedContent = (
      <Box
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          padding: '1.5rem',
          textAlign: 'center',
          maxWidth: 600,
          margin: '0 auto'
        }}
      >
        <Alert
          color="red"
          title={
            <Box style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <IconShield size={20} />
              <span>Access Denied</span>
            </Box>
          }
          style={{ width: '100%', marginBottom: '1.5rem' }}
        >
          <Text size="sm" style={{ marginBottom: '1rem' }}>
            Your current role ({userRole}) does not have permission to access this content.
          </Text>
          <Text size="sm" c="dimmed">
            Required roles: {allowedRoles.join(', ')}
          </Text>
        </Alert>

        <Box style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
          <Button
            variant="filled"
            leftSection={<IconArrowLeft size={16} />}
            onClick={() => navigate(redirectTo)}
          >
            Go Back
          </Button>

          {process.env.NODE_ENV === 'development' && (
            <Button
              variant="outline"
              color="yellow"
              onClick={() => {
                // In development, allow role switching for testing
                console.log('Development mode: Role switching not implemented in this guard');
              }}
            >
              Switch Role (Dev)
            </Button>
          )}
        </Box>
      </Box>
    );

    return fallback || accessDeniedContent;
  }

  // Check permission-based access
  if (requiredPermissions && requiredPermissions.length > 0) {
    const hasAllPermissions = requiredPermissions.every(permission => {
      const permissionKey = permission as keyof typeof userPermissions;
      return userPermissions[permissionKey] === true;
    });

    if (!hasAllPermissions) {
      const missingPermissions = requiredPermissions.filter(permission => {
        const permissionKey = permission as keyof typeof userPermissions;
        return userPermissions[permissionKey] !== true;
      });

      const permissionDeniedContent = (
        <Box
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            padding: '1.5rem',
            textAlign: 'center',
            maxWidth: 600,
            margin: '0 auto'
          }}
        >
          <Alert
            color="red"
            title={
              <Box style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <IconShield size={20} />
                <span>Insufficient Permissions</span>
              </Box>
            }
            style={{ width: '100%', marginBottom: '1.5rem' }}
          >
            <Text size="sm" style={{ marginBottom: '1rem' }}>
              Your current role ({userRole}) does not have the required permissions for this action.
            </Text>
            <Text size="sm" c="dimmed">
              Missing permissions: {missingPermissions.join(', ')}
            </Text>
          </Alert>

          <Button
            variant="filled"
            leftSection={<IconArrowLeft size={16} />}
            onClick={() => navigate(redirectTo)}
          >
            Go Back
          </Button>
        </Box>
      );

      return fallback || permissionDeniedContent;
    }
  }

  // Access granted
  return <>{children}</>;
};

// Hook for checking permissions in components
export const useClerkPermissions = () => {
  const { user, isLoaded } = useUser();

  const checkRole = React.useCallback((allowedRoles: UserRole[]): boolean => {
    if (!isLoaded || !user) return false;
    const userRole = (user.publicMetadata?.role as UserRole) || 'student';
    return allowedRoles.includes(userRole);
  }, [user, isLoaded]);

  const checkPermission = React.useCallback((permission: string): boolean => {
    if (!isLoaded || !user) return false;
    const userRole = (user.publicMetadata?.role as UserRole) || 'student';
    const userPermissions = ROLE_PERMISSIONS[userRole];
    const permissionKey = permission as keyof typeof userPermissions;
    return userPermissions[permissionKey] === true;
  }, [user, isLoaded]);

  const checkPermissions = React.useCallback((permissions: string[]): boolean => {
    if (!isLoaded || !user) return false;
    const userRole = (user.publicMetadata?.role as UserRole) || 'student';
    const userPermissions = ROLE_PERMISSIONS[userRole];
    return permissions.every(permission => {
      const permissionKey = permission as keyof typeof userPermissions;
      return userPermissions[permissionKey] === true;
    });
  }, [user, isLoaded]);

  const getUserRole = React.useCallback((): UserRole | null => {
    if (!isLoaded || !user) return null;
    return (user.publicMetadata?.role as UserRole) || 'student';
  }, [user, isLoaded]);

  return {
    checkRole,
    checkPermission,
    checkPermissions,
    getUserRole,
    isLoaded,
    user
  };
};

export default ClerkRoleGuard;