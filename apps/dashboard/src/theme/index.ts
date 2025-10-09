/**
 * Roblox Theme System - Main Export File (Updated for Mantine v8)
 *
 * This file provides a centralized export for all theme-related functionality
 * including themes, design tokens, styled components, and utilities.
 * Updated for Mantine v8 compatibility.
 */

// Core theme exports - Updated for Mantine v8
export {
  mantineTheme,
  theme,
  robloxColors,
  themeUtils,
  getThemedStyles,
  globalStyles,
  globalStylesCSS,
} from './mantine-theme';

// Import global styles CSS
import './global-styles.css';

// Backward compatibility aliases
export { mantineTheme as robloxTheme } from './mantine-theme';
export { theme as defaultTheme } from './mantine-theme';

// Mantine v8 compatible utilities
export const createMantineTheme = () => mantineTheme;

// Color scheme utilities for v8
export const getColorSchemeValue = (lightValue: string, darkValue: string) => {
  return `light-dark(${lightValue}, ${darkValue})`;
};

// CSS variable helpers
export const getCSSVariable = (variableName: string) => {
  return `var(--mantine-${variableName})`;
};

// Common theme patterns for v8
export const themePatterns = {
  // Background patterns
  glassMorphism: 'backdrop-filter: blur(10px); background: light-dark(rgba(255, 255, 255, 0.1), rgba(0, 0, 0, 0.1));',
  // Border patterns
  glassBorder: 'border: 1px solid light-dark(rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));',
  // Input backgrounds
  inputBackground: 'background-color: light-dark(rgba(0, 0, 0, 0.02), rgba(255, 255, 255, 0.05));',
  // Card backgrounds
  cardBackground: 'background: light-dark(rgba(255, 255, 255, 0.9), rgba(26, 26, 26, 0.8));',
  // Modal backgrounds
  modalBackground: 'background: light-dark(rgba(255, 255, 255, 0.98), rgba(26, 26, 26, 0.95));',
} as const;

// Theme mode type
export type ThemeMode = 'light' | 'dark' | 'auto';

// Export theme types for TypeScript
export type RobloxTheme = typeof mantineTheme;
export type RobloxColors = typeof robloxColors;

// Default export for convenience
export { mantineTheme as default } from './mantine-theme';

/**
 * Mantine v8 Quick Start Guide:
 *
 * 1. Wrap your app with MantineProvider:
 *    import { MantineProvider } from '@mantine/core';
 *    import { theme } from './theme';
 *
 *    function App() {
 *      return (
 *        <MantineProvider theme={theme} defaultColorScheme="light">
 *          <YourApp />
 *        </MantineProvider>
 *      );
 *    }
 *
 * 2. Use theme in components:
 *    import { useMantineTheme } from '@mantine/core';
 *
 *    function MyComponent() {
 *      const theme = useMantineTheme();
 *      const styles = getThemedStyles(theme);
 *      // Use theme properties
 *    }
 *
 * 3. Use Mantine components with custom theme:
 *    import { Button, Card, Text } from '@mantine/core';
 *
 *    function MyComponent() {
 *      return (
 *        <Card>
 *          <Text>Roblox-styled content</Text>
 *          <Button>Action Button</Button>
 *        </Card>
 *      );
 *    }
 *
 * 4. Apply global styles:
 *    Import the CSS file in your main app:
 *    import './theme/global-styles.css';
 *
 * 5. Use color scheme switching:
 *    import { useComputedColorScheme, useMantineColorScheme } from '@mantine/core';
 *
 *    function ThemeToggle() {
 *      const { setColorScheme } = useMantineColorScheme();
 *      const computedColorScheme = useComputedColorScheme('light');
 *
 *      return (
 *        <Button onClick={() => setColorScheme(computedColorScheme === 'dark' ? 'light' : 'dark')}>
 *          Toggle Theme
 *        </Button>
 *      );
 *    }
 */
