/**
 * Clerk Protected Route Component (2025)
 * Provides route protection using Clerk authentication
 * Migrated to Mantine v8
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth as useClerkAuth, RedirectToSignIn } from '@clerk/clerk-react';
import { Loader, Center } from '@mantine/core';
import type { UserRole } from '../../types/roles';
import { useAuth } from '../../contexts/ClerkAuthContext';

interface ClerkProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
  requireAuth?: boolean;
  redirectTo?: string;
}

export const ClerkProtectedRoute = ({
  children,
  allowedRoles,
  requireAuth = true,
  redirectTo = '/sign-in'
}: ClerkProtectedRouteProps) => {
  const { isLoaded, isSignedIn } = useClerkAuth();
  const { user, userConfig } = useAuth();
  const location = useLocation();

  // Show loading while Clerk is initializing
  if (!isLoaded) {
    return (
      <Center style={{ minHeight: '100vh' }}>
        <Loader size="lg" />
      </Center>
    );
  }

  // If authentication is required and user is not signed in
  if (requireAuth && !isSignedIn) {
    // Use Clerk's RedirectToSignIn component which handles return URLs
    return <RedirectToSignIn />;
  }

  // Check role-based access
  if (allowedRoles && user) {
    const userRole = user.role as UserRole;
    if (!allowedRoles.includes(userRole)) {
      // Redirect to unauthorized page or dashboard
      return <Navigate to="/unauthorized" state={{ from: location }} replace />;
    }
  }

  // User is authenticated and authorized
  return <>{children}</>;
};

// HOC for easier route protection
export const withClerkAuth = <P extends object>(
  Component: React.ComponentType<P>,
  options?: {
    allowedRoles?: UserRole[];
    requireAuth?: boolean;
  }
) => {
  return (props: P) => (
    <ClerkProtectedRoute {...options}>
      <Component {...props} />
    </ClerkProtectedRoute>
  );
};

// Role-specific route guards
export const AdminRoute = ({ children }: { children: React.ReactNode }) => (
  <ClerkProtectedRoute allowedRoles={['admin']}>
    {children}
  </ClerkProtectedRoute>
);

export const TeacherRoute = ({ children }: { children: React.ReactNode }) => (
  <ClerkProtectedRoute allowedRoles={['teacher', 'admin']}>
    {children}
  </ClerkProtectedRoute>
);

export const StudentRoute = ({ children }: { children: React.ReactNode }) => (
  <ClerkProtectedRoute allowedRoles={['student', 'teacher', 'admin']}>
    {children}
  </ClerkProtectedRoute>
);
