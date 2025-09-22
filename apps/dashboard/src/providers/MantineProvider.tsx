import React from 'react';
import {
  MantineProvider as BaseMantineProvider,
  createTheme,
  MantineColorsTuple,
  DEFAULT_THEME
} from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';

// Custom color palette that matches ToolBoxAI branding
const toolboxaiBlue: MantineColorsTuple = [
  '#f0f4ff',
  '#e1ecff',
  '#bdd7ff',
  '#94c1ff',
  '#74b0ff',
  '#5ea4ff',
  '#529dff',
  '#4188e5',
  '#3579cd',
  '#2869b5'
];

const toolboxaiPurple: MantineColorsTuple = [
  '#f9f5ff',
  '#f3eaff',
  '#e9d5ff',
  '#d8b4fe',
  '#c084fc',
  '#a855f7',
  '#9333ea',
  '#7c3aed',
  '#6b21a8',
  '#581c87'
];

// Create custom theme
const theme = createTheme({
  /** Primary color scheme that matches the existing design */
  primaryColor: 'toolboxai-blue',

  /** Custom colors for ToolBoxAI */
  colors: {
    'toolboxai-blue': toolboxaiBlue,
    'toolboxai-purple': toolboxaiPurple,
  },

  /** Font configuration */
  fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  fontFamilyMonospace: 'Fira Code, ui-monospace, SFMono-Regular, "SF Mono", Consolas, monospace',
  headings: {
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    fontWeight: '600',
    sizes: {
      h1: { fontSize: '2.125rem', lineHeight: '1.3' },
      h2: { fontSize: '1.625rem', lineHeight: '1.35' },
      h3: { fontSize: '1.375rem', lineHeight: '1.4' },
      h4: { fontSize: '1.125rem', lineHeight: '1.45' },
      h5: { fontSize: '1rem', lineHeight: '1.5' },
      h6: { fontSize: '0.875rem', lineHeight: '1.5' },
    },
  },

  /** Border radius - matching modern design trends */
  radius: {
    xs: '0.25rem',
    sm: '0.375rem',
    md: '0.5rem',
    lg: '0.75rem',
    xl: '1rem',
  },

  /** Spacing system */
  spacing: {
    xs: '0.5rem',
    sm: '0.75rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
  },

  /** Shadows matching Material Design */
  shadows: {
    xs: '0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24)',
    sm: '0 3px 6px rgba(0, 0, 0, 0.16), 0 3px 6px rgba(0, 0, 0, 0.23)',
    md: '0 10px 20px rgba(0, 0, 0, 0.19), 0 6px 6px rgba(0, 0, 0, 0.23)',
    lg: '0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22)',
    xl: '0 19px 38px rgba(0, 0, 0, 0.30), 0 15px 12px rgba(0, 0, 0, 0.22)',
  },

  /** Component-specific styling */
  components: {
    Button: {
      defaultProps: {
        radius: 'md',
      },
      styles: {
        root: {
          fontWeight: 600,
          textTransform: 'none' as const,
        },
      },
    },
    Card: {
      defaultProps: {
        radius: 'lg',
        shadow: 'sm',
        withBorder: true,
      },
    },
    TextInput: {
      defaultProps: {
        radius: 'md',
      },
    },
    PasswordInput: {
      defaultProps: {
        radius: 'md',
      },
    },
    Paper: {
      defaultProps: {
        radius: 'lg',
        shadow: 'sm',
      },
    },
    Modal: {
      defaultProps: {
        radius: 'lg',
        shadow: 'lg',
      },
    },
    Notification: {
      defaultProps: {
        radius: 'md',
      },
    },
  },

  /** Breakpoints for responsive design */
  breakpoints: {
    xs: '36em',
    sm: '48em',
    md: '62em',
    lg: '75em',
    xl: '88em',
  },

  /** Other properties */
  respectReducedMotion: true,
  cursorType: 'pointer',
  focusRing: 'auto',
  defaultGradient: {
    from: 'toolboxai-blue',
    to: 'toolboxai-purple',
    deg: 135,
  },
});

interface MantineProviderProps {
  children: React.ReactNode;
}

export function MantineProvider({ children }: MantineProviderProps) {
  return (
    <BaseMantineProvider theme={theme} defaultColorScheme="light">
      <Notifications position="top-right" limit={5} />
      {children}
    </BaseMantineProvider>
  );
}

export { theme };