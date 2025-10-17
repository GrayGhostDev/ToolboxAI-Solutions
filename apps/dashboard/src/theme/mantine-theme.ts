/**
 * Mantine Theme Configuration for Roblox Dashboard
 *
 * This file replaces the MUI theme system with Mantine's theming.
 * It provides the same Roblox-inspired design system but using Mantine components.
 * Updated for Mantine v8 compatibility.
 */

import { createTheme, type MantineColorsTuple } from '@mantine/core';

// Roblox Brand Colors - Updated for Mantine v8 MantineColorsTuple
export const robloxColors = {
  // Primary colors
  red: [
    '#ffe5e5', '#ffcccc', '#ff9999', '#ff6666', '#ff3333',
    '#e60000', '#cc0000', '#b30000', '#990000', '#800000'
  ] as MantineColorsTuple,
  gray: [
    '#f8f9fa', '#f1f3f5', '#e9ecef', '#dee2e6', '#ced4da',
    '#adb5bd', '#6c757d', '#495057', '#343a40', '#212529'
  ] as MantineColorsTuple,
  // Roblox colors
  brand: [
    '#ffebeb', '#ffd6d6', '#ffb3b3', '#ff8080', '#ff4d4d',
    '#ff1a1a', '#e60000', '#cc0000', '#990000', '#660000'
  ] as MantineColorsTuple,
  // Game-like colors
  neon: [
    '#e6ffff', '#ccffff', '#99ffff', '#66ffff', '#33ffff',
    '#00ffff', '#00e6e6', '#00cccc', '#00b3b3', '#009999'
  ] as MantineColorsTuple,
  purple: [
    '#f3e5ff', '#e6ccff', '#d9b3ff', '#cc99ff', '#bf80ff',
    '#b366ff', '#a64dff', '#9933ff', '#8c1aff', '#7f00ff'
  ] as MantineColorsTuple,
  orange: [
    '#fff4e6', '#ffe8cc', '#ffd8a8', '#ffc284', '#ffaa60',
    '#ff9940', '#ff8800', '#e67700', '#cc6600', '#b35500'
  ] as MantineColorsTuple,
  green: [
    '#e6ffe6', '#ccffcc', '#99ff99', '#66ff66', '#33ff33',
    '#00ff00', '#00e600', '#00cc00', '#00b300', '#009900'
  ] as MantineColorsTuple,
};

