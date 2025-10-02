/**
 * Clerk Provider Wrapper Component (2025)
 * Enhanced Clerk integration with loading states and error handling
 */

import React, { Suspense } from 'react';
import { ClerkProvider } from '@clerk/clerk-react';
import { Box, Loader, Text, Alert } from '@mantine/core';
import ClerkErrorBoundary from './ClerkErrorBoundary';

interface ClerkProviderWrapperProps {
  children: React.ReactNode;
  publishableKey?: string;
}

// Loading component for Clerk initialization
const ClerkLoadingFallback = () => (
  <Box
    style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      gap: '1rem'
    }}
  >
    <Loader size="lg" />
    <Text size="sm" c="dimmed">
      Initializing authentication...
    </Text>
  </Box>
);

// Error fallback for Clerk provider
const ClerkErrorFallback = ({ error, retry }: { error: Error; retry: () => void }) => (
  <Box
    style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      padding: '1.5rem',
      maxWidth: '600px',
      margin: '0 auto'
    }}
  >
    <Alert color="red" title="Authentication Service Unavailable" style={{ width: '100%', marginBottom: '1rem' }}>
      <Text size="sm" mb="md">
        {error.message.includes('publishable key')
          ? 'The authentication service is not properly configured.'
          : 'Unable to connect to the authentication service.'}
      </Text>
      <Text size="sm" c="dimmed">
        Please check your connection and try again.
      </Text>
    </Alert>
  </Box>
);

// Check if Clerk is properly configured
const validateClerkConfig = (publishableKey?: string): string => {
  // Try to get from environment variables
  const envKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;
  const key = publishableKey || envKey;

  if (!key) {
    throw new Error(
      'Clerk publishable key not found. Please set VITE_CLERK_PUBLISHABLE_KEY in your environment variables.'
    );
  }

  if (!key.startsWith('pk_')) {
    throw new Error(
      'Invalid Clerk publishable key format. Key should start with "pk_".'
    );
  }

  return key;
};

export const ClerkProviderWrapper = ({
  children,
  publishableKey
}: ClerkProviderWrapperProps) => {
  // Validate configuration
  let validatedKey: string;
  try {
    validatedKey = validateClerkConfig(publishableKey);
  } catch (error) {
    return (
      <ClerkErrorFallback
        error={error as Error}
        retry={() => window.location.reload()}
      />
    );
  }

  // Clerk provider configuration
  const clerkConfig = {
    // Production URLs from environment
    signInUrl: import.meta.env.VITE_CLERK_SIGN_IN_URL || '/sign-in',
    signUpUrl: import.meta.env.VITE_CLERK_SIGN_UP_URL || '/sign-up',
    afterSignInUrl: import.meta.env.VITE_CLERK_AFTER_SIGN_IN_URL || '/',
    afterSignUpUrl: import.meta.env.VITE_CLERK_AFTER_SIGN_UP_URL || '/',

    // Enhanced localization support
    localization: {
      locale: 'en-US' // Can be made dynamic based on user preference
    },

    // Appearance customization for Material-UI theme integration
    appearance: {
      elements: {
        rootBox: {
          fontFamily: '"Roboto","Helvetica","Arial",sans-serif'
        },
        card: {
          borderRadius: '8px',
          boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.1)'
        }
      },
      variables: {
        colorPrimary: '#1976d2', // Material-UI primary blue
        fontFamily: '"Roboto","Helvetica","Arial",sans-serif'
      }
    },

    // Enhanced telemetry for better error tracking
    telemetry: {
      disabled: process.env.NODE_ENV === 'development'
    }
  };

  return (
    <ClerkErrorBoundary fallback={ClerkErrorFallback}>
      <Suspense fallback={<ClerkLoadingFallback />}>
        <ClerkProvider
          publishableKey={validatedKey}
          {...clerkConfig}
        >
          {children}
        </ClerkProvider>
      </Suspense>
    </ClerkErrorBoundary>
  );
};

export default ClerkProviderWrapper;