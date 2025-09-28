/**
 * Clerk Authentication Components (2025)
 * Material-UI styled Clerk components with enhanced error handling
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
  Typography,
  Button,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  ListItemIcon,
  ListItemText,
  Alert
} from '@mui/material';
import {
  LogoutRounded,
  SettingsRounded,
  PersonRounded,
  SecurityRounded
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import ClerkErrorBoundary from './ClerkErrorBoundary';

// Enhanced Sign In Component
export const SignIn= ({ redirectUrl }: { redirectUrl?: string }) => {
  return (
    <ClerkErrorBoundary>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
          p: 2
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            borderRadius: 2,
            maxWidth: 400,
            width: '100%'
          }}
        >
          <Typography
            variant="h4"
            component="h1"
            gutterBottom
            textAlign="center"
            sx={{ mb: 3 }}
          >
            Welcome Back
          </Typography>
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
export const SignUp= ({ redirectUrl }: { redirectUrl?: string }) => {
  return (
    <ClerkErrorBoundary>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
          p: 2
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            borderRadius: 2,
            maxWidth: 400,
            width: '100%'
          }}
        >
          <Typography
            variant="h4"
            component="h1"
            gutterBottom
            textAlign="center"
            sx={{ mb: 3 }}
          >
            Get Started
          </Typography>
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

// Enhanced User Button with Material-UI styling
export const UserButton= () => {
  const { user, isLoaded } = useUser();
  const { signOut } = useAuth();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleSignOut = async () => {
    try {
      await signOut();
      navigate('/');
    } catch (error) {
      console.error('Sign out error:', error);
    } finally {
      handleClose();
    }
  };

  const handleProfile = () => {
    navigate('/profile');
    handleClose();
  };

  const handleSettings = () => {
    navigate('/settings');
    handleClose();
  };

  if (!isLoaded) {
    return (
      <Avatar sx={{ width: 32, height: 32 }}>
        <PersonRounded />
      </Avatar>
    );
  }

  if (!user) {
    return (
      <Button
        variant="outlined"
        size="small"
        onClick={() => navigate('/sign-in')}
      >
        Sign In
      </Button>
    );
  }

  return (
    <ClerkErrorBoundary>
      <Box>
        <Avatar
          src={user.imageUrl}
          alt={user.fullName || user.username || 'User'}
          sx={{
            width: 32,
            height: 32,
            cursor: 'pointer',
            border: '2px solid',
            borderColor: 'primary.main'
          }}
          onClick={handleClick}
        >
          {(user.fullName || user.username || 'U').charAt(0).toUpperCase()}
        </Avatar>

        <Menu
          anchorEl={anchorEl}
          open={open}
          onClose={handleClose}
          onClick={handleClose}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          sx={{
            '& .MuiPaper-root': {
              minWidth: 200,
              mt: 1.5
            }
          }}
        >
          <Box sx={{ px: 2, py: 1 }}>
            <Typography variant="subtitle2" noWrap>
              {user.fullName || user.username}
            </Typography>
            <Typography variant="body2" color="text.secondary" noWrap>
              {user.primaryEmailAddress?.emailAddress}
            </Typography>
          </Box>

          <Divider />

          <MenuItem onClick={handleProfile}>
            <ListItemIcon>
              <PersonRounded fontSize="small" />
            </ListItemIcon>
            <ListItemText>Profile</ListItemText>
          </MenuItem>

          <MenuItem onClick={handleSettings}>
            <ListItemIcon>
              <SettingsRounded fontSize="small" />
            </ListItemIcon>
            <ListItemText>Settings</ListItemText>
          </MenuItem>

          <Divider />

          <MenuItem onClick={handleSignOut}>
            <ListItemIcon>
              <LogoutRounded fontSize="small" />
            </ListItemIcon>
            <ListItemText>Sign Out</ListItemText>
          </MenuItem>
        </Menu>
      </Box>
    </ClerkErrorBoundary>
  );
};

// Enhanced Sign Out Button
export const SignOutButton = ({ children, variant = 'outlined' }: {
  children?: React.ReactNode;
  variant?: 'contained' | 'outlined' | 'text';
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
        startIcon={<LogoutRounded />}
      >
        {children || 'Sign Out'}
      </Button>
    </ClerkErrorBoundary>
  );
};

// Authentication Status Component
export const AuthStatus= () => {
  const { isLoaded, isSignedIn } = useAuth();
  const { user } = useUser();

  if (!isLoaded) {
    return (
      <Alert severity="info">
        Loading authentication...
      </Alert>
    );
  }

  if (!isSignedIn) {
    return (
      <Alert severity="warning">
        You are not signed in.
      </Alert>
    );
  }

  return (
    <Alert severity="success">
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
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh'
        }}
      >
        <Typography>Loading...</Typography>
      </Box>
    );
  }

  if (!isSignedIn) {
    return fallback ? (
      <>{fallback}</>
    ) : (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh'
        }}
      >
        <Typography>Redirecting to sign in...</Typography>
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