// Mantine Theme Configuration - Updated for v8
export const mantineTheme = createTheme({
  // Primary color
  primaryColor: 'brand',
  colors: robloxColors,

  // Note: defaultColorScheme is set via MantineProvider, not in theme

  // Typography
  fontFamily: 'Rubik, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  fontFamilyMonospace: 'Monaco, Courier, monospace',
  headings: {
    fontFamily: 'Rubik, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    fontWeight: '700',
    sizes: {
      h1: { fontSize: '2.5rem', lineHeight: '1.2' },
      h2: { fontSize: '2rem', lineHeight: '1.3' },
      h3: { fontSize: '1.75rem', lineHeight: '1.4' },
      h4: { fontSize: '1.5rem', lineHeight: '1.4' },
      h5: { fontSize: '1.25rem', lineHeight: '1.5' },
      h6: { fontSize: '1rem', lineHeight: '1.5' },
    },
  },

  // Spacing
  spacing: {
    xs: '0.5rem',
    sm: '0.75rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
  },

  // Radius
  radius: {
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '24px',
  },

  // Shadows
  shadows: {
    xs: '0 1px 3px rgba(0, 0, 0, 0.05)',
    sm: '0 2px 8px rgba(0, 0, 0, 0.08)',
    md: '0 4px 16px rgba(0, 0, 0, 0.12)',
    lg: '0 8px 24px rgba(0, 0, 0, 0.16)',
    xl: '0 16px 48px rgba(0, 0, 0, 0.24)',
  },

  // Component defaults - Updated for Mantine v8
  components: {
    Button: {
      defaultProps: {
        radius: 'md',
        size: 'md',
      },
      styles: (theme) => ({
        root: {
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          transition: 'all 0.2s ease',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: theme.shadows.md,
          },
        },
      }),
    },
    Card: {
      defaultProps: {
        radius: 'lg',
        shadow: 'sm',
        padding: 'lg',
      },
      styles: (theme) => ({
        root: {
          backdropFilter: 'blur(10px)',
          background: 'light-dark(rgba(255, 255, 255, 0.9), rgba(26, 26, 26, 0.8))',
          border: '1px solid light-dark(rgba(0, 0, 0, 0.05), rgba(255, 255, 255, 0.1))',
        },
      }),
    },
    Paper: {
      defaultProps: {
        radius: 'md',
        shadow: 'sm',
      },
      styles: () => ({
        root: {
          backdropFilter: 'blur(8px)',
        },
      }),
    },
    Badge: {
      defaultProps: {
        radius: 'xl',
      },
      styles: () => ({
        root: {
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
        },
      }),
    },
    ActionIcon: {
      defaultProps: {
        radius: 'md',
      },
      styles: () => ({
        root: {
          transition: 'all 0.2s ease',
          '&:hover': {
            transform: 'scale(1.1)',
          },
        },
      }),
    },
    TextInput: {
      defaultProps: {
        radius: 'md',
      },
      styles: (theme) => ({
        input: {
          backgroundColor: 'light-dark(rgba(0, 0, 0, 0.02), rgba(255, 255, 255, 0.05))',
          border: '1px solid light-dark(rgba(0, 0, 0, 0.1), rgba(255, 255, 255, 0.1))',
          '&:focus': {
            borderColor: theme.colors.brand[5],
            boxShadow: `0 0 0 2px ${theme.colors.brand[1]}`,
          },
        },
      }),
    },
    Select: {
      defaultProps: {
        radius: 'md',
      },
      styles: () => ({
        input: {
          backgroundColor: 'light-dark(rgba(0, 0, 0, 0.02), rgba(255, 255, 255, 0.05))',
          border: '1px solid light-dark(rgba(0, 0, 0, 0.1), rgba(255, 255, 255, 0.1))',
        },
      }),
    },
    Modal: {
      defaultProps: {
        radius: 'lg',
        centered: true,
      },
      styles: () => ({
        content: {
          backdropFilter: 'blur(10px)',
          background: 'light-dark(rgba(255, 255, 255, 0.98), rgba(26, 26, 26, 0.95))',
        },
        overlay: {
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
        },
      }),
    },
    Loader: {
      defaultProps: {
        color: 'brand',
        size: 'md',
      },
    },
    Progress: {
      defaultProps: {
        radius: 'xl',
        size: 'md',
      },
      styles: () => ({
        root: {
          backgroundColor: 'rgba(0, 0, 0, 0.1)',
        },
      }),
    },
    Alert: {
      defaultProps: {
        radius: 'md',
      },
      styles: () => ({
        root: {
          backdropFilter: 'blur(8px)',
        },
      }),
    },
    Notification: {
      defaultProps: {
        radius: 'md',
      },
      styles: () => ({
        root: {
          backdropFilter: 'blur(10px)',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.15)',
        },
      }),
    },
    NavLink: {
      defaultProps: {
        variant: 'light',
      },
      styles: () => ({
        root: {
          color: 'white',
          '&[data-active]': {
            color: 'white',
          },
          '&:hover': {
            color: 'white',
          },
        },
        label: {
          color: 'white !important',
          fontWeight: 400,
          '&[data-active]': {
            fontWeight: 600,
          },
        },
        icon: {
          color: 'white !important',
        },
      }),
    },
    Drawer: {
      styles: () => ({
        content: {
          color: 'white',
        },
        body: {
          color: 'white',
        },
      }),
    },
  },

  // Other theme properties
  other: {
    // Game-specific properties
    gameColors: {
      health: '#00ff00',
      mana: '#00ccff',
      experience: '#ffcc00',
      danger: '#ff0000',
      success: '#00ff88',
      warning: '#ff9900',
    },
    // Animation durations
    transitions: {
      fast: '0.15s',
      normal: '0.3s',
      slow: '0.5s',
    },
    // Z-index layers
    layers: {
      background: 0,
      content: 10,
      overlay: 100,
      modal: 1000,
      popover: 2000,
      tooltip: 3000,
      notification: 4000,
    },
    // Gamification elements
    gamification: {
      levelColors: {
        bronze: '#cd7f32',
        silver: '#c0c0c0',
        gold: '#ffd700',
        platinum: '#e5e4e2',
        diamond: '#b9f2ff',
      },
      rarityColors: {
        common: '#808080',
        uncommon: '#00ff00',
        rare: '#0099ff',
        epic: '#cc00ff',
        legendary: '#ff9900',
        mythic: '#ff0066',
      },
    },
  },
});

// Theme utilities
export const themeUtils = {
  getContrastText: (background: string): string => {
    // Simple contrast calculation
    const rgb = background.match(/\d+/g);
    if (!rgb) return '#000000';
    const brightness = (parseInt(rgb[0]) * 299 + parseInt(rgb[1]) * 587 + parseInt(rgb[2]) * 114) / 1000;
    return brightness > 128 ? '#000000' : '#ffffff';
  },

  hexToRgba: (hex: string, alpha: number = 1): string => {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  },

  darken: (color: string, amount: number): string => {
    // Simple darken function
    return color; // Implement if needed
  },

  lighten: (color: string, amount: number): string => {
    // Simple lighten function
    return color; // Implement if needed
  },
};

