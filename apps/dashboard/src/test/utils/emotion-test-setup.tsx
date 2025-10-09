/**
 * Mantine Test Setup - 2025 Best Practices
 *
 * Proper Mantine configuration for testing
 * Based on 2025 testing recommendations
 */

import React from 'react';
import { MantineProvider, createTheme } from '@mantine/core';
import { Notifications } from '@mantine/notifications';

// Create a default test theme for Mantine
export const createTestTheme = () => {
  return createTheme({
    // Disable animations for testing
    respectReducedMotion: false,
    // Basic theme configuration for tests
    primaryColor: 'blue',
    fontFamily: 'Arial, sans-serif',
  });
};

interface MantineTestProviderProps {
  children: React.ReactNode;
  theme?: ReturnType<typeof createTheme>;
}

/**
 * MantineTestProvider - Wraps components with proper Mantine configuration
 *
 * Usage in tests:
 * ```tsx
 * render(
 *   <MantineTestProvider>
 *     <YourComponent />
 *   </MantineTestProvider>
 * );
 * ```
 */
export const MantineTestProvider: React.FunctionComponent<MantineTestProviderProps> = ({
  children,
  theme = createTestTheme(),
}) => {
  return (
    <MantineProvider theme={theme}>
      <Notifications />
      {children}
    </MantineProvider>
  );
};

// Export convenience function for custom render
export const wrapWithMantineProviders = (ui: React.ReactElement) => {
  return <MantineTestProvider>{ui}</MantineTestProvider>;
};

// Legacy export for backwards compatibility
export const EmotionTestProvider = MantineTestProvider;
export const wrapWithEmotionProviders = wrapWithMantineProviders;
export const createTestEmotionCache = () => null; // No-op for compatibility