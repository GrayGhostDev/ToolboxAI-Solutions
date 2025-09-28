import { createTheme, MantineColorsTuple } from '@mantine/core';
import { robloxColors } from '../theme/robloxTheme';

// Roblox-themed color palettes for Mantine
const robloxRed: MantineColorsTuple = [
  '#fff5f5', // lightest
  '#ffe3e3',
  '#ffc9c9',
  '#ffa8a8',
  '#ff8787',
  '#ff6b6b',
  '#fa5252', // base red
  '#f03e3e',
  '#e03131',
  '#c92a2a', // darkest
];

const robloxBlue: MantineColorsTuple = [
  '#e7f5ff', // lightest
  '#d0ebff',
  '#a5d8ff',
  '#74c0fc',
  '#339af0',
  '#228be6',
  '#1c7ed6', // base blue
  '#1971c2',
  '#1864ab',
  '#0f5132', // darkest
];

const robloxCyan: MantineColorsTuple = [
  '#e3fafc', // lightest
  '#c5f6fa',
  '#99e9f2',
  '#66d9ef',
  '#3bc9db',
  '#22b8cf',
  '#15aabf', // base cyan - matches neon electricBlue
  '#1098ad',
  '#0c8599',
  '#0a6e7a', // darkest
];

const robloxPurple: MantineColorsTuple = [
  '#f3e8ff', // lightest
  '#e9d5ff',
  '#d8b4fe',
  '#c084fc',
  '#a855f7',
  '#9333ea',
  '#7c3aed', // base purple
  '#6d28d9',
  '#5b21b6',
  '#4c1d95', // darkest
];

const robloxGreen: MantineColorsTuple = [
  '#ebfbee', // lightest
  '#d3f9d8',
  '#b2f2bb',
  '#8ce99a',
  '#69db7c',
  '#51cf66',
  '#40c057', // base green
  '#37b24d',
  '#2f9e44',
  '#2b8a3e', // darkest
];

const robloxOrange: MantineColorsTuple = [
  '#fff4e6', // lightest
  '#ffe8cc',
  '#ffd8a8',
  '#ffc078',
  '#ffa94d',
  '#ff922b',
  '#fd7e14', // base orange
  '#f76707',
  '#e8590c',
  '#d9480f', // darkest
];

const robloxPink: MantineColorsTuple = [
  '#fff0f6', // lightest
  '#ffdeeb',
  '#fcc2d7',
  '#faa2c1',
  '#f783ac',
  '#f06595',
  '#e64980', // base pink
  '#d6336c',
  '#c2255c',
  '#a61e4d', // darkest
];

const robloxYellow: MantineColorsTuple = [
  '#fff9db', // lightest
  '#fff3bf',
  '#ffec99',
  '#ffe066',
  '#ffd43b',
  '#fcc419',
  '#fab005', // base yellow
  '#f59f00',
  '#f08c00',
  '#e67700', // darkest
];

