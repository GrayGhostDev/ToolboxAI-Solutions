/**
 * Clerk Authentication Components (2025)
 * Mantine styled Clerk components with enhanced error handling
 */

import React from 'react';
import {
  SignIn as ClerkSignIn,
  SignUp as ClerkSignUp,
  UserButton as ClerkUserButton,
  SignOutButton as ClerkSignOutButton,
  useAuth,
  useUser
} from '@clerk/clerk-react';
import {
  Box,
  Paper,
  Text,
  Title,
  Button,
  Avatar,
  Menu,
  Divider,
  Alert,
  Loader
} from '@mantine/core';
import {
  IconLogout,
  IconSettings,
  IconUser,
  IconShield
} from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import ClerkErrorBoundary from './ClerkErrorBoundary';

// Enhanced Sign In Component
export const SignIn = ({ redirectUrl }: { redirectUrl?: string }) => {
  return (
    <ClerkErrorBoundary>
      <Box
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
          padding: '1rem'
        }}
      >
        <Paper
          shadow="md"
          p="xl"
          style={{
            borderRadius: '8px',
            maxWidth: 400,
            width: '100%'
          }}
        >
          <Title
            order={1}
            ta="center"
            mb="xl"
          >
            Welcome Back
          </Title>
          <ClerkSignIn
            path="/sign-in"
            routing="path"
            signUpUrl="/sign-up"
            redirectUrl={redirectUrl || '/dashboard'}
            afterSignInUrl={redirectUrl || '/dashboard'}
          />
        </Paper>
      </Box>
    </ClerkErrorBoundary>
  );
};

// Enhanced Sign Up Component
export const SignUp = ({ redirectUrl }: { redirectUrl?: string }) => {
  return (
    <ClerkErrorBoundary>
      <Box
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
          padding: '1rem'
        }}
      >
        <Paper
          shadow="md"
          p="xl"
          style={{
            borderRadius: '8px',
            maxWidth: 400,
            width: '100%'
          }}
        >
          <Title
            order={1}
            ta="center"
            mb="xl"
          >
            Get Started
          </Title>
          <ClerkSignUp
            path="/sign-up"
            routing="path"
            signInUrl="/sign-in"
            redirectUrl={redirectUrl || '/dashboard'}
            afterSignUpUrl={redirectUrl || '/dashboard'}
          />
        </Paper>
      </Box>
    </ClerkErrorBoundary>
  );
};

// Enhanced User Button with Mantine styling
export const UserButton = () => {
  const { user, isLoaded } = useUser();
  const { signOut } = useAuth();
  const navigate = useNavigate();

  const handleSignOut = async () => {
    try {
      await signOut();
      navigate('/');
    } catch (error) {
      console.error('Sign out error:', error);
    }
  };

  const handleProfile = () => {
    navigate('/profile');
  };

  const handleSettings = () => {
    navigate('/settings');
  };

  if (!isLoaded) {
    return (
      <Avatar size="sm">
        <IconUser size={16} />
      </Avatar>
    );
  }

  if (!user) {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={() => navigate('/sign-in')}
      >
        Sign In
      </Button>
    );
  }

  return (
    <ClerkErrorBoundary>
      <Menu shadow="md" width={200} position="bottom-end">
        <Menu.Target>
          <Avatar
            src={user.imageUrl}
            alt={user.fullName || user.username || 'User'}
            size="sm"
            style={{
              cursor: 'pointer',
              border: '2px solid var(--mantine-color-blue-6)'
            }}
          >
            {(user.fullName || user.username || 'U').charAt(0).toUpperCase()}
          </Avatar>
        </Menu.Target>

        <Menu.Dropdown>
          <Box p="xs">
            <Text size="sm" fw={500} truncate>
              {user.fullName || user.username}
            </Text>
            <Text size="xs" c="dimmed" truncate>
              {user.primaryEmailAddress?.emailAddress}
            </Text>
          </Box>

          <Divider />

          <Menu.Item
            leftSection={<IconUser size={14} />}
            onClick={handleProfile}
          >
            Profile
          </Menu.Item>

          <Menu.Item
            leftSection={<IconSettings size={14} />}
            onClick={handleSettings}
          >
            Settings
          </Menu.Item>

          <Divider />

          <Menu.Item
            leftSection={<IconLogout size={14} />}
            onClick={handleSignOut}
            color="red"
          >
            Sign Out
          </Menu.Item>
        </Menu.Dropdown>
      </Menu>
    </ClerkErrorBoundary>
  );
};

// Enhanced Sign Out Button
export const SignOutButton = ({ children, variant = 'outline' }: {
  children?: React.ReactNode;
  variant?: 'filled' | 'outline' | 'light' | 'subtle';
}) => {
  const { signOut } = useAuth();
  const navigate = useNavigate();

  const handleSignOut = async () => {
    try {
      await signOut();
      navigate('/');
    } catch (error) {
      console.error('Sign out error:', error);
    }
  };

  return (
    <ClerkErrorBoundary>
      <Button
        variant={variant}
        onClick={handleSignOut}
        leftSection={<IconLogout size={16} />}
      >
        {children || 'Sign Out'}
      </Button>
    </ClerkErrorBoundary>
  );
};

// Authentication Status Component
export const AuthStatus = () => {
  const { isLoaded, isSignedIn } = useAuth();
  const { user } = useUser();

  if (!isLoaded) {
    return (
      <Alert color="blue" title="Loading">
        Loading authentication...
      </Alert>
    );
  }

  if (!isSignedIn) {
    return (
      <Alert color="yellow" title="Not Signed In">
        You are not signed in.
      </Alert>
    );
  }

  return (
    <Alert color="green" title="Signed In">
      Signed in as {user?.fullName || user?.username || 'User'}
    </Alert>
  );
};

// Protected Route Component
export const ProtectedRoute = ({ children, fallback }: {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) => {
  const { isLoaded, isSignedIn } = useAuth();
  const navigate = useNavigate();

  React.useEffect(() => {
    if (isLoaded && !isSignedIn) {
      navigate('/sign-in');
    }
  }, [isLoaded, isSignedIn, navigate]);

  if (!isLoaded) {
    return (
      <Box
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh'
        }}
      >
        <Loader size="md" />
        <Text ml="md">Loading...</Text>
      </Box>
    );
  }

  if (!isSignedIn) {
    return fallback ? (
      <>{fallback}</>
    ) : (
      <Box
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh'
        }}
      >
        <Text>Redirecting to sign in...</Text>
      </Box>
    );
  }

  return <>{children}</>;
};

export default {
  SignIn,
  SignUp,
  UserButton,
  SignOutButton,
  AuthStatus,
  ProtectedRoute
};
