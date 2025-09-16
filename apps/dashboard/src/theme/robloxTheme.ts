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

// ULTRA WILD Roblox-inspired color palette - Maximum energy!
export const robloxColors = {
  // Standard color shortcuts (for compatibility)
  primary: "#00ffff",
  secondary: "#ff00ff",
  accent: "#00ff00",
  success: "#00ff00",
  error: "#ff0066",
  warning: "#ff8800",
  info: "#00aaff",
  gray: "#b0b0b0",
  lightGray: "#ffffff",
  darkGray: "#3a3a3a",
  dark: "#0a0a0a",
  white: "#ffffff",
  gold: "#ffff00",
  silver: "#c0c0c0",
  bronze: "#cd7f32",
  yellow: "#ffff00",

  // WILD Neon colors for maximum visual impact
  neon: {
    electricBlue: "#00ffff",
    hotPink: "#ff00ff",
    toxicGreen: "#00ff00",
    laserOrange: "#ff8800",
    plasmaYellow: "#ffff00",
    deepPurple: "#9945ff",
    ultraViolet: "#7b00ff",
    cherryRed: "#ff0066",
    mintGreen: "#00ffaa",
    skyBlue: "#00aaff",
    // Compatibility aliases
    blue: "#00ffff",
    pink: "#ff00ff",
    green: "#00ff00",
    orange: "#ff8800",
    purple: "#9945ff",
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

  // Gamification colors - DOPAMINE TRIGGERS!
  gamification: {
    xp: "#ff00ff", // Hot magenta for XP
    badge: "#00ff00", // Toxic green for badges
    level: "#ff8800", // Laser orange for levels
    achievement: "#ffff00", // Plasma yellow for achievements
    power: "#00ffff", // Electric cyan for power-ups
    legendary: "#9945ff", // Deep purple for legendary items
    epic: "#7b00ff", // Ultra violet for epic rewards
    rare: "#00aaff", // Sky blue for rare finds
    common: "#00ffaa", // Mint green for common items
  },

  // Effects and gradients
  effects: {
    rainbowGradient: "linear-gradient(90deg, #ff0000, #ff8800, #ffff00, #00ff00, #00ffff, #0088ff, #8800ff, #ff00ff)",
    electricGradient: "linear-gradient(135deg, #00ffff, #ff00ff, #ffff00)",
    fireGradient: "linear-gradient(135deg, #ff0000, #ff8800, #ffff00)",
    iceGradient: "linear-gradient(135deg, #00ffff, #00aaff, #0066ff)",
    toxicGradient: "linear-gradient(135deg, #00ff00, #00ff88, #88ff00)",
    cosmicGradient: "linear-gradient(135deg, #9945ff, #ff00ff, #00ffff)",
  },
};

export const robloxTheme = createTheme({
  palette: {
    mode: "dark",
    primary: {
      main: robloxColors.primary,
      light: "#64ffff",
      dark: "#00b8cc",
    },
    secondary: {
      main: robloxColors.secondary,
      light: "#ff64ff",
      dark: "#cc00cc",
    },
    background: {
      default: robloxColors.dark,
      paper: "#1a1a1a",
    },
    text: {
      primary: "#ffffff",
      secondary: "#b0b0b0",
    },
    success: {
      main: robloxColors.success,
    },
    error: {
      main: robloxColors.error,
    },
    warning: {
      main: robloxColors.warning,
    },
    info: {
      main: robloxColors.info,
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
      background: `linear-gradient(135deg, ${robloxColors.neon.electricBlue}, ${robloxColors.neon.green})`,
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
          boxShadow: `0 4px 12px ${alpha(robloxColors.neon.electricBlue, 0.3)}`,
          transition: 'none',
          animation: 'none',
          transform: 'none',
          '&:hover': {
            transform: 'none',
            transition: 'none',
            boxShadow: `0 4px 12px ${alpha(robloxColors.neon.electricBlue, 0.4)}`,
            filter: 'brightness(1.1)',
          },
          '&:active': {
            transform: 'none',
          },
        },
        contained: {
          background: robloxColors.effects.electricGradient,
          color: '#ffffff',
          fontWeight: 700,
          position: 'relative',
          overflow: 'hidden',
          transition: 'none',
          '&::before': {
            display: 'none'
          },
          '&:hover': {
            background: robloxColors.effects.cosmicGradient,
            transform: 'none',
            transition: 'none',
          },
        },
        outlined: {
          borderWidth: '2px',
          borderColor: robloxColors.neon.electricBlue,
          color: robloxColors.neon.electricBlue,
          textShadow: `0 0 5px ${robloxColors.neon.electricBlue}`,
          '&:hover': {
            borderColor: robloxColors.neon.hotPink,
            backgroundColor: alpha(robloxColors.neon.hotPink, 0.1),
            color: robloxColors.neon.hotPink,
            textShadow: `0 0 10px ${robloxColors.neon.hotPink}`,
            boxShadow: `inset 0 0 20px ${alpha(robloxColors.neon.hotPink, 0.2)}, ${`0 0 30px ${robloxColors.secondary}`}`,
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
          boxShadow: `0 8px 32px ${alpha(robloxColors.neon.deepPurple, 0.3)}, inset 0 1px 0 ${alpha(robloxColors.neon.electricBlue, 0.2)}`,
          backdropFilter: 'blur(20px) saturate(1.5)',
          transition: 'none',
          transform: 'none',
          position: 'relative',
          overflow: 'hidden',
          '&::after': {
            display: 'none'
          },
          '&:hover': {
            transform: 'none',
            transition: 'none',
            boxShadow: `0 8px 32px ${alpha(robloxColors.neon.deepPurple, 0.3)}, inset 0 1px 0 ${alpha(robloxColors.neon.electricBlue, 0.2)}`,
            borderColor: robloxColors.neon.electricBlue,
          },
        },
      },
    },

    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: '20px',
          fontWeight: 700,
          background: robloxColors.effects.electricGradient,
          color: robloxColors.dark.text,
          border: `1px solid ${alpha(robloxColors.neon.electricBlue, 0.5)}`,
          boxShadow: `0 2px 10px ${alpha(robloxColors.neon.hotPink, 0.3)}`,
          animation: 'none',
          transition: 'none',
          '&:hover': {
            background: robloxColors.effects.cosmicGradient,
            transform: 'none',
            transition: 'none',
            boxShadow: `0 4px 20px ${alpha(robloxColors.neon.plasmaYellow, 0.5)}`,
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
            color: robloxColors.neon.electricBlue,
            textShadow: `0 0 10px ${robloxColors.neon.electricBlue}`,
            fontWeight: 700,
          },
          '&:hover': {
            color: robloxColors.neon.hotPink,
            transform: 'scale(1.05)',
          },
        },
      },
    },

    MuiTabs: {
      styleOverrides: {
        indicator: {
          background: robloxColors.effects.rainbowGradient,
          height: '4px',
          borderRadius: '2px',
          boxShadow: `0 0 10px ${robloxColors.neon.electricBlue}`,
          animation: 'rainbow-shift 3s linear infinite',
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
          background: robloxColors.effects.rainbowGradient,
          boxShadow: `0 0 20px ${robloxColors.neon.electricBlue}, inset 0 0 10px rgba(255,255,255,0.3)`,
          animation: 'progress-pulse 1s ease-in-out infinite',
          backgroundSize: '200% 100%',
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
          background: robloxColors.effects.fireGradient,
          color: robloxColors.dark.text,
          fontWeight: 700,
          boxShadow: `0 0 15px ${robloxColors.neon.laserOrange}`,
          border: `1px solid ${alpha(robloxColors.neon.plasmaYellow, 0.5)}`,
          animation: 'badge-bounce 2s ease-in-out infinite',
        },
      },
    },

    MuiIconButton: {
      styleOverrides: {
        root: {
          color: robloxColors.neon.electricBlue,
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            color: robloxColors.neon.hotPink,
            backgroundColor: alpha(robloxColors.neon.hotPink, 0.15),
            transform: 'scale(1.15) rotate(10deg)',
            boxShadow: `0 0 30px ${robloxColors.secondary}`,
          },
          '&:active': {
            transform: 'scale(0.95)',
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

// CSS animation keyframes to be injected
export const animationStyles = `
  @keyframes subtle-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.9; }
  }

  @keyframes chip-glow {
    0%, 100% { filter: brightness(1); }
    50% { filter: brightness(1.2) drop-shadow(0 0 10px currentColor); }
  }

  @keyframes rainbow-shift {
    0% { background-position: 0% 50%; }
    100% { background-position: 100% 50%; }
  }

  @keyframes progress-pulse {
    0%, 100% { transform: scaleY(1); }
    50% { transform: scaleY(1.1); }
  }

  @keyframes badge-bounce {
    0%, 100% { transform: translateY(0); }
    25% { transform: translateY(-2px) rotate(-5deg); }
    75% { transform: translateY(2px) rotate(5deg); }
  }

  @keyframes float {
    0%, 100% { transform: translateY(0) rotate(0deg); }
    33% { transform: translateY(-10px) rotate(-3deg); }
    66% { transform: translateY(-5px) rotate(3deg); }
  }

  @keyframes neon-pulse {
    0%, 100% {
      filter: brightness(1);
      text-shadow: 0 0 5px currentColor;
    }
    50% {
      filter: brightness(1.2);
      text-shadow: 0 0 20px currentColor, 0 0 30px currentColor;
    }
  }

  @keyframes electric-border {
    0%, 100% {
      border-color: #00ffff;
      box-shadow: 0 0 5px #00ffff;
    }
    25% {
      border-color: #ff00ff;
      box-shadow: 0 0 5px #ff00ff;
    }
    50% {
      border-color: #ffff00;
      box-shadow: 0 0 5px #ffff00;
    }
    75% {
      border-color: #00ff00;
      box-shadow: 0 0 5px #00ff00;
    }
  }
`;

// Light theme version with bright, energetic colors for daytime viewing
export const robloxLightTheme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#0099ff", // Bright blue
      light: "#64d0ff",
      dark: "#0066cc",
    },
    secondary: {
      main: "#ff0099", // Bright pink
      light: "#ff64cc",
      dark: "#cc0066",
    },
    background: {
      default: "#f5f5ff", // Light purple-tinted background
      paper: "#ffffff",
    },
    text: {
      primary: "#1a1a2e", // Dark blue-gray
      secondary: "#5a5a7e",
    },
    success: {
      main: "#00cc66",
    },
    error: {
      main: "#ff3366",
    },
    warning: {
      main: "#ff9900",
    },
    info: {
      main: "#0099cc",
    },
  },
  typography: robloxTheme.typography,
  shape: robloxTheme.shape,
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          textTransform: 'none',
          fontWeight: 700,
          padding: '10px 24px',
          fontSize: '1rem',
          transition: 'none',
          transform: 'none',
        },
        contained: {
          background: "linear-gradient(135deg, #0099ff, #ff0099)",
          color: "#ffffff",
          fontWeight: 700,
          boxShadow: "0 4px 20px rgba(0, 153, 255, 0.3)",
          transition: 'none',
          "&:hover": {
            background: "linear-gradient(135deg, #0099ff, #ff0099)",
            boxShadow: "0 4px 20px rgba(0, 153, 255, 0.4)",
            transform: 'none',
            transition: 'none',
            filter: 'brightness(1.1)',
          },
        },
        outlined: {
          borderWidth: '2px',
          borderColor: "#0099ff",
          color: "#0099ff",
          "&:hover": {
            borderColor: "#ff0099",
            backgroundColor: alpha("#ff0099", 0.1),
            color: "#ff0099",
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: "16px",
          background: "#ffffff",
          border: "2px solid rgba(0, 153, 255, 0.2)",
          boxShadow: "0 8px 32px rgba(0, 153, 255, 0.1)",
          transition: 'none',
          transform: 'none',
          "&:hover": {
            transform: "none",
            transition: 'none',
            boxShadow: "0 8px 32px rgba(0, 153, 255, 0.15)",
            borderColor: "rgba(0, 153, 255, 0.3)",
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          background: "linear-gradient(90deg, #ffffff 0%, #f5f5ff 100%)",
          color: "#1a1a2e",
          borderBottom: "2px solid #0099ff",
          boxShadow: "0 4px 20px rgba(0, 153, 255, 0.2)",
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: '20px',
          fontWeight: 600,
          background: "linear-gradient(135deg, #0099ff, #ff0099)",
          color: "#ffffff",
          border: "none",
          transition: 'none',
          transform: 'none',
          "&:hover": {
            transform: 'none',
            transition: 'none',
            filter: 'brightness(1.1)',
          },
        },
      },
    },
  },
});

// Dark theme version - the original wild neon theme
export const robloxDarkTheme = robloxTheme;

export default robloxTheme;
