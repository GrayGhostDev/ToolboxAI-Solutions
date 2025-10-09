import { useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import { ClerkAuthContext } from '../contexts/ClerkAuthContext';

/**
 * Unified auth hook that conditionally uses Clerk or Legacy auth.
 *
 * This approach ensures compliance with React's Rules of Hooks
 * by always calling the same hooks in the same order.
 * The contexts themselves handle whether they are available or not.
 */
export function useUnifiedAuth() {
  const isClerkEnabled = import.meta.env.VITE_ENABLE_CLERK_AUTH === 'true';

  // Always call both hooks in the same order to comply with React rules
  // Use useContext directly to avoid throwing errors if context is not available
  const legacyAuthContext = useContext(AuthContext);
  const clerkAuthContext = useContext(ClerkAuthContext);

  // Return the appropriate auth result based on configuration
  if (isClerkEnabled && clerkAuthContext) {
    return clerkAuthContext;
  }

  // Fall back to legacy auth if Clerk is disabled or not available
  if (legacyAuthContext) {
    return legacyAuthContext;
  }

  // Return a default auth state if neither is available
  // This prevents crashes while the providers are being set up
  return {
    user: null,
    signIn: async () => { console.warn('No auth provider available'); },
    signOut: async () => { console.warn('No auth provider available'); },
    signUp: async () => { console.warn('No auth provider available'); },
    resetPassword: async () => { console.warn('No auth provider available'); },
    updateProfile: async () => { console.warn('No auth provider available'); },
    isLoaded: false,
    isSignedIn: false,
    session: null,
  };
}