/**
 * Roblox-Inspired Futuristic Theme
 *
 * A vibrant, tech-focused theme designed for kids with:
 * - Neon colors inspired by Roblox Discord communities
 * - Futuristic UI elements
 * - Engaging animations and effects
 * - Character and 3D icon integration
 */

import { createTheme, alpha } from "@mui/material/styles";

// Roblox-inspired color palette based on Discord communities and gaming aesthetics
const robloxColors = {
  // Primary colors - Bright, energetic blues and purples
  primary: {
    main: "#00bcd4", // Neon cyan
    light: "#4dd0e1",
    dark: "#0097a7",
  },

  // Secondary colors - Vibrant purples and magentas
  secondary: {
    main: "#e91e63", // Neon pink
    light: "#f06292",
    dark: "#c2185b",
  },

  // Accent colors - Neon greens and cyans
  accent: {
    main: "#4caf50", // Neon green
    light: "#81c784",
    dark: "#388e3c",
  },

  // Neon colors for highlights and effects
  neon: {
    blue: "#00bcd4",
    purple: "#e91e63",
    green: "#4caf50",
    orange: "#ff9800",
    pink: "#f06292",
    cyan: "#00e5ff",
    yellow: "#ffeb3b",
    lime: "#cddc39",
  },

  // Dark theme colors for space/tech feel
  dark: {
    background: "#0a0a0a",
    surface: "#1a1a1a",
    card: "#2a2a2a",
    border: "#3a3a3a",
    text: "#ffffff",
    textSecondary: "#b0b0b0",
  },

  // Gamification colors
  gamification: {
    xp: "#e91e63", // Neon pink
    badge: "#4caf50", // Neon green
    level: "#ff9800", // Neon orange
    achievement: "#ffeb3b", // Neon yellow
    power: "#00bcd4", // Neon cyan
  },
};

export const robloxTheme = createTheme({
  palette: {
    mode: "dark",
    primary: robloxColors.primary,
    secondary: robloxColors.secondary,
    background: {
      default: robloxColors.dark.background,
      paper: robloxColors.dark.surface,
    },
    text: {
      primary: robloxColors.dark.text,
      secondary: robloxColors.dark.textSecondary,
    },
  },

  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 800,
      lineHeight: 1.2,
      background: `linear-gradient(135deg, ${robloxColors.neon.blue}, ${robloxColors.neon.purple})`,
      backgroundClip: 'text',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 700,
      lineHeight: 1.3,
      background: `linear-gradient(135deg, ${robloxColors.neon.cyan}, ${robloxColors.neon.green})`,
      backgroundClip: 'text',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
      lineHeight: 1.4,
      color: robloxColors.neon.blue,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.4,
      color: robloxColors.neon.purple,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.5,
      color: robloxColors.neon.green,
    },
    h6: {
      fontSize: '1.125rem',
      fontWeight: 600,
      lineHeight: 1.5,
      color: robloxColors.neon.orange,
    },
  },

  shape: {
    borderRadius: 12,
  },

  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          textTransform: 'none',
          fontWeight: 600,
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: '0 8px 25px rgba(0, 0, 0, 0.25)',
          },
        },
        contained: {
          background: `linear-gradient(135deg, ${robloxColors.primary.main}, ${robloxColors.secondary.main})`,
          '&:hover': {
            background: `linear-gradient(135deg, ${robloxColors.primary.dark}, ${robloxColors.secondary.dark})`,
          },
        },
        outlined: {
          borderColor: robloxColors.neon.blue,
          color: robloxColors.neon.blue,
          '&:hover': {
            borderColor: robloxColors.neon.cyan,
            backgroundColor: `${robloxColors.neon.cyan}20`,
          },
        },
      },
    },

    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: '16px',
          background: `linear-gradient(145deg, ${robloxColors.dark.surface}, ${robloxColors.dark.card})`,
          border: `1px solid ${robloxColors.dark.border}`,
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
          backdropFilter: 'blur(10px)',
          transition: 'all 0.3s ease',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: '0 12px 40px rgba(0, 0, 0, 0.4)',
            borderColor: robloxColors.neon.blue,
          },
        },
      },
    },

    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: '20px',
          fontWeight: 600,
          background: `linear-gradient(135deg, ${robloxColors.neon.blue}, ${robloxColors.neon.purple})`,
          color: robloxColors.dark.text,
          '&:hover': {
            background: `linear-gradient(135deg, ${robloxColors.neon.cyan}, ${robloxColors.neon.pink})`,
          },
        },
      },
    },

    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          fontSize: '1rem',
          minHeight: '48px',
          '&.Mui-selected': {
            color: robloxColors.neon.blue,
          },
        },
      },
    },

    MuiTabs: {
      styleOverrides: {
        indicator: {
          background: `linear-gradient(90deg, ${robloxColors.neon.blue}, ${robloxColors.neon.purple})`,
          height: '3px',
          borderRadius: '2px',
        },
      },
    },

    MuiLinearProgress: {
      styleOverrides: {
        root: {
          borderRadius: '10px',
          height: '8px',
          backgroundColor: robloxColors.dark.border,
        },
        bar: {
          borderRadius: '10px',
          background: `linear-gradient(90deg, ${robloxColors.neon.blue}, ${robloxColors.neon.purple}, ${robloxColors.neon.green})`,
          boxShadow: `0 0 10px ${robloxColors.neon.blue}60`,
        },
      },
    },

    MuiCircularProgress: {
      styleOverrides: {
        root: {
          color: robloxColors.neon.blue,
        },
      },
    },

    MuiBadge: {
      styleOverrides: {
        badge: {
          background: `linear-gradient(135deg, ${robloxColors.neon.orange}, ${robloxColors.neon.pink})`,
          color: robloxColors.dark.text,
          fontWeight: 600,
          boxShadow: `0 0 10px ${robloxColors.neon.orange}60`,
        },
      },
    },

    MuiIconButton: {
      styleOverrides: {
        root: {
          color: robloxColors.neon.blue,
          transition: 'all 0.3s ease',
          '&:hover': {
            color: robloxColors.neon.cyan,
            backgroundColor: `${robloxColors.neon.cyan}20`,
            transform: 'scale(1.1)',
          },
        },
      },
    },

    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          border: `1px solid ${robloxColors.neon.blue}40`,
          background: `linear-gradient(145deg, ${robloxColors.dark.surface}, ${robloxColors.dark.card})`,
          backdropFilter: 'blur(10px)',
        },
        standardInfo: {
          backgroundColor: `${robloxColors.neon.blue}20`,
          color: robloxColors.neon.blue,
        },
        standardSuccess: {
          backgroundColor: `${robloxColors.neon.green}20`,
          color: robloxColors.neon.green,
        },
        standardWarning: {
          backgroundColor: `${robloxColors.neon.orange}20`,
          color: robloxColors.neon.orange,
        },
        standardError: {
          backgroundColor: `${robloxColors.neon.pink}20`,
          color: robloxColors.neon.pink,
        },
      },
    },
  },
});

export { robloxColors };
