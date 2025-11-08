/**
 * Role-Based Router
 * Redirects users to the appropriate dashboard based on their role
 */

import * as React from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAppSelector } from '../../store';
import { getDefaultRouteForRole } from '../../utils/auth-utils';
import { logger } from '../../utils/logger';

interface RoleBasedRouterProps {
  children: React.ReactNode;
}

/**
 * RoleBasedRouter
 *
 * Ensures users are routed to the correct dashboard based on their role.
 * Role is managed by Redux (either from Clerk or legacy auth).
 */
export function RoleBasedRouter({ children }: RoleBasedRouterProps) {
  const location = useLocation();
  const reduxRole = useAppSelector((s) => s.user.role);
  const isAuthenticated = useAppSelector((s) => s.user.isAuthenticated);

  // If not authenticated, let the app handle it (will show login)
  if (!isAuthenticated) {
    return <>{children}</>;
  }

  // If user has a role and is on root path, redirect to their dashboard
  if (reduxRole && location.pathname === '/') {
    const defaultRoute = getDefaultRouteForRole(reduxRole);
    logger.info(`Redirecting user with role ${reduxRole} to ${defaultRoute}`);
    return <Navigate to={defaultRoute} replace />;
  }

  // Otherwise, just render children
  return <>{children}</>;
}

/**
 * withRoleBasedRouting HOC
 * Wraps a component with role-based routing logic
 */
export function withRoleBasedRouting<P extends object>(
  Component: React.ComponentType<P>
): React.ComponentType<P> {
  return function RoleBasedComponent(props: P) {
    return (
      <RoleBasedRouter>
        <Component {...props} />
      </RoleBasedRouter>
    );
  };
}

/**
 * useRoleBasedRedirect Hook
 * Programmatically redirect based on user role
 */
export function useRoleBasedRedirect() {
  const navigate = useNavigate();
  const reduxRole = useAppSelector((s) => s.user.role);

  return React.useCallback(() => {
    if (reduxRole) {
      const route = getDefaultRouteForRole(reduxRole);
      navigate(route, { replace: true });
    }
  }, [reduxRole, navigate]);
}

