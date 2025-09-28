/**
 * Clerk Role Guard Component (2025)
 * Role-based access control with Clerk authentication
 */

import React from 'react';
import { useUser } from '@clerk/clerk-react';
import { Box, Alert, AlertTitle, Typography, Button } from '@mui/material';
import { SecurityRounded, ArrowBackRounded } from '@mui/icons-material';
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
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: 200
        }}
      >
        <Typography>Loading...</Typography>
      </Box>
    );
  }

  // User not signed in
  if (!user) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          p: 3,
          textAlign: 'center'
        }}
      >
        <Alert severity="warning" sx={{ maxWidth: 500 }}>
          <AlertTitle>Authentication Required</AlertTitle>
          <Typography variant="body2">
            You need to be signed in to access this content.
          </Typography>
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
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          p: 3,
          textAlign: 'center',
          maxWidth: 600,
          mx: 'auto'
        }}
      >
        <Alert severity="error" sx={{ width: '100%', mb: 3 }}>
          <AlertTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SecurityRounded />
            Access Denied
          </AlertTitle>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Your current role ({userRole}) does not have permission to access this content.
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Required roles: {allowedRoles.join(', ')}
          </Typography>
        </Alert>

        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
          <Button
            variant="contained"
            startIcon={<ArrowBackRounded />}
            onClick={() => navigate(redirectTo)}
          >
            Go Back
          </Button>

          {process.env.NODE_ENV === 'development' && (
            <Button
              variant="outlined"
              color="warning"
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
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            p: 3,
            textAlign: 'center',
            maxWidth: 600,
            mx: 'auto'
          }}
        >
          <Alert severity="error" sx={{ width: '100%', mb: 3 }}>
            <AlertTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <SecurityRounded />
              Insufficient Permissions
            </AlertTitle>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Your current role ({userRole}) does not have the required permissions for this action.
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Missing permissions: {missingPermissions.join(', ')}
            </Typography>
          </Alert>

          <Button
            variant="contained"
            startIcon={<ArrowBackRounded />}
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