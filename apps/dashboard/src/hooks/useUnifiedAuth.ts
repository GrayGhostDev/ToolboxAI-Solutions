import { useAuth as useClerkAuth } from "../contexts/ClerkAuthContext";
import { useAuth as useLegacyAuth } from "../contexts/AuthContext";

/**
 * Unified auth hook that conditionally uses either Clerk or Legacy auth
 * based on the VITE_ENABLE_CLERK_AUTH environment variable.
 *
 * This hook ensures that React's Rules of Hooks are followed by always
 * calling the same hooks in the same order, regardless of configuration.
 */
export function useUnifiedAuth() {
  const clerkResult = useClerkAuth();
  const legacyResult = useLegacyAuth();

  const isClerkEnabled = import.meta.env.VITE_ENABLE_CLERK_AUTH === 'true';

  if (isClerkEnabled && clerkResult) {
    return clerkResult;
  }

  return legacyResult;
}
