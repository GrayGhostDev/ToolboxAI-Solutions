import * as React from 'react';
import { useAppSelector } from '../../store';
import { type UserRole } from '../../types';
import { Text, Alert, Box, Button } from '@mantine/core';
import { useNavigate } from 'react-router-dom';

interface Props {
  allow: UserRole[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export default function RoleGuard({ allow, children, fallback }: Props) {
  const navigate = useNavigate();
  const role = useAppSelector((s) => s.user.role);
  const isAuthenticated = useAppSelector((s) => s.user.isAuthenticated);

  // Check if we're in bypass mode - allow all access
  const bypassAuth = import.meta.env.VITE_BYPASS_AUTH === 'true';

  // In bypass mode, always render the children
  if (bypassAuth) {
    return <>{children}</>;
  }

  if (!isAuthenticated) {
    return (
      <Box p={32} style={{ textAlign: 'center' }}>
        <Alert color="yellow" mb={16}>
          You must be logged in to access this page.
        </Alert>
        <Button onClick={() => navigate('/login')}>
          Sign In
        </Button>
      </Box>
    );
  }

  if (!allow.includes(role)) {
    if (fallback) {
      return <>{fallback}</>;
    }

    return (
      <Box p={32} style={{ textAlign: 'center' }}>
        <Alert color="red" mb={16}>
          <Text size="lg" fw={600} mb={8}>
            Access Denied
          </Text>
          <Text size="sm">
            You don't have permission to access this section. This page is only available for:{' '}
            {allow.join(', ')}.
          </Text>
        </Alert>
        <Button onClick={() => navigate('/')}>
          Go to Dashboard
        </Button>
      </Box>
    );
  }

  return <>{children}</>;
}