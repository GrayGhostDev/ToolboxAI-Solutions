/**
 * Roblox Theme System - Main Export File
 *
 * This file provides a centralized export for all theme-related functionality
 * including themes, design tokens, styled components, and utilities.
 */

// Core theme exports
export {
  robloxTheme,
  robloxLightTheme,
  robloxDarkTheme,
  getRobloxTheme,
  robloxColors,
  themeUtils,
  gamificationHelpers,
  a11yHelpers
} from './robloxTheme';

// Design tokens
export {
  designTokens,
  lightModeTokens,
  darkModeTokens
} from './designTokens';

// Theme context and providers
export {
  RobloxThemeProvider,
  useThemeContext
} from '../contexts/ThemeContext';

// Styled components
export {
  RobloxCard,
  RobloxButton,
  RobloxChip,
  XPProgressBar,
  RobloxFAB,
  RobloxAvatar,
  AchievementBadge,
  RobloxNotificationCard,
  RobloxSkeleton,
  GameContainer
} from '../components/RobloxStyledComponents';

// Animation utilities
export { injectAnimations } from './injectAnimations';

// Theme switcher component
export { default as ThemeSwitcher } from '../components/ThemeSwitcher';

// Main theme wrapper
export { ThemeWrapper } from '../components/ThemeWrapper';

// Default exports for backward compatibility
export { robloxDarkTheme as theme, robloxLightTheme as lightTheme, robloxDarkTheme as darkTheme } from './robloxTheme';

// Utility types
export type {
  DesignTokens,
  LightModeTokens,
  DarkModeTokens
} from './designTokens';

// Theme mode type
export type ThemeMode = 'light' | 'dark' | 'system';

// Re-export Material-UI theme types for convenience
export type { Theme, Palette, PaletteMode } from '@mui/material/styles';

/**
 * Quick start guide:
 *
 * 1. Wrap your app with ThemeWrapper:
 *    import { ThemeWrapper } from './theme';
 *
 *    function App() {
 *      return (
 *        ThemeWrapper(
 *          YourApp()
 *        )
 *      );
 *    }
 *
 * 2. Use theme context in components:
 *    import { useThemeContext } from './theme';
 *
 *    function MyComponent() {
 *      const { mode, toggleTheme, isDark } = useThemeContext();
 *      // Use theme properties
 *    }
 *
 * 3. Use styled components:
 *    import { RobloxCard, RobloxButton } from './theme';
 *
 *    function MyComponent() {
 *      return RobloxCard with RobloxButton;
 *    }
 *
 * 4. Add theme switcher:
 *    import { ThemeSwitcher } from './theme';
 *    Add ThemeSwitcher component to your header
 */
