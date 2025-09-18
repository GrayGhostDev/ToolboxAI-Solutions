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
  darkBase: "#0a0a0a",
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
  darkTheme: {
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

// CSS animation keyframes for Roblox theme
export const animationStyles = `
  @keyframes roblox-pulse {
    0%, 100% {
      opacity: 1;
      transform: scale(1);
    }
    50% {
      opacity: 0.9;
      transform: scale(1.02);
    }
  }

  @keyframes roblox-glow {
    0%, 100% {
      box-shadow: 0 0 5px rgba(226, 35, 26, 0.3);
    }
    50% {
      box-shadow: 0 0 20px rgba(226, 35, 26, 0.6);
    }
  }

  @keyframes roblox-bounce {
    0%, 100% {
      transform: translateY(0);
    }
    50% {
      transform: translateY(-4px);
    }
  }

  @keyframes roblox-float {
    0%, 100% {
      transform: translateY(0px);
    }
    50% {
      transform: translateY(-8px);
    }
  }

  @keyframes roblox-shimmer {
    0% {
      background-position: -200% center;
    }
    100% {
      background-position: 200% center;
    }
  }

  @keyframes roblox-rotate {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  .roblox-pulse {
    animation: roblox-pulse 2s ease-in-out infinite;
  }

  .roblox-glow {
    animation: roblox-glow 2s ease-in-out infinite;
  }

  .roblox-bounce {
    animation: roblox-bounce 1s ease-in-out infinite;
  }

  .roblox-float {
    animation: roblox-float 3s ease-in-out infinite;
  }

  .roblox-shimmer {
    background: linear-gradient(
      90deg,
      transparent,
      rgba(226, 35, 26, 0.1),
      transparent
    );
    background-size: 200% 100%;
    animation: roblox-shimmer 2s infinite;
  }

  .roblox-rotate {
    animation: roblox-rotate 2s linear infinite;
  }
`;

// Light theme version with Roblox branding
export const robloxLightTheme = createTheme({
  ...baseThemeConfig,
  palette: {
    mode: "light",
    primary: {
      main: robloxColors.brand.red.primary,
      light: robloxColors.brand.red.light,
      dark: robloxColors.brand.red.dark,
      contrastText: robloxColors.white
    },
    secondary: {
      main: robloxColors.brand.gray.primary,
      light: robloxColors.brand.gray.light,
      dark: robloxColors.brand.gray.dark,
      contrastText: robloxColors.white
    },
    background: {
      default: lightModeTokens.colors.background.primary,
      paper: lightModeTokens.colors.surface.primary
    },
    surface: {
      main: lightModeTokens.colors.surface.secondary
    } as any,
    text: {
      primary: lightModeTokens.colors.text.primary,
      secondary: lightModeTokens.colors.text.secondary
    },
    success: {
      main: robloxColors.semantic.success
    },
    error: {
      main: robloxColors.semantic.error
    },
    warning: {
      main: robloxColors.semantic.warning
    },
    info: {
      main: robloxColors.semantic.info
    },
    divider: lightModeTokens.colors.border.primary
  },
  components: {
    ...robloxTheme.components,
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: designTokens.borderRadius['2xl'],
          backgroundColor: lightModeTokens.colors.surface.primary,
          border: `1px solid ${lightModeTokens.colors.border.primary}`,
          boxShadow: designTokens.shadows.base,
          transition: `all ${designTokens.animation.duration.normal} ${designTokens.animation.easing.inOut}`,
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: designTokens.shadows.lg,
            borderColor: alpha(robloxColors.brand.red.primary, 0.3)
          }
        }
      }
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: lightModeTokens.colors.surface.primary,
          borderBottom: `1px solid ${lightModeTokens.colors.border.primary}`,
          boxShadow: designTokens.shadows.sm,
          color: lightModeTokens.colors.text.primary
        }
      }
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: designTokens.borderRadius.lg,
            '& fieldset': {
              borderColor: lightModeTokens.colors.border.primary
            },
            '&:hover fieldset': {
              borderColor: lightModeTokens.colors.border.secondary
            },
            '&.Mui-focused fieldset': {
              borderColor: robloxColors.brand.red.primary
            }
          }
        }
      }
    }
  }
});

// Dark theme is the main theme
export const robloxDarkTheme = robloxTheme;

// Export theme variants
export { robloxTheme as default };

// Theme selection helper
export const getRobloxTheme = (mode: 'light' | 'dark') => {
  return mode === 'light' ? robloxLightTheme : robloxDarkTheme;
};

// Theme utilities
export const themeUtils = {
  // Get theme-aware color
  getColor: (theme: typeof robloxTheme, path: string) => {
    return path.split('.').reduce((obj, key) => obj[key], theme.palette as any);
  },

  // Create theme-aware gradient
  createGradient: (color1: string, color2: string, angle = 135) => {
    return `linear-gradient(${angle}deg, ${color1} 0%, ${color2} 100%)`;
  },

  // Get responsive spacing
  getSpacing: (theme: typeof robloxTheme, factor: number) => {
    return theme.spacing(factor);
  },

  // Create theme-aware shadow
  createShadow: (color: string, opacity = 0.1) => {
    return `0 4px 12px ${alpha(color, opacity)}`;
  }
};

// Gamification theme helpers
export const gamificationHelpers = {
  // Get XP progress color based on percentage
  getXPColor: (percentage: number) => {
    if (percentage >= 80) return robloxColors.gamification.star;
    if (percentage >= 60) return robloxColors.gamification.level;
    if (percentage >= 40) return robloxColors.gamification.badge;
    return robloxColors.gamification.xp;
  },

  // Get badge color based on rarity
  getBadgeColor: (rarity: 'common' | 'rare' | 'epic' | 'legendary') => {
    switch (rarity) {
      case 'legendary': return robloxColors.gamification.star;
      case 'epic': return robloxColors.gamification.gem;
      case 'rare': return robloxColors.gamification.achievement;
      default: return robloxColors.gamification.badge;
    }
  },

  // Create level-based gradient
  getLevelGradient: (level: number) => {
    const colors = [
      robloxColors.gamification.xp,
      robloxColors.gamification.badge,
      robloxColors.gamification.achievement,
      robloxColors.gamification.star
    ];
    const colorIndex = Math.min(Math.floor(level / 10), colors.length - 1);
    const nextColorIndex = Math.min(colorIndex + 1, colors.length - 1);
    return themeUtils.createGradient(colors[colorIndex], colors[nextColorIndex]);
  }
};

// Accessibility helpers
export const a11yHelpers = {
  // Check color contrast ratio
  getContrastRatio: (foreground: string, background: string) => {
    // Simplified contrast ratio calculation
    // In a real implementation, you'd use a proper contrast ratio library
    return 4.5; // Placeholder for WCAG AA compliance
  },

  // Get accessible text color for background
  getAccessibleTextColor: (backgroundColor: string, theme: typeof robloxTheme) => {
    // Simplified logic - in practice, calculate actual contrast
    return theme.palette.mode === 'dark'
      ? darkModeTokens.colors.text.primary
      : lightModeTokens.colors.text.primary;
  },

  // Focus ring styles
  getFocusRing: (color = robloxColors.brand.red.primary) => ({
    outline: `2px solid ${color}`,
    outlineOffset: '2px',
    borderRadius: designTokens.borderRadius.md
  })
};
