/**
 * Emotion Test Setup - 2025 Best Practices
 *
 * Proper Emotion cache configuration for MUI v5 testing
 * Based on 2025 testing recommendations
 */

import React from 'react';
import { CacheProvider } from '@emotion/react';
import createCache from '@emotion/cache';
import { ThemeProvider } from '@mui/material/styles';
import { createTheme } from '@mui/material/styles';

// Create a test-specific emotion cache with proper configuration
// This prevents style injection issues in jsdom/happy-dom
export const createTestEmotionCache = () => {
  return createCache({
    key: 'mui-test',
    prepend: true, // Ensures proper style injection order
    speedy: false, // Disable speedy mode for better compatibility
  });
};

// Create a default test theme
export const createTestTheme = () => {
  return createTheme({
    // Disable transitions for testing
    transitions: {
      create: () => 'none',
      duration: {
        shortest: 0,
        shorter: 0,
        short: 0,
        standard: 0,
        complex: 0,
        enteringScreen: 0,
        leavingScreen: 0,
      },
    },
    // Disable animations
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          '*, *::before, *::after': {
            transition: 'none !important',
            animation: 'none !important',
          },
        },
      },
      // Disable ripple effects
      MuiButtonBase: {
        defaultProps: {
          disableRipple: true,
        },
      },
    },
  });
};

interface EmotionTestProviderProps {
  children: React.ReactNode;
  cache?: ReturnType<typeof createCache>;
  theme?: ReturnType<typeof createTheme>;
}

/**
 * EmotionTestProvider - Wraps components with proper Emotion/MUI configuration
 *
 * Usage in tests:
 * ```tsx
 * render(
 *   <EmotionTestProvider>
 *     <YourComponent />
 *   </EmotionTestProvider>
 * );
 * ```
 */
export const EmotionTestProvider: React.FunctionComponent<EmotionTestProviderProps> = ({
  children,
  cache = createTestEmotionCache(),
  theme = createTestTheme(),
}) => {
  return (
    <CacheProvider value={cache}>
      <ThemeProvider theme={theme}>
        {children}
      </ThemeProvider>
    </CacheProvider>
  );
};

// Export convenience function for custom render
export const wrapWithEmotionProviders = (ui: React.ReactElement) => {
  return <EmotionTestProvider>{ui}</EmotionTestProvider>;
};