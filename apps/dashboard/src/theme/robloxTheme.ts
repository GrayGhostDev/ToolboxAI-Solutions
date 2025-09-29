/**
 * Roblox-Inspired Futuristic Theme
 *
 * A vibrant, tech-focused theme designed for kids with:
 * - Neon colors inspired by Roblox Discord communities
 * - Futuristic UI elements
 * - Engaging animations and effects
 * - Character and 3D icon integration
 */

// Material UI imports removed - now using Mantine theme system
// See config/mantine-theme.ts for the main Mantine theme configuration

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

  // Brand colors for Roblox
  brand: {
    red: {
      primary: "#ee0000",
      light: "#ff3333",
      dark: "#cc0000"
    },
    gray: {
      primary: "#474747",
      light: "#707070",
      dark: "#2b2b2b"
    }
  },

  // Semantic colors
  semantic: {
    success: "#00ff00",
    error: "#ff0066",
    warning: "#ff8800",
    info: "#00aaff"
  },

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

// Design tokens for consistent styling
export const designTokens = {
  borderRadius: {
    sm: '4px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    '2xl': '20px'
  },
  shadows: {
    sm: '0 1px 3px rgba(0,0,0,0.12)',
    base: '0 4px 6px rgba(0,0,0,0.1)',
    md: '0 6px 12px rgba(0,0,0,0.15)',
    lg: '0 10px 20px rgba(0,0,0,0.2)',
    xl: '0 20px 40px rgba(0,0,0,0.3)'
  },
  animation: {
    duration: {
      fast: '150ms',
      normal: '250ms',
      slow: '350ms'
    },
    easing: {
      inOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
      out: 'cubic-bezier(0.0, 0, 0.2, 1)',
      in: 'cubic-bezier(0.4, 0, 1, 1)'
    }
  }
};

// Dark mode tokens
export const darkModeTokens = {
  colors: {
    background: {
      primary: robloxColors.darkTheme.background,
      secondary: robloxColors.darkTheme.surface
    },
    surface: {
      primary: robloxColors.darkTheme.surface,
      secondary: robloxColors.darkTheme.card
    },
    text: {
      primary: robloxColors.darkTheme.text,
      secondary: robloxColors.darkTheme.textSecondary
    },
    border: {
      primary: robloxColors.darkTheme.border,
      secondary: '#4a4a4a'
    }
  }
};

// Light mode tokens
export const lightModeTokens = {
  colors: {
    background: {
      primary: '#ffffff',
      secondary: '#f5f5f5'
    },
    surface: {
      primary: '#ffffff',
      secondary: '#fafafa'
    },
    text: {
      primary: '#1a1a1a',
      secondary: '#666666'
    },
    border: {
      primary: '#e0e0e0',
      secondary: '#d0d0d0'
    }
  }
};

// Base theme configuration shared between light and dark themes
const baseThemeConfig = {
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 800,
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 700,
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.5,
    },
    h6: {
      fontSize: '1.125rem',
      fontWeight: 600,
      lineHeight: 1.5,
    },
  },
  shape: {
    borderRadius: 12,
  },
};

// TODO: Convert to Mantine theme object instead of MUI createTheme
// The actual Mantine theme is defined in config/mantine-theme.ts
// This theme object is kept for compatibility but should be migrated
export const robloxTheme = {
  mode: "dark",
  colors: {
    primary: robloxColors.primary,
    secondary: robloxColors.secondary,
    background: robloxColors.darkBase,
    surface: "#1a1a1a",
    text: "#ffffff",
    textSecondary: "#b0b0b0",
    success: robloxColors.success,
    error: robloxColors.error,
    warning: robloxColors.warning,
    info: robloxColors.info,
  },
  typography: baseThemeConfig.typography,
  // Note: Component styles moved to Mantine theme
};

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

// Light theme version for compatibility
export const robloxLightTheme = {
  mode: "light",
  colors: {
    primary: robloxColors.brand.red.primary,
    secondary: robloxColors.brand.gray.primary,
    background: lightModeTokens.colors.background.primary,
    surface: lightModeTokens.colors.surface.primary,
    text: lightModeTokens.colors.text.primary,
    textSecondary: lightModeTokens.colors.text.secondary,
    success: robloxColors.semantic.success,
    error: robloxColors.semantic.error,
    warning: robloxColors.semantic.warning,
    info: robloxColors.semantic.info,
  },
  typography: baseThemeConfig.typography,
};

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
    return path.split('.').reduce((obj, key) => obj[key], theme.colors as any);
  },

  // Create theme-aware gradient
  createGradient: (color1: string, color2: string, angle = 135) => {
    return `linear-gradient(${angle}deg, ${color1} 0%, ${color2} 100%)`;
  },

  // Get responsive spacing (simplified for Mantine compatibility)
  getSpacing: (theme: typeof robloxTheme, factor: number) => {
    return `${factor * 8}px`; // Mantine uses rem-based spacing
  },

  // Create theme-aware shadow (simplified without alpha)
  createShadow: (color: string, opacity = 0.1) => {
    return `0 4px 12px ${color}${Math.round(opacity * 255).toString(16).padStart(2, '0')}`;
  }
};

// Gamification theme helpers
export const gamificationHelpers = {
  // Get XP progress color based on percentage
  getXPColor: (percentage: number) => {
    if (percentage >= 80) return robloxColors.gamification.legendary;
    if (percentage >= 60) return robloxColors.gamification.level;
    if (percentage >= 40) return robloxColors.gamification.badge;
    return robloxColors.gamification.xp;
  },

  // Get badge color based on rarity
  getBadgeColor: (rarity: 'common' | 'rare' | 'epic' | 'legendary') => {
    switch (rarity) {
      case 'legendary': return robloxColors.gamification.legendary;
      case 'epic': return robloxColors.gamification.epic;
      case 'rare': return robloxColors.gamification.rare;
      default: return robloxColors.gamification.badge;
    }
  },

  // Create level-based gradient
  getLevelGradient: (level: number) => {
    const colors = [
      robloxColors.gamification.xp,
      robloxColors.gamification.badge,
      robloxColors.gamification.achievement,
      robloxColors.gamification.legendary
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
    return theme.mode === 'dark'
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
