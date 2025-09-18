import React from 'react';
import { CssBaseline, GlobalStyles } from '@mui/material';
import { RobloxThemeProvider } from '../contexts/ThemeContext';
import { designTokens } from '../theme/designTokens';

interface ThemeWrapperProps {
  children: React.ReactNode;
}

// Global styles for the Roblox theme
const globalStyles = {
  '*': {
    boxSizing: 'border-box'
  },
  '*, *::before, *::after': {
    boxSizing: 'inherit'
  },
  html: {
    fontSize: '16px',
    lineHeight: 1.5
  },
  body: {
    margin: 0,
    padding: 0,
    fontFamily: designTokens.typography.fontFamily.sans.join(', '),
    fontSize: designTokens.typography.fontSize.base[0],
    lineHeight: designTokens.typography.fontSize.base[1].lineHeight,
    WebkitFontSmoothing: 'antialiased',
    MozOsxFontSmoothing: 'grayscale',
    textSizeAdjust: '100%'
  },
  '#root': {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column'
  },
  // Custom scrollbar for Roblox theme
  '::-webkit-scrollbar': {
    width: '8px',
    height: '8px'
  },
  '::-webkit-scrollbar-track': {
    backgroundColor: 'rgba(0, 0, 0, 0.1)',
    borderRadius: designTokens.borderRadius.full
  },
  '::-webkit-scrollbar-thumb': {
    backgroundColor: 'rgba(226, 35, 26, 0.6)',
    borderRadius: designTokens.borderRadius.full,
    '&:hover': {
      backgroundColor: 'rgba(226, 35, 26, 0.8)'
    }
  },
  // Focus styles
  '*:focus-visible': {
    outline: `2px solid var(--roblox-primary-color, #E2231A)`,
    outlineOffset: '2px'
  },
  // Selection styles
  '::selection': {
    backgroundColor: 'rgba(226, 35, 26, 0.2)',
    color: 'inherit'
  },
  // Disable text selection on UI elements
  'button, [role="button"], .MuiButton-root, .MuiIconButton-root, .MuiTab-root': {
    userSelect: 'none'
  },
  // Smooth scrolling
  '@media (prefers-reduced-motion: no-preference)': {
    html: {
      scrollBehavior: 'smooth'
    }
  },
  // Ensure proper rendering on different devices
  '@media print': {
    '*': {
      background: 'transparent !important',
      color: 'black !important',
      boxShadow: 'none !important',
      textShadow: 'none !important'
    }
  }
};

export const ThemeWrapper: React.FC<ThemeWrapperProps> = ({ children }) => {
  return (
    <RobloxThemeProvider>
      <CssBaseline />
      <GlobalStyles styles={globalStyles} />
      {children}
    </RobloxThemeProvider>
  );
};

export default ThemeWrapper;