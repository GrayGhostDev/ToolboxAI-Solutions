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

    // Material-UI theme integration
    appearance: {
      elements: {
        rootBox: {
          fontFamily: '"Roboto","Helvetica","Arial",sans-serif',
        },
        card: {
          borderRadius: '8px',
          boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.1)',
          border: '1px solid #e0e0e0',
        },
        headerTitle: {
          fontFamily: '"Roboto","Helvetica","Arial",sans-serif',
          fontSize: '1.5rem',
          fontWeight: 500,
        },
        headerSubtitle: {
          fontFamily: '"Roboto","Helvetica","Arial",sans-serif',
          fontSize: '0.875rem',
          color: '#666',
        },
        formButtonPrimary: {
          backgroundColor: '#1976d2',
          '&:hover': {
            backgroundColor: '#1565c0',
          },
        },
        formFieldInput: {
          borderRadius: '4px',
          border: '1px solid #c4c4c4',
          '&:focus': {
            borderColor: '#1976d2',
            outline: 'none',
            boxShadow: '0 0 0 2px rgba(25, 118, 210, 0.2)',
          },
        },
        footerActionLink: {
          color: '#1976d2',
          textDecoration: 'none',
          '&:hover': {
            textDecoration: 'underline',
          },
        },
      },
      variables: {
        colorPrimary: '#1976d2',
        colorDanger: '#d32f2f',
        colorSuccess: '#2e7d32',
        colorWarning: '#ed6c02',
        colorNeutral: '#666',
        colorText: '#212121',
        colorTextSecondary: '#666',
        colorBackground: '#ffffff',
        colorInputBackground: '#ffffff',
        colorInputText: '#212121',
        fontFamily: '"Roboto","Helvetica","Arial",sans-serif',
        fontSize: '14px',
        fontWeight: '400',
        borderRadius: '4px',
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