// Create enhanced Mantine theme
export const robloxMantineTheme = createTheme({
  /** Primary color matching Roblox brand */
  primaryColor: 'roblox-cyan',

  /** Custom Roblox-inspired colors */
  colors: {
    'roblox-red': robloxRed,
    'roblox-blue': robloxBlue,
    'roblox-cyan': robloxCyan,
    'roblox-purple': robloxPurple,
    'roblox-green': robloxGreen,
    'roblox-orange': robloxOrange,
    'roblox-pink': robloxPink,
    'roblox-yellow': robloxYellow,
    // Add aliases for easier usage
    'toolboxai-blue': robloxBlue,
    'toolboxai-purple': robloxPurple,
  },

  /** Typography matching existing Roblox theme */
  fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  fontFamilyMonospace: 'Fira Code, ui-monospace, SFMono-Regular, "SF Mono", Consolas, monospace',

  headings: {
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    fontWeight: '700',
    sizes: {
      h1: { fontSize: '2.5rem', lineHeight: '1.2', fontWeight: '800' },
      h2: { fontSize: '2rem', lineHeight: '1.3', fontWeight: '700' },
      h3: { fontSize: '1.75rem', lineHeight: '1.4', fontWeight: '600' },
      h4: { fontSize: '1.5rem', lineHeight: '1.4', fontWeight: '600' },
      h5: { fontSize: '1.25rem', lineHeight: '1.5', fontWeight: '600' },
      h6: { fontSize: '1.125rem', lineHeight: '1.5', fontWeight: '600' },
    },
  },

  /** Spacing system */
  spacing: {
    xs: '0.5rem',
    sm: '0.75rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
  },

  /** Border radius matching Roblox design */
  radius: {
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '20px',
  },

  /** Shadows for depth */
  shadows: {
    xs: '0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24)',
    sm: '0 3px 6px rgba(0, 0, 0, 0.16), 0 3px 6px rgba(0, 0, 0, 0.23)',
    md: '0 10px 20px rgba(0, 0, 0, 0.19), 0 6px 6px rgba(0, 0, 0, 0.23)',
    lg: '0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22)',
    xl: '0 19px 38px rgba(0, 0, 0, 0.30), 0 15px 12px rgba(0, 0, 0, 0.22)',
  },

  /** Breakpoints for responsive design */
  breakpoints: {
    xs: '36em',
    sm: '48em',
    md: '62em',
    lg: '75em',
    xl: '88em',
  },

  /** Component-specific customizations */
  components: {
    Button: {
      defaultProps: {
        radius: 'md',
      },
      styles: {
        root: {
          fontWeight: 600,
          textTransform: 'none',
          transition: 'all 250ms ease',
          '&:hover': {
            transform: 'translateY(-1px)',
          },
        },
      },
    },

    Card: {
      defaultProps: {
        radius: 'lg',
        shadow: 'sm',
        withBorder: true,
      },
      styles: {
        root: {
          transition: 'all 250ms ease',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: '0 14px 28px rgba(0, 0, 0, 0.25), 0 10px 10px rgba(0, 0, 0, 0.22)',
          },
        },
      },
    },

    Paper: {
      defaultProps: {
        radius: 'lg',
        shadow: 'sm',
      },
    },

    TextInput: {
      defaultProps: {
        radius: 'md',
      },
      styles: {
        input: {
          border: '2px solid',
          '&:focus': {
            borderColor: 'var(--mantine-color-roblox-cyan-6)',
            boxShadow: '0 0 0 3px var(--mantine-color-roblox-cyan-1)',
          },
        },
      },
    },

    PasswordInput: {
      defaultProps: {
        radius: 'md',
      },
      styles: {
        input: {
          border: '2px solid',
          '&:focus': {
            borderColor: 'var(--mantine-color-roblox-cyan-6)',
            boxShadow: '0 0 0 3px var(--mantine-color-roblox-cyan-1)',
          },
        },
      },
    },

    Modal: {
      defaultProps: {
        radius: 'lg',
        shadow: 'xl',
        centered: true,
      },
    },

    Notification: {
      defaultProps: {
        radius: 'md',
      },
    },

    Badge: {
      defaultProps: {
        radius: 'md',
      },
      styles: {
        root: {
          fontWeight: 700,
          textTransform: 'none',
        },
      },
    },

    ActionIcon: {
      defaultProps: {
        radius: 'md',
      },
      styles: {
        root: {
          transition: 'all 150ms ease',
          '&:hover': {
            transform: 'scale(1.05)',
          },
        },
      },
    },

    Alert: {
      defaultProps: {
        radius: 'md',
      },
    },

    Tabs: {
      styles: {
        tab: {
          fontWeight: 600,
          '&[data-active]': {
            fontWeight: 700,
          },
        },
      },
    },

    Progress: {
      defaultProps: {
        radius: 'xl',
        size: 'md',
      },
    },

    RingProgress: {
      defaultProps: {
        size: 120,
        thickness: 8,
      },
    },

    Timeline: {
      styles: {
        item: {
          '&:not(:last-of-type)': {
            borderLeft: '2px solid var(--mantine-color-gray-3)',
          },
        },
        itemBullet: {
          borderWidth: '3px',
        },
      },
    },
  },

  /** Other configurations */
  respectReducedMotion: true,
  cursorType: 'pointer',
  focusRing: 'auto',

  defaultGradient: {
    from: 'roblox-cyan',
    to: 'roblox-purple',
    deg: 135,
  },

  /** Dark theme colors */
  white: '#ffffff',
  black: '#0a0a0a',

  other: {
    // Custom CSS variables for advanced theming
    robloxBrandRed: robloxColors.brand.red.primary,
    robloxNeonBlue: robloxColors.neon.electricBlue,
    robloxNeonPink: robloxColors.neon.hotPink,
    robloxNeonGreen: robloxColors.neon.toxicGreen,
    robloxDarkBg: robloxColors.darkTheme.background,
    robloxDarkSurface: robloxColors.darkTheme.surface,
    robloxDarkCard: robloxColors.darkTheme.card,
  },
});

export default robloxMantineTheme;