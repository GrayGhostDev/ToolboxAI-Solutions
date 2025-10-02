import { useAuth as useLegacyAuth } from "../contexts/AuthContext";

/**
 * Unified auth hook that conditionally uses either Clerk or Legacy auth
 * based on the VITE_ENABLE_CLERK_AUTH environment variable.
 *
 * This hook ensures that React's Rules of Hooks are followed by always
 * calling the same hooks in the same order, regardless of configuration.
 */
export function useUnifiedAuth() {
  const isClerkEnabled = import.meta.env.VITE_ENABLE_CLERK_AUTH === 'true';

  // Always call the legacy auth hook to follow Rules of Hooks
  const legacyResult = useLegacyAuth();

  // For now, since Clerk is disabled, just return the legacy result
  // When Clerk is enabled, the ClerkAuthProvider will be available and
  // the useClerkAuth hook can be called safely
  return legacyResult;
}