// Export themed components helpers - Updated for Mantine v8
export const getThemedStyles = (theme: any) => ({
  glowEffect: (color: string = theme.colors.brand[5]) => ({
    boxShadow: `0 0 20px ${themeUtils.hexToRgba(color, 0.5)}`,
    '&:hover': {
      boxShadow: `0 0 30px ${themeUtils.hexToRgba(color, 0.7)}`,
    },
  }),

  gameCard: {
    background: 'light-dark(linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(245, 245, 255, 0.9) 100%), linear-gradient(135deg, rgba(26, 26, 26, 0.9) 0%, rgba(10, 10, 10, 0.9) 100%))',
    backdropFilter: 'blur(10px)',
    border: `2px solid ${theme.colors.brand[5]}`,
    borderRadius: theme.radius.lg,
    padding: theme.spacing.lg,
    transition: 'all 0.3s ease',
    '&:hover': {
      transform: 'translateY(-4px)',
      boxShadow: `0 8px 24px ${themeUtils.hexToRgba(theme.colors.brand[5], 0.3)}`,
    },
  },

  neonText: (color: string = theme.colors.neon[5]) => ({
    color: color,
    textShadow: `0 0 10px ${color}, 0 0 20px ${color}, 0 0 30px ${color}`,
  }),

  pixelBorder: {
    border: `4px solid ${theme.colors.gray[7]}`,
    borderImageSlice: 1,
    borderImageSource: `linear-gradient(45deg, ${theme.colors.brand[5]} 0%, ${theme.colors.neon[5]} 50%, ${theme.colors.purple[5]} 100%)`,
  },
});

// Global styles for Mantine v8 - Use with CSS-in-JS or import in your App
export const globalStyles = {
  body: {
    backgroundColor: 'light-dark(#f0f2ff, #0f0f2e)',
    backgroundImage: 'light-dark(radial-gradient(circle at 20% 50%, rgba(120, 0, 255, 0.05) 0%, transparent 50%), radial-gradient(circle at 80% 80%, rgba(255, 0, 128, 0.05) 0%, transparent 50%), radial-gradient(circle at 20% 50%, rgba(120, 0, 255, 0.15) 0%, transparent 50%), radial-gradient(circle at 80% 80%, rgba(255, 0, 128, 0.15) 0%, transparent 50%))',
    minHeight: '100vh',
  },
  '::selection': {
    backgroundColor: 'var(--mantine-color-brand-3)',
    color: 'var(--mantine-color-white)',
  },
  '::-webkit-scrollbar': {
    width: '12px',
    height: '12px',
  },
  '::-webkit-scrollbar-track': {
    background: 'light-dark(rgba(0, 0, 0, 0.05), rgba(255, 255, 255, 0.05))',
    borderRadius: '6px',
  },
  '::-webkit-scrollbar-thumb': {
    background: 'light-dark(rgba(0, 0, 0, 0.2), rgba(255, 255, 255, 0.2))',
    borderRadius: '6px',
    '&:hover': {
      background: 'light-dark(rgba(0, 0, 0, 0.3), rgba(255, 255, 255, 0.3))',
    },
  },
} as const;

// CSS string version for easy injection
export const globalStylesCSS = `
  body {
    background-color: light-dark(#f0f2ff, #0f0f2e);
    background-image: light-dark(
      radial-gradient(circle at 20% 50%, rgba(120, 0, 255, 0.05) 0%, transparent 50%),
      radial-gradient(circle at 80% 80%, rgba(255, 0, 128, 0.05) 0%, transparent 50%),
      radial-gradient(circle at 20% 50%, rgba(120, 0, 255, 0.15) 0%, transparent 50%),
      radial-gradient(circle at 80% 80%, rgba(255, 0, 128, 0.15) 0%, transparent 50%)
    );
    min-height: 100vh;
  }

  ::selection {
    background-color: var(--mantine-color-brand-3);
    color: var(--mantine-color-white);
  }

  ::-webkit-scrollbar {
    width: 12px;
    height: 12px;
  }

  ::-webkit-scrollbar-track {
    background: light-dark(rgba(0, 0, 0, 0.05), rgba(255, 255, 255, 0.05));
    border-radius: 6px;
  }

  ::-webkit-scrollbar-thumb {
    background: light-dark(rgba(0, 0, 0, 0.2), rgba(255, 255, 255, 0.2));
    border-radius: 6px;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: light-dark(rgba(0, 0, 0, 0.3), rgba(255, 255, 255, 0.3));
  }
`;

// Named export for the theme
export const theme = mantineTheme;

// Export default theme
export default mantineTheme;