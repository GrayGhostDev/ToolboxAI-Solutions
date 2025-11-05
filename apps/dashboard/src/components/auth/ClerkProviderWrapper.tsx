/**
 * Clerk Provider Wrapper Component
 *
 * Conditionally wraps the application with Clerk's authentication provider
 * based on environment configuration.
 */

import React from 'react';
import { ClerkProvider } from '@clerk/clerk-react';
import { logger } from '../../utils/logger';

interface ClerkProviderWrapperProps {
  children: React.ReactNode;
}

const ClerkProviderWrapper: React.FC<ClerkProviderWrapperProps> = ({ children }) => {
  const clerkPubKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;
  const isClerkEnabled = import.meta.env.VITE_ENABLE_CLERK_AUTH === 'true';

  // If Clerk is not enabled, just return children without wrapping
  if (!isClerkEnabled) {
    logger.debug('Clerk authentication is disabled');
    return <>{children}</>;
  }

  // If Clerk is enabled but no key is provided, log error and return children
  if (!clerkPubKey) {
    logger.error('Clerk is enabled but VITE_CLERK_PUBLISHABLE_KEY is not set');
    return <>{children}</>;
  }

  // Valid Clerk configuration - wrap with provider
  logger.info('Initializing Clerk authentication');

  return (
    <ClerkProvider publishableKey={clerkPubKey}>
      {children}
    </ClerkProvider>
  );
};

export default ClerkProviderWrapper;

