/**
 * Comprehensive Clerk Authentication Mock for Testing
 *
 * This mock replaces @clerk/clerk-react in tests to avoid external dependencies
 * and provide deterministic authentication scenarios.
 */

import React, { createContext, useContext, ReactNode } from 'react';

// Mock types matching Clerk's API
interface MockUser {
  id: string;
  username?: string;
  firstName?: string;
  lastName?: string;
  imageUrl?: string;
  primaryEmailAddress?: {
    emailAddress: string;
    verification?: {
      status: 'verified' | 'unverified';
    };
  };
  publicMetadata?: Record<string, any>;
  unsafeMetadata?: Record<string, any>;
  createdAt?: number;
  update: (data: Partial<MockUser>) => Promise<void>;
}

interface MockSession {
  id: string;
  status: 'active' | 'expired' | 'loading';
  user: MockUser;
}

interface MockAuthState {
  isLoaded: boolean;
  userId?: string;
  sessionId?: string;
  user?: MockUser;
  session?: MockSession;
  isSignedIn: boolean;
  isLoading: boolean;
}

// Context for controlling mock auth state in tests
interface ClerkMockContextType {
  authState: MockAuthState;
  setAuthState: (state: Partial<MockAuthState>) => void;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const ClerkMockContext = createContext<ClerkMockContextType | undefined>(undefined);

// Provider for tests to control auth state
interface ClerkMockProviderProps {
  children: ReactNode;
  authState?: 'authenticated' | 'unauthenticated' | 'loading';
  userRole?: 'admin' | 'teacher' | 'student';
  customUser?: Partial<MockUser>;
}

export const ClerkMockProvider = ({
  children,
  authState = 'authenticated',
  userRole = 'student',
  customUser = {}
}: ClerkMockProviderProps) => {
  const [currentAuthState, setCurrentAuthState] = React.useState<MockAuthState>(() => {
    const isAuthenticated = authState === 'authenticated';
    const isLoading = authState === 'loading';

    const mockUser: MockUser | undefined = isAuthenticated ? {
      id: `mock-user-${userRole}`,
      username: `test_${userRole}`,
      firstName: userRole.charAt(0).toUpperCase() + userRole.slice(1),
      lastName: 'User',
      imageUrl: `https://avatar.example.com/${userRole}.png`,
      primaryEmailAddress: {
        emailAddress: `${userRole}@test.com`,
        verification: { status: 'verified' }
      },
      publicMetadata: { role: userRole },
      unsafeMetadata: {},
      createdAt: Date.now() - 86400000, // Yesterday
      update: async (data: Partial<MockUser>) => {
        setCurrentAuthState(prev => ({
          ...prev,
          user: prev.user ? { ...prev.user, ...data } : undefined
        }));
      },
      ...customUser
    } : undefined;

    return {
      isLoaded: !isLoading,
      userId: mockUser?.id,
      sessionId: isAuthenticated ? 'mock-session-id' : undefined,
      user: mockUser,
      session: isAuthenticated ? {
        id: 'mock-session-id',
        status: 'active',
        user: mockUser!
      } : undefined,
      isSignedIn: isAuthenticated,
      isLoading
    };
  });

  const setAuthState = React.useCallback((newState: Partial<MockAuthState>) => {
    setCurrentAuthState(prev => ({ ...prev, ...newState }));
  }, []);

  const login = React.useCallback(async (email: string, password: string) => {
    // Simulate login delay
    await new Promise(resolve => setTimeout(resolve, 100));

    // Create user based on email domain
    const role = email.includes('admin') ? 'admin' :
                 email.includes('teacher') ? 'teacher' : 'student';

    const user: MockUser = {
      id: `mock-user-${Date.now()}`,
      username: email.split('@')[0],
      firstName: role.charAt(0).toUpperCase() + role.slice(1),
      lastName: 'User',
      imageUrl: `https://avatar.example.com/${role}.png`,
      primaryEmailAddress: {
        emailAddress: email,
        verification: { status: 'verified' }
      },
      publicMetadata: { role },
      unsafeMetadata: {},
      createdAt: Date.now(),
      update: async (data: Partial<MockUser>) => {
        setCurrentAuthState(prev => ({
          ...prev,
          user: prev.user ? { ...prev.user, ...data } : undefined
        }));
      }
    };

    setCurrentAuthState({
      isLoaded: true,
      userId: user.id,
      sessionId: 'mock-session-id',
      user,
      session: {
        id: 'mock-session-id',
        status: 'active',
        user
      },
      isSignedIn: true,
      isLoading: false
    });
  }, []);

  const logout = React.useCallback(async () => {
    await new Promise(resolve => setTimeout(resolve, 50));
    setCurrentAuthState({
      isLoaded: true,
      userId: undefined,
      sessionId: undefined,
      user: undefined,
      session: undefined,
      isSignedIn: false,
      isLoading: false
    });
  }, []);

  const contextValue: ClerkMockContextType = {
    authState: currentAuthState,
    setAuthState,
    login,
    logout
  };

  return (
    <ClerkMockContext.Provider value={contextValue}>
      {children}
    </ClerkMockContext.Provider>
  );
};

// Mock hooks that replace Clerk's hooks
export const useAuth = () => {
  const context = useContext(ClerkMockContext);
  if (!context) {
    throw new Error('useAuth must be used within ClerkMockProvider');
  }

  const { authState, logout } = context;

  return {
    isLoaded: authState.isLoaded,
    isSignedIn: authState.isSignedIn,
    userId: authState.userId,
    sessionId: authState.sessionId,
    getToken: async () => 'mock-jwt-token',
    signOut: logout
  };
};

export const useUser = () => {
  const context = useContext(ClerkMockContext);
  if (!context) {
    throw new Error('useUser must be used within ClerkMockProvider');
  }

  const { authState } = context;

  return {
    isLoaded: authState.isLoaded,
    isSignedIn: authState.isSignedIn,
    user: authState.user
  };
};

export const useSession = () => {
  const context = useContext(ClerkMockContext);
  if (!context) {
    throw new Error('useSession must be used within ClerkMockProvider');
  }

  const { authState } = context;

  return {
    isLoaded: authState.isLoaded,
    isSignedIn: authState.isSignedIn,
    session: authState.session
  };
};

// Mock components that replace Clerk's components
export const SignIn = ({ afterSignInUrl }: { routing?: string; path?: string; afterSignInUrl?: string }) => {
  const context = useContext(ClerkMockContext);
  if (!context) return null;

  const { login } = context;
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [loading, setLoading] = React.useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      if (afterSignInUrl) {
        window.location.href = afterSignInUrl;
      }
    } catch (error) {
      console.error('Mock login error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="clerk-sign-in">
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          data-testid="email-input"
          disabled={loading}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          data-testid="password-input"
          disabled={loading}
        />
        <button type="submit" disabled={loading} data-testid="sign-in-button">
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
      </form>
    </div>
  );
};

export const SignUp = ({ afterSignUpUrl }: { routing?: string; path?: string; afterSignUpUrl?: string }) => {
  return (
    <div data-testid="clerk-sign-up">
      <form>
        <input type="email" placeholder="Email" data-testid="email-input" />
        <input type="password" placeholder="Password" data-testid="password-input" />
        <button type="submit" data-testid="sign-up-button">Sign Up</button>
      </form>
    </div>
  );
};

export const UserButton = ({ afterSignOutUrl }: { afterSignOutUrl?: string }) => {
  const { authState, logout } = useContext(ClerkMockContext) || {};
  if (!authState?.isSignedIn) return null;

  const handleSignOut = async () => {
    await logout?.();
    if (afterSignOutUrl) {
      window.location.href = afterSignOutUrl;
    }
  };

  return (
    <div data-testid="clerk-user-button">
      <button onClick={handleSignOut} data-testid="user-button-signout">
        Sign Out
      </button>
    </div>
  );
};

export const SignOutButton = ({ children }: { children: ReactNode }) => {
  const { logout } = useContext(ClerkMockContext) || {};

  return (
    <button onClick={logout} data-testid="sign-out-button">
      {children || 'Sign Out'}
    </button>
  );
};

// Hook for tests to control auth state
export const useClerkMockControls = () => {
  const context = useContext(ClerkMockContext);
  if (!context) {
    throw new Error('useClerkMockControls must be used within ClerkMockProvider');
  }
  return context;
};

// Utility functions for tests
export const createMockUser = (
  role: 'admin' | 'teacher' | 'student' = 'student',
  overrides: Partial<MockUser> = {}
): MockUser => ({
  id: `mock-user-${role}`,
  username: `test_${role}`,
  firstName: role.charAt(0).toUpperCase() + role.slice(1),
  lastName: 'User',
  imageUrl: `https://avatar.example.com/${role}.png`,
  primaryEmailAddress: {
    emailAddress: `${role}@test.com`,
    verification: { status: 'verified' }
  },
  publicMetadata: { role },
  unsafeMetadata: {},
  createdAt: Date.now(),
  update: async () => {},
  ...overrides
});

export default ClerkMockProvider;