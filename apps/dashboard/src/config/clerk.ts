/**
 * Clerk Configuration (2025)
 * Centralized configuration for Clerk authentication
 */

export interface ClerkConfig {
  publishableKey: string;
  signInUrl: string;
  signUpUrl: string;
  afterSignInUrl: string;
  afterSignUpUrl: string;
  frontendApiUrl?: string;
  allowedOrigins: string[];
  appearance: {
    elements: Record<string, React.CSSProperties>;
    variables: Record<string, string>;
  };
  localization: {
    locale: string;
  };
  telemetry: {
    disabled: boolean;
  };
}

// Environment variable validation
const validateEnvVar = (name: string, value: string | undefined, required = true): string => {
  if (!value && required) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value || '';
};

// Get and validate Clerk configuration
export const getClerkConfig = (): ClerkConfig => {
  const publishableKey = validateEnvVar(
    'VITE_CLERK_PUBLISHABLE_KEY',
    import.meta.env.VITE_CLERK_PUBLISHABLE_KEY,
    true
  );

  // Validate publishable key format
  if (!publishableKey.startsWith('pk_')) {
    throw new Error('Invalid Clerk publishable key format. Key should start with "pk_".');
  }

  const allowedOriginsString = validateEnvVar(
    'VITE_CLERK_ALLOWED_ORIGINS',
    import.meta.env.VITE_CLERK_ALLOWED_ORIGINS,
    false
  );

  const allowedOrigins = allowedOriginsString
    ? allowedOriginsString.split(',').map(origin => origin.trim())
    : ['http://localhost:5179', 'http://127.0.0.1:5179'];

  return {
    publishableKey,
    signInUrl: validateEnvVar(
      'VITE_CLERK_SIGN_IN_URL',
      import.meta.env.VITE_CLERK_SIGN_IN_URL,
      false
    ) || '/sign-in',
    signUpUrl: validateEnvVar(
      'VITE_CLERK_SIGN_UP_URL',
      import.meta.env.VITE_CLERK_SIGN_UP_URL,
      false
    ) || '/sign-up',
    afterSignInUrl: validateEnvVar(
      'VITE_CLERK_AFTER_SIGN_IN_URL',
      import.meta.env.VITE_CLERK_AFTER_SIGN_IN_URL,
      false
    ) || '/dashboard',
    afterSignUpUrl: validateEnvVar(
      'VITE_CLERK_AFTER_SIGN_UP_URL',
      import.meta.env.VITE_CLERK_AFTER_SIGN_UP_URL,
      false
    ) || '/dashboard',
    frontendApiUrl: validateEnvVar(
      'VITE_CLERK_FRONTEND_API_URL',
      import.meta.env.VITE_CLERK_FRONTEND_API_URL,
      false
    ),
    allowedOrigins,

    // Mantine theme integration with Roblox branding
    appearance: {
      elements: {
        rootBox: {
          fontFamily: 'var(--mantine-font-family)',
        },
        card: {
          borderRadius: 'var(--mantine-radius-md)',
          boxShadow: 'var(--mantine-shadow-sm)',
          border: '1px solid var(--mantine-color-gray-3)',
        },
        headerTitle: {
          fontFamily: 'var(--mantine-font-family)',
          fontSize: 'var(--mantine-font-size-xl)',
          fontWeight: 600,
        },
        headerSubtitle: {
          fontFamily: 'var(--mantine-font-family)',
          fontSize: 'var(--mantine-font-size-sm)',
          color: 'var(--mantine-color-dimmed)',
        },
        formButtonPrimary: {
          backgroundColor: '#e60012', // Roblox red
          '&:hover': {
            backgroundColor: '#cc0010',
          },
        },
        formFieldInput: {
          borderRadius: 'var(--mantine-radius-sm)',
          border: '1px solid var(--mantine-color-gray-4)',
          '&:focus': {
            borderColor: '#e60012', // Roblox red
            outline: 'none',
            boxShadow: '0 0 0 2px rgba(230, 0, 18, 0.2)',
          },
        },
        footerActionLink: {
          color: '#e60012', // Roblox red
          textDecoration: 'none',
          '&:hover': {
            textDecoration: 'underline',
          },
        },
      },
      variables: {
        colorPrimary: '#e60012', // Roblox red
        colorDanger: '#e60012',
        colorSuccess: '#00a135', // Roblox green
        colorWarning: '#ffb900',
        colorNeutral: '#393b3d',
        colorText: '#393b3d',
        colorTextSecondary: '#6c757d',
        colorBackground: '#ffffff',
        colorInputBackground: '#f8f9fa',
        colorInputText: '#495057',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        fontSize: '16px',
        fontWeight: '400',
        borderRadius: '8px',
        spacingUnit: '8px',
      },
    },

    localization: {
      locale: 'en-US', // Can be made dynamic
    },

    telemetry: {
      disabled: import.meta.env.DEV || process.env.NODE_ENV === 'development',
    },
  };
};

// Feature flags for Clerk functionality
export const clerkFeatures = {
  enabled: import.meta.env.VITE_ENABLE_CLERK_AUTH !== 'false',
  multiSession: false, // Enable if multiple sessions are needed
  userProfile: true,
  organizationProfile: false, // Enable if organizations are used
  socialProviders: ['google', 'github'], // Configure based on needs
};

// CORS configuration for Clerk
export const corsConfig = {
  allowedOrigins: getClerkConfig().allowedOrigins,
  allowCredentials: true,
  allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: [
    'Content-Type',
    'Authorization',
    'X-Requested-With',
    'Accept',
    'Origin',
    'Access-Control-Request-Method',
    'Access-Control-Request-Headers',
  ],
};

export default getClerkConfig;